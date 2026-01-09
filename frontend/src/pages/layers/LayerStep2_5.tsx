import { useEffect, useState, useRef } from 'react';
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
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { sectionLayerApi, InterSectionLogicResponse } from '../../services/analysisApi';

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
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

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
  const [showAiSuggestion, setShowAiSuggestion] = useState(false);

  const isAnalyzingRef = useRef(false);

  // Load document
  useEffect(() => {
    if (documentId) {
      loadDocumentText(documentId);
    }
  }, [documentId]);

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
      // Call actual API
      // 调用实际API
      const analysisResult = await sectionLayerApi.analyzeInterSectionLogic(
        documentText,
        undefined,
        undefined,
        sessionId || undefined
      );

      setResult(analysisResult);

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
                    <strong>Issue:</strong> The argument chain is perfectly linear (A→B→C→D→E) with no branches.
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
                    Logic Structure Improvement Suggestions / 逻辑结构改进建议
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

      {/* Navigation */}
      {showNavigation && (
        <div className="flex items-center justify-between pt-6 border-t">
          <Button variant="secondary" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back: Transitions / 上一步：章节衔接
          </Button>
          <Button variant="primary" onClick={handleNext} disabled={isAnalyzing || !result}>
            Finish Layer 4 → Layer 3 / 完成第4层 → 第3层
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
