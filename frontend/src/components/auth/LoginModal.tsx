/**
 * Login/Register Modal Component
 * 登录/注册弹窗组件
 *
 * Features:
 * - Login: Phone + Password
 * - Register: CAPTCHA -> SMS Code -> Phone + Password + Email
 * - Password Reset: Email + CAPTCHA -> Reset Link
 *
 * All user operations call the user microservice at /api/user/*
 * 所有用户操作调用用户微服务 /api/user/*
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  X, Phone, Lock, Mail, AlertCircle, Loader2,
  Eye, EyeOff, CheckCircle, MessageSquare, ArrowLeft
} from 'lucide-react';
import AliyunCaptcha, { useCaptcha } from './AliyunCaptcha';
import * as userApi from '../../services/userApi';
import { useAuthStore } from '../../stores/authStore';

// ==========================================
// Types
// 类型定义
// ==========================================

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

type ModalMode = 'login' | 'register' | 'forgot';
type RegisterStep = 'captcha' | 'sms' | 'form';

// ==========================================
// Configuration
// 配置
// ==========================================

// Aliyun CAPTCHA configuration from environment variables
// 从环境变量获取阿里云验证码配置
const ALIYUN_CAPTCHA_SCENE_ID = import.meta.env.VITE_ALIYUN_CAPTCHA_SCENE_ID || '';
const ALIYUN_CAPTCHA_APP_KEY = import.meta.env.VITE_ALIYUN_CAPTCHA_APP_KEY || '';

// ==========================================
// Component
// 组件
// ==========================================

export default function LoginModal({ isOpen, onClose, onSuccess }: LoginModalProps) {
  const { setAuth } = useAuthStore();

  // Mode and step state
  const [mode, setMode] = useState<ModalMode>('login');
  const [registerStep, setRegisterStep] = useState<RegisterStep>('captcha');

  // Form state
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [email, setEmail] = useState('');
  const [smsCode, setSmsCode] = useState('');

  // UI state
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // SMS countdown
  const [smsCountdown, setSmsCountdown] = useState(0);

  // CAPTCHA state
  const captcha = useCaptcha();

  // ==========================================
  // Reset state when modal opens/closes
  // 弹窗打开/关闭时重置状态
  // ==========================================

  useEffect(() => {
    if (isOpen) {
      resetForm();
    }
  }, [isOpen]);

  const resetForm = useCallback(() => {
    setMode('login');
    setRegisterStep('captcha');
    setPhone('');
    setPassword('');
    setPasswordConfirm('');
    setEmail('');
    setSmsCode('');
    setShowPassword(false);
    setShowPasswordConfirm(false);
    setError(null);
    setSuccessMessage(null);
    captcha.reset();
  }, [captcha]);

  // Clear error when switching modes
  useEffect(() => {
    setError(null);
    setSuccessMessage(null);
  }, [mode, registerStep]);

  // SMS countdown timer
  useEffect(() => {
    if (smsCountdown > 0) {
      const timer = setTimeout(() => setSmsCountdown(smsCountdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [smsCountdown]);

  // ==========================================
  // Validation
  // 表单验证
  // ==========================================

  const isPhoneValid = /^1[3-9]\d{9}$/.test(phone);
  const isEmailValid = !email || /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email);
  const isPasswordValid = password.length >= 6 && password.length <= 32;
  const isPasswordMatch = password === passwordConfirm;
  const isSmsCodeValid = /^\d{4,6}$/.test(smsCode);

  const isLoginValid = isPhoneValid && password.length > 0;
  const isRegisterValid = isPhoneValid && isPasswordValid && isPasswordMatch && isSmsCodeValid;
  const isForgotValid = isEmailValid && email.length > 0 && captcha.isVerified;

  // ==========================================
  // Handlers
  // 处理函数
  // ==========================================

  /**
   * Handle login
   * 处理登录
   */
  const handleLogin = async () => {
    if (!isLoginValid) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await userApi.login({
        phone,
        password,
        captcha: captcha.captchaParam || undefined,
      });

      if (response.success && response.token && response.user) {
        setAuth(response.token, response.user, response.refreshToken);
        setSuccessMessage('登录成功！');
        setTimeout(() => {
          onSuccess?.();
          onClose();
        }, 500);
      } else {
        setError(response.messageZh || response.message || '登录失败');
      }
    } catch (err) {
      setError((err as Error).message || '登录失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle send SMS code
   * 处理发送短信验证码
   */
  const handleSendSms = async () => {
    if (!isPhoneValid || !captcha.captchaParam) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await userApi.sendSmsCode({
        phone,
        captcha: captcha.captchaParam,
      });

      if (response.success) {
        setSmsCountdown(60);
        setRegisterStep('form');
        setSuccessMessage('验证码已发送');
      } else {
        setError(response.messageZh || response.message || '发送失败');
      }
    } catch (err) {
      setError((err as Error).message || '发送验证码失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle registration
   * 处理注册
   */
  const handleRegister = async () => {
    if (!isRegisterValid || !captcha.captchaParam) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await userApi.register({
        phone,
        password,
        passwordConfirm,
        smsCode,
        email: email || undefined,
        captcha: captcha.captchaParam,
      });

      if (response.success) {
        setSuccessMessage('注册成功！正在自动登录...');

        // Auto login after registration
        setTimeout(async () => {
          try {
            const loginResponse = await userApi.login({ phone, password });
            if (loginResponse.success && loginResponse.token && loginResponse.user) {
              setAuth(loginResponse.token, loginResponse.user, loginResponse.refreshToken);
              onSuccess?.();
              onClose();
            } else {
              setMode('login');
              setSuccessMessage('注册成功，请登录');
            }
          } catch {
            setMode('login');
            setSuccessMessage('注册成功，请登录');
          }
        }, 800);
      } else {
        setError(response.messageZh || response.message || '注册失败');
      }
    } catch (err) {
      setError((err as Error).message || '注册失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle forgot password
   * 处理找回密码
   */
  const handleForgotPassword = async () => {
    if (!isForgotValid || !captcha.captchaParam) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await userApi.requestPasswordReset({
        email,
        captcha: captcha.captchaParam,
      });

      if (response.success) {
        setSuccessMessage('重置链接已发送到您的邮箱，请查收');
      } else {
        setError(response.messageZh || response.message || '发送失败');
      }
    } catch (err) {
      setError((err as Error).message || '发送失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle form submit
   * 处理表单提交
   */
  const handleSubmit = () => {
    if (mode === 'login') {
      handleLogin();
    } else if (mode === 'register') {
      if (registerStep === 'sms') {
        handleSendSms();
      } else if (registerStep === 'form') {
        handleRegister();
      }
    } else if (mode === 'forgot') {
      handleForgotPassword();
    }
  };

  /**
   * Handle key press
   */
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  /**
   * Handle CAPTCHA success for registration
   */
  const handleRegisterCaptchaSuccess = (param: userApi.CaptchaVerifyParam) => {
    captcha.onCaptchaSuccess(param);
    setRegisterStep('sms');
  };

  // ==========================================
  // Render
  // 渲染
  // ==========================================

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b sticky top-0 bg-white z-10">
          <div className="flex items-center gap-3">
            {/* Back button for register steps */}
            {mode === 'register' && registerStep !== 'captcha' && (
              <button
                onClick={() => {
                  if (registerStep === 'form') setRegisterStep('sms');
                  else if (registerStep === 'sms') setRegisterStep('captcha');
                }}
                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-500" />
              </button>
            )}
            {mode === 'forgot' && (
              <button
                onClick={() => setMode('login')}
                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-500" />
              </button>
            )}
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {mode === 'login' && 'Login 登录'}
                {mode === 'register' && 'Register 注册'}
                {mode === 'forgot' && 'Reset Password 找回密码'}
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                {mode === 'login' && '使用手机号和密码登录'}
                {mode === 'register' && registerStep === 'captcha' && '第1步：人机验证'}
                {mode === 'register' && registerStep === 'sms' && '第2步：验证手机号'}
                {mode === 'register' && registerStep === 'form' && '第3步：设置密码'}
                {mode === 'forgot' && '通过邮箱找回密码'}
              </p>
            </div>
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

          {/* ==========================================
              LOGIN MODE
              登录模式
              ========================================== */}
          {mode === 'login' && (
            <>
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
                    placeholder="请输入密码"
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
              </div>

              {/* Forgot password link */}
              <div className="text-right">
                <button
                  onClick={() => setMode('forgot')}
                  className="text-sm text-blue-600 hover:text-blue-700"
                  disabled={isLoading}
                >
                  忘记密码？
                </button>
              </div>
            </>
          )}

          {/* ==========================================
              REGISTER MODE - CAPTCHA STEP
              注册模式 - 验证码步骤
              ========================================== */}
          {mode === 'register' && registerStep === 'captcha' && (
            <div className="py-4">
              <p className="text-gray-600 mb-4 text-center">
                请完成人机验证以继续注册
              </p>
              <AliyunCaptcha
                sceneId={ALIYUN_CAPTCHA_SCENE_ID}
                appKey={ALIYUN_CAPTCHA_APP_KEY}
                onSuccess={handleRegisterCaptchaSuccess}
                onFail={captcha.onCaptchaFail}
                buttonText="点击进行安全验证"
              />
            </div>
          )}

          {/* ==========================================
              REGISTER MODE - SMS STEP
              注册模式 - 短信步骤
              ========================================== */}
          {mode === 'register' && registerStep === 'sms' && (
            <>
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

              <p className="text-sm text-gray-500">
                点击下方按钮，我们将发送验证码到您的手机
              </p>
            </>
          )}

          {/* ==========================================
              REGISTER MODE - FORM STEP
              注册模式 - 表单步骤
              ========================================== */}
          {mode === 'register' && registerStep === 'form' && (
            <>
              {/* Phone display */}
              <div className="bg-gray-50 rounded-lg p-3 flex items-center gap-2">
                <Phone className="w-5 h-5 text-gray-400" />
                <span className="text-gray-700">{phone}</span>
                <CheckCircle className="w-4 h-4 text-green-500 ml-auto" />
              </div>

              {/* SMS Code input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SMS Code 短信验证码
                </label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <MessageSquare className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      value={smsCode}
                      onChange={(e) => setSmsCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      onKeyPress={handleKeyPress}
                      placeholder="请输入验证码"
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                      disabled={isLoading}
                    />
                  </div>
                  <button
                    onClick={handleSendSms}
                    disabled={smsCountdown > 0 || isLoading}
                    className="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
                  >
                    {smsCountdown > 0 ? `${smsCountdown}s` : '重新发送'}
                  </button>
                </div>
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
                    placeholder="6-32位密码"
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
                {password && !isPasswordValid && (
                  <p className="mt-1 text-sm text-red-500">密码长度需要6-32位</p>
                )}
              </div>

              {/* Password confirm */}
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

              {/* Email input (optional) */}
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
            </>
          )}

          {/* ==========================================
              FORGOT PASSWORD MODE
              找回密码模式
              ========================================== */}
          {mode === 'forgot' && (
            <>
              {/* Email input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email 注册邮箱
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

              {/* CAPTCHA */}
              <AliyunCaptcha
                sceneId={ALIYUN_CAPTCHA_SCENE_ID}
                appKey={ALIYUN_CAPTCHA_APP_KEY}
                onSuccess={captcha.onCaptchaSuccess}
                onFail={captcha.onCaptchaFail}
                buttonText="点击进行安全验证"
                disabled={!email || !isEmailValid}
              />

              <p className="text-sm text-gray-500">
                我们将发送密码重置链接到您的注册邮箱
              </p>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 bg-gray-50 border-t">
          {/* Submit button */}
          {!(mode === 'register' && registerStep === 'captcha') && (
            <button
              onClick={handleSubmit}
              disabled={
                isLoading ||
                (mode === 'login' && !isLoginValid) ||
                (mode === 'register' && registerStep === 'sms' && !isPhoneValid) ||
                (mode === 'register' && registerStep === 'form' && !isRegisterValid) ||
                (mode === 'forgot' && !isForgotValid)
              }
              className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {isLoading && <Loader2 className="w-5 h-5 animate-spin" />}
              {mode === 'login' && (isLoading ? '登录中...' : 'Login 登录')}
              {mode === 'register' && registerStep === 'sms' && (isLoading ? '发送中...' : '发送验证码')}
              {mode === 'register' && registerStep === 'form' && (isLoading ? '注册中...' : 'Register 注册')}
              {mode === 'forgot' && (isLoading ? '发送中...' : '发送重置链接')}
            </button>
          )}

          {/* Mode switch */}
          <div className="mt-4 text-center">
            {mode === 'login' && (
              <p className="text-sm text-gray-600">
                没有账号？{' '}
                <button
                  onClick={() => {
                    setMode('register');
                    setRegisterStep('captcha');
                    captcha.reset();
                  }}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                  disabled={isLoading}
                >
                  立即注册
                </button>
              </p>
            )}
            {mode === 'register' && (
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
            {mode === 'forgot' && (
              <p className="text-sm text-gray-600">
                想起密码了？{' '}
                <button
                  onClick={() => setMode('login')}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                  disabled={isLoading}
                >
                  返回登录
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
