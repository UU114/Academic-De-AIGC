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
  Filter,
  Hash,
  Type,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { paragraphLayerApi, ParagraphIdentificationResponse, ParagraphMeta } from '../../services/analysisApi';

/**
 * Layer Step 3.0 - Paragraph Identification & Segmentation
 * 步骤 3.0 - 段落识别与分割
 *
 * This is the foundational step for Layer 3 (Paragraph Level Analysis).
 * All subsequent Layer 3 steps depend on correct paragraph identification.
 *
 * 这是第3层（段落级分析）的基础步骤。
 * 所有后续的第3层步骤都依赖于正确的段落识别。
 *
 * Functions:
 * - Identify paragraph boundaries
 * - Filter non-body content (headers, keywords, etc.)
 * - Map paragraphs to sections from Layer 4
 * - Extract paragraph metadata
 *
 * 功能：
 * - 识别段落边界
 * - 过滤非正文内容（标题、关键词等）
 * - 将段落映射到Layer 4的章节
 * - 提取段落元数据
 */

interface LayerStep3_0Props {
  documentIdProp?: string;
  onComplete?: (result: ParagraphIdentificationResponse) => void;
  showNavigation?: boolean;
  sectionContext?: Record<string, unknown>;
}

export default function LayerStep3_0({
  documentIdProp,
  onComplete,
  showNavigation = true,
  sectionContext,
}: LayerStep3_0Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // Update session step
  // 更新会话步骤
  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer3-step3-0').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<ParagraphIdentificationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedParagraphIndex, setExpandedParagraphIndex] = useState<number | null>(null);

  const isAnalyzingRef = useRef(false);

  // Load document
  // 加载文档
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
  // 文档加载后运行分析
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
      const analysisResult = await paragraphLayerApi.identifyParagraphs(
        documentText,
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

  // Navigate to next step
  // 导航到下一步
  const goToNextStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-1/${documentId}?${params.toString()}`);
  };

  // Navigate to previous step (Layer 4 last step)
  // 导航到上一步（Layer 4 最后一步）
  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer4-step2-5/${documentId}?${params.toString()}`);
  };

  // Get risk level color
  // 获取风险等级颜色
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'text-green-600 bg-green-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'high':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  // Toggle paragraph expansion
  // 切换段落展开状态
  const toggleParagraph = (index: number) => {
    setExpandedParagraphIndex(expandedParagraphIndex === index ? null : index);
  };

  // Render loading state
  // 渲染加载状态
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage message="Loading document... / 加载文档中..." />
      </div>
    );
  }

  // Render error state
  // 渲染错误状态
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
              <Layers className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3.0: Paragraph Identification
              </h2>
              <p className="text-sm text-gray-500">
                步骤 3.0: 段落识别与分割
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
          This step identifies paragraph boundaries and filters non-body content to prepare for paragraph-level analysis.
          <br />
          <span className="text-gray-500">
            此步骤识别段落边界并过滤非正文内容，为段落级分析做准备。
          </span>
        </p>

        {/* Summary Stats */}
        {result && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-blue-600 mb-1">
                <FileText className="w-4 h-4" />
                <span className="text-sm font-medium">Paragraphs</span>
              </div>
              <div className="text-2xl font-bold text-blue-700">
                {result.paragraphCount}
              </div>
              <div className="text-xs text-blue-500">识别段落数</div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-purple-600 mb-1">
                <Hash className="w-4 h-4" />
                <span className="text-sm font-medium">Total Words</span>
              </div>
              <div className="text-2xl font-bold text-purple-700">
                {result.totalWordCount}
              </div>
              <div className="text-xs text-purple-500">总词数</div>
            </div>

            <div className="bg-orange-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-orange-600 mb-1">
                <Filter className="w-4 h-4" />
                <span className="text-sm font-medium">Filtered</span>
              </div>
              <div className="text-2xl font-bold text-orange-700">
                {result.filteredCount}
              </div>
              <div className="text-xs text-orange-500">过滤的非正文</div>
            </div>

            <div className={clsx(
              'rounded-lg p-4',
              result.riskLevel === 'low' ? 'bg-green-50' :
              result.riskLevel === 'medium' ? 'bg-yellow-50' : 'bg-red-50'
            )}>
              <div className={clsx(
                'flex items-center gap-2 mb-1',
                result.riskLevel === 'low' ? 'text-green-600' :
                result.riskLevel === 'medium' ? 'text-yellow-600' : 'text-red-600'
              )}>
                {result.riskLevel === 'low' ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <AlertCircle className="w-4 h-4" />
                )}
                <span className="text-sm font-medium">Risk Level</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                result.riskLevel === 'low' ? 'text-green-700' :
                result.riskLevel === 'medium' ? 'text-yellow-700' : 'text-red-700'
              )}>
                {result.riskLevel.toUpperCase()}
              </div>
              <div className={clsx(
                'text-xs',
                result.riskLevel === 'low' ? 'text-green-500' :
                result.riskLevel === 'medium' ? 'text-yellow-500' : 'text-red-500'
              )}>风险等级</div>
            </div>
          </div>
        )}
      </div>

      {/* Paragraph List */}
      {result && result.paragraphMetadata.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            Paragraph List / 段落列表
          </h3>

          <div className="space-y-3">
            {result.paragraphMetadata.map((para: ParagraphMeta, index: number) => (
              <div
                key={index}
                className="border rounded-lg overflow-hidden hover:border-blue-300 transition-colors"
              >
                <div
                  className="flex items-center justify-between p-4 cursor-pointer bg-gray-50 hover:bg-gray-100"
                  onClick={() => toggleParagraph(index)}
                >
                  <div className="flex items-center gap-4">
                    <span className="w-8 h-8 flex items-center justify-center bg-blue-100 text-blue-600 rounded-full font-medium">
                      {index + 1}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500">
                          {para.wordCount} words / {para.sentenceCount} sentences
                        </span>
                        {para.sectionIndex !== undefined && (
                          <span className="px-2 py-0.5 bg-purple-100 text-purple-600 text-xs rounded">
                            Section {para.sectionIndex + 1}
                          </span>
                        )}
                      </div>
                      <p className="text-gray-700 text-sm mt-1 truncate max-w-xl">
                        {para.preview}
                      </p>
                    </div>
                  </div>
                  {expandedParagraphIndex === index ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  )}
                </div>

                {expandedParagraphIndex === index && (
                  <div className="p-4 border-t bg-white">
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div className="text-center p-3 bg-gray-50 rounded">
                        <div className="text-lg font-semibold text-gray-700">{para.wordCount}</div>
                        <div className="text-xs text-gray-500">Words / 词数</div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 rounded">
                        <div className="text-lg font-semibold text-gray-700">{para.sentenceCount}</div>
                        <div className="text-xs text-gray-500">Sentences / 句数</div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 rounded">
                        <div className="text-lg font-semibold text-gray-700">{para.charCount}</div>
                        <div className="text-xs text-gray-500">Characters / 字符数</div>
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded p-3">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Full Text / 完整文本:</h4>
                      <p className="text-sm text-gray-600 whitespace-pre-wrap">
                        {result.paragraphs[index]}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {result && result.recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-600" />
            Recommendations / 建议
          </h3>
          <ul className="space-y-2">
            {result.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-yellow-500 mt-1">•</span>
                <div>
                  <p className="text-gray-700">{rec}</p>
                  {result.recommendationsZh[index] && (
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
          <Button
            variant="outline"
            onClick={goToPreviousStep}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Previous: Layer 4 Step 2.5
          </Button>
          <Button
            onClick={goToNextStep}
            disabled={!result}
            className="flex items-center gap-2"
          >
            Next: Step 3.1 Role Detection
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
