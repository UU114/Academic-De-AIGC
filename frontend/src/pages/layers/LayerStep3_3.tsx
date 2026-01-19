import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  Anchor,
  FileText,
  RefreshCw,
  Hash,
  Quote,
  Percent,
  AlertTriangle,
  Edit3,
  Sparkles,
  Upload,
  Check,
  X,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import { useSubstepStateStore } from '../../stores/substepStateStore';
import {
  paragraphLayerApi,
  documentLayerApi,
  ParagraphAnalysisResponse,
  DetectionIssue,
  IssueSeverity,
} from '../../services/analysisApi';

/**
 * Layer Step 3.3 - Anchor Density Analysis
 * 步骤 3.3 - 锚点密度分析
 *
 * Analyzes evidence density in paragraphs:
 * - 13 anchor types (citations, numbers, proper nouns, etc.)
 * - Calculates anchors per 100 words
 * - Flags high hallucination risk (<5 anchors/100 words)
 *
 * 分析段落中的证据密度：
 * - 13类学术锚点（引用、数字、专有名词等）
 * - 计算每100词的锚点数
 * - 标记高幻觉风险（<5锚点/100词）
 */

// Response types for merge modify operations
// 合并修改操作的响应类型
interface ModifyPromptResponse {
  prompt: string;
  promptZh: string;
  issuesSummaryZh: string;
  colloquialismLevel: number;
  estimatedChanges: number;
}

interface ApplyModifyResponse {
  modifiedText: string;
  changesSummaryZh: string;
  changesCount: number;
  remainingAttempts: number;
  colloquialismLevel: number;
}

// Issue suggestion response type
// 问题建议响应类型
interface IssueSuggestionResponse {
  analysis: string;
  suggestions: string[];
  exampleFix?: string;
}

interface LayerStep3_3Props {
  documentIdProp?: string;
  onComplete?: (result: ParagraphAnalysisResponse) => void;
  showNavigation?: boolean;
  sectionContext?: Record<string, unknown>;
}

export default function LayerStep3_3({
  documentIdProp,
  onComplete,
  showNavigation = true,
  sectionContext,
}: LayerStep3_3Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // Helper function to check if documentId is valid
  const isValidDocumentId = (id: string | undefined): boolean => {
    return !!(id && id !== 'undefined' && id !== 'null');
  };

  const getInitialDocumentId = (): string | undefined => {
    if (isValidDocumentId(documentIdProp)) return documentIdProp;
    if (isValidDocumentId(documentIdParam)) return documentIdParam;
    return undefined;
  };

  const [documentId, setDocumentId] = useState<string | undefined>(getInitialDocumentId());
  const [sessionFetchAttempted, setSessionFetchAttempted] = useState(
    isValidDocumentId(documentIdProp) || isValidDocumentId(documentIdParam)
  );

  useEffect(() => {
    const fetchDocumentIdFromSession = async () => {
      if (!isValidDocumentId(documentId) && sessionId) {
        try {
          const sessionState = await sessionApi.getCurrent(sessionId);
          if (sessionState.documentId) {
            setDocumentId(sessionState.documentId);
          }
        } catch (err) {
          console.error('Failed to get documentId from session:', err);
        }
      }
      setSessionFetchAttempted(true);
    };

    if (!sessionId) {
      setSessionFetchAttempted(true);
    } else if (!isValidDocumentId(documentId)) {
      fetchDocumentIdFromSession();
    } else {
      setSessionFetchAttempted(true);
    }
  }, [documentId, sessionId]);

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer3-step3-3').catch(console.error);
    }
  }, [sessionId]);

  // Basic state
  // 基本状态
  const [result, setResult] = useState<ParagraphAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [documentText, setDocumentText] = useState<string>('');

  // Issues derived from analysis result
  // 从分析结果派生的问题列表
  const [anchorIssues, setAnchorIssues] = useState<DetectionIssue[]>([]);

  // Issue selection for merge modify
  // 用于合并修改的问题选择
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());

  // Click-expand state for individual issue analysis
  // 点击展开状态，用于单个问题分析
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

  // Issue suggestion state (LLM-based detailed suggestions)
  // 问题建议状态（基于LLM的详细建议）
  const [issueSuggestion, setIssueSuggestion] = useState<IssueSuggestionResponse | null>(null);
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);

  // Per-issue suggestion cache to avoid redundant API calls
  // 每个问题的建议缓存，避免重复API调用
  const suggestionCacheRef = useRef<Map<number, IssueSuggestionResponse>>(new Map());

  // Merge modify state
  // 合并修改状态
  const [showMergeConfirm, setShowMergeConfirm] = useState(false);
  const [mergeMode, setMergeMode] = useState<'prompt' | 'apply'>('prompt');
  const [mergeUserNotes, setMergeUserNotes] = useState('');
  const [isMerging, setIsMerging] = useState(false);
  const [mergeResult, setMergeResult] = useState<ModifyPromptResponse | ApplyModifyResponse | null>(null);

  // Document modification state
  // 文档修改状态
  const [modifyMode, setModifyMode] = useState<'file' | 'text'>('file');
  const [newFile, setNewFile] = useState<File | null>(null);
  const [newText, setNewText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Skip confirmation state
  // 跳过确认状态
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);

  // Data/Citation warning state
  // 数据/引用警告状态
  const [showDataWarning, setShowDataWarning] = useState(false);
  const [dataWarningAction, setDataWarningAction] = useState<'prompt' | 'apply' | 'accept' | 'continue' | null>(null);

  const isAnalyzingRef = useRef(false);

  // Substep state store for document text handling
  // 子步骤状态存储用于文档文本处理
  const substepStore = useSubstepStateStore();

  // Check if selected issues involve adding data/citations/references
  // 检查选中的问题是否涉及添加数据/引用/参考文献
  const hasDataRelatedIssues = useCallback(() => {
    const selectedIssues = Array.from(selectedIssueIndices).map(i => anchorIssues[i]);
    const dataRelatedTypes = ['low_density', 'no_anchors', 'very_low_anchor_density', 'suspected_hallucination'];
    const dataRelatedKeywords = ['anchor', 'citation', 'data', 'reference', 'statistic', 'number', '引用', '数据', '锚点', '统计'];

    return selectedIssues.some(issue => {
      // Check issue type
      if (dataRelatedTypes.includes(issue.type)) return true;
      // Check description for keywords
      const desc = (issue.description + ' ' + (issue.descriptionZh || '')).toLowerCase();
      return dataRelatedKeywords.some(keyword => desc.includes(keyword.toLowerCase()));
    });
  }, [selectedIssueIndices, anchorIssues]);

  // Load document
  // 加载文档
  useEffect(() => {
    if (!sessionFetchAttempted) return;
    if (isValidDocumentId(documentId)) {
      loadDocumentText(documentId!);
    } else {
      setError('Document ID not found. Please start from the document upload page. / 未找到文档ID，请从文档上传页面开始。');
      setIsLoading(false);
    }
  }, [documentId, sessionFetchAttempted]);

  const loadDocumentText = async (docId: string) => {
    try {
      // Initialize substep store for session if needed
      // 如果需要，为会话初始化子步骤存储
      if (sessionId && substepStore.currentSessionId !== sessionId) {
        await substepStore.initForSession(sessionId);
      }

      // Check previous steps for modified text (step3-2, step3-1, step3-0, then Layer 4 steps, then Layer 5 steps)
      // 检查前面步骤的修改文本（先检查step3-2, step3-1, step3-0，再检查第4层，再检查第5层）
      const previousSteps = ['step3-2', 'step3-1', 'step3-0',
                            'step2-5', 'step2-4', 'step2-3', 'step2-2', 'step2-1', 'step2-0',
                            'step1-5', 'step1-4', 'step1-3', 'step1-2', 'step1-1'];
      let foundModifiedText: string | null = null;

      for (const stepName of previousSteps) {
        const stepState = substepStore.getState(stepName);
        if (stepState?.modifiedText) {
          console.log(`[LayerStep3_3] Using modified text from ${stepName}`);
          foundModifiedText = stepState.modifiedText;
          break;
        }
      }

      if (foundModifiedText) {
        setDocumentText(foundModifiedText);
      } else {
        const doc = await documentApi.get(docId);
        if (doc.originalText) {
          setDocumentText(doc.originalText);
        } else {
          setError('Document text not found / 未找到文档文本');
        }
      }
    } catch (err) {
      console.error('Failed to load document:', err);
      setError('Failed to load document / 加载文档失败');
    } finally {
      setIsLoading(false);
    }
  };

  // Run analysis when document is loaded
  // 文档加载后运行分析
  useEffect(() => {
    if (documentText && analysisStarted && !isAnalyzingRef.current) {
      runAnalysis();
    }
  }, [documentText, analysisStarted]);

  const runAnalysis = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;
    setIsAnalyzing(true);
    setError(null);

    try {
      const analysisResult = await paragraphLayerApi.analyzeAnchor(documentText, sectionContext, sessionId || undefined);
      setResult(analysisResult);
      console.log('Anchor analysis result:', analysisResult);  // Debug log

      // Create issues from analysis result
      // 从分析结果创建问题列表
      const issues: DetectionIssue[] = [];

      // Check for low anchor density paragraphs (hallucination risk)
      // 检查低锚点密度段落（幻觉风险）
      if (analysisResult.paragraphDetails) {
        analysisResult.paragraphDetails.forEach((para, index) => {
          const anchorCount = para.anchorCount || 0;
          // Get paragraph preview (first 5 words or from backend)
          // 获取段落预览（前5个单词或从后端获取）
          const preview = para.preview || `Para ${index + 1}`;
          const locationText = `[${index + 1}] "${preview}"`;

          if (anchorCount < 3) {
            issues.push({
              type: 'very_low_anchor_density',
              description: `Paragraph ${index + 1} "${preview}" has very low anchor density (${anchorCount} anchors) - high hallucination risk`,
              descriptionZh: `段落${index + 1} "${preview}" 锚点密度极低 (${anchorCount}个锚点) - 高幻觉风险`,
              severity: 'high' as IssueSeverity,
              layer: 'paragraph',
              location: locationText,
            });
          } else if (anchorCount < 5) {
            issues.push({
              type: 'low_anchor_density',
              description: `Paragraph ${index + 1} "${preview}" has low anchor density (${anchorCount} anchors) - moderate hallucination risk`,
              descriptionZh: `段落${index + 1} "${preview}" 锚点密度较低 (${anchorCount}个锚点) - 中等幻觉风险`,
              severity: 'medium' as IssueSeverity,
              layer: 'paragraph',
              location: locationText,
            });
          }
        });
      }

      // Check overall anchor density
      // 检查整体锚点密度
      if (analysisResult.anchorDensity !== undefined && analysisResult.anchorDensity < 5) {
        issues.push({
          type: 'overall_low_anchor_density',
          description: `Overall anchor density is low (${analysisResult.anchorDensity.toFixed(1)}/100 words)`,
          descriptionZh: `整体锚点密度较低 (${analysisResult.anchorDensity.toFixed(1)}/100词)`,
          severity: analysisResult.anchorDensity < 3 ? 'high' as IssueSeverity : 'medium' as IssueSeverity,
          layer: 'paragraph',
          location: 'Document-wide',
        });
      }

      setAnchorIssues(issues);

      if (onComplete) {
        onComplete(analysisResult);
      }
    } catch (err) {
      console.error('Analysis failed:', err);
      setError('Analysis failed / 分析失败');
    } finally {
      setIsAnalyzing(false);
      isAnalyzingRef.current = false;
    }
  };

  // Load detailed suggestion for a specific issue (LLM-based) with caching
  // 为特定问题加载详细建议（基于LLM），带缓存
  const loadIssueSuggestion = useCallback(async (index: number) => {
    const issue = anchorIssues[index];
    if (!issue || !documentId) return;

    // Check cache first
    // 首先检查缓存
    const cached = suggestionCacheRef.current.get(index);
    if (cached) {
      setIssueSuggestion(cached);
      return;
    }

    setIsLoadingSuggestion(true);
    setSuggestionError(null);

    try {
      const response = await documentLayerApi.getIssueSuggestion(
        documentId,
        issue,
        false
      );
      // Transform response to match our interface
      const suggestion = {
        analysis: response.diagnosisZh || '',
        suggestions: response.strategies?.map((s) => `${s.nameZh}: ${s.descriptionZh}`) || [],
        exampleFix: response.strategies?.[0]?.exampleAfter || '',
      };
      // Store in cache
      // 存入缓存
      suggestionCacheRef.current.set(index, suggestion);
      setIssueSuggestion(suggestion);
    } catch (err) {
      console.error('Failed to load suggestion:', err);
      setSuggestionError('Failed to load detailed suggestion / 加载详细建议失败');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [anchorIssues, documentId]);

  // Handle issue click - toggle expand and auto-load suggestions
  // 处理问题点击 - 切换展开并自动加载建议
  const handleIssueClick = useCallback(async (index: number) => {
    if (expandedIssueIndex === index) {
      // Collapse if already expanded
      // 如果已展开则折叠
      setExpandedIssueIndex(null);
      setIssueSuggestion(null);
      return;
    }
    // Expand and load suggestion
    // 展开并加载建议
    setExpandedIssueIndex(index);
    await loadIssueSuggestion(index);
  }, [expandedIssueIndex, loadIssueSuggestion]);

  // Toggle issue selection (checkbox only)
  // 切换问题选择（仅复选框）
  const toggleIssueSelection = useCallback((index: number) => {
    setSelectedIssueIndices(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
    setMergeResult(null);
  }, []);

  // Trigger data warning check before action
  // 在操作前触发数据警告检查
  const triggerWithDataWarning = useCallback((action: 'prompt' | 'apply' | 'accept') => {
    if (hasDataRelatedIssues()) {
      setDataWarningAction(action);
      setShowDataWarning(true);
    } else {
      // No warning needed, execute directly
      if (action === 'prompt' || action === 'apply') {
        setMergeMode(action === 'prompt' ? 'prompt' : 'apply');
        executeActualMergeModify();
      } else if (action === 'accept') {
        executeActualAcceptModification();
      }
    }
  }, [hasDataRelatedIssues]);

  // Execute merge modify (generate prompt or apply modification) - actual execution
  // 执行合并修改（生成提示或应用修改）- 实际执行
  const executeActualMergeModify = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentId) return;

    setIsMerging(true);
    setShowMergeConfirm(false);
    setShowDataWarning(false);
    setDataWarningAction(null);

    try {
      const selectedIssues = Array.from(selectedIssueIndices).map(i => anchorIssues[i]);

      if (mergeMode === 'prompt') {
        const response = await documentLayerApi.generateModifyPrompt(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult(response);
      } else {
        const response = await documentLayerApi.applyModify(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult(response);
      }
    } catch (err) {
      console.error('Merge modify failed:', err);
      setError('Merge modify failed / 合并修改失败');
    } finally {
      setIsMerging(false);
    }
  }, [selectedIssueIndices, documentId, anchorIssues, mergeMode, mergeUserNotes, sessionId]);

  // Actual accept modification execution
  // 实际接受修改执行
  const executeActualAcceptModification = useCallback(() => {
    if (mergeResult && 'modifiedText' in mergeResult && mergeResult.modifiedText) {
      setNewText(mergeResult.modifiedText);
      setModifyMode('text');
      setMergeResult(null);
      setShowDataWarning(false);
      setDataWarningAction(null);
    }
  }, [mergeResult]);

  // Check if modified text contains placeholder markers that need verification
  // 检查修改后的文本是否包含需要验证的占位符标记
  const hasPlaceholderMarkers = useCallback((text: string) => {
    const placeholderPatterns = [
      /\[AUTHOR_X+\]/i,
      /\[AUTHOR_YEAR_X+\]/i,
      /\[DATA_X+%?\]/i,
      /\[N=X+\]/i,
      /\[DATE_X+\]/i,
      /\[YEAR_X+\]/i,
      /\[INSTITUTION_X+\]/i,
      /\[DATASET_X+\]/i,
      /\[citation needed\]/i,
    ];
    return placeholderPatterns.some(pattern => pattern.test(text));
  }, []);

  // Actual execution of confirm modify (after warning)
  // 确认修改的实际执行（警告后）
  const executeActualConfirmModify = useCallback(async () => {
    setIsUploading(true);
    setError(null);
    setShowDataWarning(false);
    setDataWarningAction(null);

    try {
      // Extract modified text from file or text input
      // 从文件或文本输入中提取修改后的文本
      let modifiedText: string = '';
      if (modifyMode === 'file' && newFile) {
        modifiedText = await newFile.text();
      } else if (modifyMode === 'text' && newText.trim()) {
        modifiedText = newText.trim();
      } else {
        setError('Please select a file or enter text / 请选择文件或输入文本');
        setIsUploading(false);
        return;
      }

      // Save modified text to substep store
      // 将修改后的文本保存到子步骤存储
      if (sessionId && modifiedText) {
        await substepStore.saveModifiedText('step3-3', modifiedText);
        await substepStore.markCompleted('step3-3');
        console.log('[LayerStep3_3] Saved modified text to substep store');
      }

      // Navigate to next step
      // 导航到下一步
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer3-step3-4/${documentId}?${params.toString()}`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload modified document / 上传修改后的文档失败');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate, documentId, substepStore]);

  // Handle data warning confirmation
  // 处理数据警告确认
  const handleDataWarningConfirm = useCallback(() => {
    setShowDataWarning(false);
    if (dataWarningAction === 'prompt') {
      setMergeMode('prompt');
      executeActualMergeModify();
    } else if (dataWarningAction === 'apply') {
      setMergeMode('apply');
      executeActualMergeModify();
    } else if (dataWarningAction === 'accept') {
      executeActualAcceptModification();
    } else if (dataWarningAction === 'continue') {
      executeActualConfirmModify();
    }
    setDataWarningAction(null);
  }, [dataWarningAction, executeActualMergeModify, executeActualAcceptModification, executeActualConfirmModify]);

  // Execute merge modify (wrapper that checks for data warning)
  // 执行合并修改（检查数据警告的包装函数）
  const executeMergeModify = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentId) return;

    if (hasDataRelatedIssues()) {
      setDataWarningAction(mergeMode);
      setShowDataWarning(true);
    } else {
      executeActualMergeModify();
    }
  }, [selectedIssueIndices, documentId, hasDataRelatedIssues, mergeMode, executeActualMergeModify]);

  // Handle regenerate
  // 处理重新生成
  const handleRegenerate = useCallback(() => {
    setMergeResult(null);
    setShowMergeConfirm(true);
    setMergeMode('apply');
  }, []);

  // Handle accept modification (with data warning check)
  // 处理接受修改（带数据警告检查）
  const handleAcceptModification = useCallback(() => {
    if (hasDataRelatedIssues()) {
      setDataWarningAction('accept');
      setShowDataWarning(true);
    } else {
      executeActualAcceptModification();
    }
  }, [hasDataRelatedIssues, executeActualAcceptModification]);

  // Handle file selection
  // 处理文件选择
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setNewFile(file);
    }
  }, []);

  // Handle confirm modification and navigate to next step (with warning check)
  // 处理确认修改并导航到下一步（带警告检查）
  const handleConfirmModify = useCallback(async () => {
    // Get the text that will be applied
    // 获取将要应用的文本
    let textToCheck = '';
    if (modifyMode === 'file' && newFile) {
      textToCheck = await newFile.text();
    } else if (modifyMode === 'text' && newText.trim()) {
      textToCheck = newText.trim();
    }

    // Check for placeholder markers or data-related issues
    // 检查占位符标记或数据相关问题
    if (hasPlaceholderMarkers(textToCheck) || hasDataRelatedIssues()) {
      setDataWarningAction('continue');
      setShowDataWarning(true);
    } else {
      executeActualConfirmModify();
    }
  }, [modifyMode, newFile, newText, hasPlaceholderMarkers, hasDataRelatedIssues, executeActualConfirmModify]);

  // Navigation handlers
  // 导航处理
  const goToNextStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-4/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-2/${documentId}?${params.toString()}`);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getDensityColor = (density: number) => {
    if (density >= 10) return 'text-green-600 bg-green-100';
    if (density >= 5) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getDensityRiskLevel = (density: number): string => {
    if (density >= 10) return 'low';
    if (density >= 5) return 'medium';
    return 'high';
  };

  const hasSelectedIssues = selectedIssueIndices.size > 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage message="Loading document... / 加载文档中..." />
      </div>
    );
  }

  if (error && !result) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center gap-2 text-red-700">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
        <Button onClick={() => { setError(null); isAnalyzingRef.current = false; runAnalysis(); }} className="mt-4" variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry / 重试
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Loading Overlay for LLM operations */}
      {/* LLM操作加载遮罩 */}
      <LoadingOverlay
        isVisible={isMerging}
        operationType={mergeMode}
        issueCount={selectedIssueIndices.size}
      />

      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Anchor className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3.3: Anchor Density Analysis
              </h2>
              <p className="text-sm text-gray-500">
                步骤 3.3: 锚点密度分析
              </p>
            </div>
          </div>
          {isAnalyzing && (
            <div className="flex items-center gap-2 text-orange-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing... / 分析中...</span>
            </div>
          )}
        </div>

        <p className="text-gray-600 mb-4">
          Analyzes evidence density (academic anchors) in each paragraph. Low anchor density (&lt;5/100 words) indicates potential AI-generated filler content (hallucination risk).
          <br />
          <span className="text-gray-500">
            分析每个段落的证据密度（学术锚点）。低锚点密度（&lt;5/100词）表示可能是AI填充内容（幻觉风险）。
          </span>
        </p>

        {/* Overall Metrics */}
        {result && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className={clsx('rounded-lg p-4', getRiskColor(result.riskLevel))}>
              <div className="text-2xl font-bold">{result.riskScore}/100</div>
              <div className="text-sm">Risk Score / 风险分数</div>
            </div>
            <div className={clsx('rounded-lg p-4', getDensityColor(result.anchorDensity || 0))}>
              <div className="text-2xl font-bold">
                {(result.anchorDensity || 0).toFixed(1)}
              </div>
              <div className="text-sm">Density/100 words / 密度</div>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-700">
                {result.paragraphCount || 0}
              </div>
              <div className="text-sm text-blue-600">Paragraphs / 段落数</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-red-700">
                {result.paragraphDetails?.filter(p => (p.anchorCount || 0) < 5).length || 0}
              </div>
              <div className="text-sm text-red-600">High Risk / 高风险段落</div>
            </div>
          </div>
        )}

        {/* Density Scale Legend */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Anchor Density Scale / 锚点密度等级:</h4>
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-green-500"></div>
              <span className="text-sm">&gt;=10 (Low Risk / 低风险)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-yellow-500"></div>
              <span className="text-sm">5-10 (Medium / 中等)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-red-500"></div>
              <span className="text-sm">&lt;5 (Hallucination Risk / 幻觉风险)</span>
            </div>
          </div>
        </div>

        {/* Start Analysis / Skip Step */}
        {/* 开始分析 / 跳过此步 */}
        {documentText && !analysisStarted && !isAnalyzing && !result && (
          <div className="mt-4 p-6 bg-gray-50 border border-gray-200 rounded-lg">
            <div className="text-center">
              <Anchor className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Analyze / 准备分析</h3>
              <p className="text-gray-600 mb-6">
                Click to analyze anchor density and detect hallucination risk
                <br />
                <span className="text-gray-500">点击分析锚点密度并检测幻觉风险</span>
              </p>
              <div className="flex items-center justify-center gap-4">
                <Button variant="primary" size="lg" onClick={() => setAnalysisStarted(true)}>
                  <Sparkles className="w-5 h-5 mr-2" />
                  Start Analysis / 开始分析
                </Button>
                <Button variant="secondary" size="lg" onClick={() => setShowSkipConfirm(true)}>
                  <ArrowRight className="w-5 h-5 mr-2" />
                  Skip Step / 跳过此步
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Issues Section with Selection and Click-Expand */}
      {/* 问题部分（带选择和点击展开功能） */}
      {anchorIssues.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              Detected Issues / 检测到的问题
              <span className="text-sm font-normal text-gray-500">
                ({anchorIssues.length} issues / 问题)
              </span>
            </h3>
            <div className="flex items-center gap-3">
              {/* Select All / Deselect All buttons */}
              {/* 全选/取消全选按钮 */}
              <button
                onClick={() => {
                  const allIndices = new Set(anchorIssues.map((_, i) => i));
                  setSelectedIssueIndices(allIndices);
                }}
                className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
              >
                Select All / 全选
              </button>
              <span className="text-gray-300">|</span>
              <button
                onClick={() => setSelectedIssueIndices(new Set())}
                className="text-sm text-gray-600 hover:text-gray-800 hover:underline"
              >
                Deselect All / 取消全选
              </button>
              {hasSelectedIssues && (
                <span className="text-sm text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                  {selectedIssueIndices.size} selected / 已选
                </span>
              )}
            </div>
          </div>
          <div className="space-y-2">
            {anchorIssues.map((issue, idx) => (
              <div
                key={idx}
                className={clsx(
                  'rounded-lg border transition-all',
                  expandedIssueIndex === idx
                    ? 'bg-purple-50 border-purple-300 ring-2 ring-purple-200'
                    : selectedIssueIndices.has(idx)
                    ? 'bg-blue-50 border-blue-300'
                    : 'bg-white border-gray-200'
                )}
              >
                <div className="flex items-start gap-3 p-3">
                  {/* Checkbox button - separate click handler */}
                  {/* 复选框按钮 - 单独的点击处理器 */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleIssueSelection(idx);
                    }}
                    className={clsx(
                      'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors',
                      selectedIssueIndices.has(idx)
                        ? 'bg-blue-600 border-blue-600'
                        : 'border-gray-300 hover:border-blue-400'
                    )}
                  >
                    {selectedIssueIndices.has(idx) && (
                      <Check className="w-3 h-3 text-white" />
                    )}
                  </button>
                  {/* Content area - click to expand */}
                  {/* 内容区域 - 点击展开 */}
                  <button
                    onClick={() => handleIssueClick(idx)}
                    className="flex-1 text-left"
                  >
                    <div className="flex items-center gap-2">
                      <span className={clsx(
                        'px-2 py-0.5 rounded text-xs font-medium',
                        issue.severity === 'high' ? 'bg-red-100 text-red-700' :
                        issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-700'
                      )}>
                        {issue.severity === 'high' ? 'High / 高' :
                         issue.severity === 'medium' ? 'Medium / 中' : 'Low / 低'}
                      </span>
                      <span className="text-xs text-gray-500">{issue.layer}</span>
                      {expandedIssueIndex === idx && (
                        <span className="text-xs text-purple-600 ml-auto">Expanded / 已展开</span>
                      )}
                    </div>
                    <p className="text-gray-900 mt-1">{issue.description}</p>
                    <p className="text-gray-600 text-sm">{issue.descriptionZh}</p>
                    {issue.location && (
                      <p className="text-gray-500 text-xs mt-1 font-mono">{issue.location}</p>
                    )}
                  </button>
                </div>
                {/* Expanded content section - inline suggestion display */}
                {/* 展开内容部分 - 内联建议显示 */}
                {expandedIssueIndex === idx && (
                  <div className="border-t border-purple-200 p-3 bg-purple-50">
                    {isLoadingSuggestion ? (
                      <div className="flex items-center gap-2 text-purple-600">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Loading suggestions... / 加载建议中...</span>
                      </div>
                    ) : suggestionError ? (
                      <div className="text-red-600 text-sm">{suggestionError}</div>
                    ) : issueSuggestion ? (
                      <div className="space-y-3">
                        <div>
                          <h5 className="text-sm font-medium text-purple-800">Analysis / 分析:</h5>
                          <p className="text-purple-700 mt-1 text-sm">{issueSuggestion.analysis}</p>
                        </div>
                        {issueSuggestion.suggestions && issueSuggestion.suggestions.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium text-purple-800">Suggestions / 建议:</h5>
                            <ul className="list-disc list-inside mt-1 space-y-1">
                              {issueSuggestion.suggestions.map((s, i) => (
                                <li key={i} className="text-purple-700 text-sm">{s}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {issueSuggestion.exampleFix && (
                          <div>
                            <h5 className="text-sm font-medium text-purple-800">Example Fix / 示例修复:</h5>
                            <pre className="mt-1 p-2 bg-white rounded text-xs text-gray-800 overflow-x-auto">
                              {issueSuggestion.exampleFix}
                            </pre>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-gray-500 text-sm">No suggestion available / 暂无建议</div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons for Selected Issues */}
      {/* 选中问题的操作按钮 */}
      {hasSelectedIssues && (
        <div className="mb-6 pb-6 border-b">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">{selectedIssueIndices.size} selected / 已选择 {selectedIssueIndices.size} 个问题</div>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setMergeMode('prompt');
                  setShowMergeConfirm(true);
                }}
                disabled={selectedIssueIndices.size === 0}
              >
                <Edit3 className="w-4 h-4 mr-2" />
                Generate Prompt / 生成提示
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  setMergeMode('apply');
                  setShowMergeConfirm(true);
                }}
                disabled={selectedIssueIndices.size === 0}
              >
                <Sparkles className="w-4 h-4 mr-2" />
                AI Modify / AI修改
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Merge Confirm Dialog */}
      {/* 合并确认对话框 */}
      {showMergeConfirm && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h4 className="font-semibold text-yellow-900 mb-3">
            {mergeMode === 'prompt' ? 'Generate Modification Prompt / 生成修改提示' : 'Apply AI Modification / 应用AI修改'}
          </h4>
          <p className="text-yellow-800 text-sm mb-3">
            {mergeMode === 'prompt'
              ? 'Generate a prompt that you can use to modify the document manually / 生成一个提示，您可以用它来手动修改文档'
              : 'AI will automatically modify the document based on selected issues / AI将根据选中的问题自动修改文档'}
          </p>
          <div className="mb-3">
            <label className="block text-sm font-medium text-yellow-800 mb-1">
              Additional Notes (Optional) / 附加说明（可选）
            </label>
            <textarea
              value={mergeUserNotes}
              onChange={(e) => setMergeUserNotes(e.target.value)}
              placeholder="Add any specific instructions for modification... / 添加任何特定的修改指示..."
              className="w-full px-3 py-2 border border-yellow-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500"
              rows={2}
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant="primary"
              size="sm"
              onClick={executeMergeModify}
              disabled={isMerging}
            >
              {isMerging ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Check className="w-4 h-4 mr-2" />
              )}
              Confirm / 确认
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowMergeConfirm(false)}
            >
              <X className="w-4 h-4 mr-2" />
              Cancel / 取消
            </Button>
          </div>
        </div>
      )}

      {/* Merge Result Display */}
      {/* 合并结果展示 */}
      {mergeResult && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <h4 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            {'modifiedText' in mergeResult ? 'AI Modification Result / AI修改结果' : 'Generated Prompt / 生成的提示'}
          </h4>

          {'prompt' in mergeResult && mergeResult.prompt && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-green-800">Prompt / 提示:</h5>
              <pre className="mt-1 p-3 bg-white rounded text-sm text-gray-800 overflow-x-auto whitespace-pre-wrap">
                {mergeResult.prompt}
              </pre>
            </div>
          )}

          {'modifiedText' in mergeResult && mergeResult.modifiedText && (
            <div className="mb-3">
              {/* Modified text display - full content with scrollable area */}
              {/* 修改后内容显示 - 完整内容可滚动 */}
              <h5 className="text-sm font-medium text-green-800">
                Modified Text / 修改后的文本 ({mergeResult.modifiedText?.length || 0} 字符):
              </h5>
              <pre className="mt-1 p-3 bg-white rounded text-sm text-gray-800 overflow-x-auto whitespace-pre-wrap max-h-96 overflow-y-auto">
                {mergeResult.modifiedText}
              </pre>
            </div>
          )}

          {'changesSummaryZh' in mergeResult && mergeResult.changesSummaryZh && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-green-800">Changes Summary / 修改摘要:</h5>
              <p className="mt-1 text-green-700">{mergeResult.changesSummaryZh}</p>
            </div>
          )}

          {'modifiedText' in mergeResult && (
            <div className="flex gap-2 mt-4">
              <Button variant="primary" size="sm" onClick={handleAcceptModification}>
                <Check className="w-4 h-4 mr-2" />
                Accept / 接受
              </Button>
              <Button variant="secondary" size="sm" onClick={handleRegenerate}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Regenerate / 重新生成
              </Button>
              <Button variant="secondary" size="sm" onClick={() => setMergeResult(null)}>
                <X className="w-4 h-4 mr-2" />
                Cancel / 取消
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Paragraph Anchor Details */}
      {result && result.paragraphDetails && result.paragraphDetails.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-orange-600" />
            Paragraph Anchor Density / 段落锚点密度
          </h3>

          <div className="space-y-3">
            {result.paragraphDetails.map((para, index) => {
              // Calculate approximate density (anchors per 100 words equivalent)
              const density = para.anchorCount || 0;
              const risk_level = getDensityRiskLevel(density);

              return (
                <div
                  key={index}
                  className={clsx(
                    'border rounded-lg p-4',
                    risk_level === 'high' ? 'border-red-300 bg-red-50' :
                    risk_level === 'medium' ? 'border-yellow-300 bg-yellow-50' :
                    'border-green-300 bg-green-50'
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span className={clsx(
                        'w-8 h-8 flex items-center justify-center rounded-full font-medium flex-shrink-0',
                        risk_level === 'high' ? 'bg-red-200 text-red-700' :
                        risk_level === 'medium' ? 'bg-yellow-200 text-yellow-700' :
                        'bg-green-200 text-green-700'
                      )}>
                        {index + 1}
                      </span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-700">Paragraph {index + 1}</span>
                          <span className="text-sm text-gray-500">({para.role || 'body'})</span>
                        </div>
                        {/* Show paragraph preview - first few words */}
                        {/* 显示段落预览 - 前几个单词 */}
                        {para.preview && (
                          <p className="text-xs text-gray-500 truncate mt-0.5 italic">"{para.preview}"</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className={clsx(
                        'px-3 py-1 rounded-full text-sm font-medium',
                        getDensityColor(density)
                      )}>
                        <Anchor className="w-3 h-3 inline mr-1" />
                        {density} anchors
                      </div>
                      {risk_level === 'high' && (
                        <div className="flex items-center gap-1 text-red-600">
                          <AlertTriangle className="w-4 h-4" />
                          <span className="text-sm font-medium">Hallucination Risk</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {risk_level === 'high' && (
                    <div className="mt-2 p-2 bg-white rounded border border-red-200 text-sm text-red-700">
                      <strong>Warning:</strong> This paragraph may contain AI-generated filler content. Consider adding specific data, citations, or concrete examples.
                      <br />
                      <span className="text-red-600">警告：此段落可能包含AI填充内容。建议添加具体数据、引用或具体例子。</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Anchor Types Distribution - only show when we have actual data */}
      {/* 锚点类型分布 - 仅在有实际数据时显示 */}
      {result && (result?.details as Record<string, unknown>)?.anchor_type_distribution && (
        ((result?.details as Record<string, unknown>)?.anchor_type_distribution?.numbers ?? 0) +
        ((result?.details as Record<string, unknown>)?.anchor_type_distribution?.dates ?? 0) +
        ((result?.details as Record<string, unknown>)?.anchor_type_distribution?.names ?? 0) +
        ((result?.details as Record<string, unknown>)?.anchor_type_distribution?.citations ?? 0)
      ) > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Hash className="w-5 h-5 text-blue-600" />
            Detected Anchor Types / 检测到的锚点类型
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              {
                icon: Hash,
                label: 'Numbers',
                labelZh: '数字',
                count: (result?.details as Record<string, unknown>)?.anchor_type_distribution?.numbers ?? 0,
                example: 'e.g., 85%, 3.5'
              },
              {
                icon: FileText,
                label: 'Dates',
                labelZh: '日期',
                count: (result?.details as Record<string, unknown>)?.anchor_type_distribution?.dates ?? 0,
                example: 'e.g., 2023, March'
              },
              {
                icon: Quote,
                label: 'Names',
                labelZh: '名称',
                count: (result?.details as Record<string, unknown>)?.anchor_type_distribution?.names ?? 0,
                example: 'e.g., Dr. Smith'
              },
              {
                icon: Percent,
                label: 'Citations',
                labelZh: '引用',
                count: (result?.details as Record<string, unknown>)?.anchor_type_distribution?.citations ?? 0,
                example: 'e.g., [1], (2020)'
              },
            ].map((type, index) => (
              <div key={index} className={`p-4 rounded-lg border ${(type.count as number) > 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                <div className="flex items-center gap-2 mb-2">
                  <type.icon className={`w-5 h-5 ${(type.count as number) > 0 ? 'text-green-600' : 'text-red-500'}`} />
                  <span className="font-medium text-gray-800">{type.label}</span>
                </div>
                <div className="text-xs text-gray-500 mb-2">{type.labelZh}</div>
                <div className={`text-2xl font-bold ${(type.count as number) > 0 ? 'text-green-600' : 'text-red-500'}`}>
                  {type.count as number}
                </div>
                <div className="text-xs text-gray-400 mt-1">{type.example}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
            <strong>Total Anchors:</strong> {
              ((result?.details as Record<string, unknown>)?.anchor_type_distribution?.numbers ?? 0) +
              ((result?.details as Record<string, unknown>)?.anchor_type_distribution?.dates ?? 0) +
              ((result?.details as Record<string, unknown>)?.anchor_type_distribution?.names ?? 0) +
              ((result?.details as Record<string, unknown>)?.anchor_type_distribution?.citations ?? 0)
            } |
            <strong> Target:</strong> ≥5 per 100 words for low AI risk
          </div>
        </div>
      )}

      {/* No issues message - only show when risk is actually low */}
      {/* 无问题消息 - 仅当风险实际较低时显示 */}
      {anchorIssues.length === 0 && result && result.riskLevel === 'low' && (result.anchorDensity === undefined || result.anchorDensity >= 5) && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-green-800">
              Anchor Density Looks Good
            </h3>
            <p className="text-green-600 mt-1">
              锚点密度良好。段落包含充足的学术锚点（引用、数据、具体细节）。
            </p>
          </div>
        </div>
      )}

      {/* High risk warning when no detailed issues but risk score is high */}
      {/* 当没有详细问题但风险分数高时显示警告 */}
      {anchorIssues.length === 0 && result && (result.riskLevel === 'high' || result.riskLevel === 'medium' || (result.anchorDensity !== undefined && result.anchorDensity < 5)) && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-yellow-800">
              Low Anchor Density Detected / 检测到低锚点密度
            </h3>
            <p className="text-yellow-600 mt-1">
              The document appears to lack specific anchors (citations, data, statistics, proper nouns).
              This may indicate generic or AI-generated content. Consider adding more specific details.
            </p>
            <p className="text-yellow-600 mt-1">
              文档似乎缺少具体的锚点（引用、数据、统计数字、专有名词）。
              这可能表示内容过于笼统或由AI生成。建议添加更多具体细节。
            </p>
          </div>
        </div>
      )}

      {/* Document Modification Section */}
      {/* 文档修改部分 */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Document Modification / 文档修改
        </h3>
        <p className="text-gray-600 text-sm mb-4">
          Upload a modified file or paste modified text to continue to the next step.
          上传修改后的文件或粘贴修改后的文本以继续下一步。
        </p>

        {/* Mode Toggle */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setModifyMode('file')}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              modifyMode === 'file'
                ? 'bg-blue-600 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            )}
          >
            <Upload className="w-4 h-4 inline mr-2" />
            Upload File / 上传文件
          </button>
          <button
            onClick={() => setModifyMode('text')}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              modifyMode === 'text'
                ? 'bg-blue-600 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            )}
          >
            <Edit3 className="w-4 h-4 inline mr-2" />
            Input Text / 输入文本
          </button>
        </div>

        {/* File Upload Mode */}
        {modifyMode === 'file' && (
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md,.doc,.docx"
              onChange={handleFileSelect}
              className="hidden"
            />
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
            >
              <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">
                {newFile ? newFile.name : 'Click to select file / 点击选择文件'}
              </p>
              <p className="text-gray-400 text-sm mt-1">
                Supported: .txt, .md, .doc, .docx
              </p>
            </div>
          </div>
        )}

        {/* Text Input Mode */}
        {modifyMode === 'text' && (
          <div>
            <textarea
              value={newText}
              onChange={(e) => setNewText(e.target.value)}
              placeholder="Paste modified text here... / 在此粘贴修改后的文本..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-[200px]"
            />
            <p className="text-gray-500 text-sm mt-1">
              {newText.length} characters / 字符
            </p>
          </div>
        )}

        {/* Apply and Continue Button */}
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            {modifyMode === 'file'
              ? (newFile ? 'File selected, ready to apply / 文件已选择，可以应用' : 'Please select a file first / 请先选择文件')
              : (newText.trim() ? 'Content entered, ready to apply / 内容已输入，可以应用' : 'Please enter content first / 请先输入内容')}
          </p>
          <Button
            variant="primary"
            onClick={handleConfirmModify}
            disabled={isUploading || (modifyMode === 'file' && !newFile) || (modifyMode === 'text' && !newText.trim())}
          >
            {isUploading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <ArrowRight className="w-4 h-4 mr-2" />
            )}
            Apply and Continue / 应用并继续
          </Button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        )}
      </div>

      {/* Recommendations */}
      {result && result.recommendations && result.recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            Recommendations / 建议
          </h3>
          <ul className="space-y-2">
            {result.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-green-500 mt-1">-</span>
                <div>
                  <p className="text-gray-700">{rec}</p>
                  {result.recommendationsZh && result.recommendationsZh[index] && (
                    <p className="text-gray-500 text-sm">{result.recommendationsZh[index]}</p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Skip Confirmation Dialog */}
      {/* 跳过确认对话框 */}
      {showSkipConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl">
            <div className="flex items-start gap-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-yellow-600 flex-shrink-0" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Skip without modifying? / 跳过不修改？
                </h3>
                <p className="text-gray-600 mt-2">
                  You have not applied any modifications on this page. Are you sure you want to skip to the next step?
                </p>
                <p className="text-gray-600 mt-1">
                  您尚未在此页面应用任何修改。确定要跳过到下一步吗？
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <Button
                variant="secondary"
                onClick={() => setShowSkipConfirm(false)}
              >
                Cancel / 取消
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  setShowSkipConfirm(false);
                  goToNextStep();
                }}
              >
                Confirm Skip / 确认跳过
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Data/Citation Warning Dialog */}
      {/* 数据/引用警告对话框 */}
      {showDataWarning && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full flex flex-col max-h-[90vh]">
            {/* Fixed Header */}
            <div className="flex items-center gap-3 p-4 border-b bg-red-50 rounded-t-lg">
              <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0" />
              <h3 className="text-lg font-bold text-red-700">
                Warning / 警告
              </h3>
            </div>

            {/* Scrollable Content */}
            <div className="overflow-y-auto flex-1 p-4 space-y-3">
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-700">
                  <strong>Hallucination Risk / 幻觉风险:</strong> AI may generate fabricated citations and data. / AI可能生成虚假引用和数据。
                </p>
              </div>

              <div className="bg-purple-50 border border-purple-300 rounded-lg p-3">
                <p className="text-sm text-purple-800 font-medium">
                  <strong>Use tools like NotebookLM, Elicit, Consensus</strong> for accurate citations.
                </p>
                <p className="text-sm text-purple-700 mt-1">
                  建议使用 NotebookLM、Elicit、Consensus 等工具获取准确引用。
                </p>
                <p className="text-sm text-purple-900 font-bold mt-2 border-t border-purple-200 pt-2">
                  Rewrites are EXAMPLES only. Do NOT adopt directly! / 改写仅供参考，不建议直接采纳！
                </p>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-sm font-semibold text-yellow-800 mb-1">You Must / 您必须:</p>
                <ul className="text-xs text-yellow-700 space-y-0.5 list-disc list-inside">
                  <li>Verify ALL data & citations / 核实所有数据和引用</li>
                  <li>Replace placeholders with real data / 用真实数据替换占位符</li>
                  <li>Never submit unverified content / 不要提交未核实内容</li>
                </ul>
              </div>

              <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                <p className="text-sm font-semibold text-orange-800 mb-1">Placeholders / 占位符:</p>
                <div className="text-xs text-orange-700 font-mono grid grid-cols-2 gap-1">
                  <span><code className="bg-orange-100 px-1 rounded">[AUTHOR_XXXXX]</code></span>
                  <span><code className="bg-orange-100 px-1 rounded">[DATA_XX%]</code></span>
                  <span><code className="bg-orange-100 px-1 rounded">[YEAR_XXXX]</code></span>
                  <span><code className="bg-orange-100 px-1 rounded">[N=XXXX]</code></span>
                </div>
                <p className="text-xs text-orange-600 font-semibold mt-1">Search "XXXXX" to find all! / 搜索"XXXXX"找到所有占位符！</p>
              </div>
            </div>

            {/* Fixed Footer */}
            <div className="flex justify-end gap-3 p-4 border-t bg-gray-50 rounded-b-lg">
              <Button
                variant="secondary"
                onClick={() => {
                  setShowDataWarning(false);
                  setDataWarningAction(null);
                }}
              >
                Cancel / 取消
              </Button>
              <Button
                variant="primary"
                className="bg-red-600 hover:bg-red-700"
                onClick={handleDataWarningConfirm}
              >
                I Understand / 我理解
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      {showNavigation && (
        <div className="flex justify-between items-center pt-4 border-t">
          <Button variant="outline" onClick={goToPreviousStep} className="flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Previous: Step 3.2
          </Button>
          <Button onClick={() => setShowSkipConfirm(true)} disabled={!result} className="flex items-center gap-2">
            Skip and Continue / 跳过并继续
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
