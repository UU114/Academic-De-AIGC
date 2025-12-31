/**
 * Session state management using Zustand
 * 使用 Zustand 的会话状态管理
 */

import { create } from 'zustand';
import type {
  SessionState,
  SentenceAnalysis,
  SuggestResponse,
  RiskLevel,
  SuggestionSource,
  DetailedSentenceAnalysis,
} from '../types';
import { sessionApi, suggestApi } from '../services/api';

// Cache for storing suggestions per sentence
// 用于存储每个句子建议的缓存
type SuggestionsCache = Map<string, SuggestResponse>;

// Cache for storing analysis results per sentence
// 用于存储每个句子分析结果的缓存
type AnalysisCache = Map<string, DetailedSentenceAnalysis>;

// Cache for storing custom text drafts per sentence
// 用于存储每个句子自定义文本草稿的缓存
type CustomTextCache = Map<string, string>;

// Counter for tracking suggestion request IDs to handle race conditions
// 用于追踪建议请求ID的计数器，处理竞态条件
let suggestionRequestCounter = 0;

interface SessionStore {
  // State
  // 状态
  session: SessionState | null;
  isLoading: boolean;
  error: string | null;
  suggestions: SuggestResponse | null;
  isLoadingSuggestions: boolean;
  customText: string;
  validationResult: {
    passed: boolean;
    similarity: number;
    message: string;
  } | null;
  suggestionsCache: SuggestionsCache;  // Cache for suggestions by sentence ID
  analysisCache: AnalysisCache;  // Cache for analysis results by sentence ID
  customTextCache: CustomTextCache;  // Cache for custom text drafts by sentence ID
  currentSuggestionRequestId: number;  // Track current request to handle race conditions / 追踪当前请求ID以处理竞态条件

  // Actions
  // 动作
  startSession: (
    documentId: string,
    options: {
      mode?: 'intervention' | 'yolo';
      colloquialismLevel?: number;
      targetLang?: string;
      processLevels?: RiskLevel[];
    }
  ) => Promise<void>;

  loadCurrentState: (sessionId: string) => Promise<void>;
  loadSuggestions: (sentence: SentenceAnalysis, colloquialismLevel: number, forceRefresh?: boolean) => Promise<void>;
  nextSentence: () => Promise<void>;
  skipSentence: () => Promise<void>;
  flagSentence: () => Promise<void>;
  applySuggestion: (source: SuggestionSource) => Promise<void>;
  applyCustom: () => Promise<void>;
  setCustomText: (text: string) => void;
  setCustomTextForSentence: (sentenceId: string, text: string) => void;  // Save custom text to cache
  getCustomTextForSentence: (sentenceId: string) => string;  // Get custom text from cache
  setAnalysisForSentence: (sentenceId: string, analysis: DetailedSentenceAnalysis) => void;  // Save analysis to cache
  getAnalysisForSentence: (sentenceId: string) => DetailedSentenceAnalysis | null;  // Get analysis from cache
  validateCustomText: () => Promise<void>;
  completeSession: () => Promise<void>;
  clearError: () => void;
  clearAllCaches: () => void;  // Clear all caches for new session
  reset: () => void;
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  // Initial state
  // 初始状态
  session: null,
  isLoading: false,
  error: null,
  suggestions: null,
  isLoadingSuggestions: false,
  customText: '',
  validationResult: null,
  suggestionsCache: new Map(),  // Cache: sentenceId -> SuggestResponse
  analysisCache: new Map(),  // Cache: sentenceId -> DetailedSentenceAnalysis
  customTextCache: new Map(),  // Cache: sentenceId -> custom text draft
  currentSuggestionRequestId: 0,  // Track current request ID / 追踪当前请求ID

  // Start a new session
  // 开始新会话
  startSession: async (documentId, options) => {
    // Clear all caches for new session
    // 为新会话清除所有缓存
    set({
      isLoading: true,
      error: null,
      suggestionsCache: new Map(),
      analysisCache: new Map(),
      customTextCache: new Map(),
    });
    try {
      const session = await sessionApi.start(documentId, options);
      set({ session, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Load current session state
  // 加载当前会话状态
  loadCurrentState: async (sessionId) => {
    set({ isLoading: true, error: null });
    try {
      const session = await sessionApi.getCurrent(sessionId);
      set({ session, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Load suggestions for current sentence (with caching and race condition handling)
  // 为当前句子加载建议（带缓存和竞态条件处理）
  loadSuggestions: async (sentence, colloquialismLevel, forceRefresh = false) => {
    const { suggestionsCache } = get();
    const cacheKey = sentence.id;

    // Check cache first (unless force refresh requested)
    // 首先检查缓存（除非请求强制刷新）
    if (!forceRefresh && suggestionsCache.has(cacheKey)) {
      const cachedSuggestions = suggestionsCache.get(cacheKey)!;
      set({ suggestions: cachedSuggestions, isLoadingSuggestions: false, customText: '' });
      return;
    }

    // Generate unique request ID and store it to handle race conditions
    // 生成唯一请求ID并存储，用于处理竞态条件
    const requestId = ++suggestionRequestCounter;
    set({ isLoadingSuggestions: true, suggestions: null, currentSuggestionRequestId: requestId });

    try {
      const suggestions = await suggestApi.getSuggestions(sentence.text, {
        issues: sentence.issues.map((i) => ({
          type: i.type,
          description: i.description,
        })),
        lockedTerms: sentence.lockedTerms,
        colloquialismLevel,
      });

      // Check if this request is still the current one (race condition guard)
      // 检查此请求是否仍然是当前请求（竞态条件保护）
      if (get().currentSuggestionRequestId !== requestId) {
        // This request is stale, discard the result
        // 此请求已过期，丢弃结果
        console.log('[loadSuggestions] Discarding stale response for:', cacheKey);
        return;
      }

      // Store in cache
      // 存入缓存
      const newCache = new Map(get().suggestionsCache);
      newCache.set(cacheKey, suggestions);

      set({
        suggestions,
        isLoadingSuggestions: false,
        customText: '',
        suggestionsCache: newCache,
      });
    } catch (error) {
      // Only update error state if this is still the current request
      // 仅当这仍然是当前请求时才更新错误状态
      if (get().currentSuggestionRequestId === requestId) {
        set({
          error: (error as Error).message,
          isLoadingSuggestions: false
        });
      }
    }
  },

  // Move to next sentence
  // 移动到下一句
  nextSentence: async () => {
    const { session } = get();
    if (!session) return;

    set({ isLoading: true, error: null, suggestions: null, validationResult: null });
    try {
      const newSession = await sessionApi.next(session.sessionId);
      set({ session: newSession, isLoading: false, customText: '' });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Skip current sentence (without auto-jumping to next)
  // 跳过当前句子（不自动跳转到下一句）
  skipSentence: async () => {
    const { session } = get();
    if (!session) return;

    set({ isLoading: true, error: null });
    try {
      const newSession = await sessionApi.skip(session.sessionId);
      set({
        session: newSession,
        isLoading: false,
        suggestions: null,  // Clear suggestions to show "已处理" state
        customText: '',
        validationResult: null,
      });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Flag sentence for manual review (without auto-jumping to next)
  // 标记句子需要人工审核（不自动跳转到下一句）
  flagSentence: async () => {
    const { session } = get();
    if (!session) return;

    set({ isLoading: true, error: null });
    try {
      const newSession = await sessionApi.flag(session.sessionId);
      set({
        session: newSession,
        isLoading: false,
        suggestions: null,  // Clear suggestions to show "已处理" state
        customText: '',
        validationResult: null,
      });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Apply suggestion from Track A or B
  // 应用轨道A或B的建议
  applySuggestion: async (source) => {
    const { session, suggestions } = get();
    if (!session || !session.currentSentence || !suggestions) return;

    const suggestion = source === 'llm' ? suggestions.llmSuggestion : suggestions.ruleSuggestion;
    if (!suggestion) return;

    set({ isLoading: true, error: null });
    try {
      // Save modification to database using sentence ID
      // 使用句子ID将修改保存到数据库
      await sessionApi.applySuggestion(
        session.sessionId,
        session.currentSentence.id,  // Use database ID, not index
        source,
        suggestion.rewritten
      );

      // Update session state without auto-jumping to next sentence
      // 更新会话状态，但不自动跳转到下一句（节省token）
      // User will click on sidebar to navigate
      // 用户将点击侧边栏进行导航
      const newSession = await sessionApi.getCurrent(session.sessionId);
      set({
        session: newSession,
        isLoading: false,
        suggestions: null,  // Clear suggestions to indicate completion
        customText: '',
        validationResult: null,
      });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Apply custom text
  // 应用自定义文本
  applyCustom: async () => {
    const { session, customText, validationResult } = get();
    if (!session || !session.currentSentence || !customText) return;

    // Must pass validation first
    // 必须先通过验证
    if (!validationResult?.passed) {
      set({ error: 'Please validate the custom text first' });
      return;
    }

    set({ isLoading: true, error: null });
    try {
      await sessionApi.applySuggestion(
        session.sessionId,
        session.currentSentence.id,  // Use database ID, not index
        'custom',
        customText
      );

      // Update session state without auto-jumping to next sentence
      // 更新会话状态，但不自动跳转到下一句（节省token）
      const newSession = await sessionApi.getCurrent(session.sessionId);
      set({
        session: newSession,
        isLoading: false,
        suggestions: null,  // Clear suggestions to indicate completion
        customText: '',
        validationResult: null,
      });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Set custom text
  // 设置自定义文本
  setCustomText: (text) => {
    set({ customText: text, validationResult: null });
  },

  // Validate custom text
  // 验证自定义文本
  validateCustomText: async () => {
    const { session, customText } = get();
    if (!session || !session.currentSentence || !customText) return;

    try {
      const result = await suggestApi.validateCustom(
        session.sessionId,
        session.currentSentence.id,  // Use database ID
        customText
      );
      set({
        validationResult: {
          passed: result.passed,
          similarity: result.semanticSimilarity,
          message: result.messageZh || result.message,
        },
      });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  // Complete session
  // 完成会话
  completeSession: async () => {
    const { session } = get();
    if (!session) return;

    set({ isLoading: true, error: null });
    try {
      await sessionApi.complete(session.sessionId);
      set({ isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Clear error
  // 清除错误
  clearError: () => set({ error: null }),

  // Set custom text for a specific sentence (save to cache)
  // 为特定句子设置自定义文本（保存到缓存）
  setCustomTextForSentence: (sentenceId, text) => {
    const { customTextCache } = get();
    const newCache = new Map(customTextCache);
    newCache.set(sentenceId, text);
    set({ customTextCache: newCache });
  },

  // Get custom text for a specific sentence from cache
  // 从缓存获取特定句子的自定义文本
  getCustomTextForSentence: (sentenceId) => {
    const { customTextCache } = get();
    return customTextCache.get(sentenceId) || '';
  },

  // Set analysis result for a specific sentence (save to cache)
  // 为特定句子设置分析结果（保存到缓存）
  setAnalysisForSentence: (sentenceId, analysis) => {
    const { analysisCache } = get();
    const newCache = new Map(analysisCache);
    newCache.set(sentenceId, analysis);
    set({ analysisCache: newCache });
  },

  // Get analysis result for a specific sentence from cache
  // 从缓存获取特定句子的分析结果
  getAnalysisForSentence: (sentenceId) => {
    const { analysisCache } = get();
    return analysisCache.get(sentenceId) || null;
  },

  // Clear all caches (call when starting new session)
  // 清除所有缓存（开始新会话时调用）
  clearAllCaches: () => set({
    suggestionsCache: new Map(),
    analysisCache: new Map(),
    customTextCache: new Map(),
  }),

  // Reset store
  // 重置存储
  reset: () =>
    set({
      session: null,
      isLoading: false,
      error: null,
      suggestions: null,
      isLoadingSuggestions: false,
      customText: '',
      validationResult: null,
      suggestionsCache: new Map(),
      analysisCache: new Map(),
      customTextCache: new Map(),
      currentSuggestionRequestId: 0,
    }),
}));
