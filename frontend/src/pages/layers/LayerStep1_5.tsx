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
  Unlink,
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
  ContentSubstantialityResponse,
  DetectionIssue,
  IssueSuggestionResponse,
  ModifyPromptResponse,
  ApplyModifyResponse,
} from '../../services/analysisApi';
import { useSubstepStateStore } from '../../stores/substepStateStore';

/**
 * Layer Step 1.5 - Content Substantiality Analysis
 * 步骤 1.5 - 内容实质性分析
 *
 * Detects:
 * - Generic phrases common in AI text (AI文本中常见的泛化短语)
 * - Filler words and vague language (填充词和模糊语言)
 * - Lack of specific details (numbers, names, dates) (缺乏具体细节)
 * - Anchor density for hallucination risk (锚点密度/幻觉风险)
 *
 * Priority: ★★☆☆☆ (Final step, depends on paragraph content being stable)
 * 优先级: ★★☆☆☆ (最后处理，依赖段落内容稳定)
 *
 * Uses LLM to analyze content for specificity vs. generic AI-like patterns.
 * 使用LLM分析内容的具体性与泛泛的AI风格模式。
 */

// Content substantiality level config
// 内容实质性等级配置
const SUBSTANTIALITY_LEVEL_CONFIG: Record<string, { label: string; labelZh: string; color: string }> = {
  high: { label: 'High', labelZh: '高', color: 'green' },
  medium: { label: 'Medium', labelZh: '中', color: 'yellow' },
  low: { label: 'Low', labelZh: '低', color: 'red' },
};

interface LayerStep1_5Props {
  documentIdProp?: string;
  onComplete?: (result: ContentSubstantialityResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep1_5({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep1_5Props) {
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
      sessionApi.updateStep(sessionId, 'layer5-step1-5').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<ContentSubstantialityResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedTransitionIndex, setExpandedTransitionIndex] = useState<number | null>(null);

  // Issues derived from analysis result
  // 从分析结果派生的问题列表
  const [transitionIssues, setTransitionIssues] = useState<DetectionIssue[]>([]);

  // Issue selection for merge modify
  // 用于合并修改的问题选择
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());

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

      // Check previous steps for modified text (step5-4, step5-3, step5-2, step5-1 for LayerStep1_5)
      // 检查前序步骤的修改后文本（LayerStep1_5检查step5-4, step5-3, step5-2, step5-1）
      const previousSteps = ['step5-4', 'step5-3', 'step5-2', 'step5-1'];
      let foundModifiedText: string | null = null;

      for (const stepName of previousSteps) {
        const stepState = substepStore.getState(stepName);
        if (stepState?.modifiedText) {
          console.log(`[LayerStep1_5] Using modified text from ${stepName}`);
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
      // Call content substantiality API (LLM-based)
      // 调用内容实质性分析API（基于LLM）
      const analysisResult = await documentLayerApi.analyzeContentSubstantiality(documentText, sessionId || undefined);
      setResult(analysisResult);

      // Create issues from analysis result
      // 从分析结果创建问题列表
      const issues: DetectionIssue[] = [];

      // Add issue for low substantiality
      // 为低实质性内容添加问题
      if (analysisResult.overallSubstantiality === 'low') {
        issues.push({
          type: 'low_substantiality',
          description: `Low content substantiality detected (score: ${analysisResult.overallSpecificityScore})`,
          descriptionZh: `检测到内容实质性较低 (分数: ${analysisResult.overallSpecificityScore})`,
          severity: 'high',
          layer: 'document',
        });
      } else if (analysisResult.overallSubstantiality === 'medium') {
        issues.push({
          type: 'medium_substantiality',
          description: `Medium content substantiality (score: ${analysisResult.overallSpecificityScore})`,
          descriptionZh: `内容实质性中等 (分数: ${analysisResult.overallSpecificityScore})`,
          severity: 'medium',
          layer: 'document',
        });
      }

      // Add issues for generic phrases
      // 为泛化短语添加问题
      if (analysisResult.totalGenericPhrases > 0) {
        issues.push({
          type: 'generic_phrases',
          description: `${analysisResult.totalGenericPhrases} generic phrases detected`,
          descriptionZh: `检测到${analysisResult.totalGenericPhrases}个泛化短语`,
          severity: analysisResult.totalGenericPhrases > 10 ? 'high' : 'medium',
          layer: 'document',
        });
      }

      // Add issues for low substantiality paragraphs
      // 为低实质性段落添加问题
      analysisResult.lowSubstantialityParagraphs?.forEach((paraIdx) => {
        issues.push({
          type: 'low_substantiality_paragraph',
          description: `Paragraph ${paraIdx + 1} has low content substantiality`,
          descriptionZh: `段落${paraIdx + 1}内容实质性较低`,
          severity: 'medium',
          layer: 'paragraph',
          location: `Para ${paraIdx + 1}`,
        });
      });

      setTransitionIssues(issues);

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

  // Load detailed suggestion for a specific issue (LLM-based)
  // 为特定问题加载详细建议（基于LLM）
  // Uses the same API as LayerStep1_1 for consistency
  // 使用与LayerStep1_1相同的API以保持一致性
  const loadIssueSuggestion = useCallback(async (index: number) => {
    const issue = transitionIssues[index];
    if (!issue || !documentId) return;

    setIsLoadingSuggestion(true);
    setSuggestionError(null);

    try {
      // Use the same API as LayerStep1_1 - calls LLM for issue-specific analysis
      // 使用与LayerStep1_1相同的API - 调用LLM进行问题特定分析
      const response = await documentLayerApi.getIssueSuggestion(documentId, issue, false);

      // Store the full response for display
      // 存储完整响应用于显示
      setIssueSuggestion({
        ...response,
        analysis: response.diagnosisZh || '',
        suggestions: response.strategies?.map(s => s.descriptionZh) || [],
        exampleFix: response.strategies?.[0]?.exampleAfter || '',
      });
    } catch (err) {
      console.error('Failed to load suggestion:', err);
      setSuggestionError('Failed to load detailed suggestion / 加载详细建议失败');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [transitionIssues, documentId]);

  // Handle issue click - toggle expand and auto-load LLM suggestion
  // 处理问题点击 - 切换展开并自动加载LLM建议
  const handleIssueClick = useCallback(async (index: number) => {
    const issue = transitionIssues[index];
    if (!issue || !documentId) return;

    // Collapse if already expanded
    // 如果已展开则收起
    if (expandedTransitionIndex === index) {
      setExpandedTransitionIndex(null);
      setIssueSuggestion(null);
      return;
    }

    // Expand and auto-load LLM suggestion
    // 展开并自动加载LLM建议
    setExpandedTransitionIndex(index);
    setIssueSuggestion(null);
    await loadIssueSuggestion(index);
  }, [transitionIssues, documentId, expandedTransitionIndex, loadIssueSuggestion]);

  // Toggle issue selection (for batch operations)
  // 切换问题选择（用于批量操作）
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
  }, []);

  // Select all issues
  // 全选所有问题
  const selectAllIssues = useCallback(() => {
    setSelectedIssueIndices(new Set(transitionIssues.map((_, idx) => idx)));
  }, [transitionIssues]);

  // Deselect all issues
  // 取消全选所有问题
  const deselectAllIssues = useCallback(() => {
    setSelectedIssueIndices(new Set());
  }, []);

  // Execute merge modify (generate prompt or apply modification)
  // 执行合并修改（生成提示或应用修改）
  const executeMergeModify = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentId) return;

    setIsMerging(true);
    setShowMergeConfirm(false);

    try {
      const selectedIssues = Array.from(selectedIssueIndices).map(i => transitionIssues[i]);

      if (mergeMode === 'prompt') {
        // Generate prompt only
        // 仅生成提示
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
        // Apply modification directly
        // 直接应用修改
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
  }, [selectedIssueIndices, documentId, transitionIssues, mergeMode, mergeUserNotes, sessionId]);

  // Handle regenerate (retry AI modification)
  // 处理重新生成（重试AI修改）
  const handleRegenerate = useCallback(() => {
    setMergeResult(null);
    setShowMergeConfirm(true);
    setMergeMode('apply');
  }, []);

  // Handle accept modification (copy to text input)
  // 处理接受修改（复制到文本输入）
  const handleAcceptModification = useCallback(() => {
    if (mergeResult && 'modifiedText' in mergeResult && mergeResult.modifiedText) {
      setNewText(mergeResult.modifiedText);
      setModifyMode('text');
      setMergeResult(null);
    }
  }, [mergeResult]);

  // Handle file selection
  // 处理文件选择
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setNewFile(file);
    }
  }, []);

  // Handle confirm modification and navigate to next layer
  // 处理确认修改并导航到下一层
  const handleConfirmModify = useCallback(async () => {
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
        await substepStore.saveModifiedText('step5-5', modifiedText);
        await substepStore.markCompleted('step5-5');
        console.log('[LayerStep1_5] Saved modified text to substep store');
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
        const result = await documentApi.uploadText(newText, `step1_5_modified_${Date.now()}.txt`);
        newDocId = result.documentId;
      }

      // Navigate to Layer 4 Step 2.0 with new document (use documentId from URL/props)
      // 导航到第4层步骤2.0（使用URL/props中的documentId）
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer4-step2-0/${documentId}?${params.toString()}`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload modified document / 上传修改后的文档失败');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate, documentId, substepStore]);

  // Navigation
  const handleBack = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer5-step1-4/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    // Go to Layer 4 Step 2.0 (Section Identification)
    // 跳转到第4层步骤2.0（章节识别）
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer4-step2-0/${documentId}?${params.toString()}`);
  };

  const toggleTransition = (index: number) => {
    setExpandedTransitionIndex(expandedTransitionIndex === index ? null : index);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage category="transition" centered />
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

  const hasLowSubstantiality = result?.overallSubstantiality === 'low' || result?.riskLevel === 'high';
  const lowQualityParagraphs = result?.lowSubstantialityParagraphs || [];
  const genericPhrases = result?.commonGenericPhrases || [];
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
          <span className="text-gray-900 font-medium">Step 1.5 内容实质性</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Content Substantiality Analysis
        </h1>
        <p className="text-gray-600 mt-1">
          内容实质性分析 - 使用LLM检测泛化短语、填充词和缺乏具体细节的段落
        </p>
      </div>

      {/* Start Analysis / Skip Step */}
      {documentText && !analysisStarted && !isAnalyzing && !result && (
        <div className="mb-6 p-6 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="text-center">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Analyze / 准备分析</h3>
            <p className="text-gray-600 mb-6">
              Click "Start Analysis" to detect content substantiality issues, or skip this step.
              <br />点击"开始分析"检测内容实质性问题，或跳过此步骤。
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
              <p className="text-blue-800 font-medium">Analyzing content substantiality... / 分析内容实质性中...</p>
              <p className="text-blue-600 text-sm">Using LLM to detect generic phrases and lack of specificity / 使用LLM检测泛化短语和缺乏具体性</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* Summary Stats */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Overall Substantiality */}
            <div className={clsx(
              'p-4 rounded-lg border',
              result.overallSubstantiality === 'low' ? 'bg-red-50 border-red-200' :
              result.overallSubstantiality === 'medium' ? 'bg-yellow-50 border-yellow-200' :
              'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                {result.overallSubstantiality === 'low' ? (
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                ) : result.overallSubstantiality === 'medium' ? (
                  <AlertCircle className="w-5 h-5 text-yellow-600" />
                ) : (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                )}
                <span className="font-medium text-gray-900">Substantiality / 实质性</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                result.overallSubstantiality === 'low' ? 'text-red-600' :
                result.overallSubstantiality === 'medium' ? 'text-yellow-600' :
                'text-green-600'
              )}>
                {result.overallSubstantiality?.toUpperCase() || 'HIGH'}
              </div>
            </div>

            {/* Specificity Score */}
            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">Specificity Score / 具体性</span>
              </div>
              <div className="text-2xl font-bold text-gray-700">
                {result.overallSpecificityScore || 0}
              </div>
            </div>

            {/* Generic Phrases */}
            <div className={clsx(
              'p-4 rounded-lg border',
              (result.totalGenericPhrases || 0) > 5 ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className={clsx('w-5 h-5', (result.totalGenericPhrases || 0) > 5 ? 'text-yellow-600' : 'text-gray-600')} />
                <span className="font-medium text-gray-900">Generic Phrases / 泛化短语</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                (result.totalGenericPhrases || 0) > 5 ? 'text-yellow-600' : 'text-gray-700'
              )}>
                {result.totalGenericPhrases || 0}
              </div>
            </div>

            {/* Low Substantiality Paragraphs */}
            <div className={clsx(
              'p-4 rounded-lg border',
              (result.lowSubstantialityParagraphs?.length || 0) > 0 ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <Unlink className={clsx('w-5 h-5', (result.lowSubstantialityParagraphs?.length || 0) > 0 ? 'text-red-600' : 'text-gray-600')} />
                <span className="font-medium text-gray-900">Low Quality Paras / 低质量段落</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                (result.lowSubstantialityParagraphs?.length || 0) > 0 ? 'text-red-600' : 'text-gray-700'
              )}>
                {result.lowSubstantialityParagraphs?.length || 0}
              </div>
            </div>
          </div>

          {/* Risk Alert */}
          {hasLowSubstantiality && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Low Content Substantiality Detected
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：检测到内容实质性较低。存在过多泛泛而谈或缺乏具体细节的段落。
                  建议增加具体数据、实例和专业术语，减少空洞的表述。
                </p>
              </div>
            </div>
          )}

          {/* Issues Section with Selection and Expandable LLM Suggestions */}
          {/* 问题部分（带选择功能和可展开的LLM建议） */}
          {transitionIssues.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                  Detected Issues / 检测到的问题
                  <span className="text-sm font-normal text-gray-500">
                    ({selectedIssueIndices.size}/{transitionIssues.length} selected / 已选择)
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
                {transitionIssues.map((issue, idx) => {
                  const isExpanded = expandedTransitionIndex === idx;
                  const isSelected = selectedIssueIndices.has(idx);
                  const severityColor = {
                    high: 'border-red-200 bg-red-50',
                    medium: 'border-yellow-200 bg-yellow-50',
                    low: 'border-gray-200 bg-gray-50',
                  }[issue.severity] || 'border-gray-200 bg-gray-50';
                  const severityTextColor = {
                    high: 'text-red-800',
                    medium: 'text-yellow-800',
                    low: 'text-gray-800',
                  }[issue.severity] || 'text-gray-800';

                  return (
                    <div
                      key={idx}
                      className={clsx('border rounded-lg overflow-hidden', severityColor)}
                    >
                      <div className="flex items-start">
                        {/* Selection checkbox */}
                        {/* 选择复选框 */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleIssueSelection(idx);
                          }}
                          className="p-4 hover:bg-white/50 transition-colors"
                        >
                          <div className={clsx(
                            'w-5 h-5 rounded border-2 flex items-center justify-center',
                            isSelected
                              ? 'bg-blue-600 border-blue-600'
                              : 'border-gray-400'
                          )}>
                            {isSelected && (
                              <Check className="w-3 h-3 text-white" />
                            )}
                          </div>
                        </button>

                        {/* Issue content - click to expand and load LLM suggestion */}
                        {/* 问题内容 - 点击展开并加载LLM建议 */}
                        <button
                          onClick={() => handleIssueClick(idx)}
                          className="flex-1 px-4 py-3 flex items-center justify-between hover:opacity-90 transition-opacity text-left"
                        >
                          <div className="flex items-center gap-3">
                            <AlertCircle className={clsx('w-5 h-5', severityTextColor)} />
                            <div>
                              <div className="flex items-center gap-2 mb-1">
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
                                {issue.location && (
                                  <span className="text-xs text-gray-400 font-mono">{issue.location}</span>
                                )}
                              </div>
                              <p className={clsx('font-medium', severityTextColor)}>
                                {issue.descriptionZh || issue.description}
                              </p>
                              {issue.descriptionZh && issue.description !== issue.descriptionZh && (
                                <p className="text-sm text-gray-600 mt-0.5">{issue.description}</p>
                              )}
                            </div>
                          </div>
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0 ml-2" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0 ml-2" />
                          )}
                        </button>
                      </div>

                      {/* Expanded content with LLM suggestion */}
                      {/* 展开内容显示LLM建议 */}
                      {isExpanded && (
                        <div className="px-4 py-3 border-t border-current border-opacity-20 bg-white/50">
                          {isLoadingSuggestion && (
                            <div className="flex items-center justify-center py-6">
                              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                              <span className="ml-2 text-gray-600">Loading LLM suggestion... / 加载LLM建议中...</span>
                            </div>
                          )}

                          {!isLoadingSuggestion && issueSuggestion && (
                            <div className="space-y-4">
                              {/* Diagnosis / Analysis */}
                              {/* 诊断/分析 */}
                              {issueSuggestion.analysis && (
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                                    <Sparkles className="w-4 h-4 text-purple-600" />
                                    诊断 / Diagnosis
                                  </h4>
                                  <p className="text-sm text-gray-700 bg-purple-50 p-3 rounded-lg">
                                    {issueSuggestion.analysis}
                                  </p>
                                </div>
                              )}

                              {/* Strategies / Suggestions */}
                              {/* 策略/建议 */}
                              {issueSuggestion.suggestions && issueSuggestion.suggestions.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                    修改策略 / Modification Strategies
                                  </h4>
                                  <ul className="space-y-2">
                                    {issueSuggestion.suggestions.map((suggestion, sIdx) => (
                                      <li key={sIdx} className="text-sm text-gray-700 bg-blue-50 p-2 rounded flex items-start gap-2">
                                        <span className="text-blue-600 font-medium">{sIdx + 1}.</span>
                                        {suggestion}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Example Fix */}
                              {/* 示例修复 */}
                              {issueSuggestion.exampleFix && (
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                    示例修复 / Example Fix
                                  </h4>
                                  <pre className="text-sm text-gray-800 bg-green-50 p-3 rounded-lg whitespace-pre-wrap overflow-x-auto">
                                    {issueSuggestion.exampleFix}
                                  </pre>
                                </div>
                              )}

                              {/* Full strategies from API response */}
                              {/* API响应中的完整策略 */}
                              {issueSuggestion.strategies && issueSuggestion.strategies.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                    详细策略 / Detailed Strategies
                                  </h4>
                                  <div className="space-y-3">
                                    {issueSuggestion.strategies.map((strategy, sIdx) => (
                                      <div key={sIdx} className="bg-white p-3 rounded border border-gray-200">
                                        <div className="flex items-center justify-between mb-2">
                                          <h5 className="font-medium text-gray-900">{strategy.nameZh}</h5>
                                          <span className="text-xs text-gray-500">
                                            效果: {strategy.effectiveness}/100
                                          </span>
                                        </div>
                                        <p className="text-sm text-gray-600 mb-2">
                                          {strategy.descriptionZh}
                                        </p>
                                        {strategy.exampleBefore && strategy.exampleAfter && (
                                          <div className="mt-2 text-xs space-y-1">
                                            <div>
                                              <span className="text-red-600">修改前: </span>
                                              <span className="text-gray-700">{strategy.exampleBefore}</span>
                                            </div>
                                            <div>
                                              <span className="text-green-600">修改后: </span>
                                              <span className="text-gray-700">{strategy.exampleAfter}</span>
                                            </div>
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}

                          {!isLoadingSuggestion && !issueSuggestion && suggestionError && (
                            <div className="py-4 text-center">
                              <p className="text-red-600 text-sm mb-2">{suggestionError}</p>
                              <button
                                onClick={() => loadIssueSuggestion(idx)}
                                className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
                              >
                                点击重试 / Click to retry
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Action Buttons for Selected Issues (Batch Operations) */}
          {/* 选中问题的操作按钮（批量操作） */}
          {transitionIssues.length > 0 && (
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

          {/* Generic Phrases */}
          {/* 泛化短语列表 */}
          {genericPhrases.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-600" />
                Generic Phrases / 泛化短语
                <span className="text-sm font-normal text-gray-500">
                  ({genericPhrases.length} detected)
                </span>
              </h3>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex flex-wrap gap-2">
                  {genericPhrases.map((phrase: string, idx: number) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium"
                    >
                      "{phrase}"
                    </span>
                  ))}
                </div>
                <p className="text-yellow-700 text-sm mt-3">
                  These generic phrases are commonly found in AI-generated text.
                  Consider replacing with more specific and concrete expressions.
                </p>
                <p className="text-yellow-600 text-sm mt-1">
                  这些泛化短语在AI生成的文本中很常见。建议替换为更具体、更明确的表达。
                </p>
              </div>
            </div>
          )}

          {/* Low Substantiality Paragraphs */}
          {/* 低实质性段落详情 */}
          {lowQualityParagraphs.length > 0 && result?.paragraphs && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Unlink className="w-5 h-5 text-red-600" />
                Low Substantiality Paragraphs / 低实质性段落
                <span className="text-sm font-normal text-gray-500">
                  ({lowQualityParagraphs.length} paragraphs)
                </span>
              </h3>
              <div className="space-y-2">
                {result.paragraphs
                  .filter(p => lowQualityParagraphs.includes(p.index))
                  .map((para, idx) => {
                    const isExpanded = expandedTransitionIndex === idx;

                    return (
                      <div
                        key={idx}
                        className="bg-red-50 border border-red-200 rounded-lg overflow-hidden"
                      >
                        <button
                          onClick={() => toggleTransition(idx)}
                          className="w-full px-4 py-3 flex items-center justify-between hover:bg-red-100 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <AlertTriangle className="w-5 h-5 text-red-600" />
                            <div className="text-left">
                              <p className="font-medium text-red-800">
                                Paragraph {para.index + 1} / 段落 {para.index + 1}
                              </p>
                              <p className="text-sm text-red-600">
                                Specificity: {para.specificityScore} | Generic: {para.genericPhraseCount} | Filler: {(para.fillerRatio * 100).toFixed(0)}%
                              </p>
                            </div>
                          </div>
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400" />
                          )}
                        </button>
                        {isExpanded && (
                          <div className="px-4 py-3 border-t border-red-200 bg-white">
                            <div className="space-y-3">
                              {/* Preview */}
                              <div>
                                <h4 className="text-sm font-medium text-gray-700 mb-1">
                                  Preview / 预览
                                </h4>
                                <p className="text-gray-600 text-sm bg-gray-50 p-2 rounded">
                                  {para.preview}
                                </p>
                              </div>

                              {/* Generic Phrases in this paragraph */}
                              {para.genericPhrases && para.genericPhrases.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-medium text-gray-700 mb-1">
                                    Generic Phrases / 泛化短语
                                  </h4>
                                  <div className="flex flex-wrap gap-1">
                                    {para.genericPhrases.map((phrase, pIdx) => (
                                      <span key={pIdx} className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs">
                                        {phrase}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Suggestion */}
                              <div>
                                <h4 className="text-sm font-medium text-gray-700 mb-1">
                                  Suggestion / 建议
                                </h4>
                                <p className="text-gray-600 text-sm bg-blue-50 p-2 rounded">
                                  {para.suggestionZh || para.suggestion}
                                </p>
                              </div>
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
          {!hasLowSubstantiality && lowQualityParagraphs.length === 0 && genericPhrases.length === 0 && transitionIssues.length === 0 && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">
                  Good Content Substantiality
                </h3>
                <p className="text-green-600 mt-1">
                  内容实质性良好。未检测到空洞表述或缺乏具体细节的问题。
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
              Upload a modified file or paste modified text to finish Layer 5 and continue to Layer 4.
              上传修改后的文件或粘贴修改后的文本，完成第5层并继续进入第4层。
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
                Finish Layer 5 & Continue / 完成第5层并继续
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

      {/* Navigation */}
      {showNavigation && (
        <div className="flex items-center justify-between pt-6 border-t">
          <Button variant="secondary" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back: Paragraph Length / 上一步：段落长度
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
