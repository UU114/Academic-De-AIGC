/**
 * TypeScript type definitions for AcademicGuard
 * AcademicGuard 的 TypeScript 类型定义
 */

// Risk levels
// 风险等级
export type RiskLevel = 'safe' | 'low' | 'medium' | 'high';

// Suggestion source
// 建议来源
export type SuggestionSource = 'llm' | 'rule' | 'custom';

// Processing mode
// 处理模式
export type ProcessMode = 'intervention' | 'yolo';

// Session status
// 会话状态
export type SessionStatus = 'active' | 'paused' | 'completed';

// Fingerprint match
// 指纹匹配
export interface FingerprintMatch {
  word: string;
  position: number;
  riskWeight: number;
  category: string;
  replacements: string[];
}

// Issue detail
// 问题详情
export interface IssueDetail {
  type: string;
  description: string;
  descriptionZh: string;
  severity: RiskLevel;
  position?: number;
  word?: string;
}

// Detector view (Turnitin/GPTZero)
// 检测器视角
export interface DetectorView {
  detector: string;
  riskScore: number;
  keyIssues: string[];
  keyIssuesZh: string[];
}

// Sentence status in session
// 句子在会话中的状态
export type SentenceStatus = 'pending' | 'current' | 'processed' | 'skip' | 'flag';

// Sentence analysis result
// 句子分析结果
export interface SentenceAnalysis {
  id: string;  // Database ID for API calls
  index: number;
  text: string;
  riskScore: number;
  riskLevel: RiskLevel;
  ppl: number;
  pplRisk: RiskLevel;
  fingerprints: FingerprintMatch[];
  fingerprintDensity: number;
  issues: IssueDetail[];
  turnitinView?: DetectorView;
  gptzeroView?: DetectorView;
  lockedTerms: string[];
  status?: SentenceStatus;  // Status in session context
}

// Change detail
// 改动详情
export interface ChangeDetail {
  original: string;
  replacement: string;
  reason: string;
  reasonZh: string;
}

// Single suggestion
// 单个建议
export interface Suggestion {
  source: SuggestionSource;
  rewritten: string;
  changes: ChangeDetail[];
  predictedRisk: number;
  semanticSimilarity: number;
  explanation: string;
  explanationZh: string;
}

// Suggestion response
// 建议响应
export interface SuggestResponse {
  original: string;
  originalRisk: number;
  translation: string;
  llmSuggestion?: Suggestion;
  ruleSuggestion?: Suggestion;
  lockedTerms: string[];
}

// Validation result
// 验证结果
export interface ValidationResult {
  passed: boolean;
  semanticSimilarity: number;
  termsIntact: boolean;
  newRiskScore: number;
  newRiskLevel: RiskLevel;
  message: string;
  messageZh: string;
}

// Session state
// 会话状态
export interface SessionState {
  sessionId: string;
  documentId: string;
  mode: ProcessMode;
  totalSentences: number;
  processed: number;
  skipped: number;
  flagged: number;
  currentIndex: number;
  currentSentence?: SentenceAnalysis;
  suggestions?: SuggestResponse;
  progressPercent: number;
}

// Document info
// 文档信息
export interface DocumentInfo {
  id: string;
  filename: string;
  status: string;
  totalSentences: number;
  highRiskCount: number;
  mediumRiskCount: number;
  lowRiskCount: number;
  createdAt: string;
}

// Session info for listing
// 用于列表的会话信息
export interface SessionInfo {
  sessionId: string;
  documentId: string;
  documentName: string;
  mode: ProcessMode;
  status: string;
  totalSentences: number;
  processed: number;
  progressPercent: number;
  createdAt: string;
  completedAt?: string;
}

// Session config
// 会话配置
export interface SessionConfig {
  colloquialismLevel: number;
  targetLang: string;
  processLevels: RiskLevel[];
}

// Colloquialism level info
// 口语化等级信息
export interface ColloquialismLevelInfo {
  level: number;
  name: string;
  nameZh: string;
  description: string;
}

// Progress update for YOLO mode
// YOLO模式的进度更新
export interface ProgressUpdate {
  total: number;
  processed: number;
  currentSentence: string;
  percent: number;
  estimatedRemaining?: number;
}

// API error response
// API错误响应
export interface ApiError {
  detail: string;
  status: number;
}

// Grammar modifier (attributive/adverbial/complement)
// 语法修饰成分（定语/状语/补语）
export interface GrammarModifier {
  type: string;
  typeZh: string;
  text: string;
  modifies: string;
}

// Grammar structure
// 语法结构
export interface GrammarStructure {
  subject: string;
  subjectZh: string;
  predicate: string;
  predicateZh: string;
  object?: string;
  objectZh?: string;
  modifiers: GrammarModifier[];
}

// Clause information
// 从句信息
export interface ClauseInfo {
  type: string;
  typeZh: string;
  text: string;
  function: string;
  functionZh: string;
}

// Pronoun reference
// 代词指代
export interface PronounReference {
  pronoun: string;
  reference: string;
  referenceZh: string;
  context: string;
}

// AI word suggestion
// AI词汇建议
export interface AIWordSuggestion {
  word: string;
  level: number;
  levelDesc: string;
  alternatives: string[];
  contextSuggestion: string;
}

// Rewrite suggestion
// 改写建议
export interface RewriteSuggestion {
  type: string;
  typeZh: string;
  description: string;
  descriptionZh: string;
  example?: string;
}

// Detailed sentence analysis response
// 详细句子分析响应
export interface DetailedSentenceAnalysis {
  original: string;
  grammar: GrammarStructure;
  clauses: ClauseInfo[];
  pronouns: PronounReference[];
  aiWords: AIWordSuggestion[];
  rewriteSuggestions: RewriteSuggestion[];
}
