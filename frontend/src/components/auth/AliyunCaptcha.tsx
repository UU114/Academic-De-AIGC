/**
 * Aliyun CAPTCHA Component
 * 阿里云验证码组件
 *
 * Integrates Aliyun's behavioral CAPTCHA (slider/click verification)
 * 集成阿里云行为验证码（滑块/点选验证）
 *
 * @see https://help.aliyun.com/document_detail/193141.html
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { Loader2, ShieldCheck, ShieldAlert } from 'lucide-react';
import type { CaptchaVerifyParam } from '../../services/userApi';

// ==========================================
// Types
// 类型定义
// ==========================================

interface AliyunCaptchaProps {
  /**
   * Scene ID from Aliyun console
   * 阿里云控制台的场景ID
   */
  sceneId: string;

  /**
   * App Key from Aliyun console (China region)
   * 阿里云控制台的AppKey（中国区）
   */
  appKey: string;

  /**
   * Callback when verification succeeds
   * 验证成功回调
   */
  onSuccess: (param: CaptchaVerifyParam) => void;

  /**
   * Callback when verification fails
   * 验证失败回调
   */
  onFail?: (error: string) => void;

  /**
   * Button text
   * 按钮文字
   */
  buttonText?: string;

  /**
   * Whether the button is disabled
   * 按钮是否禁用
   */
  disabled?: boolean;

  /**
   * Additional CSS class
   * 额外的CSS类
   */
  className?: string;
}

// Aliyun CAPTCHA SDK types
declare global {
  interface Window {
    ALIYUN_CAPTCHA_LOADED?: boolean;
    initAliyunCaptcha: (config: {
      SceneId: string;
      prefix: string;
      mode: string;
      element: string;
      button: string;
      captchaVerifyCallback: (param: string) => Promise<{ captchaResult: boolean; bizResult: boolean }>;
      onBizResultCallback: (result: boolean) => void;
      getInstance: (instance: unknown) => void;
      slideStyle?: {
        width: number;
        height: number;
      };
      language?: string;
    }) => void;
  }
}

// ==========================================
// Component
// 组件
// ==========================================

export default function AliyunCaptcha({
  sceneId,
  appKey,
  onSuccess,
  onFail,
  buttonText = '点击进行安全验证',
  disabled = false,
  className = '',
}: AliyunCaptchaProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const captchaInstance = useRef<unknown>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isVerified, setIsVerified] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const verifyParamRef = useRef<string | null>(null);

  /**
   * Load Aliyun CAPTCHA SDK script
   * 加载阿里云验证码SDK脚本
   */
  const loadCaptchaScript = useCallback(() => {
    return new Promise<void>((resolve, reject) => {
      // Check if already loaded
      if (window.ALIYUN_CAPTCHA_LOADED) {
        resolve();
        return;
      }

      // Check if script is already in DOM
      const existingScript = document.querySelector('script[src*="aliyuncs.com/captcha"]');
      if (existingScript) {
        existingScript.addEventListener('load', () => {
          window.ALIYUN_CAPTCHA_LOADED = true;
          resolve();
        });
        return;
      }

      // Create and load script
      const script = document.createElement('script');
      script.src = 'https://o.alicdn.com/captcha-frontend/aliyunCaptcha/AliyunCaptcha.js';
      script.async = true;

      script.onload = () => {
        window.ALIYUN_CAPTCHA_LOADED = true;
        resolve();
      };

      script.onerror = () => {
        reject(new Error('Failed to load Aliyun CAPTCHA SDK'));
      };

      document.head.appendChild(script);
    });
  }, []);

  /**
   * Initialize CAPTCHA instance
   * 初始化验证码实例
   */
  const initCaptcha = useCallback(async () => {
    if (!containerRef.current || !buttonRef.current) return;
    if (!sceneId || !appKey) {
      setError('验证码配置缺失');
      setIsLoading(false);
      return;
    }

    try {
      await loadCaptchaScript();

      // Generate unique IDs for elements
      const containerId = `captcha-container-${Date.now()}`;
      const buttonId = `captcha-button-${Date.now()}`;

      containerRef.current.id = containerId;
      buttonRef.current.id = buttonId;

      window.initAliyunCaptcha({
        SceneId: sceneId,
        prefix: appKey,
        mode: 'popup',  // Popup mode for better UX
        element: `#${containerId}`,
        button: `#${buttonId}`,
        captchaVerifyCallback: async (captchaVerifyParam: string) => {
          // Store the verification parameter
          verifyParamRef.current = captchaVerifyParam;

          // Return success to close the CAPTCHA popup
          // Actual verification happens on the server
          return {
            captchaResult: true,
            bizResult: true,
          };
        },
        onBizResultCallback: (result: boolean) => {
          if (result && verifyParamRef.current) {
            setIsVerified(true);
            setError(null);
            onSuccess({
              captchaVerifyParam: verifyParamRef.current,
            });
          } else {
            setError('验证失败，请重试');
            onFail?.('Verification failed');
          }
        },
        getInstance: (instance: unknown) => {
          captchaInstance.current = instance;
        },
        slideStyle: {
          width: 360,
          height: 40,
        },
        language: 'cn',
      });

      setIsLoading(false);
    } catch (err) {
      setError((err as Error).message || '加载验证码失败');
      setIsLoading(false);
      onFail?.((err as Error).message);
    }
  }, [sceneId, appKey, onSuccess, onFail, loadCaptchaScript]);

  /**
   * Reset CAPTCHA state
   * 重置验证码状态
   */
  const reset = useCallback(() => {
    setIsVerified(false);
    verifyParamRef.current = null;
    // Re-initialize if needed
  }, []);

  // Initialize on mount
  useEffect(() => {
    initCaptcha();

    return () => {
      // Cleanup
      captchaInstance.current = null;
    };
  }, [initCaptcha]);

  // Expose reset method
  useEffect(() => {
    if (containerRef.current) {
      (containerRef.current as HTMLDivElement & { reset?: () => void }).reset = reset;
    }
  }, [reset]);

  return (
    <div className={`aliyun-captcha-wrapper ${className}`}>
      {/* CAPTCHA Container */}
      <div ref={containerRef} className="captcha-container" />

      {/* Trigger Button */}
      <button
        ref={buttonRef}
        type="button"
        disabled={disabled || isLoading || isVerified}
        className={`
          w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg
          font-medium transition-all duration-200
          ${isVerified
            ? 'bg-green-100 text-green-700 border border-green-300 cursor-default'
            : isLoading
              ? 'bg-gray-100 text-gray-400 cursor-wait'
              : error
                ? 'bg-red-50 text-red-600 border border-red-300 hover:bg-red-100'
                : 'bg-blue-50 text-blue-600 border border-blue-300 hover:bg-blue-100'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>加载验证码...</span>
          </>
        ) : isVerified ? (
          <>
            <ShieldCheck className="w-5 h-5" />
            <span>验证通过</span>
          </>
        ) : error ? (
          <>
            <ShieldAlert className="w-5 h-5" />
            <span>{error}</span>
          </>
        ) : (
          <>
            <ShieldCheck className="w-5 h-5" />
            <span>{buttonText}</span>
          </>
        )}
      </button>

      {/* Help text */}
      {!isVerified && !isLoading && !error && (
        <p className="text-xs text-gray-500 mt-2 text-center">
          点击按钮完成人机验证
        </p>
      )}
    </div>
  );
}

// ==========================================
// Hook for CAPTCHA state management
// 验证码状态管理 Hook
// ==========================================

export interface UseCaptchaReturn {
  isVerified: boolean;
  captchaParam: CaptchaVerifyParam | null;
  onCaptchaSuccess: (param: CaptchaVerifyParam) => void;
  onCaptchaFail: (error: string) => void;
  reset: () => void;
}

export function useCaptcha(): UseCaptchaReturn {
  const [isVerified, setIsVerified] = useState(false);
  const [captchaParam, setCaptchaParam] = useState<CaptchaVerifyParam | null>(null);

  const onCaptchaSuccess = useCallback((param: CaptchaVerifyParam) => {
    setIsVerified(true);
    setCaptchaParam(param);
  }, []);

  const onCaptchaFail = useCallback((error: string) => {
    setIsVerified(false);
    setCaptchaParam(null);
    console.error('CAPTCHA failed:', error);
  }, []);

  const reset = useCallback(() => {
    setIsVerified(false);
    setCaptchaParam(null);
  }, []);

  return {
    isVerified,
    captchaParam,
    onCaptchaSuccess,
    onCaptchaFail,
    reset,
  };
}
