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
  Repeat,
  ArrowDownUp,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import {
  documentLayerApi,
  ProgressionClosureResponse,
  ProgressionMarker,
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
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

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
      const analysisResult = await documentLayerApi.analyzeProgressionClosure(documentText, sessionId || undefined);
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

  // Group markers by category (using actual ProgressionMarker.category property)
  // 按类别分组标记（使用实际的 ProgressionMarker.category 属性）
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

  // Filter monotonic vs non-monotonic markers from progressionMarkers
  // 从 progressionMarkers 中过滤单调和非单调标记
  const monotonicMarkers = result?.progressionMarkers?.filter(m => m.isMonotonic) || [];
  const nonMonotonicMarkers = result?.progressionMarkers?.filter(m => !m.isMonotonic) || [];
  const groupedMarkers = groupMarkersByCategory(monotonicMarkers);
  const nonMonotonicCount = nonMonotonicMarkers.length;
  const monotonicCount = monotonicMarkers.length;

  return (
    <div className="p-6 max-w-6xl mx-auto">
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
          {/* 发现的非单调标记 */}
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

          {/* No issues */}
          {progressionConfig.risk === 'low' && (
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
        </>
      )}

      {/* Navigation */}
      {showNavigation && (
        <div className="flex items-center justify-between pt-6 border-t">
          <Button variant="secondary" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back: Uniformity / 上一步：均匀性
          </Button>
          <Button variant="primary" onClick={handleNext} disabled={isAnalyzing}>
            Next: Paragraph Length / 下一步：段落长度
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
