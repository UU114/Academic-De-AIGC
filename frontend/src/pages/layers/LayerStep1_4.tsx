import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Layers,
  AlertTriangle,
  RefreshCw,
  BarChart3,
  Sparkles,
  Upload,
  FileText,
  Check,
  X,
  Edit3,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import {
  documentLayerApi,
  ConnectorAnalysisResponse,
  DetectionIssue,
  IssueSuggestionResponse,
  ModifyPromptResponse,
  ApplyModifyResponse,
} from '../../services/analysisApi';
import { useSubstepStateStore } from '../../stores/substepStateStore';

/**
 * Layer Step 1.4 - Connector & Transition Analysis
 * 步骤 1.4 - 连接词与衔接分析
 *
 * Detects:
 * - H: Explicit Connector Overuse (显性连接词过度使用)
 * - I: Missing Semantic Echo (缺乏语义回声)
 * - J: Logic Break Points (逻辑断裂点)
 *
 * Priority: ★★☆☆☆ (Depends on paragraph structure being stable)
 * 优先级: ★★☆☆☆ (依赖段落结构稳定)
 *
 * Uses LLM to analyze paragraph transitions for AI-like patterns.
 * 使用LLM分析段落过渡中的AI风格模式。
 */


interface LayerStep1_4Props {
  documentIdProp?: string;
  onComplete?: (result: ConnectorAnalysisResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep1_4({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep1_4Props) {
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
      sessionApi.updateStep(sessionId, 'layer5-step1-4').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<ConnectorAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedParagraphIndex, setExpandedParagraphIndex] = useState<number | null>(null);

  // Issues derived from analysis result
  // 从分析结果派生的问题列表
  const [lengthIssues, setLengthIssues] = useState<DetectionIssue[]>([]);

  // Issue selection for merge modify
  // 用于合并修改的问题选择
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());

  // Expanded issue index for showing details
  // 展开的问题索引，用于显示详情
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

  // Issue suggestion state (LLM-based detailed suggestions)
  // 问题建议状态（基于LLM的详细建议）
  const [issueSuggestion, setIssueSuggestion] = useState<IssueSuggestionResponse | null>(null);
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);

  // Merge modify state
  // 合并修改状态
  const [showMergeConfirm, setShowMergeConfirm] = useState(false);
  const [mergeMode, setMergeMode] = useState<'prompt' | 'apply'>('prompt');
  const [mergeUserNotes, setMergeUserNotes] = useState('');
  const [isMerging, setIsMerging] = useState(false);
  const [mergeResult, setMergeResult] = useState<ModifyPromptResponse | ApplyModifyResponse | null>(null);

  // Skip confirmation state
  // 跳过确认状态
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);

  // Data/Citation warning state for placeholder verification
  // 数据/引用警告状态，用于占位符验证
  const [showDataWarning, setShowDataWarning] = useState(false);
  const [dataWarningAction, setDataWarningAction] = useState<'prompt' | 'apply' | 'accept' | 'continue' | null>(null);

  // Document modification state
  // 文档修改状态
  const [modifyMode, setModifyMode] = useState<'file' | 'text'>('file');
  const [newFile, setNewFile] = useState<File | null>(null);
  const [newText, setNewText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isAnalyzingRef = useRef(false);

  // ============================================
  // NEW CODE - Get substep state store reference for checking previous steps' modifiedText
  // 新代码 - 获取子步骤状态存储引用用于检查前序步骤的修改后文本
  // ============================================
  const substepStore = useSubstepStateStore();
  // ============================================

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
  }, [documentId, sessionFetchAttempted, sessionId, substepStore]);

  const loadDocumentText = async (docId: string) => {
    try {
      // ============================================
      // NEW CODE - Check previous steps' modifiedText from substep store
      // 新代码 - 从子步骤存储检查前序步骤的修改后文本
      // ============================================
      if (sessionId && substepStore.currentSessionId !== sessionId) {
        await substepStore.initForSession(sessionId);
      }

      // Check previous steps for modified text (step5-3, step5-2, step5-1 for LayerStep1_4)
      // 检查前序步骤的修改后文本（LayerStep1_4检查step5-3, step5-2, step5-1）
      const previousSteps = ['step5-3', 'step5-2', 'step5-1'];
      let foundModifiedText: string | null = null;

      for (const stepName of previousSteps) {
        const stepState = substepStore.getState(stepName);
        if (stepState?.modifiedText) {
          console.log(`[LayerStep1_4] Using modified text from ${stepName}`);
          foundModifiedText = stepState.modifiedText;
          break;
        }
      }

      if (foundModifiedText) {
        setDocumentText(foundModifiedText);
        setIsLoading(false);
        return;
      }
      // ============================================

      const doc = await documentApi.get(docId);
      // Fallback to originalText if no modified text found in substep store
      // 如果子步骤存储中没有修改后的文本，则回退到originalText
      if (doc.originalText) {
        setDocumentText(doc.originalText);
      } else {
        setError('Document text not found / 未找到文档文本');
      }
    } catch (err) {
      console.error('Failed to load document:', err);
      setError('Failed to load document / 加载文档失败');
    } finally {
      setIsLoading(false);
    }
  };

  // Run analysis when user clicks start
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
      // Call connector analysis API (LLM-based)
      // 调用连接词分析API（基于LLM）
      const analysisResult = await documentLayerApi.analyzeConnectors(documentText, sessionId || undefined);
      setResult(analysisResult);

      // Use issues directly from LLM analysis result
      // 直接使用LLM分析结果中的问题列表
      const issues: DetectionIssue[] = analysisResult.issues || [];

      // Add overall connector density issue if too high
      // 如果连接词密度过高，添加整体问题
      const hasConnectorIssue = analysisResult.connectorDensity > 0.3 || analysisResult.totalExplicitConnectors > 5;
      if (hasConnectorIssue && !issues.some(i => i.type === 'explicit_connector_overuse')) {
        issues.unshift({
          type: 'explicit_connector_overuse',
          description: `High explicit connector density (${(analysisResult.connectorDensity * 100).toFixed(1)}%, ${analysisResult.totalExplicitConnectors} connectors)`,
          descriptionZh: `显性连接词密度过高 (${(analysisResult.connectorDensity * 100).toFixed(1)}%, ${analysisResult.totalExplicitConnectors}个连接词)`,
          severity: 'high',
          layer: 'document',
        });
      }

      setLengthIssues(issues);

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

  // Load suggestion for a specific issue (LLM-based)
  // 为特定问题加载建议（基于LLM）
  const loadIssueSuggestion = useCallback(async (index: number) => {
    const issue = lengthIssues[index];
    if (!issue || !documentId) return;

    setIsLoadingSuggestion(true);
    setIssueSuggestion(null);
    setSuggestionError(null);

    try {
      // Call LLM to get detailed suggestion for this specific issue
      // 调用LLM获取此特定问题的详细建议
      const suggestion = await documentLayerApi.getIssueSuggestion(documentId, issue, false);
      setIssueSuggestion(suggestion);
    } catch (err) {
      console.error('Failed to load issue suggestion:', err);
      setSuggestionError('Failed to load detailed suggestion / 加载详细建议失败');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [lengthIssues, documentId]);

  // Handle issue click - toggle expand and load LLM suggestion
  // 处理问题点击 - 切换展开并加载LLM建议
  const handleIssueClick = useCallback(async (index: number) => {
    const issue = lengthIssues[index];
    if (!issue || !documentId) return;

    // Collapse if already expanded
    // 如果已展开则折叠
    if (expandedIssueIndex === index) {
      setExpandedIssueIndex(null);
      setIssueSuggestion(null);
      return;
    }

    // Expand and load LLM suggestion
    // 展开并加载LLM建议
    setExpandedIssueIndex(index);
    await loadIssueSuggestion(index);
  }, [lengthIssues, documentId, expandedIssueIndex, loadIssueSuggestion]);

  // Handle issue checkbox selection (for merge modify)
  // 处理问题复选框选择（用于合并修改）
  const handleIssueSelect = useCallback((index: number, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering expand
    setSelectedIssueIndices(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  }, []);

  // Select all issues
  // 全选所有问题
  const selectAllIssues = useCallback(() => {
    setSelectedIssueIndices(new Set(lengthIssues.map((_, idx) => idx)));
  }, [lengthIssues]);

  // Deselect all issues
  // 取消全选所有问题
  const deselectAllIssues = useCallback(() => {
    setSelectedIssueIndices(new Set());
  }, []);

  // Check if selected issues involve adding data/citations/references
  // 检查选中的问题是否涉及添加数据/引用/参考文献
  const hasDataRelatedIssues = useCallback(() => {
    const selectedIssues = Array.from(selectedIssueIndices).map(i => lengthIssues[i]);
    const dataRelatedTypes = [
      'low_anchor_density', 'low_density', 'no_anchors', 'very_low_anchor_density',
      'suspected_hallucination', 'missing_evidence', 'abstract_claims'
    ];
    const dataRelatedKeywords = [
      'anchor', 'citation', 'data', 'reference', 'statistic', 'number', 'evidence',
      'measurement', 'concrete', 'abstract', 'claims', 'support',
      '引用', '数据', '锚点', '统计', '证据', '测量', '具体', '抽象', '主张', '支持'
    ];

    return selectedIssues.some(issue => {
      // Check issue type
      if (dataRelatedTypes.includes(issue.type)) return true;
      // Check description for keywords
      const desc = (issue.description + ' ' + (issue.descriptionZh || '')).toLowerCase();
      return dataRelatedKeywords.some(keyword => desc.includes(keyword.toLowerCase()));
    });
  }, [selectedIssueIndices, lengthIssues]);

  // Actual merge modify execution (without warning check)
  // 实际合并修改执行（不检查警告）
  const executeActualMergeModify = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentText) return;

    setIsMerging(true);
    setShowMergeConfirm(false);
    setShowDataWarning(false);
    setDataWarningAction(null);

    try {
      const selectedIssues = Array.from(selectedIssueIndices).map(i => lengthIssues[i]);

      if (mergeMode === 'prompt') {
        // Generate prompt only
        // 仅生成提示
        const response = await documentLayerApi.generateModifyPrompt(
          documentId!,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult(response);
      } else {
        // Apply modification directly
        // 直接应用修改
        const response = await documentLayerApi.applyModify(
          documentId!,
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
  }, [selectedIssueIndices, documentId, documentText, lengthIssues, mergeMode, mergeUserNotes, sessionId]);

  // Execute merge modify (wrapper that checks for data warning)
  // 执行合并修改（检查数据警告的包装函数）
  const executeMergeModify = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentText) return;

    if (hasDataRelatedIssues()) {
      setDataWarningAction(mergeMode);
      setShowDataWarning(true);
    } else {
      executeActualMergeModify();
    }
  }, [selectedIssueIndices, documentText, hasDataRelatedIssues, mergeMode, executeActualMergeModify]);

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

  // Handle data warning confirmation (defined after executeActualConfirmModify)
  // 处理数据警告确认（定义在 executeActualConfirmModify 之后）

  // Handle regenerate (retry AI modification)
  // 处理重新生成（重试AI修改）
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

  // Check if text contains unverified placeholders
  // 检查文本是否包含未验证的占位符
  const hasUnverifiedPlaceholders = useCallback((text: string) => {
    const placeholderPatterns = [
      /\[AUTHOR_X+.*?\]/gi,
      /\[YEAR_X+\]/gi,
      /\[X+\]%/gi,
      /\[X+\]/gi,
      /p\s*[<>=]\s*\[X+\.?X*\]/gi,
      /\[AUTHOR.*?,\s*YEAR.*?\]/gi,
      /\[\d*X+\d*\]/gi,
    ];
    return placeholderPatterns.some(pattern => pattern.test(text));
  }, []);

  // Actual confirm modification and navigate (without warning check)
  // 实际确认修改并导航（不检查警告）
  const executeActualConfirmModify = useCallback(async () => {
    setIsUploading(true);
    setError(null);
    setShowDataWarning(false);
    setDataWarningAction(null);

    try {
      let newDocId: string;

      if (modifyMode === 'file' && newFile) {
        // Upload new file
        // 上传新文件
        const result = await documentApi.upload(newFile);
        newDocId = result.documentId;
      } else if (modifyMode === 'text' && newText.trim()) {
        // Upload text as document
        // 将文本作为文档上传
        const result = await documentApi.uploadText(newText, `step1_4_modified_${Date.now()}.txt`);
        newDocId = result.documentId;
      } else {
        setError('Please select a file or enter text / 请选择文件或输入文本');
        setIsUploading(false);
        return;
      }

      // Navigate to next step with new document
      // 使用新文档导航到下一步
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer5-step1-5/${newDocId}?${params.toString()}`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload modified document / 上传修改后的文档失败');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate]);

  // Handle confirm modification (with placeholder warning check)
  // 处理确认修改（带占位符警告检查）
  const handleConfirmModify = useCallback(async () => {
    // Check if text mode has unverified placeholders
    // 检查文本模式是否有未验证的占位符
    if (modifyMode === 'text' && newText.trim() && hasUnverifiedPlaceholders(newText)) {
      setDataWarningAction('continue');
      setShowDataWarning(true);
      return;
    }

    // Check if data-related issues were selected (may have placeholders in modified text)
    // 检查是否选择了数据相关问题（修改后的文本中可能有占位符）
    if (hasDataRelatedIssues() && modifyMode === 'text' && newText.trim()) {
      setDataWarningAction('continue');
      setShowDataWarning(true);
      return;
    }

    // No warning needed, proceed directly
    // 无需警告，直接执行
    setIsUploading(true);
    setError(null);

    try {
      // ============================================
      // NEW CODE - Save modified text to substep store
      // 新代码 - 保存修改后的文本到子步骤存储
      // ============================================
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

      if (sessionId && modifiedText) {
        await substepStore.saveModifiedText('step5-4', modifiedText);
        await substepStore.markCompleted('step5-4');
        console.log('[LayerStep1_4] Saved modified text to substep store');
      }
      // ============================================

      let newDocId: string;

      if (modifyMode === 'file' && newFile) {
        // Upload new file
        // 上传新文件
        const result = await documentApi.upload(newFile);
        newDocId = result.documentId;
      } else {
        // Upload text as document
        // 将文本作为文档上传
        const result = await documentApi.uploadText(newText, `step1_4_modified_${Date.now()}.txt`);
        newDocId = result.documentId;
      }

      // Navigate to next step with new document (use documentId from URL/props)
      // 导航到下一步（使用URL/props中的documentId）
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer5-step1-5/${documentId}?${params.toString()}`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload modified document / 上传修改后的文档失败');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate, hasUnverifiedPlaceholders, hasDataRelatedIssues, documentId, substepStore]);

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
      // User confirmed to continue with unverified placeholders
      // 用户确认继续使用未验证的占位符
      executeActualConfirmModify();
    }
    setDataWarningAction(null);
  }, [dataWarningAction, executeActualMergeModify, executeActualAcceptModification, executeActualConfirmModify]);

  // Navigation
  const handleBack = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer5-step1-3/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer5-step1-5/${documentId}?${params.toString()}`);
  };

  const toggleParagraph = (index: number) => {
    setExpandedParagraphIndex(expandedParagraphIndex === index ? null : index);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage category="paragraph" centered />
      </div>
    );
  }

  // Error state
  if (error && !result) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-red-800">Error / 错误</h3>
            <p className="text-red-600 mt-1">{error}</p>
            <Button
              variant="secondary"
              size="sm"
              className="mt-3"
              onClick={() => {
                setError(null);
                isAnalyzingRef.current = false;
                runAnalysis();
              }}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry / 重试
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const hasConnectorIssue = (result?.connectorDensity || 0) > 0.3 || (result?.totalExplicitConnectors || 0) > 5;
  const hasSelectedIssues = selectedIssueIndices.size > 0;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Loading Overlay for LLM operations */}
      {/* LLM操作加载遮罩 */}
      <LoadingOverlay
        isVisible={isMerging}
        operationType={mergeMode}
        issueCount={selectedIssueIndices.size}
      />

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Layers className="w-4 h-4" />
          <span>Layer 5 / 第5层</span>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Step 1.4 连接词与衔接</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Connector & Transition Analysis
        </h1>
        <p className="text-gray-600 mt-1">
          连接词与衔接分析 - 使用LLM检测显性连接词、语义回声和逻辑断裂点
        </p>
      </div>

      {/* Start Analysis / Skip Step */}
      {documentText && !analysisStarted && !isAnalyzing && !result && (
        <div className="mb-6 p-6 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="text-center">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Analyze / 准备分析</h3>
            <p className="text-gray-600 mb-6">
              Click "Start Analysis" to detect connectors and transitions, or skip this step.
              <br />点击"开始分析"检测连接词与衔接模式，或跳过此步骤。
            </p>
            <div className="flex items-center justify-center gap-4">
              <Button variant="primary" size="lg" onClick={() => setAnalysisStarted(true)}>
                <Sparkles className="w-5 h-5 mr-2" />Start Analysis / 开始分析
              </Button>
              <Button variant="secondary" size="lg" onClick={handleNext}>
                <ArrowRight className="w-5 h-5 mr-2" />Skip Step / 跳过此步
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing connectors and transitions... / 分析连接词与衔接中...</p>
              <p className="text-blue-600 text-sm">Using LLM to detect AI-like transition patterns / 使用LLM检测AI风格过渡模式</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* Connector Analysis Summary */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Smoothness Score */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasConnectorIssue ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className={clsx('w-5 h-5', hasConnectorIssue ? 'text-red-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Smoothness Score / 平滑度</span>
              </div>
              <div className={clsx(
                'text-3xl font-bold',
                hasConnectorIssue ? 'text-red-600' : 'text-green-600'
              )}>
                {result.overallSmoothnessScore || 0}
              </div>
              <p className={clsx(
                'text-sm mt-1',
                hasConnectorIssue ? 'text-red-600' : 'text-green-600'
              )}>
                {hasConnectorIssue ? 'High risk / 高风险' : 'Natural transitions / 自然过渡'}
              </p>
            </div>

            {/* Explicit Connectors Count */}
            <div className={clsx(
              'p-4 rounded-lg border',
              (result.totalExplicitConnectors || 0) > 5 ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <span className="font-medium text-gray-900">Explicit Connectors / 显性连接词</span>
              </div>
              <div className={clsx(
                'text-3xl font-bold',
                (result.totalExplicitConnectors || 0) > 5 ? 'text-yellow-600' : 'text-gray-700'
              )}>
                {result.totalExplicitConnectors || 0}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {(result.connectorDensity * 100).toFixed(1)}% density / 密度
              </p>
            </div>

            {/* Total Transitions */}
            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-medium text-gray-900">Transitions Analyzed / 过渡分析</span>
              </div>
              <div className="text-3xl font-bold text-gray-700">
                {result.totalTransitions || 0}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {result.problematicTransitions || 0} problematic / 有问题的
              </p>
            </div>
          </div>

          {/* Risk Alert */}
          {hasConnectorIssue && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Excessive Explicit Connectors Detected
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：检测到过多显性连接词。AI生成文本常使用"Furthermore"、"Moreover"等显性连接词。
                  建议使用语义回声（引用上段关键概念）替代显性连接词，使过渡更自然。
                </p>
              </div>
            </div>
          )}

          {/* Issues Section with Selection */}
          {/* 问题部分（带选择功能） */}
          {lengthIssues.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                  Detected Issues / 检测到的问题
                  <span className="text-sm font-normal text-gray-500">
                    ({selectedIssueIndices.size}/{lengthIssues.length} selected / 已选择)
                  </span>
                </h3>
                <div className="flex items-center gap-2">
                  {/* Select All / Deselect All buttons */}
                  {/* 全选/取消全选按钮 */}
                  <Button variant="secondary" size="sm" onClick={selectAllIssues}>
                    Select All / 全选
                  </Button>
                  <Button variant="secondary" size="sm" onClick={deselectAllIssues}>
                    Deselect All / 取消全选
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                {lengthIssues.map((issue, idx) => {
                  const isExpanded = expandedIssueIndex === idx;
                  const hasDetails = issue.suggestion || issue.suggestionZh || issue.details || issue.position;

                  return (
                    <div
                      key={idx}
                      className={clsx(
                        'rounded-lg border transition-all overflow-hidden',
                        selectedIssueIndices.has(idx)
                          ? 'bg-blue-50 border-blue-300 ring-2 ring-blue-200'
                          : 'bg-white border-gray-200'
                      )}
                    >
                      {/* Issue header - clickable for expand with LLM suggestion */}
                      {/* 问题头部 - 点击展开并加载LLM建议 */}
                      <div className="flex items-start gap-3 p-3">
                        {/* Checkbox for selection (for merge modify) */}
                        {/* 选择复选框（用于合并修改） */}
                        <button
                          onClick={(e) => handleIssueSelect(idx, e)}
                          className={clsx(
                            'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5',
                            selectedIssueIndices.has(idx)
                              ? 'bg-blue-600 border-blue-600'
                              : 'border-gray-300 hover:border-gray-400'
                          )}
                        >
                          {selectedIssueIndices.has(idx) && (
                            <Check className="w-3 h-3 text-white" />
                          )}
                        </button>

                        {/* Issue content - clickable to expand and load LLM suggestion */}
                        {/* 问题内容 - 点击展开并加载LLM建议 */}
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
                          </div>
                          <p className="text-gray-900 mt-1">{issue.description}</p>
                          <p className="text-gray-600 text-sm">{issue.descriptionZh}</p>
                        </button>

                        {/* Expand/Collapse icon */}
                        {/* 展开/折叠图标 */}
                        <button
                          onClick={() => handleIssueClick(idx)}
                          className="flex-shrink-0 p-1 hover:bg-gray-100 rounded"
                        >
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400" />
                          )}
                        </button>
                      </div>

                      {/* Expanded details section - shows LLM suggestion */}
                      {/* 展开的详情部分 - 显示LLM建议 */}
                      {isExpanded && (
                        <div className="px-4 py-3 bg-gray-50 border-t space-y-3">
                          {/* Loading state */}
                          {/* 加载中状态 */}
                          {isLoadingSuggestion && (
                            <div className="flex items-center justify-center py-4">
                              <Loader2 className="w-6 h-6 animate-spin text-blue-500 mr-2" />
                              <span className="text-gray-600">Loading LLM analysis... / 加载LLM分析中...</span>
                            </div>
                          )}

                          {/* Error state */}
                          {/* 错误状态 */}
                          {suggestionError && !isLoadingSuggestion && (
                            <div className="flex items-center gap-2 text-red-600 bg-red-50 px-3 py-2 rounded">
                              <AlertTriangle className="w-4 h-4" />
                              <span className="text-sm">{suggestionError}</span>
                              <button
                                onClick={() => loadIssueSuggestion(idx)}
                                className="ml-auto text-sm text-blue-600 hover:underline"
                              >
                                Retry / 重试
                              </button>
                            </div>
                          )}

                          {/* LLM Suggestion content */}
                          {/* LLM建议内容 */}
                          {issueSuggestion && !isLoadingSuggestion && (
                            <>
                              {/* Diagnosis */}
                              {/* 诊断 */}
                              {issueSuggestion.diagnosisZh && (
                                <div>
                                  <h5 className="text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                                    <Sparkles className="w-4 h-4 text-yellow-500" />
                                    LLM Analysis / LLM分析
                                  </h5>
                                  <p className="text-sm text-gray-700 bg-white px-3 py-2 rounded border">
                                    {issueSuggestion.diagnosisZh}
                                  </p>
                                </div>
                              )}

                              {/* Strategies */}
                              {/* 修改策略 */}
                              {issueSuggestion.strategies && issueSuggestion.strategies.length > 0 && (
                                <div>
                                  <h5 className="text-sm font-medium text-gray-700 mb-2">
                                    Modification Strategies / 修改策略
                                  </h5>
                                  <div className="space-y-2">
                                    {issueSuggestion.strategies.map((strategy, strategyIdx) => (
                                      <div key={strategyIdx} className="bg-white rounded border p-3">
                                        <div className="flex items-center justify-between mb-1">
                                          <span className="font-medium text-sm text-gray-800">
                                            {strategy.nameZh}
                                          </span>
                                          <div className="flex items-center gap-2">
                                            <span className={clsx(
                                              'text-xs px-2 py-0.5 rounded',
                                              strategy.difficulty === 'high' ? 'bg-red-100 text-red-700' :
                                              strategy.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                              'bg-green-100 text-green-700'
                                            )}>
                                              {strategy.difficulty === 'high' ? 'Hard / 难' :
                                               strategy.difficulty === 'medium' ? 'Medium / 中' : 'Easy / 易'}
                                            </span>
                                            <span className="text-xs text-gray-500">
                                              {strategy.effectiveness}% effective
                                            </span>
                                          </div>
                                        </div>
                                        <p className="text-sm text-gray-600">{strategy.descriptionZh}</p>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Priority Tips */}
                              {/* 优先提示 */}
                              {issueSuggestion.priorityTipsZh && issueSuggestion.priorityTipsZh.length > 0 && (
                                <div>
                                  <h5 className="text-sm font-medium text-gray-700 mb-1">
                                    Tips / 提示
                                  </h5>
                                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                                    {issueSuggestion.priorityTipsZh.map((tip, tipIdx) => (
                                      <li key={tipIdx}>{tip}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Caution */}
                              {/* 注意事项 */}
                              {issueSuggestion.cautionZh && (
                                <div className="bg-yellow-50 border border-yellow-200 rounded px-3 py-2">
                                  <p className="text-sm text-yellow-800">
                                    <span className="font-medium">Caution / 注意:</span> {issueSuggestion.cautionZh}
                                  </p>
                                </div>
                              )}
                            </>
                          )}

                          {/* Fallback: show basic issue info if no LLM suggestion yet */}
                          {/* 后备：如果还没有LLM建议则显示基本问题信息 */}
                          {!issueSuggestion && !isLoadingSuggestion && !suggestionError && (
                            <>
                              {issue.position && (
                                <div>
                                  <h5 className="text-sm font-medium text-gray-700 mb-1">Position / 位置</h5>
                                  <p className="text-sm text-gray-600 font-mono bg-white px-2 py-1 rounded">{issue.position}</p>
                                </div>
                              )}
                              {(issue.suggestion || issue.suggestionZh) && (
                                <div>
                                  <h5 className="text-sm font-medium text-gray-700 mb-1">Suggestion / 建议</h5>
                                  {issue.suggestion && <p className="text-sm text-gray-600">{issue.suggestion}</p>}
                                  {issue.suggestionZh && <p className="text-sm text-gray-500">{issue.suggestionZh}</p>}
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Action Buttons for Selected Issues */}
          {/* 选中问题的操作按钮 */}
          {lengthIssues.length > 0 && (
            <div className="mb-6 pb-6 border-b">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  {selectedIssueIndices.size} selected / 已选择 {selectedIssueIndices.size} 个问题
                </div>
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
            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
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
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
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

              {'changesSummary' in mergeResult && mergeResult.changesSummary && (
                <div className="mb-3">
                  <h5 className="text-sm font-medium text-green-800">Changes Summary / 修改摘要:</h5>
                  <p className="mt-1 text-green-700">{mergeResult.changesSummary}</p>
                </div>
              )}

              {/* Action buttons for merge result */}
              {/* 合并结果的操作按钮 */}
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

          {/* Connector List */}
          {result.connectorList && result.connectorList.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Detected Connectors / 检测到的连接词
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.connectorList.map((connector, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-yellow-50 border border-yellow-200 rounded-full text-sm text-yellow-700"
                  >
                    {connector}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Transition Analysis */}
          {result.transitions && result.transitions.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Transition Analysis / 过渡分析
              </h3>
              <div className="space-y-2">
                {result.transitions.map((trans, idx) => {
                  const isExpanded = expandedParagraphIndex === idx;
                  const hasIssues = trans.issues && trans.issues.length > 0;

                  return (
                    <div
                      key={idx}
                      className="bg-white border rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => toggleParagraph(idx)}
                        className="w-full px-4 py-3 flex items-center gap-4 hover:bg-gray-50 transition-colors"
                      >
                        {/* Index */}
                        <span className={clsx(
                          'w-8 h-8 flex items-center justify-center rounded-full text-sm font-medium flex-shrink-0',
                          hasIssues ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600'
                        )}>
                          {idx + 1}
                        </span>

                        {/* Transition description */}
                        <div className="flex-1 text-left">
                          <p className="text-sm text-gray-900">
                            Para {trans.paraAIndex + 1} → Para {trans.paraBIndex + 1}
                          </p>
                          {trans.explicitConnectors && trans.explicitConnectors.length > 0 && (
                            <p className="text-xs text-yellow-600 mt-0.5">
                              Connectors: {trans.explicitConnectors.join(', ')}
                            </p>
                          )}
                        </div>

                        {/* Smoothness score */}
                        <span className={clsx(
                          'text-sm w-16 text-right',
                          trans.riskLevel === 'high' ? 'text-red-600' :
                          trans.riskLevel === 'medium' ? 'text-yellow-600' : 'text-green-600'
                        )}>
                          {trans.smoothnessScore}
                        </span>

                        {/* Expand icon */}
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                        )}
                      </button>

                      {isExpanded && (
                        <div className="px-4 py-3 bg-gray-50 border-t">
                          <div className="space-y-3">
                            {/* Para A ending */}
                            <div>
                              <h4 className="text-sm font-medium text-gray-700 mb-1">
                                Paragraph {trans.paraAIndex + 1} ending / 段落结尾
                              </h4>
                              <p className="text-sm text-gray-600 italic">
                                "...{trans.paraAEnding}"
                              </p>
                            </div>

                            {/* Para B opening */}
                            <div>
                              <h4 className="text-sm font-medium text-gray-700 mb-1">
                                Paragraph {trans.paraBIndex + 1} opening / 段落开头
                              </h4>
                              <p className="text-sm text-gray-600 italic">
                                "{trans.paraBOpening}..."
                              </p>
                            </div>

                            {/* Issues */}
                            {trans.issues && trans.issues.length > 0 && (
                              <div>
                                <h4 className="text-sm font-medium text-gray-700 mb-1">
                                  Issues / 问题
                                </h4>
                                <ul className="list-disc list-inside text-sm text-gray-600">
                                  {trans.issues.map((issue, i) => (
                                    <li key={i}>{issue.descriptionZh || issue.description}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* No issues */}
          {!hasConnectorIssue && lengthIssues.length === 0 && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">
                  Natural Transitions Detected
                </h3>
                <p className="text-green-600 mt-1">
                  段落过渡自然。没有检测到过多的显性连接词或AI风格的过渡模式。
                </p>
              </div>
            </div>
          )}

          {/* Document Modification Section */}
          {/* 文档修改部分 */}
          <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
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

          {/* Processing time */}
          {result.processingTimeMs && (
            <p className="text-sm text-gray-500 mb-6">
              Analysis completed in {result.processingTimeMs}ms
            </p>
          )}
        </>
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
                  handleNext();
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg mx-4 shadow-xl">
            <div className="flex items-start gap-3 mb-4">
              <AlertTriangle className="w-8 h-8 text-red-600 flex-shrink-0" />
              <div>
                <h3 className="text-lg font-bold text-red-700">
                  Data & Citation Risk Warning / 数据及引用风险警告
                </h3>
              </div>
            </div>

            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <h4 className="font-semibold text-red-800 mb-2">CRITICAL / 重要警告:</h4>
              <ul className="text-sm text-red-700 space-y-1 list-disc list-inside">
                <li>AI may add PLACEHOLDER data like <code className="bg-red-100 px-1 rounded">[AUTHOR_XXXXXXXXXX, YEAR_XXXX]</code></li>
                <li>AI may add PLACEHOLDER statistics like <code className="bg-red-100 px-1 rounded">[XXXX]%</code></li>
                <li>These placeholders are NOT real data - they are for YOU to replace</li>
                <li className="text-red-600 font-semibold">AI可能添加占位符数据如 [AUTHOR_XXXXXXXXXX, YEAR_XXXX]</li>
                <li className="text-red-600 font-semibold">这些占位符不是真实数据 - 需要您自行替换</li>
              </ul>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <h4 className="font-semibold text-yellow-800 mb-2">You MUST / 您必须:</h4>
              <ul className="text-sm text-yellow-700 space-y-1 list-disc list-inside">
                <li>Replace ALL <code className="bg-yellow-100 px-1 rounded">[XXXX]</code> placeholders with REAL verified data</li>
                <li>Verify ALL citations against original sources</li>
                <li>Never submit documents with unverified placeholders</li>
                <li>用真实已验证的数据替换所有 [XXXX] 占位符</li>
                <li>对照原始来源核实所有引用</li>
                <li>永远不要提交包含未验证占位符的文档</li>
              </ul>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-gray-700">
                <strong>Placeholder format / 占位符格式:</strong>
              </p>
              <ul className="text-xs text-gray-600 mt-1 space-y-0.5 font-mono">
                <li>[AUTHOR_XXXXXXXXXX, YEAR_XXXX] - for citations / 用于引用</li>
                <li>[XXXX]% - for percentages / 用于百分比</li>
                <li>p &lt; [X.XX] - for p-values / 用于p值</li>
                <li>[XXXX] - for numbers / 用于数字</li>
              </ul>
            </div>

            <div className="flex justify-end gap-3 pt-2">
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
                I Understand, Proceed / 我理解，继续
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      {showNavigation && (
        <div className="flex items-center justify-between pt-6 border-t">
          <Button variant="secondary" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back: Logic Pattern / 上一步：逻辑模式
          </Button>
          <Button variant="primary" onClick={() => setShowSkipConfirm(true)} disabled={isAnalyzing}>
            Skip and Continue / 跳过并继续
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
