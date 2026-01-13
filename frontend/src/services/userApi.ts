/**
 * User Microservice API
 * 用户微服务 API
 *
 * All user-related operations are handled by a separate microservice.
 * 所有用户相关操作由独立的微服务处理。
 *
 * API Base: /api/user/*  (proxied by Nginx to user microservice)
 */

const USER_API_BASE = '/api/user';

// ==========================================
// Types
// 类型定义
// ==========================================

export interface CaptchaVerifyParam {
  captchaVerifyParam: string;  // Aliyun CAPTCHA verification parameter
  lotNumber?: string;
  passToken?: string;
  genTime?: string;
}

export interface SendSmsRequest {
  phone: string;
  captcha: CaptchaVerifyParam;  // Must pass CAPTCHA first
}

export interface RegisterRequest {
  phone: string;
  password: string;
  passwordConfirm: string;
  smsCode: string;  // SMS verification code
  email?: string;   // Optional, for password recovery
  captcha: CaptchaVerifyParam;
}

export interface LoginRequest {
  phone: string;
  password: string;
  captcha?: CaptchaVerifyParam;  // Optional, required if triggered by risk control
}

export interface ResetPasswordRequest {
  email: string;
  captcha: CaptchaVerifyParam;
}

export interface ResetPasswordConfirmRequest {
  token: string;     // Token from email link
  password: string;
  passwordConfirm: string;
}

export interface UserInfo {
  userId: string;
  phone: string;
  email?: string;
  createdAt: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  messageZh: string;
  token?: string;       // JWT token
  refreshToken?: string;
  user?: UserInfo;
}

export interface ApiError {
  error: string;
  message: string;
  messageZh: string;
}

// ==========================================
// API Functions
// API 函数
// ==========================================

/**
 * Handle API response
 * 处理 API 响应
 */
async function handleResponse<T>(response: Response): Promise<T> {
  const data = await response.json();

  if (!response.ok) {
    const error = data as ApiError;
    throw new Error(error.messageZh || error.message || 'Request failed');
  }

  return data as T;
}

/**
 * Send SMS verification code
 * 发送短信验证码
 *
 * Requires CAPTCHA verification first
 * 需要先通过图形验证码
 */
export async function sendSmsCode(request: SendSmsRequest): Promise<AuthResponse> {
  const response = await fetch(`${USER_API_BASE}/sms/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      phone: request.phone,
      captcha_verify_param: request.captcha.captchaVerifyParam,
    }),
  });

  return handleResponse<AuthResponse>(response);
}

/**
 * Register new user
 * 用户注册
 *
 * Flow: CAPTCHA -> SMS Code -> Register
 * 流程: 图形验证码 -> 短信验证码 -> 注册
 */
export async function register(request: RegisterRequest): Promise<AuthResponse> {
  const response = await fetch(`${USER_API_BASE}/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      phone: request.phone,
      password: request.password,
      password_confirm: request.passwordConfirm,
      sms_code: request.smsCode,
      email: request.email,
      captcha_verify_param: request.captcha.captchaVerifyParam,
    }),
  });

  return handleResponse<AuthResponse>(response);
}

/**
 * User login
 * 用户登录
 */
export async function login(request: LoginRequest): Promise<AuthResponse> {
  const response = await fetch(`${USER_API_BASE}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      phone: request.phone,
      password: request.password,
      captcha_verify_param: request.captcha?.captchaVerifyParam,
    }),
  });

  return handleResponse<AuthResponse>(response);
}

/**
 * Request password reset
 * 请求密码重置
 *
 * Sends reset link to email
 * 发送重置链接到邮箱
 */
export async function requestPasswordReset(request: ResetPasswordRequest): Promise<AuthResponse> {
  const response = await fetch(`${USER_API_BASE}/password/reset-request`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: request.email,
      captcha_verify_param: request.captcha.captchaVerifyParam,
    }),
  });

  return handleResponse<AuthResponse>(response);
}

/**
 * Confirm password reset
 * 确认密码重置
 *
 * Called after user clicks email link
 * 用户点击邮件链接后调用
 */
export async function confirmPasswordReset(request: ResetPasswordConfirmRequest): Promise<AuthResponse> {
  const response = await fetch(`${USER_API_BASE}/password/reset-confirm`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      token: request.token,
      password: request.password,
      password_confirm: request.passwordConfirm,
    }),
  });

  return handleResponse<AuthResponse>(response);
}

/**
 * Get current user info
 * 获取当前用户信息
 */
export async function getCurrentUser(token: string): Promise<UserInfo> {
  const response = await fetch(`${USER_API_BASE}/me`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  return handleResponse<UserInfo>(response);
}

/**
 * Refresh access token
 * 刷新访问令牌
 */
export async function refreshToken(refreshToken: string): Promise<AuthResponse> {
  const response = await fetch(`${USER_API_BASE}/token/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      refresh_token: refreshToken,
    }),
  });

  return handleResponse<AuthResponse>(response);
}

/**
 * Logout
 * 登出
 */
export async function logout(token: string): Promise<void> {
  await fetch(`${USER_API_BASE}/logout`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// ==========================================
// Aliyun CAPTCHA Helper
// 阿里云验证码辅助函数
// ==========================================

/**
 * Aliyun CAPTCHA configuration
 * 阿里云验证码配置
 *
 * These values should be set in environment variables
 * 这些值应该在环境变量中设置
 */
export const ALIYUN_CAPTCHA_CONFIG = {
  // China region scene ID (from Aliyun console)
  // 中国区场景ID（从阿里云控制台获取）
  sceneId: import.meta.env.VITE_ALIYUN_CAPTCHA_SCENE_ID || '',

  // China region app key
  // 中国区应用密钥
  appKey: import.meta.env.VITE_ALIYUN_CAPTCHA_APP_KEY || '',

  // China region endpoint
  // 中国区端点
  endpoint: 'https://captcha.aliyuncs.com',
};
