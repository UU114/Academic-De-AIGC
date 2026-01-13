/// <reference types="vite/client" />

/**
 * Vite Environment Variables Type Definitions
 * Vite 环境变量类型定义
 */
interface ImportMetaEnv {
  // Aliyun CAPTCHA Configuration
  // 阿里云验证码配置
  readonly VITE_ALIYUN_CAPTCHA_SCENE_ID: string;
  readonly VITE_ALIYUN_CAPTCHA_APP_KEY: string;

  // Debug mode
  // 调试模式
  readonly VITE_DEBUG_MODE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
