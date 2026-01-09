import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  FileText,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Layers,
  AlertTriangle,
  ListOrdered,
  RefreshCw,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { documentLayerApi, DocumentAnalysisResponse, DetectionIssue } from '../../services/analysisApi';

/**
 * Layer Step 1.1 - Section Structure & Order Detection
 * 步骤 1.1 - 章节结构与顺序识别
 *
 * Detects:
 * - Section structure (identifies chapter boundaries)
 * - Predictable section order (Introduction-Method-Results-Discussion pattern)
 *
 * Priority: ★★★★★ (Highest - all subsequent analysis depends on this)
 * 优先级: ★★★★★ (最高 - 所有后续分析都依赖于此)
 *
 * Part of the 5-layer detection architecture - Layer 5 Sub-steps.
 * 5层检测架构的一部分 - 第5层子步骤。
 */

// Section role display configuration
// 章节角色显示配置
const SECTION_ROLE_CONFIG: Record<string, { label: string; labelZh: string; color: string }> = {
  introduction: { label: 'Introduction', labelZh: '引言', color: 'bg-blue-100 text-blue-800' },
  background: { label: 'Background', labelZh: '背景', color: 'bg-purple-100 text-purple-800' },
  method: { label: 'Method', labelZh: '方法', color: 'bg-green-100 text-green-800' },
  methodology: { label: 'Methodology', labelZh: '方法论', color: 'bg-green-100 text-green-800' },
  results: { label: 'Results', labelZh: '结果', color: 'bg-yellow-100 text-yellow-800' },
  discussion: { label: 'Discussion', labelZh: '讨论', color: 'bg-orange-100 text-orange-800' },
  conclusion: { label: 'Conclusion', labelZh: '结论', color: 'bg-red-100 text-red-800' },
  body: { label: 'Body', labelZh: '正文', color: 'bg-gray-100 text-gray-800' },
  unknown: { label: 'Unknown', labelZh: '未知', color: 'bg-gray-100 text-gray-600' },
};

// Order pattern display configuration
// 顺序模式显示配置
const ORDER_PATTERN_CONFIG: Record<string, { label: string; labelZh: string; risk: string; color: string }> = {
  'AI-typical': { label: 'AI-Typical (Formulaic)', labelZh: 'AI典型（公式化）', risk: 'high', color: 'text-red-600' },
  'Human-like': { label: 'Human-like (Natural)', labelZh: '人类风格（自然）', risk: 'low', color: 'text-green-600' },
  'Mixed': { label: 'Mixed Pattern', labelZh: '混合模式', risk: 'medium', color: 'text-yellow-600' },
  'unknown': { label: 'Unknown', labelZh: '未知', risk: 'low', color: 'text-gray-600' },
};

interface SectionInfo {
  index: number;
  role: string;
  title?: string;
  paragraphCount: number;
  wordCount: number;
}

interface LayerStep1_1Props {
  // Optional document ID from props
  documentIdProp?: string;
  // Callback when analysis completes
  onComplete?: (result: DocumentAnalysisResponse) => void;
  // Whether to show navigation buttons
  showNavigation?: boolean;
}

export default function LayerStep1_1({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep1_1Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Processing mode and session from URL parameter
  // 从URL参数获取处理模式和会话ID
  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // Update session step on mount
  // 挂载时更新会话步骤
  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer5-step1-1').catch(console.error);
    }
  }, [sessionId]);

  // Analysis state
  // 分析状态
  const [result, setResult] = useState<DocumentAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Document text
  // 文档文本
  const [documentText, setDocumentText] = useState<string>('');

  // Sections detected
  // 检测到的章节
  const [sections, setSections] = useState<SectionInfo[]>([]);
  const [structurePattern, setStructurePattern] = useState<string>('unknown');
  const [expandedSectionIndex, setExpandedSectionIndex] = useState<number | null>(null);

  // Order issues
  // 顺序问题
  const [orderIssues, setOrderIssues] = useState<DetectionIssue[]>([]);
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

  // Prevent duplicate API calls
  // 防止重复API调用
  const isAnalyzingRef = useRef(false);

  // Load document text
  // 加载文档文本
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

  // Run analysis when text is loaded
  // 文本加载后运行分析
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
      // Call structure analysis API
      // 调用结构分析API
      const analysisResult = await documentLayerApi.analyzeStructure(documentText);
      setResult(analysisResult);

      // Extract sections
      // 提取章节
      if (analysisResult.sections) {
        setSections(analysisResult.sections);
      }

      // Extract structure pattern
      // 提取结构模式
      if (analysisResult.structurePattern) {
        setStructurePattern(analysisResult.structurePattern);
      }

      // Filter order-related issues
      // 过滤顺序相关问题
      const orderRelatedIssues = analysisResult.issues.filter(
        (issue) =>
          issue.type.includes('predictable') ||
          issue.type.includes('order') ||
          issue.type.includes('structure') ||
          issue.type.includes('formulaic')
      );
      setOrderIssues(orderRelatedIssues);

      // Callback
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

  // Navigation handlers
  // 导航处理
  const handleBack = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/term-lock/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer5-step1-2/${documentId}?${params.toString()}`);
  };

  // Toggle section expansion
  // 切换章节展开
  const toggleSection = (index: number) => {
    setExpandedSectionIndex(expandedSectionIndex === index ? null : index);
  };

  // Toggle issue expansion
  // 切换问题展开
  const toggleIssue = (index: number) => {
    setExpandedIssueIndex(expandedIssueIndex === index ? null : index);
  };

  // Get role config
  // 获取角色配置
  const getRoleConfig = (role: string) => {
    return SECTION_ROLE_CONFIG[role.toLowerCase()] || SECTION_ROLE_CONFIG.unknown;
  };

  // Get order pattern config
  // 获取顺序模式配置
  const getPatternConfig = (pattern: string) => {
    return ORDER_PATTERN_CONFIG[pattern] || ORDER_PATTERN_CONFIG.unknown;
  };

  // Loading state
  // 加载状态
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage category="structure" centered />
      </div>
    );
  }

  // Error state
  // 错误状态
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

  const patternConfig = getPatternConfig(structurePattern);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Layers className="w-4 h-4" />
          <span>Layer 5 / 第5层</span>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Step 1.1 章节结构与顺序</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Section Structure & Order Detection
        </h1>
        <p className="text-gray-600 mt-1">
          章节结构与顺序识别 - 检测公式化章节顺序（如：引言-方法-结果-讨论）
        </p>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing structure... / 分析结构中...</p>
              <p className="text-blue-600 text-sm">Identifying sections and order patterns</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* Structure Pattern Summary */}
          <div className="mb-6 p-4 bg-white border rounded-lg shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <ListOrdered className="w-5 h-5" />
                  Structure Pattern / 结构模式
                </h2>
                <p className="text-gray-600 text-sm mt-1">
                  Detected {sections.length} sections in document
                  / 检测到 {sections.length} 个章节
                </p>
              </div>
              <div className={clsx('px-4 py-2 rounded-lg font-medium', patternConfig.color)}>
                {patternConfig.labelZh}
                <span className="ml-2 text-sm opacity-75">({patternConfig.label})</span>
              </div>
            </div>

            {/* Risk indicator */}
            {patternConfig.risk === 'high' && (
              <div className="mt-4 p-3 bg-red-50 rounded-lg flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
                <div>
                  <p className="text-red-800 font-medium">
                    High AI Risk: Formulaic Structure Detected
                  </p>
                  <p className="text-red-600 text-sm">
                    高AI风险：检测到公式化结构。建议打乱顺序、合并章节或改变章节功能定位。
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Section List */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Detected Sections / 检测到的章节
            </h3>
            <div className="space-y-2">
              {sections.map((section, idx) => {
                const roleConfig = getRoleConfig(section.role);
                const isExpanded = expandedSectionIndex === idx;
                return (
                  <div
                    key={idx}
                    className="bg-white border rounded-lg overflow-hidden"
                  >
                    <button
                      onClick={() => toggleSection(idx)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-8 h-8 flex items-center justify-center bg-gray-100 rounded-full text-sm font-medium text-gray-600">
                          {idx + 1}
                        </span>
                        <div className="text-left">
                          <div className="flex items-center gap-2">
                            <span className={clsx('px-2 py-0.5 rounded text-xs font-medium', roleConfig.color)}>
                              {roleConfig.labelZh}
                            </span>
                            {section.title && (
                              <span className="text-gray-900 font-medium">{section.title}</span>
                            )}
                          </div>
                          <p className="text-sm text-gray-500 mt-0.5">
                            {section.paragraphCount} paragraphs / {section.wordCount} words
                            • {section.paragraphCount} 段落 / {section.wordCount} 词
                          </p>
                        </div>
                      </div>
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      )}
                    </button>
                    {isExpanded && (
                      <div className="px-4 py-3 bg-gray-50 border-t">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Role / 角色:</span>
                            <span className="ml-2 text-gray-900">{roleConfig.label}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Index / 索引:</span>
                            <span className="ml-2 text-gray-900">{section.index}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Paragraphs / 段落数:</span>
                            <span className="ml-2 text-gray-900">{section.paragraphCount}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Word Count / 字数:</span>
                            <span className="ml-2 text-gray-900">{section.wordCount}</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Order Issues */}
          {orderIssues.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
                Structure Issues / 结构问题
                <span className="text-sm font-normal text-gray-500">
                  ({orderIssues.length} issues detected)
                </span>
              </h3>
              <div className="space-y-2">
                {orderIssues.map((issue, idx) => {
                  const isExpanded = expandedIssueIndex === idx;
                  const severityColor = {
                    high: 'border-red-200 bg-red-50',
                    medium: 'border-yellow-200 bg-yellow-50',
                    low: 'border-gray-200 bg-gray-50',
                  }[issue.severity];
                  const severityTextColor = {
                    high: 'text-red-800',
                    medium: 'text-yellow-800',
                    low: 'text-gray-800',
                  }[issue.severity];
                  return (
                    <div
                      key={idx}
                      className={clsx('border rounded-lg overflow-hidden', severityColor)}
                    >
                      <button
                        onClick={() => toggleIssue(idx)}
                        className="w-full px-4 py-3 flex items-center justify-between hover:opacity-90 transition-opacity"
                      >
                        <div className="flex items-center gap-3">
                          <AlertCircle className={clsx('w-5 h-5', severityTextColor)} />
                          <div className="text-left">
                            <p className={clsx('font-medium', severityTextColor)}>
                              {issue.descriptionZh || issue.description}
                            </p>
                            <p className="text-sm text-gray-600 mt-0.5">
                              Severity: {issue.severity.toUpperCase()}
                            </p>
                          </div>
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        )}
                      </button>
                      {isExpanded && (
                        <div className="px-4 py-3 border-t border-current border-opacity-20">
                          <div className="space-y-3">
                            <div>
                              <h4 className="text-sm font-medium text-gray-700">
                                Description / 描述
                              </h4>
                              <p className="text-gray-600 text-sm mt-1">
                                {issue.description}
                              </p>
                            </div>
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
          {orderIssues.length === 0 && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">
                  No Structure Issues Detected
                </h3>
                <p className="text-green-600 mt-1">
                  未检测到结构问题。章节顺序看起来是自然的。
                </p>
              </div>
            </div>
          )}

          {/* Processing time */}
          {result.processingTimeMs && (
            <p className="text-sm text-gray-500 mb-6">
              Analysis completed in {result.processingTimeMs}ms
              / 分析完成，耗时 {result.processingTimeMs}ms
            </p>
          )}
        </>
      )}

      {/* Navigation */}
      {showNavigation && (
        <div className="flex items-center justify-between pt-6 border-t">
          <Button
            variant="secondary"
            onClick={handleBack}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Term Lock / 返回术语锁定
          </Button>
          <Button
            variant="primary"
            onClick={handleNext}
            disabled={isAnalyzing}
          >
            Next: Section Uniformity / 下一步：章节均匀性
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
