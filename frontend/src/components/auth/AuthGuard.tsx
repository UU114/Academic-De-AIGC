/**
 * Auth Guard Component
 * 认证守卫组件
 *
 * Wraps content that requires authentication in operational mode.
 * 包装在运营模式下需要认证的内容。
 */

import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { useModeStore } from '../../stores/modeStore';
import LoginModal from './LoginModal';

interface AuthGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  fallback?: React.ReactNode;
  onAuthRequired?: () => void;
}

export default function AuthGuard({
  children,
  requireAuth = false,
  fallback,
  onAuthRequired,
}: AuthGuardProps) {
  const { isLoggedIn, checkAuth } = useAuthStore();
  const { isDebug, isLoaded, loadMode } = useModeStore();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  // Load mode and check auth on mount
  // 挂载时加载模式并检查认证
  useEffect(() => {
    const init = async () => {
      if (!isLoaded) {
        await loadMode();
      }
      await checkAuth();
      setIsChecking(false);
    };
    init();
  }, [isLoaded, loadMode, checkAuth]);

  // Show loading while checking
  // 检查时显示加载
  if (isChecking) {
    return fallback || null;
  }

  // In debug mode, always allow access
  // 调试模式下始终允许访问
  if (isDebug) {
    return <>{children}</>;
  }

  // In operational mode, check if auth required
  // 运营模式下检查是否需要认证
  if (requireAuth && !isLoggedIn) {
    // Show login modal or call callback
    // 显示登录弹窗或调用回调
    if (onAuthRequired) {
      onAuthRequired();
      return fallback || null;
    }

    return (
      <>
        {fallback || (
          <div className="flex flex-col items-center justify-center p-8">
            <p className="text-gray-600 mb-4">Please login to continue</p>
            <button
              onClick={() => setShowLoginModal(true)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Login 登录
            </button>
          </div>
        )}
        <LoginModal
          isOpen={showLoginModal}
          onClose={() => setShowLoginModal(false)}
        />
      </>
    );
  }

  return <>{children}</>;
}

/**
 * Higher-order component for auth guarding
 * 用于认证守卫的高阶组件
 */
export function withAuthGuard<P extends object>(
  Component: React.ComponentType<P>,
  options?: { requireAuth?: boolean }
) {
  return function AuthGuardedComponent(props: P) {
    return (
      <AuthGuard requireAuth={options?.requireAuth}>
        <Component {...props} />
      </AuthGuard>
    );
  };
}
