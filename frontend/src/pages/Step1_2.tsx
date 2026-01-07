import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Link,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
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
  Upload,
  FileText,
  Type,
  BarChart3,
  Merge,
  Expand,
  Scissors,
  PenLine,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import LoadingMessage from '../components/common/LoadingMessage';
import { structureApi, sessionApi, documentApi } from '../services/api';

// Unified issue type for display
// 统一的问题类型用于显示
interface UnifiedIssue {
  id: string;
  type: string;
  description: string;
  descriptionZh: string;
  severity: string;
  affectedPositions: string[];
  category: 'connector' | 'logic_break' | 'paragraph_risk' | 'relationship';
  originalData: unknown;
}

/**
 * Step 1-2 Page: Paragraph Relationship Analysis
 * 步骤 1-2 页面：段落关系分析
 *
 * Analyzes paragraph relationships: connectors, logic breaks, AI risks
 * 分析段落关系：连接词、逻辑断层、AI风险
 */
export default function Step1_2() {
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
      sessionApi.updateStep(sessionId, 'step1-2').catch(console.error);
    }
  }, [sessionId]);

  // Analysis result state
  // 分析结果状态
  const [result, setResult] = useState<{
    explicitConnectors: Array<{
      word: string;
      position: string;
      location: string;
      severity: string;
    }>;
    logicBreaks: Array<{
      fromPosition: string;
      toPosition: string;
      transitionType: string;
      issue: string;
      issueZh: string;
      suggestion: string;
      suggestionZh: string;
    }>;
    paragraphRisks: Array<{
      position: string;
      aiRisk: string;
      aiRiskReason: string;
      openingConnector: string | null;
      rewriteSuggestionZh: string;
    }>;
    relationshipScore: number;
    relationshipIssues: Array<{
      type: string;
      description: string;
      descriptionZh: string;
      severity: string;
      affectedPositions: string[];
    }>;
    scoreBreakdown: Record<string, number>;
  } | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Issue expansion state
  // 问题展开状态
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);
  const [issueSuggestion, setIssueSuggestion] = useState<{
    diagnosisZh: string;
    strategies: Array<{
      nameZh: string;
      descriptionZh: string;
      exampleBefore?: string;
      exampleAfter?: string;
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

  // Document modification state
  // 文档修改状态
  const [modifyMode, setModifyMode] = useState<'file' | 'text'>('file');
  const [newFile, setNewFile] = useState<File | null>(null);
  const [newText, setNewText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Paragraph length analysis state (Two-Phase Enhancement)
  // 段落长度分析状态（两阶段增强）
  const [paragraphLengthAnalysis, setParagraphLengthAnalysis] = useState<{
    paragraphLengths: Array<{
      position: string;
      wordCount: number;
      section: string;
      summary: string;
      summaryZh: string;
    }>;
    meanLength: number;
    stdDev: number;
    cv: number;
    isUniform: boolean;
    humanLikeCvTarget: number;
    strategies: Array<{
      strategyType: string;
      targetPositions: string[];
      description: string;
      descriptionZh: string;
      reason: string;
      reasonZh: string;
      priority: number;
      expandSuggestion?: string;
      expandSuggestionZh?: string;
      // For merge strategy, semantic relationship between paragraphs
      // 对于合并策略，段落间的语义关系
      semanticRelation?: string;
      semanticRelationZh?: string;
      // For split/compress strategy, what aspects to separate or remove
      // 对于拆分/压缩策略，应分离或删除哪些方面
      splitPoints?: string[];
      splitPointsZh?: string[];
    }>;
    summary: string;
    summaryZh: string;
  } | null>(null);
  const [isLoadingParagraphLength, setIsLoadingParagraphLength] = useState(false);
  const [paragraphLengthError, setParagraphLengthError] = useState<string | null>(null);
  const [selectedStrategyIndices, setSelectedStrategyIndices] = useState<Set<number>>(new Set());
  const [expandTexts, setExpandTexts] = useState<Record<number, string>>({}); // strategyIndex -> expandText
  const [isApplyingStrategies, setIsApplyingStrategies] = useState(false);
  const [strategyResult, setStrategyResult] = useState<{
    modifiedText: string;
    changesSummaryZh: string;
    strategiesApplied: number;
    newCv?: number;
  } | null>(null);

  // Prevent duplicate API calls
  // 防止重复API调用
  const isAnalyzingRef = useRef(false);

  // Load analysis on mount
  // 挂载时加载分析
  useEffect(() => {
    if (documentId && !isAnalyzingRef.current) {
      analyzeRelationships(documentId);
    }
  }, [documentId]);

  // Analyze paragraph relationships
  // 分析段落关系
  const analyzeRelationships = async (docId: string) => {
    if (isAnalyzingRef.current) return;
    isAnalyzingRef.current = true;

    setIsLoading(true);
    setError(null);
    try {
      console.log('Step 1-2: Analyzing paragraph relationships for ID:', docId);
      const data = await structureApi.analyzeStep1_2(docId);
      console.log('Step 1-2 result:', data);
      setResult(data);
    } catch (err: unknown) {
      console.error('Failed to analyze paragraph relationships:', err);
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.status === 404) {
        setError('文档不存在或未完成 Step 1-1 分析 / Document not found or Step 1-1 not completed');
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

  // Convert result to unified issues list
  // 将结果转换为统一的问题列表
  const getUnifiedIssues = useCallback((): UnifiedIssue[] => {
    if (!result) return [];

    const issues: UnifiedIssue[] = [];

    // Add explicit connectors as issues
    // 将显性连接词作为问题添加
    result.explicitConnectors?.forEach((conn, idx) => {
      issues.push({
        id: `connector-${idx}`,
        type: 'explicit_connector',
        description: `Explicit connector "${conn.word}" at paragraph ${conn.position}`,
        descriptionZh: `段落${conn.position}使用了显性连接词"${conn.word}"`,
        severity: conn.severity || 'medium',
        affectedPositions: [conn.position],
        category: 'connector',
        originalData: conn,
      });
    });

    // Add logic breaks as issues
    // 将逻辑断层作为问题添加
    result.logicBreaks?.forEach((lb, idx) => {
      issues.push({
        id: `logic-break-${idx}`,
        type: 'logic_break',
        description: lb.issue || `Logic break between paragraphs ${lb.fromPosition} and ${lb.toPosition}`,
        descriptionZh: lb.issueZh || `段落${lb.fromPosition}与${lb.toPosition}之间存在逻辑断层`,
        severity: 'high',
        affectedPositions: [lb.fromPosition, lb.toPosition],
        category: 'logic_break',
        originalData: lb,
      });
    });

    // Add high-risk paragraphs as issues
    // 将高风险段落作为问题添加
    result.paragraphRisks?.filter(r => r.aiRisk === 'high').forEach((risk, idx) => {
      issues.push({
        id: `risk-${idx}`,
        type: 'high_ai_risk',
        description: risk.aiRiskReason || `High AI risk detected in paragraph ${risk.position}`,
        descriptionZh: risk.aiRiskReason || `段落${risk.position}具有高AI风险`,
        severity: 'high',
        affectedPositions: [risk.position],
        category: 'paragraph_risk',
        originalData: risk,
      });
    });

    // Add relationship issues
    // 添加关系问题
    result.relationshipIssues?.forEach((issue, idx) => {
      issues.push({
        id: `relationship-${idx}`,
        type: issue.type,
        description: issue.description,
        descriptionZh: issue.descriptionZh,
        severity: issue.severity,
        affectedPositions: issue.affectedPositions,
        category: 'relationship',
        originalData: issue,
      });
    });

    return issues;
  }, [result]);

  const unifiedIssues = getUnifiedIssues();

  // Handle issue click - expand and load suggestions
  // 处理问题点击 - 展开并加载建议
  const handleIssueClick = useCallback(async (index: number, issue: UnifiedIssue) => {
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
        {
          type: issue.type,
          description: issue.description,
          descriptionZh: issue.descriptionZh,
          severity: issue.severity,
          affectedPositions: issue.affectedPositions,
        },
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
    if (selectedIssueIndices.size === unifiedIssues.length) {
      setSelectedIssueIndices(new Set());
    } else {
      setSelectedIssueIndices(new Set(unifiedIssues.map((_, i) => i)));
    }
  }, [unifiedIssues, selectedIssueIndices.size]);

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
    if (!documentId) return;

    const selectedIssues = Array.from(selectedIssueIndices).map(idx => unifiedIssues[idx]);
    const issuesForApi = selectedIssues.map(issue => ({
      type: issue.type,
      description: issue.description,
      descriptionZh: issue.descriptionZh,
      severity: issue.severity,
      affectedPositions: issue.affectedPositions,
    }));

    setIsMerging(true);
    setShowMergeConfirm(false);

    try {
      if (mergeMode === 'prompt') {
        const response = await structureApi.mergeModifyPrompt(
          documentId,
          issuesForApi,
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
          issuesForApi,
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
  }, [documentId, unifiedIssues, selectedIssueIndices, sessionId, mergeMode, mergeUserNotes]);

  // Regenerate AI modification (limited to 3 times)
  // 重新生成AI修改（限制3次）
  const handleRegenerate = useCallback(async () => {
    if (regenerateCount >= MAX_REGENERATE || !documentId) return;

    const selectedIssues = Array.from(selectedIssueIndices).map(idx => unifiedIssues[idx]);
    const issuesForApi = selectedIssues.map(issue => ({
      type: issue.type,
      description: issue.description,
      descriptionZh: issue.descriptionZh,
      severity: issue.severity,
      affectedPositions: issue.affectedPositions,
    }));

    setIsMerging(true);

    try {
      const response = await structureApi.mergeModifyApply(
        documentId,
        issuesForApi,
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
  }, [documentId, unifiedIssues, selectedIssueIndices, sessionId, mergeUserNotes, regenerateCount]);

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

  // ==== Paragraph Length Analysis Functions (Two-Phase Enhancement) ====
  // ==== 段落长度分析功能（两阶段增强）====

  // Analyze paragraph length distribution (Phase 1)
  // 分析段落长度分布（阶段1）
  const analyzeParagraphLength = useCallback(async () => {
    if (!documentId) return;

    setIsLoadingParagraphLength(true);
    setParagraphLengthError(null);
    setSelectedStrategyIndices(new Set());
    setExpandTexts({});
    setStrategyResult(null);

    try {
      const data = await structureApi.analyzeParagraphLength(documentId);
      setParagraphLengthAnalysis(data);
    } catch (err) {
      console.error('Paragraph length analysis error:', err);
      setParagraphLengthError('段落长度分析失败 / Paragraph length analysis failed');
    } finally {
      setIsLoadingParagraphLength(false);
    }
  }, [documentId]);

  // Toggle strategy selection
  // 切换策略选择
  const toggleStrategySelection = useCallback((index: number) => {
    setSelectedStrategyIndices(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
        // Clear expand text if deselected
        setExpandTexts(prev => {
          const { [index]: _, ...rest } = prev;
          return rest;
        });
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  }, []);

  // Update expand text for a strategy
  // 更新策略的扩展文本
  const updateExpandText = useCallback((index: number, text: string) => {
    setExpandTexts(prev => ({
      ...prev,
      [index]: text,
    }));
  }, []);

  // Apply selected strategies (Phase 2)
  // 应用选中的策略（阶段2）
  const applyStrategies = useCallback(async () => {
    if (!documentId || !paragraphLengthAnalysis || selectedStrategyIndices.size === 0) return;

    setIsApplyingStrategies(true);
    setStrategyResult(null);

    try {
      const selectedStrategies = Array.from(selectedStrategyIndices).map(idx => {
        const strategy = paragraphLengthAnalysis.strategies[idx];
        return {
          strategyType: strategy.strategyType,
          targetPositions: strategy.targetPositions,
          expandText: strategy.strategyType === 'expand' ? expandTexts[idx] : undefined,
        };
      });

      const result = await structureApi.applyParagraphStrategies(
        documentId,
        selectedStrategies,
        { sessionId: sessionId || undefined }
      );
      setStrategyResult(result);
      // Set the modified text for continuation
      setNewText(result.modifiedText);
      setModifyMode('text');
    } catch (err) {
      console.error('Apply strategies error:', err);
      setParagraphLengthError('应用策略失败 / Failed to apply strategies');
    } finally {
      setIsApplyingStrategies(false);
    }
  }, [documentId, paragraphLengthAnalysis, selectedStrategyIndices, expandTexts, sessionId]);

  // Close strategy result
  // 关闭策略结果
  const closeStrategyResult = useCallback(() => {
    setStrategyResult(null);
  }, []);

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

      // Navigate to Step 2 with new document
      // 使用新文档导航到 Step 2
      const sessionParam = sessionId ? `&session=${sessionId}` : '';
      navigate(`/flow/step2/${newDocumentId}?mode=${mode}${sessionParam}`);
    } catch (err) {
      setUploadError((err as Error).message || '上传失败，请重试');
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, sessionId, mode, navigate]);

  // Handle continue to Step 2
  // 处理继续到 Step 2
  const handleContinue = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/step2/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

  // Handle skip to Step 2
  // 处理跳过到 Step 2
  const handleSkip = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/step2/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

  // Handle back to Step 1-1
  // 处理返回 Step 1-1
  const handleBack = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/step1-1/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

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
            返回 Step 1-1
          </Button>
        </div>
      </div>
    );
  }

  const highRiskCount = result?.paragraphRisks?.filter(r => r.aiRisk === 'high').length || 0;

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="p-2 rounded-lg bg-blue-100 text-blue-600 mr-3">
              <Link className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Step 1-2: 段落关系分析
              </h1>
              <p className="text-gray-600 mt-1">
                Paragraph Relationship Analysis
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
          <span className="text-green-600">Step 1-1 ✓</span>
          <span className="mx-2">→</span>
          <span className="font-medium text-blue-600">Step 1-2</span>
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
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-1">
                  关系风险分数 / Relationship Risk Score
                </h3>
                <p className="text-sm text-gray-500">
                  越高表示段落关系越可能被检测为AI生成
                </p>
              </div>
              <div className="text-right">
                <p className={clsx(
                  'text-4xl font-bold',
                  result.relationshipScore <= 30 && 'text-green-600',
                  result.relationshipScore > 30 && result.relationshipScore <= 60 && 'text-yellow-600',
                  result.relationshipScore > 60 && 'text-red-600'
                )}>
                  {result.relationshipScore}
                </p>
              </div>
            </div>

            {/* Statistics */}
            {/* 统计信息 */}
            <div className="grid grid-cols-3 gap-4">
              <div className="p-3 bg-amber-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-amber-600">
                  {result.explicitConnectors?.length || 0}
                </p>
                <p className="text-sm text-gray-600">显性连接词</p>
              </div>
              <div className="p-3 bg-red-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-red-600">
                  {result.logicBreaks?.length || 0}
                </p>
                <p className="text-sm text-gray-600">逻辑断层</p>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-purple-600">
                  {highRiskCount}
                </p>
                <p className="text-sm text-gray-600">高风险段落</p>
              </div>
            </div>
          </div>

          {/* Unified Issues List with Selection */}
          {/* 统一问题列表（带选择功能）*/}
          {unifiedIssues.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold text-gray-800">
                  检测到 {unifiedIssues.length} 个问题
                </h3>
                {/* Select all checkbox */}
                <button
                  onClick={toggleSelectAll}
                  className="flex items-center text-sm text-primary-600 hover:text-primary-700"
                >
                  {selectedIssueIndices.size === unifiedIssues.length ? (
                    <CheckSquare className="w-4 h-4 mr-1" />
                  ) : (
                    <Square className="w-4 h-4 mr-1" />
                  )}
                  {selectedIssueIndices.size === unifiedIssues.length ? '取消全选' : '全选'}
                </button>
              </div>
              <p className="text-sm text-gray-500 mb-4">
                勾选问题后可使用"合并修改"功能，点击问题查看详细建议
              </p>

              <div className="space-y-3">
                {unifiedIssues.map((issue, idx) => (
                  <div key={issue.id} className="space-y-2">
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
                              <div className="flex items-center gap-2 mb-1">
                                <span className={clsx(
                                  'px-2 py-0.5 rounded text-xs font-medium',
                                  issue.category === 'connector' && 'bg-amber-100 text-amber-700',
                                  issue.category === 'logic_break' && 'bg-red-100 text-red-700',
                                  issue.category === 'paragraph_risk' && 'bg-purple-100 text-purple-700',
                                  issue.category === 'relationship' && 'bg-blue-100 text-blue-700'
                                )}>
                                  {issue.category === 'connector' && '连接词'}
                                  {issue.category === 'logic_break' && '逻辑断层'}
                                  {issue.category === 'paragraph_risk' && '高风险段落'}
                                  {issue.category === 'relationship' && '关系问题'}
                                </span>
                              </div>
                              <p className="font-medium text-gray-800">{issue.descriptionZh}</p>
                              <p className="text-sm text-gray-500 mt-1">{issue.description}</p>
                              {issue.affectedPositions.length > 0 && (
                                <p className="text-xs text-gray-400 mt-1">
                                  影响位置: {issue.affectedPositions.join(', ')}
                                </p>
                              )}
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
                      const issue = unifiedIssues[idx];
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

          {/* Paragraph Length Analysis Section (Two-Phase Enhancement) */}
          {/* 段落长度分析区域（两阶段增强）*/}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <BarChart3 className="w-5 h-5 text-purple-600 mr-2" />
                <h3 className="text-lg font-semibold text-gray-800">
                  段落长度分布分析 / Paragraph Length Analysis
                </h3>
              </div>
              <Button
                variant="outline"
                onClick={analyzeParagraphLength}
                disabled={isLoadingParagraphLength}
                className="flex items-center"
              >
                {isLoadingParagraphLength ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    分析中...
                  </>
                ) : (
                  <>
                    <BarChart3 className="w-4 h-4 mr-2" />
                    开始分析
                  </>
                )}
              </Button>
            </div>

            <p className="text-sm text-gray-500 mb-4">
              分析段落长度分布，检测是否过于均匀（AI写作特征），并提供改进策略。
            </p>

            {/* Loading State */}
            {isLoadingParagraphLength && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-8 h-8 animate-spin text-purple-600 mr-3" />
                <span className="text-gray-600">正在分析段落长度分布...</span>
              </div>
            )}

            {/* Error State */}
            {paragraphLengthError && (
              <div className="flex items-center p-3 bg-red-50 text-red-700 rounded-lg">
                <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
                <span>{paragraphLengthError}</span>
              </div>
            )}

            {/* Analysis Result */}
            {paragraphLengthAnalysis && !isLoadingParagraphLength && (
              <div className="space-y-4">
                {/* Statistics */}
                <div className="grid grid-cols-4 gap-3">
                  <div className="p-3 bg-gray-50 rounded-lg text-center">
                    <p className="text-lg font-bold text-gray-800">
                      {paragraphLengthAnalysis.meanLength.toFixed(1)}
                    </p>
                    <p className="text-xs text-gray-500">平均长度（词）</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg text-center">
                    <p className="text-lg font-bold text-gray-800">
                      {paragraphLengthAnalysis.stdDev.toFixed(1)}
                    </p>
                    <p className="text-xs text-gray-500">标准差</p>
                  </div>
                  <div className={clsx(
                    'p-3 rounded-lg text-center',
                    paragraphLengthAnalysis.isUniform ? 'bg-red-50' : 'bg-green-50'
                  )}>
                    <p className={clsx(
                      'text-lg font-bold',
                      paragraphLengthAnalysis.isUniform ? 'text-red-600' : 'text-green-600'
                    )}>
                      {paragraphLengthAnalysis.cv.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">CV (变异系数)</p>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg text-center">
                    <p className="text-lg font-bold text-purple-600">
                      {paragraphLengthAnalysis.humanLikeCvTarget.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">目标 CV</p>
                  </div>
                </div>

                {/* Uniform Warning */}
                {paragraphLengthAnalysis.isUniform && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <div className="flex items-start">
                      <AlertCircle className="w-5 h-5 text-amber-500 mr-2 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="font-medium text-amber-800">
                          段落长度过于均匀 / Paragraph lengths too uniform
                        </p>
                        <p className="text-sm text-amber-700 mt-1">
                          {paragraphLengthAnalysis.summaryZh}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Strategy Suggestions */}
                {paragraphLengthAnalysis.strategies.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-semibold text-gray-800 mb-3">
                      改进策略（可多选）/ Improvement Strategies
                    </h4>
                    <div className="space-y-3">
                      {paragraphLengthAnalysis.strategies.map((strategy, idx) => (
                        <div
                          key={idx}
                          className={clsx(
                            'p-4 rounded-lg border-2 transition-all',
                            selectedStrategyIndices.has(idx)
                              ? 'border-purple-500 bg-purple-50'
                              : 'border-gray-200 bg-white hover:border-gray-300'
                          )}
                        >
                          <div className="flex items-start">
                            <button
                              onClick={() => toggleStrategySelection(idx)}
                              className="mr-3 mt-1 text-gray-500 hover:text-purple-600"
                            >
                              {selectedStrategyIndices.has(idx) ? (
                                <CheckSquare className="w-5 h-5 text-purple-600" />
                              ) : (
                                <Square className="w-5 h-5" />
                              )}
                            </button>
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                {strategy.strategyType === 'merge' && (
                                  <span className="flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
                                    <Merge className="w-3 h-3 mr-1" />
                                    合并
                                  </span>
                                )}
                                {strategy.strategyType === 'expand' && (
                                  <span className="flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
                                    <Expand className="w-3 h-3 mr-1" />
                                    扩展
                                  </span>
                                )}
                                {strategy.strategyType === 'split' && (
                                  <span className="flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-700">
                                    <Scissors className="w-3 h-3 mr-1" />
                                    拆分
                                  </span>
                                )}
                                {strategy.strategyType === 'compress' && (
                                  <span className="flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
                                    <Scissors className="w-3 h-3 mr-1" />
                                    压缩
                                  </span>
                                )}
                                <span className="text-xs text-gray-400">
                                  优先级: {strategy.priority}
                                </span>
                              </div>
                              <p className="font-medium text-gray-800">
                                {strategy.descriptionZh}
                              </p>
                              <p className="text-sm text-gray-500 mt-1">
                                {strategy.reasonZh}
                              </p>
                              {strategy.targetPositions.length > 0 && (
                                <p className="text-xs text-gray-400 mt-1">
                                  目标段落: {strategy.targetPositions.join(', ')}
                                </p>
                              )}

                              {/* Semantic Relation for Merge Strategy */}
                              {/* 合并策略的语义关系 */}
                              {strategy.strategyType === 'merge' && strategy.semanticRelationZh && (
                                <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
                                  <p className="text-xs text-blue-700">
                                    <span className="font-medium">语义关系：</span>
                                    {strategy.semanticRelationZh}
                                  </p>
                                </div>
                              )}

                              {/* Split Points for Split/Compress Strategy */}
                              {/* 拆分/压缩策略的拆分点 */}
                              {(strategy.strategyType === 'split' || strategy.strategyType === 'compress') && strategy.splitPointsZh && strategy.splitPointsZh.length > 0 && (
                                <div className="mt-2 p-2 bg-orange-50 rounded border border-orange-200">
                                  <p className="text-xs text-orange-700 font-medium mb-1">
                                    {strategy.strategyType === 'split' ? '建议拆分点：' : '建议修改：'}
                                  </p>
                                  <ul className="text-xs text-orange-600 list-disc list-inside">
                                    {strategy.splitPointsZh.map((point, pIdx) => (
                                      <li key={pIdx}>{point}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Expand Text Input */}
                              {strategy.strategyType === 'expand' && selectedStrategyIndices.has(idx) && (
                                <div className="mt-3">
                                  {strategy.expandSuggestionZh && (
                                    <p className="text-xs text-purple-600 mb-2">
                                      <PenLine className="w-3 h-3 inline mr-1" />
                                      建议: {strategy.expandSuggestionZh}
                                    </p>
                                  )}
                                  <textarea
                                    value={expandTexts[idx] || ''}
                                    onChange={(e) => updateExpandText(idx, e.target.value)}
                                    placeholder="请输入要添加的内容..."
                                    className="textarea w-full h-24 text-sm"
                                  />
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Apply Strategies Button */}
                    <div className="mt-4 flex justify-end">
                      <Button
                        variant="primary"
                        onClick={applyStrategies}
                        disabled={selectedStrategyIndices.size === 0 || isApplyingStrategies}
                        className="flex items-center"
                      >
                        {isApplyingStrategies ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            应用中...
                          </>
                        ) : (
                          <>
                            <Wand2 className="w-4 h-4 mr-2" />
                            应用 {selectedStrategyIndices.size} 个策略
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                )}

                {/* No Strategies Needed */}
                {paragraphLengthAnalysis.strategies.length === 0 && !paragraphLengthAnalysis.isUniform && (
                  <div className="flex items-center p-3 bg-green-50 text-green-700 rounded-lg">
                    <CheckCircle className="w-5 h-5 mr-2 flex-shrink-0" />
                    <span>段落长度分布良好，无需调整。</span>
                  </div>
                )}
              </div>
            )}

            {/* Strategy Apply Result */}
            {strategyResult && (
              <div className="mt-4 p-4 bg-white border border-green-200 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-green-800">
                    策略应用成功
                  </h4>
                  <button onClick={closeStrategyResult} className="text-gray-400 hover:text-gray-600">
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <p className="text-sm text-green-700 mb-3">
                  {strategyResult.changesSummaryZh}
                </p>
                <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700 whitespace-pre-wrap max-h-60 overflow-y-auto">
                  {strategyResult.modifiedText.substring(0, 500)}
                  {strategyResult.modifiedText.length > 500 && '...'}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  修改后的文本已自动填入下方输入框，您可以继续编辑或直接进入下一步。
                </p>
              </div>
            )}
          </div>

          {/* No Issues */}
          {/* 无问题 */}
          {unifiedIssues.length === 0 && (
            <div className="card p-6 text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-gray-800">
                段落关系良好
              </h3>
              <p className="text-gray-600 mt-1">
                No obvious relationship issues detected
              </p>
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
