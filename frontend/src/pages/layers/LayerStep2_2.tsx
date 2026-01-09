import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  Loader2,
  Layers,
  AlertTriangle,
  RefreshCw,
  BarChart3,
  Scale,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { sectionLayerApi, SectionLengthResponse } from '../../services/analysisApi';

/**
 * Layer Step 2.2 - Section Length Distribution Detection
 * 步骤 2.2 - 章节长度分布检测
 *
 * Detects:
 * - I: Section Length CV (章节长度变异系数)
 * - J: Extreme Section Length (极端长度检测)
 * - K: Key Section Weight (关键章节权重)
 * - L: Paragraph Count Variance (段落数量变异)
 *
 * Priority: (High - depends on section boundaries from Step 2.0)
 * 优先级: (高 - 依赖步骤2.0的章节边界)
 */

interface LayerStep2_2Props {
  documentIdProp?: string;
  onComplete?: (result: SectionLengthResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep2_2({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep2_2Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer4-step2-2').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<SectionLengthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
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
      const analysisResult = await sectionLayerApi.analyzeLengthDistribution(
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
    navigate(`/flow/layer4-step2-1/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer4-step2-3/${documentId}?${params.toString()}`);
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
  const hasLengthIssue = (result?.lengthCv || 0) < 0.3;
  // Calculate min/max from sections for display
  const minLength = result ? Math.min(...result.sections.map(s => s.wordCount)) : 0;
  const maxLength = result ? Math.max(...result.sections.map(s => s.wordCount)) : 0;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Layers className="w-4 h-4" />
          <span>Layer 4 / 第4层</span>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Step 2.2 长度分布</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Section Length Distribution Detection
        </h1>
        <p className="text-gray-600 mt-1">
          章节长度分布检测 - 检测章节长度变异系数、极端长度和关键章节权重
        </p>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing length distribution... / 分析长度分布中...</p>
              <p className="text-blue-600 text-sm">Calculating CV and checking extremes</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* Summary Stats */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Length CV */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasLengthIssue ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <Scale className={clsx('w-5 h-5', hasLengthIssue ? 'text-red-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Length CV</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasLengthIssue ? 'text-red-600' : 'text-green-600'
              )}>
                {result.lengthCv.toFixed(2)}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Target: &ge; 0.40 | {hasLengthIssue ? 'Too uniform' : 'Good variance'}
              </p>
            </div>

            {/* Total Words */}
            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">Total Words</span>
              </div>
              <div className="text-2xl font-bold text-gray-700">
                {result.totalWords}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {result.sectionCount} sections
              </p>
            </div>

            {/* Mean Length */}
            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">Mean Length</span>
              </div>
              <div className="text-2xl font-bold text-gray-700">
                {Math.round(result.meanLength)} <span className="text-sm font-normal">words</span>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                StdDev: {Math.round(result.stdevLength)}
              </p>
            </div>

            {/* Range */}
            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">Length Range</span>
              </div>
              <div className="text-2xl font-bold text-gray-700">
                {minLength} - {maxLength}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                words per section
              </p>
            </div>
          </div>

          {/* High Risk Alert */}
          {hasHighRisk && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Uniform Section Lengths
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：章节长度过于均匀 (CV &lt; 0.30)。
                  AI倾向于生成长度相近的章节。建议增加长度变化。
                </p>
              </div>
            </div>
          )}

          {/* Section Length Visualization */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              Section Length Comparison / 章节长度对比
            </h3>
            <div className="bg-white border rounded-lg p-4 space-y-3">
              {result.sections.map((section) => {
                const widthPercent = Math.min(100, (section.wordCount / maxLength) * 100);
                const relativeLength = 1 + section.deviationFromMean;
                const isShort = relativeLength < 0.5;
                const isLong = relativeLength > 2.5;
                const isKeySection = ['results', 'methodology'].includes(section.role);
                const hasWeightDeviation = Math.abs(section.weightDeviation) > 0.3;

                return (
                  <div key={section.index} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-gray-700">
                        {section.role.charAt(0).toUpperCase() + section.role.slice(1).replace('_', ' ')}
                        {isKeySection && (
                          <span className="ml-2 px-1.5 py-0.5 bg-orange-100 text-orange-700 rounded text-xs">
                            Key
                          </span>
                        )}
                        {section.isExtreme && (
                          <span className="ml-2 px-1.5 py-0.5 bg-red-100 text-red-700 rounded text-xs">
                            Extreme
                          </span>
                        )}
                      </span>
                      <span className="text-gray-500">
                        {section.wordCount} words ({relativeLength.toFixed(2)}x mean)
                      </span>
                    </div>
                    <div className="h-6 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={clsx(
                          'h-full rounded-full transition-all',
                          section.isExtreme ? 'bg-red-400' :
                          isShort ? 'bg-yellow-400' :
                          isLong ? 'bg-red-400' :
                          hasWeightDeviation ? 'bg-orange-400' :
                          'bg-blue-400'
                        )}
                        style={{ width: `${widthPercent}%` }}
                      />
                    </div>
                    {hasWeightDeviation && section.expectedWeight && (
                      <p className="text-sm text-orange-600 pl-2">
                        Weight: {(section.actualWeight * 100).toFixed(1)}% (expected: {(section.expectedWeight * 100).toFixed(1)}%)
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Issues */}
          {result.issues.length > 0 && (
            <div className="mb-6 p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <h4 className="font-medium text-orange-800 mb-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Length Distribution Issues / 长度分布问题
              </h4>
              <ul className="space-y-1 text-orange-700 text-sm">
                {result.issues.map((issue, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-orange-500">•</span>
                    <div>
                      <span>{issue.description}</span>
                      {issue.descriptionZh && (
                        <span className="block text-orange-600">{issue.descriptionZh}</span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
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
                    Length Adjustment Suggestions / 长度调整建议
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
            Back: Section Order / 上一步：章节顺序
          </Button>
          <Button variant="primary" onClick={handleNext} disabled={isAnalyzing || !result}>
            Next: Internal Structure / 下一步：内部结构
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
