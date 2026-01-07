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
  TransitionAnalysisResponse,
  DocumentTransitionSummary,
  TransitionStrategy,
  StructureAnalysisResponse,
  StructureStrategy,
  StructureOption,
  LogicDiagnosisResponse,
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
  timeout: 300000,  // Increased to 300s (5min) for LLM structure analysis
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
   *
   * Note: Text is sent in request body to avoid URL length limits (431 error)
   * 注意：文本通过请求体发送以避免URL长度限制（431错误）
   */
  uploadText: async (text: string): Promise<{ id: string; status: string }> => {
    const response = await api.post('/documents/new/text', { text });
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
   *
   * Note: Sentence is sent in request body to avoid URL length limits (431 error)
   * 注意：句子通过请求体发送以避免URL长度限制（431错误）
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
    const response = await api.post('/suggest/hints', { sentence });
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
   *
   * Note: Parameters are sent in request body to avoid URL length limits (431 error)
   * 注意：参数通过请求体发送以避免URL长度限制（431错误）
   */
  applySuggestion: async (
    sessionId: string,
    sentenceId: string,
    source: SuggestionSource,
    modifiedText?: string
  ): Promise<{ status: string }> => {
    const response = await api.post('/suggest/apply', {
      session_id: sessionId,
      sentence_id: sentenceId,
      source,
      modified_text: modifiedText,
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

  /**
   * Update session current step
   * 更新会话当前步骤
   */
  updateStep: async (sessionId: string, step: string): Promise<{ sessionId: string; currentStep: string }> => {
    const response = await api.post(`/session/${sessionId}/step/${step}`);
    return transformKeys<{ sessionId: string; currentStep: string }>(response.data);
  },

  /**
   * YOLO auto-process all sentences
   * YOLO 自动处理所有句子
   *
   * This method calls LLM for each sentence and applies the best suggestion automatically.
   * 此方法为每个句子调用 LLM 并自动应用最佳建议。
   */
  yoloProcess: async (sessionId: string): Promise<{
    status: string;
    sessionId: string;
    totalSentences: number;
    processed: number;
    skipped: number;
    avgRiskReduction: number;
    logs: Array<{
      index: number;
      action: string;
      message: string;
      originalRisk: number;
      newRisk: number;
      source?: string;
    }>;
  }> => {
    const response = await api.post(`/session/${sessionId}/yolo-process`, null, {
      timeout: 600000,  // 10 minutes timeout for processing many sentences
    });
    return transformKeys(response.data);
  },

  /**
   * YOLO Full Auto Process: Process all levels automatically from Step 1-1 to Step 3
   * YOLO 全自动处理：从 Step 1-1 到 Step 3 自动处理所有层级
   *
   * This method automatically:
   * 1. Step 1-1: Analyze structure → Auto-select all issues → AI modify
   * 2. Step 1-2: Analyze paragraphs → Auto-select all issues → AI modify
   * 3. Step 2: Analyze transitions → Auto-select all issues → AI modify
   * 4. Step 3: Process all medium/high risk sentences
   */
  yoloFullAuto: async (sessionId: string): Promise<{
    status: string;
    sessionId: string;
    finalDocumentId: string;
    logs: Array<{
      step: string;
      action: string;
      message: string;
      issuesCount?: number;
      changesCount?: number;
      processed?: number;
      skipped?: number;
      avgRiskReduction?: number;
    }>;
  }> => {
    const response = await api.post(`/session/${sessionId}/yolo-full-auto`, null, {
      timeout: 900000,  // 15 minutes timeout for full automation processing
    });
    return transformKeys(response.data);
  },
};

// Transition APIs (Phase 3: Level 2 De-AIGC)
// 衔接 API（第三阶段：Level 2 De-AIGC）
export const transitionApi = {
  /**
   * Analyze transition between two paragraphs
   * 分析两个段落之间的衔接
   */
  analyze: async (
    paraA: string,
    paraB: string,
    contextHint?: string
  ): Promise<TransitionAnalysisResponse> => {
    const response = await api.post('/transition/', {
      para_a: paraA,
      para_b: paraB,
      context_hint: contextHint,
    });
    return transformKeys<TransitionAnalysisResponse>(response.data);
  },

  /**
   * Analyze transition and get repair suggestions
   * 分析衔接并获取修复建议
   */
  analyzeWithSuggestions: async (
    paraA: string,
    paraB: string,
    contextHint?: string
  ): Promise<TransitionAnalysisResponse> => {
    const response = await api.post('/transition/with-suggestions', {
      para_a: paraA,
      para_b: paraB,
      context_hint: contextHint,
    });
    return transformKeys<TransitionAnalysisResponse>(response.data);
  },

  /**
   * Get suggestion for a specific strategy
   * 获取特定策略的建议
   */
  getSuggestion: async (
    strategy: TransitionStrategy,
    paraA: string,
    paraB: string,
    contextHint?: string
  ): Promise<TransitionAnalysisResponse['options'][0]> => {
    const response = await api.post(`/transition/suggest/${strategy}`, {
      para_a: paraA,
      para_b: paraB,
      context_hint: contextHint,
    });
    return transformKeys(response.data);
  },

  /**
   * Get available transition strategies
   * 获取可用的衔接策略
   */
  getStrategies: async (): Promise<{
    strategies: Array<{
      id: string;
      name: string;
      nameZh: string;
      description: string;
      descriptionZh: string;
    }>;
  }> => {
    const response = await api.get('/transition/strategies');
    return transformKeys(response.data);
  },

  /**
   * Analyze all transitions in a document
   * 分析文档中所有衔接
   */
  analyzeDocument: async (
    documentId: string,
    contextHint?: string
  ): Promise<DocumentTransitionSummary> => {
    const response = await api.post('/transition/document', {
      document_id: documentId,
      context_hint: contextHint,
    });
    return transformKeys<DocumentTransitionSummary>(response.data);
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

// Structure APIs (Phase 4: Level 1 De-AIGC)
// 结构 API（第4阶段：Level 1 De-AIGC）
export const structureApi = {
  /**
   * Analyze document structure
   * 分析文档结构
   */
  analyze: async (
    text: string,
    extractThesis: boolean = true
  ): Promise<StructureAnalysisResponse> => {
    const response = await api.post('/structure/', {
      text,
      extract_thesis: extractThesis,
    });
    return transformKeys<StructureAnalysisResponse>(response.data);
  },

  /**
   * Analyze structure with suggestions
   * 分析结构并获取建议
   */
  analyzeWithSuggestions: async (
    text: string,
    extractThesis: boolean = true
  ): Promise<StructureAnalysisResponse> => {
    const response = await api.post('/structure/with-suggestions', {
      text,
      extract_thesis: extractThesis,
    });
    return transformKeys<StructureAnalysisResponse>(response.data);
  },

  /**
   * Get suggestion for a specific strategy
   * 获取特定策略的建议
   */
  getSuggestion: async (
    strategy: StructureStrategy,
    text: string,
    extractThesis: boolean = true
  ): Promise<StructureOption> => {
    const response = await api.post(`/structure/suggest/${strategy}`, {
      text,
      extract_thesis: extractThesis,
    });
    return transformKeys<StructureOption>(response.data);
  },

  /**
   * Get logic diagnosis card
   * 获取逻辑诊断卡
   */
  getDiagnosis: async (
    text: string,
    extractThesis: boolean = true
  ): Promise<LogicDiagnosisResponse> => {
    const response = await api.post('/structure/diagnosis', {
      text,
      extract_thesis: extractThesis,
    });
    return transformKeys<LogicDiagnosisResponse>(response.data);
  },

  /**
   * Analyze document structure by ID (legacy combined analysis)
   * 按ID分析文档结构（遗留的组合分析）
   */
  analyzeDocument: async (
    documentId: string,
    extractThesis: boolean = true
  ): Promise<StructureAnalysisResponse> => {
    const response = await api.post('/structure/document', {
      document_id: documentId,
      extract_thesis: extractThesis,
    });
    return transformKeys<StructureAnalysisResponse>(response.data);
  },

  /**
   * Step 1-1: Analyze document STRUCTURE only (global patterns)
   * 步骤 1-1：仅分析文档结构（全局模式）
   *
   * Returns: sections, paragraphs, structure_score, structure_issues, style_analysis
   */
  analyzeStep1_1: async (
    documentId: string,
    sessionId?: string
  ): Promise<{
    sections: Array<{
      number: string;
      title: string;
      paragraphs: Array<{
        position: string;
        summary: string;
        summaryZh: string;
        firstSentence: string;
        lastSentence: string;
        wordCount: number;
      }>;
    }>;
    totalParagraphs: number;
    totalSections: number;
    structureScore: number;
    riskLevel: string;
    structureIssues: Array<{
      type: string;
      description: string;
      descriptionZh: string;
      severity: string;
      affectedPositions: string[];
    }>;
    scoreBreakdown: Record<string, number>;
    recommendationZh: string;
    // Style analysis fields (for colloquialism level support)
    // 风格分析字段（用于支持口语化级别）
    styleAnalysis?: {
      detectedStyle: number;
      styleName: string;
      styleNameZh: string;
      styleIndicators: string[];
      styleIndicatorsZh: string[];
      mismatchWarning?: string;
      mismatchWarningZh?: string;
      targetColloquialism?: number;
      styleMismatchLevel?: number;
    };
  }> => {
    const response = await api.post('/structure/document/step1-1', {
      document_id: documentId,
      session_id: sessionId,
    });
    return transformKeys(response.data);
  },

  /**
   * Step 1-2: Analyze paragraph RELATIONSHIPS (connections, transitions)
   * 步骤 1-2：分析段落关系（连接、过渡）
   *
   * Requires Step 1-1 to be completed first.
   * Returns: explicit_connectors, logic_breaks, paragraph_risks, relationship_score
   */
  analyzeStep1_2: async (
    documentId: string
  ): Promise<{
    explicitConnectors: Array<{
      word: string;
      position: string;
      location: string;
      severity: string;
    }>;
    logicBreaks: Array<{
      fromPosition: string;
      toPosition: string;
      transitionType: string;
      issue: string;
      issueZh: string;
      suggestion: string;
      suggestionZh: string;
    }>;
    paragraphRisks: Array<{
      position: string;
      aiRisk: string;
      aiRiskReason: string;
      openingConnector: string | null;
      rewriteSuggestionZh: string;
    }>;
    relationshipScore: number;
    relationshipIssues: Array<{
      type: string;
      description: string;
      descriptionZh: string;
      severity: string;
      affectedPositions: string[];
    }>;
    scoreBreakdown: Record<string, number>;
  }> => {
    const response = await api.post('/structure/document/step1-2', {
      document_id: documentId,
    });
    return transformKeys(response.data);
  },

  /**
   * Clear analysis cache for a document
   * 清除文档的分析缓存
   */
  clearCache: async (documentId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/structure/document/${documentId}/cache`);
    return response.data;
  },

  /**
   * Get available structure strategies
   * 获取可用的结构策略
   */
  getStrategies: async (): Promise<{
    strategies: Array<{
      id: string;
      name: string;
      nameZh: string;
      description: string;
      descriptionZh: string;
    }>;
  }> => {
    const response = await api.get('/structure/strategies');
    return transformKeys(response.data);
  },

  /**
   * Get rewrite suggestion for a single paragraph
   * 获取单个段落的改写建议
   */
  getParagraphSuggestion: async (
    paragraphText: string,
    paragraphPosition: string,
    options?: {
      aiRisk?: string;
      aiRiskReason?: string;
      contextHint?: string;
    }
  ): Promise<{
    paragraphPosition: string;
    rewriteSuggestionZh: string;
    rewriteExample?: string;  // English example
    aiRisk: string;
    aiRiskReason: string;  // Chinese reason
  }> => {
    const response = await api.post('/structure/paragraph-suggestion', {
      paragraph_text: paragraphText,
      paragraph_position: paragraphPosition,
      ai_risk: options?.aiRisk,
      ai_risk_reason: options?.aiRiskReason,
      context_hint: options?.contextHint,
    });
    return transformKeys(response.data);
  },

  /**
   * Get 7-indicator structural risk card
   * 获取7指征结构风险卡片
   *
   * Returns a visual risk card showing:
   * - 7 AI structural indicators with emoji and color
   * - Whether each indicator is triggered
   * - Overall risk level and summary
   */
  getRiskCard: async (text: string): Promise<{
    indicators: Array<{
      id: string;
      name: string;
      nameZh: string;
      triggered: boolean;
      riskLevel: number;
      emoji: string;
      color: string;
      description: string;
      descriptionZh: string;
      details: string;
      detailsZh: string;
    }>;
    triggeredCount: number;
    overallRisk: string;
    overallRiskZh: string;
    summary: string;
    summaryZh: string;
    totalScore: number;
  }> => {
    const response = await api.post('/structure/risk-card', { text });
    return transformKeys(response.data);
  },

  /**
   * Get detailed suggestion for a specific structure issue
   * 获取针对特定结构问题的详细建议
   *
   * Uses LLM with comprehensive De-AIGC knowledge to generate:
   * - Detailed diagnosis of the issue
   * - Multiple modification strategies
   * - A complete modification prompt for other AI tools
   */
  getIssueSuggestion: async (
    documentId: string,
    issue: {
      type: string;
      description: string;
      descriptionZh: string;
      severity: string;
      affectedPositions?: string[];
    },
    quickMode: boolean = false
  ): Promise<{
    diagnosisZh: string;
    strategies: Array<{
      name_zh: string;
      description_zh: string;
      example_before?: string;
      example_after?: string;
      difficulty: string;
      effectiveness: string;
    }>;
    modificationPrompt: string;
    priorityTipsZh: string;
    cautionZh: string;
    quickFixZh?: string;
    estimatedImprovement?: number;
  }> => {
    const response = await api.post('/structure/issue-suggestion', {
      documentId,
      issueType: issue.type,
      issueDescription: issue.description,
      issueDescriptionZh: issue.descriptionZh,
      severity: issue.severity,
      affectedPositions: issue.affectedPositions || [],
      quickMode,
    });
    return transformKeys(response.data);
  },

  /**
   * Generate merge modification prompt for selected issues
   * 为选定的问题生成合并修改提示词
   *
   * User can copy this prompt to use with other AI tools.
   */
  mergeModifyPrompt: async (
    documentId: string,
    selectedIssues: Array<{
      type: string;
      description: string;
      descriptionZh: string;
      severity: string;
      affectedPositions?: string[];
    }>,
    options?: {
      sessionId?: string;
      userNotes?: string;
    }
  ): Promise<{
    prompt: string;
    promptZh: string;
    issuesSummaryZh: string;
    colloquialismLevel?: number;
    estimatedChanges: number;
  }> => {
    const response = await api.post('/structure/merge-modify/prompt', {
      documentId,
      sessionId: options?.sessionId,
      selectedIssues: selectedIssues.map(issue => ({
        type: issue.type,
        description: issue.description,
        descriptionZh: issue.descriptionZh,
        severity: issue.severity,
        affectedPositions: issue.affectedPositions || [],
      })),
      userNotes: options?.userNotes,
      mode: 'prompt',
    });
    return transformKeys(response.data);
  },

  /**
   * Apply AI modification directly to document
   * 直接将AI修改应用到文档
   *
   * Returns modified text, limited to 3 regeneration attempts.
   */
  mergeModifyApply: async (
    documentId: string,
    selectedIssues: Array<{
      type: string;
      description: string;
      descriptionZh: string;
      severity: string;
      affectedPositions?: string[];
    }>,
    options?: {
      sessionId?: string;
      userNotes?: string;
    }
  ): Promise<{
    modifiedText: string;
    changesSummaryZh: string;
    changesCount: number;
    issuesAddressed: string[];
    remainingAttempts: number;
    colloquialismLevel?: number;
  }> => {
    const response = await api.post('/structure/merge-modify/apply', {
      documentId,
      sessionId: options?.sessionId,
      selectedIssues: selectedIssues.map(issue => ({
        type: issue.type,
        description: issue.description,
        descriptionZh: issue.descriptionZh,
        severity: issue.severity,
        affectedPositions: issue.affectedPositions || [],
      })),
      userNotes: options?.userNotes,
      mode: 'apply',
    });
    return transformKeys(response.data);
  },

  /**
   * Phase 1: Analyze paragraph length distribution
   * 第一阶段：分析段落长度分布
   */
  analyzeParagraphLength: async (
    documentId: string
  ): Promise<{
    paragraphLengths: Array<{
      position: string;
      wordCount: number;
      section: string;
      summary: string;
      summaryZh: string;
    }>;
    meanLength: number;
    stdDev: number;
    cv: number;
    isUniform: boolean;
    humanLikeCvTarget: number;
    strategies: Array<{
      strategyType: string;
      targetPositions: string[];
      description: string;
      descriptionZh: string;
      reason: string;
      reasonZh: string;
      priority: number;
      expandSuggestion?: string;
      expandSuggestionZh?: string;
    }>;
    summary: string;
    summaryZh: string;
  }> => {
    const response = await api.post('/structure/paragraph-length/analyze', {
      documentId,
    });
    return transformKeys(response.data);
  },

  /**
   * Phase 2: Apply selected paragraph length strategies
   * 第二阶段：应用选中的段落长度策略
   */
  applyParagraphStrategies: async (
    documentId: string,
    selectedStrategies: Array<{
      strategyType: string;
      targetPositions: string[];
      expandText?: string;
    }>,
    options?: {
      sessionId?: string;
    }
  ): Promise<{
    modifiedText: string;
    changesSummaryZh: string;
    strategiesApplied: number;
    newCv?: number;
  }> => {
    const response = await api.post('/structure/paragraph-length/apply', {
      documentId,
      sessionId: options?.sessionId,
      selectedStrategies: selectedStrategies.map(s => ({
        strategyType: s.strategyType,
        targetPositions: s.targetPositions,
        expandText: s.expandText,
      })),
    });
    return transformKeys(response.data);
  },
};

// Flow APIs (Phase 5: Full Flow Integration)
// 流程 API（第5阶段：全流程整合）
export const flowApi = {
  /**
   * Start a new processing flow
   * 开始新的处理流程
   */
  start: async (
    documentId: string,
    options?: {
      mode?: 'quick' | 'deep';
      colloquialismLevel?: number;
      whitelist?: string[];
    }
  ): Promise<{
    flowId: string;
    sessionId: string;
    mode: string;
    currentLevel: string;
    levels: Array<{ level: string; nameEn: string; nameZh: string; status: string }>;
  }> => {
    const response = await api.post('/flow/start', {
      document_id: documentId,
      mode: options?.mode || 'deep',
      colloquialism_level: options?.colloquialismLevel ?? 4,
      whitelist: options?.whitelist || [],
    });
    return transformKeys(response.data);
  },

  /**
   * Get flow progress
   * 获取流程进度
   */
  getProgress: async (flowId: string): Promise<{
    flowId: string;
    mode: string;
    currentLevel: string;
    overallStatus: string;
    levels: Array<{
      level: string;
      nameEn: string;
      nameZh: string;
      status: string;
      scoreBefore?: number;
      scoreAfter?: number;
      issuesFound?: number;
      issuesFixed?: number;
    }>;
    summary: {
      totalIssuesFound: number;
      totalIssuesFixed: number;
      totalScoreReduction: number;
      completedLevels: number;
      skippedLevels: number;
    };
  }> => {
    const response = await api.get(`/flow/${flowId}/progress`);
    return transformKeys(response.data);
  },

  /**
   * Complete a level
   * 完成层级
   */
  completeLevel: async (
    flowId: string,
    level: string,
    result: {
      scoreBefore: number;
      scoreAfter: number;
      issuesFound: number;
      issuesFixed: number;
      changes?: Array<{ type: string; description: string }>;
      updatedText?: string;
    }
  ): Promise<{
    flowId: string;
    completedLevel: string;
    nextLevel: string | null;
    progress: Record<string, unknown>;
  }> => {
    const response = await api.post(`/flow/${flowId}/complete-level`, {
      flow_id: flowId,
      level,
      score_before: result.scoreBefore,
      score_after: result.scoreAfter,
      issues_found: result.issuesFound,
      issues_fixed: result.issuesFixed,
      changes: result.changes || [],
      updated_text: result.updatedText,
    });
    return transformKeys(response.data);
  },

  /**
   * Skip a level
   * 跳过层级
   */
  skipLevel: async (
    flowId: string,
    level: string
  ): Promise<{
    flowId: string;
    skippedLevel: string;
    nextLevel: string | null;
    progress: Record<string, unknown>;
  }> => {
    const response = await api.post(`/flow/${flowId}/skip-level`, null, {
      params: { level },
    });
    return transformKeys(response.data);
  },

  /**
   * Get context for a level
   * 获取层级上下文
   */
  getLevelContext: async (
    flowId: string,
    level: string
  ): Promise<{
    flowId: string;
    level: string;
    context: Record<string, unknown>;
  }> => {
    const response = await api.get(`/flow/${flowId}/context/${level}`);
    return transformKeys(response.data);
  },

  /**
   * Update flow context
   * 更新流程上下文
   */
  updateContext: async (
    flowId: string,
    updates: Record<string, unknown>
  ): Promise<{
    flowId: string;
    status: string;
    updatedFields: string[];
  }> => {
    const response = await api.post(`/flow/${flowId}/update-context`, updates);
    return transformKeys(response.data);
  },

  /**
   * Get current text
   * 获取当前文本
   */
  getCurrentText: async (flowId: string): Promise<{
    flowId: string;
    currentLevel: string;
    text: string;
    paragraphCount: number;
  }> => {
    const response = await api.get(`/flow/${flowId}/current-text`);
    return transformKeys(response.data);
  },

  /**
   * Cancel flow
   * 取消流程
   */
  cancel: async (flowId: string): Promise<{ status: string; flowId: string }> => {
    const response = await api.delete(`/flow/${flowId}`);
    return transformKeys(response.data);
  },
};

// Paragraph Logic APIs (Level 3 Enhancement: Intra-paragraph Logic)
// 段落逻辑 API（Level 3 增强：段落内逻辑）
export const paragraphApi = {
  /**
   * Get available strategies
   * 获取可用策略
   */
  getStrategies: async (): Promise<{
    strategies: Array<{
      key: string;
      name: string;
      nameZh: string;
      description: string;
      descriptionZh: string;
    }>;
  }> => {
    const response = await api.get('/paragraph/strategies');
    return transformKeys(response.data);
  },

  /**
   * Analyze paragraph logic
   * 分析段落逻辑
   */
  analyze: async (
    paragraph: string,
    toneLevel: number = 4
  ): Promise<{
    issues: Array<{
      type: string;
      description: string;
      descriptionZh: string;
      severity: string;
      position: number[];
      suggestion: string;
      suggestionZh: string;
      details?: Record<string, unknown>;
    }>;
    hasSubjectRepetition: boolean;
    hasUniformLength: boolean;
    hasLinearStructure: boolean;
    hasFirstPersonOveruse: boolean;
    subjectDiversityScore: number;
    lengthVariationCv: number;
    logicStructure: string;
    firstPersonRatio: number;
    connectorDensity: number;
    paragraphRiskAdjustment: number;
    sentenceCount: number;
    sentences: string[];
  }> => {
    const response = await api.post('/paragraph/analyze', {
      paragraph,
      tone_level: toneLevel,
    });
    return transformKeys(response.data);
  },

  /**
   * Restructure paragraph
   * 重组段落
   */
  restructure: async (
    paragraph: string,
    strategy: 'ani' | 'subject_diversity' | 'implicit_connector' | 'rhythm' | 'all',
    toneLevel: number = 4,
    options?: {
      detectedIssues?: Array<{
        type: string;
        description: string;
        severity: string;
      }>;
      repeatedSubject?: string;
      subjectCount?: number;
      connectorsFound?: Array<{
        index: number;
        connector: string;
        category: string;
      }>;
      lengths?: number[];
      cv?: number;
    }
  ): Promise<{
    original: string;
    restructured: string;
    strategy: string;
    strategyName: string;
    strategyNameZh: string;
    changes: Array<{
      type: string;
      description: string;
      original?: string;
      result?: string;
    }>;
    explanation: string;
    explanationZh: string;
    originalRiskAdjustment: number;
    newRiskAdjustment: number;
    improvement: number;
  }> => {
    const response = await api.post('/paragraph/restructure', {
      paragraph,
      strategy,
      tone_level: toneLevel,
      detected_issues: options?.detectedIssues,
      repeated_subject: options?.repeatedSubject,
      subject_count: options?.subjectCount,
      connectors_found: options?.connectorsFound,
      lengths: options?.lengths,
      cv: options?.cv,
    });
    return transformKeys(response.data);
  },

  /**
   * Analyze paragraph logic framework (Step 2 Enhancement)
   * 分析段落逻辑框架（Step 2 增强）
   *
   * Provides:
   * - Sentence role analysis (论点/证据/分析/批判/让步/综合等)
   * - Logic framework pattern detection (linear/dynamic)
   * - Burstiness analysis (sentence length variation)
   * - Missing element identification
   * - Improvement suggestions
   */
  analyzeLogicFramework: async (
    paragraph: string,
    paragraphPosition?: string
  ): Promise<{
    sentenceRoles: Array<{
      index: number;
      role: string;
      roleZh: string;
      confidence: number;
      brief: string;
    }>;
    roleDistribution: Record<string, number>;
    logicFramework: {
      pattern: string;
      patternZh: string;
      isAiLike: boolean;
      riskLevel: string;
      description: string;
      descriptionZh: string;
    };
    burstinessAnalysis: {
      sentenceLengths: number[];
      meanLength: number;
      stdDev: number;
      cv: number;
      burstinessLevel: string;
      burstinessZh: string;
      hasDramaticVariation: boolean;
      longestSentence: { index: number; length: number };
      shortestSentence: { index: number; length: number };
    };
    missingElements: {
      roles: string[];
      description: string;
      descriptionZh: string;
    };
    improvementSuggestions: Array<{
      type: string;
      suggestion: string;
      suggestionZh: string;
      priority: number;
      example?: string;
    }>;
    overallAssessment: {
      aiRiskScore: number;
      mainIssues: string[];
      summary: string;
      summaryZh: string;
    };
    basicAnalysis: Record<string, unknown>;
    sentences: string[];
  }> => {
    const response = await api.post('/paragraph/analyze-logic-framework', {
      paragraph,
      paragraphPosition,
    });
    return transformKeys(response.data);
  },
};

// Structure Guidance APIs (Level 1 Guided Interaction)
// 结构指引 API（Level 1 指引式交互）
export const structureGuidanceApi = {
  /**
   * Get categorized structure issues for a document
   * 获取文档的分类结构问题
   */
  getIssues: async (
    documentId: string,
    includeLowSeverity: boolean = false
  ): Promise<{
    structureIssues: Array<{
      id: string;
      type: string;
      category: string;
      severity: string;
      titleZh: string;
      titleEn: string;
      briefZh: string;
      briefEn?: string;
      affectedPositions: string[];
      affectedTextPreview: string;
      canGenerateReference: boolean;
      status: string;
      connectorWord?: string;
      wordCount?: number;
      neighborAvg?: number;
    }>;
    transitionIssues: Array<{
      id: string;
      type: string;
      category: string;
      severity: string;
      titleZh: string;
      titleEn: string;
      briefZh: string;
      briefEn?: string;
      affectedPositions: string[];
      affectedTextPreview: string;
      canGenerateReference: boolean;
      status: string;
      connectorWord?: string;
      wordCount?: number;
      neighborAvg?: number;
    }>;
    totalIssues: number;
    highSeverityCount: number;
    mediumSeverityCount: number;
    lowSeverityCount: number;
    documentId: string;
    structureScore: number;
    riskLevel: string;
  }> => {
    const response = await api.post('/structure-guidance/issues', {
      document_id: documentId,
      include_low_severity: includeLowSeverity,
    });
    return transformKeys(response.data);
  },

  /**
   * Get detailed guidance for a specific issue (calls LLM)
   * 获取特定问题的详细指引（调用 LLM）
   */
  getGuidance: async (
    documentId: string,
    issueId: string,
    issueType: string,
    options?: {
      affectedPositions?: string[];
      affectedText?: string;
      prevParagraph?: string;
      nextParagraph?: string;
      connectorWord?: string;
    }
  ): Promise<{
    issueId: string;
    issueType: string;
    guidanceZh: string;
    guidanceEn: string;
    referenceVersion: string | null;
    referenceExplanationZh: string | null;
    whyNoReference: string | null;
    affectedText: string;
    keyConcepts: {
      fromPrev: string[];
      fromNext: string[];
    };
    confidence: number;
    canGenerateReference: boolean;
  }> => {
    const response = await api.post('/structure-guidance/guidance', {
      document_id: documentId,
      issue_id: issueId,
      issue_type: issueType,
      affected_positions: options?.affectedPositions,
      affected_text: options?.affectedText,
      prev_paragraph: options?.prevParagraph,
      next_paragraph: options?.nextParagraph,
      connector_word: options?.connectorWord,
    });
    return transformKeys(response.data);
  },

  /**
   * Apply a structure fix
   * 应用结构修复
   */
  applyFix: async (
    documentId: string,
    issueId: string,
    fixType: 'use_reference' | 'custom' | 'skip' | 'mark_done',
    options?: {
      customText?: string;
      affectedPositions?: string[];
    }
  ): Promise<{
    success: boolean;
    issueId: string;
    newStatus: string;
    message: string;
    messageZh: string;
    updatedText?: string;
  }> => {
    const response = await api.post('/structure-guidance/apply-fix', {
      document_id: documentId,
      issue_id: issueId,
      fix_type: fixType,
      custom_text: options?.customText,
      affected_positions: options?.affectedPositions,
    });
    return transformKeys(response.data);
  },

  /**
   * Get paragraph reorder suggestion
   * 获取段落重排建议
   */
  getReorderSuggestion: async (
    documentId: string
  ): Promise<{
    currentOrder: number[];
    suggestedOrder: number[];
    changes: Array<{
      action: string;
      paragraphIndex: number;
      fromPosition: number;
      toPosition: number;
      paragraphSummary: string;
      reasonZh: string;
      reasonEn: string;
    }>;
    overallGuidanceZh: string;
    warningsZh: string[];
    previewFlowZh: string;
    estimatedImprovement: number;
    confidence: number;
  }> => {
    const response = await api.post('/structure-guidance/reorder-suggestion', {
      document_id: documentId,
    });
    return transformKeys(response.data);
  },
};

// Task APIs (Billing System)
// 任务 API（计费系统）
export const taskApi = {
  /**
   * Create a billing task for a document
   * 为文档创建计费任务
   */
  create: async (documentId: string): Promise<{
    taskId: string;
    documentId: string;
    wordCountRaw: number;
    wordCountBillable: number;
    billableUnits: number;
    priceCalculated: number;
    priceFinal: number;
    isMinimumCharge: boolean;
    status: string;
    paymentStatus: string;
    isDebugMode: boolean;
  }> => {
    const response = await api.post('/task/create', {
      document_id: documentId,
    });
    return transformKeys(response.data);
  },

  /**
   * Get task by ID
   * 根据ID获取任务
   */
  get: async (taskId: string): Promise<{
    taskId: string;
    documentId: string;
    wordCountBillable: number;
    priceFinal: number;
    status: string;
    paymentStatus: string;
    isDebugMode: boolean;
  }> => {
    const response = await api.get(`/task/${taskId}`);
    return transformKeys(response.data);
  },

  /**
   * Get task by document ID
   * 根据文档ID获取任务
   */
  getByDocument: async (documentId: string): Promise<{
    taskId: string;
    documentId: string;
    status: string;
    paymentStatus: string;
  } | null> => {
    const response = await api.get(`/task/by-document/${documentId}`);
    return response.data ? transformKeys(response.data) : null;
  },

  /**
   * Check if task can start processing
   * 检查任务是否可以开始处理
   */
  checkCanProcess: async (taskId: string): Promise<{
    canProcess: boolean;
    reason: string;
  }> => {
    const response = await api.post(`/task/${taskId}/check-can-process`);
    return transformKeys(response.data);
  },
};

// Payment APIs (Billing System)
// 支付 API（计费系统）
export const paymentApi = {
  /**
   * Get price quote for a task
   * 获取任务报价
   */
  getQuote: async (taskId: string): Promise<{
    taskId: string;
    wordCountRaw: number;
    wordCountBillable: number;
    billableUnits: number;
    calculatedPrice: number;
    finalPrice: number;
    isMinimumCharge: boolean;
    minimumCharge: number;
    isDebugMode: boolean;
    paymentRequired: boolean;
  }> => {
    const response = await api.get(`/payment/quote/${taskId}`);
    return transformKeys(response.data);
  },

  /**
   * Initiate payment for a task
   * 发起任务支付
   */
  pay: async (taskId: string): Promise<{
    taskId: string;
    platformOrderId: string;
    paymentUrl: string | null;
    qrCodeUrl: string | null;
    amount: number;
    expiresAt: string | null;
    isDebugMode: boolean;
    autoPaid: boolean;
  }> => {
    const response = await api.post(`/payment/pay/${taskId}`);
    return transformKeys(response.data);
  },

  /**
   * Check payment status
   * 检查支付状态
   */
  checkStatus: async (taskId: string): Promise<{
    taskId: string;
    status: string;
    paymentStatus: string;
    paidAt: string | null;
    canProcess: boolean;
  }> => {
    const response = await api.get(`/payment/status/${taskId}`);
    return transformKeys(response.data);
  },
};

// Admin APIs (Statistics Dashboard)
// 管理员 API（统计仪表板）
export const adminApi = {
  /**
   * Admin login with secret key
   * 使用密钥登录管理员
   */
  login: async (secretKey: string): Promise<{
    accessToken: string;
    tokenType: string;
    expiresIn: number;
    adminId: string;
  }> => {
    const response = await api.post('/admin/login', {
      secret_key: secretKey,
    });
    return transformKeys(response.data);
  },

  /**
   * Get overview statistics
   * 获取概览统计
   */
  getOverview: async (): Promise<{
    totalRevenue: number;
    todayRevenue: number;
    thisWeekRevenue: number;
    thisMonthRevenue: number;
    totalTasks: number;
    paidTasks: number;
    pendingTasks: number;
    completedTasks: number;
    failedTasks: number;
    totalUsers: number;
    activeUsersToday: number;
    activeUsersWeek: number;
    newUsersToday: number;
    totalWordsProcessed: number;
    totalDocuments: number;
    dataFrom: string;
    dataTo: string;
  }> => {
    const adminToken = localStorage.getItem('academicguard-admin');
    let token = '';
    try {
      if (adminToken) {
        const parsed = JSON.parse(adminToken);
        token = parsed.state?.adminToken || '';
      }
    } catch (e) { /* ignore */ }

    const response = await api.get('/admin/stats/overview', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return transformKeys(response.data);
  },

  /**
   * Get revenue statistics
   * 获取营收统计
   */
  getRevenue: async (params?: {
    period?: 'daily' | 'weekly' | 'monthly';
    days?: number;
  }): Promise<{
    period: string;
    data: Array<{
      date: string;
      revenue: number;
      taskCount: number;
      avgPrice: number;
    }>;
    totalRevenue: number;
    totalTasks: number;
    averageOrderValue: number;
    growthRate: number | null;
  }> => {
    const adminToken = localStorage.getItem('academicguard-admin');
    let token = '';
    try {
      if (adminToken) {
        const parsed = JSON.parse(adminToken);
        token = parsed.state?.adminToken || '';
      }
    } catch (e) { /* ignore */ }

    const response = await api.get('/admin/stats/revenue', {
      params: {
        period: params?.period || 'daily',
        days: params?.days || 30,
      },
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return transformKeys(response.data);
  },

  /**
   * Get task statistics
   * 获取任务统计
   */
  getTasks: async (params?: {
    days?: number;
  }): Promise<{
    statusDistribution: Array<{
      status: string;
      count: number;
      percentage: number;
    }>;
    paymentDistribution: Array<{
      status: string;
      count: number;
      percentage: number;
    }>;
    avgWordCount: number;
    avgPrice: number;
    minPrice: number;
    maxPrice: number;
    minimumChargeCount: number;
    minimumChargeRatio: number;
    tasksByDate: Array<{
      date: string;
      count: number;
    }>;
  }> => {
    const adminToken = localStorage.getItem('academicguard-admin');
    let token = '';
    try {
      if (adminToken) {
        const parsed = JSON.parse(adminToken);
        token = parsed.state?.adminToken || '';
      }
    } catch (e) { /* ignore */ }

    const response = await api.get('/admin/stats/tasks', {
      params: { days: params?.days || 30 },
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return transformKeys(response.data);
  },

  /**
   * Get user statistics
   * 获取用户统计
   */
  getUsers: async (params?: {
    days?: number;
  }): Promise<{
    registrationsByDate: Array<{
      date: string;
      count: number;
    }>;
    totalNewUsers: number;
    topUsers: Array<{
      userId: string;
      phone: string;
      nickname: string;
      taskCount: number;
      totalSpent: number;
    }>;
    periodDays: number;
  }> => {
    const adminToken = localStorage.getItem('academicguard-admin');
    let token = '';
    try {
      if (adminToken) {
        const parsed = JSON.parse(adminToken);
        token = parsed.state?.adminToken || '';
      }
    } catch (e) { /* ignore */ }

    const response = await api.get('/admin/stats/users', {
      params: { days: params?.days || 30 },
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return transformKeys(response.data);
  },

  /**
   * Get feedback statistics
   * 获取反馈统计
   */
  getFeedback: async (): Promise<{
    totalFeedbacks: number;
    statusDistribution: Record<string, { count: number; percentage: number }>;
    pendingCount: number;
    recentFeedbacks: Array<{
      id: string;
      contact: string;
      content: string;
      status: string;
      createdAt: string;
    }>;
  }> => {
    const adminToken = localStorage.getItem('academicguard-admin');
    let token = '';
    try {
      if (adminToken) {
        const parsed = JSON.parse(adminToken);
        token = parsed.state?.adminToken || '';
      }
    } catch (e) { /* ignore */ }

    const response = await api.get('/admin/stats/feedback', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return transformKeys(response.data);
  },

  // Anomaly Detection APIs
  // 异常检测 API

  /**
   * Get anomaly detection overview
   * 获取异常检测概览
   */
  getAnomalyOverview: async (sigma: number = 2.0): Promise<{
    totalTasks: number;
    anomalyCount: number;
    anomalyRate: number;
    sigma: number;
    priceRanges: Array<{
      rangeLabel: string;
      minPrice: number;
      maxPrice: number;
      taskCount: number;
      meanCalls: number;
      stdCalls: number;
      threshold: number;
      anomalyCount: number;
    }>;
  }> => {
    const adminToken = localStorage.getItem('academicguard-admin');
    let token = '';
    try {
      if (adminToken) {
        const parsed = JSON.parse(adminToken);
        token = parsed.state?.adminToken || '';
      }
    } catch (e) { /* ignore */ }

    const response = await api.get('/admin/anomaly/overview', {
      params: { sigma },
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return transformKeys(response.data);
  },

  /**
   * Get anomaly distribution data for charts
   * 获取异常分布数据（用于图表）
   */
  getAnomalyDistribution: async (params?: {
    minPrice?: number;
    maxPrice?: number;
    sigma?: number;
  }): Promise<{
    scatterData: Array<{
      taskId: string;
      price: number;
      calls: number;
      isAnomaly: boolean;
      wordCount?: number;
    }>;
    histogramData: Array<{
      rangeLabel: string;
      rangeMin: number;
      rangeMax: number;
      count: number;
      isAboveThreshold: boolean;
    }>;
    stats: {
      mean: number;
      std: number;
      threshold: number;
      sigma: number;
      totalCount: number;
    } | null;
  }> => {
    const adminToken = localStorage.getItem('academicguard-admin');
    let token = '';
    try {
      if (adminToken) {
        const parsed = JSON.parse(adminToken);
        token = parsed.state?.adminToken || '';
      }
    } catch (e) { /* ignore */ }

    const response = await api.get('/admin/anomaly/distribution', {
      params: {
        min_price: params?.minPrice,
        max_price: params?.maxPrice,
        sigma: params?.sigma || 2.0,
      },
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return transformKeys(response.data);
  },

  /**
   * Get anomaly orders list
   * 获取异常订单列表
   */
  getAnomalyOrders: async (params?: {
    minPrice?: number;
    maxPrice?: number;
    sigma?: number;
    page?: number;
    pageSize?: number;
  }): Promise<{
    orders: Array<{
      taskId: string;
      userId: string | null;
      priceFinal: number;
      apiCallCount: number;
      expectedCalls: number;
      deviation: number;
      wordCount: number | null;
      createdAt: string;
      status: string;
    }>;
    total: number;
    page: number;
    pageSize: number;
    stats: {
      mean: number;
      std: number;
      threshold: number;
      sigma: number;
    } | null;
  }> => {
    const adminToken = localStorage.getItem('academicguard-admin');
    let token = '';
    try {
      if (adminToken) {
        const parsed = JSON.parse(adminToken);
        token = parsed.state?.adminToken || '';
      }
    } catch (e) { /* ignore */ }

    const response = await api.get('/admin/anomaly/orders', {
      params: {
        min_price: params?.minPrice,
        max_price: params?.maxPrice,
        sigma: params?.sigma || 2.0,
        page: params?.page || 1,
        page_size: params?.pageSize || 20,
      },
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return transformKeys(response.data);
  },
};

// Add auth token interceptor
// 添加认证令牌拦截器
api.interceptors.request.use((config) => {
  // Try to get token from localStorage
  // 尝试从 localStorage 获取令牌
  try {
    const authData = localStorage.getItem('academicguard-auth');
    if (authData) {
      const parsed = JSON.parse(authData);
      if (parsed.state?.token) {
        config.headers.Authorization = `Bearer ${parsed.state.token}`;
      }
    }
  } catch (e) {
    // Ignore parse errors
  }
  return config;
});

// Add error interceptor
// 添加错误拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => handleError(error)
);

export default api;
