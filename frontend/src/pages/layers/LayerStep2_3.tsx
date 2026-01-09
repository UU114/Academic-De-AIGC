import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  Loader2,
  Layers,
  AlertTriangle,
  RefreshCw,
  GitCompare,
  Grid3X3,
  FileText,
  Zap,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { sectionLayerApi, InternalStructureSimilarityResponse } from '../../services/analysisApi';

/**
 * Layer Step 2.3 - Internal Structure Similarity Detection
 * 步骤 2.3 - 章节内部结构相似性检测
 *
 * This is a NEW core detection feature for Layer 4.
 * 这是第4层新增的核心检测功能。
 *
 * Detects:
 * - R: Internal Structure Similarity (章节内部逻辑结构相似性) - NEW
 * - M: Heading Depth Variance (子标题深度变异)
 * - N: Argument Density (章节内论点密度)
 *
 * AI Pattern: AI tends to use the same internal template for all sections
 * AI模式: AI倾向于为所有章节使用相同的内部模板
 */

// Paragraph function types
// 段落功能类型
const PARAGRAPH_FUNCTIONS = {
  topic_sentence: { label: 'Topic', labelZh: '主题句', color: 'blue' },
  evidence: { label: 'Evidence', labelZh: '证据', color: 'green' },
  analysis: { label: 'Analysis', labelZh: '分析', color: 'purple' },
  transition: { label: 'Transition', labelZh: '过渡', color: 'yellow' },
  mini_conclusion: { label: 'Summary', labelZh: '小结', color: 'red' },
  example: { label: 'Example', labelZh: '举例', color: 'orange' },
};

interface LayerStep2_3Props {
  documentIdProp?: string;
  onComplete?: (result: InternalStructureSimilarityResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep2_3({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep2_3Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer4-step2-3').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<InternalStructureSimilarityResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedSection, setExpandedSection] = useState<number | null>(null);
  const [showAiSuggestion, setShowAiSuggestion] = useState(false);

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

  const runAnalysis = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;
    setIsAnalyzing(true);
    setError(null);

    try {
      // Call actual API
      // 调用实际API
      const analysisResult = await sectionLayerApi.analyzeSimilarity(
        documentText,
        undefined,
        undefined,
        sessionId || undefined
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

  // Navigation
  const handleBack = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer4-step2-2/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer4-step2-4/${documentId}?${params.toString()}`);
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

  const hasHighRisk = result?.riskLevel === 'high';
  const hasSimilarityIssue = (result?.averageSimilarity || 0) > 80;
  const hasHeadingIssue = (result?.headingDepthCv || 0) < 0.1;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Layers className="w-4 h-4" />
          <span>Layer 4 / 第4层</span>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Step 2.3 内部结构</span>
          <span className="ml-2 px-2 py-0.5 bg-orange-100 text-orange-700 rounded text-xs">NEW</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Internal Structure Similarity Detection
        </h1>
        <p className="text-gray-600 mt-1">
          章节内部结构相似性检测 - 比较不同章节的内部逻辑模式是否高度相似（AI模板特征）
        </p>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing internal structures... / 分析内部结构中...</p>
              <p className="text-blue-600 text-sm">Labeling paragraph functions and calculating similarity</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* Summary Stats */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Average Similarity */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasSimilarityIssue ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <GitCompare className={clsx('w-5 h-5', hasSimilarityIssue ? 'text-red-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Avg Similarity / 平均相似度</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasSimilarityIssue ? 'text-red-600' : 'text-green-600'
              )}>
                {result.averageSimilarity}%
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {hasSimilarityIssue ? 'High risk (&gt;80% = AI pattern)' : 'Good diversity (&lt;80%)'}
              </p>
            </div>

            {/* Heading Depth CV */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasHeadingIssue ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <Grid3X3 className={clsx('w-5 h-5', hasHeadingIssue ? 'text-yellow-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Heading Depth CV</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasHeadingIssue ? 'text-yellow-600' : 'text-green-600'
              )}>
                {result.headingDepthCv.toFixed(2)}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {hasHeadingIssue ? 'Too uniform heading depth' : 'Good depth variety'}
              </p>
            </div>

            {/* Argument Density CV */}
            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">Argument Density CV</span>
              </div>
              <div className="text-2xl font-bold text-gray-700">
                {result.argumentDensityCv.toFixed(2)}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Variance in argument count
              </p>
            </div>
          </div>

          {/* High Risk Alert */}
          {hasHighRisk && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Template-Like Internal Structure
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：不同章节的内部逻辑结构高度相似。
                  AI倾向于为所有章节使用相同的"主题句→证据→分析→小结"模板。
                  建议为不同章节采用不同的内部结构。
                </p>
              </div>
            </div>
          )}

          {/* Section Structure Comparison */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <GitCompare className="w-5 h-5 text-blue-600" />
              Section Internal Structure / 章节内部结构对比
            </h3>
            <div className="bg-white border rounded-lg divide-y">
              {result.sectionStructures.map((section) => {
                const isExpanded = expandedSection === section.sectionIndex;
                return (
                  <div key={section.sectionIndex}>
                    <button
                      onClick={() => setExpandedSection(isExpanded ? null : section.sectionIndex)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-8 h-8 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-medium">
                          {section.sectionIndex + 1}
                        </span>
                        <div className="text-left">
                          <span className="font-medium text-gray-900">
                            {section.sectionRole.charAt(0).toUpperCase() + section.sectionRole.slice(1).replace('_', ' ')}
                          </span>
                          <div className="flex gap-1 mt-1">
                            {section.functionSequence.map((func, idx) => {
                              const config = PARAGRAPH_FUNCTIONS[func as keyof typeof PARAGRAPH_FUNCTIONS];
                              return (
                                <span
                                  key={idx}
                                  className={clsx(
                                    'px-1.5 py-0.5 rounded text-xs',
                                    `bg-${config?.color || 'gray'}-100 text-${config?.color || 'gray'}-700`
                                  )}
                                >
                                  {config?.label || func}
                                </span>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm text-gray-500">
                          H{section.headingDepth} | {section.argumentCount} args
                        </span>
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                    </button>
                    {isExpanded && (
                      <div className="px-4 py-3 bg-gray-50 border-t">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <h5 className="font-medium text-gray-700 mb-2">Function Sequence / 功能序列</h5>
                            <div className="flex flex-wrap gap-1">
                              {section.functionSequence.map((func, idx) => {
                                const config = PARAGRAPH_FUNCTIONS[func as keyof typeof PARAGRAPH_FUNCTIONS];
                                return (
                                  <span key={idx} className="flex items-center gap-1">
                                    <span
                                      className={clsx(
                                        'px-2 py-1 rounded',
                                        `bg-${config?.color || 'gray'}-100 text-${config?.color || 'gray'}-700`
                                      )}
                                    >
                                      {config?.labelZh || func}
                                    </span>
                                    {idx < section.functionSequence.length - 1 && (
                                      <span className="text-gray-400">→</span>
                                    )}
                                  </span>
                                );
                              })}
                            </div>
                          </div>
                          <div>
                            <h5 className="font-medium text-gray-700 mb-2">Similarity with Others / 与其他章节相似度</h5>
                            <div className="space-y-1">
                              {result.similarityPairs
                                .filter(p => p.sectionAIndex === section.sectionIndex || p.sectionBIndex === section.sectionIndex)
                                .map((pair, idx) => {
                                  const otherIndex = pair.sectionAIndex === section.sectionIndex ? pair.sectionBIndex : pair.sectionAIndex;
                                  return (
                                    <div key={idx} className="flex items-center justify-between">
                                      <span className="text-gray-600">
                                        vs Section {otherIndex + 1}
                                      </span>
                                      <span className={clsx(
                                        'px-2 py-0.5 rounded text-xs',
                                        pair.structureSimilarity > 85 ? 'bg-red-100 text-red-700' :
                                        pair.structureSimilarity > 70 ? 'bg-yellow-100 text-yellow-700' :
                                        'bg-green-100 text-green-700'
                                      )}>
                                        {Math.round(pair.structureSimilarity)}%
                                      </span>
                                    </div>
                                  );
                                })}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Suspicious Pairs */}
          {result.suspiciousPairs.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                Suspicious Similar Pairs / 可疑相似对
              </h3>
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="space-y-2">
                  {result.suspiciousPairs.map((pair, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-white rounded">
                      <span className="text-gray-700">
                        Section {pair.sectionAIndex + 1} ({pair.sectionARole}) &harr; Section {pair.sectionBIndex + 1} ({pair.sectionBRole})
                      </span>
                      <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-sm">
                        {Math.round(pair.structureSimilarity)}% similar
                      </span>
                    </div>
                  ))}
                </div>
                <p className="text-red-600 text-sm mt-3">
                  These section pairs have highly similar internal structures, which is a common AI writing pattern.
                </p>
                <p className="text-red-500 text-sm mt-1">
                  这些章节对具有高度相似的内部结构，这是常见的AI写作模式。
                </p>
              </div>
            </div>
          )}

          {/* AI Suggestions */}
          {(result.recommendations.length > 0 || result.recommendationsZh.length > 0) && (
            <div className="mb-6">
              <Button
                variant="secondary"
                onClick={() => setShowAiSuggestion(!showAiSuggestion)}
                className="w-full"
              >
                <Zap className="w-4 h-4 mr-2" />
                {showAiSuggestion ? 'Hide Suggestions' : 'View Suggestions / 查看建议'}
              </Button>
              {showAiSuggestion && (
                <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                  <h4 className="font-medium text-purple-800 mb-2">
                    Structure Differentiation Suggestions / 结构差异化建议
                  </h4>
                  <ul className="space-y-2 text-purple-700 text-sm">
                    {result.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-purple-500">•</span>
                        <div>
                          <span>{rec}</span>
                          {result.recommendationsZh[idx] && (
                            <span className="block text-purple-600 mt-1">
                              {result.recommendationsZh[idx]}
                            </span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
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
            Back: Length Distribution / 上一步：长度分布
          </Button>
          <Button variant="primary" onClick={handleNext} disabled={isAnalyzing || !result}>
            Next: Transitions / 下一步：章节衔接
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
