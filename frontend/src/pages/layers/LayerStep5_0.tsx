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
  BookOpen,
  FileText,
  RefreshCw,
  Hash,
  BarChart3,
  AlertTriangle,
  Sparkles,
  Edit3,
  Upload,
  Check,
  X,
  Lock,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import { useSubstepStateStore } from '../../stores/substepStateStore';
import {
  lexicalLayerApi,
  documentLayerApi,
  LexicalContextResponse,
  WordFrequency,
  LockedTermStatus,
  DetectionIssue,
} from '../../services/analysisApi';

/**
 * Layer Step 5.0 - Lexical Context Preparation
 * 步骤 5.0 - 词汇环境准备
 *
 * This is the foundational step for Layer 1 (Lexical Level Analysis).
 * Analyzes vocabulary statistics and prepares context for lexical analysis.
 *
 * 这是第1层（词汇级分析）的基础步骤。
 * 分析词汇统计并为词汇分析准备上下文。
 *
 * Functions:
 * - Analyze vocabulary statistics (total words, unique words, richness)
 * - Calculate Type-Token Ratio (TTR)
 * - Identify overused words
 * - Verify locked terms status
 *
 * 功能：
 * - 分析词汇统计（总词数、唯一词数、丰富度）
 * - 计算类型-词符比（TTR）
 * - 识别过度使用的词汇
 * - 验证锁定词汇状态
 */

// Response type for issue suggestions
// 问题建议响应类型
interface IssueSuggestionResponse {
  analysis: string;
  suggestions: string[];
  exampleFix?: string;
}

// Response type for modify prompt
// 修改提示响应类型
interface ModifyPromptResponse {
  prompt: string;
  promptZh?: string;
  issuesSummaryZh?: string;
}

// Response type for apply modify
// 应用修改响应类型
interface ApplyModifyResponse {
  modifiedText: string;
  changesSummary?: string;
  changesCount?: number;
}

interface LayerStep5_0Props {
  documentIdProp?: string;
  onComplete?: (result: LexicalContextResponse) => void;
  showNavigation?: boolean;
  sentenceContext?: Record<string, unknown>;
}

export default function LayerStep5_0({
  documentIdProp,
  onComplete,
  showNavigation = true,
  sentenceContext,
}: LayerStep5_0Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // Substep state store for caching modified text
  // 子步骤状态存储，用于缓存修改后的文本
  const substepStore = useSubstepStateStore();

  // Helper function to check if documentId is valid
  // 检查documentId是否有效的辅助函数
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

  // Update session step
  // 更新会话步骤
  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer1-step5-0').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<LexicalContextResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedSection, setExpandedSection] = useState<string | null>('stats');

  // Issues derived from analysis result
  // 从分析结果派生的问题列表
  const [lexicalIssues, setLexicalIssues] = useState<DetectionIssue[]>([]);

  // Issue selection for merge modify
  // 用于合并修改的问题选择
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());

  // Click-expand state for individual issue analysis
  // 点击展开状态，用于单个问题分析
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

  // Issue suggestion state (LLM-based detailed suggestions)
  // 问题建议状态（基于LLM的详细建议）
  const [issueSuggestion, setIssueSuggestion] = useState<IssueSuggestionResponse | null>(null);
  // Per-issue suggestion cache to avoid redundant API calls
  // 每个问题的建议缓存，避免重复API调用
  const suggestionCacheRef = useRef<Map<number, IssueSuggestionResponse>>(new Map());
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);

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

  const loadDocumentText = useCallback(async (docId: string) => {
    try {
      // Initialize substep store for session if needed
      // 如果需要，为会话初始化子步骤存储
      if (sessionId && substepStore.currentSessionId !== sessionId) {
        await substepStore.initForSession(sessionId);
      }

      // LayerStep5_0 is the first step, just use originalText
      // LayerStep5_0 是第一步，直接使用 originalText
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
  }, [sessionId, substepStore]);

  // Run analysis when document is loaded
  // 文档加载后运行分析
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
      // Call actual API
      // 调用实际API
      const analysisResult = await lexicalLayerApi.prepareContext(
        documentText,
        sessionId || undefined
      );

      setResult(analysisResult);

      // Create issues from analysis result
      // 从分析结果创建问题列表
      const issues: DetectionIssue[] = [];

      // Check vocabulary richness
      // 检查词汇丰富度
      if (analysisResult.vocabularyStats.vocabularyRichness < 0.35) {
        issues.push({
          type: 'low_vocabulary_richness',
          description: `Low vocabulary richness (${(analysisResult.vocabularyStats.vocabularyRichness * 100).toFixed(1)}%) - may indicate AI repetition`,
          descriptionZh: `词汇丰富度较低 (${(analysisResult.vocabularyStats.vocabularyRichness * 100).toFixed(1)}%) - 可能表示AI重复`,
          severity: 'high',
          layer: 'lexical',
        });
      }

      // Check TTR
      // 检查TTR
      if (analysisResult.vocabularyStats.ttr < 0.4) {
        issues.push({
          type: 'low_ttr',
          description: `Low Type-Token Ratio (${(analysisResult.vocabularyStats.ttr * 100).toFixed(1)}%) - AI text often has lower TTR`,
          descriptionZh: `类型-词符比较低 (${(analysisResult.vocabularyStats.ttr * 100).toFixed(1)}%) - AI文本通常TTR较低`,
          severity: 'medium',
          layer: 'lexical',
        });
      }

      // Check for overused words
      // 检查过度使用的词汇
      if (analysisResult.overusedWords && analysisResult.overusedWords.length > 0) {
        issues.push({
          type: 'overused_words',
          description: `${analysisResult.overusedWords.length} overused words detected: ${analysisResult.overusedWords.slice(0, 5).join(', ')}`,
          descriptionZh: `检测到 ${analysisResult.overusedWords.length} 个过度使用的词汇: ${analysisResult.overusedWords.slice(0, 5).join(', ')}`,
          severity: 'medium',
          layer: 'lexical',
        });
      }

      // Check locked terms
      // 检查锁定词汇
      const missingTerms = analysisResult.lockedTermsStatus?.filter(t => !t.found) || [];
      if (missingTerms.length > 0) {
        issues.push({
          type: 'missing_locked_terms',
          description: `${missingTerms.length} locked terms not found: ${missingTerms.map(t => t.term).join(', ')}`,
          descriptionZh: `${missingTerms.length} 个锁定词汇未找到: ${missingTerms.map(t => t.term).join(', ')}`,
          severity: 'high',
          layer: 'lexical',
        });
      }

      // Add issues from API response
      // 添加API响应中的问题
      if (analysisResult.issues) {
        issues.push(...analysisResult.issues);
      }

      setLexicalIssues(issues);

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

  // Load detailed suggestion for a single issue (LLM-based) with caching
  // 为单个问题加载详细建议（基于LLM），支持缓存
  const loadIssueSuggestion = useCallback(async (index: number) => {
    const issue = lexicalIssues[index];
    if (!issue || !documentId) return;

    // Check cache first
    // 先检查缓存
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
        suggestions: response.strategies?.map((s: { nameZh: string; descriptionZh: string }) => `${s.nameZh}: ${s.descriptionZh}`) || [],
        exampleFix: response.strategies?.[0]?.exampleAfter || '',
      };
      suggestionCacheRef.current.set(index, suggestion);
      setIssueSuggestion(suggestion);
    } catch (err) {
      console.error('Failed to load suggestion:', err);
      setSuggestionError('Failed to load detailed suggestion / 加载详细建议失败');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [lexicalIssues, documentId]);

  // Handle issue click to expand and auto-load suggestions
  // 处理问题点击展开并自动加载建议
  const handleIssueClick = useCallback(async (index: number) => {
    if (expandedIssueIndex === index) {
      setExpandedIssueIndex(null);
      setIssueSuggestion(null);
      return;
    }
    setExpandedIssueIndex(index);
    await loadIssueSuggestion(index);
  }, [expandedIssueIndex, loadIssueSuggestion]);

  // Toggle issue selection for checkbox only
  // 仅用于复选框的问题选择切换
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
    setSelectedIssueIndices(new Set(lexicalIssues.map((_, idx) => idx)));
  }, [lexicalIssues]);

  // Deselect all issues
  // 取消全选所有问题
  const deselectAllIssues = useCallback(() => {
    setSelectedIssueIndices(new Set());
  }, []);

  // Execute merge modify
  // 执行合并修改
  const executeMergeModify = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentId) return;

    setIsMerging(true);
    setShowMergeConfirm(false);

    try {
      const selectedIssues = Array.from(selectedIssueIndices).map(i => lexicalIssues[i]);

      if (mergeMode === 'prompt') {
        const response = await documentLayerApi.generateModifyPrompt(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult(response as ModifyPromptResponse);
      } else {
        const response = await documentLayerApi.applyModify(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult(response as ApplyModifyResponse);
      }
    } catch (err) {
      console.error('Merge modify failed:', err);
      setError('Merge modify failed / 合并修改失败');
    } finally {
      setIsMerging(false);
    }
  }, [selectedIssueIndices, documentId, lexicalIssues, mergeMode, mergeUserNotes, sessionId]);

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
      // 将修改后的文本保存到子步骤存储
      if (sessionId && modifiedText) {
        await substepStore.saveModifiedText('step1-0', modifiedText);
        await substepStore.markCompleted('step1-0');
        console.log('[LayerStep5_0] Saved modified text to substep store');
      }

      // Navigate to next step with same document ID
      // 使用相同的文档ID导航到下一步
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer1-step5-1/${documentId}?${params.toString()}`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload modified document / 上传修改后的文档失败');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate, documentId, substepStore]);

  // Navigate to next step
  // 导航到下一步
  const goToNextStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer1-step5-1/${documentId}?${params.toString()}`);
  };

  // Navigate to previous step (Layer 2 last step)
  // 导航到上一步（Layer 2 最后一步）
  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer2-step4-console/${documentId}?${params.toString()}`);
  };

  // Get risk level color
  // 获取风险等级颜色
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'text-green-600 bg-green-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'high':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  // Toggle section expansion
  // 切换部分展开状态
  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const hasSelectedIssues = selectedIssueIndices.size > 0;

  // Render loading state
  // 渲染加载状态
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage message="Loading document... / 加载文档中..." />
      </div>
    );
  }

  // Render error state
  // 渲染错误状态
  if (error && !result) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center gap-2 text-red-700">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
        <Button onClick={runAnalysis} className="mt-4" variant="outline">
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
            <div className="p-2 bg-indigo-100 rounded-lg">
              <BookOpen className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 5.0: Lexical Context Preparation
              </h2>
              <p className="text-sm text-gray-500">
                步骤 5.0: 词汇环境准备
              </p>
            </div>
          </div>
          {isAnalyzing && (
            <div className="flex items-center gap-2 text-indigo-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing... / 分析中...</span>
            </div>
          )}
        </div>

        <p className="text-gray-600 mb-4">
          Analyzes vocabulary statistics and prepares context for lexical-level analysis.
          <br />
          <span className="text-gray-500">
            分析词汇统计并为词汇级分析准备上下文。
          </span>
        </p>

        {/* Summary Stats */}
        {result && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className="bg-indigo-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-indigo-600 mb-1">
                <Hash className="w-4 h-4" />
                <span className="text-sm font-medium">Total Words</span>
              </div>
              <div className="text-2xl font-bold text-indigo-700">
                {result.vocabularyStats?.totalWords || 0}
              </div>
              <div className="text-xs text-indigo-500">总词数</div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-purple-600 mb-1">
                <FileText className="w-4 h-4" />
                <span className="text-sm font-medium">Unique Words</span>
              </div>
              <div className="text-2xl font-bold text-purple-700">
                {result.vocabularyStats?.uniqueWords || 0}
              </div>
              <div className="text-xs text-purple-500">唯一词数</div>
            </div>

            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-blue-600 mb-1">
                <BarChart3 className="w-4 h-4" />
                <span className="text-sm font-medium">TTR</span>
              </div>
              <div className="text-2xl font-bold text-blue-700">
                {((result.vocabularyStats?.ttr || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-blue-500">类型-词符比</div>
            </div>

            <div className={clsx(
              'rounded-lg p-4',
              result.riskLevel === 'low' ? 'bg-green-50' :
              result.riskLevel === 'medium' ? 'bg-yellow-50' : 'bg-red-50'
            )}>
              <div className={clsx(
                'flex items-center gap-2 mb-1',
                result.riskLevel === 'low' ? 'text-green-600' :
                result.riskLevel === 'medium' ? 'text-yellow-600' : 'text-red-600'
              )}>
                {result.riskLevel === 'low' ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <AlertCircle className="w-4 h-4" />
                )}
                <span className="text-sm font-medium">Risk Level</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                result.riskLevel === 'low' ? 'text-green-700' :
                result.riskLevel === 'medium' ? 'text-yellow-700' : 'text-red-700'
              )}>
                {result.riskLevel?.toUpperCase() || 'N/A'}
              </div>
              <div className={clsx(
                'text-xs',
                result.riskLevel === 'low' ? 'text-green-500' :
                result.riskLevel === 'medium' ? 'text-yellow-500' : 'text-red-500'
              )}>风险等级</div>
            </div>
          </div>
        )}
      </div>

      {/* Issues Section with Selection and Click-Expand */}
      {/* 问题部分（带选择和点击展开功能） */}
      {lexicalIssues.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              Detected Issues / 检测到的问题
              <span className="text-sm font-normal text-gray-500">
                ({selectedIssueIndices.size}/{lexicalIssues.length} selected / 已选择)
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
            {lexicalIssues.map((issue, idx) => (
              <div key={idx} className="space-y-0">
                <div
                  className={clsx(
                    'w-full text-left p-3 rounded-lg border transition-all',
                    expandedIssueIndex === idx
                      ? 'bg-indigo-50 border-indigo-300'
                      : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  )}
                >
                  <div className="flex items-start gap-3">
                    {/* Checkbox - separate click handler */}
                    {/* 复选框 - 独立点击处理 */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleIssueSelection(idx);
                      }}
                      className={clsx(
                        'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5 cursor-pointer',
                        selectedIssueIndices.has(idx)
                          ? 'bg-indigo-600 border-indigo-600'
                          : 'border-gray-300 hover:border-indigo-400'
                      )}
                    >
                      {selectedIssueIndices.has(idx) && (
                        <Check className="w-3 h-3 text-white" />
                      )}
                    </button>
                    {/* Content - click to expand */}
                    {/* 内容 - 点击展开 */}
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
                        {expandedIssueIndex === idx ? (
                          <ChevronUp className="w-4 h-4 text-gray-400 ml-auto" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-gray-400 ml-auto" />
                        )}
                      </div>
                      <p className="text-gray-900 mt-1">{issue.description}</p>
                      <p className="text-gray-600 text-sm">{issue.descriptionZh}</p>
                    </button>
                  </div>
                </div>
                {/* Expanded content section */}
                {/* 展开内容部分 */}
                {expandedIssueIndex === idx && (
                  <div className="ml-8 mt-2 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                    {isLoadingSuggestion ? (
                      <div className="flex items-center gap-2 text-purple-600">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Loading suggestions... / 加载建议中...</span>
                      </div>
                    ) : suggestionError ? (
                      <div className="text-red-600">{suggestionError}</div>
                    ) : issueSuggestion ? (
                      <div className="space-y-3">
                        <h4 className="font-semibold text-purple-900 flex items-center gap-2">
                          <Sparkles className="w-4 h-4" />
                          AI Suggestions / AI建议
                        </h4>
                        <div>
                          <h5 className="text-sm font-medium text-purple-800">Analysis / 分析:</h5>
                          <p className="text-purple-700 mt-1">{issueSuggestion.analysis}</p>
                        </div>
                        {issueSuggestion.suggestions && issueSuggestion.suggestions.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium text-purple-800">Suggestions / 建议:</h5>
                            <ul className="list-disc list-inside mt-1 space-y-1">
                              {issueSuggestion.suggestions.map((s, i) => (
                                <li key={i} className="text-purple-700">{s}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {issueSuggestion.exampleFix && (
                          <div>
                            <h5 className="text-sm font-medium text-purple-800">Example Fix / 示例修复:</h5>
                            <pre className="mt-1 p-2 bg-white rounded text-sm text-gray-800 overflow-x-auto">
                              {issueSuggestion.exampleFix}
                            </pre>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-gray-500">No suggestions available / 暂无建议</p>
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
                disabled={selectedIssueIndices.size === 0}
                onClick={() => {
                  setMergeMode('prompt');
                  setShowMergeConfirm(true);
                }}
              >
                <Edit3 className="w-4 h-4 mr-2" />
                Generate Prompt / 生成提示
              </Button>
              <Button
                variant="primary"
                size="sm"
                disabled={selectedIssueIndices.size === 0}
                onClick={() => {
                  setMergeMode('apply');
                  setShowMergeConfirm(true);
                }}
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

      {/* Top Words Section */}
      {result && result.topWords && result.topWords.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={() => toggleSection('topwords')}
          >
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-indigo-600" />
              Top Words / 高频词汇
            </h3>
            {expandedSection === 'topwords' ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </div>

          {expandedSection === 'topwords' && (
            <div className="mt-4 space-y-2">
              {result.topWords.slice(0, 20).map((word: WordFrequency, index: number) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 flex items-center justify-center bg-indigo-100 text-indigo-600 rounded-full text-xs font-medium">
                      {index + 1}
                    </span>
                    <span className="font-medium text-gray-700">{word.word}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-500">{word.count} times</span>
                    <span className="text-sm text-gray-400">{word.percentage.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Locked Terms Status */}
      {result && result.lockedTermsStatus && result.lockedTermsStatus.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={() => toggleSection('locked')}
          >
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Lock className="w-5 h-5 text-indigo-600" />
              Locked Terms Status / 锁定词汇状态
            </h3>
            {expandedSection === 'locked' ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </div>

          {expandedSection === 'locked' && (
            <div className="mt-4 space-y-2">
              {result.lockedTermsStatus.map((term: LockedTermStatus, index: number) => (
                <div
                  key={index}
                  className={clsx(
                    'flex items-center justify-between p-3 rounded-lg border',
                    term.found ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                  )}
                >
                  <div className="flex items-center gap-3">
                    {term.found ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-600" />
                    )}
                    <span className={clsx(
                      'font-medium',
                      term.found ? 'text-green-700' : 'text-red-700'
                    )}>
                      {term.term}
                    </span>
                  </div>
                  <span className={clsx(
                    'text-sm',
                    term.found ? 'text-green-600' : 'text-red-600'
                  )}>
                    {term.found ? `Found ${term.count} times` : 'Not found'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* No issues message */}
      {lexicalIssues.length === 0 && result && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-green-800">
              Vocabulary Statistics Look Good
            </h3>
            <p className="text-green-600 mt-1">
              词汇统计良好。未检测到明显问题。
            </p>
          </div>
        </div>
      )}

      {/* Document Modification Section */}
      {/* 文档修改部分 */}
      {result && (
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
                  ? 'bg-indigo-600 text-white'
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
                  ? 'bg-indigo-600 text-white'
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
                className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 transition-colors"
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 min-h-[200px]"
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
      )}

      {/* Recommendations */}
      {result && result.recommendations && result.recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-600" />
            Recommendations / 建议
          </h3>
          <ul className="space-y-2">
            {result.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-yellow-500 mt-1">*</span>
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

      {/* Navigation */}
      {showNavigation && (
        <div className="flex justify-between items-center pt-4 border-t">
          <Button
            variant="outline"
            onClick={goToPreviousStep}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Previous: Layer 2 Console
          </Button>
          <Button
            onClick={() => setShowSkipConfirm(true)}
            disabled={!result}
            className="flex items-center gap-2"
          >
            Skip and Continue / 跳过并继续
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
