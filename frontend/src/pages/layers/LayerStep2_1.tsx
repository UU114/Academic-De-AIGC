import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Layers,
  AlertTriangle,
  RefreshCw,
  GitBranch,
  ListOrdered,
  Shuffle,
  Zap,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { sectionLayerApi, SectionOrderResponse } from '../../services/analysisApi';

/**
 * Layer Step 2.1 - Section Order & Structure Detection
 * 步骤 2.1 - 章节顺序与结构检测
 *
 * Detects:
 * - B: Predictable Section Order (章节顺序可预测性)
 * - C: Missing Sections (缺失章节检测)
 * - D: Section Function Fusion (章节功能融合度)
 *
 * Priority: (High - depends on correct section identification from Step 2.0)
 * 优先级: (高 - 依赖步骤2.0的正确章节识别)
 */

// Expected academic section order (AI template)
// 期望的学术论文章节顺序（AI模板）
const EXPECTED_ORDER = [
  'introduction',
  'literature_review',
  'methodology',
  'results',
  'discussion',
  'conclusion',
];

const ORDER_LABELS: Record<string, { label: string; labelZh: string }> = {
  introduction: { label: 'Introduction', labelZh: '引言' },
  literature_review: { label: 'Literature Review', labelZh: '文献综述' },
  methodology: { label: 'Methodology', labelZh: '方法论' },
  results: { label: 'Results', labelZh: '结果' },
  discussion: { label: 'Discussion', labelZh: '讨论' },
  conclusion: { label: 'Conclusion', labelZh: '结论' },
};

interface LayerStep2_1Props {
  documentIdProp?: string;
  onComplete?: (result: SectionOrderResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep2_1({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep2_1Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer4-step2-1').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<SectionOrderResponse | null>(null);
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
      const analysisResult = await sectionLayerApi.analyzeOrder(
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
    navigate(`/flow/layer4-step2-0/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer4-step2-2/${documentId}?${params.toString()}`);
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
  const hasMissingSections = (result?.orderAnalysis?.missingSections?.length || 0) > 0;
  const hasHighFunctionPurity = (result?.orderAnalysis?.fusionScore || 0) > 90;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Layers className="w-4 h-4" />
          <span>Layer 4 / 第4层</span>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Step 2.1 章节顺序</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Section Order & Structure Detection
        </h1>
        <p className="text-gray-600 mt-1">
          章节顺序与结构检测 - 检测章节顺序可预测性、缺失章节和功能融合度
        </p>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing section structure... / 分析章节结构中...</p>
              <p className="text-blue-600 text-sm">Checking order, missing sections, and function fusion</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* Summary Stats */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Order Match Score */}
            <div className={clsx(
              'p-4 rounded-lg border',
              result.orderAnalysis.orderMatchScore >= 80 ? 'bg-red-50 border-red-200' :
              result.orderAnalysis.orderMatchScore >= 60 ? 'bg-yellow-50 border-yellow-200' :
              'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <ListOrdered className={clsx(
                  'w-5 h-5',
                  result.orderAnalysis.orderMatchScore >= 80 ? 'text-red-600' :
                  result.orderAnalysis.orderMatchScore >= 60 ? 'text-yellow-600' : 'text-green-600'
                )} />
                <span className="font-medium text-gray-900">Order Match / 顺序匹配</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                result.orderAnalysis.orderMatchScore >= 80 ? 'text-red-600' :
                result.orderAnalysis.orderMatchScore >= 60 ? 'text-yellow-600' : 'text-green-600'
              )}>
                {result.orderAnalysis.orderMatchScore}%
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {result.orderAnalysis.orderMatchScore >= 80 ? 'High risk (AI template)' :
                 result.orderAnalysis.orderMatchScore >= 60 ? 'Medium risk' : 'Low risk (natural)'}
              </p>
            </div>

            {/* Missing Sections */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasMissingSections ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <Shuffle className={clsx(
                  'w-5 h-5',
                  hasMissingSections ? 'text-blue-600' : 'text-gray-600'
                )} />
                <span className="font-medium text-gray-900">Missing Sections / 缺失章节</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasMissingSections ? 'text-blue-600' : 'text-gray-700'
              )}>
                {result.orderAnalysis.missingSections.length}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {hasMissingSections ? 'Non-standard structure (more human)' : 'Complete standard structure'}
              </p>
            </div>

            {/* Function Fusion */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasHighFunctionPurity ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <GitBranch className={clsx(
                  'w-5 h-5',
                  hasHighFunctionPurity ? 'text-red-600' : 'text-green-600'
                )} />
                <span className="font-medium text-gray-900">Function Purity / 功能纯度</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasHighFunctionPurity ? 'text-red-600' : 'text-green-600'
              )}>
                {result.orderAnalysis.fusionScore}%
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {hasHighFunctionPurity ? 'High risk (isolated functions)' : 'Good (mixed functions)'}
              </p>
            </div>
          </div>

          {/* High Risk Alert */}
          {hasHighRisk && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Predictable Section Structure
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：章节结构高度匹配学术论文模板。
                  建议打乱章节顺序或合并相关内容。
                </p>
              </div>
            </div>
          )}

          {/* Section Order Comparison */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <ListOrdered className="w-5 h-5 text-blue-600" />
              Section Order Comparison / 章节顺序对比
            </h3>
            <div className="bg-white border rounded-lg p-4">
              <div className="grid grid-cols-2 gap-4">
                {/* Detected Order */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Detected Order / 检测到的顺序
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {result.orderAnalysis.detectedOrder.map((section, idx) => (
                      <div key={idx} className="flex items-center gap-1">
                        <span className="w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm">
                          {idx + 1}
                        </span>
                        <span className="text-gray-700">
                          {ORDER_LABELS[section]?.labelZh || section}
                        </span>
                        {idx < result.orderAnalysis.detectedOrder.length - 1 && (
                          <span className="text-gray-400 mx-1">→</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Expected Order */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Expected Template / 期望模板
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {EXPECTED_ORDER.map((section, idx) => {
                      const isPresent = result.orderAnalysis.detectedOrder.includes(section);
                      return (
                        <div key={idx} className="flex items-center gap-1">
                          <span className={clsx(
                            'w-6 h-6 rounded-full flex items-center justify-center text-sm',
                            isPresent ? 'bg-gray-200 text-gray-600' : 'bg-red-100 text-red-600'
                          )}>
                            {idx + 1}
                          </span>
                          <span className={clsx(
                            isPresent ? 'text-gray-500' : 'text-red-600 line-through'
                          )}>
                            {ORDER_LABELS[section]?.labelZh || section}
                          </span>
                          {idx < EXPECTED_ORDER.length - 1 && (
                            <span className="text-gray-400 mx-1">→</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Missing Sections */}
          {hasMissingSections && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Shuffle className="w-5 h-5 text-blue-600" />
                Missing Sections / 缺失章节
                <span className="text-sm font-normal text-gray-500">
                  (This may indicate more human-like writing)
                </span>
              </h3>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex flex-wrap gap-2">
                  {result.orderAnalysis.missingSections.map((section, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                    >
                      {ORDER_LABELS[section]?.labelZh || section}
                    </span>
                  ))}
                </div>
                <p className="text-blue-700 text-sm mt-3">
                  Missing standard sections may actually be a positive sign - human writers often
                  deviate from strict templates.
                </p>
                <p className="text-blue-600 text-sm mt-1">
                  缺少标准章节可能是正面信号 - 人类写作者通常会偏离严格的模板。
                </p>
              </div>
            </div>
          )}

          {/* Function Fusion Details */}
          <div className="mb-6">
            <button
              onClick={() => setExpandedIssue(expandedIssue === 'function' ? null : 'function')}
              className="w-full"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <GitBranch className="w-5 h-5 text-blue-600" />
                  Function Fusion Analysis / 功能融合分析
                </div>
                {expandedIssue === 'function' ? (
                  <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
              </h3>
            </button>
            {expandedIssue === 'function' && (
              <div className="bg-white border rounded-lg p-4">
                {result.orderAnalysis.multiFunctionSections.length > 0 ? (
                  <>
                    <p className="text-gray-700 mb-3">
                      Sections with multi-function content (indicating more natural writing):
                    </p>
                    <p className="text-gray-600 text-sm mb-3">
                      包含多功能内容的章节（表示更自然的写作）：
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {result.orderAnalysis.multiFunctionSections.map((sectionIdx) => (
                        <span
                          key={sectionIdx}
                          className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                        >
                          Section {sectionIdx + 1}
                        </span>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-red-600">
                      All sections have isolated functions - this is an AI writing pattern.
                    </p>
                    <p className="text-red-500 text-sm mt-1">
                      所有章节功能隔离 - 这是AI写作的特征。
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* AI Suggestion Button */}
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
                    Structure Improvement Suggestions / 结构改进建议
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
            Back: Section ID / 上一步：章节识别
          </Button>
          <Button variant="primary" onClick={handleNext} disabled={isAnalyzing || !result}>
            Next: Length Distribution / 下一步：长度分布
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
