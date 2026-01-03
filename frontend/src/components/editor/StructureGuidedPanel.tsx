import { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Layers,
  Link2,
  AlertTriangle,
  CheckCircle,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Shuffle,
} from 'lucide-react';
import { clsx } from 'clsx';
import type {
  StructureIssueItem,
  StructureIssueListResponse,
  IssueStatus,
  ReorderSuggestionResponse,
} from '../../types';
import Button from '../common/Button';
import InfoTooltip from '../common/InfoTooltip';
import StructureIssueCard from './StructureIssueCard';
import { structureGuidanceApi } from '../../services/api';

interface StructureGuidedPanelProps {
  documentId: string;
  onComplete?: () => void;
  onSkip?: () => void;
}

/**
 * Structure Guided Panel - Level 1 Guided Interaction
 * 结构指引面板 - Level 1 指引式交互
 *
 * Displays categorized structure issues with expandable guidance cards
 * 显示分类结构问题和可展开的指引卡片
 */
export default function StructureGuidedPanel({
  documentId,
  onComplete,
  onSkip,
}: StructureGuidedPanelProps) {
  // State
  // 状态
  const [isLoading, setIsLoading] = useState(true);
  const [issueData, setIssueData] = useState<StructureIssueListResponse | null>(null);
  const [structureIssues, setStructureIssues] = useState<StructureIssueItem[]>([]);
  const [transitionIssues, setTransitionIssues] = useState<StructureIssueItem[]>([]);
  const [showStructureSection, setShowStructureSection] = useState(true);
  const [showTransitionSection, setShowTransitionSection] = useState(true);
  const [showLowSeverity, setShowLowSeverity] = useState(false);
  const [reorderSuggestion, setReorderSuggestion] = useState<ReorderSuggestionResponse | null>(null);
  const [isLoadingReorder, setIsLoadingReorder] = useState(false);
  const [showReorderPanel, setShowReorderPanel] = useState(false);

  // Load issues on mount
  // 挂载时加载问题
  useEffect(() => {
    loadIssues();
  }, [documentId, showLowSeverity]);

  // Load issues from API
  // 从 API 加载问题
  const loadIssues = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await structureGuidanceApi.getIssues(documentId, showLowSeverity);
      // Cast the response to proper type - API returns string but we need StructureIssueType
      // 将响应转换为正确的类型 - API返回string但我们需要StructureIssueType
      setIssueData(response as unknown as StructureIssueListResponse);
      setStructureIssues(response.structureIssues as StructureIssueItem[]);
      setTransitionIssues(response.transitionIssues as StructureIssueItem[]);
    } catch (error) {
      console.error('Failed to load issues:', error);
    } finally {
      setIsLoading(false);
    }
  }, [documentId, showLowSeverity]);

  // Handle issue status change
  // 处理问题状态变更
  const handleStatusChange = useCallback((issueId: string, newStatus: IssueStatus) => {
    setStructureIssues(prev =>
      prev.map(issue =>
        issue.id === issueId ? { ...issue, status: newStatus } : issue
      )
    );
    setTransitionIssues(prev =>
      prev.map(issue =>
        issue.id === issueId ? { ...issue, status: newStatus } : issue
      )
    );
  }, []);

  // Handle text applied (could update document)
  // 处理文本应用（可更新文档）
  const handleTextApplied = useCallback((issueId: string, text: string) => {
    console.log(`Text applied for issue ${issueId}:`, text);
    // In a full implementation, this would update the document
    // 在完整实现中，这将更新文档
  }, []);

  // Load reorder suggestion
  // 加载重排建议
  const loadReorderSuggestion = useCallback(async () => {
    setIsLoadingReorder(true);
    try {
      const response = await structureGuidanceApi.getReorderSuggestion(documentId);
      setReorderSuggestion(response);
      setShowReorderPanel(true);
    } catch (error) {
      console.error('Failed to load reorder suggestion:', error);
    } finally {
      setIsLoadingReorder(false);
    }
  }, [documentId]);

  // Calculate progress
  // 计算进度
  const allIssues = [...structureIssues, ...transitionIssues];
  const resolvedCount = allIssues.filter(
    issue => issue.status === 'fixed' || issue.status === 'skipped'
  ).length;
  const totalCount = allIssues.length;
  const progress = totalCount > 0 ? Math.round((resolvedCount / totalCount) * 100) : 0;

  // Check if all done
  // 检查是否全部完成
  const isAllDone = resolvedCount === totalCount && totalCount > 0;

  // Get risk level color
  // 获取风险等级颜色
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'bg-red-100 text-red-700';
      case 'medium':
        return 'bg-amber-100 text-amber-700';
      default:
        return 'bg-green-100 text-green-700';
    }
  };

  return (
    <div className="card p-4 space-y-4">
      {/* Header */}
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText className="w-5 h-5 text-indigo-600" />
          <h3 className="font-semibold text-gray-800">
            结构问题指引
          </h3>
          <span className="text-sm text-gray-500">/ Structure Guidance</span>
          <InfoTooltip
            title="Level 1: 指引式交互"
            content="逐个展开问题，获取详细改进意见和参考版本。你可以直接使用参考，也可以自行修改。"
          />
        </div>

        {/* Score and risk badge */}
        {/* 分数和风险徽章 */}
        {issueData && (
          <div className="flex items-center space-x-2">
            <span className={clsx(
              'px-2 py-0.5 rounded-full text-xs font-medium',
              getRiskColor(issueData.riskLevel)
            )}>
              结构分数: {issueData.structureScore}
            </span>
            {issueData.riskLevel === 'low' && (
              <CheckCircle className="w-4 h-4 text-green-500" />
            )}
            {issueData.riskLevel !== 'low' && (
              <AlertTriangle className={clsx(
                'w-4 h-4',
                issueData.riskLevel === 'high' ? 'text-red-500' : 'text-amber-500'
              )} />
            )}
          </div>
        )}
      </div>

      {/* Loading state */}
      {/* 加载状态 */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-indigo-500 mr-2" />
          <span className="text-gray-600">正在分析文档结构...</span>
        </div>
      )}

      {/* Issue counts summary */}
      {/* 问题数量摘要 */}
      {!isLoading && issueData && (
        <div className="flex flex-wrap gap-3 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-red-500"></span>
            <span className="text-xs text-gray-600">
              高风险: {issueData.highSeverityCount}
            </span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span>
            <span className="text-xs text-gray-600">
              中风险: {issueData.mediumSeverityCount}
            </span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
            <span className="text-xs text-gray-600">
              低风险: {issueData.lowSeverityCount}
            </span>
          </div>
          <div className="flex-1"></div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-600">
              进度: {resolvedCount}/{totalCount}
            </span>
            <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Structure Issues Section */}
      {/* 全文结构问题部分 */}
      {!isLoading && structureIssues.length > 0 && (
        <div className="space-y-2">
          <button
            onClick={() => setShowStructureSection(!showStructureSection)}
            className="flex items-center w-full text-left py-1"
          >
            {showStructureSection ? (
              <ChevronUp className="w-4 h-4 mr-1 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 mr-1 text-gray-500" />
            )}
            <Layers className="w-4 h-4 mr-2 text-indigo-500" />
            <span className="font-medium text-gray-700">全文结构问题</span>
            <span className="ml-2 text-xs text-gray-500">
              ({structureIssues.length} 个)
            </span>
            <span className="ml-2 px-1.5 py-0.5 bg-indigo-100 text-indigo-700 text-xs rounded">
              优先处理
            </span>
          </button>

          {showStructureSection && (
            <div className="space-y-2 pl-6">
              {structureIssues.map(issue => (
                <StructureIssueCard
                  key={issue.id}
                  issue={issue}
                  documentId={documentId}
                  onStatusChange={handleStatusChange}
                  onTextApplied={handleTextApplied}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Transition Issues Section */}
      {/* 段落关系问题部分 */}
      {!isLoading && transitionIssues.length > 0 && (
        <div className="space-y-2">
          <button
            onClick={() => setShowTransitionSection(!showTransitionSection)}
            className="flex items-center w-full text-left py-1"
          >
            {showTransitionSection ? (
              <ChevronUp className="w-4 h-4 mr-1 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 mr-1 text-gray-500" />
            )}
            <Link2 className="w-4 h-4 mr-2 text-teal-500" />
            <span className="font-medium text-gray-700">段落关系问题</span>
            <span className="ml-2 text-xs text-gray-500">
              ({transitionIssues.length} 个)
            </span>
          </button>

          {showTransitionSection && (
            <div className="space-y-2 pl-6">
              {transitionIssues.map(issue => (
                <StructureIssueCard
                  key={issue.id}
                  issue={issue}
                  documentId={documentId}
                  onStatusChange={handleStatusChange}
                  onTextApplied={handleTextApplied}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* No issues message */}
      {/* 无问题消息 */}
      {!isLoading && totalCount === 0 && (
        <div className="py-8 text-center">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
          <p className="text-gray-700 font-medium">文档结构良好</p>
          <p className="text-sm text-gray-500">未检测到明显的 AI 结构特征</p>
        </div>
      )}

      {/* Reorder Suggestion Panel */}
      {/* 重排建议面板 */}
      {showReorderPanel && reorderSuggestion && (
        <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Shuffle className="w-4 h-4 text-purple-600" />
              <span className="font-medium text-purple-700">段落重排建议</span>
            </div>
            <button
              onClick={() => setShowReorderPanel(false)}
              className="text-xs text-purple-600 hover:text-purple-800"
            >
              收起
            </button>
          </div>

          {reorderSuggestion.changes.length > 0 ? (
            <>
              <p className="text-sm text-purple-700">
                {reorderSuggestion.overallGuidanceZh}
              </p>
              <div className="space-y-1">
                {reorderSuggestion.changes.map((change, idx) => (
                  <div key={idx} className="text-xs text-purple-600 pl-2 border-l-2 border-purple-300">
                    P{change.paragraphIndex + 1}: {change.reasonZh}
                  </div>
                ))}
              </div>
              {reorderSuggestion.warningsZh.length > 0 && (
                <div className="text-xs text-amber-600">
                  ⚠️ {reorderSuggestion.warningsZh.join(' ')}
                </div>
              )}
              <p className="text-xs text-purple-500">
                预览: {reorderSuggestion.previewFlowZh}
              </p>
            </>
          ) : (
            <p className="text-sm text-purple-600">
              当前段落顺序较为合理，无需重排。
            </p>
          )}
        </div>
      )}

      {/* Toggle low severity */}
      {/* 切换低风险问题 */}
      {!isLoading && (
        <div className="flex items-center space-x-2 text-xs text-gray-500">
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={showLowSeverity}
              onChange={(e) => setShowLowSeverity(e.target.checked)}
              className="mr-1.5"
            />
            显示低风险问题
          </label>
        </div>
      )}

      {/* Action buttons */}
      {/* 操作按钮 */}
      <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100">
        <Button
          variant="ghost"
          size="sm"
          onClick={loadIssues}
          disabled={isLoading}
        >
          <RefreshCw className={clsx('w-4 h-4 mr-1', isLoading && 'animate-spin')} />
          刷新
        </Button>

        {structureIssues.some(i => i.type === 'linear_flow' && i.status === 'pending') && (
          <Button
            variant="secondary"
            size="sm"
            onClick={loadReorderSuggestion}
            disabled={isLoadingReorder}
          >
            {isLoadingReorder ? (
              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
            ) : (
              <Shuffle className="w-4 h-4 mr-1" />
            )}
            获取重排建议
          </Button>
        )}

        <div className="flex-1"></div>

        {onSkip && (
          <Button variant="ghost" size="sm" onClick={onSkip}>
            跳过 Level 1
          </Button>
        )}

        {isAllDone && onComplete && (
          <Button size="sm" onClick={onComplete}>
            <CheckCircle className="w-4 h-4 mr-1" />
            完成，进入 Level 2
          </Button>
        )}
      </div>
    </div>
  );
}
