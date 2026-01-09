import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Type,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Fingerprint,
  Link,
  AlertTriangle,
  Copy,
  Check,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import {
  lexicalLayerApi,
  LexicalAnalysisResponse,
  DetectionIssue,
} from '../../services/analysisApi';

/**
 * Layer Lexical (Layer 1) - Lexical Analysis
 * 词汇层（第1层）- 词汇分析
 *
 * Steps:
 * - Step 5.1: Fingerprint Detection (指纹词检测)
 * - Step 5.2: Connector Analysis (连接词分析)
 * - Step 5.3: Word-Level Risk (词级风险)
 *
 * This is the finest granularity layer, analyzing individual words.
 * 这是最细粒度的层，分析单个词。
 */

interface LayerLexicalProps {
  documentIdProp?: string;
  onComplete?: (result: LexicalAnalysisResponse) => void;
  showNavigation?: boolean;
}

export default function LayerLexical({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerLexicalProps) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer-lexical').catch(console.error);
    }
  }, [sessionId]);

  // Analysis state
  const [result, setResult] = useState<LexicalAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<'5.1' | '5.2' | '5.3'>('5.1');

  // Document text
  const [documentText, setDocumentText] = useState<string>('');

  // Issue expansion
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

  // Copy state for replacements
  const [copiedWord, setCopiedWord] = useState<string | null>(null);

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
      analyzeLexical();
    }
  }, [documentText]);

  const analyzeLexical = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;

    setIsLoading(true);
    setError(null);

    try {
      console.log('Layer 1: Analyzing lexical patterns...');

      // Run lexical analysis
      const analysisResult = await lexicalLayerApi.analyze(documentText);
      console.log('Layer 1 result:', analysisResult);

      setResult(analysisResult);

      if (onComplete) {
        onComplete(analysisResult);
      }
    } catch (err: unknown) {
      console.error('Lexical analysis failed:', err);
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

  const handleIssueClick = useCallback((index: number) => {
    setExpandedIssueIndex(prev => prev === index ? null : index);
  }, []);

  const handleCopyReplacement = useCallback((word: string, replacement: string) => {
    navigator.clipboard.writeText(replacement).then(() => {
      setCopiedWord(word);
      setTimeout(() => setCopiedWord(null), 2000);
    });
  }, []);

  const handleFinish = useCallback(() => {
    // Navigate to summary or next step
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/summary/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

  const handleBack = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/layer-sentence/${documentId}?mode=${mode}${sessionParam}`);
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
              返回句子层
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
            <div className="p-2 rounded-lg bg-pink-100 text-pink-600 mr-3">
              <Type className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Layer 1: 词汇层分析
              </h1>
              <p className="text-gray-600 mt-1">
                Lexical Layer Analysis
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

        {/* 5-Layer Progress - Complete with Step 1.0 */}
        {/* 5层进度完成（含Step 1.0）*/}
        <div className="mt-4 flex items-center text-sm text-gray-500 flex-wrap gap-y-1">
          <button
            onClick={() => navigate(`/flow/term-lock/${documentId}?mode=${mode}${sessionId ? `&session=${sessionId}` : ''}`)}
            className="text-green-600 hover:text-indigo-600 hover:underline transition-colors"
          >
            Step 1.0 ✓
          </button>
          <span className="mx-2">→</span>
          <span className="text-green-600">Layer 5 ✓</span>
          <span className="mx-2">→</span>
          <span className="text-green-600">Layer 4 ✓</span>
          <span className="mx-2">→</span>
          <span className="text-green-600">Layer 3 ✓</span>
          <span className="mx-2">→</span>
          <span className="text-green-600">Layer 2 ✓</span>
          <span className="mx-2">→</span>
          <span className="font-medium text-pink-600 bg-pink-50 px-2 py-1 rounded">
            Layer 1 词汇
          </span>
        </div>

        {/* Step tabs */}
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            onClick={() => setCurrentStep('5.1')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '5.1' ? 'bg-pink-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <Fingerprint className="w-4 h-4 mr-1" />
            5.1 指纹词
          </button>
          <button
            onClick={() => setCurrentStep('5.2')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '5.2' ? 'bg-pink-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <Link className="w-4 h-4 mr-1" />
            5.2 连接词
          </button>
          <button
            onClick={() => setCurrentStep('5.3')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '5.3' ? 'bg-pink-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <AlertTriangle className="w-4 h-4 mr-1" />
            5.3 词级风险
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
                  词汇层风险分数 / Lexical Layer Risk Score
                </h3>
                <p className="text-sm text-gray-500">
                  分析指纹词、连接词和词级风险
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

            <div className="mt-4 grid grid-cols-3 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-pink-600">
                  {result.fingerprintDensity?.toFixed(1) || 0}
                </p>
                <p className="text-sm text-gray-600">指纹密度</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-pink-600">
                  {(result.connectorRatio * 100)?.toFixed(0) || 0}%
                </p>
                <p className="text-sm text-gray-600">连接词比</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-pink-600">
                  {Object.keys(result.replacementSuggestions || {}).length}
                </p>
                <p className="text-sm text-gray-600">需替换词</p>
              </div>
            </div>
          </div>

          {/* Step 5.1: Fingerprint Detection */}
          {currentStep === '5.1' && result.fingerprintMatches && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Fingerprint className="w-5 h-5 mr-2 text-pink-600" />
                指纹词检测 / Fingerprint Detection
              </h3>

              {/* Type A: Dead Giveaways */}
              {result.fingerprintMatches.typeA && result.fingerprintMatches.typeA.length > 0 && (
                <div className="mb-4">
                  <h4 className="font-medium text-red-700 mb-2 flex items-center">
                    <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                    Type A: 致命指纹词 (+40 风险)
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {result.fingerprintMatches.typeA.map((match, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm"
                      >
                        {match.word} ({match.count})
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Type B: Academic Clichés */}
              {result.fingerprintMatches.typeB && result.fingerprintMatches.typeB.length > 0 && (
                <div className="mb-4">
                  <h4 className="font-medium text-yellow-700 mb-2 flex items-center">
                    <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
                    Type B: 学术套话 (+5-25 风险)
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {result.fingerprintMatches.typeB.map((match, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm"
                      >
                        {match.word} ({match.count})
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Phrases */}
              {result.fingerprintMatches.phrases && result.fingerprintMatches.phrases.length > 0 && (
                <div>
                  <h4 className="font-medium text-purple-700 mb-2 flex items-center">
                    <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                    AI短语模式
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {result.fingerprintMatches.phrases.map((match, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm"
                      >
                        {match.phrase} ({match.count})
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {(!result.fingerprintMatches.typeA?.length &&
                !result.fingerprintMatches.typeB?.length &&
                !result.fingerprintMatches.phrases?.length) && (
                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="text-green-800">未检测到明显的AI指纹词</p>
                </div>
              )}
            </div>
          )}

          {/* Step 5.2: Connector Analysis */}
          {currentStep === '5.2' && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Link className="w-5 h-5 mr-2 text-pink-600" />
                连接词分析 / Connector Analysis
              </h3>

              <div className="p-4 bg-gray-50 rounded-lg mb-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">句首连接词比例</span>
                  <span className={clsx(
                    'text-xl font-bold',
                    (result.connectorRatio || 0) > 0.3 && 'text-red-600',
                    (result.connectorRatio || 0) <= 0.3 && 'text-green-600'
                  )}>
                    {((result.connectorRatio || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                {(result.connectorRatio || 0) > 0.3 && (
                  <p className="text-sm text-red-600 mt-2">
                    连接词使用过多是AI生成的典型特征，建议减少显式连接词
                  </p>
                )}
              </div>

              {result.connectorMatches && result.connectorMatches.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-gray-700 mb-2">检测到的连接词:</h4>
                  {result.connectorMatches.map((match, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-gray-50 rounded-lg flex items-center justify-between"
                    >
                      <span className="font-medium text-gray-800">{match.connector}</span>
                      <span className="text-sm px-2 py-1 bg-pink-100 text-pink-700 rounded">
                        出现 {match.count} 次
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Step 5.3: Word-Level Risk & Replacements */}
          {currentStep === '5.3' && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2 text-pink-600" />
                词级风险与替换建议 / Word-Level Risk & Replacements
              </h3>

              {result.replacementSuggestions && Object.keys(result.replacementSuggestions).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(result.replacementSuggestions).map(([word, replacements], idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-red-700 line-through">{word}</span>
                        <span className="text-xs text-gray-500">建议替换为:</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {(replacements as string[]).slice(0, 5).map((replacement, rIdx) => (
                          <button
                            key={rIdx}
                            onClick={() => handleCopyReplacement(word, replacement)}
                            className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm hover:bg-green-200 flex items-center"
                          >
                            {replacement}
                            {copiedWord === word ? (
                              <Check className="w-3 h-3 ml-1" />
                            ) : (
                              <Copy className="w-3 h-3 ml-1 opacity-50" />
                            )}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="text-green-800">没有需要替换的高风险词</p>
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
                返回句子层
              </Button>
              <Button onClick={handleFinish}>
                完成分析
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
