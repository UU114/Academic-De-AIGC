import { useEffect, useState, useRef, useCallback } from 'react';
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
  AlertTriangle,
  Sparkles,
  Upload,
  Check,
  X,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import { useSubstepStateStore } from '../../stores/substepStateStore';
import {
  sectionLayerApi,
  documentLayerApi,
  SectionIdentificationResponse,
  SectionInfo,
  DetectionIssue,
  IssueSuggestionResponse,
  ModifyPromptResponse,
  ApplyModifyResponse,
} from '../../services/analysisApi';

/**
 * Layer Step 2.0 - Section Identification & Role Labeling
 * 步骤 2.0 - 章节识别与角色标注
 *
 * This is the foundational step for Layer 4 (Section Level Analysis).
 * All subsequent Layer 4 steps depend on correct section identification.
 *
 * 这是第4层（章节级分析）的基础步骤。
 * 所有后续的第4层步骤都依赖于正确的章节识别。
 */

// Section role configuration
// 章节角色配置
const SECTION_ROLE_CONFIG: Record<string, { label: string; labelZh: string; icon: typeof BookOpen; color: string }> = {
  abstract: { label: 'Abstract', labelZh: '摘要', icon: FileText, color: 'cyan' },
  introduction: { label: 'Introduction', labelZh: '引言', icon: BookOpen, color: 'blue' },
  background: { label: 'Background', labelZh: '背景', icon: BookOpen, color: 'indigo' },
  literature_review: { label: 'Literature Review', labelZh: '文献综述', icon: FileText, color: 'purple' },
  methodology: { label: 'Methodology', labelZh: '方法论', icon: Beaker, color: 'green' },
  results: { label: 'Results', labelZh: '结果', icon: BarChart3, color: 'orange' },
  discussion: { label: 'Discussion', labelZh: '讨论', icon: MessageSquare, color: 'yellow' },
  conclusion: { label: 'Conclusion', labelZh: '结论', icon: CheckSquare, color: 'red' },
  references: { label: 'References', labelZh: '参考文献', icon: FileText, color: 'slate' },
  appendix: { label: 'Appendix', labelZh: '附录', icon: FileText, color: 'stone' },
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
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // Helper function to check if documentId is valid
  // 辅助函数：检查documentId是否有效
  const isValidDocumentId = (id: string | undefined): boolean => {
    return !!(id && id !== 'undefined' && id !== 'null');
  };

  // Get initial documentId, filtering out invalid values
  // 获取初始documentId，过滤掉无效值
  const getInitialDocumentId = (): string | undefined => {
    if (isValidDocumentId(documentIdProp)) return documentIdProp;
    if (isValidDocumentId(documentIdParam)) return documentIdParam;
    return undefined;
  };

  const [documentId, setDocumentId] = useState<string | undefined>(getInitialDocumentId());

  // Track whether we have attempted to fetch documentId from session
  // 跟踪是否已尝试从会话获取documentId
  const [sessionFetchAttempted, setSessionFetchAttempted] = useState(
    // If documentId is already available, no need to fetch from session
    // 如果documentId已可用，无需从session获取
    isValidDocumentId(documentIdProp) || isValidDocumentId(documentIdParam)
  );

  // If documentId is missing but sessionId exists, try to get documentId from session
  // 如果缺少documentId但有sessionId，尝试从会话获取documentId
  useEffect(() => {
    const fetchDocumentIdFromSession = async () => {
      if (!isValidDocumentId(documentId) && sessionId) {
        try {
          console.log('Fetching documentId from session:', sessionId);
          const sessionState = await sessionApi.getCurrent(sessionId);
          console.log('Session state received:', sessionState);
          if (sessionState.documentId) {
            setDocumentId(sessionState.documentId);
          }
        } catch (err) {
          console.error('Failed to get documentId from session:', err);
        }
      }
      // Mark that we've attempted to fetch, regardless of success
      // 无论是否成功，标记已尝试获取
      setSessionFetchAttempted(true);
    };

    // If no sessionId, we can't fetch from session, so mark as attempted
    // 如果没有sessionId，无法从session获取，直接标记为已尝试
    if (!sessionId) {
      setSessionFetchAttempted(true);
    } else if (!isValidDocumentId(documentId)) {
      fetchDocumentIdFromSession();
    } else {
      // documentId already exists, no need to fetch from session
      // documentId已存在，无需从session获取
      setSessionFetchAttempted(true);
    }
  }, [documentId, sessionId]);

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
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedSectionIndex, setExpandedSectionIndex] = useState<number | null>(null);
  const [editingRole, setEditingRole] = useState<number | null>(null);

  // Issues derived from analysis result
  // 从分析结果派生的问题列表
  const [sectionIssues, setSectionIssues] = useState<DetectionIssue[]>([]);

  // Issue selection for merge modify
  // 用于合并修改的问题选择
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());

  // Issue suggestion state (LLM-based detailed suggestions)
  // 问题建议状态（基于LLM的详细建议）
  const [issueSuggestion, setIssueSuggestion] = useState<IssueSuggestionResponse | null>(null);
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);

  // Merge modify state
  // 合并修改状态
  const [showMergeConfirm, setShowMergeConfirm] = useState(false);
  const [mergeMode, setMergeMode] = useState<'prompt' | 'apply'>('prompt');
  const [mergeUserNotes, setMergeUserNotes] = useState('');
  const [isMerging, setIsMerging] = useState(false);
  const [mergeResult, setMergeResult] = useState<ModifyPromptResponse | ApplyModifyResponse | null>(null);

  // Skip confirmation state
  // 跳过确认状态
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);

  // Document modification state
  // 文档修改状态
  const [modifyMode, setModifyMode] = useState<'file' | 'text'>('file');
  const [newFile, setNewFile] = useState<File | null>(null);
  const [newText, setNewText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isAnalyzingRef = useRef(false);

  // Load document - only after session fetch has been attempted
  // 加载文档 - 仅在尝试从session获取后
  useEffect(() => {
    // Wait for session fetch attempt to complete first
    // 首先等待session获取尝试完成
    if (!sessionFetchAttempted) {
      return;
    }

    if (isValidDocumentId(documentId)) {
      loadDocumentText(documentId!);
    } else {
      // Handle missing documentId (only after we've tried fetching from session)
      // 处理缺失的documentId（仅在尝试从session获取后）
      setError('Document ID not found in URL. Please navigate from Layer 5. / URL中缺少文档ID，请从第5层导航。');
      setIsLoading(false);
    }
  }, [documentId, sessionFetchAttempted]);

  // Get substep state store for checking previous step's modified text
  // 获取子步骤状态存储，用于检查前一个步骤的修改文本
  const substepStore = useSubstepStateStore();

  const loadDocumentText = async (docId: string) => {
    // Guard against invalid document IDs (including string "undefined")
    // 防止无效的文档ID（包括字符串"undefined"）
    if (!docId || docId === 'undefined' || docId === 'null') {
      console.error('Invalid document ID:', docId);
      setError('Invalid document ID. Please navigate from Layer 5. / 无效的文档ID，请从第5层导航。');
      setIsLoading(false);
      return;
    }

    try {
      // Initialize substep store for session if not already done
      // 如果尚未初始化，为会话初始化子步骤存储
      if (sessionId && substepStore.currentSessionId !== sessionId) {
        await substepStore.initForSession(sessionId);
      }

      // Check for modified text from Layer 5 steps (most recent first)
      // 检查来自第5层步骤的修改文本（最近的优先）
      // Priority: step1-5 > step1-4 > step1-3 > step1-2 > step1-1 > originalText
      const layer5Steps = ['step1-5', 'step1-4', 'step1-3', 'step1-2', 'step1-1'];
      let foundModifiedText: string | null = null;

      for (const stepName of layer5Steps) {
        const stepState = substepStore.getState(stepName);
        if (stepState?.modifiedText) {
          console.log(`[LayerStep2_0] Using modified text from ${stepName}`);
          foundModifiedText = stepState.modifiedText;
          break;
        }
      }

      if (foundModifiedText) {
        // Use modified text from previous layer
        // 使用前一层的修改文本
        setDocumentText(foundModifiedText);
      } else {
        // Fallback to original document text
        // 回退到原始文档文本
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
      const analysisResult = await sectionLayerApi.identifySections(
        documentText,
        undefined,
        sessionId || undefined
      );

      setResult(analysisResult);

      // Use issues from API response (LLM-detected) if available, otherwise generate locally
      // 优先使用API返回的issues（LLM检测），如果没有则本地生成
      let issues: DetectionIssue[] = [];

      if (analysisResult.issues && analysisResult.issues.length > 0) {
        // Use LLM-detected issues from API
        // 使用API返回的LLM检测的issues
        issues = analysisResult.issues;
      } else {
        // Fallback: generate issues locally (for backward compatibility)
        // 回退：本地生成issues（向后兼容）

        // Check for low confidence sections
        // 检查低置信度章节
        analysisResult.sections.forEach((section: SectionInfo) => {
          if (section.roleConfidence < 0.7) {
            issues.push({
              type: 'low_confidence_role',
              description: `Section ${section.index + 1} has low role confidence (${Math.round(section.roleConfidence * 100)}%)`,
              descriptionZh: `章节${section.index + 1}的角色置信度较低 (${Math.round(section.roleConfidence * 100)}%)`,
              severity: section.roleConfidence < 0.5 ? 'high' : 'medium',
              layer: 'section',
              location: `Section ${section.index + 1}: ${SECTION_ROLE_CONFIG[section.role]?.labelZh || section.role}`,
            });
          }

          if (section.role === 'unknown') {
            issues.push({
              type: 'unknown_role',
              description: `Section ${section.index + 1} has unknown role - may need manual labeling`,
              descriptionZh: `章节${section.index + 1}角色未知 - 可能需要手动标注`,
              severity: 'medium',
              layer: 'section',
              location: `Section ${section.index + 1}`,
            });
          }
        });

        // Check for very short or very long sections
        // 检查过短或过长的章节
        const avgWordCount = analysisResult.totalWords / analysisResult.sectionCount;
        analysisResult.sections.forEach((section: SectionInfo) => {
          if (section.wordCount < avgWordCount * 0.3) {
            issues.push({
              type: 'short_section',
              description: `Section ${section.index + 1} is unusually short (${section.wordCount} words)`,
              descriptionZh: `章节${section.index + 1}异常短 (${section.wordCount}词)`,
              severity: 'low',
              layer: 'section',
              location: `Section ${section.index + 1}`,
            });
          }
        });
      }

      setSectionIssues(issues);

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

  // Load detailed suggestion for selected issues (LLM-based)
  // 为选中的问题加载详细建议（基于LLM）
  const loadIssueSuggestion = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentText) return;

    setIsLoadingSuggestion(true);
    setSuggestionError(null);

    try {
      const selectedIssues = Array.from(selectedIssueIndices).map(i => sectionIssues[i]);
      const response = await documentLayerApi.getIssueSuggestion(
        documentText,
        selectedIssues,
        'step2_0',
        sessionId || undefined
      );
      setIssueSuggestion(response);
    } catch (err) {
      console.error('Failed to load suggestion:', err);
      setSuggestionError('Failed to load detailed suggestion / 加载详细建议失败');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [selectedIssueIndices, documentText, sectionIssues, sessionId]);

  // Handle issue selection toggle
  // 处理问题选择切换
  const handleIssueClick = useCallback((index: number) => {
    setSelectedIssueIndices(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
    setIssueSuggestion(null);
    setMergeResult(null);
  }, []);

  // Select all issues
  // 全选所有问题
  const selectAllIssues = useCallback(() => {
    setSelectedIssueIndices(new Set(sectionIssues.map((_, idx) => idx)));
  }, [sectionIssues]);

  // Deselect all issues
  // 取消全选所有问题
  const deselectAllIssues = useCallback(() => {
    setSelectedIssueIndices(new Set());
  }, []);

  // Execute merge modify (generate prompt or apply modification)
  // 执行合并修改（生成提示或应用修改）
  const executeMergeModify = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentId) return;

    setIsMerging(true);
    setShowMergeConfirm(false);

    try {
      const selectedIssues = Array.from(selectedIssueIndices).map(i => sectionIssues[i]);

      if (mergeMode === 'prompt') {
        const response = await documentLayerApi.generateModifyPrompt(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult(response);
      } else {
        const response = await documentLayerApi.applyModify(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult(response);
      }
    } catch (err) {
      console.error('Merge modify failed:', err);
      setError('Merge modify failed / 合并修改失败');
    } finally {
      setIsMerging(false);
    }
  }, [selectedIssueIndices, documentId, sectionIssues, mergeMode, mergeUserNotes, sessionId]);

  // Handle regenerate
  // 处理重新生成
  const handleRegenerate = useCallback(() => {
    setMergeResult(null);
    setShowMergeConfirm(true);
    setMergeMode('apply');
  }, []);

  // Handle accept modification
  // 处理接受修改
  const handleAcceptModification = useCallback(() => {
    if (mergeResult && 'modifiedText' in mergeResult && mergeResult.modifiedText) {
      setNewText(mergeResult.modifiedText);
      setModifyMode('text');
      setMergeResult(null);
    }
  }, [mergeResult]);

  // Handle file selection
  // 处理文件选择
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setNewFile(file);
    }
  }, []);

  // Handle confirm modification and navigate to next step
  // 处理确认修改并导航到下一步
  const handleConfirmModify = useCallback(async () => {
    setIsUploading(true);
    setError(null);

    try {
      let modifiedText: string = '';

      if (modifyMode === 'file' && newFile) {
        // Read file content to save to substep store
        // 读取文件内容以保存到子步骤存储
        modifiedText = await newFile.text();
      } else if (modifyMode === 'text' && newText.trim()) {
        modifiedText = newText.trim();
      } else {
        setError('Please select a file or enter text / 请选择文件或输入文本');
        setIsUploading(false);
        return;
      }

      // Save modified text to substep store for next steps to use
      // 保存修改后的文本到子步骤存储，供后续步骤使用
      if (sessionId && modifiedText) {
        await substepStore.saveModifiedText('step2-0', modifiedText);
        await substepStore.markCompleted('step2-0');
        console.log('[LayerStep2_0] Saved modified text to substep store');
      }

      // Navigate to next step with same document ID
      // 使用相同的文档ID导航到下一步（下一步会从substep store获取修改后的文本）
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer4-step2-1/${documentId}?${params.toString()}`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to save modified document / 保存修改后的文档失败');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate, documentId, substepStore]);

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

  const hasSelectedIssues = selectedIssueIndices.size > 0;

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
  if (error && !result) {
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
      {/* Loading Overlay for LLM operations */}
      {/* LLM操作加载遮罩 */}
      <LoadingOverlay
        isVisible={isMerging}
        operationType={mergeMode}
        issueCount={selectedIssueIndices.size}
      />

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

      {/* Start Analysis / Skip Step */}
      {/* 开始分析 / 跳过此步 */}
      {documentText && !analysisStarted && !isAnalyzing && !result && (
        <div className="mb-6 p-6 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="text-center">
            <Layers className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Analyze / 准备分析</h3>
            <p className="text-gray-600 mb-6">
              Click to identify sections and assign roles (introduction, methodology, results, etc.)
              <br />
              <span className="text-gray-500">点击开始识别章节并分配角色（引言、方法论、结果等）</span>
            </p>
            <div className="flex items-center justify-center gap-4">
              <Button variant="primary" size="lg" onClick={() => setAnalysisStarted(true)}>
                <Sparkles className="w-5 h-5 mr-2" />
                Start Analysis / 开始分析
              </Button>
              <Button variant="secondary" size="lg" onClick={() => setShowSkipConfirm(true)}>
                <ArrowRight className="w-5 h-5 mr-2" />
                Skip Step / 跳过此步
              </Button>
            </div>
          </div>
        </div>
      )}

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

          {/* Issues Section with Selection */}
          {/* 问题部分（带选择功能） */}
          {sectionIssues.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                  Detected Issues / 检测到的问题
                  <span className="text-sm font-normal text-gray-500">
                    ({selectedIssueIndices.size}/{sectionIssues.length} selected / 已选择)
                  </span>
                </h3>
                <div className="flex items-center gap-2">
                  {/* Select All / Deselect All buttons */}
                  {/* 全选/取消全选按钮 */}
                  <Button variant="secondary" size="sm" onClick={selectAllIssues}>
                    Select All / 全选
                  </Button>
                  <Button variant="secondary" size="sm" onClick={deselectAllIssues}>
                    Deselect All / 取消全选
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                {sectionIssues.map((issue, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleIssueClick(idx)}
                    className={clsx(
                      'w-full text-left p-3 rounded-lg border transition-all',
                      selectedIssueIndices.has(idx)
                        ? 'bg-blue-50 border-blue-300 ring-2 ring-blue-200'
                        : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <div className={clsx(
                        'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5',
                        selectedIssueIndices.has(idx)
                          ? 'bg-blue-600 border-blue-600'
                          : 'border-gray-300'
                      )}>
                        {selectedIssueIndices.has(idx) && (
                          <Check className="w-3 h-3 text-white" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className={clsx(
                            'px-2 py-0.5 rounded text-xs font-medium',
                            issue.severity === 'high' ? 'bg-red-100 text-red-700' :
                            issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-700'
                          )}>
                            {issue.severity === 'high' ? 'High / 高' :
                             issue.severity === 'medium' ? 'Medium / 中' : 'Low / 低'}
                          </span>
                          <span className="text-xs text-gray-500">{issue.layer}</span>
                        </div>
                        <p className="text-gray-900 mt-1">{issue.description}</p>
                        <p className="text-gray-600 text-sm">{issue.descriptionZh}</p>
                        {issue.location && (
                          <p className="text-gray-500 text-xs mt-1 font-mono">{issue.location}</p>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons for Selected Issues */}
          {/* 选中问题的操作按钮 - Style matched with LayerStep1_1 */}
          {sectionIssues.length > 0 && (
            <div className="mb-6 pb-6 border-b">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  {selectedIssueIndices.size} selected / 已选择 {selectedIssueIndices.size} 个问题
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={loadIssueSuggestion}
                    disabled={selectedIssueIndices.size === 0 || isLoadingSuggestion}
                  >
                    {isLoadingSuggestion ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Sparkles className="w-4 h-4 mr-2" />
                    )}
                    Load Suggestions / 加载建议
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setMergeMode('prompt');
                      setShowMergeConfirm(true);
                    }}
                    disabled={selectedIssueIndices.size === 0}
                  >
                    <Edit3 className="w-4 h-4 mr-2" />
                    Generate Prompt / 生成提示
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                      setMergeMode('apply');
                      setShowMergeConfirm(true);
                    }}
                    disabled={selectedIssueIndices.size === 0}
                  >
                    <Sparkles className="w-4 h-4 mr-2" />
                    AI Modify / AI修改
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Suggestion Error */}
          {suggestionError && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-red-600">{suggestionError}</p>
                <Button
                  variant="secondary"
                  size="sm"
                  className="mt-2"
                  onClick={() => setSuggestionError(null)}
                >
                  Dismiss / 关闭
                </Button>
              </div>
            </div>
          )}

          {/* Issue Suggestion Display (LLM-based) */}
          {/* 问题建议展示（基于LLM） */}
          {issueSuggestion && (
            <div className="mb-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <h4 className="font-semibold text-purple-900 mb-3 flex items-center gap-2">
                <Sparkles className="w-5 h-5" />
                AI Suggestions / AI建议
              </h4>
              <div className="space-y-3">
                <div>
                  <h5 className="text-sm font-medium text-purple-800">Analysis / 分析:</h5>
                  <p className="text-purple-700 mt-1">{issueSuggestion.analysis}</p>
                </div>
                {issueSuggestion.suggestions && issueSuggestion.suggestions.length > 0 && (
                  <div>
                    <h5 className="text-sm font-medium text-purple-800">Suggestions / 建议:</h5>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                      {issueSuggestion.suggestions.map((s, i) => (
                        <li key={i} className="text-purple-700">{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {issueSuggestion.exampleFix && (
                  <div>
                    <h5 className="text-sm font-medium text-purple-800">Example Fix / 示例修复:</h5>
                    <pre className="mt-1 p-2 bg-white rounded text-sm text-gray-800 overflow-x-auto">
                      {issueSuggestion.exampleFix}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Merge Confirm Dialog */}
          {/* 合并确认对话框 */}
          {showMergeConfirm && (
            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h4 className="font-semibold text-yellow-900 mb-3">
                {mergeMode === 'prompt' ? 'Generate Modification Prompt / 生成修改提示' : 'Apply AI Modification / 应用AI修改'}
              </h4>
              <p className="text-yellow-800 text-sm mb-3">
                {mergeMode === 'prompt'
                  ? 'Generate a prompt that you can use to modify the document manually / 生成一个提示，您可以用它来手动修改文档'
                  : 'AI will automatically modify the document based on selected issues / AI将根据选中的问题自动修改文档'}
              </p>
              <div className="mb-3">
                <label className="block text-sm font-medium text-yellow-800 mb-1">
                  Additional Notes (Optional) / 附加说明（可选）
                </label>
                <textarea
                  value={mergeUserNotes}
                  onChange={(e) => setMergeUserNotes(e.target.value)}
                  placeholder="Add any specific instructions for modification... / 添加任何特定的修改指示..."
                  className="w-full px-3 py-2 border border-yellow-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500"
                  rows={2}
                />
              </div>
              <div className="flex gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={executeMergeModify}
                  disabled={isMerging}
                >
                  {isMerging ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Check className="w-4 h-4 mr-2" />
                  )}
                  Confirm / 确认
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setShowMergeConfirm(false)}
                >
                  <X className="w-4 h-4 mr-2" />
                  Cancel / 取消
                </Button>
              </div>
            </div>
          )}

          {/* Merge Result Display */}
          {/* 合并结果展示 */}
          {mergeResult && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                <CheckCircle className="w-5 h-5" />
                {'modifiedText' in mergeResult ? 'AI Modification Result / AI修改结果' : 'Generated Prompt / 生成的提示'}
              </h4>

              {'prompt' in mergeResult && mergeResult.prompt && (
                <div className="mb-3">
                  <h5 className="text-sm font-medium text-green-800">Prompt / 提示:</h5>
                  <pre className="mt-1 p-3 bg-white rounded text-sm text-gray-800 overflow-x-auto whitespace-pre-wrap">
                    {mergeResult.prompt}
                  </pre>
                </div>
              )}

              {'modifiedText' in mergeResult && mergeResult.modifiedText && (
                <div className="mb-3">
                  {/* Modified text display - full content with scrollable area */}
                  {/* 修改后内容显示 - 完整内容可滚动 */}
                  <h5 className="text-sm font-medium text-green-800">
                    Modified Text / 修改后的文本 ({mergeResult.modifiedText?.length || 0} 字符):
                  </h5>
                  <pre className="mt-1 p-3 bg-white rounded text-sm text-gray-800 overflow-x-auto whitespace-pre-wrap max-h-96 overflow-y-auto">
                    {mergeResult.modifiedText}
                  </pre>
                </div>
              )}

              {'changesSummary' in mergeResult && mergeResult.changesSummary && (
                <div className="mb-3">
                  <h5 className="text-sm font-medium text-green-800">Changes Summary / 修改摘要:</h5>
                  <p className="mt-1 text-green-700">{mergeResult.changesSummary}</p>
                </div>
              )}

              {'modifiedText' in mergeResult && (
                <div className="flex gap-2 mt-4">
                  <Button variant="primary" size="sm" onClick={handleAcceptModification}>
                    <Check className="w-4 h-4 mr-2" />
                    Accept / 接受
                  </Button>
                  <Button variant="secondary" size="sm" onClick={handleRegenerate}>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Regenerate / 重新生成
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => setMergeResult(null)}>
                    <X className="w-4 h-4 mr-2" />
                    Cancel / 取消
                  </Button>
                </div>
              )}
            </div>
          )}

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
                    <div
                      onClick={() => toggleSection(section.index)}
                      className={clsx(
                        'w-full px-4 py-3 flex items-center justify-between cursor-pointer',
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
                            {/* Display original title instead of role label */}
                            {/* 显示原始标题而非角色标签 */}
                            {!isEditing && section.title ? (
                              <span className={clsx(
                                'px-2 py-0.5 text-xs rounded-full',
                                `bg-${roleConfig.color}-100 text-${roleConfig.color}-700`
                              )}>
                                {section.title}
                              </span>
                            ) : !isEditing ? (
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
                    </div>

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

          {/* No issues message */}
          {sectionIssues.length === 0 && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">
                  Section Structure Looks Good
                </h3>
                <p className="text-green-600 mt-1">
                  章节结构良好。所有章节角色识别置信度正常。
                </p>
              </div>
            </div>
          )}

          {/* Document Modification Section */}
          {/* 文档修改部分 */}
          <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Document Modification / 文档修改
            </h3>
            <p className="text-gray-600 text-sm mb-4">
              Upload a modified file or paste modified text to continue to the next step.
              上传修改后的文件或粘贴修改后的文本以继续下一步。
            </p>

            {/* Mode Toggle */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setModifyMode('file')}
                className={clsx(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  modifyMode === 'file'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                )}
              >
                <Upload className="w-4 h-4 inline mr-2" />
                Upload File / 上传文件
              </button>
              <button
                onClick={() => setModifyMode('text')}
                className={clsx(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  modifyMode === 'text'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                )}
              >
                <Edit3 className="w-4 h-4 inline mr-2" />
                Input Text / 输入文本
              </button>
            </div>

            {/* File Upload Mode */}
            {modifyMode === 'file' && (
              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.md,.doc,.docx"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
                >
                  <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-600">
                    {newFile ? newFile.name : 'Click to select file / 点击选择文件'}
                  </p>
                  <p className="text-gray-400 text-sm mt-1">
                    Supported: .txt, .md, .doc, .docx
                  </p>
                </div>
              </div>
            )}

            {/* Text Input Mode */}
            {modifyMode === 'text' && (
              <div>
                <textarea
                  value={newText}
                  onChange={(e) => setNewText(e.target.value)}
                  placeholder="Paste modified text here... / 在此粘贴修改后的文本..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-[200px]"
                />
                <p className="text-gray-500 text-sm mt-1">
                  {newText.length} characters / 字符
                </p>
              </div>
            )}

            {/* Apply and Continue Button - Style matched with LayerStep1_1 */}
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-gray-500">
                {modifyMode === 'file'
                  ? (newFile ? 'File selected, ready to apply / 文件已选择，可以应用' : 'Please select a file first / 请先选择文件')
                  : (newText.trim() ? 'Content entered, ready to apply / 内容已输入，可以应用' : 'Please enter content first / 请先输入内容')}
              </p>
              <Button
                variant="primary"
                onClick={handleConfirmModify}
                disabled={isUploading || (modifyMode === 'file' && !newFile) || (modifyMode === 'text' && !newText.trim())}
              >
                {isUploading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <ArrowRight className="w-4 h-4 mr-2" />
                )}
                Apply and Continue / 应用并继续
              </Button>
            </div>

            {/* Error Display */}
            {error && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}
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

      {/* Skip Confirmation Dialog */}
      {/* 跳过确认对话框 */}
      {showSkipConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl">
            <div className="flex items-start gap-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-yellow-600 flex-shrink-0" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Skip without modifying? / 跳过不修改？
                </h3>
                <p className="text-gray-600 mt-2">
                  You have not applied any modifications on this page. Are you sure you want to skip to the next step?
                </p>
                <p className="text-gray-600 mt-1">
                  您尚未在此页面应用任何修改。确定要跳过到下一步吗？
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <Button
                variant="secondary"
                onClick={() => setShowSkipConfirm(false)}
              >
                Cancel / 取消
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  setShowSkipConfirm(false);
                  handleNext();
                }}
              >
                Confirm Skip / 确认跳过
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      {/* 导航 */}
      {showNavigation && (
        <div className="flex items-center justify-between pt-6 border-t">
          <Button variant="secondary" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back: Layer 5 / 返回：第5层
          </Button>
          <Button
            variant="primary"
            onClick={() => setShowSkipConfirm(true)}
            disabled={isAnalyzing || !result}
          >
            Skip and Continue / 跳过并继续
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
