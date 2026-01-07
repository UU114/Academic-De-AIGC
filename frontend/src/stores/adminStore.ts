/**
 * Admin Store - Admin authentication state management
 * 管理员存储 - 管理员认证状态管理
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// ==========================================
// Types
// 类型定义
// ==========================================

export interface AdminState {
  // State
  adminToken: string | null;
  isAdminLoggedIn: boolean;
  isLoading: boolean;
  error: string | null;
  adminId: string | null;

  // Actions
  adminLogin: (secretKey: string) => Promise<boolean>;
  adminLogout: () => void;
  checkAdminAuth: () => boolean;
  clearError: () => void;
}

// ==========================================
// API Base URL
// API基础URL
// ==========================================

const API_BASE = '/api/v1/admin';

// ==========================================
// Store
// 存储
// ==========================================

export const useAdminStore = create<AdminState>()(
  persist(
    (set, get) => ({
      // Initial state
      // 初始状态
      adminToken: null,
      isAdminLoggedIn: false,
      isLoading: false,
      error: null,
      adminId: null,

      // Admin login with secret key
      // 使用密钥登录管理员
      adminLogin: async (secretKey: string) => {
        set({ isLoading: true, error: null });

        try {
          const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ secret_key: secretKey }),
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.detail?.message_zh || data.detail?.message || 'Login failed');
          }

          set({
            adminToken: data.access_token,
            isAdminLoggedIn: true,
            isLoading: false,
            adminId: data.admin_id,
          });

          return true;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          set({ isLoading: false, error: message });
          return false;
        }
      },

      // Admin logout
      // 管理员登出
      adminLogout: () => {
        set({
          adminToken: null,
          isAdminLoggedIn: false,
          error: null,
          adminId: null,
        });
      },

      // Check if admin is authenticated (token exists)
      // 检查管理员是否已认证（令牌存在）
      checkAdminAuth: () => {
        const token = get().adminToken;
        return !!token;
      },

      // Clear error
      // 清除错误
      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'academicguard-admin',
      partialize: (state) => ({
        adminToken: state.adminToken,
        isAdminLoggedIn: state.isAdminLoggedIn,
        adminId: state.adminId,
      }),
    }
  )
);

// ==========================================
// Helper Functions
// 辅助函数
// ==========================================

/**
 * Get admin authorization header for API requests
 * 获取管理员API请求的授权头
 */
export const getAdminAuthHeader = (): Record<string, string> => {
  const token = useAdminStore.getState().adminToken;
  if (!token) return {};
  return { 'Authorization': `Bearer ${token}` };
};

/**
 * Check if admin is authenticated
 * 检查管理员是否已认证
 */
export const isAdminAuthenticated = (): boolean => {
  return useAdminStore.getState().isAdminLoggedIn;
};
