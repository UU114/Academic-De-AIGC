/**
 * Login/Register Modal Component
 * 登录/注册弹窗组件
 *
 * Supports login with phone + password and registration with phone + password + email
 * 支持手机号+密码登录，以及手机号+密码+邮箱注册
 */

import React, { useState, useEffect } from 'react';
import { X, Phone, Lock, Mail, AlertCircle, Loader2, Eye, EyeOff, CheckCircle } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

type ModalMode = 'login' | 'register';

export default function LoginModal({ isOpen, onClose, onSuccess }: LoginModalProps) {
  const { login, register, isLoading, error, clearError } = useAuthStore();

  const [mode, setMode] = useState<ModalMode>('login');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [email, setEmail] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Clear state when modal opens/closes
  // 弹窗打开/关闭时清除状态
  useEffect(() => {
    if (isOpen) {
      clearError();
      setPhone('');
      setPassword('');
      setPasswordConfirm('');
      setEmail('');
      setSuccessMessage(null);
      setShowPassword(false);
      setShowPasswordConfirm(false);
    }
  }, [isOpen, clearError]);

  // Clear error when switching modes
  // 切换模式时清除错误
  useEffect(() => {
    clearError();
    setSuccessMessage(null);
  }, [mode, clearError]);

  // Validate phone number format
  // 验证手机号格式
  const isPhoneValid = /^1[3-9]\d{9}$/.test(phone);

  // Validate email format (optional)
  // 验证邮箱格式（可选）
  const isEmailValid = !email || /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email);

  // Validate password
  // 验证密码
  const isPasswordValid = password.length >= 6 && password.length <= 32;
  const isPasswordMatch = password === passwordConfirm;

  // Check if form is valid
  // 检查表单是否有效
  const isLoginValid = isPhoneValid && password.length > 0;
  const isRegisterValid = isPhoneValid && isPasswordValid && isPasswordMatch && isEmailValid;

  // Handle login
  // 处理登录
  const handleLogin = async () => {
    if (!isLoginValid) return;

    const success = await login(phone, password);
    if (success) {
      onSuccess?.();
      onClose();
    }
  };

  // Handle registration
  // 处理注册
  const handleRegister = async () => {
    if (!isRegisterValid) return;

    const result = await register({
      phone,
      password,
      passwordConfirm,
      email: email || undefined,
    });

    if (result.success) {
      setSuccessMessage('注册成功！正在自动登录...');
      // Auto-login after successful registration
      // 注册成功后自动登录
      setTimeout(async () => {
        const loginSuccess = await login(phone, password);
        if (loginSuccess) {
          onSuccess?.();
          onClose();
        } else {
          // If auto-login fails, switch to login mode
          // 如果自动登录失败，切换到登录模式
          setMode('login');
          setPassword('');
          setPasswordConfirm('');
          setEmail('');
          setSuccessMessage(null);
        }
      }, 800);
    }
  };

  // Handle form submit
  // 处理表单提交
  const handleSubmit = () => {
    if (mode === 'login') {
      handleLogin();
    } else {
      handleRegister();
    }
  };

  // Handle key press
  // 处理按键
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
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
              {mode === 'login' ? 'Login 登录' : 'Register 注册'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {mode === 'login' ? '使用手机号和密码登录' : '创建新账号'}
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
        <div className="p-6 space-y-4">
          {/* Success message */}
          {successMessage && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center gap-2 text-green-700">
                <CheckCircle className="w-5 h-5" />
                <span className="text-sm">{successMessage}</span>
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
            {phone && !isPhoneValid && (
              <p className="mt-1 text-sm text-red-500">请输入有效的手机号</p>
            )}
          </div>

          {/* Password input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password 密码
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={mode === 'register' ? '6-32位密码' : '请输入密码'}
                className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
            {mode === 'register' && password && !isPasswordValid && (
              <p className="mt-1 text-sm text-red-500">密码长度需要6-32位</p>
            )}
          </div>

          {/* Password confirm (register only) */}
          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confirm Password 确认密码
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showPasswordConfirm ? 'text' : 'password'}
                  value={passwordConfirm}
                  onChange={(e) => setPasswordConfirm(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="再次输入密码"
                  className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPasswordConfirm ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {passwordConfirm && !isPasswordMatch && (
                <p className="mt-1 text-sm text-red-500">两次输入的密码不一致</p>
              )}
            </div>
          )}

          {/* Email input (register only, optional) */}
          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email 邮箱 <span className="text-gray-400 font-normal">(可选，用于找回密码)</span>
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="your@email.com"
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  disabled={isLoading}
                />
              </div>
              {email && !isEmailValid && (
                <p className="mt-1 text-sm text-red-500">请输入有效的邮箱地址</p>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 bg-gray-50 border-t">
          <button
            onClick={handleSubmit}
            disabled={(mode === 'login' ? !isLoginValid : !isRegisterValid) || isLoading}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {isLoading && <Loader2 className="w-5 h-5 animate-spin" />}
            {isLoading
              ? (mode === 'login' ? 'Logging in...' : 'Registering...')
              : (mode === 'login' ? 'Login 登录' : 'Register 注册')}
          </button>

          {/* Mode switch */}
          <div className="mt-4 text-center">
            {mode === 'login' ? (
              <p className="text-sm text-gray-600">
                没有账号？{' '}
                <button
                  onClick={() => setMode('register')}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                  disabled={isLoading}
                >
                  立即注册
                </button>
              </p>
            ) : (
              <p className="text-sm text-gray-600">
                已有账号？{' '}
                <button
                  onClick={() => setMode('login')}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                  disabled={isLoading}
                >
                  立即登录
                </button>
              </p>
            )}
          </div>

          <p className="mt-4 text-center text-xs text-gray-400">
            By continuing, you agree to our Terms of Service
          </p>
        </div>
      </div>
    </div>
  );
}
