/**
 * Mode Store - System mode state management
 * 模式存储 - 系统模式状态管理
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// ==========================================
// Types
// 类型定义
// ==========================================

export interface PricingConfig {
  pricePerUnit: number;      // Price per 100 words (每100词价格)
  minimumCharge: number;     // Minimum charge (最低消费)
  currency: string;          // Currency code (货币代码)
}

export interface ModeFeatures {
  requireLogin: boolean;     // Whether login is required (是否需要登录)
  requirePayment: boolean;   // Whether payment is required (是否需要支付)
  showPricing: boolean;      // Whether to show pricing (是否显示价格)
  paymentSkipped: boolean;   // Whether payment is skipped (是否跳过支付)
}

export interface ModeState {
  // State
  mode: 'debug' | 'operational';
  isDebug: boolean;
  isOperational: boolean;
  platformConfigured: boolean;
  features: ModeFeatures;
  pricing: PricingConfig;
  isLoaded: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  loadMode: () => Promise<void>;
  reset: () => void;
}

// ==========================================
// Default Values
// 默认值
// ==========================================

const defaultFeatures: ModeFeatures = {
  requireLogin: false,
  requirePayment: false,
  showPricing: true,
  paymentSkipped: true,
};

const defaultPricing: PricingConfig = {
  pricePerUnit: 2.0,
  minimumCharge: 50.0,
  currency: 'CNY',
};

// ==========================================
// Store
// 存储
// ==========================================

export const useModeStore = create<ModeState>()(
  persist(
    (set, get) => ({
      // Initial state (default to debug mode)
      // 初始状态（默认为调试模式）
      mode: 'debug',
      isDebug: true,
      isOperational: false,
      platformConfigured: false,
      features: defaultFeatures,
      pricing: defaultPricing,
      isLoaded: false,
      isLoading: false,
      error: null,

      // Load mode from server
      // 从服务器加载模式
      loadMode: async () => {
        // Don't reload if already loading
        if (get().isLoading) return;

        set({ isLoading: true, error: null });

        try {
          const response = await fetch('/api/v1/auth/mode');

          if (!response.ok) {
            throw new Error('Failed to fetch system mode');
          }

          const data = await response.json();

          set({
            mode: data.mode,
            isDebug: data.is_debug,
            isOperational: data.is_operational,
            platformConfigured: data.platform_configured,
            features: {
              requireLogin: data.features.require_login,
              requirePayment: data.features.require_payment,
              showPricing: data.features.show_pricing,
              paymentSkipped: data.features.payment_skipped,
            },
            pricing: {
              pricePerUnit: data.pricing.price_per_100_words,
              minimumCharge: data.pricing.minimum_charge,
              currency: data.pricing.currency,
            },
            isLoaded: true,
            isLoading: false,
          });
        } catch (error) {
          console.error('Failed to load system mode:', error);
          // Fallback to debug mode on error
          // 出错时回退到调试模式
          set({
            mode: 'debug',
            isDebug: true,
            isOperational: false,
            features: defaultFeatures,
            pricing: defaultPricing,
            isLoaded: true,
            isLoading: false,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      },

      // Reset state
      // 重置状态
      reset: () => {
        set({
          mode: 'debug',
          isDebug: true,
          isOperational: false,
          platformConfigured: false,
          features: defaultFeatures,
          pricing: defaultPricing,
          isLoaded: false,
          isLoading: false,
          error: null,
        });
      },
    }),
    {
      name: 'academicguard-mode',
      partialize: (state) => ({
        mode: state.mode,
        isDebug: state.isDebug,
        features: state.features,
        pricing: state.pricing,
      }),
    }
  )
);

// ==========================================
// Selector Hooks
// 选择器钩子
// ==========================================

/**
 * Check if payment is required for processing
 * 检查处理是否需要支付
 */
export const usePaymentRequired = () => {
  const { features } = useModeStore();
  return features.requirePayment;
};

/**
 * Check if login is required
 * 检查是否需要登录
 */
export const useLoginRequired = () => {
  const { features } = useModeStore();
  return features.requireLogin;
};

/**
 * Get pricing configuration
 * 获取定价配置
 */
export const usePricing = () => {
  const { pricing } = useModeStore();
  return pricing;
};
