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
  ArrowRightLeft,
  Link2,
  Unlink,
  MessageSquare,
  Zap,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { sectionLayerApi, SectionTransitionResponse } from '../../services/analysisApi';

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
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

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
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedTransition, setExpandedTransition] = useState<number | null>(null);
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
      const analysisResult = await sectionLayerApi.analyzeTransitions(
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
    navigate(`/flow/layer4-step2-3/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer4-step2-5/${documentId}?${params.toString()}`);
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
  const hasExplicitIssue = (result?.explicitRatio || 0) > 0.7;
  const hasEchoIssue = (result?.avgSemanticEcho || 0) < 0.4;

  return (
    <div className="p-6 max-w-6xl mx-auto">
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
                {hasExplicitIssue ? 'Too many explicit (&gt;70%)' : 'Good balance'}
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

      {/* Navigation */}
      {showNavigation && (
        <div className="flex items-center justify-between pt-6 border-t">
          <Button variant="secondary" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back: Internal Structure / 上一步：内部结构
          </Button>
          <Button variant="primary" onClick={handleNext} disabled={isAnalyzing || !result}>
            Next: Logic Relations / 下一步：逻辑关系
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
