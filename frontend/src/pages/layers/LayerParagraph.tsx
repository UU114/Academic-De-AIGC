import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  AlignLeft,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Users,
  Link2,
  Anchor,
  BarChart2,
  FileText,
  Filter,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import {
  paragraphLayerApi,
  sectionLayerApi,
  ParagraphAnalysisResponse,
  DetectionIssue,
} from '../../services/analysisApi';

/**
 * Layer Paragraph (Layer 3) - Paragraph Analysis
 * 段落层（第3层）- 段落分析
 *
 * Steps:
 * - Step 3.1: Paragraph Role Detection (段落角色识别)
 * - Step 3.2: Paragraph Internal Coherence (段落内部连贯性)
 * - Step 3.3: Anchor Density Analysis (锚点密度分析)
 * - Step 3.4: Sentence Length Distribution (段内句子长度分布)
 *
 * Receives context from Layer 4 (Section).
 * 从第4层（章节层）接收上下文。
 */

interface LayerParagraphProps {
  documentIdProp?: string;
  onComplete?: (result: ParagraphAnalysisResponse) => void;
  showNavigation?: boolean;
}

export default function LayerParagraph({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerParagraphProps) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer-paragraph').catch(console.error);
    }
  }, [sessionId]);

  // Analysis state
  const [result, setResult] = useState<ParagraphAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<'preview' | '3.1' | '3.2' | '3.3' | '3.4'>('preview');

  // Document context
  const [documentText, setDocumentText] = useState<string>('');
  const [sectionContext, setSectionContext] = useState<Record<string, unknown> | null>(null);

  // Issue expansion
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);
  const [expandedParagraphIndex, setExpandedParagraphIndex] = useState<number | null>(null);

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
      analyzeParagraph();
    }
  }, [documentText]);

  const analyzeParagraph = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;

    setIsLoading(true);
    setError(null);

    try {
      console.log('Layer 3: Getting section context from Layer 4...');

      // Get section context from Layer 4
      const secContext = await sectionLayerApi.getContext(documentText);
      setSectionContext(secContext as Record<string, unknown>);

      console.log('Layer 3: Analyzing paragraphs with section context...');

      // Run paragraph analysis with context
      const analysisResult = await paragraphLayerApi.analyze(
        documentText,
        secContext as Record<string, unknown>
      );
      console.log('Layer 3 result:', analysisResult);

      setResult(analysisResult);

      if (onComplete) {
        onComplete(analysisResult);
      }
    } catch (err: unknown) {
      console.error('Paragraph analysis failed:', err);
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

  const handleParagraphClick = useCallback((index: number) => {
    setExpandedParagraphIndex(prev => prev === index ? null : index);
  }, []);

  const handleNext = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/layer-sentence/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

  const handleBack = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/layer-section/${documentId}?mode=${mode}${sessionParam}`);
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
              返回章节层
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
            <div className="p-2 rounded-lg bg-teal-100 text-teal-600 mr-3">
              <AlignLeft className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Layer 3: 段落层分析
              </h1>
              <p className="text-gray-600 mt-1">
                Paragraph Layer Analysis
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
          <span className="font-medium text-teal-600 bg-teal-50 px-2 py-1 rounded">
            Layer 3 段落
          </span>
          <span className="mx-2">→</span>
          <span>Layer 2</span>
          <span className="mx-2">→</span>
          <span>Layer 1</span>
        </div>

        {/* Step tabs */}
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            onClick={() => setCurrentStep('preview')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === 'preview' ? 'bg-teal-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <FileText className="w-4 h-4 mr-1" />
            段落预览
          </button>
          <button
            onClick={() => setCurrentStep('3.1')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '3.1' ? 'bg-teal-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <Users className="w-4 h-4 mr-1" />
            3.1 角色
          </button>
          <button
            onClick={() => setCurrentStep('3.2')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '3.2' ? 'bg-teal-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <Link2 className="w-4 h-4 mr-1" />
            3.2 连贯性
          </button>
          <button
            onClick={() => setCurrentStep('3.3')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '3.3' ? 'bg-teal-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <Anchor className="w-4 h-4 mr-1" />
            3.3 锚点
          </button>
          <button
            onClick={() => setCurrentStep('3.4')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '3.4' ? 'bg-teal-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <BarChart2 className="w-4 h-4 mr-1" />
            3.4 句长分布
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
                  段落层风险分数 / Paragraph Layer Risk Score
                </h3>
                <p className="text-sm text-gray-500">
                  分析段落角色、连贯性、锚点密度和句长分布
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
                <p className="text-2xl font-bold text-teal-600">{result.paragraphCount || 0}</p>
                <p className="text-sm text-gray-600">段落数</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-teal-600">{result.coherenceScore || 0}</p>
                <p className="text-sm text-gray-600">连贯分</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-teal-600">{result.anchorDensity?.toFixed(1) || 0}</p>
                <p className="text-sm text-gray-600">锚点密度</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-teal-600">
                  {result.sentenceLengthAnalysis?.meanCv?.toFixed(2) || 'N/A'}
                </p>
                <p className="text-sm text-gray-600">句长CV</p>
              </div>
            </div>
          </div>

          {/* Paragraph Preview - Show filtered paragraphs */}
          {/* 段落预览 - 显示过滤后的段落 */}
          {currentStep === 'preview' && result.paragraphs && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Filter className="w-5 h-5 mr-2 text-teal-600" />
                已过滤段落列表 / Filtered Paragraphs
              </h3>

              {/* Filter explanation */}
              <div className="p-4 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg mb-4">
                <p className="text-blue-800 font-medium flex items-center">
                  <Filter className="w-4 h-4 mr-2" />
                  智能过滤已启用
                </p>
                <p className="text-sm text-blue-600 mt-1">
                  系统已自动过滤标题、章节名、Keywords、表格标题、图片说明等非正文内容，仅保留真正的段落用于AI检测分析。
                </p>
                <p className="text-sm text-blue-600 mt-1">
                  Headers, section titles, keywords, table captions, and figure captions have been filtered out. Only actual paragraphs are kept for AI detection analysis.
                </p>
              </div>

              {/* Paragraph count */}
              <div className="flex items-center justify-between mb-4 p-3 bg-teal-50 rounded-lg">
                <span className="text-teal-800 font-medium">
                  检测到 {result.paragraphs.length} 个有效段落
                </span>
                <span className="text-sm text-teal-600">
                  {result.paragraphs.length} valid paragraphs detected
                </span>
              </div>

              {/* Paragraph list */}
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {result.paragraphs.map((para, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-teal-300 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className="px-2 py-1 bg-teal-100 text-teal-700 text-xs font-medium rounded">
                        段落 {idx + 1}
                      </span>
                      <span className="text-xs text-gray-500">
                        {para.split(/[.!?。！？]/).filter(s => s.trim()).length} 句 / {para.length} 字符
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {para.length > 300 ? para.substring(0, 300) + '...' : para}
                    </p>
                    {para.length > 300 && (
                      <button
                        onClick={() => handleParagraphClick(idx)}
                        className="mt-2 text-xs text-teal-600 hover:text-teal-800"
                      >
                        {expandedParagraphIndex === idx ? '收起' : '展开全文'}
                      </button>
                    )}
                    {expandedParagraphIndex === idx && para.length > 300 && (
                      <p className="text-sm text-gray-700 leading-relaxed mt-2 pt-2 border-t border-gray-200">
                        {para}
                      </p>
                    )}
                  </div>
                ))}
              </div>

              {result.paragraphs.length === 0 && (
                <div className="p-8 text-center text-gray-500">
                  <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <p>未检测到有效段落</p>
                  <p className="text-sm mt-1">No valid paragraphs detected</p>
                </div>
              )}
            </div>
          )}

          {/* Step 3.1: Role Distribution */}
          {currentStep === '3.1' && result.roleDistribution && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Users className="w-5 h-5 mr-2 text-teal-600" />
                段落角色分布 / Paragraph Role Distribution
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(result.roleDistribution).map(([role, count]) => (
                  <div key={role} className="p-3 bg-gray-50 rounded-lg flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">{role}</span>
                    <span className="text-lg font-bold text-teal-600">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 3.2: Coherence */}
          {currentStep === '3.2' && result.paragraphDetails && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Link2 className="w-5 h-5 mr-2 text-teal-600" />
                段落连贯性分析 / Paragraph Coherence
              </h3>
              <div className="space-y-3">
                {result.paragraphDetails.map((para, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleParagraphClick(idx)}
                    className="p-4 bg-gray-50 rounded-lg border border-gray-200 cursor-pointer hover:shadow-md"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-800">段落 {para.index + 1}</span>
                      <div className="flex items-center space-x-2">
                        <span className={clsx(
                          'px-2 py-1 rounded text-xs',
                          para.coherenceScore >= 70 && 'bg-green-100 text-green-700',
                          para.coherenceScore >= 40 && para.coherenceScore < 70 && 'bg-yellow-100 text-yellow-700',
                          para.coherenceScore < 40 && 'bg-red-100 text-red-700'
                        )}>
                          连贯分: {para.coherenceScore}
                        </span>
                        {expandedParagraphIndex === idx ? (
                          <ChevronUp className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        )}
                      </div>
                    </div>
                    {expandedParagraphIndex === idx && para.issues.length > 0 && (
                      <div className="mt-3 space-y-1">
                        {para.issues.map((issue, iIdx) => (
                          <p key={iIdx} className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
                            {issue}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 3.3: Anchor Density */}
          {currentStep === '3.3' && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Anchor className="w-5 h-5 mr-2 text-teal-600" />
                锚点密度分析 / Anchor Density Analysis
              </h3>
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-700">整体锚点密度 / Overall Anchor Density</span>
                    <span className={clsx(
                      'text-2xl font-bold',
                      (result.anchorDensity || 0) >= 5 && 'text-green-600',
                      (result.anchorDensity || 0) < 5 && 'text-red-600'
                    )}>
                      {result.anchorDensity?.toFixed(1) || 0} / 100词
                    </span>
                  </div>
                  {(result.anchorDensity || 0) < 5 && (
                    <p className="text-sm text-red-600 mt-2">
                      锚点密度过低（&lt;5/100词）表示内容可能缺乏具体细节，有AI生成风险
                    </p>
                  )}
                </div>
                {result.paragraphDetails && (
                  <div className="space-y-2">
                    {result.paragraphDetails.map((para, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 rounded-lg flex items-center justify-between">
                        <span className="text-sm text-gray-700">段落 {para.index + 1}</span>
                        <span className={clsx(
                          'font-medium',
                          para.anchorCount >= 5 && 'text-green-600',
                          para.anchorCount < 5 && 'text-red-600'
                        )}>
                          {para.anchorCount} 锚点
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Step 3.4: Sentence Length Distribution */}
          {currentStep === '3.4' && result.sentenceLengthAnalysis && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <BarChart2 className="w-5 h-5 mr-2 text-teal-600" />
                段内句子长度分布 / Sentence Length Distribution
              </h3>
              {result.sentenceLengthAnalysis.uniformLengthRisk && (
                <div className="p-4 bg-amber-50 border-l-4 border-amber-500 rounded-r-lg mb-4">
                  <p className="text-amber-800 font-medium">句长分布过于均匀</p>
                  <p className="text-sm text-amber-600 mt-1">
                    这是AI生成文本的典型特征。建议增加句长变化以提高自然度。
                  </p>
                </div>
              )}
              {result.sentenceLengthAnalysis.lowBurstinessParagraphs &&
               result.sentenceLengthAnalysis.lowBurstinessParagraphs.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm text-gray-600 mb-2">
                    以下段落的句长变化较低（低burstiness）：
                  </p>
                  {result.sentenceLengthAnalysis.lowBurstinessParagraphs.map((paraIdx, idx) => (
                    <div key={idx} className="p-3 bg-red-50 rounded-lg">
                      <span className="text-sm text-red-700">
                        段落 {paraIdx + 1} - 建议增加句长变化
                      </span>
                    </div>
                  ))}
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
                返回章节层
              </Button>
              <Button onClick={handleNext}>
                继续到句子层
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
