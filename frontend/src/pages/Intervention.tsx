import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  ArrowRight,
  SkipForward,
  Flag,
  Loader2,
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
import ColloquialismSlider from '../components/settings/ColloquialismSlider';
import ProgressBar from '../components/common/ProgressBar';
import RiskBadge from '../components/common/RiskBadge';
import { useSessionStore } from '../stores/sessionStore';
import { useConfigStore } from '../stores/configStore';
import { sessionApi } from '../services/api';
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

  // Load session on mount
  // 挂载时加载会话
  useEffect(() => {
    if (sessionId) {
      loadCurrentState(sessionId);
      loadAllSentences(sessionId);
    }
  }, [sessionId, loadCurrentState]);

  // Load all sentences for sidebar
  // 为侧边栏加载所有句子
  const loadAllSentences = async (sid: string) => {
    setLoadingSentences(true);
    try {
      const sentences = await sessionApi.getSentences(sid);
      setAllSentences(sentences);
    } catch (err) {
      console.error('Failed to load sentences:', err);
    } finally {
      setLoadingSentences(false);
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

  // Load suggestions when current sentence INDEX changes (not on every object change)
  // 当前句子索引变化时加载建议（不是每次对象变化时）
  useEffect(() => {
    // Only load suggestions if:
    // 1. We have a current sentence
    // 2. The index has actually changed (not just a state refresh after applying)
    // 3. We don't already have suggestions for this sentence
    // 只有在以下情况加载建议：
    // 1. 有当前句子
    // 2. 索引实际发生了变化（不是应用后的状态刷新）
    // 3. 我们还没有这个句子的建议
    if (
      session?.currentSentence &&
      session.currentIndex !== lastLoadedIndex
    ) {
      setLastLoadedIndex(session.currentIndex);
      loadSuggestions(session.currentSentence, colloquialismLevel);
    }
  }, [session?.currentIndex, session?.currentSentence, colloquialismLevel, loadSuggestions, lastLoadedIndex]);

  // Handle apply suggestion
  // 处理应用建议
  const handleApply = async (source: SuggestionSource) => {
    await applySuggestion(source);
  };

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

  // Handle complete session
  // 处理完成会话
  const handleComplete = async () => {
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
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        <span className="ml-3 text-gray-600">加载会话中...</span>
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
          <div className="flex-1 overflow-y-auto">
            {loadingSentences ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
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
                          <RiskBadge
                            level={sentence.riskLevel}
                            score={sentence.riskScore}
                            size="sm"
                          />
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
              第 {session ? session.currentIndex + 1 : '-'} 句，
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

        {/* Progress Bar */}
        {session && (
          <div className="px-4 py-2 bg-white border-b border-gray-200">
            <ProgressBar
              value={session.progressPercent}
              color={session.progressPercent === 100 ? 'success' : 'primary'}
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
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid lg:grid-cols-2 gap-6 max-w-6xl mx-auto">
            {/* Left: Current Sentence */}
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-3">
                当前句子 / Current Sentence
              </h2>
              {session?.currentSentence ? (
                <SentenceCard
                  sentence={session.currentSentence}
                  translation={suggestions?.translation}
                  isActive
                />
              ) : (
                <div className="card p-6 text-center text-gray-500">
                  加载中...
                </div>
              )}

              {/* Action Buttons */}
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
            </div>

            {/* Right: Suggestions */}
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-3">
                修改建议 / Suggestions
              </h2>
              <SuggestionPanel
                suggestions={suggestions}
                isLoading={isLoadingSuggestions}
                customText={customText}
                onCustomTextChange={setCustomText}
                onValidateCustom={validateCustomText}
                validationResult={validationResult}
                onApply={handleApply}
                onApplyCustom={applyCustom}
                sentenceProcessed={!suggestions && !isLoadingSuggestions && (session?.processed ?? 0) > 0}
                colloquialismLevel={colloquialismLevel}
                sentenceId={session?.currentSentence?.id}
              />
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
              disabled={!session || session.processed < session.totalSentences * 0.5}
            >
              完成处理
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
