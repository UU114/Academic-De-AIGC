/**
 * Auth Store - Authentication state management
 * 认证存储 - 认证状态管理
 *
 * Now integrates with user microservice at /api/user/*
 * 现在与用户微服务集成 /api/user/*
 *
 * Supports registration with phone + password + email (via SMS verification)
 * 支持手机号 + 密码 + 邮箱注册（通过短信验证）
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// ==========================================
// Types
// 类型定义
// ==========================================

/**
 * User info from microservice
 * 来自微服务的用户信息
 */
export interface UserInfo {
  userId: string;
  phone: string;
  email?: string;
  createdAt?: string;
  // Legacy fields for backward compatibility
  // 向后兼容的遗留字段
  platformUserId?: string;
  nickname?: string;
  isDebug?: boolean;
}

export interface RegisterData {
  phone: string;
  password: string;
  passwordConfirm: string;
  email?: string;
}

export interface AuthState {
  // State
  token: string | null;
  refreshToken: string | null;
  user: UserInfo | null;
  isLoggedIn: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  setAuth: (token: string, user: UserInfo, refreshToken?: string) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  checkAuth: () => Promise<void>;
  // Legacy actions (for backward compatibility)
  logout: () => void;
  setToken: (token: string, user: UserInfo) => void;
}

// ==========================================
// API Base URL (User Microservice)
// API基础URL（用户微服务）
// ==========================================

const USER_API_BASE = '/api/user';

// ==========================================
// Store
// 存储
// ==========================================

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      // 初始状态
      token: null,
      refreshToken: null,
      user: null,
      isLoggedIn: false,
      isLoading: false,
      error: null,

      // Set auth state (called by LoginModal after successful login/register)
      // 设置认证状态（登录/注册成功后由LoginModal调用）
      setAuth: (token: string, user: UserInfo, refreshToken?: string) => {
        set({
          token,
          refreshToken: refreshToken || null,
          user,
          isLoggedIn: true,
          error: null,
        });
      },

      // Clear auth state (logout)
      // 清除认证状态（登出）
      clearAuth: () => {
        const token = get().token;

        // Call microservice logout API (fire and forget)
        // 调用微服务登出API（不等待结果）
        if (token) {
          fetch(`${USER_API_BASE}/logout`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }).catch(() => {});
        }

        set({
          token: null,
          refreshToken: null,
          user: null,
          isLoggedIn: false,
          error: null,
        });
      },

      // Set loading state
      // 设置加载状态
      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      // Set error
      // 设置错误
      setError: (error: string | null) => {
        set({ error });
      },

      // Clear error
      // 清除错误
      clearError: () => {
        set({ error: null });
      },

      // Check current auth status via microservice
      // 通过微服务检查当前认证状态
      checkAuth: async () => {
        const token = get().token;

        if (!token) {
          set({ isLoggedIn: false, user: null });
          return;
        }

        set({ isLoading: true });

        try {
          const response = await fetch(`${USER_API_BASE}/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            // Token expired or invalid - try refresh
            // 令牌过期或无效 - 尝试刷新
            const refreshToken = get().refreshToken;
            if (refreshToken) {
              try {
                const refreshResponse = await fetch(`${USER_API_BASE}/token/refresh`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ refresh_token: refreshToken }),
                });

                if (refreshResponse.ok) {
                  const refreshData = await refreshResponse.json();
                  set({
                    token: refreshData.token,
                    refreshToken: refreshData.refreshToken || refreshToken,
                    isLoading: false,
                  });
                  // Retry auth check with new token
                  // 使用新令牌重试认证检查
                  get().checkAuth();
                  return;
                }
              } catch {
                // Refresh failed, clear auth
                // 刷新失败，清除认证
              }
            }

            set({
              token: null,
              refreshToken: null,
              user: null,
              isLoggedIn: false,
              isLoading: false,
            });
            return;
          }

          const data = await response.json();

          set({
            user: {
              userId: data.userId || data.user_id,
              phone: data.phone,
              email: data.email,
              createdAt: data.createdAt || data.created_at,
            },
            isLoggedIn: true,
            isLoading: false,
          });
        } catch {
          set({
            token: null,
            refreshToken: null,
            user: null,
            isLoggedIn: false,
            isLoading: false,
          });
        }
      },

      // Legacy: logout (alias for clearAuth)
      // 遗留: 登出（clearAuth的别名）
      logout: () => {
        get().clearAuth();
      },

      // Legacy: setToken (alias for setAuth without refreshToken)
      // 遗留: 设置令牌（不带refreshToken的setAuth别名）
      setToken: (token: string, user: UserInfo) => {
        get().setAuth(token, user);
      },
    }),
    {
      name: 'academicguard-auth',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
        isLoggedIn: state.isLoggedIn,
      }),
    }
  )
);

// ==========================================
// Helper Functions
// 辅助函数
// ==========================================

/**
 * Get authorization header for API requests
 * 获取API请求的授权头
 */
export const getAuthHeader = (): Record<string, string> => {
  const token = useAuthStore.getState().token;
  if (!token) return {};
  return { 'Authorization': `Bearer ${token}` };
};

/**
 * Check if user is authenticated
 * 检查用户是否已认证
 */
export const isAuthenticated = (): boolean => {
  return useAuthStore.getState().isLoggedIn;
};
