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
  Edit3,
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
import { sectionLayerApi, SectionIdentificationResponse, SectionInfo } from '../../services/analysisApi';

/**
 * Layer Step 2.0 - Section Identification & Role Labeling
 * 步骤 2.0 - 章节识别与角色标注
 *
 * This is the foundational step for Layer 4 (Section Level Analysis).
 * All subsequent Layer 4 steps depend on correct section identification.
 *
 * 这是第4层（章节级分析）的基础步骤。
 * 所有后续的第4层步骤都依赖于正确的章节识别。
 *
 * Detection:
 * - A: Section Role Detection (章节角色识别)
 *
 * Priority: (Highest - foundation for all subsequent analysis)
 * 优先级: (最高 - 所有后续分析的基础)
 */

// Section role configuration
// 章节角色配置
const SECTION_ROLE_CONFIG: Record<string, { label: string; labelZh: string; icon: typeof BookOpen; color: string }> = {
  introduction: { label: 'Introduction', labelZh: '引言', icon: BookOpen, color: 'blue' },
  literature_review: { label: 'Literature Review', labelZh: '文献综述', icon: FileText, color: 'purple' },
  methodology: { label: 'Methodology', labelZh: '方法论', icon: Beaker, color: 'green' },
  results: { label: 'Results', labelZh: '结果', icon: BarChart3, color: 'orange' },
  discussion: { label: 'Discussion', labelZh: '讨论', icon: MessageSquare, color: 'yellow' },
  conclusion: { label: 'Conclusion', labelZh: '结论', icon: CheckSquare, color: 'red' },
  body: { label: 'Body', labelZh: '正文', icon: FileText, color: 'gray' },
  unknown: { label: 'Unknown', labelZh: '未知', icon: FileText, color: 'gray' },
};

interface LayerStep2_0Props {
  documentIdProp?: string;
  onComplete?: (result: SectionIdentificationResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep2_0({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep2_0Props) {
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
      sessionApi.updateStep(sessionId, 'layer4-step2-0').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<SectionIdentificationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedSectionIndex, setExpandedSectionIndex] = useState<number | null>(null);
  const [editingRole, setEditingRole] = useState<number | null>(null);

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
      const analysisResult = await sectionLayerApi.identifySections(
        documentText,
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

  // Navigation handlers
  // 导航处理
  const handleBack = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer5-step1-5/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer4-step2-1/${documentId}?${params.toString()}`);
  };

  const toggleSection = (index: number) => {
    setExpandedSectionIndex(expandedSectionIndex === index ? null : index);
  };

  const handleRoleChange = (sectionIndex: number, newRole: string) => {
    if (result) {
      const updatedSections = result.sections.map((section: SectionInfo) =>
        section.index === sectionIndex ? { ...section, role: newRole, userAssignedRole: newRole } : section
      );
      setResult({ ...result, sections: updatedSections });
    }
    setEditingRole(null);
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

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      {/* 页头 */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Layers className="w-4 h-4" />
          <span>Layer 4 / 第4层</span>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Step 2.0 章节识别</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Section Identification & Role Labeling
        </h1>
        <p className="text-gray-600 mt-1">
          章节识别与角色标注 - 自动检测章节边界，识别每个章节的功能角色
        </p>
      </div>

      {/* Analysis Progress */}
      {/* 分析进度 */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Identifying sections... / 识别章节中...</p>
              <p className="text-blue-600 text-sm">Detecting boundaries and roles</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {/* 结果 */}
      {result && !isAnalyzing && (
        <>
          {/* Summary Stats */}
          {/* 统计摘要 */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg border bg-blue-50 border-blue-200">
              <div className="flex items-center gap-2 mb-2">
                <Layers className="w-5 h-5 text-blue-600" />
                <span className="font-medium text-gray-900">Total Sections / 章节数</span>
              </div>
              <div className="text-2xl font-bold text-blue-600">
                {result.sectionCount}
              </div>
            </div>

            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">Total Paragraphs</span>
              </div>
              <div className="text-2xl font-bold text-gray-700">
                {result.totalParagraphs}
              </div>
            </div>

            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">Total Words / 总词数</span>
              </div>
              <div className="text-2xl font-bold text-gray-700">
                {result.totalWords}
              </div>
            </div>

            <div className="p-4 rounded-lg border bg-green-50 border-green-200">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="font-medium text-gray-900">Status / 状态</span>
              </div>
              <div className="text-lg font-bold text-green-600">
                Ready / 就绪
              </div>
            </div>
          </div>

          {/* Section Structure */}
          {/* 章节结构 */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Layers className="w-5 h-5 text-blue-600" />
              Detected Section Structure / 检测到的章节结构
            </h3>
            <div className="space-y-2">
              {result.sections.map((section) => {
                const isExpanded = expandedSectionIndex === section.index;
                const isEditing = editingRole === section.index;
                const roleConfig = SECTION_ROLE_CONFIG[section.role] || SECTION_ROLE_CONFIG.unknown;
                const RoleIcon = roleConfig.icon;

                return (
                  <div
                    key={section.index}
                    className={clsx(
                      'border rounded-lg overflow-hidden',
                      `border-${roleConfig.color}-200`,
                      isExpanded ? `bg-${roleConfig.color}-50` : 'bg-white'
                    )}
                  >
                    <button
                      onClick={() => toggleSection(section.index)}
                      className={clsx(
                        'w-full px-4 py-3 flex items-center justify-between',
                        'hover:bg-gray-50 transition-colors'
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <div className={clsx(
                          'w-8 h-8 rounded-full flex items-center justify-center',
                          `bg-${roleConfig.color}-100`
                        )}>
                          <RoleIcon className={clsx('w-4 h-4', `text-${roleConfig.color}-600`)} />
                        </div>
                        <div className="text-left">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900">
                              Section {section.index + 1}
                            </span>
                            {!isEditing ? (
                              <span className={clsx(
                                'px-2 py-0.5 text-xs rounded-full',
                                `bg-${roleConfig.color}-100 text-${roleConfig.color}-700`
                              )}>
                                {roleConfig.labelZh} ({roleConfig.label})
                              </span>
                            ) : null}
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setEditingRole(isEditing ? null : section.index);
                              }}
                              className="p-1 hover:bg-gray-200 rounded"
                              title="Edit role / 编辑角色"
                            >
                              <Edit3 className="w-3 h-3 text-gray-500" />
                            </button>
                          </div>
                          <p className="text-sm text-gray-500">
                            Para {section.startParagraphIdx + 1}-{section.endParagraphIdx + 1} ({section.paragraphCount} paragraphs, {section.wordCount} words)
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={clsx(
                          'text-sm',
                          section.roleConfidence >= 0.9 ? 'text-green-600' :
                          section.roleConfidence >= 0.7 ? 'text-yellow-600' : 'text-red-600'
                        )}>
                          {Math.round(section.roleConfidence * 100)}% confidence
                        </span>
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                    </button>

                    {/* Role editing dropdown */}
                    {/* 角色编辑下拉框 */}
                    {isEditing && (
                      <div className="px-4 py-2 border-t bg-gray-50">
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(SECTION_ROLE_CONFIG).map(([role, config]) => (
                            <button
                              key={role}
                              onClick={() => handleRoleChange(section.index, role)}
                              className={clsx(
                                'px-3 py-1 rounded-full text-sm border',
                                section.role === role
                                  ? `bg-${config.color}-100 border-${config.color}-300 text-${config.color}-700`
                                  : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-100'
                              )}
                            >
                              {config.labelZh}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Expanded content */}
                    {/* 展开内容 */}
                    {isExpanded && (
                      <div className="px-4 py-3 border-t bg-white">
                        <div className="space-y-3">
                          <div>
                            <h4 className="text-sm font-medium text-gray-700 mb-1">
                              Preview / 预览
                            </h4>
                            <p className="text-gray-600 text-sm bg-gray-50 p-3 rounded">
                              {section.preview}...
                            </p>
                          </div>
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <span className="text-gray-500">Start / 起始：</span>
                              <span className="font-medium ml-1">Para {section.startParagraphIdx + 1}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">End / 结束：</span>
                              <span className="font-medium ml-1">Para {section.endParagraphIdx + 1}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">Words / 词数：</span>
                              <span className="font-medium ml-1">{section.wordCount}</span>
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

          {/* Info message */}
          {/* 提示信息 */}
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-blue-800">
                Review Section Structure / 检查章节结构
              </h3>
              <p className="text-blue-600 mt-1">
                Please verify the detected sections are correct. You can edit the role of each section
                by clicking the edit icon. The section structure will be used in all subsequent analyses.
              </p>
              <p className="text-blue-600 mt-1">
                请确认检测到的章节是否正确。您可以点击编辑图标修改每个章节的角色。
                章节结构将用于所有后续分析。
              </p>
            </div>
          </div>

          {/* Processing time */}
          {/* 处理时间 */}
          {result.processingTimeMs && (
            <p className="text-sm text-gray-500 mb-6">
              Analysis completed in {result.processingTimeMs}ms
            </p>
          )}
        </>
      )}

      {/* Navigation */}
      {/* 导航 */}
      {showNavigation && (
        <div className="flex items-center justify-between pt-6 border-t">
          <Button variant="secondary" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back: Layer 5 / 返回：第5层
          </Button>
          <Button variant="primary" onClick={handleNext} disabled={isAnalyzing || !result}>
            Next: Section Order / 下一步：章节顺序
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
