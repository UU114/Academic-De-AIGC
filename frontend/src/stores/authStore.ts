/**
 * Auth Store - Authentication state management
 * 认证存储 - 认证状态管理
 *
 * Supports registration with phone + password + email
 * 支持手机号 + 密码 + 邮箱注册
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// ==========================================
// Types
// 类型定义
// ==========================================

export interface UserInfo {
  userId: string;
  platformUserId?: string;
  nickname?: string;
  phone?: string;
  isDebug: boolean;
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
  user: UserInfo | null;
  isLoggedIn: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (phone: string, password: string) => Promise<boolean>;
  register: (data: RegisterData) => Promise<{ success: boolean; message?: string }>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  setToken: (token: string, user: UserInfo) => void;
  clearError: () => void;
}

// ==========================================
// API Base URL
// API基础URL
// ==========================================

const API_BASE = '/api/v1/auth';

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
      user: null,
      isLoggedIn: false,
      isLoading: false,
      error: null,

      // Register new user
      // 注册新用户
      register: async (data: RegisterData) => {
        set({ isLoading: true, error: null });

        try {
          const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              phone: data.phone,
              password: data.password,
              password_confirm: data.passwordConfirm,
              email: data.email || null,
            }),
          });

          const result = await response.json();

          if (!response.ok) {
            throw new Error(result.detail?.message_zh || result.detail?.message || 'Registration failed');
          }

          set({ isLoading: false });

          return {
            success: true,
            message: result.message_zh || result.message,
          };
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          set({ isLoading: false, error: message });
          return { success: false, message };
        }
      },

      // Login with phone and password
      // 使用手机号和密码登录
      login: async (phone: string, password: string) => {
        set({ isLoading: true, error: null });

        try {
          const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, password }),
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.detail?.message_zh || data.detail?.message || 'Login failed');
          }

          const user: UserInfo = {
            userId: data.user.platform_user_id,
            platformUserId: data.user.platform_user_id,
            nickname: data.user.nickname,
            phone: data.user.phone,
            isDebug: data.system_mode === 'debug',
          };

          set({
            token: data.access_token,
            user,
            isLoggedIn: true,
            isLoading: false,
          });

          return true;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          set({ isLoading: false, error: message });
          return false;
        }
      },

      // Logout
      // 登出
      logout: () => {
        const token = get().token;

        // Call logout API (fire and forget)
        // 调用登出API（不等待结果）
        if (token) {
          fetch(`${API_BASE}/logout`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }).catch(() => {});
        }

        set({
          token: null,
          user: null,
          isLoggedIn: false,
          error: null,
        });
      },

      // Check current auth status
      // 检查当前认证状态
      checkAuth: async () => {
        const token = get().token;

        if (!token) {
          set({ isLoggedIn: false, user: null });
          return;
        }

        set({ isLoading: true });

        try {
          const response = await fetch(`${API_BASE}/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            // Token expired or invalid
            // 令牌过期或无效
            set({
              token: null,
              user: null,
              isLoggedIn: false,
              isLoading: false,
            });
            return;
          }

          const data = await response.json();

          set({
            user: {
              userId: data.user_id,
              platformUserId: data.platform_user_id,
              nickname: data.nickname,
              phone: data.phone,
              isDebug: data.is_debug,
            },
            isLoggedIn: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            token: null,
            user: null,
            isLoggedIn: false,
            isLoading: false,
          });
        }
      },

      // Set token and user directly (for SSO or other auth methods)
      // 直接设置令牌和用户（用于SSO或其他认证方式）
      setToken: (token: string, user: UserInfo) => {
        set({
          token,
          user,
          isLoggedIn: true,
        });
      },

      // Clear error
      // 清除错误
      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'academicguard-auth',
      partialize: (state) => ({
        token: state.token,
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
