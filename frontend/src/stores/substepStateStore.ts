/**
 * Substep State Store - Zustand store for caching substep states
 * 子步骤状态存储 - 用于缓存子步骤状态的Zustand存储
 *
 * This store manages:
 * 1. Caching of LLM analysis results to avoid repeated calls
 * 2. User inputs/selections for each substep
 * 3. Syncing with backend database for persistence
 *
 * 此存储管理：
 * 1. 缓存LLM分析结果以避免重复调用
 * 2. 每个子步骤的用户输入/选择
 * 3. 与后端数据库同步以实现持久化
 */

import { create } from 'zustand';
import axios from 'axios';

// API base for substep state operations
const api = axios.create({
  baseURL: '/api/v1/substep-state',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token interceptor
api.interceptors.request.use((config) => {
  try {
    const authData = localStorage.getItem('academicguard-auth');
    if (authData) {
      const parsed = JSON.parse(authData);
      if (parsed.state?.token) {
        config.headers.Authorization = `Bearer ${parsed.state.token}`;
      }
    }
  } catch {
    // Ignore parse errors
  }
  return config;
});

// ============================================
// Types
// 类型定义
// ============================================

export interface SubstepState {
  id: string;
  sessionId: string;
  stepName: string;
  analysisResult: Record<string, unknown> | null;
  userInputs: Record<string, unknown> | null;
  modifiedText: string | null;
  status: 'pending' | 'completed' | 'skipped';
  createdAt?: string;
  updatedAt?: string;
}

interface SubstepStateStore {
  // State
  // 状态
  states: Map<string, SubstepState>;  // key: stepName
  currentSessionId: string | null;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  lastSyncTime: Map<string, Date>;  // key: stepName -> last sync time

  // Actions
  // 动作

  // Initialize store for a session (loads all cached states from DB)
  // 为会话初始化存储（从数据库加载所有缓存状态）
  initForSession: (sessionId: string) => Promise<void>;

  // Get cached state for a step (from memory first, then DB)
  // 获取步骤的缓存状态（优先从内存，然后从数据库）
  getState: (stepName: string) => SubstepState | null;

  // Check if a step has cached state (quick check without loading full data)
  // 检查步骤是否有缓存状态（快速检查，不加载完整数据）
  hasState: (stepName: string) => boolean;

  // Save analysis result for a step (saves to memory and DB)
  // 保存步骤的分析结果（保存到内存和数据库）
  saveAnalysisResult: (stepName: string, result: Record<string, unknown>) => Promise<void>;

  // Save user inputs for a step (saves to memory and DB)
  // 保存步骤的用户输入（保存到内存和数据库）
  saveUserInputs: (stepName: string, inputs: Record<string, unknown>) => Promise<void>;

  // Update user inputs incrementally (merges with existing)
  // 增量更新用户输入（与现有合并）
  updateUserInputs: (stepName: string, inputs: Record<string, unknown>) => Promise<void>;

  // Save modified text for a step
  // 保存步骤的修改文本
  saveModifiedText: (stepName: string, text: string) => Promise<void>;

  // Mark step as completed
  // 标记步骤为已完成
  markCompleted: (stepName: string) => Promise<void>;

  // Mark step as skipped
  // 标记步骤为已跳过
  markSkipped: (stepName: string) => Promise<void>;

  // Clear state for a specific step (for re-analysis)
  // 清除特定步骤的状态（用于重新分析）
  clearState: (stepName: string) => Promise<void>;

  // Clear all states for current session
  // 清除当前会话的所有状态
  clearAllStates: () => Promise<void>;

  // Reload state from DB for a specific step
  // 从数据库重新加载特定步骤的状态
  reloadState: (stepName: string) => Promise<SubstepState | null>;

  // Reset store (when changing sessions)
  // 重置存储（切换会话时）
  reset: () => void;

  // Clear error
  // 清除错误
  clearError: () => void;
}

// Helper to convert snake_case to camelCase
const toCamelCase = (obj: unknown): unknown => {
  if (obj === null || obj === undefined) return obj;
  if (Array.isArray(obj)) {
    return obj.map(item => toCamelCase(item));
  }
  if (typeof obj === 'object') {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
      result[camelKey] = toCamelCase(value);
    }
    return result;
  }
  return obj;
};

export const useSubstepStateStore = create<SubstepStateStore>((set, get) => ({
  // Initial state
  states: new Map(),
  currentSessionId: null,
  isLoading: false,
  isSaving: false,
  error: null,
  lastSyncTime: new Map(),

  // Initialize store for a session
  initForSession: async (sessionId: string) => {
    // If same session, skip reload
    if (get().currentSessionId === sessionId && get().states.size > 0) {
      return;
    }

    set({ isLoading: true, error: null, currentSessionId: sessionId });

    try {
      const response = await api.get(`/load-all/${sessionId}`);
      const data = toCamelCase(response.data) as {
        sessionId: string;
        states: Record<string, SubstepState>;
        totalCount: number;
      };

      const statesMap = new Map<string, SubstepState>();
      const syncTimeMap = new Map<string, Date>();

      for (const [stepName, state] of Object.entries(data.states || {})) {
        statesMap.set(stepName, state);
        syncTimeMap.set(stepName, new Date());
      }

      set({
        states: statesMap,
        lastSyncTime: syncTimeMap,
        isLoading: false,
      });
    } catch (error) {
      // No cached states is not an error, just empty
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        set({ states: new Map(), isLoading: false });
      } else {
        set({ error: (error as Error).message, isLoading: false });
      }
    }
  },

  // Get cached state for a step
  getState: (stepName: string) => {
    const { states } = get();
    return states.get(stepName) || null;
  },

  // Check if step has cached state
  hasState: (stepName: string) => {
    const { states } = get();
    const state = states.get(stepName);
    // Has state if analysisResult exists
    return state?.analysisResult != null;
  },

  // Save analysis result
  saveAnalysisResult: async (stepName: string, result: Record<string, unknown>) => {
    const { currentSessionId, states } = get();
    if (!currentSessionId) {
      set({ error: 'No active session' });
      return;
    }

    set({ isSaving: true, error: null });

    try {
      const response = await api.post('/save', {
        session_id: currentSessionId,
        step_name: stepName,
        analysis_result: result,
        status: 'pending',
      });
      const savedState = toCamelCase(response.data) as SubstepState;

      // Update local cache
      const newStates = new Map(states);
      newStates.set(stepName, savedState);

      const newSyncTime = new Map(get().lastSyncTime);
      newSyncTime.set(stepName, new Date());

      set({ states: newStates, lastSyncTime: newSyncTime, isSaving: false });
    } catch (error) {
      set({ error: (error as Error).message, isSaving: false });
    }
  },

  // Save user inputs
  saveUserInputs: async (stepName: string, inputs: Record<string, unknown>) => {
    const { currentSessionId, states } = get();
    if (!currentSessionId) {
      set({ error: 'No active session' });
      return;
    }

    set({ isSaving: true, error: null });

    try {
      const existingState = states.get(stepName);

      const response = await api.post('/save', {
        session_id: currentSessionId,
        step_name: stepName,
        analysis_result: existingState?.analysisResult || null,
        user_inputs: inputs,
        status: existingState?.status || 'pending',
      });
      const savedState = toCamelCase(response.data) as SubstepState;

      // Update local cache
      const newStates = new Map(states);
      newStates.set(stepName, savedState);

      const newSyncTime = new Map(get().lastSyncTime);
      newSyncTime.set(stepName, new Date());

      set({ states: newStates, lastSyncTime: newSyncTime, isSaving: false });
    } catch (error) {
      set({ error: (error as Error).message, isSaving: false });
    }
  },

  // Update user inputs incrementally
  updateUserInputs: async (stepName: string, inputs: Record<string, unknown>) => {
    const { currentSessionId, states } = get();
    if (!currentSessionId) {
      set({ error: 'No active session' });
      return;
    }

    set({ isSaving: true, error: null });

    try {
      const response = await api.post(`/update-user-inputs/${currentSessionId}/${stepName}`, inputs);
      const data = toCamelCase(response.data) as { userInputs: Record<string, unknown> };

      // Update local cache
      const existingState = states.get(stepName);
      const newStates = new Map(states);
      newStates.set(stepName, {
        ...(existingState || {
          id: '',
          sessionId: currentSessionId,
          stepName,
          analysisResult: null,
          modifiedText: null,
          status: 'pending' as const,
        }),
        userInputs: data.userInputs,
      });

      const newSyncTime = new Map(get().lastSyncTime);
      newSyncTime.set(stepName, new Date());

      set({ states: newStates, lastSyncTime: newSyncTime, isSaving: false });
    } catch (error) {
      set({ error: (error as Error).message, isSaving: false });
    }
  },

  // Save modified text
  saveModifiedText: async (stepName: string, text: string) => {
    const { currentSessionId, states } = get();
    if (!currentSessionId) {
      set({ error: 'No active session' });
      return;
    }

    set({ isSaving: true, error: null });

    try {
      const existingState = states.get(stepName);

      const response = await api.post('/save', {
        session_id: currentSessionId,
        step_name: stepName,
        analysis_result: existingState?.analysisResult || null,
        user_inputs: existingState?.userInputs || null,
        modified_text: text,
        status: existingState?.status || 'pending',
      });
      const savedState = toCamelCase(response.data) as SubstepState;

      // Update local cache
      const newStates = new Map(states);
      newStates.set(stepName, savedState);

      const newSyncTime = new Map(get().lastSyncTime);
      newSyncTime.set(stepName, new Date());

      set({ states: newStates, lastSyncTime: newSyncTime, isSaving: false });
    } catch (error) {
      set({ error: (error as Error).message, isSaving: false });
    }
  },

  // Mark step as completed
  markCompleted: async (stepName: string) => {
    const { currentSessionId, states } = get();
    if (!currentSessionId) return;

    set({ isSaving: true, error: null });

    try {
      const existingState = states.get(stepName);

      const response = await api.post('/save', {
        session_id: currentSessionId,
        step_name: stepName,
        analysis_result: existingState?.analysisResult || null,
        user_inputs: existingState?.userInputs || null,
        modified_text: existingState?.modifiedText || null,
        status: 'completed',
      });
      const savedState = toCamelCase(response.data) as SubstepState;

      const newStates = new Map(states);
      newStates.set(stepName, savedState);

      set({ states: newStates, isSaving: false });
    } catch (error) {
      set({ error: (error as Error).message, isSaving: false });
    }
  },

  // Mark step as skipped
  markSkipped: async (stepName: string) => {
    const { currentSessionId, states } = get();
    if (!currentSessionId) return;

    set({ isSaving: true, error: null });

    try {
      const existingState = states.get(stepName);

      const response = await api.post('/save', {
        session_id: currentSessionId,
        step_name: stepName,
        analysis_result: existingState?.analysisResult || null,
        user_inputs: existingState?.userInputs || null,
        modified_text: existingState?.modifiedText || null,
        status: 'skipped',
      });
      const savedState = toCamelCase(response.data) as SubstepState;

      const newStates = new Map(states);
      newStates.set(stepName, savedState);

      set({ states: newStates, isSaving: false });
    } catch (error) {
      set({ error: (error as Error).message, isSaving: false });
    }
  },

  // Clear state for a specific step
  clearState: async (stepName: string) => {
    const { currentSessionId, states } = get();
    if (!currentSessionId) return;

    set({ isSaving: true, error: null });

    try {
      await api.delete(`/clear/${currentSessionId}/${stepName}`);

      const newStates = new Map(states);
      newStates.delete(stepName);

      const newSyncTime = new Map(get().lastSyncTime);
      newSyncTime.delete(stepName);

      set({ states: newStates, lastSyncTime: newSyncTime, isSaving: false });
    } catch (error) {
      set({ error: (error as Error).message, isSaving: false });
    }
  },

  // Clear all states
  clearAllStates: async () => {
    const { currentSessionId } = get();
    if (!currentSessionId) return;

    set({ isSaving: true, error: null });

    try {
      await api.delete(`/clear-all/${currentSessionId}`);
      set({
        states: new Map(),
        lastSyncTime: new Map(),
        isSaving: false,
      });
    } catch (error) {
      set({ error: (error as Error).message, isSaving: false });
    }
  },

  // Reload state from DB
  reloadState: async (stepName: string) => {
    const { currentSessionId, states } = get();
    if (!currentSessionId) return null;

    set({ isLoading: true, error: null });

    try {
      const response = await api.get(`/load/${currentSessionId}/${stepName}`);
      const state = toCamelCase(response.data) as SubstepState;

      const newStates = new Map(states);
      newStates.set(stepName, state);

      const newSyncTime = new Map(get().lastSyncTime);
      newSyncTime.set(stepName, new Date());

      set({ states: newStates, lastSyncTime: newSyncTime, isLoading: false });
      return state;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        // No cached state, not an error
        set({ isLoading: false });
        return null;
      }
      set({ error: (error as Error).message, isLoading: false });
      return null;
    }
  },

  // Reset store
  reset: () => {
    set({
      states: new Map(),
      currentSessionId: null,
      isLoading: false,
      isSaving: false,
      error: null,
      lastSyncTime: new Map(),
    });
  },

  // Clear error
  clearError: () => set({ error: null }),
}));

// ============================================
// Helper hooks for common patterns
// 常用模式的辅助hooks
// ============================================

/**
 * Hook to check if a step should use cached data or call LLM
 * 用于检查步骤是否应使用缓存数据或调用LLM的hook
 */
export const useShouldUseCachedAnalysis = (stepName: string): boolean => {
  const hasState = useSubstepStateStore((state) => state.hasState(stepName));
  return hasState;
};

/**
 * Hook to get cached analysis result for a step
 * 获取步骤缓存分析结果的hook
 */
export const useCachedAnalysisResult = (stepName: string): Record<string, unknown> | null => {
  const state = useSubstepStateStore((state) => state.getState(stepName));
  return state?.analysisResult || null;
};

/**
 * Hook to get cached user inputs for a step
 * 获取步骤缓存用户输入的hook
 */
export const useCachedUserInputs = (stepName: string): Record<string, unknown> | null => {
  const state = useSubstepStateStore((state) => state.getState(stepName));
  return state?.userInputs || null;
};
