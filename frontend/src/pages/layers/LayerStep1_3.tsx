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
  GitBranch,
  Repeat,
  ArrowDownUp,
  Sparkles,
  Wand2,
  Copy,
  Check,
  X,
  Upload,
  Type,
  Square,
  CheckSquare,
  RotateCcw,
  FileText,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import {
  documentLayerApi,
  ProgressionClosureResponse,
  ProgressionMarker,
  DetectionIssue,
} from '../../services/analysisApi';

/**
 * Layer Step 1.3 - Section Logic Pattern Detection
 * 步骤 1.3 - 章节逻辑模式检测
 *
 * Detects (Merged Group 2):
 * - F: Repetitive Logic Pattern (章节逻辑重复模式 - 每章都是问题-分析-结论)
 * - G: Linear Logic Flow (章节逻辑线性流动 - First-Second-Third)
 *
 * Priority: ★★★☆☆ (Depends on 1.2 section structure)
 * 优先级: ★★★☆☆ (依赖1.2的章节结构稳定)
 *
 * Conflict Note: Must process before Step 1.4 (paragraph length), otherwise they conflict.
 * 冲突说明: 必须在1.4(段落长度)之前处理，否则会互相打乱。
 */

// Progression type display config
// 推进类型显示配置
const PROGRESSION_TYPE_CONFIG: Record<string, { label: string; labelZh: string; risk: string; color: string; icon: typeof GitBranch }> = {
  monotonic: {
    label: 'Monotonic (AI-like)',
    labelZh: '单调推进（AI风格）',
    risk: 'high',
    color: 'text-red-600 bg-red-50 border-red-200',
    icon: ArrowDownUp,
  },
  non_monotonic: {
    label: 'Non-monotonic (Human-like)',
    labelZh: '非单调（人类风格）',
    risk: 'low',
    color: 'text-green-600 bg-green-50 border-green-200',
    icon: GitBranch,
  },
  mixed: {
    label: 'Mixed',
    labelZh: '混合',
    risk: 'medium',
    color: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    icon: GitBranch,
  },
};

// Marker type display config
// 标记类型显示配置
const MARKER_TYPE_CONFIG: Record<string, { label: string; labelZh: string; pattern: string }> = {
  sequential: { label: 'Sequential', labelZh: '顺序类', pattern: 'First, Second, Third...' },
  additive: { label: 'Additive', labelZh: '累加类', pattern: 'Furthermore, Moreover...' },
  causal: { label: 'Causal', labelZh: '因果类', pattern: 'Therefore, Thus...' },
  return: { label: 'Return', labelZh: '回溯类', pattern: 'As noted earlier...' },
  conditional: { label: 'Conditional', labelZh: '条件类', pattern: 'If, When, Unless...' },
  contrastive: { label: 'Contrastive', labelZh: '对比类', pattern: 'However, But...' },
  concessive: { label: 'Concessive', labelZh: '让步类', pattern: 'Although, Despite...' },
};

interface LayerStep1_3Props {
  documentIdProp?: string;
  onComplete?: (result: ProgressionClosureResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep1_3({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep1_3Props) {
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
      sessionApi.updateStep(sessionId, 'layer5-step1-3').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<ProgressionClosureResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedMarkerType, setExpandedMarkerType] = useState<string | null>(null);

  // Issue selection for merge modify
  // 问题选择（用于合并修改）
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());
  const [logicIssues, setLogicIssues] = useState<DetectionIssue[]>([]);
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

  // Issue suggestion state
  // 问题建议状态
  const [issueSuggestion, setIssueSuggestion] = useState<{
    diagnosisZh: string;
    strategies: Array<{
      nameZh: string;
      descriptionZh: string;
      exampleBefore?: string;
      exampleAfter?: string;
      difficulty: string;
      effectiveness: number;
    }>;
    modificationPrompt: string;
    priorityTipsZh: string[];
    cautionZh: string;
  } | null>(null);
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);

  // Merge modify state
  // 合并修改状态
  const [showMergeConfirm, setShowMergeConfirm] = useState(false);
  const [mergeMode, setMergeMode] = useState<'prompt' | 'apply'>('prompt');
  const [mergeUserNotes, setMergeUserNotes] = useState('');
  const [isMerging, setIsMerging] = useState(false);
  const [mergeResult, setMergeResult] = useState<{
    type: 'prompt' | 'apply';
    prompt?: string;
    promptZh?: string;
    modifiedText?: string;
    changesSummaryZh?: string;
    changesCount?: number;
    remainingAttempts?: number;
    colloquialismLevel?: number;
  } | null>(null);
  const [copiedMergePrompt, setCopiedMergePrompt] = useState(false);
  const [regenerateCount, setRegenerateCount] = useState(0);
  const MAX_REGENERATE = 3;

  // Skip confirmation state
  // 跳过确认状态
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);

  // Document modification state
  // 文档修改状态
  const [modifyMode, setModifyMode] = useState<'file' | 'text'>('file');
  const [newFile, setNewFile] = useState<File | null>(null);
  const [newText, setNewText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const isAnalyzingRef = useRef(false);

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
      const doc = await documentApi.get(docId);
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

  // Run analysis
  useEffect(() => {
    if (documentText && !isAnalyzingRef.current) {
      runAnalysis();
    }
  }, [documentText]);

  const runAnalysis = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;
    setIsAnalyzing(true);
    setError(null);

    try {
      const analysisResult = await documentLayerApi.analyzeProgressionClosure(documentText, sessionId || undefined);
      setResult(analysisResult);

      // Create logic issues from result
      // 从结果创建逻辑问题
      const issues: DetectionIssue[] = [];

      // Check for monotonic progression
      if (analysisResult.progressionType === 'monotonic') {
        issues.push({
          type: 'monotonic_progression',
          description: 'Monotonic progression detected - AI-like linear flow',
          descriptionZh: '检测到单调推进 - AI风格的线性流动',
          severity: 'high',
          layer: 'document',
          suggestion: 'Add returns, conditionals, and contrasts',
          suggestionZh: '添加回溯、条件和对比元素',
        });
      }

      // Check for strong closure
      if (analysisResult.closureType === 'strong') {
        issues.push({
          type: 'strong_closure',
          description: 'Strong closure pattern - too definitive',
          descriptionZh: '强闭合模式 - 过于明确',
          severity: 'medium',
          layer: 'document',
          suggestion: 'Consider leaving some questions open',
          suggestionZh: '考虑留下一些开放性问题',
        });
      }

      // Add issues from recommendations
      if (analysisResult.recommendations) {
        analysisResult.recommendations.forEach((rec, idx) => {
          issues.push({
            type: 'recommendation',
            description: rec,
            descriptionZh: analysisResult.recommendationsZh?.[idx] || rec,
            severity: 'medium',
            layer: 'document',
          });
        });
      }

      setLogicIssues(issues);

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

  // Navigation
  const handleBack = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer5-step1-2/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer5-step1-4/${documentId}?${params.toString()}`);
  };

  const toggleMarkerType = (type: string) => {
    setExpandedMarkerType(expandedMarkerType === type ? null : type);
  };

  // Toggle issue selection
  // 切换问题选择
  const toggleIssueSelection = (index: number) => {
    const newSelected = new Set(selectedIssueIndices);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedIssueIndices(newSelected);
  };

  // Load suggestion for a specific issue
  // 为特定问题加载建议
  const loadIssueSuggestion = useCallback(async (index: number) => {
    const issue = logicIssues[index];
    if (!issue || !documentId) return;

    setIsLoadingSuggestion(true);
    setIssueSuggestion(null);

    try {
      const suggestion = await documentLayerApi.getIssueSuggestion(documentId, issue, false);
      setIssueSuggestion(suggestion);
    } catch (err) {
      console.error('Failed to load issue suggestion:', err);
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [logicIssues, documentId]);

  // Handle issue click
  // 处理问题点击
  const handleIssueClick = useCallback(async (index: number) => {
    if (expandedIssueIndex === index) {
      setExpandedIssueIndex(null);
      setIssueSuggestion(null);
      return;
    }

    setExpandedIssueIndex(index);
    await loadIssueSuggestion(index);
  }, [expandedIssueIndex, loadIssueSuggestion]);

  // Execute merge modify
  // 执行合并修改
  const executeMergeModify = useCallback(async () => {
    if (!documentId || selectedIssueIndices.size === 0) return;

    const selectedIssues = Array.from(selectedIssueIndices).map(idx => logicIssues[idx]);

    setIsMerging(true);
    setShowMergeConfirm(false);

    try {
      if (mergeMode === 'prompt') {
        const response = await documentLayerApi.generateModifyPrompt(
          documentId,
          selectedIssues,
          { sessionId: sessionId || undefined, userNotes: mergeUserNotes || undefined }
        );
        setMergeResult({
          type: 'prompt',
          prompt: response.prompt,
          promptZh: response.promptZh,
          colloquialismLevel: response.colloquialismLevel,
        });
      } else {
        const response = await documentLayerApi.applyModify(
          documentId,
          selectedIssues,
          { sessionId: sessionId || undefined, userNotes: mergeUserNotes || undefined }
        );
        setMergeResult({
          type: 'apply',
          modifiedText: response.modifiedText,
          changesSummaryZh: response.changesSummaryZh,
          changesCount: response.changesCount,
          remainingAttempts: response.remainingAttempts,
          colloquialismLevel: response.colloquialismLevel,
        });
        setRegenerateCount(1);
      }
    } catch (err) {
      console.error('Merge modify failed:', err);
      alert('操作失败，请重试 / Operation failed, please try again');
    } finally {
      setIsMerging(false);
    }
  }, [documentId, selectedIssueIndices, logicIssues, mergeMode, mergeUserNotes, sessionId]);

  // Handle regenerate
  // 处理重新生成
  const handleRegenerate = useCallback(async () => {
    if (regenerateCount >= MAX_REGENERATE || !documentId || selectedIssueIndices.size === 0) return;

    const selectedIssues = Array.from(selectedIssueIndices).map(idx => logicIssues[idx]);

    setIsMerging(true);

    try {
      const response = await documentLayerApi.applyModify(
        documentId,
        selectedIssues,
        { sessionId: sessionId || undefined, userNotes: mergeUserNotes || undefined }
      );
      setMergeResult({
        type: 'apply',
        modifiedText: response.modifiedText,
        changesSummaryZh: response.changesSummaryZh,
        changesCount: response.changesCount,
        remainingAttempts: response.remainingAttempts,
        colloquialismLevel: response.colloquialismLevel,
      });
      setRegenerateCount(prev => prev + 1);
    } catch (err) {
      console.error('Regenerate failed:', err);
      alert('重新生成失败，请重试 / Regeneration failed, please try again');
    } finally {
      setIsMerging(false);
    }
  }, [documentId, regenerateCount, selectedIssueIndices, logicIssues, sessionId, mergeUserNotes]);

  // Handle accept modification
  // 处理接受修改
  const handleAcceptModification = useCallback(() => {
    if (mergeResult?.modifiedText) {
      setNewText(mergeResult.modifiedText);
      setModifyMode('text');
      setMergeResult(null);
      setTimeout(() => {
        const modifySection = document.getElementById('modify-section');
        if (modifySection) {
          modifySection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
    }
  }, [mergeResult?.modifiedText]);

  // Handle confirm modify
  // 处理确认修改
  const handleConfirmModify = useCallback(async () => {
    if (modifyMode === 'file' && !newFile) {
      setUploadError('请选择一个文件 / Please select a file');
      return;
    }

    if (modifyMode === 'text' && !newText.trim()) {
      setUploadError('请输入文本内容 / Please enter text content');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      let newDocumentId: string;

      if (modifyMode === 'file' && newFile) {
        const result = await documentApi.upload(newFile);
        newDocumentId = result.id;
      } else {
        const result = await documentApi.uploadText(newText);
        newDocumentId = result.id;
      }

      const sessionParam = sessionId ? `&session=${sessionId}` : '';
      navigate(`/flow/layer5-step1-4/${newDocumentId}?mode=${mode}${sessionParam}`);
    } catch (err) {
      setUploadError((err as Error).message || '上传失败，请重试 / Upload failed, please try again');
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, sessionId, mode, navigate]);

  // Validate and set file
  // 验证并设置文件
  const validateAndSetFile = (selectedFile: File) => {
    const allowedTypes = [
      'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];
    const maxSize = 10 * 1024 * 1024;

    if (!allowedTypes.includes(selectedFile.type)) {
      setUploadError('仅支持 TXT 和 DOCX 格式 / Only TXT and DOCX formats are supported');
      return;
    }

    if (selectedFile.size > maxSize) {
      setUploadError('文件大小不能超过 10MB / File size cannot exceed 10MB');
      return;
    }

    setNewFile(selectedFile);
    setUploadError(null);
  };

  // Handle file change
  // 处理文件变化
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  // Copy to clipboard
  // 复制到剪贴板
  const copyToClipboard = (text: string, setCopied: (value: boolean) => void) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  // Group markers by category
  // 按类别分组标记
  const groupMarkersByCategory = (markers: ProgressionMarker[]): Record<string, ProgressionMarker[]> => {
    const grouped: Record<string, ProgressionMarker[]> = {};
    markers.forEach((marker) => {
      const category = marker.category || 'unknown';
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(marker);
    });
    return grouped;
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage category="structure" centered />
      </div>
    );
  }

  // Error state
  if (error) {
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

  const progressionConfig = result?.progressionType
    ? PROGRESSION_TYPE_CONFIG[result.progressionType] || PROGRESSION_TYPE_CONFIG.mixed
    : PROGRESSION_TYPE_CONFIG.mixed;

  const monotonicMarkers = result?.progressionMarkers?.filter(m => m.isMonotonic) || [];
  const nonMonotonicMarkers = result?.progressionMarkers?.filter(m => !m.isMonotonic) || [];
  const groupedMarkers = groupMarkersByCategory(monotonicMarkers);
  const nonMonotonicCount = nonMonotonicMarkers.length;
  const monotonicCount = monotonicMarkers.length;

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
          <span className="text-gray-900 font-medium">Step 1.3 逻辑模式</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Section Logic Pattern Detection
        </h1>
        <p className="text-gray-600 mt-1">
          章节逻辑模式检测 - 检测重复模式（问题-分析-结论）和线性流动（First-Second-Third）
        </p>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing logic patterns... / 分析逻辑模式中...</p>
              <p className="text-blue-600 text-sm">Detecting progression markers and patterns</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* Progression Type Summary */}
          <div className={clsx('mb-6 p-4 rounded-lg border', progressionConfig.color)}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <progressionConfig.icon className="w-6 h-6" />
                <div>
                  <h2 className="text-lg font-semibold">
                    Progression Type / 推进类型
                  </h2>
                  <p className="text-sm opacity-75">
                    {progressionConfig.labelZh} ({progressionConfig.label})
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold">
                  {result.progressionScore || 0}%
                </div>
                <p className="text-sm opacity-75">Predictability Score</p>
              </div>
            </div>
          </div>

          {/* Marker Statistics */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Monotonic Markers */}
            <div className={clsx(
              'p-4 rounded-lg border',
              monotonicCount > nonMonotonicCount ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <Repeat className={clsx('w-5 h-5', monotonicCount > nonMonotonicCount ? 'text-red-600' : 'text-gray-600')} />
                <span className="font-medium text-gray-900">
                  Monotonic Markers / 单调标记
                </span>
              </div>
              <div className={clsx(
                'text-3xl font-bold',
                monotonicCount > nonMonotonicCount ? 'text-red-600' : 'text-gray-600'
              )}>
                {monotonicCount}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Sequential, Additive, Causal patterns
              </p>
            </div>

            {/* Non-monotonic Markers */}
            <div className={clsx(
              'p-4 rounded-lg border',
              nonMonotonicCount >= monotonicCount ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <GitBranch className={clsx('w-5 h-5', nonMonotonicCount >= monotonicCount ? 'text-green-600' : 'text-gray-600')} />
                <span className="font-medium text-gray-900">
                  Non-monotonic Markers / 非单调标记
                </span>
              </div>
              <div className={clsx(
                'text-3xl font-bold',
                nonMonotonicCount >= monotonicCount ? 'text-green-600' : 'text-gray-600'
              )}>
                {nonMonotonicCount}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Return, Conditional, Contrastive patterns
              </p>
            </div>
          </div>

          {/* Risk Alert */}
          {progressionConfig.risk === 'high' && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Monotonic Progression Detected
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：检测到单调推进模式。缺少回溯引用、条件触发和对比转折。
                  建议添加"however"、"as noted earlier"等非单调元素。
                </p>
              </div>
            </div>
          )}

          {/* Monotonic Markers by Type */}
          {Object.keys(groupedMarkers).length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
                Detected Monotonic Markers / 检测到的单调标记
              </h3>
              <div className="space-y-2">
                {Object.entries(groupedMarkers).map(([type, markers]) => {
                  const typeConfig = MARKER_TYPE_CONFIG[type] || { label: type, labelZh: type, pattern: '' };
                  const isExpanded = expandedMarkerType === type;
                  return (
                    <div
                      key={type}
                      className="bg-yellow-50 border border-yellow-200 rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => toggleMarkerType(type)}
                        className="w-full px-4 py-3 flex items-center justify-between hover:bg-yellow-100 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <span className="px-2 py-1 bg-yellow-200 rounded text-yellow-800 text-sm font-medium">
                            {markers.length}
                          </span>
                          <div className="text-left">
                            <p className="font-medium text-yellow-800">
                              {typeConfig.labelZh} ({typeConfig.label})
                            </p>
                            <p className="text-sm text-yellow-600">
                              Pattern: {typeConfig.pattern}
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
                        <div className="px-4 py-3 border-t border-yellow-200 bg-white">
                          <div className="space-y-2">
                            {markers.map((m, idx) => (
                              <div key={idx} className="flex items-start gap-2 text-sm">
                                <span className="text-gray-400">•</span>
                                <span className="font-mono text-yellow-700">"{m.marker}"</span>
                                <span className="text-gray-500">
                                  (Paragraph {m.paragraphIndex + 1})
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Non-monotonic Markers Found */}
          {nonMonotonicMarkers.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                Non-monotonic Elements Found / 发现的非单调元素
              </h3>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex flex-wrap gap-2">
                  {nonMonotonicMarkers.map((m, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm"
                    >
                      "{m.marker}" (P{m.paragraphIndex + 1})
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Logic Issues with Selection */}
          {logicIssues.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
                Logic Pattern Issues / 逻辑模式问题
                <span className="text-sm font-normal text-gray-500">
                  ({logicIssues.length} issues)
                </span>
              </h3>
              <div className="space-y-2">
                {logicIssues.map((issue, idx) => {
                  const isExpanded = expandedIssueIndex === idx;
                  const isSelected = selectedIssueIndices.has(idx);
                  return (
                    <div
                      key={idx}
                      className="bg-yellow-50 border border-yellow-200 rounded-lg overflow-hidden"
                    >
                      <div className="flex items-start">
                        <button
                          onClick={() => toggleIssueSelection(idx)}
                          className="p-4 hover:bg-yellow-100 transition-colors"
                        >
                          {isSelected ? (
                            <CheckSquare className="w-5 h-5 text-blue-600" />
                          ) : (
                            <Square className="w-5 h-5 text-gray-400" />
                          )}
                        </button>

                        <button
                          onClick={() => handleIssueClick(idx)}
                          className="flex-1 px-4 py-3 flex items-center justify-between hover:bg-yellow-100 transition-colors text-left"
                        >
                          <div className="flex items-center gap-3">
                            <AlertCircle className="w-5 h-5 text-yellow-600" />
                            <p className="font-medium text-yellow-800">
                              {issue.descriptionZh || issue.description}
                            </p>
                          </div>
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400" />
                          )}
                        </button>
                      </div>

                      {isExpanded && (
                        <div className="px-4 py-3 border-t border-yellow-200">
                          {isLoadingSuggestion && (
                            <div className="flex items-center justify-center py-6">
                              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                              <span className="ml-2 text-gray-600">Loading suggestion...</span>
                            </div>
                          )}

                          {!isLoadingSuggestion && issueSuggestion && (
                            <div className="space-y-4">
                              <div>
                                <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                  诊断 / Diagnosis
                                </h4>
                                <p className="text-sm text-gray-700">
                                  {issueSuggestion.diagnosisZh}
                                </p>
                              </div>

                              {issueSuggestion.strategies && issueSuggestion.strategies.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                    修改策略 / Modification Strategies
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

                              {issueSuggestion.priorityTipsZh && issueSuggestion.priorityTipsZh.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                    优先建议 / Priority Tips
                                  </h4>
                                  <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                                    {issueSuggestion.priorityTipsZh.map((tip, tIdx) => (
                                      <li key={tIdx}>{tip}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}

                          {!isLoadingSuggestion && !issueSuggestion && (
                            <button
                              onClick={() => loadIssueSuggestion(idx)}
                              className="w-full text-left text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 p-2 rounded transition-colors"
                            >
                              🔍 点击加载详细建议 / Click to load detailed suggestion
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Batch Actions */}
          {logicIssues.length > 0 && (
            <div className="mb-6 pb-6 border-b">
              <div className="flex items-center justify-between mb-4">
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
                    <Sparkles className="w-4 h-4 mr-2" />
                    生成Prompt / Generate Prompt
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
                    <Wand2 className="w-4 h-4 mr-2" />
                    AI修改 / AI Modify
                  </Button>
                </div>
              </div>

              {/* Confirm Dialog */}
              {showMergeConfirm && (
                <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-semibold text-blue-900 mb-2">
                    {mergeMode === 'prompt' ? '生成修改提示词 / Generate Prompt' : 'AI直接修改 / AI Direct Modify'}
                  </h4>
                  <p className="text-sm text-blue-700 mb-3">
                    已选择 {selectedIssueIndices.size} 个问题
                  </p>
                  <textarea
                    placeholder="附加说明（可选）/ Additional notes (optional)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mb-3"
                    rows={2}
                    value={mergeUserNotes}
                    onChange={(e) => setMergeUserNotes(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={executeMergeModify}
                      disabled={isMerging}
                    >
                      {isMerging ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>确认 / Confirm</>
                      )}
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setShowMergeConfirm(false)}
                      disabled={isMerging}
                    >
                      取消 / Cancel
                    </Button>
                  </div>
                </div>
              )}

              {/* Merge Result */}
              {mergeResult && (
                <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  {mergeResult.type === 'prompt' ? (
                    <>
                      <h4 className="font-semibold text-green-900 mb-2">
                        ✅ 提示词已生成 / Prompt Generated
                      </h4>
                      <div className="bg-white p-3 rounded border border-green-300 mb-3">
                        <pre className="text-sm whitespace-pre-wrap text-gray-800">
                          {mergeResult.promptZh || mergeResult.prompt}
                        </pre>
                      </div>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => copyToClipboard(mergeResult.promptZh || mergeResult.prompt || '', setCopiedMergePrompt)}
                      >
                        {copiedMergePrompt ? (
                          <>
                            <Check className="w-4 h-4 mr-2" />
                            已复制 / Copied
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4 mr-2" />
                            复制 / Copy
                          </>
                        )}
                      </Button>
                    </>
                  ) : (
                    <>
                      <h4 className="font-semibold text-green-900 mb-2">
                        ✅ AI修改完成 / AI Modification Complete
                      </h4>
                      <p className="text-sm text-green-700 mb-2">
                        {mergeResult.changesSummaryZh} ({mergeResult.changesCount} 处修改)
                      </p>

                      {/* Preview of modified text - full content with scrollable area */}
                      {/* 修改后内容预览 - 完整内容可滚动 */}
                      <div className="bg-white p-3 rounded border border-green-300 mb-3 max-h-96 overflow-y-auto">
                        <p className="text-xs text-gray-500 mb-1">
                          修改后内容 / Modified Content ({mergeResult.modifiedText?.length || 0} 字符):
                        </p>
                        <pre className="text-sm whitespace-pre-wrap text-gray-800 font-mono">
                          {mergeResult.modifiedText}
                        </pre>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={handleAcceptModification}
                        >
                          <Check className="w-4 h-4 mr-2" />
                          采纳修改（填入下方输入框）
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={handleRegenerate}
                          disabled={regenerateCount >= MAX_REGENERATE || isMerging}
                        >
                          {isMerging ? (
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          ) : (
                            <RotateCcw className="w-4 h-4 mr-2" />
                          )}
                          重新生成 ({regenerateCount}/{MAX_REGENERATE})
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setMergeResult(null)}
                        >
                          <X className="w-4 h-4 mr-2" />
                          取消
                        </Button>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        💡 点击"采纳修改"后，内容会自动填入下方文本框，您可以继续编辑后再应用
                      </p>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {/* No issues */}
          {progressionConfig.risk === 'low' && logicIssues.length === 0 && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">
                  Natural Logic Pattern Detected
                </h3>
                <p className="text-green-600 mt-1">
                  检测到自然的逻辑模式。包含回溯、对比和条件等非单调元素。
                </p>
              </div>
            </div>
          )}

          {/* Processing time */}
          {result.processingTimeMs && (
            <p className="text-sm text-gray-500 mb-6">
              Analysis completed in {result.processingTimeMs}ms
            </p>
          )}

          {/* Document Modification Section */}
          <div id="modify-section" className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              修改文档并应用 / Modify Document and Apply
            </h3>

            {/* Mode selector */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setModifyMode('file')}
                className={clsx(
                  'flex-1 py-3 px-4 rounded-lg border-2 transition-colors flex flex-col items-center',
                  modifyMode === 'file'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-600 hover:border-gray-400'
                )}
              >
                <Upload className="w-5 h-5 mb-1" />
                <span className="text-sm font-medium">上传修改后的文件</span>
                <span className="text-xs text-gray-500">Upload Modified File</span>
              </button>
              <button
                onClick={() => setModifyMode('text')}
                className={clsx(
                  'flex-1 py-3 px-4 rounded-lg border-2 transition-colors flex flex-col items-center',
                  modifyMode === 'text'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-600 hover:border-gray-400'
                )}
              >
                <Type className="w-5 h-5 mb-1" />
                <span className="text-sm font-medium">输入修改后的内容</span>
                <span className="text-xs text-gray-500">Input Modified Content</span>
              </button>
            </div>

            {/* File upload mode */}
            {modifyMode === 'file' && (
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-600 mb-3">
                  支持 TXT 和 DOCX 格式，最大 10MB
                  <br />
                  <span className="text-gray-400">Supports TXT and DOCX formats, max 10MB</span>
                </p>
                <input
                  type="file"
                  accept=".txt,.docx"
                  onChange={handleFileChange}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                {newFile && (
                  <p className="mt-2 text-sm text-green-600">
                    ✓ {newFile.name} ({(newFile.size / 1024).toFixed(2)} KB)
                  </p>
                )}
              </div>
            )}

            {/* Text input mode */}
            {modifyMode === 'text' && (
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-600 mb-3">
                  在下方输入修改后的文本内容，AI修改结果会自动填入此处
                  <br />
                  <span className="text-gray-400">Enter modified text below. AI modification results will auto-fill here.</span>
                </p>
                <textarea
                  value={newText}
                  onChange={(e) => setNewText(e.target.value)}
                  placeholder="粘贴或输入修改后的文本内容... / Paste or type modified text content..."
                  className="w-full h-64 px-3 py-2 border border-gray-300 rounded-lg resize-y font-mono text-sm"
                />
                <div className="mt-2 flex items-center justify-between">
                  <p className="text-sm text-gray-500">
                    {newText.length} 字符 / characters
                  </p>
                  {newText && (
                    <button
                      onClick={() => setNewText('')}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      清空 / Clear
                    </button>
                  )}
                </div>
              </div>
            )}

            {uploadError && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                {uploadError}
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
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    处理中...
                  </>
                ) : (
                  <>
                    <ArrowRight className="w-4 h-4 mr-2" />
                    应用并进行下一步 / Apply and Continue
                  </>
                )}
              </Button>
            </div>
          </div>
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
            Back: Uniformity / 上一步：均匀性
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
