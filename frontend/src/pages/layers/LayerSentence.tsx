import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  MessageSquare,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Repeat,
  Circle,
  Tag,
  Wand2,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import {
  sentenceLayerApi,
  paragraphLayerApi,
  SentenceAnalysisResponse,
  DetectionIssue,
  RewriteContext,
} from '../../services/analysisApi';

/**
 * Layer Sentence (Layer 2) - Sentence Analysis
 * 句子层（第2层）- 句子分析
 *
 * Steps:
 * - Step 4.1: Sentence Pattern Detection (句式模式检测)
 * - Step 4.2: Syntactic Void Detection (句法空洞检测)
 * - Step 4.3: Sentence Role Classification (句子角色分类)
 * - Step 4.4: Sentence Polish Context (句子润色上下文)
 *
 * IMPORTANT: All sentence analysis is performed within paragraph context.
 * 重要：所有句子分析都在段落上下文中进行。
 */

interface LayerSentenceProps {
  documentIdProp?: string;
  onComplete?: (result: SentenceAnalysisResponse) => void;
  showNavigation?: boolean;
}

export default function LayerSentence({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerSentenceProps) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer-sentence').catch(console.error);
    }
  }, [sessionId]);

  // Analysis state
  const [result, setResult] = useState<SentenceAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<'4.1' | '4.2' | '4.3' | '4.4'>('4.1');

  // Document context
  const [documentText, setDocumentText] = useState<string>('');
  const [paragraphContext, setParagraphContext] = useState<Record<string, unknown> | null>(null);

  // Selected sentence for polish context
  const [selectedSentenceIndex, setSelectedSentenceIndex] = useState<number | null>(null);
  const [rewriteContext, setRewriteContext] = useState<RewriteContext | null>(null);
  const [isLoadingContext, setIsLoadingContext] = useState(false);

  // Issue expansion
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);
  const [expandedSentenceIndex, setExpandedSentenceIndex] = useState<number | null>(null);

  const isAnalyzingRef = useRef(false);

  useEffect(() => {
    if (documentId) {
      loadDocumentText(documentId);
    }
  }, [documentId]);

  const loadDocumentText = async (docId: string) => {
    try {
      const doc = await documentApi.get(docId);
      // Use originalText field from API (camelCase transformed from original_text)
      if (doc.originalText) {
        setDocumentText(doc.originalText);
      } else {
        console.error('Document has no original text');
        setError('Document text not found');
      }
    } catch (err) {
      console.error('Failed to load document:', err);
      setError('Failed to load document');
    }
  };

  useEffect(() => {
    if (documentText && !isAnalyzingRef.current) {
      analyzeSentence();
    }
  }, [documentText]);

  const analyzeSentence = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;

    setIsLoading(true);
    setError(null);

    try {
      console.log('Layer 2: Getting paragraph context from Layer 3...');

      // Get paragraph context from Layer 3
      const paraContext = await paragraphLayerApi.getContext(documentText);
      setParagraphContext(paraContext as Record<string, unknown>);

      console.log('Layer 2: Analyzing sentences with paragraph context...');

      // Run sentence analysis with context
      const analysisResult = await sentenceLayerApi.analyze(
        documentText,
        paraContext as Record<string, unknown>
      );
      console.log('Layer 2 result:', analysisResult);

      setResult(analysisResult);

      if (onComplete) {
        onComplete(analysisResult);
      }
    } catch (err: unknown) {
      console.error('Sentence analysis failed:', err);
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      if (axiosErr.response?.data?.detail) {
        setError(axiosErr.response.data.detail);
      } else {
        setError(err instanceof Error ? err.message : 'Analysis failed');
      }
    } finally {
      setIsLoading(false);
      isAnalyzingRef.current = false;
    }
  };

  // Load rewrite context for a sentence (Step 4.4)
  const loadRewriteContext = useCallback(async (sentenceIndex: number, paragraphIndex: number) => {
    if (!documentText) return;

    setIsLoadingContext(true);
    setSelectedSentenceIndex(sentenceIndex);

    try {
      const context = await sentenceLayerApi.getRewriteContext(
        documentText,
        sentenceIndex,
        paragraphIndex
      );
      setRewriteContext(context);
    } catch (err) {
      console.error('Failed to load rewrite context:', err);
    } finally {
      setIsLoadingContext(false);
    }
  }, [documentText]);

  const handleIssueClick = useCallback((index: number) => {
    setExpandedIssueIndex(prev => prev === index ? null : index);
  }, []);

  const handleSentenceClick = useCallback((index: number) => {
    setExpandedSentenceIndex(prev => prev === index ? null : index);
  }, []);

  const handleNext = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/layer-lexical/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

  const handleBack = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/layer-paragraph/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

  const renderRiskBadge = (level: string) => (
    <span className={clsx(
      'px-2 py-1 rounded text-xs font-medium',
      level === 'high' && 'bg-red-100 text-red-700',
      level === 'medium' && 'bg-yellow-100 text-yellow-700',
      level === 'low' && 'bg-green-100 text-green-700'
    )}>
      {level === 'high' ? '高风险' : level === 'medium' ? '中风险' : '低风险'}
    </span>
  );

  const renderSeverityBadge = (severity: string) => (
    <span className={clsx(
      'px-2 py-0.5 rounded text-xs font-medium',
      severity === 'high' && 'bg-red-100 text-red-700',
      severity === 'medium' && 'bg-yellow-100 text-yellow-700',
      severity === 'low' && 'bg-blue-100 text-blue-700'
    )}>
      {severity === 'high' ? '高' : severity === 'medium' ? '中' : '低'}
    </span>
  );

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex items-center justify-center min-h-[50vh]">
          <LoadingMessage category="structure" size="lg" showEnglish={true} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex flex-col items-center justify-center min-h-[50vh]">
          <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
          <p className="text-red-600 text-lg mb-4">{error}</p>
          {showNavigation && (
            <Button variant="outline" onClick={handleBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回段落层
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="p-2 rounded-lg bg-orange-100 text-orange-600 mr-3">
              <MessageSquare className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Layer 2: 句子层分析
              </h1>
              <p className="text-gray-600 mt-1">
                Sentence Layer Analysis (with Paragraph Context)
              </p>
            </div>
          </div>
          {showNavigation && (
            <Button variant="outline" onClick={handleBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回
            </Button>
          )}
        </div>

        {/* 5-Layer Progress with Step 1.0 Term Lock */}
        {/* 5层进度（含Step 1.0词汇锁定）*/}
        <div className="mt-4 flex items-center text-sm text-gray-500 flex-wrap gap-y-1">
          <button
            onClick={() => navigate(`/flow/term-lock/${documentId}?mode=${mode}${sessionId ? `&session=${sessionId}` : ''}`)}
            className="text-gray-400 hover:text-indigo-600 hover:underline transition-colors"
          >
            Step 1.0
          </button>
          <span className="mx-2">→</span>
          <span className="text-gray-400">Layer 5</span>
          <span className="mx-2">→</span>
          <span className="text-gray-400">Layer 4</span>
          <span className="mx-2">→</span>
          <span className="text-gray-400">Layer 3</span>
          <span className="mx-2">→</span>
          <span className="font-medium text-orange-600 bg-orange-50 px-2 py-1 rounded">
            Layer 2 句子
          </span>
          <span className="mx-2">→</span>
          <span>Layer 1</span>
        </div>

        {/* Context indicator */}
        <div className="mt-2 text-xs text-gray-500 bg-gray-50 px-3 py-1 rounded inline-block">
          已加载段落上下文用于句子分析
        </div>

        {/* Step tabs */}
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            onClick={() => setCurrentStep('4.1')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '4.1' ? 'bg-orange-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <Repeat className="w-4 h-4 mr-1" />
            4.1 模式
          </button>
          <button
            onClick={() => setCurrentStep('4.2')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '4.2' ? 'bg-orange-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <Circle className="w-4 h-4 mr-1" />
            4.2 空洞
          </button>
          <button
            onClick={() => setCurrentStep('4.3')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '4.3' ? 'bg-orange-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <Tag className="w-4 h-4 mr-1" />
            4.3 角色
          </button>
          <button
            onClick={() => setCurrentStep('4.4')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '4.4' ? 'bg-orange-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <Wand2 className="w-4 h-4 mr-1" />
            4.4 润色
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Score Card */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-1">
                  句子层风险分数 / Sentence Layer Risk Score
                </h3>
                <p className="text-sm text-gray-500">
                  分析句式模式、句法空洞和句子角色
                </p>
              </div>
              <div className="text-right">
                <p className={clsx(
                  'text-4xl font-bold',
                  result.riskScore <= 30 && 'text-green-600',
                  result.riskScore > 30 && result.riskScore <= 60 && 'text-yellow-600',
                  result.riskScore > 60 && 'text-red-600'
                )}>
                  {result.riskScore}
                </p>
                {renderRiskBadge(result.riskLevel)}
              </div>
            </div>

            <div className="mt-4 grid grid-cols-4 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-orange-600">{result.sentenceCount || 0}</p>
                <p className="text-sm text-gray-600">句子数</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-orange-600">{result.patternScore || 0}</p>
                <p className="text-sm text-gray-600">模式分</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-orange-600">{result.voidCount || 0}</p>
                <p className="text-sm text-gray-600">空洞数</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-orange-600">
                  {Object.keys(result.roleDistribution || {}).length || 0}
                </p>
                <p className="text-sm text-gray-600">角色类型</p>
              </div>
            </div>
          </div>

          {/* Step 4.1: Pattern Detection */}
          {currentStep === '4.1' && result.sentenceDetails && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Repeat className="w-5 h-5 mr-2 text-orange-600" />
                句式模式检测 / Sentence Pattern Detection
              </h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {result.sentenceDetails.slice(0, 20).map((sentence, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleSentenceClick(idx)}
                    className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-700 truncate flex-1 mr-2">
                        {sentence.text?.slice(0, 60) || `句子 ${idx + 1}`}...
                      </span>
                      <span className="text-xs px-2 py-1 bg-orange-100 text-orange-700 rounded">
                        {sentence.length} 词
                      </span>
                    </div>
                    {expandedSentenceIndex === idx && sentence.issues.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {sentence.issues.map((issue, iIdx) => (
                          <p key={iIdx} className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
                            {issue}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {result.sentenceDetails.length > 20 && (
                  <p className="text-sm text-gray-500 text-center py-2">
                    还有 {result.sentenceDetails.length - 20} 个句子...
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Step 4.2: Void Detection */}
          {currentStep === '4.2' && result.sentenceDetails && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Circle className="w-5 h-5 mr-2 text-orange-600" />
                句法空洞检测 / Syntactic Void Detection
              </h3>
              {result.voidCount === 0 ? (
                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="text-green-800">未检测到句法空洞</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {result.sentenceDetails.filter(s => s.hasVoid).map((sentence, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-red-50 rounded-lg border-l-4 border-red-500"
                    >
                      <p className="text-sm text-gray-700 mb-2">{sentence.text}</p>
                      {sentence.voidTypes && sentence.voidTypes.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {sentence.voidTypes.map((type, tIdx) => (
                            <span key={tIdx} className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded">
                              {type}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Step 4.3: Role Classification */}
          {currentStep === '4.3' && result.roleDistribution && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Tag className="w-5 h-5 mr-2 text-orange-600" />
                句子角色分布 / Sentence Role Distribution
              </h3>
              <div className="grid grid-cols-2 gap-4 mb-4">
                {Object.entries(result.roleDistribution).map(([role, count]) => (
                  <div key={role} className="p-3 bg-gray-50 rounded-lg flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">{role}</span>
                    <span className="text-lg font-bold text-orange-600">{count}</span>
                  </div>
                ))}
              </div>
              {result.sentenceDetails && (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {result.sentenceDetails.slice(0, 10).map((sentence, idx) => (
                    <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-700 truncate flex-1 mr-2">
                          {sentence.text?.slice(0, 50)}...
                        </span>
                        <span className="text-xs px-2 py-1 bg-orange-100 text-orange-700 rounded">
                          {sentence.role}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Step 4.4: Polish Context */}
          {currentStep === '4.4' && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Wand2 className="w-5 h-5 mr-2 text-orange-600" />
                句子润色上下文 / Sentence Polish Context
              </h3>
              <p className="text-sm text-gray-500 mb-4">
                选择一个句子查看其完整的段落上下文，用于更准确的改写
              </p>
              {result.sentenceDetails && (
                <div className="space-y-2 max-h-64 overflow-y-auto mb-4">
                  {result.sentenceDetails.slice(0, 15).map((sentence, idx) => (
                    <div
                      key={idx}
                      onClick={() => loadRewriteContext(sentence.index, sentence.paragraphIndex)}
                      className={clsx(
                        'p-3 rounded-lg cursor-pointer transition-colors',
                        selectedSentenceIndex === sentence.index
                          ? 'bg-orange-100 border-2 border-orange-500'
                          : 'bg-gray-50 hover:bg-gray-100'
                      )}
                    >
                      <p className="text-sm text-gray-700">{sentence.text?.slice(0, 80)}...</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Rewrite Context Display */}
              {isLoadingContext && (
                <div className="p-4 bg-gray-50 rounded-lg text-center">
                  <p className="text-gray-500">加载上下文中...</p>
                </div>
              )}

              {rewriteContext && !isLoadingContext && (
                <div className="space-y-4 p-4 bg-orange-50 rounded-lg">
                  <div>
                    <h4 className="font-medium text-gray-800 mb-2">当前句子</h4>
                    <p className="text-sm bg-white p-3 rounded">{rewriteContext.sentenceText}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-800 mb-2">句子角色</h4>
                    <span className="text-xs px-2 py-1 bg-orange-100 text-orange-700 rounded">
                      {rewriteContext.sentenceRole}
                    </span>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-800 mb-2">段落上下文</h4>
                    <p className="text-sm bg-white p-3 rounded text-gray-600">
                      {rewriteContext.paragraphText}
                    </p>
                  </div>
                  {rewriteContext.prevSentence && (
                    <div>
                      <h4 className="font-medium text-gray-800 mb-2">前一句</h4>
                      <p className="text-sm bg-white p-3 rounded text-gray-500">
                        {rewriteContext.prevSentence}
                      </p>
                    </div>
                  )}
                  {rewriteContext.nextSentence && (
                    <div>
                      <h4 className="font-medium text-gray-800 mb-2">后一句</h4>
                      <p className="text-sm bg-white p-3 rounded text-gray-500">
                        {rewriteContext.nextSentence}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Issues */}
          {result.issues && result.issues.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                检测到 {result.issues.length} 个问题
              </h3>
              <div className="space-y-3">
                {result.issues.map((issue: DetectionIssue, idx: number) => (
                  <div key={idx}>
                    <div
                      onClick={() => handleIssueClick(idx)}
                      className={clsx(
                        'p-4 rounded-lg border-l-4 cursor-pointer transition-all hover:shadow-md',
                        issue.severity === 'high' && 'bg-red-50 border-red-500',
                        issue.severity === 'medium' && 'bg-yellow-50 border-yellow-500',
                        issue.severity === 'low' && 'bg-blue-50 border-blue-500'
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="font-medium text-gray-800">{issue.descriptionZh}</p>
                          <p className="text-sm text-gray-500 mt-1">{issue.description}</p>
                        </div>
                        <div className="flex items-center space-x-2 ml-4">
                          {renderSeverityBadge(issue.severity)}
                          {expandedIssueIndex === idx ? (
                            <ChevronUp className="w-5 h-5 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400" />
                          )}
                        </div>
                      </div>
                    </div>
                    {expandedIssueIndex === idx && issue.suggestion && (
                      <div className="ml-4 p-4 bg-white border rounded-lg shadow-sm mt-2">
                        <p className="text-sm text-gray-600">{issue.suggestionZh || issue.suggestion}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations && result.recommendations.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                改进建议
              </h3>
              <div className="space-y-2">
                {(result.recommendationsZh || result.recommendations).map((rec, idx) => (
                  <div key={idx} className="p-3 bg-green-50 rounded-lg">
                    <p className="text-sm text-green-800">{rec}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.processingTimeMs && (
            <p className="text-xs text-gray-400 text-center">
              分析耗时 {result.processingTimeMs}ms
            </p>
          )}

          {showNavigation && (
            <div className="flex justify-between pt-4">
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                返回段落层
              </Button>
              <Button onClick={handleNext}>
                继续到词汇层
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
