import { useState, useEffect } from 'react';
import { Sparkles, Wrench, Edit3, ChevronDown, ChevronUp, CheckCircle2, MousePointerClick, X, SkipForward, Flag } from 'lucide-react';
import { clsx } from 'clsx';
import type { SuggestResponse, Suggestion, SuggestionSource } from '../../types';
import Button from '../common/Button';
import RiskBadge from '../common/RiskBadge';
import InfoTooltip from '../common/InfoTooltip';
import LoadingMessage from '../common/LoadingMessage';
import SentenceAnalysisPanel from './SentenceAnalysisPanel';
import CustomInputSection from './CustomInputSection';
import { useSessionStore } from '../../stores/sessionStore';

interface AnalysisState {
  showAnalysis: boolean;
  loadingAnalysis: boolean;
  hasResult: boolean;
  expandedTrack: 'llm' | 'rule' | 'custom' | null;
  error?: string;
}

interface SuggestionPanelProps {
  suggestions: SuggestResponse | null;
  isLoading?: boolean;
  onApply: (source: SuggestionSource) => void;
  sentenceProcessed?: boolean;
  sentenceProcessedType?: 'processed' | 'skip' | 'flag';  // Type of processing / 处理类型
  sentenceId?: string;
  // Analysis state from parent
  // 来自父组件的分析状态
  analysisState?: AnalysisState;
  // Track C analysis state callbacks
  // 轨道C分析状态回调
  onAnalysisStateChange?: (state: AnalysisState) => void;
  // Custom input props - for rendering in right panel when analysis not shown
  // 自定义输入属性 - 分析未显示时在右侧渲染
  customText?: string;
  onCustomTextChange?: (text: string) => void;
  onValidateCustom?: () => void;
  validationResult?: { passed: boolean; similarity: number; message: string } | null;
  onApplyCustom?: () => void;
  onAnalysisToggle?: (show: boolean) => void;
}

/**
 * Suggestion panel with dual-track display
 * Track C input is rendered separately when analysis is shown
 * 双轨建议面板
 * 分析显示时，轨道C输入部分在外部渲染
 */
export default function SuggestionPanel({
  suggestions,
  isLoading = false,
  onApply,
  sentenceProcessed = false,
  sentenceProcessedType,
  sentenceId,
  analysisState: externalAnalysisState,
  onAnalysisStateChange,
  customText = '',
  onCustomTextChange,
  onValidateCustom,
  validationResult,
  onApplyCustom,
  onAnalysisToggle,
}: SuggestionPanelProps) {
  const [expandedTrack, setExpandedTrack] = useState<'llm' | 'rule' | 'custom' | null>('llm');

  // Reset to Track A when sentence changes
  // 切换句子时重置为轨道A
  useEffect(() => {
    setExpandedTrack('llm');
  }, [sentenceId]);

  // Subscribe to analysisCache directly from store for reactivity
  // 直接从store订阅analysisCache以获得响应性
  // Use a selector that extracts the specific entry to ensure reactivity
  // 使用提取特定条目的选择器以确保响应性
  const analysisResult = useSessionStore(state => {
    if (!sentenceId) return null;
    const cached = state.analysisCache.get(sentenceId);
    console.log('[SuggestionPanel] Reading cache for', sentenceId, ':', cached ? 'found' : 'not found');
    return cached || null;
  });

  // Use external state if provided, otherwise use defaults
  // 如果提供外部状态则使用，否则使用默认值
  const showAnalysis = externalAnalysisState?.showAnalysis ?? false;
  const loadingAnalysis = externalAnalysisState?.loadingAnalysis ?? false;

  // Close analysis handler - notify parent to close
  // 关闭分析处理器 - 通知父组件关闭
  const handleCloseAnalysis = () => {
    onAnalysisStateChange?.({
      showAnalysis: false,
      loadingAnalysis: false,
      hasResult: !!analysisResult,
      expandedTrack,
    });
  };

  // Notify parent of expanded track changes
  // 通知父组件展开轨道变化
  // IMPORTANT: When analysisResult is available, force loadingAnalysis to false
  // 重要：当分析结果可用时，强制将加载状态设为false
  useEffect(() => {
    // Only notify if there's actually a change to report
    // 仅在有变化需要报告时通知
    const effectiveLoadingAnalysis = analysisResult ? false : loadingAnalysis;
    onAnalysisStateChange?.({
      showAnalysis,
      loadingAnalysis: effectiveLoadingAnalysis,
      hasResult: !!analysisResult,
      expandedTrack,
    });
  }, [expandedTrack, analysisResult, showAnalysis, loadingAnalysis, onAnalysisStateChange]);

  if (isLoading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-center">
          <LoadingMessage category="suggestion" size="md" showEnglish={true} />
        </div>
      </div>
    );
  }

  // Show processed message with type-specific display
  // 根据处理类型显示相应消息
  if (sentenceProcessed && !suggestions && !isLoading) {
    // Determine message based on processing type
    // 根据处理类型确定消息内容
    let icon = <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-3" />;
    let title = '✓ 当前句子已处理';
    let titleEn = 'This sentence has been processed';

    if (sentenceProcessedType === 'skip') {
      icon = <SkipForward className="w-12 h-12 text-gray-400 mx-auto mb-3" />;
      title = '⏭ 当前句子已跳过';
      titleEn = 'This sentence was skipped';
    } else if (sentenceProcessedType === 'flag') {
      icon = <Flag className="w-12 h-12 text-amber-500 mx-auto mb-3" />;
      title = '🚩 当前句子已标记';
      titleEn = 'This sentence was flagged for review';
    }

    return (
      <div className="card p-6 text-center">
        {icon}
        <p className="text-lg font-medium text-gray-800 mb-2">
          {title}
        </p>
        <p className="text-xs text-gray-400 mb-4">
          {titleEn}
        </p>
        <div className="flex items-center justify-center text-gray-500 mb-4">
          <MousePointerClick className="w-4 h-4 mr-2" />
          <p className="text-sm">
            请从左侧列表选择下一个句子
          </p>
        </div>
        <p className="text-xs text-gray-400">
          Click a sentence from the sidebar to continue
        </p>
      </div>
    );
  }

  if (!suggestions) {
    return (
      <div className="card p-6">
        <p className="text-center text-gray-500">
          选择一个句子以获取修改建议
        </p>
      </div>
    );
  }

  // When Track C is expanded and analysis is shown, only show analysis panel
  // 当轨道C展开且分析显示时，只显示分析面板
  const showOnlyAnalysis = expandedTrack === 'custom' && showAnalysis;

  return (
    <div className="space-y-3">
      {/* Track A: LLM Suggestion - hide when only showing analysis */}
      {/* 轨道A: LLM建议 - 仅显示分析时隐藏 */}
      {!showOnlyAnalysis && suggestions.llmSuggestion && (
        <SuggestionTrack
          title="轨道A: LLM智能改写"
          titleEn="Track A: LLM Suggestion"
          icon={<Sparkles className="w-4 h-4" />}
          iconColor="text-purple-600"
          bgColor="bg-purple-50"
          borderColor="border-purple-200"
          suggestion={suggestions.llmSuggestion}
          originalRisk={suggestions.originalRisk}
          isExpanded={expandedTrack === 'llm'}
          onToggle={() => setExpandedTrack(expandedTrack === 'llm' ? null : 'llm')}
          onApply={() => onApply('llm')}
        />
      )}

      {/* Track B: Rule Suggestion - hide when only showing analysis */}
      {/* 轨道B: 规则建议 - 仅显示分析时隐藏 */}
      {!showOnlyAnalysis && suggestions.ruleSuggestion && (
        <SuggestionTrack
          title="轨道B: 规则建议"
          titleEn="Track B: Rule-based"
          icon={<Wrench className="w-4 h-4" />}
          iconColor="text-blue-600"
          bgColor="bg-blue-50"
          borderColor="border-blue-200"
          suggestion={suggestions.ruleSuggestion}
          originalRisk={suggestions.originalRisk}
          isExpanded={expandedTrack === 'rule'}
          onToggle={() => setExpandedTrack(expandedTrack === 'rule' ? null : 'rule')}
          onApply={() => onApply('rule')}
        />
      )}

      {/* Track C: Custom Input - only show header when not in analysis mode */}
      {/* 轨道C: 自定义修改 - 非分析模式时只显示标题 */}
      {!showOnlyAnalysis && (
        <div className={clsx(
          'card border-2 overflow-hidden transition-all duration-200',
          expandedTrack === 'custom' ? 'border-gray-300' : 'border-gray-200'
        )}>
          <button
            onClick={() => setExpandedTrack(expandedTrack === 'custom' ? null : 'custom')}
            className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center">
              <div className="p-1.5 rounded-lg bg-gray-100 text-gray-600 mr-3">
                <Edit3 className="w-4 h-4" />
              </div>
              <div className="text-left">
                <p className="font-medium text-gray-800">轨道C: 自定义修改</p>
                <p className="text-xs text-gray-500">Track C: Custom Input</p>
              </div>
            </div>
            {expandedTrack === 'custom' ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>

          {/* Custom input - shown when Track C is expanded but analysis not shown */}
          {/* 自定义输入 - 轨道C展开但分析未显示时显示 */}
          {expandedTrack === 'custom' && !showAnalysis && suggestions && onCustomTextChange && onValidateCustom && onApplyCustom && onAnalysisToggle && (
            <div className="px-4 pb-4">
              <CustomInputSection
                originalText={suggestions.original}
                customText={customText}
                onCustomTextChange={onCustomTextChange}
                onValidateCustom={onValidateCustom}
                validationResult={validationResult}
                onApplyCustom={onApplyCustom}
                onAnalysisToggle={onAnalysisToggle}
                showAnalysis={showAnalysis}
                loadingAnalysis={loadingAnalysis}
                hasAnalysisResult={!!analysisResult}
                sentenceId={sentenceId}
              />
            </div>
          )}
        </div>
      )}

      {/* Analysis Panel - shown when Track C is expanded and analysis is active */}
      {/* 分析面板 - 当轨道C展开且分析激活时显示 */}
      {showOnlyAnalysis && (
        <div className="card border-2 border-gray-300 overflow-hidden">
          {/* Header with close button */}
          {/* 带关闭按钮的标题 */}
          <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
            <div>
              <p className="font-medium text-gray-800">句子分析 / Sentence Analysis</p>
              <p className="text-xs text-gray-500">详细语法结构和改写建议</p>
            </div>
            <button
              onClick={handleCloseAnalysis}
              className="p-1 hover:bg-gray-200 rounded transition-colors"
              title="关闭分析"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Analysis content */}
          {/* 分析内容 */}
          {/* Priority: show result if available, then loading, then error */}
          {/* 优先级：有结果就显示结果，然后是加载，最后是错误 */}
          <div className="p-4 max-h-[60vh] overflow-y-auto">
            {analysisResult ? (
              <SentenceAnalysisPanel
                analysis={analysisResult}
                onClose={handleCloseAnalysis}
                hideCloseButton
              />
            ) : loadingAnalysis ? (
              <div className="p-6 bg-gray-50 rounded-lg text-center">
                <LoadingMessage category="analysis" size="md" showEnglish={true} centered />
                <p className="text-xs text-gray-400 mt-3">首次分析可能需要10-30秒 / First analysis may take 10-30s</p>
              </div>
            ) : externalAnalysisState?.error ? (
              <div className="p-4 bg-red-50 rounded-lg text-center">
                <p className="text-sm text-red-600">{externalAnalysisState.error}</p>
                <button
                  onClick={() => onAnalysisToggle?.(true)}
                  className="mt-2 text-xs text-red-500 underline hover:text-red-700"
                >
                  重试 / Retry
                </button>
              </div>
            ) : (
              <div className="p-4 bg-red-50 rounded-lg text-center">
                <p className="text-sm text-red-600">分析失败，请重试</p>
                <button
                  onClick={() => onAnalysisToggle?.(true)}
                  className="mt-2 text-xs text-red-500 underline hover:text-red-700"
                >
                  重试 / Retry
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Suggestion track sub-component
// 建议轨道子组件
function SuggestionTrack({
  title,
  titleEn,
  icon,
  iconColor,
  bgColor,
  borderColor,
  suggestion,
  originalRisk,
  isExpanded,
  onToggle,
  onApply,
}: {
  title: string;
  titleEn: string;
  icon: React.ReactNode;
  iconColor: string;
  bgColor: string;
  borderColor: string;
  suggestion: Suggestion;
  originalRisk: number;
  isExpanded: boolean;
  onToggle: () => void;
  onApply: () => void;
}) {
  const [showChanges, setShowChanges] = useState(false);

  // Determine risk level from score
  // 从分数确定风险等级
  const getRiskLevel = (score: number) => {
    if (score < 10) return 'safe';
    if (score < 25) return 'low';
    if (score < 50) return 'medium';
    return 'high';
  };

  const riskLevel = getRiskLevel(suggestion.predictedRisk);
  const riskDelta = originalRisk - suggestion.predictedRisk;
  const isImproved = riskDelta > 0;

  return (
    <div className={clsx(
      'card border-2 overflow-hidden transition-all duration-200',
      isExpanded ? borderColor : 'border-gray-200'
    )}>
      {/* Header */}
      <button
        onClick={onToggle}
        className={clsx(
          'w-full px-4 py-3 flex items-center justify-between transition-colors',
          isExpanded ? bgColor : 'hover:bg-gray-50'
        )}
      >
        <div className="flex items-center">
          <div className={clsx('p-1.5 rounded-lg mr-3', bgColor, iconColor)}>
            {icon}
          </div>
          <div className="text-left">
            <p className="font-medium text-gray-800">{title}</p>
            <p className="text-xs text-gray-500">{titleEn}</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1">
            <RiskBadge level={riskLevel} score={suggestion.predictedRisk} size="sm" />
            {riskDelta !== 0 && (
              <span className={clsx(
                'text-xs font-medium',
                isImproved ? 'text-green-600' : 'text-red-600'
              )}>
                ({isImproved ? '-' : '+'}{Math.abs(riskDelta)})
              </span>
            )}
          </div>
          <div className="flex items-center">
            <span className="text-xs text-gray-500 mr-1">
              {(suggestion.semanticSimilarity * 100).toFixed(0)}%
            </span>
            <InfoTooltip
              title="语义相似度"
              content="改写后与原文的语义相似程度。使用Sentence-BERT或备用算法计算。>85%表示语义保持良好，<70%可能存在语义偏移风险。建议选择高相似度的改写方案。"
              iconSize="sm"
            />
          </div>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* Rewritten text */}
          <div className="p-3 bg-white border border-gray-200 rounded-lg">
            <p className="text-gray-800 leading-relaxed">
              {suggestion.rewritten}
            </p>
          </div>

          {/* Changes toggle */}
          {suggestion.changes.length > 0 && (
            <div>
              <button
                onClick={() => setShowChanges(!showChanges)}
                className="text-sm text-gray-500 hover:text-gray-700 flex items-center"
              >
                {showChanges ? '隐藏' : '显示'}改动详情 ({suggestion.changes.length})
                {showChanges ? (
                  <ChevronUp className="w-4 h-4 ml-1" />
                ) : (
                  <ChevronDown className="w-4 h-4 ml-1" />
                )}
              </button>

              {showChanges && (
                <div className="mt-2 space-y-2">
                  {suggestion.changes.map((change, idx) => (
                    <div
                      key={idx}
                      className="text-sm p-2 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center space-x-2">
                        <span className="diff-remove">{change.original}</span>
                        <span className="text-gray-400">→</span>
                        <span className="diff-add">{change.replacement}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {change.reasonZh || change.reason}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Explanation */}
          <div className="text-sm text-gray-600">
            <p>{suggestion.explanationZh || suggestion.explanation}</p>
          </div>

          {/* Apply button */}
          <Button
            variant="primary"
            size="sm"
            onClick={onApply}
            className="w-full"
          >
            选择此建议
          </Button>
        </div>
      )}
    </div>
  );
}
