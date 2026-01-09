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
  BarChart3,
  Merge,
  Scissors,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import {
  documentLayerApi,
  ParagraphLengthAnalysisResponse,
} from '../../services/analysisApi';

/**
 * Layer Step 1.4 - Paragraph Length Uniformity Detection
 * 步骤 1.4 - 段落长度均匀性检测
 *
 * Detects:
 * - E: Uniform Paragraph Length (全文段落长度是否过于均匀)
 *
 * Priority: ★★☆☆☆ (Depends on all previous structure being stable)
 * 优先级: ★★☆☆☆ (依赖前面所有结构稳定)
 *
 * Conflict Note: Must process after Step 1.3, to avoid breaking logic pattern results.
 * 冲突说明: 必须在1.3之后处理，避免破坏逻辑模式处理的结果。
 */

// Strategy type display config
// 策略类型显示配置
const STRATEGY_CONFIG: Record<string, { label: string; labelZh: string; icon: typeof Merge; color: string }> = {
  merge: {
    label: 'Merge',
    labelZh: '合并',
    icon: Merge,
    color: 'text-blue-600 bg-blue-50',
  },
  split: {
    label: 'Split',
    labelZh: '拆分',
    icon: Scissors,
    color: 'text-purple-600 bg-purple-50',
  },
  expand: {
    label: 'Expand',
    labelZh: '扩展',
    icon: Maximize2,
    color: 'text-green-600 bg-green-50',
  },
  compress: {
    label: 'Compress',
    labelZh: '压缩',
    icon: Minimize2,
    color: 'text-orange-600 bg-orange-50',
  },
};

interface LayerStep1_4Props {
  documentIdProp?: string;
  onComplete?: (result: ParagraphLengthAnalysisResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep1_4({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep1_4Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer5-step1-4').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<ParagraphLengthAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedParagraphIndex, setExpandedParagraphIndex] = useState<number | null>(null);

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
      const analysisResult = await documentLayerApi.analyzeParagraphLength(documentText, sessionId || undefined);
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

  // Get bar width for visualization
  const getBarWidth = (value: number, max: number) => {
    return `${Math.min((value / max) * 100, 100)}%`;
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

  const isUniform = result?.cv !== undefined && result.cv < 0.3;
  const maxLength = Math.max(...(result?.paragraphs?.map(p => p.wordCount) || [1]));

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Layers className="w-4 h-4" />
          <span>Layer 5 / 第5层</span>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Step 1.4 段落长度</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Paragraph Length Uniformity Detection
        </h1>
        <p className="text-gray-600 mt-1">
          段落长度均匀性检测 - 检测全文段落长度是否过于均匀（CV &lt; 0.3 = AI特征）
        </p>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing paragraph lengths... / 分析段落长度中...</p>
              <p className="text-blue-600 text-sm">Calculating CV and suggesting strategies</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* CV Score Summary */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* CV Score */}
            <div className={clsx(
              'p-4 rounded-lg border',
              isUniform ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className={clsx('w-5 h-5', isUniform ? 'text-red-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">CV (Coefficient of Variation)</span>
              </div>
              <div className={clsx(
                'text-3xl font-bold',
                isUniform ? 'text-red-600' : 'text-green-600'
              )}>
                {((result.cv || 0) * 100).toFixed(1)}%
              </div>
              <p className={clsx(
                'text-sm mt-1',
                isUniform ? 'text-red-600' : 'text-green-600'
              )}>
                {isUniform ? 'Too uniform (< 30%) / 过于均匀' : 'Natural variation / 自然变化'}
              </p>
            </div>

            {/* Average Length (meanLength from API) */}
            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-medium text-gray-900">Average Length / 平均长度</span>
              </div>
              <div className="text-3xl font-bold text-gray-700">
                {Math.round(result.meanLength || 0)}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                words per paragraph / 词/段落
              </p>
            </div>

            {/* Total Paragraphs (paragraphCount from API) */}
            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-medium text-gray-900">Total Paragraphs / 总段落数</span>
              </div>
              <div className="text-3xl font-bold text-gray-700">
                {result.paragraphCount || result.paragraphs?.length || 0}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                paragraphs analyzed / 已分析段落
              </p>
            </div>
          </div>

          {/* Risk Alert */}
          {isUniform && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Uniform Paragraph Length Detected
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：段落长度过于均匀。目标CV应≥40%。
                  建议合并短段落、拆分长段落以创造自然的长度变化。
                </p>
              </div>
            </div>
          )}

          {/* Paragraph Length Visualization */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Paragraph Length Distribution / 段落长度分布
            </h3>
            <div className="space-y-2">
              {result.paragraphs?.map((para, idx) => {
                const isExpanded = expandedParagraphIndex === idx;
                const strategyConfig = para.suggestedStrategy
                  ? STRATEGY_CONFIG[para.suggestedStrategy]
                  : null;
                const StrategyIcon = strategyConfig?.icon || BarChart3;

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
                      <span className="w-8 h-8 flex items-center justify-center bg-gray-100 rounded-full text-sm font-medium text-gray-600 flex-shrink-0">
                        {idx + 1}
                      </span>

                      {/* Bar */}
                      <div className="flex-1">
                        <div className="h-6 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={clsx(
                              'h-full rounded-full transition-all',
                              para.suggestedStrategy ? 'bg-yellow-400' : 'bg-blue-400'
                            )}
                            style={{ width: getBarWidth(para.wordCount, maxLength) }}
                          />
                        </div>
                      </div>

                      {/* Word count */}
                      <span className="text-sm text-gray-600 w-16 text-right">
                        {para.wordCount} words
                      </span>

                      {/* Strategy badge */}
                      {strategyConfig && (
                        <span className={clsx(
                          'px-2 py-1 rounded text-xs font-medium flex items-center gap-1',
                          strategyConfig.color
                        )}>
                          <StrategyIcon className="w-3 h-3" />
                          {strategyConfig.labelZh}
                        </span>
                      )}

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
                          {/* Preview */}
                          <div>
                            <h4 className="text-sm font-medium text-gray-700 mb-1">
                              Preview / 预览
                            </h4>
                            <p className="text-sm text-gray-600 line-clamp-3">
                              {para.preview || 'No preview available'}
                            </p>
                          </div>

                          {/* Strategy suggestion (strategyReasonZh from API) */}
                          {para.strategyReasonZh && (
                            <div>
                              <h4 className="text-sm font-medium text-gray-700 mb-1">
                                Suggestion / 建议
                              </h4>
                              <p className="text-sm text-gray-600">
                                {para.strategyReasonZh}
                              </p>
                            </div>
                          )}

                          {/* AI Analysis button */}
                          {para.suggestedStrategy && (
                            <div className="pt-2">
                              <Button variant="primary" size="sm">
                                AI Analysis / AI分析
                              </Button>
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

          {/* No issues */}
          {!isUniform && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">
                  Natural Paragraph Length Variation
                </h3>
                <p className="text-green-600 mt-1">
                  段落长度变化自然。CV值表明这不是典型的AI生成文本特征。
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
            Back: Logic Pattern / 上一步：逻辑模式
          </Button>
          <Button variant="primary" onClick={handleNext} disabled={isAnalyzing}>
            Next: Transitions / 下一步：段落过渡
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
