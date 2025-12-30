import { useState, useEffect, useRef, useCallback } from 'react';
import { Sparkles, Wrench, Edit3, Check, X, Loader2, ChevronDown, ChevronUp, Lightbulb, CheckCircle2, MousePointerClick, Search } from 'lucide-react';
import { clsx } from 'clsx';
import type { SuggestResponse, Suggestion, SuggestionSource } from '../../types';
import Button from '../common/Button';
import RiskBadge from '../common/RiskBadge';
import InfoTooltip from '../common/InfoTooltip';
import SentenceAnalysisPanel from './SentenceAnalysisPanel';
import { suggestApi } from '../../services/api';
import { useSessionStore } from '../../stores/sessionStore';

interface WritingHint {
  type: string;
  title: string;
  titleZh: string;
  description: string;
  descriptionZh: string;
}

interface SuggestionPanelProps {
  suggestions: SuggestResponse | null;
  isLoading?: boolean;
  customText: string;
  onCustomTextChange: (text: string) => void;
  onValidateCustom: () => void;
  validationResult?: {
    passed: boolean;
    similarity: number;
    message: string;
  } | null;
  onApply: (source: SuggestionSource) => void;
  onApplyCustom: () => void;
  sentenceProcessed?: boolean;  // Show when sentence has been processed
  colloquialismLevel?: number;  // Colloquialism level for analysis suggestions
  sentenceId?: string;  // Sentence ID for caching
}

/**
 * Suggestion panel with dual-track display and writing hints
 * 带写作提示的双轨建议面板
 */
export default function SuggestionPanel({
  suggestions,
  isLoading = false,
  customText,
  onCustomTextChange,
  onValidateCustom,
  validationResult,
  onApply,
  onApplyCustom,
  sentenceProcessed = false,
  colloquialismLevel = 5,
  sentenceId,
}: SuggestionPanelProps) {
  const [expandedTrack, setExpandedTrack] = useState<'llm' | 'rule' | 'custom' | null>('llm');
  const [writingHints, setWritingHints] = useState<WritingHint[]>([]);
  const [loadingHints, setLoadingHints] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Get cache methods from store
  // 从 store 获取缓存方法
  const {
    setCustomTextForSentence,
    getCustomTextForSentence,
    setAnalysisForSentence,
    getAnalysisForSentence,
  } = useSessionStore();

  // Get cached analysis result
  // 获取缓存的分析结果
  const analysisResult = sentenceId ? getAnalysisForSentence(sentenceId) : null;

  // Load cached custom text when sentence changes
  // 当句子变化时加载缓存的自定义文本
  useEffect(() => {
    if (sentenceId) {
      const cachedText = getCustomTextForSentence(sentenceId);
      if (cachedText && cachedText !== customText) {
        onCustomTextChange(cachedText);
      }
    }
  }, [sentenceId]);

  // Auto-save custom text to cache every 15 seconds
  // 每15秒自动保存自定义文本到缓存
  useEffect(() => {
    if (sentenceId && customText) {
      // Clear previous timer
      // 清除之前的定时器
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
      // Set new timer
      // 设置新定时器
      autoSaveTimerRef.current = setTimeout(() => {
        setCustomTextForSentence(sentenceId, customText);
      }, 15000);
    }
    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, [customText, sentenceId, setCustomTextForSentence]);

  // Save custom text immediately when changing sentences
  // 切换句子时立即保存自定义文本
  const handleCustomTextChange = useCallback((text: string) => {
    onCustomTextChange(text);
    // Also update cache immediately on change (debounced auto-save will handle periodic saves)
    // 同时立即更新缓存（防抖自动保存会处理定期保存）
    if (sentenceId && text) {
      setCustomTextForSentence(sentenceId, text);
    }
  }, [onCustomTextChange, sentenceId, setCustomTextForSentence]);

  // Load writing hints when custom track is expanded
  // 当自定义轨道展开时加载写作提示
  useEffect(() => {
    if (expandedTrack === 'custom' && suggestions?.original) {
      loadWritingHints(suggestions.original);
    }
  }, [expandedTrack, suggestions?.original]);

  const loadWritingHints = async (sentence: string) => {
    setLoadingHints(true);
    try {
      const result = await suggestApi.getWritingHints(sentence);
      setWritingHints(result.hints || []);
    } catch (err) {
      console.error('Failed to load writing hints:', err);
      setWritingHints([]);
    } finally {
      setLoadingHints(false);
    }
  };

  // Load detailed sentence analysis (with caching)
  // 加载详细句子分析（带缓存）
  const loadAnalysis = async () => {
    if (!suggestions?.original || !sentenceId) return;

    // Check cache first
    // 首先检查缓存
    const cached = getAnalysisForSentence(sentenceId);
    if (cached) {
      setShowAnalysis(true);
      return;
    }

    setLoadingAnalysis(true);
    setShowAnalysis(true);
    try {
      const result = await suggestApi.analyzeSentence(
        suggestions.original,
        colloquialismLevel
      );
      // Save to cache
      // 保存到缓存
      setAnalysisForSentence(sentenceId, result);
    } catch (err) {
      console.error('Failed to load analysis:', err);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  // Reset analysis view when sentence changes (but keep cache)
  // 当句子变化时重置分析视图（但保留缓存）
  useEffect(() => {
    setShowAnalysis(false);
  }, [sentenceId]);

  if (isLoading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-center text-gray-500">
          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
          <span>正在生成建议...</span>
        </div>
      </div>
    );
  }

  // Show processed message - user needs to select next sentence from sidebar
  // 显示已处理消息 - 用户需要从侧边栏选择下一句
  if (sentenceProcessed && !suggestions && !isLoading) {
    return (
      <div className="card p-6 text-center">
        <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-3" />
        <p className="text-lg font-medium text-gray-800 mb-2">
          ✓ 当前句子已处理
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

  return (
    <div className="space-y-3">
      {/* Track A: LLM Suggestion */}
      {suggestions.llmSuggestion && (
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

      {/* Track B: Rule Suggestion */}
      {suggestions.ruleSuggestion && (
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

      {/* Track C: Custom Input */}
      <div className={clsx(
        'card border-2 overflow-hidden transition-all duration-200',
        expandedTrack === 'custom' ? 'border-gray-300' : 'border-gray-200',
        showAnalysis && expandedTrack === 'custom' && 'flex flex-col max-h-[70vh]'
      )}>
        <button
          onClick={() => setExpandedTrack(expandedTrack === 'custom' ? null : 'custom')}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors flex-shrink-0"
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

        {expandedTrack === 'custom' && (
          <div className={clsx(
            'flex flex-col',
            showAnalysis ? 'flex-1 min-h-0' : ''
          )}>
            {/* Sticky section: Original text + Input area + Buttons */}
            {/* 固定部分：原文 + 输入区域 + 按钮 */}
            <div className={clsx(
              'px-4 pb-3 space-y-3 flex-shrink-0 bg-white',
              showAnalysis && 'border-b border-gray-200 shadow-sm'
            )}>
              {/* Original text - show when analysis is visible */}
              {/* 原文 - 分析可见时显示 */}
              {showAnalysis && suggestions?.original && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">原文 / Original:</p>
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {suggestions.original}
                  </p>
                </div>
              )}

              {/* Writing Hints - hide when analysis is shown to save space */}
              {/* 写作提示 - 分析显示时隐藏以节省空间 */}
              {!showAnalysis && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <div className="flex items-center text-amber-700 mb-2">
                    <Lightbulb className="w-4 h-4 mr-2" />
                    <span className="text-sm font-medium">改写建议 / Writing Hints</span>
                  </div>
                  {loadingHints ? (
                    <div className="flex items-center text-amber-600 text-sm">
                      <Loader2 className="w-3 h-3 mr-2 animate-spin" />
                      加载中...
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {writingHints.map((hint, idx) => (
                        <div key={idx} className="text-sm">
                          <p className="font-medium text-amber-800">
                            {idx + 1}. {hint.titleZh}
                          </p>
                          <p className="text-amber-700 text-xs mt-0.5">
                            {hint.descriptionZh}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <textarea
                value={customText}
                onChange={(e) => handleCustomTextChange(e.target.value)}
                placeholder="输入您的修改版本..."
                className={clsx(
                  'textarea',
                  showAnalysis ? 'h-20' : 'h-24'
                )}
              />

              {/* Validation result */}
              {validationResult && (
                <div
                  className={clsx(
                    'p-3 rounded-lg flex items-start',
                    validationResult.passed
                      ? 'bg-green-50 text-green-700'
                      : 'bg-red-50 text-red-700'
                  )}
                >
                  {validationResult.passed ? (
                    <Check className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                  ) : (
                    <X className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="text-sm">
                    <p>{validationResult.message}</p>
                    <p className="text-xs mt-1">
                      语义相似度: {(validationResult.similarity * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              )}

              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadAnalysis}
                  disabled={loadingAnalysis}
                >
                  {loadingAnalysis ? (
                    <>
                      <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                      分析中...
                    </>
                  ) : analysisResult ? (
                    <>
                      <Search className="w-3 h-3 mr-1" />
                      {showAnalysis ? '隐藏分析' : '显示分析'}
                    </>
                  ) : (
                    <>
                      <Search className="w-3 h-3 mr-1" />
                      分析
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onValidateCustom}
                  disabled={!customText.trim()}
                >
                  检测风险
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={onApplyCustom}
                  disabled={!customText.trim() || !validationResult?.passed}
                >
                  确认提交
                </Button>
              </div>
            </div>

            {/* Scrollable section: Sentence Analysis Panel */}
            {/* 可滚动部分：句子分析面板 */}
            {showAnalysis && (
              <div className="flex-1 overflow-y-auto px-4 py-3 min-h-0">
                {loadingAnalysis ? (
                  <div className="p-6 bg-gray-50 rounded-lg text-center">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">正在分析句子结构...</p>
                    <p className="text-xs text-gray-400 mt-1">Analyzing sentence structure...</p>
                  </div>
                ) : analysisResult ? (
                  <SentenceAnalysisPanel
                    analysis={analysisResult}
                    onClose={() => setShowAnalysis(false)}
                  />
                ) : (
                  <div className="p-4 bg-red-50 rounded-lg text-center">
                    <p className="text-sm text-red-600">分析失败，请重试</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
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
              position="left"
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
