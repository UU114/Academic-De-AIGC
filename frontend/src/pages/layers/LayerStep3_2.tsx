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
  Link2,
  FileText,
  RefreshCw,
  Users,
  GitBranch,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { paragraphLayerApi, ParagraphAnalysisResponse } from '../../services/analysisApi';

/**
 * Layer Step 3.2 - Paragraph Internal Coherence
 * 步骤 3.2 - 段落内部连贯性
 *
 * Analyzes sentence relationships within paragraphs:
 * - Subject diversity (避免重复主语)
 * - Logic structure (线性 vs 层次结构)
 * - Connector density (连接词密度)
 * - First-person usage (第一人称使用)
 *
 * 分析段落内句子关系：
 * - 主语多样性
 * - 逻辑结构
 * - 连接词密度
 * - 第一人称使用率
 */

interface LayerStep3_2Props {
  documentIdProp?: string;
  onComplete?: (result: ParagraphAnalysisResponse) => void;
  showNavigation?: boolean;
  sectionContext?: Record<string, unknown>;
}

export default function LayerStep3_2({
  documentIdProp,
  onComplete,
  showNavigation = true,
  sectionContext,
}: LayerStep3_2Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer3-step3-2').catch(console.error);
    }
  }, [sessionId]);

  const [result, setResult] = useState<ParagraphAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

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
      const analysisResult = await paragraphLayerApi.analyzeCoherence(documentText, sectionContext);
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
    navigate(`/flow/layer3-step3-3/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-1/${documentId}?${params.toString()}`);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
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
            <div className="p-2 bg-green-100 rounded-lg">
              <Link2 className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3.2: Internal Coherence Analysis
              </h2>
              <p className="text-sm text-gray-500">
                步骤 3.2: 段落内部连贯性分析
              </p>
            </div>
          </div>
          {isAnalyzing && (
            <div className="flex items-center gap-2 text-green-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing... / 分析中...</span>
            </div>
          )}
        </div>

        <p className="text-gray-600 mb-4">
          Analyzes logical relationships between sentences within each paragraph. Detects AI-like patterns such as linear structure, subject repetition, and connector stacking.
          <br />
          <span className="text-gray-500">
            分析每个段落内句子之间的逻辑关系。检测AI式模式如线性结构、主语重复和连接词堆砌。
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
                {result.coherenceScore?.toFixed(1) || 'N/A'}
              </div>
              <div className="text-sm text-blue-600">Coherence / 连贯性</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-700">
                {result.paragraphCount || 0}
              </div>
              <div className="text-sm text-purple-600">Paragraphs / 段落数</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-orange-700">
                {result.issues?.length || 0}
              </div>
              <div className="text-sm text-orange-600">Issues / 问题数</div>
            </div>
          </div>
        )}
      </div>

      {/* Paragraph Coherence Details */}
      {result && result.paragraphDetails && result.paragraphDetails.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-green-600" />
            Paragraph Coherence Details / 段落连贯性详情
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-2 text-left">Para</th>
                  <th className="px-4 py-2 text-left">Role / 角色</th>
                  <th className="px-4 py-2 text-center">Coherence / 连贯</th>
                  <th className="px-4 py-2 text-center">Length CV</th>
                  <th className="px-4 py-2 text-center">Issues</th>
                  <th className="px-4 py-2 text-center">Status</th>
                </tr>
              </thead>
              <tbody>
                {result.paragraphDetails.map((para, index) => (
                  <tr
                    key={index}
                    className={clsx(
                      'border-t hover:bg-gray-50 cursor-pointer',
                      expandedIndex === index && 'bg-blue-50'
                    )}
                    onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}
                  >
                    <td className="px-4 py-3">
                      <span className="w-6 h-6 inline-flex items-center justify-center bg-gray-200 rounded-full text-xs font-medium">
                        {index + 1}
                      </span>
                    </td>
                    <td className="px-4 py-3">{para.role || 'body'}</td>
                    <td className={clsx('px-4 py-3 text-center font-medium', getScoreColor((para.coherenceScore || 0) * 100))}>
                      {((para.coherenceScore || 0) * 100).toFixed(0)}%
                    </td>
                    <td className={clsx(
                      'px-4 py-3 text-center',
                      (para.sentenceLengthCv || 0) < 0.25 ? 'text-red-600' : 'text-green-600'
                    )}>
                      {(para.sentenceLengthCv || 0).toFixed(2)}
                      {(para.sentenceLengthCv || 0) < 0.25 && (
                        <span className="ml-1 text-xs">⚠️</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {para.issues?.length || 0}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {!para.issues || para.issues.length === 0 ? (
                        <CheckCircle className="w-4 h-4 text-green-500 inline" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-yellow-500 inline" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {expandedIndex !== null && result.paragraphDetails[expandedIndex] && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-medium text-blue-800 mb-2">
                Paragraph {expandedIndex + 1} Details
              </h4>
              {result.paragraphDetails[expandedIndex].issues && result.paragraphDetails[expandedIndex].issues.length > 0 ? (
                <ul className="space-y-1">
                  {result.paragraphDetails[expandedIndex].issues.map((issue, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-blue-700">
                      <AlertCircle className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                      <span>{issue}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-green-700">No issues detected in this paragraph.</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Detected Issues */}
      {result && result.issues && result.issues.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            Coherence Issues / 连贯性问题
          </h3>
          <div className="space-y-3">
            {result.issues.map((issue, index) => (
              <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-red-700">{issue.description}</div>
                    {issue.descriptionZh && (
                      <div className="text-sm text-red-600 mt-1">{issue.descriptionZh}</div>
                    )}
                    {issue.suggestion && (
                      <div className="text-sm text-gray-600 mt-2 bg-white p-2 rounded">
                        <strong>💡 Suggestion:</strong> {issue.suggestion}
                      </div>
                    )}
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
            Previous: Step 3.1
          </Button>
          <Button onClick={goToNextStep} disabled={!result} className="flex items-center gap-2">
            Next: Step 3.3 Anchor Density
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
