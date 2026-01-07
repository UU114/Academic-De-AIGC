import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  ArrowRight,
  SkipForward,
  Flag,
  AlertCircle,
  CheckCircle,
  Settings,
  ChevronLeft,
  ChevronRight,
  Circle,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import SentenceCard from '../components/editor/SentenceCard';
import SuggestionPanel from '../components/editor/SuggestionPanel';
import CustomInputSection from '../components/editor/CustomInputSection';
import ColloquialismSlider from '../components/settings/ColloquialismSlider';
import ProgressBar from '../components/common/ProgressBar';
import RiskBadge from '../components/common/RiskBadge';
import LoadingMessage from '../components/common/LoadingMessage';
import { useSessionStore } from '../stores/sessionStore';
import { useConfigStore } from '../stores/configStore';
import { sessionApi, suggestApi } from '../services/api';
import type { SuggestionSource, SentenceAnalysis } from '../types';

/**
 * Intervention page - Sentence-by-sentence editing interface with sidebar
 * 干预模式页面 - 带侧边栏的逐句编辑界面
 */
export default function Intervention() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  // Store states
  // 存储状态
  const {
    session,
    isLoading,
    error,
    suggestions,
    isLoadingSuggestions,
    customText,
    validationResult,
    suggestionsCache,
    loadCurrentState,
    loadSuggestions,
    skipSentence,
    flagSentence,
    applySuggestion,
    applyCustom,
    setCustomText,
    validateCustomText,
    completeSession,
    clearError,
  } = useSessionStore();

  const { colloquialismLevel, setColloquialismLevel } = useConfigStore();

  // Local state
  // 本地状态
  const [showSettings, setShowSettings] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [allSentences, setAllSentences] = useState<SentenceAnalysis[]>([]);
  const [loadingSentences, setLoadingSentences] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // Counter ref for tracking analysis request IDs to handle race conditions
  // 用于追踪分析请求ID的计数器ref，处理竞态条件
  const analysisRequestIdRef = useRef(0);

  // Ref for sidebar scroll position preservation
  // 用于保持侧边栏滚动位置的ref
  const sidebarScrollRef = useRef<HTMLDivElement>(null);

  // Track C analysis state - when true, show input in left column
  // 轨道C分析状态 - 为true时，输入区在左列显示
  const [analysisState, setAnalysisState] = useState<{
    showAnalysis: boolean;
    loadingAnalysis: boolean;
    hasResult: boolean;
    expandedTrack: 'llm' | 'rule' | 'custom' | null;
    error?: string;
  }>({
    showAnalysis: false,
    loadingAnalysis: false,
    hasResult: false,
    expandedTrack: 'llm',
    error: undefined,
  });

  // Determine if custom input should show in left column
  // Only when Track C is expanded AND analysis is shown
  // 判断自定义输入是否应该显示在左列
  // 只有轨道C展开且分析显示时才移到左侧
  const showCustomInputInLeft = analysisState.expandedTrack === 'custom' && analysisState.showAnalysis;

  // Get analysis cache methods from store
  // 从store获取分析缓存方法
  const { getAnalysisForSentence, setAnalysisForSentence } = useSessionStore();

  // Ref to store the sentence ID that started the analysis request
  // 用于存储发起分析请求的句子ID的ref
  const analysisStartSentenceIdRef = useRef<string | null>(null);

  // Handle analysis toggle from CustomInputSection (with race condition handling)
  // 处理CustomInputSection的分析切换（带竞态条件处理）
  const handleAnalysisToggle = useCallback(async (show: boolean) => {
    if (!show) {
      setAnalysisState(prev => ({ ...prev, showAnalysis: false, error: undefined }));
      return;
    }

    const sentenceId = session?.currentSentence?.id;
    // IMPORTANT: Use current sentence text directly, not from suggestions (which may be stale)
    // 重要：直接使用当前句子文本，而不是 suggestions（可能是旧数据）
    const originalText = session?.currentSentence?.text;

    // Early return with error if no sentence data
    // 如果没有句子数据则提前返回并显示错误
    if (!sentenceId || !originalText) {
      console.error('Analysis toggle: missing sentenceId or originalText', { sentenceId, originalText });
      setAnalysisState(prev => ({
        ...prev,
        showAnalysis: true,
        loadingAnalysis: false,
        error: '无法分析：句子数据不完整 / Cannot analyze: sentence data incomplete',
      }));
      return;
    }

    // Check cache first
    // 首先检查缓存
    const cached = getAnalysisForSentence(sentenceId);
    if (cached) {
      setAnalysisState(prev => ({
        ...prev,
        showAnalysis: true,
        hasResult: true,
        error: undefined,
        expandedTrack: 'custom',
      }));
      return;
    }

    // Generate unique request ID for race condition handling
    // 生成唯一请求ID用于竞态条件处理
    const requestId = ++analysisRequestIdRef.current;
    // Store the sentence ID that started this request
    // 存储发起此请求的句子ID
    analysisStartSentenceIdRef.current = sentenceId;

    // Load analysis - also ensure expandedTrack is set to 'custom'
    // 加载分析 - 同时确保expandedTrack设置为'custom'
    setAnalysisState(prev => ({
      ...prev,
      showAnalysis: true,
      loadingAnalysis: true,
      error: undefined,
      expandedTrack: 'custom', // Ensure this is set so layout updates correctly
    }));
    console.log('[DEBUG] Starting sentence analysis for:', originalText.substring(0, 50) + '...');
    console.log('[DEBUG] sentenceId:', sentenceId, 'colloquialismLevel:', colloquialismLevel, 'requestId:', requestId);

    try {
      console.log('[DEBUG] Calling suggestApi.analyzeSentence...');
      const result = await suggestApi.analyzeSentence(
        originalText,
        colloquialismLevel
      );

      // Check if this request is still the current one (race condition guard)
      // 检查此请求是否仍然是当前请求（竞态条件保护）
      if (analysisRequestIdRef.current !== requestId) {
        console.log('[handleAnalysisToggle] Discarding stale analysis response for:', sentenceId);
        // Still cache the result for future use
        // 仍然缓存结果供将来使用
        setAnalysisForSentence(sentenceId, result);
        return;
      }

      // Check if the current sentence is still the same (user might have switched)
      // 检查当前句子是否仍然相同（用户可能已切换）
      const currentSentenceId = session?.currentSentence?.id;
      if (currentSentenceId !== sentenceId) {
        console.log('[handleAnalysisToggle] Sentence changed, caching result but not updating UI:', sentenceId);
        // Cache the result but don't update UI state (sentence reset effect will handle it)
        // 缓存结果但不更新UI状态（句子重置effect会处理）
        setAnalysisForSentence(sentenceId, result);
        return;
      }

      console.log('[DEBUG] Analysis API returned:', result);
      setAnalysisForSentence(sentenceId, result);
      setAnalysisState(prev => ({ ...prev, loadingAnalysis: false, hasResult: true, error: undefined }));
      console.log('[DEBUG] Analysis state updated successfully');
    } catch (err) {
      // Only update error state if this is still the current request
      // 仅当这仍然是当前请求时才更新错误状态
      if (analysisRequestIdRef.current !== requestId) {
        console.log('[handleAnalysisToggle] Discarding stale error for:', sentenceId);
        return;
      }
      // Also check if sentence hasn't changed
      // 同时检查句子是否未变化
      const currentSentenceId = session?.currentSentence?.id;
      if (currentSentenceId !== sentenceId) {
        console.log('[handleAnalysisToggle] Sentence changed, not showing error for:', sentenceId);
        return;
      }
      console.error('[DEBUG] Failed to load analysis:', err);
      const errorMessage = err instanceof Error ? err.message : '分析请求失败';
      setAnalysisState(prev => ({
        ...prev,
        loadingAnalysis: false,
        error: `分析失败: ${errorMessage} / Analysis failed`,
      }));
    }
  }, [session?.currentSentence?.id, suggestions?.original, colloquialismLevel, getAnalysisForSentence, setAnalysisForSentence]);

  // Handle analysis state change from SuggestionPanel
  // 处理SuggestionPanel的分析状态变化
  const handleAnalysisStateChange = useCallback((state: typeof analysisState) => {
    setAnalysisState(state);
  }, []);

  // Track previous sentence ID to detect changes
  // 追踪上一个句子ID以检测变化
  const prevSentenceIdRef = useRef<string | null>(null);

  // Reset analysis state when sentence changes (fix for "stuck" issue)
  // 当句子变化时重置分析状态（修复"卡住"问题）
  useEffect(() => {
    const currentId = session?.currentSentence?.id || null;

    // Only reset if sentence actually changed (not on initial mount with same id)
    // 仅在句子实际变化时重置（不是初始挂载时）
    if (prevSentenceIdRef.current !== null && prevSentenceIdRef.current !== currentId) {
      console.log('[DEBUG] Sentence changed from', prevSentenceIdRef.current, 'to', currentId);
      // Check if there's cached analysis for the new sentence
      // 检查新句子是否有缓存的分析结果
      const cached = currentId ? getAnalysisForSentence(currentId) : null;
      setAnalysisState({
        showAnalysis: false,
        loadingAnalysis: false,
        hasResult: !!cached,
        expandedTrack: 'llm',  // Reset to Track A
        error: undefined,
      });
    }

    // Update ref for next comparison
    // 更新ref用于下次比较
    prevSentenceIdRef.current = currentId;
  }, [session?.currentSentence?.id, getAnalysisForSentence]);

  // Load session on mount and update step
  // 挂载时加载会话并更新步骤
  useEffect(() => {
    if (sessionId) {
      loadCurrentState(sessionId);
      loadAllSentences(sessionId);
      // Update session step to step3
      // 更新会话步骤到 step3
      sessionApi.updateStep(sessionId, 'step3').catch(console.error);
    }
  }, [sessionId, loadCurrentState]);

  // Load all sentences for sidebar (preserving scroll position)
  // 为侧边栏加载所有句子（保持滚动位置）
  const loadAllSentences = async (sid: string) => {
    // Save scroll position before reloading
    // 重新加载前保存滚动位置
    const scrollTop = sidebarScrollRef.current?.scrollTop || 0;

    setLoadingSentences(true);
    try {
      const sentences = await sessionApi.getSentences(sid);
      setAllSentences(sentences);
    } catch (err) {
      console.error('Failed to load sentences:', err);
    } finally {
      setLoadingSentences(false);
      // Restore scroll position after state update
      // 状态更新后恢复滚动位置
      requestAnimationFrame(() => {
        if (sidebarScrollRef.current) {
          sidebarScrollRef.current.scrollTop = scrollTop;
        }
      });
    }
  };

  // Update sentence status when session changes
  // 当会话变化时更新句子状态
  useEffect(() => {
    if (session && sessionId) {
      // Reload sentences to get updated status
      // 重新加载句子以获取更新的状态
      loadAllSentences(sessionId);
    }
  }, [session?.currentIndex, session?.processed]);

  // Track current sentence index to avoid unnecessary suggestion reloads
  // 追踪当前句子索引，避免不必要的建议重新加载
  const [lastLoadedIndex, setLastLoadedIndex] = useState<number | null>(null);

  // Note: suggestionsCache is already destructured from useSessionStore at the top
  // 注意：suggestionsCache 已经在顶部从 useSessionStore 解构出来了

  // Load suggestions when current sentence INDEX changes
  // Logic: 1. Write current to cache (handled by store) -> 2. Clear display -> 3. Read from cache -> 4. If not found & not processed, call LLM
  // 当前句子索引变化时加载建议
  // 逻辑：1. 当前写入缓存（由store处理）-> 2. 清除显示 -> 3. 从缓存读取 -> 4. 未找到且未处理则调用LLM
  useEffect(() => {
    if (
      session?.currentSentence &&
      session.currentIndex !== lastLoadedIndex
    ) {
      setLastLoadedIndex(session.currentIndex);
      const currentSentenceId = session.currentSentence.id;

      // Step 1: Check cache for the NEW sentence
      // 步骤1：检查新句子的缓存
      const cachedSuggestions = suggestionsCache.get(currentSentenceId);

      if (cachedSuggestions) {
        // Step 2a: Found in cache - load from cache (this also updates store state)
        // 步骤2a：缓存命中 - 从缓存加载（这也会更新store状态）
        console.log('[Intervention] Loading suggestions from cache for:', currentSentenceId);
        loadSuggestions(session.currentSentence, colloquialismLevel);
      } else {
        // Step 2b: Not in cache - check if sentence is already processed
        // 步骤2b：缓存未命中 - 检查句子是否已处理
        const sentenceInList = allSentences.find(s => s.id === currentSentenceId);
        const isAlreadyProcessed = sentenceInList?.status === 'processed' ||
          sentenceInList?.status === 'skip' ||
          sentenceInList?.status === 'flag';

        if (!isAlreadyProcessed) {
          // Not processed - call LLM to generate suggestions
          // 未处理 - 调用LLM生成建议
          console.log('[Intervention] No cache, calling LLM for:', currentSentenceId);
          loadSuggestions(session.currentSentence, colloquialismLevel);
        } else {
          // Already processed and no cache - clear suggestions to show "已处理" state
          // 已处理且无缓存 - 清除suggestions以显示"已处理"状态
          console.log('[Intervention] Already processed, clearing suggestions for:', currentSentenceId);
          useSessionStore.setState({ suggestions: null, isLoadingSuggestions: false });
        }
      }
    }
  }, [session?.currentIndex, session?.currentSentence, colloquialismLevel, loadSuggestions, lastLoadedIndex, allSentences, suggestionsCache]);

  // Handle apply suggestion
  // 处理应用建议
  const handleApply = async (source: SuggestionSource) => {
    await applySuggestion(source);
  };

  // Handle reselect suggestion for already processed sentence
  // 处理已处理句子的重新选择改写方案
  const handleReselect = useCallback(async () => {
    if (!session?.currentSentence) return;

    console.log('[Intervention] Reselecting suggestion for:', session.currentSentence.id);

    // Update local state to mark sentence as "pending" again
    // 更新本地状态，将句子标记为"待处理"
    setAllSentences(prev => prev.map(s =>
      s.id === session.currentSentence?.id
        ? { ...s, status: 'pending' as const }
        : s
    ));

    // Force reload suggestions (bypass the "already processed" check)
    // 强制重新加载建议（绕过"已处理"检查）
    setLastLoadedIndex(null);  // Reset lastLoadedIndex to trigger reload
    loadSuggestions(session.currentSentence, colloquialismLevel);
  }, [session?.currentSentence, colloquialismLevel, loadSuggestions]);

  // Handle jump to sentence
  // 处理跳转到句子
  const handleGotoSentence = async (index: number) => {
    if (!sessionId) return;
    try {
      await sessionApi.gotoSentence(sessionId, index);
      // Update store with new session state
      // 用新的会话状态更新存储
      await loadCurrentState(sessionId);
    } catch (err) {
      console.error('Failed to goto sentence:', err);
    }
  };

  // Calculate completed count (processed + skipped)
  // 计算已完成数量（已处理 + 已跳过）
  const completedCount = (session?.processed || 0) + (session?.skipped || 0);
  const isAllCompleted = session ? completedCount >= session.totalSentences : false;

  // Check if current sentence is already processed (from allSentences list)
  // 检查当前句子是否已处理（从 allSentences 列表中）
  const currentSentenceStatus = allSentences.find(
    s => s.id === session?.currentSentence?.id
  )?.status;
  const isCurrentSentenceProcessed = currentSentenceStatus === 'processed' ||
    currentSentenceStatus === 'skip' ||
    currentSentenceStatus === 'flag';

  // Handle complete session
  // 处理完成会话
  const handleComplete = async () => {
    // If not all sentences completed, show confirmation dialog
    // 如果没有完成所有句子，显示确认对话框
    if (!isAllCompleted) {
      setShowConfirmDialog(true);
      return;
    }
    await completeSession();
    if (sessionId) {
      navigate(`/review/${sessionId}`);
    }
  };

  // Confirm and complete session
  // 确认并完成会话
  const confirmComplete = async () => {
    setShowConfirmDialog(false);
    await completeSession();
    if (sessionId) {
      navigate(`/review/${sessionId}`);
    }
  };

  // Check if session is complete
  // 检查会话是否完成
  const isComplete = session && session.currentIndex >= session.totalSentences;

  // Get status icon for sentence list
  // 获取句子列表的状态图标
  // Status:
  //   - gray circle: pending (not viewed)
  //   - yellow circle: viewed with cache (suggestions loaded but not processed)
  //   - green checkmark: processed (modification applied)
  //   - skip icon: skipped
  //   - flag icon: flagged for review
  //   - blue pulsing: current sentence
  const getStatusIndicator = (sentence: SentenceAnalysis, idx: number) => {
    const status = sentence.status || (idx === session?.currentIndex ? 'current' : 'pending');
    const hasCache = suggestionsCache.has(sentence.id);

    switch (status) {
      case 'processed':
        // Green checkmark - modification applied
        // 绿色对勾 - 已应用修改
        return <CheckCircle className="w-3 h-3 text-green-500" />;
      case 'current':
        // Blue pulsing dot - currently editing
        // 蓝色脉冲点 - 当前正在编辑
        return <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />;
      case 'skip':
        // Skip icon - skipped
        // 跳过图标 - 已跳过
        return <SkipForward className="w-3 h-3 text-gray-400" />;
      case 'flag':
        // Flag icon - flagged for manual review
        // 旗子图标 - 已标记待审
        return <Flag className="w-3 h-3 text-amber-500" />;
      default:
        // Check if sentence has been viewed (has cache)
        // 检查句子是否已查看（有缓存）
        if (hasCache) {
          // Yellow circle - viewed but not processed
          // 黄色圆点 - 已查看但未处理
          return <Circle className="w-3 h-3 text-amber-400 fill-amber-400" />;
        }
        // Gray circle - not viewed
        // 灰色圆点 - 未查看
        return <Circle className="w-3 h-3 text-gray-300 fill-gray-300" />;
    }
  };

  // Loading state
  // 加载状态
  if (isLoading && !session) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <LoadingMessage category="general" size="lg" showEnglish={true} />
      </div>
    );
  }

  // Error state
  // 错误状态
  if (error && !session) {
    return (
      <div className="max-w-2xl mx-auto py-12 text-center">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-800 mb-2">加载失败</h2>
        <p className="text-gray-600 mb-4">{error}</p>
        <Button variant="outline" onClick={() => navigate('/upload')}>
          返回上传
        </Button>
      </div>
    );
  }

  // Completion state
  // 完成状态
  if (isComplete) {
    return (
      <div className="max-w-2xl mx-auto py-12 text-center">
        <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-800 mb-2">处理完成！</h2>
        <p className="text-gray-600 mb-6">
          所有句子已处理完毕，您可以查看结果并导出文档
        </p>
        <div className="flex justify-center space-x-4">
          <Button variant="outline" onClick={() => navigate('/upload')}>
            处理新文档
          </Button>
          <Button variant="primary" onClick={handleComplete}>
            查看结果
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-8rem)]">
      {/* Left Sidebar - Sentence List */}
      <div
        className={clsx(
          'bg-white border-r border-gray-200 flex flex-col transition-all duration-300',
          sidebarCollapsed ? 'w-12' : 'w-72'
        )}
      >
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-3 border-b border-gray-200">
          {!sidebarCollapsed && (
            <span className="text-sm font-medium text-gray-700">
              句子列表 ({allSentences.length})
            </span>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            {sidebarCollapsed ? (
              <ChevronRight className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronLeft className="w-4 h-4 text-gray-500" />
            )}
          </button>
        </div>

        {/* Sentence List */}
        {!sidebarCollapsed && (
          <div ref={sidebarScrollRef} className="flex-1 overflow-y-auto">
            {loadingSentences ? (
              <div className="flex items-center justify-center py-8 px-2">
                <LoadingMessage category="general" size="sm" showEnglish={false} />
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {allSentences.map((sentence, idx) => (
                  <button
                    key={sentence.index}
                    onClick={() => handleGotoSentence(idx)}
                    className={clsx(
                      'w-full text-left p-3 hover:bg-gray-50 transition-colors',
                      idx === session?.currentIndex && 'bg-primary-50 border-l-2 border-primary-500'
                    )}
                  >
                    <div className="flex items-start space-x-2">
                      <div className="mt-1 flex-shrink-0">
                        {getStatusIndicator(sentence, idx)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-gray-500">#{idx + 1}</span>
                          {/* Show risk change for processed sentences */}
                          {/* 为已处理的句子显示风险变化 */}
                          {sentence.newRiskScore !== undefined && sentence.newRiskLevel ? (
                            <div className="flex items-center space-x-1">
                              <RiskBadge
                                level={sentence.riskLevel}
                                score={sentence.riskScore}
                                size="sm"
                              />
                              <span className="text-xs text-gray-400">→</span>
                              <RiskBadge
                                level={sentence.newRiskLevel}
                                score={sentence.newRiskScore}
                                size="sm"
                              />
                            </div>
                          ) : (
                            <RiskBadge
                              level={sentence.riskLevel}
                              score={sentence.riskScore}
                              size="sm"
                            />
                          )}
                        </div>
                        <p className="text-xs text-gray-600 line-clamp-2">
                          {sentence.text.substring(0, 80)}
                          {sentence.text.length > 80 && '...'}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Sidebar collapsed - show mini indicators */}
        {sidebarCollapsed && (
          <div className="flex-1 overflow-y-auto py-2">
            {allSentences.map((sentence, idx) => (
              <button
                key={sentence.index}
                onClick={() => handleGotoSentence(idx)}
                className={clsx(
                  'w-full flex justify-center py-1 hover:bg-gray-100',
                  idx === session?.currentIndex && 'bg-primary-100'
                )}
                title={`#${idx + 1}: ${sentence.text.substring(0, 50)}...`}
              >
                <div
                  className={clsx(
                    'w-2 h-2 rounded-full',
                    sentence.riskLevel === 'high' && 'bg-red-500',
                    sentence.riskLevel === 'medium' && 'bg-amber-500',
                    sentence.riskLevel === 'low' && 'bg-green-500',
                    sentence.riskLevel === 'safe' && 'bg-gray-300'
                  )}
                />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
          <div>
            <h1 className="text-xl font-bold text-gray-800">干预模式</h1>
            <p className="text-sm text-gray-600">
              已完成 {completedCount} 句，
              共 {session?.totalSentences || '-'} 句
            </p>
          </div>
          <div className="flex items-center space-x-2">
            {session && (
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <span>已处理: {session.processed}</span>
                <span>|</span>
                <span>跳过: {session.skipped}</span>
                <span>|</span>
                <span>标记: {session.flagged}</span>
              </div>
            )}
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <Settings className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>

        {/* Settings Panel (collapsible) */}
        {showSettings && (
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <ColloquialismSlider
              value={colloquialismLevel}
              onChange={setColloquialismLevel}
            />
          </div>
        )}

        {/* Progress Bar - shows completed/total ratio */}
        {/* 进度条 - 显示已完成/总数比例 */}
        {session && (
          <div className="px-4 py-2 bg-white border-b border-gray-200">
            <ProgressBar
              value={session.totalSentences > 0 ? Math.round((completedCount / session.totalSentences) * 100) : 0}
              color={completedCount >= session.totalSentences ? 'success' : 'primary'}
              showLabel
            />
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="flex items-center justify-between p-3 bg-red-50 border-b border-red-200">
            <div className="flex items-center text-red-700">
              <AlertCircle className="w-4 h-4 mr-2" />
              <span className="text-sm">{error}</span>
            </div>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700"
            >
              &times;
            </button>
          </div>
        )}

        {/* Main Content - Two Column Layout */}
        {/* Left column fixed, right column scrollable for better UX when comparing */}
        {/* 左列固定，右列可滚动，便于对照原句与修改建议 */}
        <div className="flex-1 flex overflow-hidden p-4">
          <div className="flex flex-col lg:flex-row gap-6 max-w-6xl mx-auto w-full">
            {/* Left: Current Sentence + Custom Input (when Track C expanded) */}
            {/* 左侧：当前句子 + 自定义输入（轨道C展开时） */}
            <div className={clsx(
              'flex-shrink-0 flex flex-col',
              showCustomInputInLeft ? 'lg:w-1/2' : 'lg:w-1/2'
            )}>
              <h2 className="text-lg font-semibold text-gray-800 mb-3">
                当前句子 / Current Sentence
              </h2>
              {session?.currentSentence ? (
                <SentenceCard
                  sentence={session.currentSentence}
                  translation={suggestions?.translation}
                  isActive
                  displayIndex={(session?.currentIndex ?? 0) + 1}
                />
              ) : (
                <div className="card p-6 text-center text-gray-500">
                  加载中...
                </div>
              )}

              {/* Action Buttons - always show */}
              {/* 操作按钮 - 始终显示 */}
              <div className="flex items-center justify-between mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={skipSentence}
                  disabled={isLoading}
                >
                  <SkipForward className="w-4 h-4 mr-1" />
                  跳过
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={flagSentence}
                  disabled={isLoading}
                >
                  <Flag className="w-4 h-4 mr-1" />
                  标记待审
                </Button>
              </div>

              {/* Custom Input Section - show when Track C is expanded */}
              {/* 自定义输入区 - 轨道C展开时显示 */}
              {showCustomInputInLeft && suggestions && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h3 className="text-sm font-medium text-gray-700 mb-3">
                    自定义修改 / Custom Edit
                  </h3>
                  <CustomInputSection
                    originalText={suggestions.original}
                    customText={customText}
                    onCustomTextChange={setCustomText}
                    onValidateCustom={validateCustomText}
                    validationResult={validationResult}
                    onApplyCustom={applyCustom}
                    onAnalysisToggle={handleAnalysisToggle}
                    showAnalysis={analysisState.showAnalysis}
                    loadingAnalysis={analysisState.loadingAnalysis}
                    hasAnalysisResult={analysisState.hasResult}
                    sentenceId={session?.currentSentence?.id}
                  />
                </div>
              )}
            </div>

            {/* Right: Suggestions - Independent scrollable area */}
            {/* 右侧：修改建议 - 独立滚动区域 */}
            <div className="lg:w-1/2 flex flex-col min-h-0">
              <h2 className="text-lg font-semibold text-gray-800 mb-3 flex-shrink-0">
                修改建议 / Suggestions
              </h2>
              <div className="flex-1 overflow-y-auto pr-2">
                <SuggestionPanel
                  suggestions={suggestions}
                  isLoading={isLoadingSuggestions}
                  onApply={handleApply}
                  sentenceProcessed={isCurrentSentenceProcessed || (!suggestions && !isLoadingSuggestions && (session?.processed ?? 0) > 0)}
                  sentenceProcessedType={currentSentenceStatus as 'processed' | 'skip' | 'flag' | undefined}
                  sentenceId={session?.currentSentence?.id}
                  onReselect={handleReselect}
                  analysisState={analysisState}
                  onAnalysisStateChange={handleAnalysisStateChange}
                  customText={customText}
                  onCustomTextChange={setCustomText}
                  onValidateCustom={validateCustomText}
                  validationResult={validationResult}
                  onApplyCustom={applyCustom}
                  onAnalysisToggle={handleAnalysisToggle}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Navigation */}
        <div className="border-t border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between max-w-6xl mx-auto">
            <Button
              variant="outline"
              onClick={() => navigate('/history')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回历史
            </Button>

            <Button
              variant="primary"
              onClick={handleComplete}
            >
              完成处理
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      {/* 确认对话框 */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md mx-4">
            <div className="flex items-center mb-4">
              <AlertCircle className="w-6 h-6 text-amber-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-800">确认中断处理？</h3>
            </div>
            <p className="text-gray-600 mb-2">
              您还有 <span className="font-semibold text-amber-600">{(session?.totalSentences || 0) - completedCount}</span> 句未处理。
            </p>
            <p className="text-sm text-gray-500 mb-6">
              中断后可以从历史记录中继续处理，或直接查看当前结果。
            </p>
            <div className="flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={() => setShowConfirmDialog(false)}
              >
                继续处理
              </Button>
              <Button
                variant="primary"
                onClick={confirmComplete}
              >
                确认中断
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
