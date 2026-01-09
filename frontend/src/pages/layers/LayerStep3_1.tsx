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
  FileText,
  RefreshCw,
  Tag,
  BookOpen,
  Beaker,
  BarChart3,
  MessageSquare,
  CheckSquare,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { paragraphLayerApi, ParagraphAnalysisResponse } from '../../services/analysisApi';

/**
 * Layer Step 3.1 - Paragraph Role Detection
 * 步骤 3.1 - 段落角色识别
 *
 * Identifies the functional role of each paragraph:
 * - Introduction, background, methodology, results, discussion, conclusion
 * - Transition paragraphs
 * - Detects role distribution anomalies
 *
 * 识别每个段落的功能角色：
 * - 引言、背景、方法、结果、讨论、结论
 * - 过渡段落
 * - 检测角色分布异常
 */

// Paragraph role configuration
// 段落角色配置
const PARAGRAPH_ROLE_CONFIG: Record<string, { label: string; labelZh: string; icon: typeof BookOpen; color: string }> = {
  introduction: { label: 'Introduction', labelZh: '引言', icon: BookOpen, color: 'blue' },
  background: { label: 'Background', labelZh: '背景', icon: FileText, color: 'purple' },
  methodology: { label: 'Methodology', labelZh: '方法', icon: Beaker, color: 'green' },
  results: { label: 'Results', labelZh: '结果', icon: BarChart3, color: 'orange' },
  discussion: { label: 'Discussion', labelZh: '讨论', icon: MessageSquare, color: 'yellow' },
  conclusion: { label: 'Conclusion', labelZh: '结论', icon: CheckSquare, color: 'red' },
  transition: { label: 'Transition', labelZh: '过渡', icon: ArrowRight, color: 'cyan' },
  body: { label: 'Body', labelZh: '正文', icon: FileText, color: 'gray' },
};

interface LayerStep3_1Props {
  documentIdProp?: string;
  onComplete?: (result: ParagraphAnalysisResponse) => void;
  showNavigation?: boolean;
  sectionContext?: Record<string, unknown>;
}

export default function LayerStep3_1({
  documentIdProp,
  onComplete,
  showNavigation = true,
  sectionContext,
}: LayerStep3_1Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // Update session step
  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer3-step3-1').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<ParagraphAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

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

  // Run analysis when document is loaded
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
      const analysisResult = await paragraphLayerApi.analyzeRole(documentText, sectionContext);
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
    navigate(`/flow/layer3-step3-2/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-0/${documentId}?${params.toString()}`);
  };

  const getRoleConfig = (role: string) => {
    return PARAGRAPH_ROLE_CONFIG[role.toLowerCase()] || PARAGRAPH_ROLE_CONFIG.body;
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
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
            <div className="p-2 bg-purple-100 rounded-lg">
              <Tag className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3.1: Paragraph Role Detection
              </h2>
              <p className="text-sm text-gray-500">
                步骤 3.1: 段落角色识别
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
          Identifies the functional role of each paragraph and detects role distribution anomalies.
          <br />
          <span className="text-gray-500">
            识别每个段落的功能角色并检测角色分布异常。
          </span>
        </p>

        {/* Risk Score */}
        {result && (
          <div className="flex items-center gap-4 mt-4">
            <div className={clsx('px-4 py-2 rounded-lg', getRiskColor(result.riskLevel))}>
              <span className="font-semibold">Risk: {result.riskScore}/100</span>
              <span className="ml-2 text-sm">({result.riskLevel})</span>
            </div>
          </div>
        )}

        {/* Role Distribution */}
        {result && result.roleDistribution && (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Role Distribution / 角色分布:</h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(result.roleDistribution).map(([role, count]) => {
                const config = getRoleConfig(role);
                return (
                  <div
                    key={role}
                    className={clsx(
                      'px-3 py-1.5 rounded-full text-sm flex items-center gap-2',
                      `bg-${config.color}-100 text-${config.color}-700`
                    )}
                    style={{
                      backgroundColor: `var(--${config.color}-100, #e0e7ff)`,
                      color: `var(--${config.color}-700, #4338ca)`,
                    }}
                  >
                    <span>{config.label}</span>
                    <span className="font-bold">{count as number}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Paragraph Roles */}
      {result && result.paragraphDetails && result.paragraphDetails.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-purple-600" />
            Paragraph Roles / 段落角色
          </h3>

          <div className="space-y-3">
            {result.paragraphDetails.map((para, index) => {
              const config = getRoleConfig(para.role);
              const IconComponent = config.icon;
              return (
                <div
                  key={index}
                  className="border rounded-lg overflow-hidden hover:border-purple-300 transition-colors"
                >
                  <div
                    className="flex items-center justify-between p-4 cursor-pointer bg-gray-50 hover:bg-gray-100"
                    onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}
                  >
                    <div className="flex items-center gap-4">
                      <span className="w-8 h-8 flex items-center justify-center bg-purple-100 text-purple-600 rounded-full font-medium">
                        {index + 1}
                      </span>
                      <div className="flex items-center gap-2">
                        <div className={clsx(
                          'px-2 py-1 rounded flex items-center gap-1',
                          `bg-${config.color}-100`
                        )}>
                          <IconComponent className="w-4 h-4" />
                          <span className="text-sm font-medium">{config.label}</span>
                        </div>
                        <span className="text-gray-400">|</span>
                        <span className="text-sm text-gray-500">{config.labelZh}</span>
                      </div>
                    </div>
                    {expandedIndex === index ? (
                      <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </div>

                  {expandedIndex === index && (
                    <div className="p-4 border-t bg-white">
                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div className="text-center p-3 bg-gray-50 rounded">
                          <div className="text-lg font-semibold text-gray-700">{para.coherenceScore?.toFixed(2) || 'N/A'}</div>
                          <div className="text-xs text-gray-500">Coherence Score / 连贯分数</div>
                        </div>
                        <div className="text-center p-3 bg-gray-50 rounded">
                          <div className="text-lg font-semibold text-gray-700">{para.anchorCount || 0}</div>
                          <div className="text-xs text-gray-500">Anchor Count / 锚点数</div>
                        </div>
                      </div>
                      {para.issues && para.issues.length > 0 && (
                        <div className="mt-2">
                          <h4 className="text-sm font-medium text-gray-700 mb-1">Issues:</h4>
                          <ul className="text-sm text-red-600">
                            {para.issues.map((issue, i) => (
                              <li key={i}>• {issue}</li>
                            ))}
                          </ul>
                        </div>
                      )}
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
            Detected Issues / 检测到的问题
          </h3>
          <div className="space-y-3">
            {result.issues.map((issue, index) => (
              <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="font-medium text-red-700">{issue.description}</div>
                {issue.descriptionZh && (
                  <div className="text-sm text-red-600 mt-1">{issue.descriptionZh}</div>
                )}
                {issue.suggestion && (
                  <div className="text-sm text-gray-600 mt-2">
                    <strong>Suggestion:</strong> {issue.suggestion}
                  </div>
                )}
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
            Previous: Step 3.0
          </Button>
          <Button onClick={goToNextStep} disabled={!result} className="flex items-center gap-2">
            Next: Step 3.2 Coherence
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
