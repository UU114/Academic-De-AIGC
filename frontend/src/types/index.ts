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
  newRiskScore?: number;  // Risk score after modification
  newRiskLevel?: RiskLevel;  // Risk level after modification
  // CAASS v2.0 Phase 2: Context baseline from paragraph
  // CAASS v2.0 第二阶段：来自段落的上下文基准分
  contextBaseline?: number;
  paragraphIndex?: number;
  // Phase 2: Enhanced metrics
  // 第二阶段：增强指标
  burstinessValue?: number;  // Burstiness ratio (0-1), higher = more human-like
  burstinessRisk?: string;  // Burstiness risk level: low, medium, high, unknown
  connectorCount?: number;  // Number of explicit connectors in this sentence
  connectorWord?: string;  // Detected connector word if any
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

// Session step type
// 会话步骤类型
export type SessionStep = 'step1-1' | 'step1-2' | 'step2' | 'step3' | 'level2' | 'level3' | 'review';

// Session info for listing
// 用于列表的会话信息
export interface SessionInfo {
  sessionId: string;
  documentId: string;
  documentName: string;
  mode: ProcessMode;
  status: string;
  currentStep: SessionStep;
  totalSentences: number;
  processed: number;
  progressPercent: number;
  colloquialismLevel: number;  // Colloquialism level (0-10) / 口语化程度 (0-10)
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

// Phase 3: Transition Analysis Types (Level 2 De-AIGC)
// 第三阶段：衔接分析类型（Level 2 De-AIGC）

// Transition strategy type
// 过渡策略类型
export type TransitionStrategy = 'semantic_echo' | 'logical_hook' | 'rhythm_break';

// Transition issue
// 衔接问题
export interface TransitionIssue {
  type: string;
  description: string;
  descriptionZh: string;
  severity: string;  // high, medium, low
  position: string;  // para_a_end, para_b_start, both
  word?: string;
}

// Transition option (repair suggestion)
// 衔接选项（修复建议）
export interface TransitionOption {
  strategy: TransitionStrategy;
  strategyNameZh: string;
  paraAEnding: string;
  paraBOpening: string;
  keyConcepts?: string[];  // For semantic_echo
  hookType?: string;  // For logical_hook: implication, observation, limitation
  rhythmChange?: string;  // For rhythm_break: long→short, complex→simple
  explanation: string;
  explanationZh: string;
  predictedImprovement: number;
}

// Transition analysis response
// 衔接分析响应
export interface TransitionAnalysisResponse {
  paraAEnding: string;
  paraBOpening: string;
  smoothnessScore: number;
  riskLevel: string;  // low, medium, high
  issues: TransitionIssue[];
  explicitConnectors: string[];
  hasTopicSentencePattern: boolean;
  hasSummaryEnding: boolean;
  semanticOverlap: number;
  options: TransitionOption[];
  message: string;
  messageZh: string;
}

// Document transition summary
// 文档衔接摘要
export interface DocumentTransitionSummary {
  documentId: string;
  totalTransitions: number;
  highRiskCount: number;
  mediumRiskCount: number;
  lowRiskCount: number;
  avgSmoothnessScore: number;
  commonIssues: string[];
  transitions: TransitionAnalysisResponse[];
}

// ============================================================================
// Structure Analysis Types (Phase 4: Level 1 De-AIGC)
// 结构分析类型（第4阶段：Level 1 De-AIGC）
// ============================================================================

// Structure strategy type
// 结构策略类型
export type StructureStrategy = 'optimize_connection' | 'deep_restructure';

// Paragraph info
// 段落信息
export interface ParagraphInfo {
  index: number;
  firstSentence: string;
  lastSentence: string;
  wordCount: number;
  sentenceCount: number;
  hasTopicSentence: boolean;
  hasSummaryEnding: boolean;
  connectorWords: string[];
  functionType: string;  // introduction, body, conclusion, transition, evidence, analysis
  // Smart structure fields (from LLM analysis)
  // 智能结构字段（来自 LLM 分析）
  position?: string;  // Section position like "3.2(1)"
  summary?: string;  // Content summary
  summaryZh?: string;  // Chinese summary
  aiRisk?: string;  // high/medium/low
  aiRiskReason?: string;  // Reason for risk level
  // Detailed rewrite suggestions
  // 详细修改建议字段
  rewriteSuggestionZh?: string;  // Specific Chinese rewrite advice (中文改写建议)
  rewriteExample?: string;  // Example rewritten text in English (英文改写示例)
}

// Smart paragraph info from LLM analysis
// 来自 LLM 分析的智能段落信息
export interface SmartParagraphInfo {
  position: string;  // Section position like "3.2(1)"
  summary: string;  // English content summary
  summaryZh: string;  // Chinese content summary
  firstSentence: string;
  lastSentence: string;
  wordCount: number;
  aiRisk: string;  // high/medium/low
  aiRiskReason: string;  // Chinese reason (中文原因，引用原文保留原语言)
  // Detailed rewrite suggestions
  // 详细修改建议字段
  rewriteSuggestionZh?: string;  // Specific Chinese rewrite advice (中文改写建议)
  rewriteExample?: string;  // Example rewritten text in English (英文改写示例)
}

// Document section info
// 文档章节信息
export interface SectionInfo {
  number: string;  // Section number like "1", "1.1", "2.3.1"
  title: string;  // Section title
  paragraphs: SmartParagraphInfo[];
}

// Smart structure issue
// 智能结构问题
export interface SmartStructureIssue {
  type: string;
  description: string;
  descriptionZh: string;
  severity: string;
  affectedPositions: string[];  // Uses position instead of index
}

// Explicit connector (AI fingerprint detection)
// 显性连接词（AI指纹检测）
export interface ExplicitConnector {
  word: string;  // The connector word detected
  position: string;  // Paragraph position like "3.2(1)"
  location: string;  // "paragraph_start" or "sentence_start"
  severity: string;  // "high" or "medium"
}

// Logic break point between paragraphs
// 段落间逻辑断裂点
export interface LogicBreak {
  from_position: string;  // e.g., "2(1)"
  to_position: string;  // e.g., "2(2)"
  transition_type: string;  // "smooth", "abrupt", "glue_word_only"
  issue: string;  // Description in English
  issue_zh: string;  // Description in Chinese
  suggestion: string;  // Suggestion in English
  suggestion_zh: string;  // Suggestion in Chinese
}

// Structure issue
// 结构问题
export interface StructureIssue {
  type: string;  // linear_flow, repetitive_pattern, uniform_length, predictable_order
  description: string;
  descriptionZh: string;
  severity: string;  // high, medium, low
  affectedParagraphs: number[];
  suggestion: string;
  suggestionZh: string;
}

// Break point
// 断点
export interface BreakPoint {
  position: number;
  type: string;  // topic_shift, argument_gap, repetition, abrupt_transition
  description: string;
  descriptionZh: string;
}

// Flow relation
// 流关系
export interface FlowRelation {
  from: number;
  to: number;
  relation: string;  // continuation, comparison, evidence, return, gap
  symbol: string;  // →, ↔, ⤵, ⟳, ✗
}

// Risk area
// 风险区域
export interface RiskArea {
  paragraph: number;
  riskLevel: string;
  reason: string;
  reasonZh: string;
}

// Structure modification
// 结构修改
export interface StructureModification {
  paragraphIndex: number;
  changeType: string;  // rewrite_opening, rewrite_transition, reorder
  original?: string;
  modified?: string;
  explanation: string;
  explanationZh: string;
  echoConcept?: string;
}

// Structure change
// 结构变化
export interface StructureChange {
  type: string;  // reorder, split, merge, insert
  affectedParagraphs: number[];
  description: string;
  descriptionZh: string;
}

// Structure option
// 结构选项
export interface StructureOption {
  strategy: StructureStrategy;
  strategyNameZh: string;
  modifications: StructureModification[];  // For optimize_connection
  newOrder: number[];  // For deep_restructure
  restructureType?: string;
  restructureTypeZh?: string;
  changes: StructureChange[];
  outline: string[];
  predictedImprovement: number;
  explanation: string;
  explanationZh: string;
}

// Structure analysis response
// 结构分析响应
// Section-level suggestion for detailed improvements
// 章节级别的详细改进建议
export interface SectionSuggestion {
  sectionNumber: string;  // e.g., "1", "2.1", "Abstract"
  sectionTitle: string;
  severity: 'high' | 'medium' | 'low';
  suggestionType: 'add_content' | 'restructure' | 'merge' | 'split' | 'reorder' | 'remove_connector' | 'add_citation';
  suggestionZh: string;
  suggestionEn: string;
  details: string[];  // Specific action items
  affectedParagraphs: string[];  // e.g., ["1(1)", "1(2)"]
}

// Detailed improvement suggestions
// 详细改进建议
export interface DetailedImprovementSuggestions {
  abstractSuggestions: string[];  // Suggestions for abstract
  logicSuggestions: string[];  // Overall logic/order suggestions
  sectionSuggestions: SectionSuggestion[];  // Per-section suggestions
  priorityOrder: string[];  // Section numbers in priority order
  overallAssessmentZh: string;
  overallAssessmentEn: string;
}

export interface StructureAnalysisResponse {
  // Basic info
  totalParagraphs: number;
  totalSentences?: number;
  totalWords?: number;
  avgParagraphLength?: number;
  paragraphLengthVariance?: number;

  // Scores and levels
  structureScore: number;  // 0-100, higher = more AI-like
  riskLevel: string;  // low, medium, high

  // Smart structure fields (from LLM analysis)
  // 智能结构字段（来自 LLM 分析）
  sections?: SectionInfo[];
  totalSections?: number;
  scoreBreakdown?: Record<string, number>;
  recommendation?: string;
  recommendationZh?: string;

  // Detailed improvement suggestions
  // 详细改进建议
  detailedSuggestions?: DetailedImprovementSuggestions;

  // Explicit connectors and logic breaks (AI fingerprint detection)
  // 显性连接词和逻辑断裂点（AI指纹检测）
  explicit_connectors?: ExplicitConnector[];
  logic_breaks?: LogicBreak[];

  // Paragraph info (with smart fields)
  paragraphs: ParagraphInfo[];

  // Detected patterns
  issues?: StructureIssue[];
  breakPoints?: BreakPoint[];

  // Extracted thesis
  coreThesis?: string;
  keyArguments?: string[];

  // Pattern flags
  hasLinearFlow: boolean;
  hasRepetitivePattern: boolean;
  hasUniformLength: boolean;
  hasPredictableOrder: boolean;

  // Repair options
  options: StructureOption[];

  // Messages
  message?: string;
  messageZh?: string;
}

// Logic diagnosis response
// 逻辑诊断响应
export interface LogicDiagnosisResponse {
  flowMap: FlowRelation[];
  structurePattern: string;  // linear, parallel, nested, circular
  structurePatternZh: string;
  patternDescription: string;
  patternDescriptionZh: string;
  riskAreas: RiskArea[];
  recommendedStrategy: StructureStrategy;
  recommendationReason: string;
  recommendationReasonZh: string;
}

// ============================================================================
// Flow Coordination Types (Phase 5: Full Flow Integration)
// 流程协调类型（第5阶段：全流程整合）
// ============================================================================

// Processing level
// 处理层级
export type ProcessingLevel = 'level_1' | 'level_2' | 'level_3';

// Processing mode
// 处理模式
export type ProcessingMode = 'quick' | 'deep';

// Step status
// 步骤状态
export type StepStatus = 'pending' | 'in_progress' | 'completed' | 'skipped';

// Level info
// 层级信息
export interface LevelInfo {
  level: ProcessingLevel;
  nameEn: string;
  nameZh: string;
  status: StepStatus;
  scoreBefore?: number;
  scoreAfter?: number;
  issuesFound?: number;
  issuesFixed?: number;
}

// Flow summary
// 流程摘要
export interface FlowSummary {
  totalIssuesFound: number;
  totalIssuesFixed: number;
  totalScoreReduction: number;
  completedLevels: number;
  skippedLevels: number;
}

// Flow progress response
// 流程进度响应
export interface FlowProgress {
  flowId: string;
  mode: ProcessingMode;
  currentLevel: ProcessingLevel;
  overallStatus: 'in_progress' | 'completed';
  levels: LevelInfo[];
  summary: FlowSummary;
}

// Flow start response
// 流程启动响应
export interface FlowStartResponse {
  flowId: string;
  sessionId: string;
  mode: ProcessingMode;
  currentLevel: ProcessingLevel;
  levels: LevelInfo[];
}

// Level context response
// 层级上下文响应
export interface LevelContext {
  flowId: string;
  level: ProcessingLevel;
  context: {
    coreThesis?: string;
    keyArguments?: string[];
    structureIssues?: StructureIssue[];
    newParagraphOrder?: number[];
    paragraphPairs?: Array<{ paraA: string; paraB: string }>;
    transitionRepairs?: Array<{ strategy: TransitionStrategy; changes: string }>;
    whitelist?: string[];
    colloquialismLevel?: number;
    currentText?: string;
    paragraphs?: string[];
  };
}

// ============================================================================
// Paragraph Logic Types (Level 3 Enhancement: Intra-paragraph Logic)
// 段落逻辑类型（Level 3 增强：段落内逻辑）
// ============================================================================

// Paragraph logic issue type
// 段落逻辑问题类型
export type ParagraphLogicIssueType =
  | 'subject_repetition'
  | 'uniform_length'
  | 'linear_structure'
  | 'connector_overuse'
  | 'first_person_overuse';

// Paragraph logic issue
// 段落逻辑问题
export interface ParagraphLogicIssue {
  type: ParagraphLogicIssueType;
  description: string;
  descriptionZh: string;
  severity: 'low' | 'medium' | 'high';
  position: [number, number];  // [startIndex, endIndex]
  suggestion: string;
  suggestionZh: string;
  details?: Record<string, unknown>;
}

// Paragraph logic structure type
// 段落逻辑结构类型
export type LogicStructure = 'linear' | 'mixed' | 'varied' | 'insufficient' | 'error';

// Paragraph analysis response
// 段落分析响应
export interface ParagraphAnalysisResponse {
  issues: ParagraphLogicIssue[];
  hasSubjectRepetition: boolean;
  hasUniformLength: boolean;
  hasLinearStructure: boolean;
  hasFirstPersonOveruse: boolean;
  subjectDiversityScore: number;  // 0.0-1.0, higher = more diverse
  lengthVariationCv: number;  // Coefficient of variation
  logicStructure: LogicStructure;
  firstPersonRatio: number;
  connectorDensity: number;
  paragraphRiskAdjustment: number;  // Risk contribution 0-50
  sentenceCount: number;
  sentences: string[];
}

// Paragraph restructure strategy
// 段落重组策略
export type ParagraphRestructureStrategy =
  | 'ani'
  | 'subject_diversity'
  | 'implicit_connector'
  | 'rhythm'
  | 'citation_entanglement'
  | 'all';

// Restructure change
// 重组变更
export interface RestructureChange {
  type: string;
  description: string;
  original?: string;
  result?: string;
}

// Paragraph restructure request
// 段落重组请求
export interface ParagraphRestructureRequest {
  paragraph: string;
  strategy: ParagraphRestructureStrategy;
  toneLevel: number;
  detectedIssues?: ParagraphLogicIssue[];
  repeatedSubject?: string;
  subjectCount?: number;
  connectorsFound?: Array<{ index: number; connector: string; category: string }>;
  lengths?: number[];
  cv?: number;
}

// Paragraph restructure response
// 段落重组响应
export interface ParagraphRestructureResponse {
  original: string;
  restructured: string;
  strategy: ParagraphRestructureStrategy;
  strategyName: string;
  strategyNameZh: string;
  changes: RestructureChange[];
  explanation: string;
  explanationZh: string;
  originalRiskAdjustment: number;
  newRiskAdjustment: number;
  improvement: number;
}

// Strategy info
// 策略信息
export interface ParagraphStrategyInfo {
  key: ParagraphRestructureStrategy;
  name: string;
  nameZh: string;
  description: string;
  descriptionZh: string;
}

// ============================================================================
// Structural Risk Card Types (7-Indicator Visualization)
// 结构风险卡片类型（7指征可视化）
// ============================================================================

// Single structural indicator for risk card
// 单个结构指征
export interface StructuralIndicator {
  id: string;
  name: string;
  nameZh: string;
  triggered: boolean;
  riskLevel: number;  // 1-3 stars
  emoji: string;
  color: string;      // hex color code
  description: string;
  descriptionZh: string;
  details?: string;
  detailsZh?: string;
}

// 7-Indicator structural risk card response
// 7指征结构风险卡片响应
export interface StructuralRiskCardResponse {
  indicators: StructuralIndicator[];
  triggeredCount: number;
  overallRisk: 'low' | 'medium' | 'high';
  overallRiskZh: string;
  summary: string;
  summaryZh: string;
  totalScore: number;
}

// ============================================================================
// Level 1 Guided Interaction Types
// Level 1 指引式交互类型
// ============================================================================

// Issue category
// 问题分类
export type IssueCategory = 'structure' | 'transition';

// Structure issue type
// 结构问题类型
export type StructureIssueType =
  | 'linear_flow'
  | 'uniform_length'
  | 'predictable_structure'
  | 'explicit_connector'
  | 'missing_semantic_echo'
  | 'logic_gap'
  | 'paragraph_too_short'
  | 'paragraph_too_long'
  | 'formulaic_opening'
  | 'weak_transition';

// Issue status
// 问题状态
export type IssueStatus = 'pending' | 'expanded' | 'fixed' | 'skipped';

// Structure issue item for list display
// 用于列表展示的结构问题项
export interface StructureIssueItem {
  id: string;
  type: StructureIssueType;
  category: IssueCategory;
  severity: 'high' | 'medium' | 'low';
  titleZh: string;
  titleEn: string;
  briefZh: string;
  briefEn?: string;
  affectedPositions: string[];
  affectedTextPreview: string;
  canGenerateReference: boolean;
  status: IssueStatus;
  // Additional context
  connectorWord?: string;
  wordCount?: number;
  neighborAvg?: number;
}

// Structure issue list request
// 结构问题列表请求
export interface StructureIssueListRequest {
  documentId: string;
  includeLowSeverity?: boolean;
}

// Structure issue list response
// 结构问题列表响应
export interface StructureIssueListResponse {
  structureIssues: StructureIssueItem[];
  transitionIssues: StructureIssueItem[];
  totalIssues: number;
  highSeverityCount: number;
  mediumSeverityCount: number;
  lowSeverityCount: number;
  documentId: string;
  structureScore: number;
  riskLevel: string;
}

// Key concepts for semantic echo
// 用于语义回声的关键概念
export interface KeyConcepts {
  fromPrev: string[];
  fromNext: string[];
}

// Issue guidance request
// 问题指引请求
export interface IssueGuidanceRequest {
  documentId: string;
  issueId: string;
  issueType: StructureIssueType;
  affectedPositions?: string[];
  affectedText?: string;
  prevParagraph?: string;
  nextParagraph?: string;
  connectorWord?: string;
}

// Issue guidance response
// 问题指引响应
export interface IssueGuidanceResponse {
  issueId: string;
  issueType: string;
  guidanceZh: string;
  guidanceEn: string;
  referenceVersion: string | null;
  referenceExplanationZh: string | null;
  whyNoReference: string | null;
  affectedText: string;
  keyConcepts: KeyConcepts;
  confidence: number;
  canGenerateReference: boolean;
}

// Apply structure fix request
// 应用结构修复请求
export interface ApplyStructureFixRequest {
  documentId: string;
  issueId: string;
  fixType: 'use_reference' | 'custom' | 'skip' | 'mark_done';
  customText?: string;
  affectedPositions?: string[];
}

// Apply structure fix response
// 应用结构修复响应
export interface ApplyStructureFixResponse {
  success: boolean;
  issueId: string;
  newStatus: IssueStatus;
  message: string;
  messageZh: string;
  updatedText?: string;
}

// Reorder change
// 重排变更
export interface ReorderChange {
  action: string;
  paragraphIndex: number;
  fromPosition: number;
  toPosition: number;
  paragraphSummary: string;
  reasonZh: string;
  reasonEn: string;
}

// Reorder suggestion request
// 重排建议请求
export interface ReorderSuggestionRequest {
  documentId: string;
}

// Reorder suggestion response
// 重排建议响应
export interface ReorderSuggestionResponse {
  currentOrder: number[];
  suggestedOrder: number[];
  changes: ReorderChange[];
  overallGuidanceZh: string;
  warningsZh: string[];
  previewFlowZh: string;
  estimatedImprovement: number;
  confidence: number;
}
