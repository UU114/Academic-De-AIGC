import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  GitMerge,
  FileText,
  RefreshCw,
  Link,
  Repeat,
  AlertTriangle,
  ArrowDown,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { paragraphLayerApi, ParagraphTransitionResponse, ParagraphTransitionInfo } from '../../services/analysisApi';

/**
 * Layer Step 3.5 - Paragraph Transition Analysis
 * 步骤 3.5 - 段落过渡分析
 *
 * Analyzes transitions between paragraphs:
 * - Explicit connectors (However, Therefore, etc.)
 * - Semantic echo (keyword repetition)
 * - Transition quality (smooth/abrupt/formulaic)
 * - Formulaic opener detection
 *
 * 分析段落间过渡：
 * - 显式连接词（然而、因此等）
 * - 语义回响（关键词重复）
 * - 过渡质量（流畅/突兀/公式化）
 * - 公式化开头检测
 */

interface LayerStep3_5Props {
  documentIdProp?: string;
  onComplete?: (result: ParagraphTransitionResponse) => void;
  showNavigation?: boolean;
  sectionContext?: Record<string, unknown>;
}

export default function LayerStep3_5({
  documentIdProp,
  onComplete,
  showNavigation = true,
  sectionContext,
}: LayerStep3_5Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer3-step3-5').catch(console.error);
    }
  }, [sessionId]);

  const [result, setResult] = useState<ParagraphTransitionResponse | null>(null);
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
      const analysisResult = await paragraphLayerApi.analyzeTransitions(
        documentText,
        undefined,
        sessionId || undefined,
        sectionContext
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

  const goToNextStep = () => {
    // Go to Layer 2 (Sentence Layer) first step
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer2-step4-0/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-4/${documentId}?${params.toString()}`);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getTransitionQualityColor = (quality: string) => {
    switch (quality) {
      case 'smooth': return 'text-green-600 bg-green-100 border-green-300';
      case 'abrupt': return 'text-red-600 bg-red-100 border-red-300';
      case 'formulaic': return 'text-yellow-600 bg-yellow-100 border-yellow-300';
      default: return 'text-gray-600 bg-gray-100 border-gray-300';
    }
  };

  const getQualityLabel = (quality: string): { en: string; zh: string } => {
    switch (quality) {
      case 'smooth': return { en: 'Smooth', zh: '流畅' };
      case 'abrupt': return { en: 'Abrupt', zh: '突兀' };
      case 'formulaic': return { en: 'Formulaic', zh: '公式化' };
      default: return { en: 'Unknown', zh: '未知' };
    }
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
            <div className="p-2 bg-teal-100 rounded-lg">
              <GitMerge className="w-6 h-6 text-teal-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3.5: Paragraph Transition Analysis
              </h2>
              <p className="text-sm text-gray-500">
                步骤 3.5: 段落过渡分析
              </p>
            </div>
          </div>
          {isAnalyzing && (
            <div className="flex items-center gap-2 text-teal-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing... / 分析中...</span>
            </div>
          )}
        </div>

        <p className="text-gray-600 mb-4">
          Analyzes how paragraphs connect to each other. Detects formulaic transitions, abrupt topic shifts, and semantic echo patterns.
          <br />
          <span className="text-gray-500">
            分析段落之间的连接方式。检测公式化过渡、突兀的主题转换和语义回响模式。
          </span>
        </p>

        {/* Overall Metrics */}
        {result && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className={clsx('rounded-lg p-4', getRiskColor(result.riskLevel))}>
              <div className="text-2xl font-bold">{result.riskScore}/100</div>
              <div className="text-sm">Risk Score / 风险分数</div>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-700">
                {result.transitions?.length || 0}
              </div>
              <div className="text-sm text-blue-600">Transitions / 过渡数</div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-yellow-700">
                {result.transitions?.filter(t => t.isFormulaicOpener).length || 0}
              </div>
              <div className="text-sm text-yellow-600">Formulaic / 公式化</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-red-700">
                {result.transitions?.filter(t => t.transitionQuality === 'abrupt').length || 0}
              </div>
              <div className="text-sm text-red-600">Abrupt / 突兀</div>
            </div>
          </div>
        )}

        {/* Quality Legend */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Transition Quality / 过渡质量:</h4>
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-green-500"></div>
              <span className="text-sm">Smooth (Natural / 自然)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-yellow-500"></div>
              <span className="text-sm">Formulaic (AI pattern / AI模式)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-red-500"></div>
              <span className="text-sm">Abrupt (Topic shift / 主题跳跃)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Transition Details */}
      {result && result.transitions && result.transitions.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Link className="w-5 h-5 text-teal-600" />
            Paragraph Transitions / 段落过渡详情
          </h3>

          <div className="space-y-4">
            {result.transitions.map((transition: ParagraphTransitionInfo, index: number) => {
              const qualityLabel = getQualityLabel(transition.transitionQuality);
              return (
                <div
                  key={index}
                  className={clsx(
                    'border rounded-lg p-4',
                    getTransitionQualityColor(transition.transitionQuality)
                  )}
                >
                  {/* Transition Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-1">
                        <span className="w-7 h-7 flex items-center justify-center bg-gray-200 rounded-full text-sm font-medium">
                          {transition.fromParagraph + 1}
                        </span>
                        <ArrowDown className="w-4 h-4 text-gray-400" />
                        <span className="w-7 h-7 flex items-center justify-center bg-gray-200 rounded-full text-sm font-medium">
                          {transition.toParagraph + 1}
                        </span>
                      </div>
                      <span className="font-medium text-gray-700">
                        Para {transition.fromParagraph + 1} → Para {transition.toParagraph + 1}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className={clsx(
                        'px-3 py-1 rounded-full text-sm font-medium',
                        getTransitionQualityColor(transition.transitionQuality)
                      )}>
                        {qualityLabel.en} / {qualityLabel.zh}
                      </div>
                      {transition.isFormulaicOpener && (
                        <div className="flex items-center gap-1 text-yellow-600">
                          <AlertTriangle className="w-4 h-4" />
                          <span className="text-sm">Formulaic</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Opener Text */}
                  {transition.openerText && (
                    <div className="bg-white bg-opacity-50 rounded p-3 mb-3">
                      <div className="text-xs text-gray-500 mb-1">Opening text / 开头文本:</div>
                      <div className="text-sm text-gray-700 italic">
                        "{transition.openerText}"
                      </div>
                      {transition.openerPattern && (
                        <div className="text-xs text-gray-500 mt-1">
                          Pattern: {transition.openerPattern}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Transition Analysis */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {/* Connector */}
                    <div className="bg-white bg-opacity-50 rounded p-2">
                      <div className="text-xs text-gray-500">Connector</div>
                      <div className="flex items-center gap-1 mt-1">
                        {transition.hasExplicitConnector ? (
                          <>
                            <CheckCircle className="w-3 h-3 text-green-500" />
                            <span className="text-sm font-medium text-green-700">Yes</span>
                          </>
                        ) : (
                          <>
                            <AlertCircle className="w-3 h-3 text-gray-400" />
                            <span className="text-sm text-gray-500">No</span>
                          </>
                        )}
                      </div>
                      {transition.connectorWords && transition.connectorWords.length > 0 && (
                        <div className="text-xs text-blue-600 mt-1">
                          {transition.connectorWords.join(', ')}
                        </div>
                      )}
                    </div>

                    {/* Semantic Echo */}
                    <div className="bg-white bg-opacity-50 rounded p-2">
                      <div className="text-xs text-gray-500">Semantic Echo</div>
                      <div className="text-sm font-medium mt-1">
                        {(transition.semanticEchoScore * 100).toFixed(0)}%
                      </div>
                      {transition.echoedKeywords && transition.echoedKeywords.length > 0 && (
                        <div className="text-xs text-purple-600 mt-1">
                          {transition.echoedKeywords.slice(0, 3).join(', ')}
                          {transition.echoedKeywords.length > 3 && '...'}
                        </div>
                      )}
                    </div>

                    {/* Formulaic */}
                    <div className="bg-white bg-opacity-50 rounded p-2">
                      <div className="text-xs text-gray-500">Formulaic Opener</div>
                      <div className="flex items-center gap-1 mt-1">
                        {transition.isFormulaicOpener ? (
                          <>
                            <AlertTriangle className="w-3 h-3 text-yellow-500" />
                            <span className="text-sm font-medium text-yellow-700">Yes</span>
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-3 h-3 text-green-500" />
                            <span className="text-sm text-green-600">No</span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Risk Score */}
                    <div className="bg-white bg-opacity-50 rounded p-2">
                      <div className="text-xs text-gray-500">Risk Score</div>
                      <div className={clsx(
                        'text-sm font-medium mt-1',
                        transition.riskScore >= 70 ? 'text-red-600' :
                        transition.riskScore >= 40 ? 'text-yellow-600' : 'text-green-600'
                      )}>
                        {transition.riskScore}/100
                      </div>
                    </div>
                  </div>

                  {/* Warning for problematic transitions */}
                  {(transition.transitionQuality === 'formulaic' || transition.transitionQuality === 'abrupt') && (
                    <div className="mt-3 p-2 bg-white rounded border text-sm">
                      {transition.transitionQuality === 'formulaic' ? (
                        <>
                          <strong className="text-yellow-700">Formulaic Pattern:</strong>
                          <span className="text-gray-600 ml-1">
                            This transition uses common AI patterns. Consider more natural phrasing.
                          </span>
                          <br />
                          <span className="text-yellow-600">公式化模式：此过渡使用常见的AI模式。建议使用更自然的表达。</span>
                        </>
                      ) : (
                        <>
                          <strong className="text-red-700">Abrupt Transition:</strong>
                          <span className="text-gray-600 ml-1">
                            Topic shift without proper connection. Add transitional sentences.
                          </span>
                          <br />
                          <span className="text-red-600">突兀过渡：主题转换缺乏适当衔接。建议添加过渡句。</span>
                        </>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Formulaic Opener Patterns */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Repeat className="w-5 h-5 text-yellow-600" />
          Common Formulaic Openers / 常见公式化开头
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            { en: 'Furthermore, ...', zh: '此外，...' },
            { en: 'In addition, ...', zh: '另外，...' },
            { en: 'Moreover, ...', zh: '而且，...' },
            { en: 'It is worth noting that...', zh: '值得注意的是...' },
            { en: 'In this context, ...', zh: '在这种情况下，...' },
            { en: 'Building upon this, ...', zh: '在此基础上，...' },
          ].map((pattern, index) => (
            <div key={index} className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="text-sm font-medium text-yellow-700">{pattern.en}</div>
              <div className="text-xs text-yellow-600">{pattern.zh}</div>
            </div>
          ))}
        </div>
        <p className="mt-3 text-sm text-gray-600">
          These openers are commonly overused by AI. While valid in moderation, excessive use signals AI generation.
          <br />
          <span className="text-gray-500">
            这些开头常被AI过度使用。适度使用是有效的，但过度使用则表明AI生成。
          </span>
        </p>
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

      {/* Layer 3 Completion Summary */}
      {result && (
        <div className="bg-teal-50 rounded-lg shadow-sm border border-teal-200 p-6">
          <h3 className="text-lg font-semibold text-teal-900 mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-teal-600" />
            Layer 3 Complete / 第3层完成
          </h3>
          <p className="text-teal-700">
            Paragraph-level analysis is complete. Proceed to Layer 2 for sentence-level analysis.
            <br />
            <span className="text-teal-600">
              段落级分析已完成。继续进行第2层句子级分析。
            </span>
          </p>
        </div>
      )}

      {/* Navigation */}
      {showNavigation && (
        <div className="flex justify-between items-center pt-4 border-t">
          <Button variant="outline" onClick={goToPreviousStep} className="flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Previous: Step 3.4
          </Button>
          <Button onClick={goToNextStep} disabled={!result} className="flex items-center gap-2">
            Next: Layer 2 Sentence Analysis
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
