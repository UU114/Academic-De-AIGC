/**
 * Mode Indicator Component
 * 模式指示器组件
 *
 * Shows current system mode (debug/operational) in the UI.
 * 在UI中显示当前系统模式（调试/运营）。
 */

import React from 'react';
import { Bug, Shield, AlertTriangle } from 'lucide-react';
import { useModeStore } from '../../stores/modeStore';
import { useAuthStore } from '../../stores/authStore';

interface ModeIndicatorProps {
  showDetails?: boolean;
  className?: string;
}

export default function ModeIndicator({ showDetails = false, className = '' }: ModeIndicatorProps) {
  const { mode, isDebug, pricing, features, isLoaded } = useModeStore();
  const { isLoggedIn, user } = useAuthStore();

  if (!isLoaded) {
    return null;
  }

  // Compact badge for header
  // 标题栏的紧凑徽章
  if (!showDetails) {
    return (
      <div className={`inline-flex items-center gap-1.5 ${className}`}>
        {isDebug ? (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-amber-100 text-amber-700 text-xs font-medium rounded-full">
            <Bug className="w-3 h-3" />
            Debug
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
            <Shield className="w-3 h-3" />
            Live
          </span>
        )}
      </div>
    );
  }

  // Detailed panel for settings/info pages
  // 设置/信息页面的详细面板
  return (
    <div className={`bg-white border rounded-xl p-4 ${className}`}>
      <div className="flex items-start gap-4">
        {/* Mode icon */}
        <div className={`p-3 rounded-lg ${isDebug ? 'bg-amber-100' : 'bg-green-100'}`}>
          {isDebug ? (
            <Bug className="w-6 h-6 text-amber-600" />
          ) : (
            <Shield className="w-6 h-6 text-green-600" />
          )}
        </div>

        {/* Mode details */}
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900">
            {isDebug ? 'Debug Mode 调试模式' : 'Operational Mode 运营模式'}
          </h3>

          <p className="text-sm text-gray-600 mt-1">
            {isDebug
              ? 'No login or payment required. All features are free for testing.'
              : 'Full authentication and payment flow enabled.'}
          </p>

          {/* Feature list */}
          <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
            <div className="flex items-center gap-2">
              <span className={features.requireLogin ? 'text-green-600' : 'text-gray-400'}>
                {features.requireLogin ? '✓' : '✗'}
              </span>
              <span>Login Required</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={features.requirePayment ? 'text-green-600' : 'text-gray-400'}>
                {features.requirePayment ? '✓' : '✗'}
              </span>
              <span>Payment Required</span>
            </div>
          </div>

          {/* Pricing info */}
          {features.showPricing && (
            <div className="mt-3 p-3 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700">Pricing 定价</p>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-gray-900">
                  ¥{pricing.pricePerUnit}
                </span>
                <span className="text-sm text-gray-500">/ 100 words</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Minimum charge: ¥{pricing.minimumCharge} 最低消费
              </p>
            </div>
          )}

          {/* Debug mode warning */}
          {isDebug && (
            <div className="mt-3 flex items-start gap-2 p-3 bg-amber-50 rounded-lg">
              <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5" />
              <p className="text-xs text-amber-700">
                Debug mode is for development only. Do not use in production.
                <br />
                调试模式仅供开发使用，请勿在生产环境使用。
              </p>
            </div>
          )}

          {/* User info if logged in */}
          {isLoggedIn && user && (
            <div className="mt-3 pt-3 border-t">
              <p className="text-sm text-gray-600">
                Logged in as: <span className="font-medium">{user.nickname || user.phone || 'User'}</span>
                {user.isDebug && (
                  <span className="ml-2 text-xs text-amber-600">(Debug User)</span>
                )}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Floating debug badge for corner display
 * 角落显示的浮动调试徽章
 */
export function FloatingModeBadge() {
  const { isDebug, isLoaded } = useModeStore();

  if (!isLoaded || !isDebug) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className="flex items-center gap-2 px-3 py-2 bg-amber-500 text-white text-sm font-medium rounded-lg shadow-lg">
        <Bug className="w-4 h-4" />
        <span>Debug Mode</span>
      </div>
    </div>
  );
}
