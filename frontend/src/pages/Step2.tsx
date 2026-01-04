import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Link,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  SkipForward,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Copy,
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
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import LoadingMessage from '../components/common/LoadingMessage';
import { transitionApi, structureApi, sessionApi, documentApi } from '../services/api';
import type { DocumentTransitionSummary } from '../types';

// Unified issue type for display
// 统一的问题类型用于显示
interface UnifiedTransitionIssue {
  id: string;
  type: string;
  description: string;
  descriptionZh: string;
  severity: string;
  affectedPositions: string[];
  category: 'explicit_connector' | 'transition_issue' | 'smoothness';
  originalData: unknown;
  transitionIndex?: number;
}

/**
 * Step 2 Page: Transition Analysis
 * 步骤 2 页面：衔接分析
 *
 * Analyzes paragraph transitions and provides multi-select merge modify
 * 分析段落衔接并提供多选合并修改功能
 */
export default function Step2() {
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
      sessionApi.updateStep(sessionId, 'step2').catch(console.error);
    }
  }, [sessionId]);

  // Analysis result state
  // 分析结果状态
  const [result, setResult] = useState<DocumentTransitionSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Issue expansion state (reserved for future use)
  // 问题展开状态（保留供将来使用）

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
  const [isConfirming, setIsConfirming] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Prevent duplicate API calls
  // 防止重复API调用
  const isAnalyzingRef = useRef(false);

  // Load analysis on mount
  // 挂载时加载分析
  useEffect(() => {
    if (documentId && !isAnalyzingRef.current) {
      analyzeTransitions(documentId);
    }
  }, [documentId]);

  // Analyze document transitions
  // 分析文档衔接
  const analyzeTransitions = async (docId: string) => {
    if (isAnalyzingRef.current) return;
    isAnalyzingRef.current = true;

    setIsLoading(true);
    setError(null);
    try {
      console.log('Step 2: Analyzing transitions for ID:', docId);
      const data = await transitionApi.analyzeDocument(docId);
      console.log('Step 2 result:', data);
      setResult(data);
    } catch (err: unknown) {
      console.error('Failed to analyze transitions:', err);
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.status === 404) {
        setError('文档不存在或未完成前置分析 / Document not found or prerequisites not completed');
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

  // Convert transitions to unified issues for selection
  // 将衔接转换为统一问题格式用于选择
  const getUnifiedIssues = useCallback((): UnifiedTransitionIssue[] => {
    if (!result?.transitions) return [];

    const issues: UnifiedTransitionIssue[] = [];

    result.transitions.forEach((transition, transIdx) => {
      // Add explicit connector issues
      // 添加显性连接词问题
      if (transition.explicitConnectors && transition.explicitConnectors.length > 0) {
        transition.explicitConnectors.forEach((connector, connIdx) => {
          issues.push({
            id: `conn-${transIdx}-${connIdx}`,
            type: 'explicit_connector',
            description: `Explicit connector "${connector}" in transition ${transIdx + 1}`,
            descriptionZh: `衔接 #${transIdx + 1} 使用显性连接词 "${connector}"`,
            severity: 'high',
            affectedPositions: [`衔接 #${transIdx + 1}`],
            category: 'explicit_connector',
            originalData: { connector, transition },
            transitionIndex: transIdx,
          });
        });
      }

      // Add transition issues
      // 添加衔接问题
      if (transition.issues && transition.issues.length > 0) {
        transition.issues.forEach((issue, issueIdx) => {
          issues.push({
            id: `issue-${transIdx}-${issueIdx}`,
            type: issue.type || 'transition_issue',
            description: issue.description || `Transition issue in #${transIdx + 1}`,
            descriptionZh: issue.descriptionZh || `衔接 #${transIdx + 1} 存在问题`,
            severity: transition.riskLevel || 'medium',
            affectedPositions: [`衔接 #${transIdx + 1}`],
            category: 'transition_issue',
            originalData: { issue, transition },
            transitionIndex: transIdx,
          });
        });
      }

      // Add smoothness issues for medium/high risk transitions without explicit issues
      // 为中高风险但没有明确问题的衔接添加平滑度问题
      if ((transition.riskLevel === 'high' || transition.riskLevel === 'medium') &&
          (!transition.issues || transition.issues.length === 0) &&
          (!transition.explicitConnectors || transition.explicitConnectors.length === 0)) {
        issues.push({
          id: `smooth-${transIdx}`,
          type: 'smoothness',
          description: `Transition #${transIdx + 1} has ${transition.riskLevel} risk (score: ${transition.smoothnessScore})`,
          descriptionZh: `衔接 #${transIdx + 1} 为${transition.riskLevel === 'high' ? '高' : '中'}风险（分数：${transition.smoothnessScore}）`,
          severity: transition.riskLevel,
          affectedPositions: [`衔接 #${transIdx + 1}`],
          category: 'smoothness',
          originalData: { transition },
          transitionIndex: transIdx,
        });
      }
    });

    return issues;
  }, [result]);

  const unifiedIssues = getUnifiedIssues();

  // Toggle issue selection
  // 切换问题选择
  const toggleIssueSelection = useCallback((index: number) => {
    setSelectedIssueIndices(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }, []);

  // Toggle select all
  // 切换全选
  const toggleSelectAll = useCallback(() => {
    if (selectedIssueIndices.size === unifiedIssues.length) {
      setSelectedIssueIndices(new Set());
    } else {
      setSelectedIssueIndices(new Set(unifiedIssues.map((_, i) => i)));
    }
  }, [selectedIssueIndices.size, unifiedIssues]);

  // Open merge confirm dialog
  // 打开合并确认对话框
  const openMergeConfirm = useCallback((mode: 'prompt' | 'apply') => {
    setMergeMode(mode);
    setMergeUserNotes('');
    setShowMergeConfirm(true);
  }, []);

  // Execute merge modify
  // 执行合并修改
  const executeMergeModify = useCallback(async () => {
    if (!documentId || selectedIssueIndices.size === 0) return;

    setIsMerging(true);
    setMergeResult(null);

    try {
      // Convert selected issues to API format
      // 将选中的问题转换为API格式
      const selectedIssues = Array.from(selectedIssueIndices).map(idx => {
        const issue = unifiedIssues[idx];
        return {
          type: issue.type,
          description: issue.description,
          descriptionZh: issue.descriptionZh,
          severity: issue.severity,
          affectedPositions: issue.affectedPositions,
        };
      });

      // Add user notes about preserving previous improvements
      // 添加关于保持之前改进的用户注意事项
      const enhancedNotes = `${mergeUserNotes}\n\n【重要】这是 Step 2（衔接分析）的修改。Step 1-1 和 Step 1-2 中已经对文档结构和段落关系进行了分析和改进。请务必保持这些改进，只针对当前选中的衔接问题进行修改。`;

      if (mergeMode === 'prompt') {
        const response = await structureApi.mergeModifyPrompt(
          documentId,
          selectedIssues,
          { sessionId: sessionId || undefined, userNotes: enhancedNotes }
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
          { sessionId: sessionId || undefined, userNotes: enhancedNotes }
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
      }
    } catch (err) {
      console.error('Merge modify failed:', err);
      setError('合并修改失败，请重试');
    } finally {
      setIsMerging(false);
      setShowMergeConfirm(false);
    }
  }, [documentId, selectedIssueIndices, unifiedIssues, mergeMode, mergeUserNotes, sessionId]);

  // Copy prompt to clipboard
  // 复制提示词到剪贴板
  const copyMergePrompt = useCallback(async () => {
    if (mergeResult?.prompt) {
      await navigator.clipboard.writeText(mergeResult.prompt);
      setCopiedMergePrompt(true);
      setTimeout(() => setCopiedMergePrompt(false), 2000);
    }
  }, [mergeResult]);

  // Regenerate AI modification
  // 重新生成AI修改
  const handleRegenerate = useCallback(async () => {
    if (regenerateCount >= MAX_REGENERATE) return;
    await executeMergeModify();
  }, [regenerateCount, executeMergeModify]);

  // Accept AI modification
  // 采纳AI修改
  const handleAcceptModification = useCallback(() => {
    if (mergeResult?.modifiedText) {
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
      const validTypes = ['.txt', '.docx', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      const isValid = validTypes.some(type =>
        file.name.endsWith(type) || file.type === type
      );
      if (!isValid) {
        alert('请上传 TXT 或 DOCX 格式的文件');
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        alert('文件大小不能超过 10MB');
        return;
      }
      setNewFile(file);
    }
  }, []);

  // Handle confirm modification
  // 处理确认修改
  const handleConfirmModify = useCallback(async () => {
    if (!documentId || !sessionId) return;

    const hasContent = modifyMode === 'file' ? newFile : newText.trim();
    if (!hasContent) {
      alert('请先上传文件或输入修改后的文本');
      return;
    }

    setIsConfirming(true);
    try {
      // Upload modified document and create new document
      // 上传修改后的文档并创建新文档
      let uploadResult;
      if (modifyMode === 'file' && newFile) {
        uploadResult = await documentApi.upload(newFile);
      } else if (modifyMode === 'text' && newText.trim()) {
        uploadResult = await documentApi.uploadText(newText);
      }

      // If upload successful, navigate to Step 3 with the new document
      // 如果上传成功，使用新文档跳转到 Step 3
      if (uploadResult) {
        const route = mode === 'yolo'
          ? `/yolo/${sessionId}`
          : `/intervention/${sessionId}`;
        navigate(route);
      }
    } catch (err) {
      console.error('Failed to upload modified document:', err);
      alert('上传失败，请重试');
    } finally {
      setIsConfirming(false);
    }
  }, [documentId, sessionId, modifyMode, newFile, newText, mode, navigate]);

  // Handle continue to Step 3
  // 处理继续到 Step 3
  const handleContinue = useCallback(() => {
    if (!sessionId) {
      console.error('No session ID available for Step 3 navigation');
      return;
    }
    const route = mode === 'yolo' ? `/yolo/${sessionId}` : `/intervention/${sessionId}`;
    navigate(route);
  }, [sessionId, mode, navigate]);

  // Handle skip to Step 3
  // 处理跳过到 Step 3
  const handleSkip = useCallback(() => {
    if (!sessionId) {
      console.error('No session ID available for Step 3 navigation');
      return;
    }
    const route = mode === 'yolo' ? `/yolo/${sessionId}` : `/intervention/${sessionId}`;
    navigate(route);
  }, [sessionId, mode, navigate]);

  // Handle back to Step 1-2
  // 处理返回 Step 1-2
  const handleBack = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/step1-2/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

  // Get score color
  // 获取分数颜色
  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Get severity color
  // 获取严重程度颜色
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-700 border-red-300';
      case 'medium': return 'bg-amber-100 text-amber-700 border-amber-300';
      case 'low': return 'bg-green-100 text-green-700 border-green-300';
      default: return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  // Loading state
  // 加载状态
  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex items-center justify-center min-h-[50vh]">
          <LoadingMessage category="transition" size="lg" showEnglish={true} />
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
            返回 Step 1-2
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
            <div className="p-2 rounded-lg bg-teal-100 text-teal-600 mr-3">
              <Link className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Step 2: 段落衔接
              </h1>
              <p className="text-gray-600 mt-1">
                Paragraph Transition Analysis
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
          <span className="text-green-600">Step 1-2 ✓</span>
          <span className="mx-2">→</span>
          <span className="font-medium text-teal-600">Step 2</span>
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
                  平均衔接分数 / Average Smoothness Score
                </h3>
                <p className="text-sm text-gray-500">
                  越高表示段落间过渡越自然
                </p>
              </div>
              <div className="text-right">
                <p className={clsx('text-4xl font-bold', getScoreColor(result.avgSmoothnessScore))}>
                  {result.avgSmoothnessScore}
                </p>
              </div>
            </div>

            {/* Statistics */}
            {/* 统计信息 */}
            <div className="grid grid-cols-4 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-gray-600">
                  {result.totalTransitions}
                </p>
                <p className="text-sm text-gray-600">总衔接数</p>
              </div>
              <div className="p-3 bg-red-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-red-600">
                  {result.highRiskCount}
                </p>
                <p className="text-sm text-gray-600">高风险</p>
              </div>
              <div className="p-3 bg-amber-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-amber-600">
                  {result.mediumRiskCount}
                </p>
                <p className="text-sm text-gray-600">中风险</p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-green-600">
                  {result.lowRiskCount}
                </p>
                <p className="text-sm text-gray-600">低风险</p>
              </div>
            </div>
          </div>

          {/* Unified Issues List with Multi-select */}
          {/* 统一问题列表（多选） */}
          {unifiedIssues.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                  <AlertTriangle className="w-5 h-5 text-amber-500 mr-2" />
                  检测到的问题 ({unifiedIssues.length})
                </h3>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={toggleSelectAll}
                    className="flex items-center text-sm text-blue-600 hover:text-blue-700"
                  >
                    {selectedIssueIndices.size === unifiedIssues.length ? (
                      <>
                        <CheckSquare className="w-4 h-4 mr-1" />
                        取消全选
                      </>
                    ) : (
                      <>
                        <Square className="w-4 h-4 mr-1" />
                        全选
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Issues list */}
              {/* 问题列表 */}
              <div className="space-y-3">
                {unifiedIssues.map((issue, idx) => (
                  <div
                    key={issue.id}
                    className={clsx(
                      'p-4 rounded-lg border-2 transition-all',
                      getSeverityColor(issue.severity),
                      selectedIssueIndices.has(idx) && 'ring-2 ring-blue-500'
                    )}
                  >
                    <div className="flex items-start">
                      {/* Checkbox */}
                      <button
                        onClick={() => toggleIssueSelection(idx)}
                        className="mr-3 mt-0.5 flex-shrink-0"
                      >
                        {selectedIssueIndices.has(idx) ? (
                          <CheckSquare className="w-5 h-5 text-blue-600" />
                        ) : (
                          <Square className="w-5 h-5 text-gray-400" />
                        )}
                      </button>

                      {/* Issue content */}
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className={clsx(
                            'text-xs px-2 py-0.5 rounded font-medium',
                            issue.severity === 'high' && 'bg-red-200 text-red-700',
                            issue.severity === 'medium' && 'bg-amber-200 text-amber-700',
                            issue.severity === 'low' && 'bg-green-200 text-green-700'
                          )}>
                            {issue.severity === 'high' ? '高风险' :
                             issue.severity === 'medium' ? '中风险' : '低风险'}
                          </span>
                          <span className="text-xs text-gray-500">
                            {issue.affectedPositions.join(', ')}
                          </span>
                        </div>
                        <p className="text-gray-800 mt-1">
                          {issue.descriptionZh}
                        </p>
                        <p className="text-gray-500 text-sm mt-0.5">
                          {issue.description}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Merge modify buttons */}
              {/* 合并修改按钮 */}
              {selectedIssueIndices.size > 0 && (
                <div className="mt-4 pt-4 border-t flex items-center justify-between">
                  <p className="text-sm text-gray-600">
                    已选择 {selectedIssueIndices.size} 个问题
                  </p>
                  <div className="flex space-x-3">
                    <Button
                      variant="outline"
                      onClick={() => openMergeConfirm('prompt')}
                    >
                      <ClipboardCopy className="w-4 h-4 mr-2" />
                      生成修改提示词
                    </Button>
                    <Button
                      variant="primary"
                      onClick={() => openMergeConfirm('apply')}
                    >
                      <Wand2 className="w-4 h-4 mr-2" />
                      AI直接修改
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* No issues */}
          {/* 无问题 */}
          {unifiedIssues.length === 0 && result.transitions && result.transitions.length > 0 && (
            <div className="card p-6 bg-green-50 border border-green-200 text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-green-800">
                衔接质量良好
              </h3>
              <p className="text-green-600 mt-1">
                All transitions are natural and low risk
              </p>
            </div>
          )}

          {/* Merge Confirm Modal */}
          {/* 合并确认对话框 */}
          {showMergeConfirm && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <h3 className="text-lg font-semibold mb-4">
                  {mergeMode === 'prompt' ? '生成修改提示词' : 'AI直接修改'}
                </h3>
                <p className="text-gray-600 mb-4">
                  已选择 {selectedIssueIndices.size} 个问题进行
                  {mergeMode === 'prompt' ? '提示词生成' : 'AI修改'}
                </p>
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
                  <p className="text-sm text-amber-800">
                    <strong>注意：</strong>系统会自动告知AI保持 Step 1-1 和 Step 1-2 中的改进，只修改当前选中的衔接问题。
                  </p>
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    附加说明（可选）
                  </label>
                  <textarea
                    value={mergeUserNotes}
                    onChange={(e) => setMergeUserNotes(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="请输入额外的修改要求..."
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <Button
                    variant="outline"
                    onClick={() => setShowMergeConfirm(false)}
                    disabled={isMerging}
                  >
                    取消
                  </Button>
                  <Button
                    variant="primary"
                    onClick={executeMergeModify}
                    disabled={isMerging}
                  >
                    {isMerging ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        处理中...
                      </>
                    ) : (
                      '确认'
                    )}
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Merge Result Display */}
          {/* 合并结果显示 */}
          {mergeResult && (
            <div className="card p-6 border-2 border-blue-200 bg-blue-50">
              {mergeResult.type === 'prompt' ? (
                <>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-blue-800">
                      生成的修改提示词
                    </h3>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={copyMergePrompt}
                    >
                      {copiedMergePrompt ? (
                        <>
                          <Check className="w-4 h-4 mr-1" />
                          已复制
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4 mr-1" />
                          复制
                        </>
                      )}
                    </Button>
                  </div>
                  <div className="bg-white rounded-lg p-4 border max-h-60 overflow-y-auto">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700">
                      {mergeResult.prompt}
                    </pre>
                  </div>
                  {mergeResult.promptZh && (
                    <p className="text-sm text-blue-600 mt-2">
                      {mergeResult.promptZh}
                    </p>
                  )}
                  <div className="mt-4 flex justify-end">
                    <Button
                      variant="outline"
                      onClick={() => setMergeResult(null)}
                    >
                      <X className="w-4 h-4 mr-1" />
                      关闭
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-blue-800">
                      AI修改结果
                    </h3>
                    <div className="flex items-center space-x-2">
                      {mergeResult.remainingAttempts !== undefined && (
                        <span className="text-sm text-gray-500">
                          剩余重试次数: {MAX_REGENERATE - regenerateCount}
                        </span>
                      )}
                    </div>
                  </div>
                  {mergeResult.changesSummaryZh && (
                    <p className="text-sm text-blue-700 mb-3">
                      {mergeResult.changesSummaryZh}
                    </p>
                  )}
                  <div className="bg-white rounded-lg p-4 border max-h-60 overflow-y-auto">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700">
                      {mergeResult.modifiedText}
                    </pre>
                  </div>
                  <div className="mt-4 flex justify-end space-x-3">
                    <Button
                      variant="outline"
                      onClick={handleRegenerate}
                      disabled={regenerateCount >= MAX_REGENERATE}
                    >
                      <RotateCcw className="w-4 h-4 mr-1" />
                      重新生成
                    </Button>
                    <Button
                      variant="primary"
                      onClick={handleAcceptModification}
                    >
                      <Check className="w-4 h-4 mr-1" />
                      采纳修改
                    </Button>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Document Modification Section */}
          {/* 文档修改区域 */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              <Upload className="w-5 h-5 mr-2 text-blue-500" />
              上传修改后的文档
            </h3>

            {/* Mode toggle */}
            {/* 模式切换 */}
            <div className="flex space-x-2 mb-4">
              <button
                onClick={() => setModifyMode('file')}
                className={clsx(
                  'px-4 py-2 rounded-lg flex items-center transition-colors',
                  modifyMode === 'file'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >
                <FileText className="w-4 h-4 mr-2" />
                上传文件
              </button>
              <button
                onClick={() => setModifyMode('text')}
                className={clsx(
                  'px-4 py-2 rounded-lg flex items-center transition-colors',
                  modifyMode === 'text'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >
                <Type className="w-4 h-4 mr-2" />
                粘贴文本
              </button>
            </div>

            {/* File upload mode */}
            {/* 文件上传模式 */}
            {modifyMode === 'file' && (
              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.docx"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className={clsx(
                    'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
                    newFile
                      ? 'border-green-300 bg-green-50'
                      : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
                  )}
                >
                  {newFile ? (
                    <div className="flex items-center justify-center">
                      <FileText className="w-8 h-8 text-green-500 mr-3" />
                      <div className="text-left">
                        <p className="font-medium text-green-700">{newFile.name}</p>
                        <p className="text-sm text-green-600">
                          {(newFile.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                  ) : (
                    <>
                      <Upload className="w-10 h-10 text-gray-400 mx-auto mb-2" />
                      <p className="text-gray-600">点击或拖拽上传修改后的文档</p>
                      <p className="text-sm text-gray-400 mt-1">支持 TXT、DOCX 格式</p>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Text paste mode */}
            {/* 文本粘贴模式 */}
            {modifyMode === 'text' && (
              <textarea
                value={newText}
                onChange={(e) => setNewText(e.target.value)}
                className="w-full h-48 px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 resize-none"
                placeholder="在此粘贴修改后的文本..."
              />
            )}
          </div>

          {/* Action Buttons */}
          {/* 操作按钮 */}
          <div className="flex justify-between pt-4">
            <Button variant="outline" onClick={handleSkip}>
              <SkipForward className="w-4 h-4 mr-2" />
              跳过此步
            </Button>
            <div className="flex space-x-3">
              {(newFile || newText.trim()) && (
                <Button
                  variant="primary"
                  onClick={handleConfirmModify}
                  disabled={isConfirming}
                >
                  {isConfirming ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      确认中...
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4 mr-2" />
                      确认并继续
                    </>
                  )}
                </Button>
              )}
              <Button variant="primary" onClick={handleContinue}>
                继续 Step 3
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
