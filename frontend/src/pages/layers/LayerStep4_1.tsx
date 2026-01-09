import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  BarChart3,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  Sparkles,
  Lightbulb,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { sentenceLayerApi, PatternAnalysisResponse, SyntacticVoidMatch } from '../../services/analysisApi';

/**
 * Layer Step 4.1 - Sentence Pattern Analysis
 * 步骤 4.1 - 句式结构分析
 *
 * Analyzes sentence patterns across the document:
 * - Sentence type distribution (simple/compound/complex/compound_complex)
 * - Sentence opener analysis (repetition, subject-first ratio)
 * - Voice distribution (active/passive)
 * - Identifies high-risk paragraphs for processing
 *
 * 分析全文的句式模式：
 * - 句式类型分布
 * - 句首词分析
 * - 语态分布
 * - 识别需要处理的高风险段落
 */

interface LayerStep4_1Props {
  documentIdProp?: string;
  onComplete?: (result: PatternAnalysisResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep4_1({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep4_1Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer2-step4-1').catch(console.error);
    }
  }, [sessionId]);

  const [result, setResult] = useState<PatternAnalysisResponse | null>(null);
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
      const analysisResult = await sentenceLayerApi.analyzePatterns(documentText, undefined, sessionId || undefined);
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
    navigate(`/flow/layer2-step4-console/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer2-step4-0/${documentId}?${params.toString()}`);
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
      case 'simple': return 'bg-blue-500';
      case 'compound': return 'bg-green-500';
      case 'complex': return 'bg-purple-500';
      case 'compound_complex': return 'bg-orange-500';
      default: return 'bg-gray-500';
    }
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
            <div className="p-2 bg-purple-100 rounded-lg">
              <BarChart3 className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 4.1: Sentence Pattern Analysis
              </h2>
              <p className="text-sm text-gray-500">
                步骤 4.1: 句式结构分析
              </p>
            </div>
          </div>
          {isAnalyzing && (
            <div className="flex items-center gap-2 text-purple-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing... / 分析中...</span>
            </div>
          )}
        </div>

        <p className="text-gray-600 mb-4">
          Analyzes sentence type distribution, opener repetition, and voice balance across the document.
          <br />
          <span className="text-gray-500">
            分析全文的句式类型分布、句首重复率和语态平衡。
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
                {result.openerAnalysis?.repetitionRate ? `${(result.openerAnalysis.repetitionRate * 100).toFixed(0)}%` : 'N/A'}
              </div>
              <div className="text-sm text-blue-600">Opener Repeat / 句首重复</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-700">
                {result.voiceDistribution?.passive || 0}
              </div>
              <div className="text-sm text-purple-600">Passive / 被动句</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-orange-700">
                {result.highRiskParagraphs?.length || 0}
              </div>
              <div className="text-sm text-orange-600">High Risk Para / 高风险段</div>
            </div>
          </div>
        )}
      </div>

      {/* Type Distribution Chart */}
      {result && result.typeDistribution && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-600" />
            Type Distribution / 句式类型分布
          </h3>

          <div className="space-y-4">
            {Object.entries(result.typeDistribution).map(([type, stats]) => {
              const percentage = stats.percentage * 100;
              const isRisk = stats.isRisk;
              const threshold = stats.threshold * 100;

              return (
                <div key={type} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={clsx(
                        'w-3 h-3 rounded-full',
                        getTypeColor(type)
                      )} />
                      <span className="text-sm font-medium text-gray-700 capitalize">
                        {type.replace('_', ' ')}
                      </span>
                      {isRisk && (
                        <AlertTriangle className="w-4 h-4 text-yellow-500" />
                      )}
                    </div>
                    <span className="text-sm text-gray-600">
                      {stats.count} ({percentage.toFixed(0)}%)
                      <span className="text-gray-400 ml-1">
                        threshold: {threshold}%
                      </span>
                    </span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={clsx(
                        'h-full rounded-full transition-all',
                        getTypeColor(type),
                        isRisk ? 'opacity-100' : 'opacity-70'
                      )}
                      style={{ width: `${Math.min(percentage, 100)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Opener Analysis */}
      {result && result.openerAnalysis && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Opener Analysis / 句首词分析
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Top Repeated Openers */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Top Repeated Openers / 最常用句首:</h4>
              <div className="flex flex-wrap gap-2">
                {result.openerAnalysis.topRepeated.map((opener, i) => (
                  <span
                    key={i}
                    className={clsx(
                      'px-3 py-1 rounded-full text-sm',
                      i === 0 ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'
                    )}
                  >
                    "{opener}" ({result.openerAnalysis.openerCounts[opener] || 0}x)
                  </span>
                ))}
              </div>
            </div>

            {/* Metrics */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Repetition Rate / 重复率:</span>
                <span className={clsx(
                  'font-medium',
                  result.openerAnalysis.repetitionRate > 0.3 ? 'text-red-600' : 'text-green-600'
                )}>
                  {(result.openerAnalysis.repetitionRate * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Subject-First Rate / 主语开头率:</span>
                <span className={clsx(
                  'font-medium',
                  result.openerAnalysis.subjectOpeningRate > 0.8 ? 'text-red-600' : 'text-green-600'
                )}>
                  {(result.openerAnalysis.subjectOpeningRate * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          {/* Opener Issues */}
          {result.openerAnalysis.issues.length > 0 && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h4 className="text-sm font-medium text-yellow-800 mb-2">Issues:</h4>
              <ul className="space-y-1">
                {result.openerAnalysis.issues.map((issue, i) => (
                  <li key={i} className="text-sm text-yellow-700 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* High Risk Paragraphs */}
      {result && result.highRiskParagraphs && result.highRiskParagraphs.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            High Risk Paragraphs / 高风险段落
          </h3>

          <p className="text-sm text-gray-600 mb-4">
            These paragraphs need processing in the next steps.
            <span className="text-gray-500 ml-1">这些段落需要在后续步骤中处理。</span>
          </p>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-2 text-left">Para</th>
                  <th className="px-4 py-2 text-center">Risk</th>
                  <th className="px-4 py-2 text-center">Simple %</th>
                  <th className="px-4 py-2 text-center">Length CV</th>
                  <th className="px-4 py-2 text-center">Opener Rep</th>
                  <th className="px-4 py-2 text-center">Sentences</th>
                </tr>
              </thead>
              <tbody>
                {result.highRiskParagraphs.map((para) => (
                  <tr key={para.paragraphIndex} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className="w-6 h-6 inline-flex items-center justify-center bg-orange-200 text-orange-700 rounded-full text-xs font-medium">
                        {para.paragraphIndex + 1}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={clsx(
                        'px-2 py-0.5 rounded text-xs font-medium',
                        getRiskColor(para.riskLevel)
                      )}>
                        {para.riskScore}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={para.simpleRatio > 0.6 ? 'text-red-600 font-medium' : ''}>
                        {(para.simpleRatio * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={para.lengthCv < 0.25 ? 'text-red-600 font-medium' : ''}>
                        {para.lengthCv.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={para.openerRepetition > 0.3 ? 'text-red-600 font-medium' : ''}>
                        {(para.openerRepetition * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">{para.sentenceCount}</td>
                  </tr>
                ))}
              </tbody>
            </table>
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
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Syntactic Void Detection - NEW */}
      {/* 句法空洞检测 - 新增 */}
      {result && result.syntacticVoids && result.syntacticVoids.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-600" />
            Syntactic Voids Detected / 检测到的句法空洞
            {result.hasCriticalVoid && (
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
                Critical / 严重
              </span>
            )}
          </h3>

          {/* Void Score Summary */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className={clsx(
              'rounded-lg p-4',
              (result.voidScore || 0) > 50 ? 'bg-red-50' : (result.voidScore || 0) > 30 ? 'bg-yellow-50' : 'bg-green-50'
            )}>
              <div className={clsx(
                'text-2xl font-bold',
                (result.voidScore || 0) > 50 ? 'text-red-700' : (result.voidScore || 0) > 30 ? 'text-yellow-700' : 'text-green-700'
              )}>
                {result.voidScore || 0}
              </div>
              <div className="text-sm text-gray-600">Void Score / 空洞分数</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-700">
                {((result.voidDensity || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-purple-600">Void Density / 空洞密度</div>
            </div>
            <div className="bg-amber-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-amber-700">
                {result.syntacticVoids.length}
              </div>
              <div className="text-sm text-amber-600">Patterns Found / 发现模式</div>
            </div>
          </div>

          {/* Void Pattern List */}
          <div className="space-y-3">
            {result.syntacticVoids.slice(0, 10).map((voidMatch: SyntacticVoidMatch, index: number) => (
              <div
                key={index}
                className={clsx(
                  'p-4 rounded-lg border',
                  voidMatch.severity === 'high' ? 'bg-red-50 border-red-200' :
                  voidMatch.severity === 'medium' ? 'bg-yellow-50 border-yellow-200' :
                  'bg-gray-50 border-gray-200'
                )}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={clsx(
                      'px-2 py-0.5 rounded text-xs font-medium',
                      voidMatch.severity === 'high' ? 'bg-red-200 text-red-800' :
                      voidMatch.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                      'bg-gray-200 text-gray-800'
                    )}>
                      {voidMatch.patternType.replace(/_/g, ' ')}
                    </span>
                    <span className={clsx(
                      'text-xs',
                      voidMatch.severity === 'high' ? 'text-red-600' : 'text-gray-500'
                    )}>
                      {voidMatch.severity}
                    </span>
                  </div>
                </div>
                <div className="font-mono text-sm bg-white p-2 rounded border mb-2">
                  <span className="text-red-600 underline decoration-wavy decoration-red-300">
                    "{voidMatch.matchedText}"
                  </span>
                </div>
                {voidMatch.suggestion && (
                  <div className="flex items-start gap-2 text-sm">
                    <Lightbulb className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="text-gray-700">{voidMatch.suggestion}</span>
                      {voidMatch.suggestionZh && (
                        <span className="text-gray-500 ml-1">/ {voidMatch.suggestionZh}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            {result.syntacticVoids.length > 10 && (
              <p className="text-sm text-gray-500 text-center">
                ... and {result.syntacticVoids.length - 10} more patterns / 还有 {result.syntacticVoids.length - 10} 个模式
              </p>
            )}
          </div>

          <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm text-amber-800">
              <strong>What are Syntactic Voids?</strong> These are "flowery but semantically empty" phrases typical of AI-generated text.
              They sound impressive but lack concrete meaning.
            </p>
            <p className="text-sm text-amber-700 mt-1">
              <strong>什么是句法空洞？</strong> 这些是AI生成文本的典型特征——"华丽但语义空洞"的短语。
              听起来很高级，但缺乏具体含义。
            </p>
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
            Previous: Step 4.0
          </Button>
          <Button onClick={goToNextStep} disabled={!result} className="flex items-center gap-2">
            Next: Processing Console
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
