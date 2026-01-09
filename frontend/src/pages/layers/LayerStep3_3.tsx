import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  Anchor,
  FileText,
  RefreshCw,
  Hash,
  Quote,
  Percent,
  AlertTriangle,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { paragraphLayerApi, ParagraphAnalysisResponse } from '../../services/analysisApi';

/**
 * Layer Step 3.3 - Anchor Density Analysis
 * 步骤 3.3 - 锚点密度分析
 *
 * Analyzes evidence density in paragraphs:
 * - 13 anchor types (citations, numbers, proper nouns, etc.)
 * - Calculates anchors per 100 words
 * - Flags high hallucination risk (<5 anchors/100 words)
 *
 * 分析段落中的证据密度：
 * - 13类学术锚点（引用、数字、专有名词等）
 * - 计算每100词的锚点数
 * - 标记高幻觉风险（<5锚点/100词）
 */

interface LayerStep3_3Props {
  documentIdProp?: string;
  onComplete?: (result: ParagraphAnalysisResponse) => void;
  showNavigation?: boolean;
  sectionContext?: Record<string, unknown>;
}

export default function LayerStep3_3({
  documentIdProp,
  onComplete,
  showNavigation = true,
  sectionContext,
}: LayerStep3_3Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer3-step3-3').catch(console.error);
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
      const analysisResult = await paragraphLayerApi.analyzeAnchor(documentText, sectionContext);
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
    navigate(`/flow/layer3-step3-4/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-2/${documentId}?${params.toString()}`);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getDensityColor = (density: number) => {
    if (density >= 10) return 'text-green-600 bg-green-100';
    if (density >= 5) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getDensityRiskLevel = (density: number): string => {
    if (density >= 10) return 'low';
    if (density >= 5) return 'medium';
    return 'high';
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
            <div className="p-2 bg-orange-100 rounded-lg">
              <Anchor className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3.3: Anchor Density Analysis
              </h2>
              <p className="text-sm text-gray-500">
                步骤 3.3: 锚点密度分析
              </p>
            </div>
          </div>
          {isAnalyzing && (
            <div className="flex items-center gap-2 text-orange-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing... / 分析中...</span>
            </div>
          )}
        </div>

        <p className="text-gray-600 mb-4">
          Analyzes evidence density (academic anchors) in each paragraph. Low anchor density (&lt;5/100 words) indicates potential AI-generated filler content (hallucination risk).
          <br />
          <span className="text-gray-500">
            分析每个段落的证据密度（学术锚点）。低锚点密度（&lt;5/100词）表示可能是AI填充内容（幻觉风险）。
          </span>
        </p>

        {/* Overall Metrics */}
        {result && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className={clsx('rounded-lg p-4', getRiskColor(result.riskLevel))}>
              <div className="text-2xl font-bold">{result.riskScore}/100</div>
              <div className="text-sm">Risk Score / 风险分数</div>
            </div>
            <div className={clsx('rounded-lg p-4', getDensityColor(result.anchorDensity || 0))}>
              <div className="text-2xl font-bold">
                {(result.anchorDensity || 0).toFixed(1)}
              </div>
              <div className="text-sm">Density/100 words / 密度</div>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-700">
                {result.paragraphCount || 0}
              </div>
              <div className="text-sm text-blue-600">Paragraphs / 段落数</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-red-700">
                {result.paragraphDetails?.filter(p => p.anchorCount < 5).length || 0}
              </div>
              <div className="text-sm text-red-600">High Risk / 高风险段落</div>
            </div>
          </div>
        )}

        {/* Density Scale Legend */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Anchor Density Scale / 锚点密度等级:</h4>
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-green-500"></div>
              <span className="text-sm">≥10 (Low Risk / 低风险)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-yellow-500"></div>
              <span className="text-sm">5-10 (Medium / 中等)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-red-500"></div>
              <span className="text-sm">&lt;5 (Hallucination Risk / 幻觉风险)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Paragraph Anchor Details */}
      {result && result.paragraphDetails && result.paragraphDetails.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-orange-600" />
            Paragraph Anchor Density / 段落锚点密度
          </h3>

          <div className="space-y-3">
            {result.paragraphDetails.map((para, index) => {
              // Calculate approximate density (anchors per 100 words equivalent)
              const density = para.anchorCount || 0;
              const riskLevel = getDensityRiskLevel(density);

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
                  <div className="flex items-center justify-between mb-2">
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
                        <span className="text-sm text-gray-500 ml-2">({para.role || 'body'})</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className={clsx(
                        'px-3 py-1 rounded-full text-sm font-medium',
                        getDensityColor(density)
                      )}>
                        <Anchor className="w-3 h-3 inline mr-1" />
                        {density} anchors
                      </div>
                      {riskLevel === 'high' && (
                        <div className="flex items-center gap-1 text-red-600">
                          <AlertTriangle className="w-4 h-4" />
                          <span className="text-sm font-medium">Hallucination Risk</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {riskLevel === 'high' && (
                    <div className="mt-2 p-2 bg-white rounded border border-red-200 text-sm text-red-700">
                      <strong>Warning:</strong> This paragraph may contain AI-generated filler content. Consider adding specific data, citations, or concrete examples.
                      <br />
                      <span className="text-red-600">警告：此段落可能包含AI填充内容。建议添加具体数据、引用或具体例子。</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Anchor Types Info */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Hash className="w-5 h-5 text-blue-600" />
          Academic Anchor Types / 学术锚点类型
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {[
            { icon: Percent, label: 'Percentages', labelZh: '百分比', example: '14.2%' },
            { icon: Hash, label: 'Numbers', labelZh: '数字', example: '3.5, 500' },
            { icon: Quote, label: 'Citations', labelZh: '引用', example: '[1], (Smith, 2023)' },
            { icon: FileText, label: 'Statistics', labelZh: '统计值', example: 'p < 0.05' },
          ].map((type, index) => (
            <div key={index} className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <type.icon className="w-4 h-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-700">{type.label}</span>
              </div>
              <div className="text-xs text-gray-500">{type.labelZh}</div>
              <div className="text-xs text-blue-600 mt-1 font-mono">{type.example}</div>
            </div>
          ))}
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
            Previous: Step 3.2
          </Button>
          <Button onClick={goToNextStep} disabled={!result} className="flex items-center gap-2">
            Next: Step 3.4 Length Distribution
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
