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
  AlertTriangle,
  BarChart2,
  RefreshCw,
  Scale,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { documentLayerApi, DocumentAnalysisResponse, DetectionIssue } from '../../services/analysisApi';

/**
 * Layer Step 1.2 - Section Uniformity Detection
 * 步骤 1.2 - 章节均匀性检测
 *
 * Detects (Merged Group 1):
 * - A: Section Symmetry (章节对称结构)
 * - D: Uniform Paragraph Count per Section (章节均匀段落数量)
 * - C: Uniform Section Length (章节均匀长度)
 *
 * Priority: ★★★★☆ (Depends on 1.1 section boundaries)
 * 优先级: ★★★★☆ (依赖1.1的章节边界)
 *
 * Part of the 5-layer detection architecture - Layer 5 Sub-steps.
 * 5层检测架构的一部分 - 第5层子步骤。
 */

interface SectionUniformityData {
  index: number;
  role: string;
  title?: string;
  paragraphCount: number;
  wordCount: number;
}

interface UniformityMetrics {
  // Paragraph count uniformity
  paragraphCountMean: number;
  paragraphCountCV: number;
  paragraphCountIsUniform: boolean;
  // Word count uniformity
  wordCountMean: number;
  wordCountCV: number;
  wordCountIsUniform: boolean;
  // Overall symmetry
  isSymmetric: boolean;
  symmetryScore: number;
}

interface LayerStep1_2Props {
  documentIdProp?: string;
  onComplete?: (result: DocumentAnalysisResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep1_2({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep1_2Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // Update session step on mount
  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer5-step1-2').catch(console.error);
    }
  }, [sessionId]);

  // Analysis state
  const [result, setResult] = useState<DocumentAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');

  // Uniformity data
  const [sections, setSections] = useState<SectionUniformityData[]>([]);
  const [metrics, setMetrics] = useState<UniformityMetrics | null>(null);
  const [uniformityIssues, setUniformityIssues] = useState<DetectionIssue[]>([]);
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

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

  // Calculate uniformity metrics from sections
  const calculateMetrics = (sectionData: SectionUniformityData[]): UniformityMetrics => {
    if (sectionData.length < 2) {
      return {
        paragraphCountMean: sectionData[0]?.paragraphCount || 0,
        paragraphCountCV: 0,
        paragraphCountIsUniform: false,
        wordCountMean: sectionData[0]?.wordCount || 0,
        wordCountCV: 0,
        wordCountIsUniform: false,
        isSymmetric: false,
        symmetryScore: 0,
      };
    }

    // Calculate paragraph count stats
    const paraCountArray = sectionData.map(s => s.paragraphCount);
    const paraMean = paraCountArray.reduce((a, b) => a + b, 0) / paraCountArray.length;
    const paraStd = Math.sqrt(
      paraCountArray.reduce((sum, val) => sum + Math.pow(val - paraMean, 2), 0) / paraCountArray.length
    );
    const paraCV = paraMean > 0 ? paraStd / paraMean : 0;

    // Calculate word count stats
    const wordCountArray = sectionData.map(s => s.wordCount);
    const wordMean = wordCountArray.reduce((a, b) => a + b, 0) / wordCountArray.length;
    const wordStd = Math.sqrt(
      wordCountArray.reduce((sum, val) => sum + Math.pow(val - wordMean, 2), 0) / wordCountArray.length
    );
    const wordCV = wordMean > 0 ? wordStd / wordMean : 0;

    // Determine uniformity (CV < 0.3 is considered too uniform / AI-like)
    const paraIsUniform = paraCV < 0.3;
    const wordIsUniform = wordCV < 0.3;

    // Calculate symmetry score (0-100)
    // Lower CV = higher symmetry = more AI-like
    const symmetryScore = Math.round((1 - Math.min(paraCV + wordCV, 2) / 2) * 100);
    const isSymmetric = symmetryScore > 70;

    return {
      paragraphCountMean: paraMean,
      paragraphCountCV: paraCV,
      paragraphCountIsUniform: paraIsUniform,
      wordCountMean: wordMean,
      wordCountCV: wordCV,
      wordCountIsUniform: wordIsUniform,
      isSymmetric,
      symmetryScore,
    };
  };

  const runAnalysis = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;
    setIsAnalyzing(true);
    setError(null);

    try {
      const analysisResult = await documentLayerApi.analyze(documentText);
      setResult(analysisResult);

      // Extract sections
      if (analysisResult.sections) {
        setSections(analysisResult.sections);
        // Calculate uniformity metrics
        const calculatedMetrics = calculateMetrics(analysisResult.sections);
        setMetrics(calculatedMetrics);
      }

      // Filter uniformity-related issues
      const uniformityRelatedIssues = analysisResult.issues.filter(
        (issue) =>
          issue.type.includes('symmetry') ||
          issue.type.includes('uniform') ||
          issue.type.includes('length') ||
          issue.type.includes('balance')
      );
      setUniformityIssues(uniformityRelatedIssues);

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
    navigate(`/flow/layer5-step1-1/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer5-step1-3/${documentId}?${params.toString()}`);
  };

  const toggleIssue = (index: number) => {
    setExpandedIssueIndex(expandedIssueIndex === index ? null : index);
  };

  // Get bar width for visualization
  const getBarWidth = (value: number, max: number) => {
    return `${Math.min((value / max) * 100, 100)}%`;
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

  // Find max values for visualization
  const maxParagraphs = Math.max(...sections.map(s => s.paragraphCount), 1);
  const maxWords = Math.max(...sections.map(s => s.wordCount), 1);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Layers className="w-4 h-4" />
          <span>Layer 5 / 第5层</span>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Step 1.2 章节均匀性</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Section Uniformity Detection
        </h1>
        <p className="text-gray-600 mt-1">
          章节均匀性检测 - 检测章节对称结构、均匀段落数、均匀长度
        </p>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing uniformity... / 分析均匀性中...</p>
              <p className="text-blue-600 text-sm">Calculating section symmetry and balance</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && metrics && (
        <>
          {/* Uniformity Metrics Summary */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Symmetry Score */}
            <div className={clsx(
              'p-4 rounded-lg border',
              metrics.isSymmetric ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <Scale className={clsx('w-5 h-5', metrics.isSymmetric ? 'text-red-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Symmetry Score / 对称分数</span>
              </div>
              <div className={clsx(
                'text-3xl font-bold',
                metrics.isSymmetric ? 'text-red-600' : 'text-green-600'
              )}>
                {metrics.symmetryScore}%
              </div>
              <p className={clsx(
                'text-sm mt-1',
                metrics.isSymmetric ? 'text-red-600' : 'text-green-600'
              )}>
                {metrics.isSymmetric ? 'Too symmetric (AI-like) / 过于对称（AI风格）' : 'Natural asymmetry / 自然非对称'}
              </p>
            </div>

            {/* Paragraph Count CV */}
            <div className={clsx(
              'p-4 rounded-lg border',
              metrics.paragraphCountIsUniform ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <BarChart2 className={clsx('w-5 h-5', metrics.paragraphCountIsUniform ? 'text-yellow-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Paragraph Count CV</span>
              </div>
              <div className={clsx(
                'text-3xl font-bold',
                metrics.paragraphCountIsUniform ? 'text-yellow-600' : 'text-green-600'
              )}>
                {(metrics.paragraphCountCV * 100).toFixed(1)}%
              </div>
              <p className={clsx(
                'text-sm mt-1',
                metrics.paragraphCountIsUniform ? 'text-yellow-600' : 'text-green-600'
              )}>
                {metrics.paragraphCountIsUniform ? 'Uniform (< 30%) / 均匀' : 'Variable (natural) / 变化（自然）'}
              </p>
            </div>

            {/* Word Count CV */}
            <div className={clsx(
              'p-4 rounded-lg border',
              metrics.wordCountIsUniform ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <BarChart2 className={clsx('w-5 h-5', metrics.wordCountIsUniform ? 'text-yellow-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Word Count CV</span>
              </div>
              <div className={clsx(
                'text-3xl font-bold',
                metrics.wordCountIsUniform ? 'text-yellow-600' : 'text-green-600'
              )}>
                {(metrics.wordCountCV * 100).toFixed(1)}%
              </div>
              <p className={clsx(
                'text-sm mt-1',
                metrics.wordCountIsUniform ? 'text-yellow-600' : 'text-green-600'
              )}>
                {metrics.wordCountIsUniform ? 'Uniform (< 30%) / 均匀' : 'Variable (natural) / 变化（自然）'}
              </p>
            </div>
          </div>

          {/* Risk alert if symmetric */}
          {metrics.isSymmetric && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Symmetric Structure Detected
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：检测到对称结构。各章节的段落数和字数过于均匀。
                  建议合并短章节、拆分长章节或调整段落分布。
                </p>
              </div>
            </div>
          )}

          {/* Section Visualization */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <BarChart2 className="w-5 h-5" />
              Section Distribution / 章节分布
            </h3>
            <div className="bg-white border rounded-lg overflow-hidden">
              <div className="p-4">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 border-b">
                      <th className="pb-2 w-24">Section</th>
                      <th className="pb-2">Paragraphs / 段落数</th>
                      <th className="pb-2">Words / 字数</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sections.map((section, idx) => (
                      <tr key={idx} className="border-b last:border-b-0">
                        <td className="py-3 text-sm font-medium text-gray-900">
                          {section.title || `Section ${idx + 1}`}
                        </td>
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-blue-500 rounded-full transition-all"
                                style={{ width: getBarWidth(section.paragraphCount, maxParagraphs) }}
                              />
                            </div>
                            <span className="text-sm text-gray-600 w-8">{section.paragraphCount}</span>
                          </div>
                        </td>
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-green-500 rounded-full transition-all"
                                style={{ width: getBarWidth(section.wordCount, maxWords) }}
                              />
                            </div>
                            <span className="text-sm text-gray-600 w-12">{section.wordCount}</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="px-4 py-2 bg-gray-50 border-t text-sm text-gray-500">
                Mean paragraphs: {metrics.paragraphCountMean.toFixed(1)} |
                Mean words: {metrics.wordCountMean.toFixed(0)}
              </div>
            </div>
          </div>

          {/* Uniformity Issues */}
          {uniformityIssues.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
                Uniformity Issues / 均匀性问题
                <span className="text-sm font-normal text-gray-500">
                  ({uniformityIssues.length} issues)
                </span>
              </h3>
              <div className="space-y-2">
                {uniformityIssues.map((issue, idx) => {
                  const isExpanded = expandedIssueIndex === idx;
                  return (
                    <div
                      key={idx}
                      className="bg-yellow-50 border border-yellow-200 rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => toggleIssue(idx)}
                        className="w-full px-4 py-3 flex items-center justify-between hover:bg-yellow-100 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <AlertCircle className="w-5 h-5 text-yellow-600" />
                          <p className="font-medium text-yellow-800 text-left">
                            {issue.descriptionZh || issue.description}
                          </p>
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        )}
                      </button>
                      {isExpanded && (
                        <div className="px-4 py-3 border-t border-yellow-200">
                          <div className="space-y-3">
                            {issue.suggestionZh && (
                              <div>
                                <h4 className="text-sm font-medium text-gray-700">
                                  Suggestion / 建议
                                </h4>
                                <p className="text-gray-600 text-sm mt-1">
                                  {issue.suggestionZh}
                                </p>
                              </div>
                            )}
                            <div className="pt-2">
                              <Button variant="primary" size="sm">
                                AI Analysis / AI分析
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* No issues */}
          {!metrics.isSymmetric && uniformityIssues.length === 0 && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">
                  No Uniformity Issues Detected
                </h3>
                <p className="text-green-600 mt-1">
                  未检测到均匀性问题。章节分布看起来是自然的。
                </p>
              </div>
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
            Back: Structure / 上一步：结构
          </Button>
          <Button variant="primary" onClick={handleNext} disabled={isAnalyzing}>
            Next: Logic Pattern / 下一步：逻辑模式
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
