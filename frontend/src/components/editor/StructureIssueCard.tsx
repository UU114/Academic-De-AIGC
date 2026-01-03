import { useState, useCallback } from 'react';
import {
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  XCircle,
  Loader2,
  Lightbulb,
  Copy,
  Check,
} from 'lucide-react';
import { clsx } from 'clsx';
import type {
  StructureIssueItem,
  IssueGuidanceResponse,
  IssueStatus,
} from '../../types';
import Button from '../common/Button';
import { InlineLoading } from '../common/LoadingMessage';
import { structureGuidanceApi } from '../../services/api';

interface StructureIssueCardProps {
  issue: StructureIssueItem;
  documentId: string;
  onStatusChange?: (issueId: string, newStatus: IssueStatus) => void;
  onTextApplied?: (issueId: string, text: string) => void;
}

/**
 * Structure Issue Card with Expandable Guidance
 * 可展开指引的结构问题卡片
 *
 * Displays a single structure issue with:
 * - Collapsed: Brief info, severity badge, expand button
 * - Expanded: Detailed guidance, reference version, user input
 */
export default function StructureIssueCard({
  issue,
  documentId,
  onStatusChange,
  onTextApplied,
}: StructureIssueCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [guidance, setGuidance] = useState<IssueGuidanceResponse | null>(null);
  const [userText, setUserText] = useState('');
  const [isCopied, setIsCopied] = useState(false);
  const [isApplying, setIsApplying] = useState(false);

  // Get severity icon
  // 获取严重程度图标
  const getSeverityIcon = () => {
    switch (issue.severity) {
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'medium':
        return <AlertCircle className="w-4 h-4 text-amber-500" />;
      default:
        return <Info className="w-4 h-4 text-blue-500" />;
    }
  };

  // Get severity color classes
  // 获取严重程度颜色类
  const getSeverityClasses = () => {
    switch (issue.severity) {
      case 'high':
        return 'border-red-200 bg-red-50 hover:bg-red-100';
      case 'medium':
        return 'border-amber-200 bg-amber-50 hover:bg-amber-100';
      default:
        return 'border-blue-200 bg-blue-50 hover:bg-blue-100';
    }
  };

  // Get status badge
  // 获取状态徽章
  const getStatusBadge = () => {
    switch (issue.status) {
      case 'fixed':
        return (
          <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full flex items-center">
            <CheckCircle className="w-3 h-3 mr-1" />
            已修复
          </span>
        );
      case 'skipped':
        return (
          <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full flex items-center">
            <XCircle className="w-3 h-3 mr-1" />
            已跳过
          </span>
        );
      default:
        return null;
    }
  };

  // Handle expand/collapse
  // 处理展开/收起
  const handleToggleExpand = useCallback(async () => {
    if (!isExpanded && !guidance && issue.status === 'pending') {
      // Fetch guidance when expanding for the first time
      // 首次展开时获取指引
      setIsExpanded(true);
      setIsLoading(true);
      try {
        const response = await structureGuidanceApi.getGuidance(
          documentId,
          issue.id,
          issue.type,
          {
            affectedPositions: issue.affectedPositions,
            connectorWord: issue.connectorWord,
          }
        );
        setGuidance(response);
        // Pre-fill user text with reference if available
        // 如果有参考版本，预填用户文本
        if (response.referenceVersion) {
          setUserText(response.referenceVersion);
        }
      } catch (error) {
        console.error('Failed to fetch guidance:', error);
      } finally {
        setIsLoading(false);
      }
    } else {
      setIsExpanded(!isExpanded);
    }
  }, [isExpanded, guidance, issue, documentId]);

  // Handle apply fix
  // 处理应用修复
  const handleApplyFix = useCallback(async (
    fixType: 'use_reference' | 'custom' | 'skip' | 'mark_done'
  ) => {
    setIsApplying(true);
    try {
      const response = await structureGuidanceApi.applyFix(
        documentId,
        issue.id,
        fixType,
        {
          customText: fixType === 'custom' ? userText : undefined,
          affectedPositions: issue.affectedPositions,
        }
      );

      if (response.success) {
        onStatusChange?.(issue.id, response.newStatus as IssueStatus);
        if (fixType !== 'skip' && response.updatedText) {
          onTextApplied?.(issue.id, response.updatedText);
        }
        setIsExpanded(false);
      }
    } catch (error) {
      console.error('Failed to apply fix:', error);
    } finally {
      setIsApplying(false);
    }
  }, [documentId, issue.id, issue.affectedPositions, userText, onStatusChange, onTextApplied]);

  // Handle copy reference
  // 处理复制参考
  const handleCopyReference = useCallback(() => {
    if (guidance?.referenceVersion) {
      navigator.clipboard.writeText(guidance.referenceVersion);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }
  }, [guidance?.referenceVersion]);

  // Parse guidance sections
  // 解析指引部分
  const parseGuidanceSections = (text: string) => {
    const sections: { title: string; content: string }[] = [];
    const patterns = [
      { marker: '【问题分析】', title: '问题分析' },
      { marker: '【改进策略】', title: '改进策略' },
      { marker: '【具体建议】', title: '具体建议' },
    ];

    let remaining = text;
    for (const { marker, title } of patterns) {
      const index = remaining.indexOf(marker);
      if (index !== -1) {
        const contentStart = index + marker.length;
        const nextMarkerIndex = patterns
          .map(p => remaining.indexOf(p.marker, contentStart))
          .filter(i => i !== -1)
          .sort((a, b) => a - b)[0];

        const content = nextMarkerIndex
          ? remaining.slice(contentStart, nextMarkerIndex).trim()
          : remaining.slice(contentStart).trim();

        if (content) {
          sections.push({ title, content });
        }
      }
    }

    // If no sections found, return the whole text as one section
    // 如果没有找到分节，将整个文本作为一节返回
    if (sections.length === 0 && text.trim()) {
      sections.push({ title: '指引', content: text.trim() });
    }

    return sections;
  };

  // Don't show if already fixed/skipped and not expanded
  // 如果已修复/跳过且未展开，不显示详细内容
  const isResolved = issue.status === 'fixed' || issue.status === 'skipped';

  return (
    <div
      className={clsx(
        'rounded-lg border transition-all',
        isResolved ? 'border-gray-200 bg-gray-50 opacity-60' : getSeverityClasses()
      )}
    >
      {/* Header - Always visible */}
      {/* 头部 - 始终可见 */}
      <button
        onClick={handleToggleExpand}
        disabled={isResolved}
        className={clsx(
          'w-full p-3 flex items-center justify-between text-left',
          !isResolved && 'cursor-pointer',
          isResolved && 'cursor-default'
        )}
      >
        <div className="flex items-center space-x-2 flex-1 min-w-0">
          {getSeverityIcon()}
          <span className="font-medium text-sm text-gray-800 truncate">
            {issue.titleZh}
          </span>
          {getStatusBadge()}
        </div>
        <div className="flex items-center space-x-2 ml-2">
          {issue.canGenerateReference && !isResolved && (
            <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-xs rounded">
              可参考
            </span>
          )}
          {!isResolved && (
            isExpanded ? (
              <ChevronUp className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            )
          )}
        </div>
      </button>

      {/* Brief description - visible when collapsed */}
      {/* 简要描述 - 收起时可见 */}
      {!isExpanded && !isResolved && (
        <div className="px-3 pb-3 -mt-1">
          <p className="text-xs text-gray-600">{issue.briefZh}</p>
          {issue.affectedPositions.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {issue.affectedPositions.map((pos, idx) => (
                <span
                  key={idx}
                  className="px-1.5 py-0.5 bg-gray-200 text-gray-700 text-xs font-mono rounded"
                >
                  {pos}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Expanded content with guidance */}
      {/* 展开的内容和指引 */}
      {isExpanded && !isResolved && (
        <div className="px-3 pb-3 pt-1 border-t border-current/10 space-y-3">
          {/* Loading state */}
          {/* 加载状态 */}
          {isLoading && (
            <div className="p-3 bg-white/50 rounded">
              <InlineLoading category="structure" showEnglish={false} />
            </div>
          )}

          {/* Guidance content */}
          {/* 指引内容 */}
          {guidance && !isLoading && (
            <>
              {/* Affected text preview */}
              {/* 受影响文本预览 */}
              {guidance.affectedText && (
                <div className="p-2 bg-white/80 rounded border border-gray-200">
                  <p className="text-xs text-gray-500 mb-1">📍 原文：</p>
                  <p className="text-sm text-gray-700 italic">
                    "{guidance.affectedText.slice(0, 200)}
                    {guidance.affectedText.length > 200 ? '...' : ''}"
                  </p>
                </div>
              )}

              {/* Parsed guidance sections */}
              {/* 解析后的指引部分 */}
              <div className="space-y-2">
                {parseGuidanceSections(guidance.guidanceZh).map((section, idx) => (
                  <div key={idx} className="text-sm">
                    <span className={clsx(
                      'font-medium',
                      section.title === '问题分析' && 'text-red-600',
                      section.title === '改进策略' && 'text-blue-600',
                      section.title === '具体建议' && 'text-green-600'
                    )}>
                      【{section.title}】
                    </span>
                    <span className="text-gray-700 ml-1">{section.content}</span>
                  </div>
                ))}
              </div>

              {/* Key concepts for semantic echo */}
              {/* 语义回声的关键概念 */}
              {guidance.keyConcepts && (
                guidance.keyConcepts.fromPrev.length > 0 ||
                guidance.keyConcepts.fromNext.length > 0
              ) && (
                <div className="p-2 bg-indigo-50 rounded border border-indigo-200">
                  <p className="text-xs text-indigo-600 mb-1">
                    🔗 可用于语义回声的关键概念：
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {guidance.keyConcepts.fromPrev.map((concept, idx) => (
                      <span
                        key={`prev-${idx}`}
                        className="px-1.5 py-0.5 bg-indigo-100 text-indigo-700 text-xs rounded"
                      >
                        {concept}
                      </span>
                    ))}
                    {guidance.keyConcepts.fromNext.map((concept, idx) => (
                      <span
                        key={`next-${idx}`}
                        className="px-1.5 py-0.5 bg-purple-100 text-purple-700 text-xs rounded"
                      >
                        {concept}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Reference version */}
              {/* 参考版本 */}
              {guidance.referenceVersion && (
                <div className="p-2 bg-green-50 rounded border border-green-200">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-xs text-green-600 flex items-center">
                      <Lightbulb className="w-3 h-3 mr-1" />
                      💡 参考版本：
                    </p>
                    <button
                      onClick={handleCopyReference}
                      className="text-xs text-green-600 hover:text-green-800 flex items-center"
                    >
                      {isCopied ? (
                        <>
                          <Check className="w-3 h-3 mr-1" />
                          已复制
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3 mr-1" />
                          复制
                        </>
                      )}
                    </button>
                  </div>
                  <p className="text-sm text-green-800 font-serif italic">
                    "{guidance.referenceVersion}"
                  </p>
                  {guidance.referenceExplanationZh && (
                    <p className="text-xs text-green-600 mt-1">
                      → {guidance.referenceExplanationZh}
                    </p>
                  )}
                </div>
              )}

              {/* No reference explanation */}
              {/* 无参考版本的解释 */}
              {!guidance.referenceVersion && guidance.whyNoReference && (
                <div className="p-2 bg-amber-50 rounded border border-amber-200">
                  <p className="text-xs text-amber-700 flex items-start">
                    <Info className="w-3 h-3 mr-1 mt-0.5 flex-shrink-0" />
                    {guidance.whyNoReference}
                  </p>
                </div>
              )}

              {/* User input area (like Track C) */}
              {/* 用户输入区（类似轨道C） */}
              {guidance.canGenerateReference && (
                <div className="space-y-2">
                  <p className="text-xs text-gray-600">✏️ 你的修改：</p>
                  <textarea
                    value={userText}
                    onChange={(e) => setUserText(e.target.value)}
                    placeholder={guidance.referenceVersion
                      ? "参考版本已预填，你可以直接使用或修改..."
                      : "输入你的修改版本..."
                    }
                    className="w-full p-2 text-sm border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    rows={3}
                  />
                </div>
              )}

              {/* Action buttons */}
              {/* 操作按钮 */}
              <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-200">
                {guidance.referenceVersion && (
                  <Button
                    size="sm"
                    onClick={() => handleApplyFix('use_reference')}
                    disabled={isApplying}
                  >
                    {isApplying ? (
                      <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                    ) : null}
                    使用参考版本
                  </Button>
                )}
                {guidance.canGenerateReference && userText && (
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleApplyFix('custom')}
                    disabled={isApplying || !userText.trim()}
                  >
                    应用我的修改
                  </Button>
                )}
                {!guidance.canGenerateReference && (
                  <Button
                    size="sm"
                    onClick={() => handleApplyFix('mark_done')}
                    disabled={isApplying}
                  >
                    已理解，稍后处理 ✓
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleApplyFix('skip')}
                  disabled={isApplying}
                >
                  跳过
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
