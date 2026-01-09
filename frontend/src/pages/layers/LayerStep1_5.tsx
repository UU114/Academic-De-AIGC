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
  Link2,
  Unlink,
  MessageSquare,
  Zap,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import {
  documentLayerApi,
  ConnectorAnalysisResponse,
} from '../../services/analysisApi';

/**
 * Layer Step 1.5 - Paragraph Transition Detection
 * 步骤 1.5 - 段落过渡检测
 *
 * Detects (Merged Group 3 - MUST be merged due to conflicts):
 * - H: Explicit Connector Overuse (显性连接词过度使用)
 * - I: Missing Semantic Echo (缺乏语义回声)
 * - J: Logic Break Points (逻辑断裂点)
 *
 * Priority: ★★☆☆☆ (Final step, depends on paragraph content being stable)
 * 优先级: ★★☆☆☆ (最后处理，依赖段落内容稳定)
 *
 * Conflict Resolution:
 * - H→J conflict: Deleting connectors may create logic breaks
 * - J→H conflict: Fixing breaks may add connectors
 * - Solution: Detect all simultaneously, use semantic echo (I) as unified replacement
 *
 * 冲突解决：
 * - H→J冲突：删除连接词可能产生逻辑断裂
 * - J→H冲突：修复断裂可能添加连接词
 * - 解决方案：同时检测所有问题，使用语义回声(I)作为统一替换
 */

// Transition type config
// 过渡类型配置
const TRANSITION_TYPE_CONFIG: Record<string, { label: string; labelZh: string; icon: typeof Link2; risk: string }> = {
  smooth: { label: 'Smooth', labelZh: '平滑', icon: Link2, risk: 'low' },
  abrupt: { label: 'Abrupt', labelZh: '突兀', icon: Unlink, risk: 'medium' },
  glue_word_only: { label: 'Glue Word Only', labelZh: '仅胶水词', icon: AlertTriangle, risk: 'high' },
  ai_perfect_linear: { label: 'AI Perfect Linear', labelZh: 'AI完美线性', icon: Zap, risk: 'high' },
  semantic_echo: { label: 'Semantic Echo', labelZh: '语义回声', icon: MessageSquare, risk: 'low' },
};

interface LayerStep1_5Props {
  documentIdProp?: string;
  onComplete?: (result: ConnectorAnalysisResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep1_5({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep1_5Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer5-step1-5').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<ConnectorAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedTransitionIndex, setExpandedTransitionIndex] = useState<number | null>(null);

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
      const analysisResult = await documentLayerApi.analyzeConnectors(documentText, sessionId || undefined);
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

  const hasHighRisk = result?.overallRiskLevel === 'high';
  const problematicTransitions = result?.transitions?.filter(t =>
    t.issues && t.issues.length > 0
  ) || [];
  // Use connectorList from API (string[])
  // 使用 API 返回的 connectorList（字符串数组）
  const explicitConnectorsList = result?.connectorList || [];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Layers className="w-4 h-4" />
          <span>Layer 5 / 第5层</span>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Step 1.5 段落过渡</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Paragraph Transition Detection
        </h1>
        <p className="text-gray-600 mt-1">
          段落过渡检测 - 综合检测显性连接词、语义回声和逻辑断裂点（三者必须合并处理以避免冲突）
        </p>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing transitions... / 分析过渡中...</p>
              <p className="text-blue-600 text-sm">Detecting connectors, breaks, and echo patterns</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* Summary Stats */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Overall Risk */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasHighRisk ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                {hasHighRisk ? (
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                ) : (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                )}
                <span className="font-medium text-gray-900">Overall Risk / 总体风险</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasHighRisk ? 'text-red-600' : 'text-green-600'
              )}>
                {result.overallRiskLevel?.toUpperCase() || 'LOW'}
              </div>
            </div>

            {/* Total Transitions */}
            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <Link2 className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">Total Transitions</span>
              </div>
              <div className="text-2xl font-bold text-gray-700">
                {result.totalTransitions || 0}
              </div>
            </div>

            {/* Problematic */}
            <div className={clsx(
              'p-4 rounded-lg border',
              problematicTransitions.length > 0 ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <Unlink className={clsx('w-5 h-5', problematicTransitions.length > 0 ? 'text-yellow-600' : 'text-gray-600')} />
                <span className="font-medium text-gray-900">Problematic</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                problematicTransitions.length > 0 ? 'text-yellow-600' : 'text-gray-700'
              )}>
                {result.problematicTransitions || problematicTransitions.length}
              </div>
            </div>

            {/* Explicit Connectors */}
            <div className={clsx(
              'p-4 rounded-lg border',
              explicitConnectorsList.length > 0 ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className={clsx('w-5 h-5', explicitConnectorsList.length > 0 ? 'text-red-600' : 'text-gray-600')} />
                <span className="font-medium text-gray-900">Explicit Connectors</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                explicitConnectorsList.length > 0 ? 'text-red-600' : 'text-gray-700'
              )}>
                {explicitConnectorsList.length}
              </div>
            </div>
          </div>

          {/* Risk Alert */}
          {hasHighRisk && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Transition Issues Detected
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：检测到过渡问题。显性连接词过多或存在逻辑断裂。
                  建议使用语义回声（引用前段关键概念）替换显性连接词。
                </p>
              </div>
            </div>
          )}

          {/* Explicit Connectors */}
          {/* 显性连接词列表 */}
          {explicitConnectorsList.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                Explicit Connectors / 显性连接词
                <span className="text-sm font-normal text-gray-500">
                  ({explicitConnectorsList.length} detected)
                </span>
              </h3>
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex flex-wrap gap-2">
                  {explicitConnectorsList.map((connector: string, idx: number) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium"
                    >
                      "{connector}"
                    </span>
                  ))}
                </div>
                <p className="text-red-700 text-sm mt-3">
                  These explicit connectors create an AI-like "smooth" transition pattern.
                  Consider replacing with semantic echoes.
                </p>
                <p className="text-red-600 text-sm mt-1">
                  这些显性连接词造成了AI风格的"平滑"过渡模式。建议替换为语义回响。
                </p>
              </div>
            </div>
          )}

          {/* Transition Issues */}
          {problematicTransitions.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Unlink className="w-5 h-5 text-yellow-600" />
                Transition Issues / 过渡问题
                <span className="text-sm font-normal text-gray-500">
                  ({problematicTransitions.length} issues)
                </span>
              </h3>
              <div className="space-y-2">
                {problematicTransitions.map((transition, idx) => {
                  const isExpanded = expandedTransitionIndex === idx;
                  // Determine transition type based on riskLevel
                  // 根据 riskLevel 确定过渡类型
                  const riskTypeMap: Record<string, string> = {
                    high: 'glue_word_only',
                    medium: 'abrupt',
                    low: 'smooth',
                  };
                  const typeKey = riskTypeMap[transition.riskLevel] || 'abrupt';
                  const typeConfig = TRANSITION_TYPE_CONFIG[typeKey] || TRANSITION_TYPE_CONFIG.abrupt;
                  const TypeIcon = typeConfig.icon;

                  return (
                    <div
                      key={idx}
                      className="bg-yellow-50 border border-yellow-200 rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => toggleTransition(idx)}
                        className="w-full px-4 py-3 flex items-center justify-between hover:bg-yellow-100 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <TypeIcon className="w-5 h-5 text-yellow-600" />
                          <div className="text-left">
                            <p className="font-medium text-yellow-800">
                              Para {transition.paraAIndex + 1} → Para {transition.paraBIndex + 1}
                            </p>
                            <p className="text-sm text-yellow-600">
                              {typeConfig.labelZh} ({typeConfig.label})
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
                          <div className="space-y-3">
                            {/* Issues */}
                            {transition.issues && transition.issues.length > 0 && (
                              <div>
                                <h4 className="text-sm font-medium text-gray-700 mb-1">
                                  Issues Detected / 检测到的问题
                                </h4>
                                {transition.issues.map((issue, iIdx) => (
                                  <div key={iIdx} className="p-2 bg-gray-50 rounded mb-2">
                                    <p className="text-gray-700 text-sm">
                                      {issue.descriptionZh || issue.description}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* Paragraph Context */}
                            <div className="grid grid-cols-2 gap-3">
                              <div>
                                <h4 className="text-sm font-medium text-gray-700 mb-1">
                                  Para A Ending / A段结尾
                                </h4>
                                <p className="text-gray-600 text-sm bg-gray-50 p-2 rounded">
                                  {transition.paraAEnding?.slice(0, 80) || '...'}...
                                </p>
                              </div>
                              <div>
                                <h4 className="text-sm font-medium text-gray-700 mb-1">
                                  Para B Opening / B段开头
                                </h4>
                                <p className="text-gray-600 text-sm bg-gray-50 p-2 rounded">
                                  {transition.paraBOpening?.slice(0, 80) || '...'}...
                                </p>
                              </div>
                            </div>

                            {/* Actions */}
                            <div className="pt-2">
                              <Button variant="primary" size="sm">
                                AI Analysis / AI分析
                              </Button>
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
          {!hasHighRisk && explicitConnectorsList.length === 0 && problematicTransitions.length === 0 && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">
                  Natural Paragraph Transitions
                </h3>
                <p className="text-green-600 mt-1">
                  段落过渡自然。未检测到显性连接词过度使用或逻辑断裂。
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
        </>
      )}

      {/* Navigation */}
      {showNavigation && (
        <div className="flex items-center justify-between pt-6 border-t">
          <Button variant="secondary" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back: Paragraph Length / 上一步：段落长度
          </Button>
          <Button variant="primary" onClick={handleNext} disabled={isAnalyzing}>
            Finish Layer 5 → Layer 4 / 完成第5层 → 第4层
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
