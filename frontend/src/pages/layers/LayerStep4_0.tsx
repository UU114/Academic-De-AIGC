import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  Type,
  FileText,
  RefreshCw,
  Activity,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { sentenceLayerApi, SentenceIdentificationResponse, SentenceInfo } from '../../services/analysisApi';

/**
 * Layer Step 4.0 - Sentence Identification & Labeling
 * 步骤 4.0 - 句子识别与标注
 *
 * Identifies all sentences and labels each with:
 * - Sentence type (simple/compound/complex/compound_complex)
 * - Function role (topic/evidence/analysis/transition/conclusion)
 * - Voice (active/passive)
 * - Opener word
 * - Clause depth
 *
 * 识别所有句子并标注：
 * - 句式类型（简单句/并列句/复杂句/复合复杂句）
 * - 功能角色（主题/证据/分析/过渡/结论）
 * - 语态（主动/被动）
 * - 句首词
 * - 从句深度
 */

interface LayerStep4_0Props {
  documentIdProp?: string;
  onComplete?: (result: SentenceIdentificationResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep4_0({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep4_0Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer2-step4-0').catch(console.error);
    }
  }, [sessionId]);

  const [result, setResult] = useState<SentenceIdentificationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedParagraph, setExpandedParagraph] = useState<number | null>(null);

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
      const analysisResult = await sentenceLayerApi.identifySentences(documentText, undefined, sessionId || undefined);
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
    navigate(`/flow/layer2-step4-1/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-5/${documentId}?${params.toString()}`);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'simple': return 'bg-blue-100 text-blue-700';
      case 'compound': return 'bg-green-100 text-green-700';
      case 'complex': return 'bg-purple-100 text-purple-700';
      case 'compound_complex': return 'bg-orange-100 text-orange-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getVoiceColor = (voice: string) => {
    return voice === 'passive' ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage category="general" />
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
            <div className="p-2 bg-blue-100 rounded-lg">
              <Type className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 4.0: Sentence Identification
              </h2>
              <p className="text-sm text-gray-500">
                步骤 4.0: 句子识别与标注
              </p>
            </div>
          </div>
          {isAnalyzing && (
            <div className="flex items-center gap-2 text-blue-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing... / 分析中...</span>
            </div>
          )}
        </div>

        <p className="text-gray-600 mb-4">
          Identifies all sentences and labels each with type (simple/compound/complex), voice (active/passive), and function role.
          <br />
          <span className="text-gray-500">
            识别所有句子并标注类型、语态和功能角色。
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
                {result.sentenceCount}
              </div>
              <div className="text-sm text-blue-600">Sentences / 句子数</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-700">
                {Object.keys(result.paragraphSentenceMap || {}).length}
              </div>
              <div className="text-sm text-purple-600">Paragraphs / 段落数</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-orange-700">
                {result.typeDistribution?.simple || 0}
              </div>
              <div className="text-sm text-orange-600">Simple / 简单句</div>
            </div>
          </div>
        )}

        {/* Type Distribution */}
        {result && result.typeDistribution && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Sentence Type Distribution / 句式类型分布:</h4>
            <div className="flex flex-wrap gap-3">
              {Object.entries(result.typeDistribution).map(([type, count]) => (
                <div key={type} className="flex items-center gap-2">
                  <span className={clsx('px-2 py-1 rounded text-xs font-medium', getTypeColor(type))}>
                    {type}
                  </span>
                  <span className="text-sm text-gray-600">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Sentence List by Paragraph */}
      {result && result.sentences && result.sentences.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            Sentences by Paragraph / 按段落显示句子
          </h3>

          <div className="space-y-4">
            {Object.entries(result.paragraphSentenceMap || {}).map(([paraIdx, sentenceIndices]) => {
              const paragraphSentences = (sentenceIndices as number[]).map(
                idx => result.sentences.find(s => s.index === idx)
              ).filter(Boolean) as SentenceInfo[];

              return (
                <div
                  key={paraIdx}
                  className="border rounded-lg overflow-hidden"
                >
                  <div
                    className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer"
                    onClick={() => setExpandedParagraph(
                      expandedParagraph === Number(paraIdx) ? null : Number(paraIdx)
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-8 h-8 flex items-center justify-center bg-blue-200 text-blue-700 rounded-full font-medium">
                        {Number(paraIdx) + 1}
                      </span>
                      <span className="font-medium text-gray-700">
                        Paragraph {Number(paraIdx) + 1}
                      </span>
                      <span className="text-sm text-gray-500">
                        ({paragraphSentences.length} sentences)
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {paragraphSentences.some(s => s.sentenceType === 'simple') && (
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-600 text-xs rounded">
                          {paragraphSentences.filter(s => s.sentenceType === 'simple').length} simple
                        </span>
                      )}
                      <Activity className={clsx(
                        'w-5 h-5 transition-transform',
                        expandedParagraph === Number(paraIdx) ? 'rotate-180' : ''
                      )} />
                    </div>
                  </div>

                  {expandedParagraph === Number(paraIdx) && (
                    <div className="p-4 space-y-3">
                      {paragraphSentences.map((sent, i) => (
                        <div
                          key={sent.index}
                          className="p-3 border rounded-lg bg-white hover:bg-gray-50"
                        >
                          <div className="flex items-start gap-3">
                            <span className="w-6 h-6 flex items-center justify-center bg-gray-200 text-gray-600 rounded text-sm font-medium">
                              {i + 1}
                            </span>
                            <div className="flex-1">
                              <p className="text-gray-700 mb-2">{sent.text}</p>
                              <div className="flex flex-wrap gap-2">
                                <span className={clsx('px-2 py-0.5 text-xs rounded font-medium', getTypeColor(sent.sentenceType))}>
                                  {sent.sentenceType}
                                </span>
                                <span className={clsx('px-2 py-0.5 text-xs rounded font-medium', getVoiceColor(sent.voice))}>
                                  {sent.voice}
                                </span>
                                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                                  {sent.functionRole}
                                </span>
                                <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">
                                  {sent.wordCount} words
                                </span>
                                {sent.openerWord && (
                                  <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded">
                                    Opener: {sent.openerWord}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Issues */}
      {result && result.issues && result.issues.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            Issues Detected / 检测到的问题
          </h3>
          <div className="space-y-3">
            {result.issues.map((issue, index) => (
              <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-red-700">{String(issue.description || '')}</div>
                    {issue.descriptionZh ? (
                      <div className="text-sm text-red-600 mt-1">{String(issue.descriptionZh)}</div>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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
            Previous: Layer 3
          </Button>
          <Button onClick={goToNextStep} disabled={!result} className="flex items-center gap-2">
            Next: Step 4.1 Pattern Analysis
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
