/**
 * Login Modal Component
 * 登录弹窗组件
 */

import React, { useState, useEffect } from 'react';
import { X, Phone, Lock, AlertCircle, Loader2 } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { useModeStore } from '../../stores/modeStore';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function LoginModal({ isOpen, onClose, onSuccess }: LoginModalProps) {
  const { login, sendCode, isLoading, error, clearError } = useAuthStore();
  const { isDebug } = useModeStore();

  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [debugHint, setDebugHint] = useState<string | null>(null);

  // Countdown timer for resend
  // 重发倒计时
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  // Clear error when modal opens/closes
  // 弹窗打开/关闭时清除错误
  useEffect(() => {
    if (isOpen) {
      clearError();
      setPhone('');
      setCode('');
      setCodeSent(false);
      setDebugHint(null);
    }
  }, [isOpen, clearError]);

  // Validate phone number format
  // 验证手机号格式
  const isPhoneValid = /^1[3-9]\d{9}$/.test(phone);

  // Handle send code
  // 处理发送验证码
  const handleSendCode = async () => {
    if (!isPhoneValid) return;

    const result = await sendCode(phone);
    if (result.success) {
      setCodeSent(true);
      setCountdown(60);
      if (result.debugHint) {
        setDebugHint(result.debugHint);
      }
    }
  };

  // Handle login
  // 处理登录
  const handleLogin = async () => {
    if (!isPhoneValid || code.length < 4) return;

    const success = await login(phone, code);
    if (success) {
      onSuccess?.();
      onClose();
    }
  };

  // Handle key press
  // 处理按键
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (!codeSent) {
        handleSendCode();
      } else {
        handleLogin();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {isDebug ? 'Debug Login' : 'Login'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {isDebug ? '调试模式登录' : '使用手机号登录'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Debug mode notice */}
          {isDebug && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-amber-500 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-amber-800">Debug Mode</p>
                  <p className="text-amber-700 mt-1">
                    调试模式下，任意验证码都可以通过。建议使用: 123456
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center gap-2 text-red-700">
                <AlertCircle className="w-5 h-5" />
                <span className="text-sm">{error}</span>
              </div>
            </div>
          )}

          {/* Phone input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Phone Number 手机号
            </label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 11))}
                onKeyPress={handleKeyPress}
                placeholder="13800138000"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Code input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Verification Code 验证码
            </label>
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  onKeyPress={handleKeyPress}
                  placeholder={debugHint || '123456'}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  disabled={isLoading}
                />
              </div>
              <button
                onClick={handleSendCode}
                disabled={!isPhoneValid || countdown > 0 || isLoading}
                className="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
              >
                {countdown > 0 ? `${countdown}s` : codeSent ? 'Resend' : 'Get Code'}
              </button>
            </div>
            {debugHint && (
              <p className="mt-2 text-sm text-amber-600">
                Debug hint: {debugHint}
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 bg-gray-50 border-t">
          <button
            onClick={handleLogin}
            disabled={!isPhoneValid || code.length < 4 || isLoading}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {isLoading && <Loader2 className="w-5 h-5 animate-spin" />}
            {isLoading ? 'Logging in...' : 'Login 登录'}
          </button>

          <p className="mt-4 text-center text-sm text-gray-500">
            By logging in, you agree to our Terms of Service
          </p>
        </div>
      </div>
    </div>
  );
}
