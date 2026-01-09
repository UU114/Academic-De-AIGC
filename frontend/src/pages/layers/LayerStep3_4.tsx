import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  Ruler,
  FileText,
  RefreshCw,
  BarChart3,
  TrendingUp,
  AlertTriangle,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { paragraphLayerApi, ParagraphAnalysisResponse } from '../../services/analysisApi';

/**
 * Layer Step 3.4 - Sentence Length Distribution Analysis
 * 步骤 3.4 - 句子长度分布分析
 *
 * Analyzes sentence length variation within paragraphs:
 * - Calculates CV (Coefficient of Variation)
 * - Flags low variation (CV < 0.25) as AI-like uniformity
 * - Visualizes sentence length patterns
 *
 * 分析段落内句子长度变化：
 * - 计算变异系数(CV)
 * - 标记低变异(CV < 0.25)为AI式均匀
 * - 可视化句子长度模式
 */

interface LayerStep3_4Props {
  documentIdProp?: string;
  onComplete?: (result: ParagraphAnalysisResponse) => void;
  showNavigation?: boolean;
  sectionContext?: Record<string, unknown>;
}

export default function LayerStep3_4({
  documentIdProp,
  onComplete,
  showNavigation = true,
  sectionContext,
}: LayerStep3_4Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer3-step3-4').catch(console.error);
    }
  }, [sessionId]);

  const [result, setResult] = useState<ParagraphAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');

  const isAnalyzingRef = useRef(false);

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
      const analysisResult = await paragraphLayerApi.analyzeSentenceLength(documentText, sectionContext);
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

  const goToNextStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-5/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-3/${documentId}?${params.toString()}`);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // Get CV risk level based on threshold
  // CV < 0.25 is high risk (AI-like uniformity)
  const getCvRiskLevel = (cv: number): string => {
    if (cv >= 0.35) return 'low';
    if (cv >= 0.25) return 'medium';
    return 'high';
  };

  const getCvColor = (cv: number) => {
    const level = getCvRiskLevel(cv);
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // Render sentence length bar visualization
  // 渲染句子长度条形可视化
  const renderLengthBar = (length: number, maxLength: number) => {
    const percentage = Math.min((length / maxLength) * 100, 100);
    return (
      <div className="flex items-center gap-2">
        <div className="flex-1 h-4 bg-gray-100 rounded overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className="text-xs text-gray-500 w-12 text-right">{length} words</span>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage message="Loading document... / 加载文档中..." />
      </div>
    );
  }

  if (error) {
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
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <Ruler className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3.4: Sentence Length Distribution
              </h2>
              <p className="text-sm text-gray-500">
                步骤 3.4: 句子长度分布分析
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
          Analyzes sentence length variation within each paragraph. Low variation (CV &lt; 0.25) indicates AI-generated uniform sentence patterns.
          <br />
          <span className="text-gray-500">
            分析每个段落内句子长度变化。低变异（CV &lt; 0.25）表示AI生成的均匀句式模式。
          </span>
        </p>

        {/* Overall Metrics */}
        {result && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className={clsx('rounded-lg p-4', getRiskColor(result.riskLevel))}>
              <div className="text-2xl font-bold">{result.riskScore}/100</div>
              <div className="text-sm">Risk Score / 风险分数</div>
            </div>
            <div className={clsx('rounded-lg p-4', getCvColor(result.sentenceLengthCv || 0))}>
              <div className="text-2xl font-bold">
                {(result.sentenceLengthCv || 0).toFixed(3)}
              </div>
              <div className="text-sm">Overall CV / 总体变异系数</div>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-700">
                {result.paragraphCount || 0}
              </div>
              <div className="text-sm text-blue-600">Paragraphs / 段落数</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-red-700">
                {result.paragraphDetails?.filter(p => (p.sentenceLengthCv || 0) < 0.25).length || 0}
              </div>
              <div className="text-sm text-red-600">Low CV Paras / 低CV段落</div>
            </div>
          </div>
        )}

        {/* CV Scale Legend */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">CV Scale / 变异系数等级:</h4>
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-green-500"></div>
              <span className="text-sm">≥0.35 (Natural / 自然)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-yellow-500"></div>
              <span className="text-sm">0.25-0.35 (Moderate / 中等)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-red-500"></div>
              <span className="text-sm">&lt;0.25 (AI-like Uniform / AI式均匀)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Paragraph Length Distribution Details */}
      {result && result.paragraphDetails && result.paragraphDetails.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            Paragraph Sentence Length Analysis / 段落句长分析
          </h3>

          <div className="space-y-4">
            {result.paragraphDetails.map((para, index) => {
              const cv = para.sentenceLengthCv || 0;
              const riskLevel = getCvRiskLevel(cv);
              const sentenceLengths = para.sentenceLengths || [];
              const maxLength = Math.max(...sentenceLengths, 1);

              return (
                <div
                  key={index}
                  className={clsx(
                    'border rounded-lg p-4',
                    riskLevel === 'high' ? 'border-red-300 bg-red-50' :
                    riskLevel === 'medium' ? 'border-yellow-300 bg-yellow-50' :
                    'border-green-300 bg-green-50'
                  )}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className={clsx(
                        'w-8 h-8 flex items-center justify-center rounded-full font-medium',
                        riskLevel === 'high' ? 'bg-red-200 text-red-700' :
                        riskLevel === 'medium' ? 'bg-yellow-200 text-yellow-700' :
                        'bg-green-200 text-green-700'
                      )}>
                        {index + 1}
                      </span>
                      <div>
                        <span className="font-medium text-gray-700">Paragraph {index + 1}</span>
                        <span className="text-sm text-gray-500 ml-2">
                          ({sentenceLengths.length} sentences)
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className={clsx(
                        'px-3 py-1 rounded-full text-sm font-medium',
                        getCvColor(cv)
                      )}>
                        <TrendingUp className="w-3 h-3 inline mr-1" />
                        CV: {cv.toFixed(3)}
                      </div>
                      {riskLevel === 'high' && (
                        <div className="flex items-center gap-1 text-red-600">
                          <AlertTriangle className="w-4 h-4" />
                          <span className="text-sm font-medium">Uniform Pattern</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Sentence Length Bars */}
                  {sentenceLengths.length > 0 && (
                    <div className="space-y-1 mt-3">
                      <div className="text-xs text-gray-500 mb-2">
                        Sentence lengths (words):
                      </div>
                      {sentenceLengths.map((length, sIndex) => (
                        <div key={sIndex} className="flex items-center gap-2">
                          <span className="text-xs text-gray-400 w-6">S{sIndex + 1}</span>
                          {renderLengthBar(length, maxLength)}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Statistics */}
                  <div className="grid grid-cols-4 gap-2 mt-3 pt-3 border-t border-gray-200">
                    <div className="text-center">
                      <div className="text-sm font-medium text-gray-700">
                        {sentenceLengths.length > 0 ? Math.min(...sentenceLengths) : 0}
                      </div>
                      <div className="text-xs text-gray-500">Min</div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm font-medium text-gray-700">
                        {sentenceLengths.length > 0 ? Math.max(...sentenceLengths) : 0}
                      </div>
                      <div className="text-xs text-gray-500">Max</div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm font-medium text-gray-700">
                        {sentenceLengths.length > 0
                          ? (sentenceLengths.reduce((a, b) => a + b, 0) / sentenceLengths.length).toFixed(1)
                          : 0}
                      </div>
                      <div className="text-xs text-gray-500">Mean</div>
                    </div>
                    <div className="text-center">
                      <div className={clsx(
                        'text-sm font-medium',
                        riskLevel === 'high' ? 'text-red-600' :
                        riskLevel === 'medium' ? 'text-yellow-600' : 'text-green-600'
                      )}>
                        {cv.toFixed(3)}
                      </div>
                      <div className="text-xs text-gray-500">CV</div>
                    </div>
                  </div>

                  {riskLevel === 'high' && (
                    <div className="mt-3 p-2 bg-white rounded border border-red-200 text-sm text-red-700">
                      <strong>Warning:</strong> This paragraph has uniform sentence lengths, a common AI pattern. Consider varying sentence structure.
                      <br />
                      <span className="text-red-600">警告：此段落句子长度过于均匀，这是常见的AI模式。建议变化句式结构。</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* CV Explanation */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          Understanding CV / 理解变异系数
        </h3>
        <div className="prose prose-sm text-gray-600">
          <p>
            <strong>Coefficient of Variation (CV)</strong> measures how spread out sentence lengths are within a paragraph.
            <br />
            <span className="text-gray-500">
              <strong>变异系数(CV)</strong>衡量段落内句子长度的分散程度。
            </span>
          </p>
          <ul className="mt-2 space-y-1">
            <li>CV = Standard Deviation / Mean</li>
            <li>Higher CV → More varied sentence lengths → More natural</li>
            <li>Lower CV → More uniform sentence lengths → More AI-like</li>
          </ul>
          <p className="mt-2">
            Human writers naturally vary sentence length based on content and rhythm. AI tends to produce more uniform sentence lengths.
            <br />
            <span className="text-gray-500">
              人类作者自然地根据内容和节奏变化句子长度。AI倾向于产生更均匀的句子长度。
            </span>
          </p>
        </div>
      </div>

      {/* Recommendations */}
      {result && result.recommendations && result.recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            Recommendations / 建议
          </h3>
          <ul className="space-y-2">
            {result.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-green-500 mt-1">•</span>
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

      {/* Navigation */}
      {showNavigation && (
        <div className="flex justify-between items-center pt-4 border-t">
          <Button variant="outline" onClick={goToPreviousStep} className="flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Previous: Step 3.3
          </Button>
          <Button onClick={goToNextStep} disabled={!result} className="flex items-center gap-2">
            Next: Step 3.5 Transitions
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
