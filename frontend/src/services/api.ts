/**
 * API Service Layer
 * API 服务层
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  DocumentInfo,
  SessionInfo,
  SentenceAnalysis,
  SuggestResponse,
  SessionState,
  ValidationResult,
  RiskLevel,
  SuggestionSource,
  DetailedSentenceAnalysis,
} from '../types';

// Helper function to convert snake_case to camelCase
// 将 snake_case 转换为 camelCase 的辅助函数
const toCamelCase = (str: string): string => {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
};

// Transform object keys from snake_case to camelCase
// 将对象键从 snake_case 转换为 camelCase
const transformKeys = <T>(obj: unknown): T => {
  if (obj === null || obj === undefined) return obj as T;
  if (Array.isArray(obj)) {
    return obj.map((item) => transformKeys(item)) as T;
  }
  if (typeof obj === 'object') {
    const transformed: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      transformed[toCamelCase(key)] = transformKeys(value);
    }
    return transformed as T;
  }
  return obj as T;
};

// Create axios instance
// 创建 axios 实例
const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,  // Increased to 120s for LLM requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// Error handler
// 错误处理
const handleError = (error: AxiosError) => {
  if (error.response) {
    const data = error.response.data as { detail?: string };
    throw new Error(data.detail || 'An error occurred');
  }
  throw error;
};

// Document APIs
// 文档 API
export const documentApi = {
  /**
   * Upload document file
   * 上传文档文件
   */
  upload: async (file: File): Promise<DocumentInfo> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return transformKeys<DocumentInfo>(response.data);
  },

  /**
   * Upload text directly
   * 直接上传文本
   */
  uploadText: async (text: string): Promise<{ id: string; status: string }> => {
    const response = await api.post('/documents/new/text', null, {
      params: { text },
    });
    return transformKeys(response.data);
  },

  /**
   * Get document info
   * 获取文档信息
   */
  get: async (documentId: string): Promise<DocumentInfo> => {
    const response = await api.get(`/documents/${documentId}`);
    return transformKeys<DocumentInfo>(response.data);
  },

  /**
   * Delete document
   * 删除文档
   */
  delete: async (documentId: string): Promise<void> => {
    await api.delete(`/documents/${documentId}`);
  },

  /**
   * List all documents
   * 列出所有文档
   */
  list: async (): Promise<DocumentInfo[]> => {
    const response = await api.get('/documents/');
    return transformKeys<DocumentInfo[]>(response.data);
  },
};

// Analysis APIs
// 分析 API
export const analyzeApi = {
  /**
   * Analyze text
   * 分析文本
   */
  analyzeText: async (
    text: string,
    options?: {
      targetLang?: string;
      includeTurnitin?: boolean;
      includeGptzero?: boolean;
    }
  ): Promise<SentenceAnalysis[]> => {
    const response = await api.post('/analyze', {
      text,
      target_lang: options?.targetLang || 'zh',
      include_turnitin: options?.includeTurnitin ?? true,
      include_gptzero: options?.includeGptzero ?? true,
    });
    return transformKeys<SentenceAnalysis[]>(response.data);
  },

  /**
   * Start document analysis
   * 开始文档分析
   */
  analyzeDocument: async (
    documentId: string,
    options?: {
      includeTurnitin?: boolean;
      includeGptzero?: boolean;
    }
  ): Promise<{ status: string; documentId: string }> => {
    const response = await api.post(`/analyze/document/${documentId}`, null, {
      params: {
        include_turnitin: options?.includeTurnitin ?? true,
        include_gptzero: options?.includeGptzero ?? true,
      },
    });
    return transformKeys(response.data);
  },

  /**
   * Get analysis status
   * 获取分析状态
   */
  getStatus: async (
    analysisId: string
  ): Promise<{ status: string; totalSentences: number; analyzed: number }> => {
    const response = await api.get(`/analyze/${analysisId}/status`);
    return transformKeys(response.data);
  },

  /**
   * Get analysis result
   * 获取分析结果
   */
  getResult: async (analysisId: string): Promise<SentenceAnalysis[]> => {
    const response = await api.get(`/analyze/${analysisId}/result`);
    return transformKeys<SentenceAnalysis[]>(response.data);
  },
};

// Suggestion APIs
// 建议 API
export const suggestApi = {
  /**
   * Get suggestions for a sentence
   * 获取句子的建议
   *
   * CAASS v2.0 Phase 2: Added whitelist and contextBaseline support
   */
  getSuggestions: async (
    sentence: string,
    options: {
      issues?: Array<{ type: string; description: string }>;
      lockedTerms?: string[];
      colloquialismLevel?: number;
      targetLang?: string;
      whitelist?: string[];        // CAASS v2.0 Phase 2: Domain-specific terms to exempt
      contextBaseline?: number;    // CAASS v2.0 Phase 2: Paragraph context baseline
    }
  ): Promise<SuggestResponse> => {
    const response = await api.post('/suggest', {
      sentence,
      issues: options.issues || [],
      locked_terms: options.lockedTerms || [],
      colloquialism_level: options.colloquialismLevel ?? 4,
      target_lang: options.targetLang || 'zh',
      whitelist: options.whitelist || [],
      context_baseline: options.contextBaseline ?? 0,
    });
    return transformKeys<SuggestResponse>(response.data);
  },

  /**
   * Validate custom input
   * 验证自定义输入
   */
  validateCustom: async (
    sessionId: string,
    sentenceId: string,
    customText: string
  ): Promise<ValidationResult> => {
    const response = await api.post('/suggest/custom', {
      session_id: sessionId,
      sentence_id: sentenceId,
      custom_text: customText,
    });
    return transformKeys<ValidationResult>(response.data);
  },

  /**
   * Get writing hints for custom modification
   * 获取自定义修改的写作提示
   */
  getWritingHints: async (sentence: string): Promise<{
    hints: Array<{
      type: string;
      title: string;
      titleZh: string;
      description: string;
      descriptionZh: string;
    }>;
  }> => {
    const response = await api.post('/suggest/hints', null, {
      params: { sentence }
    });
    return transformKeys(response.data);
  },

  /**
   * Get detailed sentence analysis (grammar, clauses, pronouns, AI words, rewrite suggestions)
   * 获取详细句子分析（语法、从句、代词、AI词汇、改写建议）
   */
  analyzeSentence: async (
    sentence: string,
    colloquialismLevel: number = 5
  ): Promise<DetailedSentenceAnalysis> => {
    console.log('[API] analyzeSentence called, sentence length:', sentence.length);
    const response = await api.post('/suggest/analyze', {
      sentence,
      colloquialism_level: colloquialismLevel,
    });
    console.log('[API] analyzeSentence response received');
    return transformKeys<DetailedSentenceAnalysis>(response.data);
  },
};

// Session APIs
// 会话 API
export const sessionApi = {
  /**
   * Start a new session
   * 开始新会话
   */
  start: async (
    documentId: string,
    options: {
      mode?: 'intervention' | 'yolo';
      colloquialismLevel?: number;
      targetLang?: string;
      processLevels?: RiskLevel[];
    }
  ): Promise<SessionState> => {
    const response = await api.post('/session/start', {
      document_id: documentId,
      mode: options.mode || 'intervention',
      colloquialism_level: options.colloquialismLevel ?? 4,
      target_lang: options.targetLang || 'zh',
      process_levels: options.processLevels || ['high', 'medium'],
    });
    return transformKeys<SessionState>(response.data);
  },

  /**
   * Get current session state
   * 获取当前会话状态
   */
  getCurrent: async (sessionId: string): Promise<SessionState> => {
    const response = await api.get(`/session/${sessionId}/current`);
    return transformKeys<SessionState>(response.data);
  },

  /**
   * Move to next sentence
   * 移动到下一句
   */
  next: async (sessionId: string): Promise<SessionState> => {
    const response = await api.post(`/session/${sessionId}/next`);
    return transformKeys<SessionState>(response.data);
  },

  /**
   * Skip current sentence
   * 跳过当前句子
   */
  skip: async (sessionId: string): Promise<SessionState> => {
    const response = await api.post(`/session/${sessionId}/skip`);
    return transformKeys<SessionState>(response.data);
  },

  /**
   * Flag sentence for manual review
   * 标记句子需要人工审核
   */
  flag: async (sessionId: string): Promise<SessionState> => {
    const response = await api.post(`/session/${sessionId}/flag`);
    return transformKeys<SessionState>(response.data);
  },

  /**
   * Get session progress
   * 获取会话进度
   */
  getProgress: async (sessionId: string): Promise<{
    total: number;
    processed: number;
    skipped: number;
    flagged: number;
    currentIndex: number;
    progressPercent: number;
    status: string;
  }> => {
    const response = await api.get(`/session/${sessionId}/progress`);
    return transformKeys(response.data);
  },

  /**
   * Get session configuration including whitelist
   * 获取会话配置，包括白名单
   *
   * CAASS v2.0 Phase 2: Returns whitelist and tone_level for scoring
   */
  getConfig: async (sessionId: string): Promise<{
    sessionId: string;
    whitelist: string[];
    toneLevel: number;
    processLevels: string[];
    colloquialismLevel: number;
    targetLang: string;
  }> => {
    const response = await api.get(`/session/${sessionId}/config`);
    return transformKeys(response.data);
  },

  /**
   * Get review statistics for completed session
   * 获取已完成会话的审核统计数据
   */
  getReviewStats: async (sessionId: string): Promise<{
    totalSentences: number;
    modifiedCount: number;
    avgRiskReduction: number;
    sourceDistribution: { llm: number; rule: number; custom: number };
  }> => {
    const response = await api.get(`/session/${sessionId}/review-stats`);
    return transformKeys(response.data);
  },

  /**
   * Complete session
   * 完成会话
   */
  complete: async (sessionId: string): Promise<{ status: string; sessionId: string }> => {
    const response = await api.post(`/session/${sessionId}/complete`);
    return transformKeys(response.data);
  },

  /**
   * Apply suggestion
   * 应用建议
   */
  applySuggestion: async (
    sessionId: string,
    sentenceId: string,
    source: SuggestionSource,
    modifiedText?: string
  ): Promise<{ status: string }> => {
    const response = await api.post('/suggest/apply', null, {
      params: {
        session_id: sessionId,
        sentence_id: sentenceId,
        source,
        modified_text: modifiedText,
      },
    });
    return transformKeys(response.data);
  },

  /**
   * List all sessions
   * 列出所有会话
   */
  list: async (): Promise<SessionInfo[]> => {
    const response = await api.get('/session/list');
    return transformKeys<SessionInfo[]>(response.data);
  },

  /**
   * Get all sentences for a session
   * 获取会话的所有句子
   */
  getSentences: async (sessionId: string): Promise<SentenceAnalysis[]> => {
    const response = await api.get(`/session/${sessionId}/sentences`);
    return transformKeys<SentenceAnalysis[]>(response.data);
  },

  /**
   * Jump to a specific sentence
   * 跳转到特定句子
   */
  gotoSentence: async (sessionId: string, index: number): Promise<SessionState> => {
    const response = await api.post(`/session/${sessionId}/goto/${index}`);
    return transformKeys<SessionState>(response.data);
  },
};

// Export APIs
// 导出 API
export const exportApi = {
  /**
   * Export document
   * 导出文档
   */
  exportDocument: async (
    sessionId: string,
    format: string = 'txt'
  ): Promise<{ filename: string; format: string; size: number; downloadUrl: string }> => {
    const response = await api.post('/export/document', null, {
      params: { session_id: sessionId, format },
    });
    return transformKeys(response.data);
  },

  /**
   * Export report
   * 导出报告
   */
  exportReport: async (
    sessionId: string,
    format: string = 'json'
  ): Promise<{ filename: string; format: string; size: number; downloadUrl: string }> => {
    const response = await api.post('/export/report', null, {
      params: { session_id: sessionId, format },
    });
    return transformKeys(response.data);
  },

  /**
   * Download file
   * 下载文件
   */
  download: (filename: string): string => {
    return `/api/v1/export/download/${filename}`;
  },
};

// Add error interceptor
// 添加错误拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => handleError(error)
);

export default api;
