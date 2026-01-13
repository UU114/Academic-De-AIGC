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
  Copy,
  TrendingUp,
  Zap,
  Target,
  Lightbulb,
  Sparkles,
  Upload,
  FileText,
  Check,
  X,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import { sectionLayerApi, documentLayerApi, InterSectionLogicResponse, DetectionIssue } from '../../services/analysisApi';

/**
 * Layer Step 2.5 - Inter-Section Logic Detection
 * 步骤 2.5 - 章节间逻辑关系检测
 *
 * Detects:
 * - O: Argument Chain Completeness (论证链完整性)
 * - P: Inter-Section Redundancy (章节间信息重复)
 * - Q: Progression Pattern (递进关系检测)
 *
 * This is the final step of Layer 4, handling deep logic analysis.
 * 这是第4层的最后一步，处理深层逻辑分析。
 *
 * Priority: (Low - final analysis step, depends on all previous steps)
 * 优先级: (低 - 最终分析步骤，依赖所有前置步骤)
 */

interface LayerStep2_5Props {
  documentIdProp?: string;
  onComplete?: (result: InterSectionLogicResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep2_5({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep2_5Props) {
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
      sessionApi.updateStep(sessionId, 'layer4-step2-5').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<InterSectionLogicResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedIssue, setExpandedIssue] = useState<string | null>(null);

  // Issue selection and modification states
  const [issues, setIssues] = useState<DetectionIssue[]>([]);
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<number[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [isGeneratingPrompt, setIsGeneratingPrompt] = useState(false);
  const [isApplyingModify, setIsApplyingModify] = useState(false);
  const [generatedPrompt, setGeneratedPrompt] = useState<string>('');

  // Merge confirm dialog states
  const [showMergeConfirm, setShowMergeConfirm] = useState(false);
  const [userNotes, setUserNotes] = useState('');
  const [mergeResult, setMergeResult] = useState<string>('');
  const [showMergeResult, setShowMergeResult] = useState(false);

  // Skip confirmation state
  // 跳过确认状态
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);

  // Document modification states
  const [modifiedText, setModifiedText] = useState<string>('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const isAnalyzingRef = useRef(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  // Create issues from analysis result
  const createIssuesFromResult = useCallback((analysisResult: InterSectionLogicResponse) => {
    const detectedIssues: DetectionIssue[] = [];

    // Issue from chain coherence score (too perfect indicates AI)
    if (analysisResult.chainCoherenceScore > 90) {
      detectedIssues.push({
        id: `chain-coherence-${Date.now()}`,
        type: 'chain_coherence',
        severity: 'high',
        title: 'Overly Perfect Chain Coherence / 论证链过于完美',
        description: `Chain coherence score is ${Math.round(analysisResult.chainCoherenceScore)}%, which is unusually high and may indicate AI-generated content.`,
        descriptionZh: `论证链连贯性得分为 ${Math.round(analysisResult.chainCoherenceScore)}%，异常偏高，可能表明是AI生成的内容。`,
        location: 'Overall document structure',
        suggestion: '',
      });
    }

    // Issues from redundancies
    if (analysisResult.totalRedundancies > 0) {
      analysisResult.redundancies.forEach((redundancy, idx) => {
        detectedIssues.push({
          id: `redundancy-${idx}-${Date.now()}`,
          type: 'redundancy',
          severity: redundancy.severity === 'high' ? 'high' : redundancy.severity === 'medium' ? 'medium' : 'low',
          title: `Redundant Content between Sections / 章节间内容冗余`,
          description: `${redundancy.redundancyType} redundancy found between Section ${redundancy.sectionAIndex + 1} and Section ${redundancy.sectionBIndex + 1}: "${redundancy.redundantContent}"`,
          descriptionZh: `在第 ${redundancy.sectionAIndex + 1} 节和第 ${redundancy.sectionBIndex + 1} 节之间发现 ${redundancy.redundancyType} 类型的冗余: "${redundancy.redundantContent}"`,
          location: `Sections ${redundancy.sectionAIndex + 1} & ${redundancy.sectionBIndex + 1}`,
          suggestion: '',
        });
      });
    }

    // Issue from progression patterns (too linear)
    if (analysisResult.dominantPattern === 'linear' && analysisResult.patternVarietyScore < 20) {
      detectedIssues.push({
        id: `progression-linear-${Date.now()}`,
        type: 'progression_pattern',
        severity: 'medium',
        title: 'Overly Linear Progression Pattern / 递进模式过于线性',
        description: `The dominant pattern is linear with only ${Math.round(analysisResult.patternVarietyScore)}% variety. Human writing typically has more varied progression patterns.`,
        descriptionZh: `主导模式为线性，变化度仅为 ${Math.round(analysisResult.patternVarietyScore)}%。人类写作通常具有更多样化的递进模式。`,
        location: 'Overall progression structure',
        suggestion: '',
      });
    }

    // Issue from pattern variety score (too uniform)
    if (analysisResult.patternVarietyScore < 15) {
      detectedIssues.push({
        id: `pattern-variety-${Date.now()}`,
        type: 'pattern_variety',
        severity: 'medium',
        title: 'Low Pattern Variety / 模式变化度低',
        description: `Pattern variety score is ${Math.round(analysisResult.patternVarietyScore)}%, indicating uniform structure that may appear AI-generated.`,
        descriptionZh: `模式变化度得分为 ${Math.round(analysisResult.patternVarietyScore)}%，表明结构过于统一，可能显得像AI生成。`,
        location: 'Document patterns',
        suggestion: '',
      });
    }

    setIssues(detectedIssues);
  }, []);

  const runAnalysis = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;
    setIsAnalyzing(true);
    setError(null);

    try {
      // Call actual API
      // 调用实际API
      const analysisResult = await sectionLayerApi.analyzeInterSectionLogic(
        documentText,
        undefined,
        undefined,
        sessionId || undefined
      );

      setResult(analysisResult);
      createIssuesFromResult(analysisResult);

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

  // Issue selection handlers
  const toggleIssueSelection = (index: number) => {
    setSelectedIssueIndices(prev =>
      prev.includes(index)
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  const selectAllIssues = () => {
    setSelectedIssueIndices(issues.map((_, idx) => idx));
  };

  const deselectAllIssues = () => {
    setSelectedIssueIndices([]);
  };

  // Load suggestions for selected issues
  const handleLoadSuggestions = async () => {
    if (selectedIssueIndices.length === 0) return;

    setIsLoadingSuggestions(true);
    try {
      const selectedIssues = selectedIssueIndices.map(idx => issues[idx]);
      const response = await documentLayerApi.getIssueSuggestion(
        documentText,
        selectedIssues,
        'step2_5',
        sessionId || undefined
      );

      // Update issues with suggestions
      const updatedIssues = [...issues];
      selectedIssueIndices.forEach((issueIdx, i) => {
        if (response.suggestions && response.suggestions[i]) {
          updatedIssues[issueIdx] = {
            ...updatedIssues[issueIdx],
            suggestion: response.suggestions[i],
          };
        }
      });
      setIssues(updatedIssues);
    } catch (err) {
      console.error('Failed to load suggestions:', err);
      setError('Failed to load suggestions / 加载建议失败');
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  // Generate modify prompt
  const handleGeneratePrompt = async () => {
    if (selectedIssueIndices.length === 0 || !documentId) return;

    setIsGeneratingPrompt(true);
    try {
      const selectedIssues = selectedIssueIndices.map(idx => issues[idx]);
      const response = await documentLayerApi.generateModifyPrompt(
        documentId,
        selectedIssues,
        {
          sessionId: sessionId || undefined,
        }
      );

      setGeneratedPrompt(response.prompt || '');
    } catch (err) {
      console.error('Failed to generate prompt:', err);
      setError('Failed to generate prompt / 生成提示失败');
    } finally {
      setIsGeneratingPrompt(false);
    }
  };

  // Apply AI modification - opens confirm dialog
  const handleApplyModify = () => {
    if (selectedIssueIndices.length === 0) return;
    setShowMergeConfirm(true);
  };

  // Confirm merge and apply
  const handleConfirmMerge = async () => {
    if (!documentId) return;
    setShowMergeConfirm(false);
    setIsApplyingModify(true);

    try {
      const selectedIssues = selectedIssueIndices.map(idx => issues[idx]);
      const response = await documentLayerApi.applyModify(
        documentId,
        selectedIssues,
        {
          sessionId: sessionId || undefined,
          userNotes: userNotes || undefined,
        }
      );

      setMergeResult(response.modifiedText || '');
      setShowMergeResult(true);
    } catch (err) {
      console.error('Failed to apply modification:', err);
      setError('Failed to apply modification / 应用修改失败');
    } finally {
      setIsApplyingModify(false);
    }
  };

  // Accept merge result
  const handleAcceptMerge = () => {
    setModifiedText(mergeResult);
    setShowMergeResult(false);
    setMergeResult('');
    setUserNotes('');
  };

  // Regenerate merge
  const handleRegenerateMerge = () => {
    setShowMergeResult(false);
    setShowMergeConfirm(true);
  };

  // Cancel merge
  const handleCancelMerge = () => {
    setShowMergeResult(false);
    setMergeResult('');
    setUserNotes('');
  };

  // File upload handler
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadedFile(file);

    // Read file content
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      setModifiedText(text);
    };
    reader.readAsText(file);
  };

  // Apply changes and continue to next step
  const handleApplyAndContinue = async () => {
    if (!modifiedText.trim()) {
      setError('Please provide modified document text / 请提供修改后的文档内容');
      return;
    }

    setIsUploading(true);
    try {
      // Upload modified document text directly
      // 直接上传修改后的文档文本
      const response = await documentApi.uploadText(modifiedText);
      const newDocumentId = response.id;

      // Navigate to Layer 3 Step 3.0
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer3-step3-0/${newDocumentId}?${params.toString()}`);
    } catch (err) {
      console.error('Failed to upload modified document:', err);
      setError('Failed to upload document / 上传文档失败');
    } finally {
      setIsUploading(false);
    }
  };

  // Navigation
  const handleBack = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer4-step2-4/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    // Go to Layer 3 Step 3.0 (Paragraph Identification)
    // 跳转到第3层步骤3.0（段落识别）
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer3-step3-0/${documentId}?${params.toString()}`);
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

  const hasHighRisk = result?.riskLevel === 'high';
  const hasChainIssue = (result?.chainCoherenceScore || 0) > 90;
  const hasProgressionIssue = result?.dominantPattern === 'linear' && (result?.patternVarietyScore || 0) < 20;
  const hasRedundancy = (result?.totalRedundancies || 0) > 0;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Loading Overlay for LLM operations */}
      {/* LLM操作加载遮罩 */}
      <LoadingOverlay
        isVisible={isApplyingModify || isGeneratingPrompt}
        operationType={isGeneratingPrompt ? 'prompt' : 'apply'}
        issueCount={selectedIssueIndices.length}
      />

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Layers className="w-4 h-4" />
          <span>Layer 4 / 第4层</span>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Step 2.5 逻辑关系</span>
          <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">FINAL</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Inter-Section Logic Detection
        </h1>
        <p className="text-gray-600 mt-1">
          章节间逻辑关系检测 - 检测论证链完整性、信息重复和递进模式
        </p>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing logic relations... / 分析逻辑关系中...</p>
              <p className="text-blue-600 text-sm">Checking argument chains, redundancy, and progression</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* Summary Stats */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Argument Chain */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasChainIssue ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <Target className={clsx('w-5 h-5', hasChainIssue ? 'text-red-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Chain Score / 链条分数</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasChainIssue ? 'text-red-600' : 'text-green-600'
              )}>
                {Math.round(result.chainCoherenceScore)}%
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {hasChainIssue ? 'Too perfect (AI pattern)' : 'Natural variation'}
              </p>
            </div>

            {/* Progression Pattern */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasProgressionIssue ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className={clsx('w-5 h-5', hasProgressionIssue ? 'text-red-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Progression / 递进</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold capitalize',
                hasProgressionIssue ? 'text-red-600' : 'text-green-600'
              )}>
                {result.dominantPattern}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Variety: {Math.round(result.patternVarietyScore)}%
              </p>
            </div>

            {/* Redundancy */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasRedundancy ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <Copy className={clsx('w-5 h-5', hasRedundancy ? 'text-yellow-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Redundancy / 冗余</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasRedundancy ? 'text-yellow-600' : 'text-green-600'
              )}>
                {result.totalRedundancies}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {hasRedundancy ? 'Found redundant content' : 'No redundancy'}
              </p>
            </div>

            {/* Section Count */}
            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <GitBranch className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">Argument Chain</span>
              </div>
              <div className="text-2xl font-bold text-gray-700">
                {result.argumentChain.length}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                sections linked
              </p>
            </div>
          </div>

          {/* High Risk Alert */}
          {hasHighRisk && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Perfect Linear Logic Structure
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：论证链过于完美，递进模式过于线性。
                  人类写作通常包含开放性问题、意外发现和非线性分支。
                  建议添加一些未解决的问题或旁支讨论。
                </p>
              </div>
            </div>
          )}

          {/* Argument Chain Visualization */}
          <div className="mb-6">
            <button
              onClick={() => setExpandedIssue(expandedIssue === 'chain' ? null : 'chain')}
              className="w-full"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-blue-600" />
                  Argument Chain Structure / 论证链结构
                </div>
                {expandedIssue === 'chain' ? (
                  <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
              </h3>
            </button>
            {expandedIssue === 'chain' && (
              <div className="bg-white border rounded-lg p-4">
                <div className="space-y-3">
                  {result.argumentChain.map((chain, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <div className={clsx(
                        'w-10 h-10 rounded-full flex items-center justify-center',
                        chain.connectsToPrevious ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                      )}>
                        {chain.sectionIndex + 1}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">
                            {chain.sectionRole.charAt(0).toUpperCase() + chain.sectionRole.slice(1).replace('_', ' ')}
                          </span>
                          <span className="text-sm text-gray-500">({chain.connectionType})</span>
                        </div>
                        <p className="text-sm text-gray-600">{chain.mainArgument}</p>
                        {chain.supportingPoints.length > 0 && (
                          <span className="text-sm text-gray-400">
                            Supporting: {chain.supportingPoints.slice(0, 2).join(', ')}
                          </span>
                        )}
                      </div>
                      {chain.connectsToPrevious && (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      )}
                    </div>
                  ))}
                </div>
                <div className="mt-4 p-3 bg-yellow-50 rounded border border-yellow-200">
                  <p className="text-sm text-yellow-700">
                    <strong>Issue:</strong> The argument chain is perfectly linear (A-B-C-D-E) with no branches.
                    This is a typical AI pattern. Human writing often has side arguments, unexpected findings,
                    or unresolved questions.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Redundancy Issues */}
          {hasRedundancy && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Copy className="w-5 h-5 text-yellow-600" />
                Redundancy Issues / 信息冗余问题
                <span className="text-sm font-normal text-gray-500">
                  ({result.totalRedundancies} found)
                </span>
              </h3>
              <div className="bg-white border rounded-lg divide-y">
                {result.redundancies.map((redundancy, idx) => (
                  <div key={idx} className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={clsx(
                        'px-2 py-0.5 rounded text-xs',
                        redundancy.severity === 'high' ? 'bg-red-100 text-red-700' :
                        redundancy.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-blue-100 text-blue-700'
                      )}>
                        {redundancy.redundancyType.toUpperCase()}
                      </span>
                      <span className="text-gray-700">
                        Section {redundancy.sectionAIndex + 1} &harr; Section {redundancy.sectionBIndex + 1}
                      </span>
                      <span className={clsx(
                        'px-1.5 py-0.5 rounded text-xs',
                        redundancy.severity === 'high' ? 'bg-red-100 text-red-700' :
                        redundancy.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-600'
                      )}>
                        {redundancy.severity}
                      </span>
                    </div>
                    <p className="text-gray-600 bg-gray-50 p-2 rounded mb-2 text-sm">
                      "{redundancy.redundantContent}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Issue Selection Section */}
          {issues.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-orange-600" />
                  Detected Issues / 检测到的问题 ({issues.length})
                </h3>
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm" onClick={selectAllIssues}>
                    Select All / 全选
                  </Button>
                  <Button variant="secondary" size="sm" onClick={deselectAllIssues}>
                    Deselect All / 取消全选
                  </Button>
                </div>
              </div>

              <div className="bg-white border rounded-lg divide-y">
                {issues.map((issue, idx) => (
                  <div key={issue.id} className="p-4">
                    <div className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        checked={selectedIssueIndices.includes(idx)}
                        onChange={() => toggleIssueSelection(idx)}
                        className="mt-1 h-4 w-4 text-blue-600 rounded border-gray-300"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={clsx(
                            'px-2 py-0.5 rounded text-xs',
                            issue.severity === 'high' ? 'bg-red-100 text-red-700' :
                            issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-blue-100 text-blue-700'
                          )}>
                            {issue.severity.toUpperCase()}
                          </span>
                          <span className="font-medium text-gray-900">{issue.title}</span>
                        </div>
                        <p className="text-gray-600 text-sm">{issue.description}</p>
                        <p className="text-gray-500 text-sm mt-1">{issue.descriptionZh}</p>
                        <p className="text-gray-400 text-xs mt-1">Location: {issue.location}</p>
                        {issue.suggestion && (
                          <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded">
                            <div className="flex items-center gap-1 text-green-700 text-sm font-medium mb-1">
                              <Lightbulb className="w-4 h-4" />
                              Suggestion
                            </div>
                            <p className="text-green-600 text-sm">{issue.suggestion}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Action Buttons */}
              <div className="mt-4 flex flex-wrap gap-3">
                <Button
                  variant="secondary"
                  onClick={handleLoadSuggestions}
                  disabled={selectedIssueIndices.length === 0 || isLoadingSuggestions}
                >
                  {isLoadingSuggestions ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Lightbulb className="w-4 h-4 mr-2" />
                  )}
                  Load Suggestions / 加载建议
                </Button>
                <Button
                  variant="secondary"
                  onClick={handleGeneratePrompt}
                  disabled={selectedIssueIndices.length === 0 || isGeneratingPrompt}
                >
                  {isGeneratingPrompt ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Zap className="w-4 h-4 mr-2" />
                  )}
                  Generate Prompt / 生成提示
                </Button>
                <Button
                  variant="primary"
                  onClick={handleApplyModify}
                  disabled={selectedIssueIndices.length === 0 || isApplyingModify}
                >
                  {isApplyingModify ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4 mr-2" />
                  )}
                  AI Modify / AI修改
                </Button>
              </div>

              {/* Generated Prompt Display */}
              {generatedPrompt && (
                <div className="mt-4 p-4 bg-gray-50 border rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-purple-600" />
                    Generated Prompt / 生成的提示
                  </h4>
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap bg-white p-3 rounded border">
                    {generatedPrompt}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* Merge Confirm Dialog */}
          {showMergeConfirm && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Confirm AI Modification / 确认AI修改
                </h3>
                <p className="text-gray-600 mb-4">
                  You have selected {selectedIssueIndices.length} issue(s) to fix.
                  Add any additional notes for the AI.
                </p>
                <p className="text-gray-500 mb-4 text-sm">
                  您已选择 {selectedIssueIndices.length} 个问题进行修复。
                  请添加任何额外的说明。
                </p>
                <textarea
                  value={userNotes}
                  onChange={(e) => setUserNotes(e.target.value)}
                  placeholder="Additional notes (optional) / 额外说明（可选）"
                  className="w-full p-3 border rounded-lg resize-none h-24 mb-4"
                />
                <div className="flex justify-end gap-3">
                  <Button variant="secondary" onClick={() => setShowMergeConfirm(false)}>
                    Cancel / 取消
                  </Button>
                  <Button variant="primary" onClick={handleConfirmMerge}>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Apply / 应用
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Merge Result Display */}
          {showMergeResult && (
            <div className="mb-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <h4 className="font-medium text-purple-800 mb-3 flex items-center gap-2">
                <Sparkles className="w-5 h-5" />
                AI Modified Result / AI修改结果
              </h4>
              {/* Modified text display - full content with scrollable area */}
              {/* 修改后内容显示 - 完整内容可滚动 */}
              <div className="bg-white p-4 rounded border max-h-96 overflow-y-auto mb-4">
                <p className="text-xs text-gray-500 mb-1">
                  修改后内容 / Modified Content ({mergeResult?.length || 0} 字符):
                </p>
                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                  {mergeResult}
                </pre>
              </div>
              <div className="flex gap-3">
                <Button variant="primary" onClick={handleAcceptMerge}>
                  <Check className="w-4 h-4 mr-2" />
                  Accept / 接受
                </Button>
                <Button variant="secondary" onClick={handleRegenerateMerge}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Regenerate / 重新生成
                </Button>
                <Button variant="secondary" onClick={handleCancelMerge}>
                  <X className="w-4 h-4 mr-2" />
                  Cancel / 取消
                </Button>
              </div>
            </div>
          )}

          {/* Document Modification Section */}
          <div className="mb-6 p-4 bg-gray-50 border rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              Document Modification / 文档修改
            </h3>
            <p className="text-gray-600 text-sm mb-4">
              Upload a modified document or paste the modified text below.
              After applying changes, click "Apply and Continue" to proceed.
            </p>
            <p className="text-gray-500 text-sm mb-4">
              上传修改后的文档或在下方粘贴修改后的文本。
              应用更改后，点击"应用并继续"继续下一步。
            </p>

            {/* File Upload */}
            <div className="mb-4">
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.md,.doc,.docx"
                onChange={handleFileUpload}
                className="hidden"
              />
              <Button
                variant="secondary"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-4 h-4 mr-2" />
                Upload File / 上传文件
              </Button>
              {uploadedFile && (
                <span className="ml-3 text-sm text-gray-600">
                  {uploadedFile.name}
                </span>
              )}
            </div>

            {/* Text Input */}
            <textarea
              value={modifiedText}
              onChange={(e) => setModifiedText(e.target.value)}
              placeholder="Paste modified document text here... / 在此粘贴修改后的文档文本..."
              className="w-full p-3 border rounded-lg resize-none h-48 font-mono text-sm"
            />

            {/* Apply and Continue Button - Style matched with LayerStep2_0 */}
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-gray-500">
                {modifiedText.trim()
                  ? 'Content entered, ready to apply / 内容已输入，可以应用'
                  : 'Please enter content first / 请先输入内容'}
              </p>
              <Button
                variant="primary"
                onClick={handleApplyAndContinue}
                disabled={!modifiedText.trim() || isUploading}
              >
                {isUploading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <ArrowRight className="w-4 h-4 mr-2" />
                )}
                Apply and Continue to Layer 3 / 应用并继续到第3层
              </Button>
            </div>
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
            Back: Transitions / 上一步：章节衔接
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
