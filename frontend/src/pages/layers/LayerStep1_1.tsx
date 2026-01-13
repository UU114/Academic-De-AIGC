import { useEffect, useState, useRef, useCallback } from 'react';
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
  Sparkles,
  Wand2,
  Copy,
  Check,
  X,
  Upload,
  Type,
  Square,
  CheckSquare,
  RotateCcw,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import { documentLayerApi, DocumentAnalysisResponse, DetectionIssue } from '../../services/analysisApi';
// ============================================
// NEW CODE - Import substep state store for caching
// 新代码 - 导入子步骤状态存储用于缓存
// ============================================
import { useSubstepStateStore } from '../../stores/substepStateStore';
// ============================================

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
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Processing mode and session from URL parameter
  // 从URL参数获取处理模式和会话ID
  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // ============================================
  // NEW CODE - Substep state caching setup
  // 新代码 - 子步骤状态缓存设置
  // ============================================
  // Step name for caching
  // 用于缓存的步骤名称
  const STEP_NAME = 'layer5-step1-1';

  // Substep state store for caching
  // 子步骤状态存储用于缓存
  const {
    initForSession,
    getState: getCachedState,
    hasState: hasCachedState,
    saveAnalysisResult,
    saveUserInputs,
  } = useSubstepStateStore();
  // ============================================

  // Helper function to check if documentId is valid
  // 辅助函数：检查documentId是否有效
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

  // Fetch documentId from session if not available
  // 如果documentId不可用，从session获取
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

  // Update session step on mount and init substep state store
  // 挂载时更新会话步骤并初始化子步骤状态存储
  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer5-step1-1').catch(console.error);

      // ============================================
      // # OLD CODE - No substep state initialization
      // # 旧代码 - 无子步骤状态初始化
      // ============================================
      // # (No additional code)
      // ============================================

      // ============================================
      // NEW CODE - Initialize substep state store
      // 新代码 - 初始化子步骤状态存储
      // ============================================
      initForSession(sessionId).catch(console.error);
      // ============================================
    }
  }, [sessionId, initForSession]);

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

  // Issue selection for merge modify
  // 问题选择（用于合并修改）
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());

  // Issue suggestion state
  // 问题建议状态
  const [issueSuggestion, setIssueSuggestion] = useState<{
    diagnosisZh: string;
    strategies: Array<{
      nameZh: string;
      descriptionZh: string;
      exampleBefore?: string;
      exampleAfter?: string;
      difficulty: string;
      effectiveness: number;
    }>;
    modificationPrompt: string;
    priorityTipsZh: string[];
    cautionZh: string;
  } | null>(null);
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);

  // Merge modify state
  // 合并修改状态
  const [showMergeConfirm, setShowMergeConfirm] = useState(false);
  const [mergeMode, setMergeMode] = useState<'prompt' | 'apply'>('prompt');
  const [mergeUserNotes, setMergeUserNotes] = useState('');
  const [isMerging, setIsMerging] = useState(false);
  const [mergeResult, setMergeResult] = useState<{
    type: 'prompt' | 'apply';
    prompt?: string;
    promptZh?: string;
    modifiedText?: string;
    changesSummaryZh?: string;
    changesCount?: number;
    remainingAttempts?: number;
    colloquialismLevel?: number;
  } | null>(null);
  const [copiedMergePrompt, setCopiedMergePrompt] = useState(false);
  const [regenerateCount, setRegenerateCount] = useState(0);
  const MAX_REGENERATE = 3;

  // Document modification state
  // 文档修改状态
  const [modifyMode, setModifyMode] = useState<'file' | 'text'>('file');
  const [newFile, setNewFile] = useState<File | null>(null);
  const [newText, setNewText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Prevent duplicate API calls
  // 防止重复API调用
  const isAnalyzingRef = useRef(false);

  // Load document text
  // 加载文档文本 - wait for session fetch to complete first
  // Load document text - 首先等待 session 获取完成
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
      let analysisResult: DocumentAnalysisResponse;

      // ============================================
      // # OLD CODE - Direct API call without caching
      // # 旧代码 - 直接调用API，无缓存
      // ============================================
      // # const analysisResult = await documentLayerApi.analyzeStructure(documentText);
      // # setResult(analysisResult);
      // ============================================

      // ============================================
      // NEW CODE - With substep state caching
      // 新代码 - 带子步骤状态缓存
      // ============================================
      // Check if we have cached state for this step
      // 检查是否有此步骤的缓存状态
      const cachedState = getCachedState(STEP_NAME);
      if (cachedState?.analysisResult) {
        console.log('[LayerStep1_1] Using cached analysis result');
        // Use cached result
        // 使用缓存结果
        analysisResult = cachedState.analysisResult as DocumentAnalysisResponse;

        // Restore user selections if available
        // 如果可用，恢复用户选择
        if (cachedState.userInputs?.selectedIssueIndices) {
          const cachedIndices = cachedState.userInputs.selectedIssueIndices as number[];
          setSelectedIssueIndices(new Set(cachedIndices));
        }
      } else {
        console.log('[LayerStep1_1] Calling API for fresh analysis');
        // Call structure analysis API
        // 调用结构分析API
        analysisResult = await documentLayerApi.analyzeStructure(documentText);

        // Save to cache
        // 保存到缓存
        if (sessionId) {
          await saveAnalysisResult(STEP_NAME, analysisResult as unknown as Record<string, unknown>);
        }
      }
      // ============================================

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

      // Filter structure-related issues (Step 1.1 focuses on document structure)
      // 过滤结构相关问题（步骤1.1聚焦于文档结构）
      const structureRelatedIssues = analysisResult.issues.filter(
        (issue) =>
          issue.type.includes('predictable') ||
          issue.type.includes('order') ||
          issue.type.includes('structure') ||
          issue.type.includes('formulaic') ||
          issue.type.includes('linear') ||
          issue.type.includes('flow') ||
          issue.type.includes('repetitive') ||
          issue.type.includes('pattern') ||
          issue.type.includes('uniform') ||
          issue.type.includes('symmetry') ||
          issue.type.includes('length')
      );
      setOrderIssues(structureRelatedIssues);

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

  // Toggle issue selection
  // 切换问题选择
  const toggleIssueSelection = (index: number) => {
    const newSelected = new Set(selectedIssueIndices);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedIssueIndices(newSelected);

    // ============================================
    // # OLD CODE - No persistence of user selection
    // # 旧代码 - 用户选择不持久化
    // ============================================
    // # (No additional code - selection was only in memory)
    // # (无额外代码 - 选择仅保存在内存中)
    // ============================================

    // ============================================
    // NEW CODE - Save user selection to cache
    // 新代码 - 保存用户选择到缓存
    // ============================================
    if (sessionId) {
      saveUserInputs(STEP_NAME, {
        selectedIssueIndices: Array.from(newSelected),
      }).catch(console.error);
    }
    // ============================================
  };

  // Load suggestion for a specific issue (without toggling expand)
  // 为特定问题加载建议（不切换展开状态）
  const loadIssueSuggestion = useCallback(async (index: number) => {
    const issue = orderIssues[index];
    if (!issue || !documentId) return;

    setIsLoadingSuggestion(true);
    setIssueSuggestion(null);

    try {
      const suggestion = await documentLayerApi.getIssueSuggestion(documentId, issue, false);
      setIssueSuggestion(suggestion);
    } catch (err) {
      console.error('Failed to load issue suggestion:', err);
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [orderIssues, documentId]);

  // Handle issue click - toggle expand and load suggestion
  // 处理问题点击 - 切换展开并加载建议
  const handleIssueClick = useCallback(async (index: number) => {
    const issue = orderIssues[index];
    if (!issue || !documentId) return;

    // Collapse if already expanded
    if (expandedIssueIndex === index) {
      setExpandedIssueIndex(null);
      setIssueSuggestion(null);
      return;
    }

    // Expand and load suggestion
    setExpandedIssueIndex(index);
    await loadIssueSuggestion(index);
  }, [orderIssues, documentId, expandedIssueIndex, loadIssueSuggestion]);

  // Execute merge modify
  // 执行合并修改
  const executeMergeModify = useCallback(async () => {
    if (!documentId || selectedIssueIndices.size === 0) return;

    const selectedIssues = Array.from(selectedIssueIndices).map(idx => orderIssues[idx]);

    setIsMerging(true);
    setShowMergeConfirm(false);

    try {
      if (mergeMode === 'prompt') {
        // Generate prompt mode
        const response = await documentLayerApi.generateModifyPrompt(
          documentId,
          selectedIssues,
          { sessionId: sessionId || undefined, userNotes: mergeUserNotes || undefined }
        );
        setMergeResult({
          type: 'prompt',
          prompt: response.prompt,
          promptZh: response.promptZh,
          colloquialismLevel: response.colloquialismLevel,
        });
      } else {
        // AI direct modify mode
        const response = await documentLayerApi.applyModify(
          documentId,
          selectedIssues,
          { sessionId: sessionId || undefined, userNotes: mergeUserNotes || undefined }
        );
        setMergeResult({
          type: 'apply',
          modifiedText: response.modifiedText,
          changesSummaryZh: response.changesSummaryZh,
          changesCount: response.changesCount,
          remainingAttempts: response.remainingAttempts,
          colloquialismLevel: response.colloquialismLevel,
        });
        setRegenerateCount(1);
      }
    } catch (err) {
      console.error('Merge modify failed:', err);
      alert('操作失败，请重试 / Operation failed, please try again');
    } finally {
      setIsMerging(false);
    }
  }, [documentId, selectedIssueIndices, orderIssues, mergeMode, mergeUserNotes, sessionId]);

  // Handle regenerate
  // 处理重新生成
  const handleRegenerate = useCallback(async () => {
    if (regenerateCount >= MAX_REGENERATE || !documentId || selectedIssueIndices.size === 0) return;

    const selectedIssues = Array.from(selectedIssueIndices).map(idx => orderIssues[idx]);

    setIsMerging(true);

    try {
      const response = await documentLayerApi.applyModify(
        documentId,
        selectedIssues,
        { sessionId: sessionId || undefined, userNotes: mergeUserNotes || undefined }
      );
      setMergeResult({
        type: 'apply',
        modifiedText: response.modifiedText,
        changesSummaryZh: response.changesSummaryZh,
        changesCount: response.changesCount,
        remainingAttempts: response.remainingAttempts,
        colloquialismLevel: response.colloquialismLevel,
      });
      setRegenerateCount(prev => prev + 1);
    } catch (err) {
      console.error('Regenerate failed:', err);
      alert('重新生成失败，请重试 / Regeneration failed, please try again');
    } finally {
      setIsMerging(false);
    }
  }, [documentId, regenerateCount, selectedIssueIndices, orderIssues, sessionId, mergeUserNotes]);

  // Handle accept modification - fill into text input and scroll
  // 处理接受修改 - 填入文本输入框并滚动
  const handleAcceptModification = useCallback(() => {
    if (mergeResult?.modifiedText) {
      setNewText(mergeResult.modifiedText);
      setModifyMode('text');
      setMergeResult(null);
      // Scroll to the document modification section
      setTimeout(() => {
        const modifySection = document.getElementById('modify-section');
        if (modifySection) {
          modifySection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
    }
  }, [mergeResult?.modifiedText]);

  // Handle confirm modify
  // 处理确认修改
  const handleConfirmModify = useCallback(async () => {
    if (modifyMode === 'file' && !newFile) {
      setUploadError('请选择一个文件 / Please select a file');
      return;
    }

    if (modifyMode === 'text' && !newText.trim()) {
      setUploadError('请输入文本内容 / Please enter text content');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      let newDocumentId: string;

      if (modifyMode === 'file' && newFile) {
        const result = await documentApi.upload(newFile);
        newDocumentId = result.id;
      } else {
        const result = await documentApi.uploadText(newText);
        newDocumentId = result.id;
      }

      // Navigate to Step 1.2 with new document
      const sessionParam = sessionId ? `&session=${sessionId}` : '';
      navigate(`/flow/layer5-step1-2/${newDocumentId}?mode=${mode}${sessionParam}`);
    } catch (err) {
      setUploadError((err as Error).message || '上传失败，请重试 / Upload failed, please try again');
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, sessionId, mode, navigate]);

  // Validate and set file
  // 验证并设置文件
  const validateAndSetFile = (selectedFile: File) => {
    const allowedTypes = [
      'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(selectedFile.type)) {
      setUploadError('仅支持 TXT 和 DOCX 格式 / Only TXT and DOCX formats are supported');
      return;
    }

    if (selectedFile.size > maxSize) {
      setUploadError('文件大小不能超过 10MB / File size cannot exceed 10MB');
      return;
    }

    setNewFile(selectedFile);
    setUploadError(null);
  };

  // Handle file change
  // 处理文件变化
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  // Copy prompt to clipboard
  // 复制提示词到剪贴板
  const copyToClipboard = (text: string, setCopied: (value: boolean) => void) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
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
      {/* Loading Overlay for LLM operations */}
      {/* LLM操作加载遮罩 */}
      <LoadingOverlay
        isVisible={isMerging}
        operationType={mergeMode}
        issueCount={selectedIssueIndices.size}
      />

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
                  const isSelected = selectedIssueIndices.has(idx);
                  return (
                    <div
                      key={idx}
                      className={clsx('border rounded-lg overflow-hidden', severityColor)}
                    >
                      <div className="flex items-start">
                        {/* Selection checkbox */}
                        <button
                          onClick={() => toggleIssueSelection(idx)}
                          className="p-4 hover:bg-white/50 transition-colors"
                        >
                          {isSelected ? (
                            <CheckSquare className="w-5 h-5 text-blue-600" />
                          ) : (
                            <Square className="w-5 h-5 text-gray-400" />
                          )}
                        </button>

                        {/* Issue content */}
                        <button
                          onClick={() => handleIssueClick(idx)}
                          className="flex-1 px-4 py-3 flex items-center justify-between hover:opacity-90 transition-opacity text-left"
                        >
                          <div className="flex items-center gap-3">
                            <AlertCircle className={clsx('w-5 h-5', severityTextColor)} />
                            <div>
                              <p className={clsx('font-medium', severityTextColor)}>
                                {issue.descriptionZh || issue.description}
                              </p>
                              <p className="text-sm text-gray-600 mt-0.5">
                                Severity: {issue.severity.toUpperCase()}
                              </p>
                            </div>
                          </div>
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0 ml-2" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0 ml-2" />
                          )}
                        </button>
                      </div>

                      {/* Expanded content with detailed suggestion */}
                      {isExpanded && (
                        <div className="px-4 py-3 border-t border-current border-opacity-20">
                          {isLoadingSuggestion && (
                            <div className="flex items-center justify-center py-6">
                              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                              <span className="ml-2 text-gray-600">Loading suggestion...</span>
                            </div>
                          )}

                          {!isLoadingSuggestion && issueSuggestion && (
                            <div className="space-y-4">
                              {/* Diagnosis */}
                              <div>
                                <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                  诊断 / Diagnosis
                                </h4>
                                <p className="text-sm text-gray-700">
                                  {issueSuggestion.diagnosisZh}
                                </p>
                              </div>

                              {/* Strategies */}
                              {issueSuggestion.strategies && issueSuggestion.strategies.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                    修改策略 / Modification Strategies
                                  </h4>
                                  <div className="space-y-3">
                                    {issueSuggestion.strategies.map((strategy, sIdx) => (
                                      <div key={sIdx} className="bg-white p-3 rounded border border-gray-200">
                                        <div className="flex items-center justify-between mb-2">
                                          <h5 className="font-medium text-gray-900">{strategy.nameZh}</h5>
                                          <span className="text-xs text-gray-500">
                                            效果: {strategy.effectiveness}/100
                                          </span>
                                        </div>
                                        <p className="text-sm text-gray-600 mb-2">
                                          {strategy.descriptionZh}
                                        </p>
                                        {strategy.exampleBefore && strategy.exampleAfter && (
                                          <div className="mt-2 text-xs space-y-1">
                                            <div>
                                              <span className="text-red-600">修改前: </span>
                                              <span className="text-gray-700">{strategy.exampleBefore}</span>
                                            </div>
                                            <div>
                                              <span className="text-green-600">修改后: </span>
                                              <span className="text-gray-700">{strategy.exampleAfter}</span>
                                            </div>
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Priority Tips */}
                              {issueSuggestion.priorityTipsZh && issueSuggestion.priorityTipsZh.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                    优先建议 / Priority Tips
                                  </h4>
                                  <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                                    {issueSuggestion.priorityTipsZh.map((tip, tIdx) => (
                                      <li key={tIdx}>{tip}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}

                          {!isLoadingSuggestion && !issueSuggestion && (
                            <button
                              onClick={() => loadIssueSuggestion(idx)}
                              className="w-full text-left text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 p-2 rounded transition-colors"
                            >
                              🔍 点击加载详细建议 / Click to load detailed suggestion
                            </button>
                          )}
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

          {/* Batch操作 Actions */}
          {orderIssues.length > 0 && (
            <div className="mb-6 pb-6 border-b">
              <div className="flex items-center justify-between mb-4">
                <div className="text-sm text-gray-600">
                  {selectedIssueIndices.size} selected / 已选择 {selectedIssueIndices.size} 个问题
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setMergeMode('prompt');
                      setShowMergeConfirm(true);
                    }}
                    disabled={selectedIssueIndices.size === 0}
                  >
                    <Sparkles className="w-4 h-4 mr-2" />
                    生成Prompt / Generate Prompt
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
                    <Wand2 className="w-4 h-4 mr-2" />
                    AI修改 / AI Modify
                  </Button>
                </div>
              </div>

              {/* Confirm Dialog */}
              {showMergeConfirm && (
                <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-semibold text-blue-900 mb-2">
                    {mergeMode === 'prompt' ? '生成修改提示词 / Generate Prompt' : 'AI直接修改 / AI Direct Modify'}
                  </h4>
                  <p className="text-sm text-blue-700 mb-3">
                    已选择 {selectedIssueIndices.size} 个问题
                  </p>
                  <textarea
                    placeholder="附加说明（可选）/ Additional notes (optional)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mb-3"
                    rows={2}
                    value={mergeUserNotes}
                    onChange={(e) => setMergeUserNotes(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={executeMergeModify}
                      disabled={isMerging}
                    >
                      {isMerging ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>确认 / Confirm</>
                      )}
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setShowMergeConfirm(false)}
                      disabled={isMerging}
                    >
                      取消 / Cancel
                    </Button>
                  </div>
                </div>
              )}

              {/* Merge Result */}
              {mergeResult && (
                <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  {mergeResult.type === 'prompt' ? (
                    <>
                      <h4 className="font-semibold text-green-900 mb-2">
                        ✅ 提示词已生成 / Prompt Generated
                      </h4>
                      <div className="bg-white p-3 rounded border border-green-300 mb-3">
                        <pre className="text-sm whitespace-pre-wrap text-gray-800">
                          {mergeResult.promptZh || mergeResult.prompt}
                        </pre>
                      </div>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => copyToClipboard(mergeResult.promptZh || mergeResult.prompt || '', setCopiedMergePrompt)}
                      >
                        {copiedMergePrompt ? (
                          <>
                            <Check className="w-4 h-4 mr-2" />
                            已复制 / Copied
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4 mr-2" />
                            复制 / Copy
                          </>
                        )}
                      </Button>
                    </>
                  ) : (
                    <>
                      <h4 className="font-semibold text-green-900 mb-2">
                        ✅ AI修改完成 / AI Modification Complete
                      </h4>
                      <p className="text-sm text-green-700 mb-2">
                        {mergeResult.changesSummaryZh} ({mergeResult.changesCount} 处修改)
                      </p>

                      {/* Preview of modified text - full content with scrollable area */}
                      {/* 修改后内容预览 - 完整内容可滚动 */}
                      <div className="bg-white p-3 rounded border border-green-300 mb-3 max-h-96 overflow-y-auto">
                        <p className="text-xs text-gray-500 mb-1">
                          修改后内容 / Modified Content ({mergeResult.modifiedText?.length || 0} 字符):
                        </p>
                        <pre className="text-sm whitespace-pre-wrap text-gray-800 font-mono">
                          {mergeResult.modifiedText}
                        </pre>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={handleAcceptModification}
                        >
                          <Check className="w-4 h-4 mr-2" />
                          采纳修改（填入下方输入框）
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={handleRegenerate}
                          disabled={regenerateCount >= MAX_REGENERATE || isMerging}
                        >
                          {isMerging ? (
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          ) : (
                            <RotateCcw className="w-4 h-4 mr-2" />
                          )}
                          重新生成 ({regenerateCount}/{MAX_REGENERATE})
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setMergeResult(null)}
                        >
                          <X className="w-4 h-4 mr-2" />
                          取消
                        </Button>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        💡 点击"采纳修改"后，内容会自动填入下方文本框，您可以继续编辑后再应用
                      </p>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Document Modification Section - Always show after analysis */}
          <div id="modify-section" className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              修改文档并应用 / Modify Document and Apply
            </h3>

            {/* Mode selector */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setModifyMode('file')}
                className={clsx(
                  'flex-1 py-3 px-4 rounded-lg border-2 transition-colors flex flex-col items-center',
                  modifyMode === 'file'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-600 hover:border-gray-400'
                )}
              >
                <Upload className="w-5 h-5 mb-1" />
                <span className="text-sm font-medium">上传修改后的文件</span>
                <span className="text-xs text-gray-500">Upload Modified File</span>
              </button>
              <button
                onClick={() => setModifyMode('text')}
                className={clsx(
                  'flex-1 py-3 px-4 rounded-lg border-2 transition-colors flex flex-col items-center',
                  modifyMode === 'text'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-600 hover:border-gray-400'
                )}
              >
                <Type className="w-5 h-5 mb-1" />
                <span className="text-sm font-medium">输入修改后的内容</span>
                <span className="text-xs text-gray-500">Input Modified Content</span>
              </button>
            </div>

            {/* File upload mode */}
            {modifyMode === 'file' && (
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-600 mb-3">
                  支持 TXT 和 DOCX 格式，最大 10MB
                  <br />
                  <span className="text-gray-400">Supports TXT and DOCX formats, max 10MB</span>
                </p>
                <input
                  type="file"
                  accept=".txt,.docx"
                  onChange={handleFileChange}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                {newFile && (
                  <p className="mt-2 text-sm text-green-600">
                    ✓ {newFile.name} ({(newFile.size / 1024).toFixed(2)} KB)
                  </p>
                )}
              </div>
            )}

            {/* Text input mode */}
            {modifyMode === 'text' && (
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-600 mb-3">
                  在下方输入修改后的文本内容，AI修改结果会自动填入此处
                  <br />
                  <span className="text-gray-400">Enter modified text below. AI modification results will auto-fill here.</span>
                </p>
                <textarea
                  value={newText}
                  onChange={(e) => setNewText(e.target.value)}
                  placeholder="粘贴或输入修改后的文本内容... / Paste or type modified text content..."
                  className="w-full h-64 px-3 py-2 border border-gray-300 rounded-lg resize-y font-mono text-sm"
                />
                <div className="mt-2 flex items-center justify-between">
                  <p className="text-sm text-gray-500">
                    {newText.length} 字符 / characters
                  </p>
                  {newText && (
                    <button
                      onClick={() => setNewText('')}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      清空 / Clear
                    </button>
                  )}
                </div>
              </div>
            )}

            {uploadError && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                {uploadError}
              </div>
            )}

            {/* Apply and Continue Button */}
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-gray-500">
                {modifyMode === 'file'
                  ? (newFile ? '文件已选择，可以应用' : '请先选择文件')
                  : (newText.trim() ? '内容已输入，可以应用' : '请先输入内容')}
              </p>
              <Button
                variant="primary"
                onClick={handleConfirmModify}
                disabled={isUploading || (modifyMode === 'file' && !newFile) || (modifyMode === 'text' && !newText.trim())}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    处理中...
                  </>
                ) : (
                  <>
                    <ArrowRight className="w-4 h-4 mr-2" />
                    应用并进行下一步 / Apply and Continue
                  </>
                )}
              </Button>
            </div>
          </div>
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
