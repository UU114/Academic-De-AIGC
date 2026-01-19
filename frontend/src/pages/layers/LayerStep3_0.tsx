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
  AlertTriangle,
  Info,
  Sparkles,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { useSubstepStateStore } from '../../stores/substepStateStore';
import {
  paragraphLayerApi,
  ParagraphIdentificationResponse,
  ParagraphMeta,
  DetectionIssue,
} from '../../services/analysisApi';

/**
 * Layer Step 3.0 - Paragraph Identification & Segmentation
 * 步骤 3.0 - 段落识别与分割
 *
 * This is a preprocessing step for Layer 3 (Paragraph Level Analysis).
 * It identifies paragraphs and filters non-body content.
 * No modification is needed - this is purely informational.
 *
 * 这是第3层（段落级分析）的预处理步骤。
 * 用于识别段落并过滤非正文内容。
 * 无需修改 - 这只是信息展示。
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
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // Helper function to check if documentId is valid
  const isValidDocumentId = (id: string | undefined): boolean => {
    return !!(id && id !== 'undefined' && id !== 'null');
  };

  const getInitialDocumentId = (): string | undefined => {
    if (isValidDocumentId(documentIdProp)) return documentIdProp;
    if (isValidDocumentId(documentIdParam)) return documentIdParam;
    return undefined;
  };

  const [documentId, setDocumentId] = useState<string | undefined>(getInitialDocumentId());
  const [sessionFetchAttempted, setSessionFetchAttempted] = useState(
    isValidDocumentId(documentIdProp) || isValidDocumentId(documentIdParam)
  );

  useEffect(() => {
    const fetchDocumentIdFromSession = async () => {
      if (!isValidDocumentId(documentId) && sessionId) {
        try {
          const sessionState = await sessionApi.getCurrent(sessionId);
          if (sessionState.documentId) {
            setDocumentId(sessionState.documentId);
          }
        } catch (err) {
          console.error('Failed to get documentId from session:', err);
        }
      }
      setSessionFetchAttempted(true);
    };

    if (!sessionId) {
      setSessionFetchAttempted(true);
    } else if (!isValidDocumentId(documentId)) {
      fetchDocumentIdFromSession();
    } else {
      setSessionFetchAttempted(true);
    }
  }, [documentId, sessionId]);

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
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedParagraphIndex, setExpandedParagraphIndex] = useState<number | null>(null);

  // Issues derived from analysis result (informational only)
  // 从分析结果派生的问题列表（仅供参考）
  const [paragraphIssues, setParagraphIssues] = useState<DetectionIssue[]>([]);

  const isAnalyzingRef = useRef(false);

  // Substep state store for document text handling
  // 子步骤状态存储用于文档文本处理
  const substepStore = useSubstepStateStore();

  // Load document
  // 加载文档
  useEffect(() => {
    if (!sessionFetchAttempted) return;
    if (isValidDocumentId(documentId)) {
      loadDocumentText(documentId!);
    } else {
      setError('Document ID not found. Please start from the document upload page. / 未找到文档ID，请从文档上传页面开始。');
      setIsLoading(false);
    }
  }, [documentId, sessionFetchAttempted]);

  const loadDocumentText = async (docId: string) => {
    try {
      // Initialize substep store for session if needed
      // 如果需要，为会话初始化子步骤存储
      if (sessionId && substepStore.currentSessionId !== sessionId) {
        await substepStore.initForSession(sessionId);
      }

      // Check previous steps for modified text (Layer 4 steps, then Layer 5 steps)
      // 检查前面步骤的修改文本（先检查第4层，再检查第5层）
      const previousSteps = ['step2-5', 'step2-4', 'step2-3', 'step2-2', 'step2-1', 'step2-0',
                            'step1-5', 'step1-4', 'step1-3', 'step1-2', 'step1-1'];
      let foundModifiedText: string | null = null;

      for (const stepName of previousSteps) {
        const stepState = substepStore.getState(stepName);
        if (stepState?.modifiedText) {
          console.log(`[LayerStep3_0] Using modified text from ${stepName}`);
          foundModifiedText = stepState.modifiedText;
          break;
        }
      }

      if (foundModifiedText) {
        setDocumentText(foundModifiedText);
      } else {
        const doc = await documentApi.get(docId);
        if (doc.originalText) {
          setDocumentText(doc.originalText);
        } else {
          setError('Document text not found / 未找到文档文本');
        }
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
    if (documentText && analysisStarted && !isAnalyzingRef.current) {
      runAnalysis();
    }
  }, [documentText, analysisStarted]);

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

      // Create informational issues from analysis result
      // 从分析结果创建信息性问题列表
      const issues: DetectionIssue[] = [];

      // Check for filtered content (informational)
      // 检查过滤内容（信息性）
      if (analysisResult.filteredCount > 0) {
        issues.push({
          type: 'filtered_content',
          description: `${analysisResult.filteredCount} non-body elements were filtered (headers, keywords, etc.)`,
          descriptionZh: `已过滤 ${analysisResult.filteredCount} 个非正文元素（标题、关键词等）`,
          severity: 'low',
          layer: 'paragraph',
        });
      }

      // Check for unusual paragraph lengths (informational)
      // 检查异常段落长度（信息性）
      const avgWordCount = analysisResult.totalWordCount / analysisResult.paragraphCount;
      analysisResult.paragraphMetadata.forEach((para: ParagraphMeta) => {
        if (para.wordCount < avgWordCount * 0.2) {
          issues.push({
            type: 'short_paragraph',
            description: `Paragraph ${para.index + 1} is unusually short (${para.wordCount} words)`,
            descriptionZh: `段落${para.index + 1}异常短 (${para.wordCount}词)`,
            severity: 'low',
            layer: 'paragraph',
            position: { paragraphIndex: para.index },
          });
        } else if (para.wordCount > avgWordCount * 3) {
          issues.push({
            type: 'long_paragraph',
            description: `Paragraph ${para.index + 1} is unusually long (${para.wordCount} words)`,
            descriptionZh: `段落${para.index + 1}异常长 (${para.wordCount}词)`,
            severity: 'low',
            layer: 'paragraph',
            position: { paragraphIndex: para.index },
          });
        }
      });

      setParagraphIssues(issues);

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
  if (error && !result) {
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

        {/* Info Notice - No modification needed */}
        {/* 信息提示 - 无需修改 */}
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-2">
          <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-700">
            <p className="font-medium">This is a preprocessing step / 这是预处理步骤</p>
            <p className="text-blue-600">
              No modification is needed. This step prepares paragraph data for subsequent analysis.
              无需修改。此步骤为后续分析准备段落数据。
            </p>
          </div>
        </div>

        {/* Start Analysis / Skip Step */}
        {/* 开始分析 / 跳过此步 */}
        {documentText && !analysisStarted && !isAnalyzing && !result && (
          <div className="mt-4 p-6 bg-gray-50 border border-gray-200 rounded-lg">
            <div className="text-center">
              <Layers className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Analyze / 准备分析</h3>
              <p className="text-gray-600 mb-6">
                Click to identify paragraphs and filter non-body content for analysis
                <br />
                <span className="text-gray-500">点击开始识别段落并过滤非正文内容以进行分析</span>
              </p>
              <div className="flex items-center justify-center gap-4">
                <Button variant="primary" size="lg" onClick={() => setAnalysisStarted(true)}>
                  <Sparkles className="w-5 h-5 mr-2" />
                  Start Analysis / 开始分析
                </Button>
                <Button variant="secondary" size="lg" onClick={goToNextStep}>
                  <ArrowRight className="w-5 h-5 mr-2" />
                  Skip Step / 跳过此步
                </Button>
              </div>
            </div>
          </div>
        )}

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

      {/* Informational Issues Section (Read-only) */}
      {/* 信息性问题部分（只读） */}
      {paragraphIssues.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-3">
            <Info className="w-5 h-5 text-blue-600" />
            Paragraph Info / 段落信息
          </h3>
          <div className="space-y-2">
            {paragraphIssues.map((issue, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-gray-50 border border-gray-200"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
                        Info / 信息
                      </span>
                      <span className="text-xs text-gray-500">{issue.layer}</span>
                    </div>
                    <p className="text-gray-900 mt-1">{issue.description}</p>
                    <p className="text-gray-600 text-sm">{issue.descriptionZh}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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

      {/* No issues - All good message */}
      {paragraphIssues.length === 0 && result && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-green-800">
              Paragraph Structure Looks Good
            </h3>
            <p className="text-green-600 mt-1">
              段落结构良好。文档已准备好进行后续分析。
            </p>
          </div>
        </div>
      )}

      {/* Recommendations (if any) */}
      {result && result.recommendations && result.recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            Recommendations / 建议
          </h3>
          <ul className="space-y-2">
            {result.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-yellow-500 mt-1">*</span>
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
            Next: Step 3.1
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
