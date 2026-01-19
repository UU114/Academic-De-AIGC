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
  ArrowRightLeft,
  Link2,
  Unlink,
  MessageSquare,
  Zap,
  Edit3,
  Sparkles,
  Upload,
  Check,
  X,
  FileText,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import { useSubstepStateStore } from '../../stores/substepStateStore';
import {
  sectionLayerApi,
  documentLayerApi,
  SectionTransitionResponse,
  DetectionIssue,
  IssueSuggestionResponse,
  ModifyPromptResponse,
  ApplyModifyResponse,
} from '../../services/analysisApi';

/**
 * Layer Step 2.4 - Section Transition Detection
 * 步骤 2.4 - 章节衔接与过渡检测
 *
 * Detects:
 * - E: Explicit Transition Words (显性过渡词检测)
 * - F: Transition Strength Classification (过渡词强度分类)
 * - G: Section Semantic Echo (章节间语义回声)
 * - H: Section Opener Patterns (章节开头模式)
 *
 * Priority: (Medium - depends on section identification)
 * 优先级: (中 - 依赖章节识别)
 */

// Transition strength configuration
// 过渡强度配置
const TRANSITION_STRENGTH_CONFIG = {
  strong: { label: 'Strong', labelZh: '强过渡', color: 'red', icon: Link2 },
  moderate: { label: 'Moderate', labelZh: '中等', color: 'yellow', icon: ArrowRightLeft },
  weak: { label: 'Weak', labelZh: '弱过渡', color: 'blue', icon: Unlink },
  implicit: { label: 'Implicit', labelZh: '隐性', color: 'green', icon: MessageSquare },
};

interface LayerStep2_4Props {
  documentIdProp?: string;
  onComplete?: (result: SectionTransitionResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep2_4({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep2_4Props) {
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
      sessionApi.updateStep(sessionId, 'layer4-step2-4').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<SectionTransitionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedTransition, setExpandedTransition] = useState<number | null>(null);
  const [showAiSuggestion, setShowAiSuggestion] = useState(false);

  // Issues derived from analysis result
  // 从分析结果派生的问题列表
  const [transitionIssues, setTransitionIssues] = useState<DetectionIssue[]>([]);

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

  // Load document - wait for session fetch to complete first
  // 加载文档 - 首先等待 session 获取完成
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
    // Get substep state store for checking previous step's modified text
    // 获取子步骤状态存储，用于检查前一个步骤的修改文本
    const substepStore = useSubstepStateStore.getState();

    try {
      // Initialize substep store for session if not already done
      if (sessionId && substepStore.currentSessionId !== sessionId) {
        await substepStore.initForSession(sessionId);
      }

      // Check for modified text from previous steps (most recent first)
      const previousSteps = ['step2-3', 'step2-2', 'step2-1', 'step2-0'];
      let foundModifiedText: string | null = null;

      for (const stepName of previousSteps) {
        const stepState = substepStore.getState(stepName);
        if (stepState?.modifiedText) {
          console.log(`[LayerStep2_4] Using modified text from ${stepName}`);
          foundModifiedText = stepState.modifiedText;
          break;
        }
      }

      if (foundModifiedText) {
        setDocumentText(foundModifiedText);
      } else {
        // Fallback to original document text
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

  // Run analysis
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
      // Call actual API
      // 调用实际API
      const analysisResult = await sectionLayerApi.analyzeTransitions(
        documentText,
        undefined,
        undefined,
        sessionId || undefined
      );

      setResult(analysisResult);

      // Create issues from analysis result
      // 从分析结果创建问题列表
      const issues: DetectionIssue[] = [];

      // Check for too many explicit transitions
      // 检查显性过渡词过多
      if (analysisResult.explicitRatio > 0.7) {
        issues.push({
          type: 'excessive_explicit_transitions',
          description: `Explicit transition ratio is too high (${Math.round(analysisResult.explicitRatio * 100)}%)`,
          descriptionZh: `显性过渡词比例过高 (${Math.round(analysisResult.explicitRatio * 100)}%)`,
          severity: 'high',
          layer: 'section',
          location: 'Section transitions',
        });
      }

      // Check for low semantic echo
      // 检查语义回声过低
      if (analysisResult.avgSemanticEcho < 0.4) {
        issues.push({
          type: 'low_semantic_echo',
          description: `Average semantic echo is low (${analysisResult.avgSemanticEcho.toFixed(2)})`,
          descriptionZh: `平均语义回声较低 (${analysisResult.avgSemanticEcho.toFixed(2)})`,
          severity: 'medium',
          layer: 'section',
          location: 'Section transitions',
        });
      }

      // Check for formulaic openers
      // 检查公式化开头
      if (analysisResult.formulaicOpenerCount > 0) {
        issues.push({
          type: 'formulaic_openers',
          description: `Found ${analysisResult.formulaicOpenerCount} formulaic section opener(s)`,
          descriptionZh: `发现${analysisResult.formulaicOpenerCount}个公式化章节开头`,
          severity: analysisResult.formulaicOpenerCount > 2 ? 'high' : 'medium',
          layer: 'section',
          location: 'Section openers',
        });
      }

      // Check individual transitions
      // 检查单个过渡
      analysisResult.transitions.forEach((transition) => {
        if (transition.hasExplicitTransition && transition.explicitWords.length > 1) {
          issues.push({
            type: 'multiple_explicit_words',
            description: `Section ${transition.toSectionIndex + 1} uses multiple explicit connectors: ${transition.explicitWords.join(', ')}`,
            descriptionZh: `章节${transition.toSectionIndex + 1}使用了多个显性连接词：${transition.explicitWords.join(', ')}`,
            severity: 'low',
            layer: 'section',
            location: `Section ${transition.fromSectionIndex + 1} -> ${transition.toSectionIndex + 1}`,
          });
        }
        if (transition.isFormulaicOpener) {
          issues.push({
            type: 'formulaic_opener_pattern',
            description: `Section ${transition.toSectionIndex + 1} has formulaic opener pattern: "${transition.openerPattern}"`,
            descriptionZh: `章节${transition.toSectionIndex + 1}使用公式化开头模式："${transition.openerPattern}"`,
            severity: 'medium',
            layer: 'section',
            location: `Section ${transition.toSectionIndex + 1}`,
          });
        }
      });

      // Add issues from the result if available
      // 如果有结果中的问题也添加进来
      if (analysisResult.issues) {
        issues.push(...analysisResult.issues);
      }

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

  // Load detailed suggestion for a specific issue (LLM-based) with caching
  // 为特定问题加载详细建议（基于LLM），带缓存
  const loadIssueSuggestion = useCallback(async (index: number) => {
    const issue = transitionIssues[index];
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
      const suggestion: IssueSuggestionResponse = {
        analysis: response.diagnosisZh || '',
        suggestions: response.strategies?.map(s => `${s.nameZh}: ${s.descriptionZh}`) || [],
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
  }, [transitionIssues, documentId]);

  // Handle issue click - toggle expand and auto-load suggestion
  // 处理问题点击 - 切换展开并自动加载建议
  const handleIssueClick = useCallback(async (index: number) => {
    const issue = transitionIssues[index];
    if (!issue || !documentId) return;

    // Collapse if already expanded
    // 如果已展开则收起
    if (expandedIssueIndex === index) {
      setExpandedIssueIndex(null);
      setIssueSuggestion(null);
      return;
    }

    // Expand and load suggestion (from cache if available)
    // 展开并加载建议（如有缓存则从缓存加载）
    setExpandedIssueIndex(index);
    await loadIssueSuggestion(index);
  }, [transitionIssues, documentId, expandedIssueIndex, loadIssueSuggestion]);

  // Toggle issue selection (for checkbox only)
  // 切换问题选择（仅用于复选框）
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
        const response = await documentLayerApi.generateModifyPrompt(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult({
          prompt: response.prompt,
        } as ModifyPromptResponse);
      } else {
        const response = await documentLayerApi.applyModify(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult({
          modifiedText: response.modifiedText,
          changesSummary: response.changesSummaryZh,
        } as ApplyModifyResponse);
      }
    } catch (err) {
      console.error('Merge modify failed:', err);
      setError('Merge modify failed / 合并修改失败');
    } finally {
      setIsMerging(false);
    }
  }, [selectedIssueIndices, documentId, transitionIssues, mergeMode, mergeUserNotes, sessionId]);

  // Handle regenerate
  // 处理重新生成
  const handleRegenerate = useCallback(() => {
    setMergeResult(null);
    setShowMergeConfirm(true);
    setMergeMode('apply');
  }, []);

  // Handle accept modification
  // 处理接受修改
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

  // Handle confirm modification and navigate to next step
  // 处理确认修改并导航到下一步
  const handleConfirmModify = useCallback(async () => {
    setIsUploading(true);
    setError(null);

    // Get substep state store for saving modified text
    // 获取子步骤状态存储，用于保存修改文本
    const substepStore = useSubstepStateStore.getState();

    try {
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
      if (sessionId && modifiedText) {
        await substepStore.saveModifiedText('step2-4', modifiedText);
        await substepStore.markCompleted('step2-4');
        console.log('[LayerStep2_4] Saved modified text to substep store');
      }

      // Navigate with same documentId
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer4-step2-5/${documentId}?${params.toString()}`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload modified document / 上传修改后的文档失败');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate, documentId]);

  // Navigation
  const handleBack = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer4-step2-3/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer4-step2-5/${documentId}?${params.toString()}`);
  };

  const hasSelectedIssues = selectedIssueIndices.size > 0;

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

  const hasHighRisk = result?.riskLevel === 'high';
  const hasExplicitIssue = (result?.explicitRatio || 0) > 0.7;
  const hasEchoIssue = (result?.avgSemanticEcho || 0) < 0.4;

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
          <span>Layer 4 / 第4层</span>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Step 2.4 章节衔接</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Section Transition Detection
        </h1>
        <p className="text-gray-600 mt-1">
          章节衔接与过渡检测 - 检测显性过渡词、过渡强度、语义回声和开头模式
        </p>
      </div>

      {/* Start Analysis / Skip Step */}
      {/* 开始分析 / 跳过此步 */}
      {documentText && !analysisStarted && !isAnalyzing && !result && (
        <div className="mb-6 p-6 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="text-center">
            <ArrowRightLeft className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Analyze / 准备分析</h3>
            <p className="text-gray-600 mb-6">
              Click to analyze section transitions, detect explicit connectors, and semantic echo
              <br />
              <span className="text-gray-500">点击分析章节过渡、检测显性连接词和语义回声</span>
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

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing transitions... / 分析过渡中...</p>
              <p className="text-blue-600 text-sm">Detecting transition words and semantic echoes</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* Summary Stats */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Explicit Ratio */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasExplicitIssue ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <Link2 className={clsx('w-5 h-5', hasExplicitIssue ? 'text-red-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Explicit Ratio / 显性比例</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasExplicitIssue ? 'text-red-600' : 'text-green-600'
              )}>
                {Math.round(result.explicitRatio * 100)}%
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {hasExplicitIssue ? 'Too many explicit (>70%)' : 'Good balance'}
              </p>
            </div>

            {/* Semantic Echo */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasEchoIssue ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <MessageSquare className={clsx('w-5 h-5', hasEchoIssue ? 'text-yellow-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Semantic Echo</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasEchoIssue ? 'text-yellow-600' : 'text-green-600'
              )}>
                {result.avgSemanticEcho.toFixed(2)}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Target: &ge; 0.40 | {hasEchoIssue ? 'Low echo' : 'Good echo'}
              </p>
            </div>

            {/* Strength Distribution */}
            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <ArrowRightLeft className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">Strength Dist.</span>
              </div>
              <div className="flex gap-2 text-sm">
                <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded">
                  S:{result.strengthDistribution['strong'] || 0}
                </span>
                <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded">
                  M:{result.strengthDistribution['moderate'] || 0}
                </span>
                <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded">
                  I:{result.strengthDistribution['implicit'] || 0}
                </span>
              </div>
            </div>

            {/* Formulaic Openers */}
            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">Formulaic Openers</span>
              </div>
              <div className="text-2xl font-bold text-gray-700">
                {result.formulaicOpenerCount}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                of {result.totalTransitions} transitions
              </p>
            </div>
          </div>

          {/* High Risk Alert */}
          {hasHighRisk && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Excessive Explicit Transitions
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：显性过渡词过多。
                  AI倾向于使用"Building on...", "Having established..."等显性连接。
                  建议用语义回声（引用前段关键词）替代显性过渡词。
                </p>
              </div>
            </div>
          )}

          {/* Issues Section with Selection */}
          {/* 问题部分（带选择功能） */}
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
                {transitionIssues.map((issue, idx) => (
                  <div
                    key={idx}
                    className={clsx(
                      'rounded-lg border transition-all',
                      selectedIssueIndices.has(idx)
                        ? 'bg-blue-50 border-blue-300 ring-2 ring-blue-200'
                        : expandedIssueIndex === idx
                        ? 'bg-gray-50 border-gray-300'
                        : 'bg-white border-gray-200 hover:border-gray-300'
                    )}
                  >
                    <div className="p-3 flex items-start gap-3">
                      {/* Checkbox - separate click handler */}
                      {/* 复选框 - 独立的点击处理 */}
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
                      {/* Issue content - click to expand */}
                      {/* 问题内容 - 点击展开 */}
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
                          <span className="text-xs text-blue-500 ml-auto">
                            {expandedIssueIndex === idx ? '▼ Click to collapse' : '▶ Click for AI analysis'}
                          </span>
                        </div>
                        <p className="text-gray-900 mt-1">{issue.description}</p>
                        <p className="text-gray-600 text-sm">{issue.descriptionZh}</p>
                        {issue.location && (
                          <p className="text-gray-500 text-xs mt-1 font-mono">{issue.location}</p>
                        )}
                      </button>
                    </div>
                    {/* Expanded content - LLM analysis */}
                    {/* 展开内容 - LLM分析 */}
                    {expandedIssueIndex === idx && (
                      <div className="px-3 pb-3 pt-0 ml-8 border-t border-gray-200">
                        {isLoadingSuggestion ? (
                          <div className="flex items-center gap-2 py-3 text-blue-600">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span className="text-sm">Loading AI analysis... / 加载AI分析中...</span>
                          </div>
                        ) : issueSuggestion ? (
                          <div className="py-3 space-y-3">
                            <div>
                              <h5 className="text-sm font-medium text-purple-800">Analysis / 分析:</h5>
                              <p className="text-purple-700 text-sm mt-1">{issueSuggestion.analysis}</p>
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
                                <h5 className="text-sm font-medium text-purple-800">Example / 示例:</h5>
                                <pre className="mt-1 p-2 bg-white rounded text-xs text-gray-800 overflow-x-auto">
                                  {issueSuggestion.exampleFix}
                                </pre>
                              </div>
                            )}
                            {suggestionCacheRef.current.has(idx) && (
                              <p className="text-xs text-gray-400">✓ Cached / 已缓存</p>
                            )}
                          </div>
                        ) : suggestionError ? (
                          <div className="py-3 text-red-600 text-sm">{suggestionError}</div>
                        ) : null}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons for Selected Issues */}
          {/* 选中问题的操作按钮 */}
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

          {/* Transition Details */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <ArrowRightLeft className="w-5 h-5 text-blue-600" />
              Section Transition Details / 章节过渡详情
            </h3>
            <div className="bg-white border rounded-lg divide-y">
              {result.transitions.map((transition, idx) => {
                const isExpanded = expandedTransition === idx;
                const strengthKey = transition.transitionStrength as keyof typeof TRANSITION_STRENGTH_CONFIG;
                const strengthConfig = TRANSITION_STRENGTH_CONFIG[strengthKey] || TRANSITION_STRENGTH_CONFIG.implicit;
                const StrengthIcon = strengthConfig.icon;

                return (
                  <div key={idx}>
                    <button
                      onClick={() => setExpandedTransition(isExpanded ? null : idx)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <StrengthIcon className={clsx('w-5 h-5', `text-${strengthConfig.color}-600`)} />
                        <div className="text-left">
                          <span className="font-medium text-gray-900">
                            Section {transition.fromSectionIndex + 1} → Section {transition.toSectionIndex + 1}
                          </span>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={clsx(
                              'px-2 py-0.5 rounded text-xs',
                              `bg-${strengthConfig.color}-100 text-${strengthConfig.color}-700`
                            )}>
                              {strengthConfig.labelZh}
                            </span>
                            {transition.hasExplicitTransition && transition.explicitWords.length > 0 && (
                              <span className="text-sm text-gray-500 truncate max-w-[200px]">
                                "{transition.explicitWords[0]}"
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className={clsx(
                          'text-sm',
                          transition.semanticEchoScore >= 0.4 ? 'text-green-600' : 'text-yellow-600'
                        )}>
                          Echo: {transition.semanticEchoScore.toFixed(2)}
                        </span>
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                    </button>
                    {isExpanded && (
                      <div className="px-4 py-3 bg-gray-50 border-t">
                        <div className="space-y-3">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <h5 className="text-sm font-medium text-gray-700 mb-1">
                                Section Opening / 章节开头
                              </h5>
                              <p className="text-sm text-gray-600 bg-white p-2 rounded border">
                                {transition.openerText || '(Not available)'}
                              </p>
                            </div>
                            <div>
                              <h5 className="text-sm font-medium text-gray-700 mb-1">
                                Opener Pattern / 开头模式
                              </h5>
                              <p className="text-sm text-gray-600 bg-white p-2 rounded border">
                                {transition.openerPattern || '(Unknown)'}
                                {transition.isFormulaicOpener && (
                                  <span className="ml-2 px-1.5 py-0.5 bg-red-100 text-red-700 rounded text-xs">Formulaic</span>
                                )}
                              </p>
                            </div>
                          </div>

                          {transition.echoedKeywords && transition.echoedKeywords.length > 0 && (
                            <div className="p-3 bg-green-50 rounded border border-green-200">
                              <h5 className="text-sm font-medium text-green-700 mb-1">
                                Semantic Echo Keywords / 语义回声关键词
                              </h5>
                              <div className="flex flex-wrap gap-1">
                                {transition.echoedKeywords.map((kw, kwIdx) => (
                                  <span key={kwIdx} className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-sm">
                                    {kw}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {transition.hasExplicitTransition && transition.explicitWords.length > 0 && (
                            <div className="p-3 bg-red-50 rounded border border-red-200">
                              <h5 className="text-sm font-medium text-red-700 mb-1">
                                Explicit Transition Words / 显性过渡词
                              </h5>
                              <div className="flex flex-wrap gap-1 mb-2">
                                {transition.explicitWords.map((word, wIdx) => (
                                  <span key={wIdx} className="px-2 py-0.5 bg-red-100 text-red-800 rounded text-sm">
                                    "{word}"
                                  </span>
                                ))}
                              </div>
                              <p className="text-sm text-red-600">
                                Suggestion: Replace with semantic echo using key concepts from previous section.
                              </p>
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

          {/* No issues message */}
          {transitionIssues.length === 0 && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">
                  Section Transitions Look Good
                </h3>
                <p className="text-green-600 mt-1">
                  章节过渡表现良好。未检测到明显的AI写作模式。
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

            {/* Apply and Continue Button - Style matched with LayerStep2_0 */}
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

          {/* AI Suggestions */}
          {(result.recommendations.length > 0 || result.recommendationsZh.length > 0) && (
            <div className="mb-6">
              <Button
                variant="secondary"
                onClick={() => setShowAiSuggestion(!showAiSuggestion)}
                className="w-full"
              >
                <Zap className="w-4 h-4 mr-2" />
                {showAiSuggestion ? 'Hide Suggestions' : 'View Suggestions / 查看建议'}
              </Button>
              {showAiSuggestion && (
                <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                  <h4 className="font-medium text-purple-800 mb-2">
                    Transition Improvement Suggestions / 过渡改进建议
                  </h4>
                  <ul className="space-y-2 text-purple-700 text-sm">
                    {result.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-purple-500">•</span>
                        <div>
                          <span>{rec}</span>
                          {result.recommendationsZh[idx] && (
                            <span className="block text-purple-600 mt-1">
                              {result.recommendationsZh[idx]}
                            </span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

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
            Back: Internal Structure / 上一步：内部结构
          </Button>
          <Button variant="primary" onClick={() => setShowSkipConfirm(true)} disabled={isAnalyzing || !result}>
            Skip and Continue / 跳过并继续
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
