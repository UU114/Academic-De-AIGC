/**
 * Custom hook for substep caching
 * 子步骤缓存自定义hook
 *
 * Provides a simple interface for LayerStep components to:
 * 1. Check if cached analysis exists
 * 2. Load cached analysis or call API
 * 3. Save analysis results
 * 4. Save/restore user inputs
 *
 * 为LayerStep组件提供简单接口：
 * 1. 检查是否存在缓存分析
 * 2. 加载缓存分析或调用API
 * 3. 保存分析结果
 * 4. 保存/恢复用户输入
 */

import { useCallback, useEffect, useRef } from 'react';
import { useSubstepStateStore } from '../stores/substepStateStore';

interface UseSubstepCacheOptions<T> {
  // Step name (e.g., 'layer5-step1-1')
  stepName: string;
  // Session ID
  sessionId: string | null;
  // Function to call API for fresh analysis
  analyzeApi: () => Promise<T>;
  // Callback when analysis is complete (either from cache or API)
  onAnalysisComplete?: (result: T, fromCache: boolean) => void;
  // Callback when user inputs are restored from cache
  onUserInputsRestored?: (inputs: Record<string, unknown>) => void;
}

interface UseSubstepCacheResult<T> {
  // Check if this step has cached data
  hasCachedData: boolean;
  // Run analysis (uses cache if available, otherwise calls API)
  runAnalysis: () => Promise<T | null>;
  // Force fresh analysis (ignores cache)
  runFreshAnalysis: () => Promise<T | null>;
  // Save user inputs to cache
  saveUserInputs: (inputs: Record<string, unknown>) => Promise<void>;
  // Get cached user inputs
  getCachedUserInputs: () => Record<string, unknown> | null;
  // Clear cache for this step
  clearCache: () => Promise<void>;
  // Loading states
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
}

export function useSubstepCache<T>({
  stepName,
  sessionId,
  analyzeApi,
  onAnalysisComplete,
  onUserInputsRestored,
}: UseSubstepCacheOptions<T>): UseSubstepCacheResult<T> {
  const {
    initForSession,
    getState,
    hasState,
    saveAnalysisResult,
    saveUserInputs: storeSaveUserInputs,
    clearState,
    isLoading,
    isSaving,
    error,
  } = useSubstepStateStore();

  // Track initialization
  const initializedRef = useRef(false);

  // Initialize store when session changes
  useEffect(() => {
    if (sessionId && !initializedRef.current) {
      initializedRef.current = true;
      initForSession(sessionId).catch(console.error);
    }
  }, [sessionId, initForSession]);

  // Check if cached data exists
  const hasCachedData = sessionId ? hasState(stepName) : false;

  // Run analysis (with cache check)
  const runAnalysis = useCallback(async (): Promise<T | null> => {
    if (!sessionId) {
      // No session, just call API
      const result = await analyzeApi();
      onAnalysisComplete?.(result, false);
      return result;
    }

    // Check cache
    const cachedState = getState(stepName);
    if (cachedState?.analysisResult) {
      console.log(`[useSubstepCache] Using cached result for ${stepName}`);
      const result = cachedState.analysisResult as T;

      // Restore user inputs if available
      if (cachedState.userInputs && onUserInputsRestored) {
        onUserInputsRestored(cachedState.userInputs);
      }

      onAnalysisComplete?.(result, true);
      return result;
    }

    // No cache, call API
    console.log(`[useSubstepCache] Calling API for ${stepName}`);
    try {
      const result = await analyzeApi();

      // Save to cache
      await saveAnalysisResult(stepName, result as Record<string, unknown>);

      onAnalysisComplete?.(result, false);
      return result;
    } catch (err) {
      console.error(`[useSubstepCache] Analysis failed for ${stepName}:`, err);
      throw err;
    }
  }, [sessionId, stepName, getState, saveAnalysisResult, analyzeApi, onAnalysisComplete, onUserInputsRestored]);

  // Run fresh analysis (ignore cache)
  const runFreshAnalysis = useCallback(async (): Promise<T | null> => {
    console.log(`[useSubstepCache] Running fresh analysis for ${stepName}`);

    // Clear existing cache first
    if (sessionId) {
      await clearState(stepName);
    }

    try {
      const result = await analyzeApi();

      // Save to cache
      if (sessionId) {
        await saveAnalysisResult(stepName, result as Record<string, unknown>);
      }

      onAnalysisComplete?.(result, false);
      return result;
    } catch (err) {
      console.error(`[useSubstepCache] Fresh analysis failed for ${stepName}:`, err);
      throw err;
    }
  }, [sessionId, stepName, clearState, saveAnalysisResult, analyzeApi, onAnalysisComplete]);

  // Save user inputs
  const saveUserInputs = useCallback(async (inputs: Record<string, unknown>): Promise<void> => {
    if (!sessionId) return;
    await storeSaveUserInputs(stepName, inputs);
  }, [sessionId, stepName, storeSaveUserInputs]);

  // Get cached user inputs
  const getCachedUserInputs = useCallback((): Record<string, unknown> | null => {
    const cachedState = getState(stepName);
    return cachedState?.userInputs || null;
  }, [stepName, getState]);

  // Clear cache
  const clearCache = useCallback(async (): Promise<void> => {
    if (!sessionId) return;
    await clearState(stepName);
  }, [sessionId, stepName, clearState]);

  return {
    hasCachedData,
    runAnalysis,
    runFreshAnalysis,
    saveUserInputs,
    getCachedUserInputs,
    clearCache,
    isLoading,
    isSaving,
    error,
  };
}

export default useSubstepCache;
