import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Layers,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Upload,
  FileText,
  Type,
  Loader2,
  ChevronDown,
  ChevronUp,
  Copy,
  Sparkles,
  Wand2,
  ClipboardCopy,
  RotateCcw,
  Check,
  X,
  Square,
  CheckSquare,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import LoadingMessage from '../components/common/LoadingMessage';
import { structureApi, sessionApi, documentApi } from '../services/api';

/**
 * Step 1-1 Page: Document Structure Analysis
 * 步骤 1-1 页面：全文结构分析
 *
 * Analyzes document structure: sections, paragraphs, global patterns
 * Allows user to upload revised document or skip to next step
 * 分析文档结构：章节、段落、全局模式
 * 允许用户上传修改后的文档或跳过到下一步
 */
export default function Step1_1() {
  const { documentId } = useParams<{ documentId: string }>();
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
      sessionApi.updateStep(sessionId, 'step1-1').catch(console.error);
    }
  }, [sessionId]);

  // Analysis result state
  // 分析结果状态
  const [result, setResult] = useState<{
    sections: Array<{
      number: string;
      title: string;
      paragraphs: Array<{
        position: string;
        summary: string;
        summaryZh: string;
        firstSentence: string;
        lastSentence: string;
        wordCount: number;
      }>;
    }>;
    totalParagraphs: number;
    totalSections: number;
    structureScore: number;
    riskLevel: string;
    structureIssues: Array<{
      type: string;
      description: string;
      descriptionZh: string;
      severity: string;
      affectedPositions: string[];
    }>;
    scoreBreakdown: Record<string, number>;
    recommendationZh: string;
    // Style analysis fields (for colloquialism level support)
    // 风格分析字段（用于支持口语化级别）
    styleAnalysis?: {
      detectedStyle: number;
      styleName: string;
      styleNameZh: string;
      styleIndicators: string[];
      styleIndicatorsZh: string[];
      mismatchWarning?: string;
      mismatchWarningZh?: string;
      targetColloquialism?: number;
      styleMismatchLevel?: number;
    };
  } | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Document modification state
  // 文档修改状态
  const [modifyMode, setModifyMode] = useState<'file' | 'text'>('file');
  const [newFile, setNewFile] = useState<File | null>(null);
  const [newText, setNewText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Issue expansion state
  // 问题展开状态
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);
  const [issueSuggestion, setIssueSuggestion] = useState<{
    diagnosisZh: string;
    strategies: Array<{
      name_zh: string;
      description_zh: string;
      example_before?: string;
      example_after?: string;
      difficulty: string;
      effectiveness: string;
    }>;
    modificationPrompt: string;
    priorityTipsZh: string;
    cautionZh: string;
  } | null>(null);
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);
  const [copiedPrompt, setCopiedPrompt] = useState(false);

  // Merge modify state - 合并修改状态
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());
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

  // Prevent duplicate API calls
  // 防止重复API调用
  const isAnalyzingRef = useRef(false);

  // Load analysis on mount
  // 挂载时加载分析
  useEffect(() => {
    if (documentId && !isAnalyzingRef.current) {
      // Pass sessionId for colloquialism level detection
      // 传递 sessionId 用于口语化级别检测
      analyzeStructure(documentId, sessionId);
    }
  }, [documentId, sessionId]);

  // Analyze document structure
  // 分析文档结构
  const analyzeStructure = async (docId: string, sessId?: string | null) => {
    if (isAnalyzingRef.current) return;
    isAnalyzingRef.current = true;

    setIsLoading(true);
    setError(null);
    try {
      console.log('Step 1-1: Analyzing document structure for ID:', docId, 'sessionId:', sessId);
      // Pass sessionId to get colloquialism level for style analysis
      // 传递 sessionId 以获取口语化级别用于风格分析
      const data = await structureApi.analyzeStep1_1(docId, sessId || undefined);
      console.log('Step 1-1 result:', data);
      setResult(data);
    } catch (err: unknown) {
      console.error('Failed to analyze document structure:', err);
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.status === 404) {
        setError('文档不存在，请返回上传页面重新上传 / Document not found');
      } else if (axiosErr.response?.data?.detail) {
        setError(axiosErr.response.data.detail);
      } else {
        setError(err instanceof Error ? err.message : 'Analysis failed');
      }
    } finally {
      setIsLoading(false);
      isAnalyzingRef.current = false;
    }
  };

  // Validate and set file
  // 验证并设置文件
  const validateAndSetFile = (selectedFile: File) => {
    const allowedTypes = [
      'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(selectedFile.type)) {
      setUploadError('仅支持 TXT 和 DOCX 格式');
      return;
    }

    if (selectedFile.size > maxSize) {
      setUploadError('文件大小不能超过 10MB');
      return;
    }

    setNewFile(selectedFile);
    setUploadError(null);
  };

  // Handle file input change
  // 处理文件输入变化
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  // Handle issue click - expand and load suggestions
  // 处理问题点击 - 展开并加载建议
  const handleIssueClick = useCallback(async (index: number, issue: {
    type: string;
    description: string;
    descriptionZh: string;
    severity: string;
    affectedPositions: string[];
  }) => {
    // Toggle expand
    // 切换展开
    if (expandedIssueIndex === index) {
      setExpandedIssueIndex(null);
      setIssueSuggestion(null);
      setSuggestionError(null);
      return;
    }

    setExpandedIssueIndex(index);
    setIssueSuggestion(null);
    setSuggestionError(null);
    setIsLoadingSuggestion(true);

    try {
      // Fetch suggestions from LLM
      // 从 LLM 获取建议
      const response = await structureApi.getIssueSuggestion(
        documentId || '',
        issue,
        false // Full mode, not quick mode
      );
      setIssueSuggestion(response);
    } catch (err) {
      console.error('Failed to get issue suggestion:', err);
      setSuggestionError('获取建议失败，请稍后重试');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [expandedIssueIndex, documentId]);

  // Copy modification prompt to clipboard
  // 复制修改提示词到剪贴板
  const handleCopyPrompt = useCallback((prompt: string) => {
    navigator.clipboard.writeText(prompt).then(() => {
      setCopiedPrompt(true);
      setTimeout(() => setCopiedPrompt(false), 2000);
    });
  }, []);

  // Toggle issue selection for merge modify
  // 切换问题选择（用于合并修改）
  const toggleIssueSelection = useCallback((index: number) => {
    setSelectedIssueIndices(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  }, []);

  // Select/deselect all issues
  // 全选/取消全选问题
  const toggleSelectAll = useCallback(() => {
    if (!result?.structureIssues) return;
    if (selectedIssueIndices.size === result.structureIssues.length) {
      setSelectedIssueIndices(new Set());
    } else {
      setSelectedIssueIndices(new Set(result.structureIssues.map((_, i) => i)));
    }
  }, [result?.structureIssues, selectedIssueIndices.size]);

  // Open merge confirm dialog
  // 打开合并确认对话框
  const openMergeConfirm = useCallback((mode: 'prompt' | 'apply') => {
    if (selectedIssueIndices.size === 0) {
      return;
    }
    setMergeMode(mode);
    setShowMergeConfirm(true);
    setMergeUserNotes('');
  }, [selectedIssueIndices.size]);

  // Execute merge modification
  // 执行合并修改
  const executeMergeModify = useCallback(async () => {
    if (!result?.structureIssues || !documentId) return;

    const selectedIssues = Array.from(selectedIssueIndices).map(idx => result.structureIssues[idx]);

    setIsMerging(true);
    setShowMergeConfirm(false);

    try {
      if (mergeMode === 'prompt') {
        const response = await structureApi.mergeModifyPrompt(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult({
          type: 'prompt',
          prompt: response.prompt,
          promptZh: response.promptZh,
          colloquialismLevel: response.colloquialismLevel,
        });
      } else {
        const response = await structureApi.mergeModifyApply(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
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
      console.error('Merge modify error:', err);
      setMergeResult({
        type: mergeMode,
        prompt: mergeMode === 'prompt' ? '生成失败，请重试' : undefined,
        changesSummaryZh: mergeMode === 'apply' ? '修改失败，请重试' : undefined,
      });
    } finally {
      setIsMerging(false);
    }
  }, [documentId, result?.structureIssues, selectedIssueIndices, sessionId, mergeMode, mergeUserNotes]);

  // Regenerate AI modification (limited to 3 times)
  // 重新生成AI修改（限制3次）
  const handleRegenerate = useCallback(async () => {
    if (regenerateCount >= MAX_REGENERATE || !result?.structureIssues || !documentId) return;

    const selectedIssues = Array.from(selectedIssueIndices).map(idx => result.structureIssues[idx]);

    setIsMerging(true);

    try {
      const response = await structureApi.mergeModifyApply(
        documentId,
        selectedIssues,
        {
          sessionId: sessionId || undefined,
          userNotes: mergeUserNotes || undefined,
        }
      );
      setMergeResult({
        type: 'apply',
        modifiedText: response.modifiedText,
        changesSummaryZh: response.changesSummaryZh,
        changesCount: response.changesCount,
        remainingAttempts: MAX_REGENERATE - regenerateCount - 1,
        colloquialismLevel: response.colloquialismLevel,
      });
      setRegenerateCount(prev => prev + 1);
    } catch (err) {
      console.error('Regenerate error:', err);
    } finally {
      setIsMerging(false);
    }
  }, [documentId, result?.structureIssues, selectedIssueIndices, sessionId, mergeUserNotes, regenerateCount]);

  // Copy merge prompt to clipboard
  // 复制合并提示词到剪贴板
  const handleCopyMergePrompt = useCallback((prompt: string) => {
    navigator.clipboard.writeText(prompt).then(() => {
      setCopiedMergePrompt(true);
      setTimeout(() => setCopiedMergePrompt(false), 2000);
    });
  }, []);

  // Accept AI modification and use it as new document
  // 接受AI修改并使用它作为新文档
  const handleAcceptModification = useCallback(() => {
    if (mergeResult?.modifiedText) {
      setNewText(mergeResult.modifiedText);
      setModifyMode('text');
      setMergeResult(null);
    }
  }, [mergeResult?.modifiedText]);

  // Close merge result
  // 关闭合并结果
  const closeMergeResult = useCallback(() => {
    setMergeResult(null);
    setRegenerateCount(0);
  }, []);

  // Handle confirm modification - upload new document and continue
  // 处理确定修改 - 上传新文档并继续
  const handleConfirmModify = useCallback(async () => {
    if (modifyMode === 'file' && !newFile) {
      setUploadError('请选择一个文件');
      return;
    }

    if (modifyMode === 'text' && !newText.trim()) {
      setUploadError('请输入文本内容');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      // Upload new document
      // 上传新文档
      let newDocumentId: string;

      if (modifyMode === 'file' && newFile) {
        const result = await documentApi.upload(newFile);
        newDocumentId = result.id;
      } else {
        const result = await documentApi.uploadText(newText);
        newDocumentId = result.id;
      }

      // Navigate to Step 1-2 with new document
      // 使用新文档导航到 Step 1-2
      const sessionParam = sessionId ? `&session=${sessionId}` : '';
      navigate(`/flow/step1-2/${newDocumentId}?mode=${mode}${sessionParam}`);
    } catch (err) {
      setUploadError((err as Error).message || '上传失败，请重试');
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, sessionId, mode, navigate]);

  // Handle skip - continue with original document
  // 处理跳过 - 使用原文档继续
  const handleSkip = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/step1-2/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

  // Handle back to upload
  // 处理返回上传页面
  const handleBack = useCallback(() => {
    navigate('/upload');
  }, [navigate]);

  // Check if user has input for modification
  // 检查用户是否有修改输入
  const hasModificationInput = (modifyMode === 'file' && newFile) || (modifyMode === 'text' && newText.trim());

  // Loading state
  // 加载状态
  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex items-center justify-center min-h-[50vh]">
          <LoadingMessage category="structure" size="lg" showEnglish={true} />
        </div>
      </div>
    );
  }

  // Error state
  // 错误状态
  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex flex-col items-center justify-center min-h-[50vh]">
          <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
          <p className="text-red-600 text-lg mb-4">{error}</p>
          <Button variant="outline" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回上传
          </Button>
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
            <div className="p-2 rounded-lg bg-indigo-100 text-indigo-600 mr-3">
              <Layers className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Step 1-1: 全文结构分析
              </h1>
              <p className="text-gray-600 mt-1">
                Document Structure Analysis
              </p>
            </div>
          </div>
          <Button variant="outline" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回
          </Button>
        </div>

        {/* Progress indicator */}
        {/* 进度指示器 */}
        <div className="mt-4 flex items-center text-sm text-gray-500">
          <span className="font-medium text-indigo-600">Step 1-1</span>
          <span className="mx-2">→</span>
          <span>Step 1-2</span>
          <span className="mx-2">→</span>
          <span>Step 2</span>
          <span className="mx-2">→</span>
          <span>Step 3</span>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Score Card */}
          {/* 分数卡片 */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-1">
                  结构风险分数 / Structure Risk Score
                </h3>
                <p className="text-sm text-gray-500">
                  越高表示越容易被检测为AI生成
                </p>
              </div>
              <div className="text-right">
                <p className={clsx(
                  'text-4xl font-bold',
                  result.structureScore <= 30 && 'text-green-600',
                  result.structureScore > 30 && result.structureScore <= 60 && 'text-yellow-600',
                  result.structureScore > 60 && 'text-red-600'
                )}>
                  {result.structureScore}
                </p>
                <p className={clsx(
                  'text-sm font-medium',
                  result.riskLevel === 'low' && 'text-green-600',
                  result.riskLevel === 'medium' && 'text-yellow-600',
                  result.riskLevel === 'high' && 'text-red-600'
                )}>
                  {result.riskLevel === 'low' ? '低风险 Low Risk' :
                   result.riskLevel === 'medium' ? '中风险 Medium Risk' : '高风险 High Risk'}
                </p>
              </div>
            </div>

            {/* Statistics */}
            {/* 统计信息 */}
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-indigo-600">{result.totalSections}</p>
                <p className="text-sm text-gray-600">章节数 Sections</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-indigo-600">{result.totalParagraphs}</p>
                <p className="text-sm text-gray-600">段落数 Paragraphs</p>
              </div>
            </div>
          </div>

          {/* Style Analysis - Mismatch Warning */}
          {/* 风格分析 - 不匹配警告 */}
          {result.styleAnalysis && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                <Type className="w-5 h-5 mr-2 text-indigo-600" />
                文档风格分析 / Document Style Analysis
              </h3>

              {/* Style info */}
              <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">检测到的风格 / Detected Style:</span>
                  <span className="font-medium text-indigo-600">
                    Level {result.styleAnalysis.detectedStyle}/10 - {result.styleAnalysis.styleNameZh}
                  </span>
                </div>
                <div className="text-sm text-gray-500">
                  {result.styleAnalysis.styleName}
                </div>
              </div>

              {/* Style indicators */}
              {result.styleAnalysis.styleIndicatorsZh && result.styleAnalysis.styleIndicatorsZh.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">风格判断依据 / Style Indicators:</p>
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {result.styleAnalysis.styleIndicatorsZh.map((indicator, idx) => (
                      <li key={idx}>{indicator}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Mismatch warning - highlighted */}
              {result.styleAnalysis.mismatchWarningZh && (
                <div className="p-4 bg-amber-50 border-l-4 border-amber-500 rounded-r-lg">
                  <div className="flex items-start">
                    <AlertCircle className="w-5 h-5 text-amber-600 mr-3 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-amber-800 mb-1">风格不匹配警告</p>
                      <p className="text-sm text-amber-700">{result.styleAnalysis.mismatchWarningZh}</p>
                      {result.styleAnalysis.mismatchWarning && (
                        <p className="text-xs text-amber-600 mt-2">{result.styleAnalysis.mismatchWarning}</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* No mismatch - good style match */}
              {!result.styleAnalysis.mismatchWarningZh && result.styleAnalysis.targetColloquialism !== undefined && (
                <div className="p-4 bg-green-50 border-l-4 border-green-500 rounded-r-lg">
                  <div className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-green-800">风格匹配良好 / Style matches well</p>
                      <p className="text-sm text-green-700">
                        文档风格与您的目标级别（{result.styleAnalysis.targetColloquialism}）基本一致
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Structure Issues */}
          {/* 结构问题 */}
          {result.structureIssues && result.structureIssues.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold text-gray-800">
                  检测到 {result.structureIssues.length} 个结构问题
                </h3>
                {/* Select all checkbox */}
                <button
                  onClick={toggleSelectAll}
                  className="flex items-center text-sm text-primary-600 hover:text-primary-700"
                >
                  {selectedIssueIndices.size === result.structureIssues.length ? (
                    <CheckSquare className="w-4 h-4 mr-1" />
                  ) : (
                    <Square className="w-4 h-4 mr-1" />
                  )}
                  {selectedIssueIndices.size === result.structureIssues.length ? '取消全选' : '全选'}
                </button>
              </div>
              <p className="text-sm text-gray-500 mb-4">
                勾选问题后可使用"合并修改"功能，点击问题查看详细建议
              </p>
              <div className="space-y-3">
                {result.structureIssues.map((issue, idx) => (
                  <div key={idx} className="space-y-2">
                    {/* Issue Card Header - Clickable */}
                    {/* 问题卡片头部 - 可点击 */}
                    <div
                      className={clsx(
                        'p-4 rounded-lg border-l-4 transition-all hover:shadow-md',
                        issue.severity === 'high' && 'bg-red-50 border-red-500 hover:bg-red-100',
                        issue.severity === 'medium' && 'bg-yellow-50 border-yellow-500 hover:bg-yellow-100',
                        issue.severity === 'low' && 'bg-blue-50 border-blue-500 hover:bg-blue-100',
                        selectedIssueIndices.has(idx) && 'ring-2 ring-primary-500'
                      )}
                    >
                      <div className="flex items-start">
                        {/* Checkbox for selection */}
                        <button
                          onClick={(e) => { e.stopPropagation(); toggleIssueSelection(idx); }}
                          className="mr-3 mt-1 text-gray-500 hover:text-primary-600"
                        >
                          {selectedIssueIndices.has(idx) ? (
                            <CheckSquare className="w-5 h-5 text-primary-600" />
                          ) : (
                            <Square className="w-5 h-5" />
                          )}
                        </button>
                        <div
                          className="flex-1 cursor-pointer"
                          onClick={() => handleIssueClick(idx, issue)}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="font-medium text-gray-800">{issue.descriptionZh}</p>
                              <p className="text-sm text-gray-500 mt-1">{issue.description}</p>
                            </div>
                            <div className="flex items-center space-x-2 ml-4">
                              <span className={clsx(
                                'px-2 py-1 rounded text-xs font-medium',
                                issue.severity === 'high' && 'bg-red-100 text-red-700',
                                issue.severity === 'medium' && 'bg-yellow-100 text-yellow-700',
                                issue.severity === 'low' && 'bg-blue-100 text-blue-700'
                              )}>
                                {issue.severity === 'high' ? '高' : issue.severity === 'medium' ? '中' : '低'}
                              </span>
                              {expandedIssueIndex === idx ? (
                                <ChevronUp className="w-5 h-5 text-gray-400" />
                              ) : (
                                <ChevronDown className="w-5 h-5 text-gray-400" />
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Expanded Suggestion Panel */}
                    {/* 展开的建议面板 */}
                    {expandedIssueIndex === idx && (
                      <div className="ml-4 p-4 bg-white border rounded-lg shadow-sm">
                        {isLoadingSuggestion && (
                          <div className="flex items-center justify-center py-8">
                            <Loader2 className="w-6 h-6 animate-spin text-primary-600 mr-2" />
                            <span className="text-gray-600">正在分析并生成建议...</span>
                          </div>
                        )}

                        {suggestionError && (
                          <div className="flex items-center p-3 bg-red-50 text-red-700 rounded-lg">
                            <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
                            <span>{suggestionError}</span>
                          </div>
                        )}

                        {issueSuggestion && (
                          <div className="space-y-4">
                            {/* Diagnosis */}
                            {/* 诊断 */}
                            <div>
                              <h4 className="font-semibold text-gray-800 mb-2 flex items-center">
                                <Sparkles className="w-4 h-4 mr-2 text-purple-500" />
                                问题诊断
                              </h4>
                              <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700 whitespace-pre-wrap">
                                {issueSuggestion.diagnosisZh}
                              </div>
                            </div>

                            {/* Strategies */}
                            {/* 策略 */}
                            {issueSuggestion.strategies && issueSuggestion.strategies.length > 0 && (
                              <div>
                                <h4 className="font-semibold text-gray-800 mb-2">
                                  修改策略 ({issueSuggestion.strategies.length} 种)
                                </h4>
                                <div className="space-y-3">
                                  {issueSuggestion.strategies.map((strategy, sIdx) => (
                                    <div key={sIdx} className="p-3 bg-indigo-50 rounded-lg">
                                      <div className="flex items-center justify-between mb-2">
                                        <span className="font-medium text-indigo-800">
                                          {strategy.nameZh}
                                        </span>
                                        <div className="flex items-center space-x-2">
                                          <span className={clsx(
                                            'px-2 py-0.5 rounded text-xs',
                                            strategy.difficulty === 'easy' && 'bg-green-100 text-green-700',
                                            strategy.difficulty === 'medium' && 'bg-yellow-100 text-yellow-700',
                                            strategy.difficulty === 'hard' && 'bg-red-100 text-red-700'
                                          )}>
                                            {strategy.difficulty === 'easy' ? '易' : strategy.difficulty === 'medium' ? '中' : '难'}
                                          </span>
                                          <span className={clsx(
                                            'px-2 py-0.5 rounded text-xs',
                                            strategy.effectiveness === 'high' && 'bg-green-100 text-green-700',
                                            strategy.effectiveness === 'medium' && 'bg-yellow-100 text-yellow-700',
                                            strategy.effectiveness === 'low' && 'bg-gray-100 text-gray-700'
                                          )}>
                                            效果{strategy.effectiveness === 'high' ? '高' : strategy.effectiveness === 'medium' ? '中' : '低'}
                                          </span>
                                        </div>
                                      </div>
                                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                        {strategy.descriptionZh}
                                      </p>
                                      {strategy.exampleBefore && strategy.exampleAfter && (
                                        <div className="mt-2 text-xs space-y-1">
                                          <div className="p-2 bg-red-50 rounded">
                                            <span className="text-red-600 font-medium">原文: </span>
                                            <span className="text-gray-600">{strategy.exampleBefore}</span>
                                          </div>
                                          <div className="p-2 bg-green-50 rounded">
                                            <span className="text-green-600 font-medium">改后: </span>
                                            <span className="text-gray-600">{strategy.exampleAfter}</span>
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Modification Prompt */}
                            {/* 修改提示词 */}
                            {issueSuggestion.modificationPrompt && (
                              <div>
                                <div className="flex items-center justify-between mb-2">
                                  <h4 className="font-semibold text-gray-800">
                                    AI修改提示词 (可复制到其他AI工具使用)
                                  </h4>
                                  <button
                                    onClick={() => handleCopyPrompt(issueSuggestion.modificationPrompt)}
                                    className="flex items-center px-3 py-1 text-sm bg-primary-100 text-primary-700 rounded-lg hover:bg-primary-200 transition-colors"
                                  >
                                    <Copy className="w-4 h-4 mr-1" />
                                    {copiedPrompt ? '已复制!' : '复制'}
                                  </button>
                                </div>
                                <div className="p-3 bg-gray-900 rounded-lg text-sm text-gray-100 font-mono whitespace-pre-wrap max-h-60 overflow-y-auto">
                                  {issueSuggestion.modificationPrompt}
                                </div>
                              </div>
                            )}

                            {/* Priority Tips */}
                            {/* 优先建议 */}
                            {issueSuggestion.priorityTipsZh && (
                              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                                <h4 className="font-semibold text-amber-800 mb-1">优先修改建议</h4>
                                <p className="text-sm text-amber-700">{issueSuggestion.priorityTipsZh}</p>
                              </div>
                            )}

                            {/* Caution */}
                            {/* 注意事项 */}
                            {issueSuggestion.cautionZh && (
                              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                                <h4 className="font-semibold text-blue-800 mb-1">⚠️ 注意事项</h4>
                                <p className="text-sm text-blue-700">{issueSuggestion.cautionZh}</p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Merge Modify Buttons */}
              {/* 合并修改按钮 */}
              <div className="mt-6 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-sm text-gray-600">
                    已选择 <span className="font-medium text-primary-600">{selectedIssueIndices.size}</span> 个问题
                  </div>
                </div>
                <div className="flex flex-wrap gap-3">
                  <Button
                    variant="outline"
                    onClick={() => openMergeConfirm('prompt')}
                    disabled={selectedIssueIndices.size === 0 || isMerging}
                    className="flex items-center"
                  >
                    <ClipboardCopy className="w-4 h-4 mr-2" />
                    生成修改提示词
                  </Button>
                  <Button
                    variant="primary"
                    onClick={() => openMergeConfirm('apply')}
                    disabled={selectedIssueIndices.size === 0 || isMerging}
                    className="flex items-center"
                  >
                    <Wand2 className="w-4 h-4 mr-2" />
                    AI直接修改
                  </Button>
                </div>
                {selectedIssueIndices.size === 0 && (
                  <p className="text-xs text-gray-400 mt-2">
                    请先勾选要修改的问题
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Merge Confirm Modal */}
          {/* 合并确认对话框 */}
          {showMergeConfirm && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4 shadow-2xl">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                  {mergeMode === 'prompt' ? '生成修改提示词' : 'AI直接修改'}
                </h3>

                {/* Selected issues summary */}
                <div className="mb-4">
                  <p className="text-sm text-gray-600 mb-2">已选择的问题：</p>
                  <div className="max-h-40 overflow-y-auto space-y-2">
                    {Array.from(selectedIssueIndices).map(idx => {
                      const issue = result.structureIssues[idx];
                      return (
                        <div key={idx} className="flex items-center text-sm p-2 bg-gray-50 rounded">
                          <span className={clsx(
                            'w-2 h-2 rounded-full mr-2',
                            issue.severity === 'high' && 'bg-red-500',
                            issue.severity === 'medium' && 'bg-yellow-500',
                            issue.severity === 'low' && 'bg-blue-500'
                          )} />
                          <span className="truncate">{issue.descriptionZh}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* User notes input */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    注意事项（可选）
                  </label>
                  <textarea
                    value={mergeUserNotes}
                    onChange={(e) => setMergeUserNotes(e.target.value)}
                    placeholder="例如：保持原文的专业术语不变、注意某些特定段落..."
                    className="textarea w-full h-20"
                  />
                </div>

                {/* Info about regeneration limit */}
                {mergeMode === 'apply' && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                    <p>AI直接修改最多可重新生成 {MAX_REGENERATE} 次</p>
                  </div>
                )}

                {/* Buttons */}
                <div className="flex justify-end space-x-3">
                  <Button variant="outline" onClick={() => setShowMergeConfirm(false)}>
                    取消
                  </Button>
                  <Button variant="primary" onClick={executeMergeModify}>
                    {mergeMode === 'prompt' ? '生成提示词' : '开始修改'}
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Merge Loading */}
          {/* 合并修改加载中 */}
          {isMerging && (
            <div className="card p-6">
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-8 h-8 animate-spin text-primary-600 mr-3" />
                <span className="text-gray-600">
                  {mergeMode === 'prompt' ? '正在生成修改提示词...' : '正在进行AI修改...'}
                </span>
              </div>
            </div>
          )}

          {/* Merge Result */}
          {/* 合并修改结果 */}
          {mergeResult && !isMerging && (
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800">
                  {mergeResult.type === 'prompt' ? '修改提示词' : 'AI修改结果'}
                </h3>
                <button onClick={closeMergeResult} className="text-gray-400 hover:text-gray-600">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {mergeResult.colloquialismLevel !== undefined && (
                <p className="text-sm text-gray-500 mb-3">
                  口语化级别：{mergeResult.colloquialismLevel}/10
                </p>
              )}

              {/* Prompt Result */}
              {mergeResult.type === 'prompt' && mergeResult.prompt && (
                <div className="space-y-4">
                  <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
                    {mergeResult.promptZh}
                  </div>
                  <div className="relative">
                    <pre className="p-4 bg-gray-900 rounded-lg text-sm text-gray-100 font-mono whitespace-pre-wrap max-h-80 overflow-y-auto">
                      {mergeResult.prompt}
                    </pre>
                    <button
                      onClick={() => handleCopyMergePrompt(mergeResult.prompt!)}
                      className="absolute top-2 right-2 flex items-center px-3 py-1 text-xs bg-white text-gray-700 rounded hover:bg-gray-100"
                    >
                      {copiedMergePrompt ? <Check className="w-3 h-3 mr-1" /> : <Copy className="w-3 h-3 mr-1" />}
                      {copiedMergePrompt ? '已复制' : '复制'}
                    </button>
                  </div>
                </div>
              )}

              {/* Apply Result */}
              {mergeResult.type === 'apply' && mergeResult.modifiedText && (
                <div className="space-y-4">
                  {mergeResult.changesSummaryZh && (
                    <div className="p-3 bg-green-50 rounded-lg text-sm text-green-700">
                      <p className="font-medium mb-1">修改摘要：</p>
                      <p>{mergeResult.changesSummaryZh}</p>
                      {mergeResult.changesCount !== undefined && (
                        <p className="mt-1">共修改 {mergeResult.changesCount} 处</p>
                      )}
                    </div>
                  )}

                  <div className="p-4 bg-gray-50 rounded-lg text-sm text-gray-700 whitespace-pre-wrap max-h-80 overflow-y-auto">
                    {mergeResult.modifiedText}
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-500">
                      剩余重新生成次数：{MAX_REGENERATE - regenerateCount}
                    </div>
                    <div className="flex space-x-3">
                      <Button
                        variant="outline"
                        onClick={handleRegenerate}
                        disabled={regenerateCount >= MAX_REGENERATE || isMerging}
                        className="flex items-center"
                      >
                        <RotateCcw className="w-4 h-4 mr-2" />
                        重新生成
                      </Button>
                      <Button
                        variant="primary"
                        onClick={handleAcceptModification}
                        className="flex items-center"
                      >
                        <Check className="w-4 h-4 mr-2" />
                        采纳修改
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* No Issues */}
          {/* 无问题 */}
          {(!result.structureIssues || result.structureIssues.length === 0) && (
            <div className="card p-6 text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-gray-800">
                未检测到明显结构问题
              </h3>
              <p className="text-gray-600 mt-1">
                No obvious structure issues detected
              </p>
            </div>
          )}

          {/* Recommendation */}
          {/* 建议 */}
          {result.recommendationZh && (
            <div className="card p-6 bg-blue-50 border border-blue-200">
              <h3 className="font-semibold text-blue-800 mb-2">改进建议</h3>
              <p className="text-blue-700">{result.recommendationZh}</p>
            </div>
          )}

          {/* Document Modification Section */}
          {/* 文档修改区域 */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              根据建议修改文档 / Modify Document Based on Suggestions
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              如果您已根据上述建议修改了文档，可以在此上传修改后的版本继续处理。或者跳过此步直接进入下一阶段。
            </p>

            {/* Mode Tabs */}
            {/* 模式切换 */}
            <div className="flex space-x-2 mb-4">
              <button
                onClick={() => setModifyMode('file')}
                className={clsx(
                  'flex items-center px-4 py-2 rounded-lg font-medium transition-colors',
                  modifyMode === 'file'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >
                <Upload className="w-4 h-4 mr-2" />
                上传文件
              </button>
              <button
                onClick={() => setModifyMode('text')}
                className={clsx(
                  'flex items-center px-4 py-2 rounded-lg font-medium transition-colors',
                  modifyMode === 'text'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >
                <Type className="w-4 h-4 mr-2" />
                粘贴文本
              </button>
            </div>

            {/* File Upload */}
            {/* 文件上传 */}
            {modifyMode === 'file' && (
              <div className="border-2 border-dashed rounded-xl p-6 text-center transition-colors border-gray-300 hover:border-gray-400">
                {newFile ? (
                  <div className="flex items-center justify-center">
                    <FileText className="w-8 h-8 text-green-600 mr-3" />
                    <div className="text-left">
                      <p className="font-medium text-gray-800">{newFile.name}</p>
                      <p className="text-sm text-gray-500">
                        {(newFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                    <button
                      onClick={() => setNewFile(null)}
                      className="ml-4 text-gray-400 hover:text-red-500"
                    >
                      &times;
                    </button>
                  </div>
                ) : (
                  <>
                    <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-600 mb-2">
                      拖放修改后的文件到此处，或
                    </p>
                    <label className="inline-block">
                      <input
                        type="file"
                        accept=".txt,.docx"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                      <span className="text-primary-600 hover:text-primary-700 cursor-pointer font-medium">
                        点击选择文件
                      </span>
                    </label>
                    <p className="text-sm text-gray-500 mt-2">
                      支持 TXT、DOCX 格式
                    </p>
                  </>
                )}
              </div>
            )}

            {/* Text Input */}
            {/* 文本输入 */}
            {modifyMode === 'text' && (
              <div>
                <textarea
                  value={newText}
                  onChange={(e) => setNewText(e.target.value)}
                  placeholder="粘贴或输入修改后的文本..."
                  className="textarea h-40 w-full"
                />
                <p className="text-sm text-gray-500 mt-2 text-right">
                  {newText.length} 字符
                </p>
              </div>
            )}

            {/* Upload Error */}
            {/* 上传错误 */}
            {uploadError && (
              <div className="flex items-center p-3 mt-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
                <span className="text-sm">{uploadError}</span>
              </div>
            )}

            {/* Action Buttons */}
            {/* 操作按钮 */}
            <div className="flex justify-end space-x-4 mt-6 pt-4 border-t">
              <Button
                variant="outline"
                onClick={handleSkip}
                disabled={isUploading}
              >
                跳过，使用原文档继续
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
              <Button
                variant="primary"
                onClick={handleConfirmModify}
                disabled={!hasModificationInput || isUploading}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    上传中...
                  </>
                ) : (
                  <>
                    确定修改并继续
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
