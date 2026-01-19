/**
 * 5-Layer Analysis API Service
 * 5层分析API服务
 *
 * Provides access to the new unified 5-layer detection architecture:
 * - Layer 5: Document (文章层)
 * - Layer 4: Section (章节层)
 * - Layer 3: Paragraph (段落层)
 * - Layer 2: Sentence (句子层)
 * - Layer 1: Lexical (词汇层)
 */

import axios from 'axios';

// Create axios instance
// 创建 axios 实例
const api = axios.create({
  baseURL: '/api/v1/analysis',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

// ============================================
// Types / 类型定义
// ============================================

export type LayerLevel = 'document' | 'section' | 'paragraph' | 'sentence' | 'lexical';
export type RiskLevel = 'low' | 'medium' | 'high';
export type IssueSeverity = 'low' | 'medium' | 'high';

export interface DetectionIssue {
  type: string;
  description: string;
  descriptionZh: string;
  severity: IssueSeverity;
  layer: LayerLevel;
  position?: string;  // Position reference as string (e.g., "paragraph 1, 2")
  suggestion?: string;
  suggestionZh?: string;
  details?: Record<string, unknown>;
}

// Issue Suggestion Response (for Load Suggestions feature)
// 问题建议响应（用于加载建议功能）
export interface IssueSuggestionResponse {
  diagnosisZh: string;
  strategies: Array<{
    nameZh: string;
    descriptionZh: string;
    exampleBefore?: string;
    exampleAfter?: string;
    difficulty: string;
    effectiveness: number;
  }>;
  modificationPrompt: string;
  priorityTipsZh: string[];
  cautionZh: string;
  // Frontend-friendly aliases
  // 前端友好的别名
  analysis?: string;
  suggestions?: string[];
  exampleFix?: string;
}

export interface LayerAnalysisResult {
  layer: LayerLevel;
  riskScore: number;
  riskLevel: RiskLevel;
  issues: DetectionIssue[];
  recommendations: string[];
  recommendationsZh: string[];
  details: Record<string, unknown>;
  processingTimeMs?: number;
}

// Document Layer Types
// 文章层类型
export interface DocumentAnalysisResponse extends LayerAnalysisResult {
  structureScore: number;
  structurePattern: string;
  sections: Array<{
    index: number;
    role: string;
    title?: string;
    paragraphCount: number;
    wordCount: number;
  }>;
  globalRiskFactors: string[];
  predictabilityScores: Record<string, number>;
}

// Step 1.4: Connector & Transition Analysis Types
// 步骤 1.4：连接词与衔接分析类型
export interface TransitionIssue {
  type: string;
  description: string;
  descriptionZh: string;
  severity: IssueSeverity;
  position: string;
  word?: string;
}

export interface TransitionResult {
  transitionIndex: number;
  paraAIndex: number;
  paraBIndex: number;
  paraAEnding: string;
  paraBOpening: string;
  smoothnessScore: number;
  riskLevel: RiskLevel;
  issues: TransitionIssue[];
  explicitConnectors: string[];
  hasTopicSentencePattern: boolean;
  hasSummaryEnding: boolean;
  semanticOverlap: number;
}

export interface ConnectorAnalysisResponse {
  totalTransitions: number;
  problematicTransitions: number;
  overallSmoothnessScore: number;
  overallRiskLevel: RiskLevel;
  totalExplicitConnectors: number;
  connectorDensity: number;
  connectorList: string[];
  transitions: TransitionResult[];
  issues: DetectionIssue[];
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs?: number;
}

// Step 1.2: Paragraph Length Analysis Types
// 步骤 1.2：段落长度分析类型
export type ParagraphLengthStrategy = 'merge' | 'split' | 'expand' | 'compress' | 'none';

export interface ParagraphLengthInfo {
  index: number;
  wordCount: number;
  charCount: number;
  sentenceCount: number;
  preview: string;
  deviationFromMean: number;
  suggestedStrategy: ParagraphLengthStrategy;
  strategyReason: string;
  strategyReasonZh: string;
}

export interface ParagraphLengthAnalysisResponse {
  // Statistics from unified text parsing service
  // 来自统一文本解析服务的统计数据
  paragraphCount: number;
  totalWordCount: number;
  meanLength: number;
  stdevLength: number;
  cv: number;
  minLength: number;
  maxLength: number;
  lengthRegularityScore: number;
  riskLevel: RiskLevel;
  targetCv: number;
  paragraphs: ParagraphLengthInfo[];
  mergeSuggestions: number[];
  splitSuggestions: number[];
  expandSuggestions: number[];
  compressSuggestions: number[];
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs?: number;
  // LLM analysis results / LLM分析结果
  issues?: Array<{
    type: string;
    description: string;
    descriptionZh?: string;
    severity: string;
    evidence?: string[];
    fixSuggestions?: string[];
    fixSuggestionsZh?: string[];
    affectedPositions?: string[];
    currentCv?: number;
    targetCv?: number;
    detailedExplanation?: string;
    detailedExplanationZh?: string;
  }>;
  summary?: string;
  summaryZh?: string;
  // Section distribution from unified parsing service
  // 来自统一解析服务的章节分布
  sectionDistribution?: Array<{
    index: number;
    role: string;
    title: string;
    paragraphCount: number;
    wordCount: number;
    startParagraph?: number;
    endParagraph?: number;
  }>;
}

// Step 1.3: Progression & Closure Types
// 步骤 1.3：推进模式与闭合类型
export type ProgressionType = 'monotonic' | 'non_monotonic' | 'mixed' | 'unknown';
export type ClosureType = 'strong' | 'moderate' | 'weak' | 'open';

export interface ProgressionMarker {
  paragraphIndex: number;
  marker: string;
  category: string;
  isMonotonic: boolean;
}

export interface ProgressionClosureResponse {
  progressionScore: number;
  progressionType: ProgressionType;
  monotonicCount: number;
  nonMonotonicCount: number;
  sequentialMarkersFound: number;
  progressionMarkers: ProgressionMarker[];
  closureScore: number;
  closureType: ClosureType;
  strongClosurePatterns: string[];
  weakClosurePatterns: string[];
  lastParagraphPreview: string;
  combinedScore: number;
  riskLevel: RiskLevel;
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs?: number;
}

// Step 1.5: Content Substantiality Types
// 步骤 1.5：内容实质性类型
export type SubstantialityLevel = 'high' | 'medium' | 'low';

export interface ParagraphSubstantiality {
  index: number;
  preview: string;
  wordCount: number;
  specificityScore: number;
  genericPhraseCount: number;
  specificDetailCount: number;
  fillerRatio: number;
  genericPhrases: string[];
  specificDetails: string[];
  substantialityLevel: SubstantialityLevel;
  suggestion: string;
  suggestionZh: string;
}

export interface ContentSubstantialityResponse {
  paragraphCount: number;
  overallSpecificityScore: number;
  overallSubstantiality: SubstantialityLevel;
  riskLevel: RiskLevel;
  totalGenericPhrases: number;
  totalSpecificDetails: number;
  averageFillerRatio: number;
  lowSubstantialityParagraphs: number[];
  paragraphs: ParagraphSubstantiality[];
  commonGenericPhrases: string[];
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs?: number;
}

// Section Layer Types
// 章节层类型
export interface SectionAnalysisResponse extends LayerAnalysisResult {
  sectionCount: number;
  logicFlowScore: number;
  transitionQuality: number;
  lengthDistribution: {
    mean: number;
    stdDev: number;
    cv: number;
    isUniform: boolean;
  };
  sectionDetails: Array<{
    index: number;
    role: string;
    wordCount: number;
    transitionScore?: number;
    issues: string[];
  }>;
}

// Step 2.0: Section Identification Types
// 步骤 2.0：章节识别类型
export interface SectionInfo {
  index: number;
  role: string;
  roleConfidence: number;
  title?: string;
  startParagraphIdx: number;
  endParagraphIdx: number;
  paragraphCount: number;
  wordCount: number;
  charCount: number;
  preview: string;
  userAssignedRole?: string;
}

export interface SectionIdentificationResponse {
  sectionCount: number;
  sections: SectionInfo[];
  totalParagraphs: number;
  totalWords: number;
  roleDistribution: Record<string, number>;
  issues?: DetectionIssue[];
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs?: number;
}

// Step 2.1: Section Order & Structure Types
// 步骤 2.1：章节顺序与结构类型
export interface SectionOrderAnalysis {
  detectedOrder: string[];
  expectedOrder: string[];
  orderMatchScore: number;
  isPredictable: boolean;
  missingSections: string[];
  unexpectedSections: string[];
  fusionScore: number;
  multiFunctionSections: number[];
}

export interface SectionOrderResponse {
  riskScore: number;
  riskLevel: RiskLevel;
  orderAnalysis: SectionOrderAnalysis;
  issues: DetectionIssue[];
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs?: number;
}

// Step 2.2: Section Length Distribution Types
// 步骤 2.2：章节长度分布类型
export interface SectionLengthInfo {
  index: number;
  role: string;
  title?: string;  // Actual section title from document / 文档中的实际章节标题
  wordCount: number;
  paragraphCount: number;
  deviationFromMean: number;
  isExtreme: boolean;
  expectedWeight?: number;
  actualWeight: number;
  weightDeviation: number;
}

export interface SectionLengthResponse {
  riskScore: number;
  riskLevel: RiskLevel;
  sectionCount: number;
  totalWords: number;
  meanLength: number;
  stdevLength: number;
  lengthCv: number;
  isUniform: boolean;
  sections: SectionLengthInfo[];
  extremelyShort: number[];
  extremelyLong: number[];
  keySectionWeightScore: number;
  issues: DetectionIssue[];
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs?: number;
}

// Step 2.3: Internal Structure Similarity Types (NEW)
// 步骤 2.3：章节内部结构相似性类型（新）
export interface ParagraphFunctionInfo {
  paragraphIndex: number;
  localIndex: number;
  function: string;
  functionConfidence: number;
  preview: string;
}

export interface SectionInternalStructure {
  sectionIndex: number;
  sectionRole: string;
  paragraphFunctions: ParagraphFunctionInfo[];
  functionSequence: string[];
  headingDepth: number;
  hasSubheadings: boolean;
  argumentCount: number;
  argumentDensity: number;
}

export interface StructureSimilarityPair {
  sectionAIndex: number;
  sectionBIndex: number;
  sectionARole: string;
  sectionBRole: string;
  functionSequenceSimilarity: number;
  structureSimilarity: number;
  isSuspicious: boolean;
}

export interface InternalStructureSimilarityResponse {
  riskScore: number;
  riskLevel: RiskLevel;
  sectionStructures: SectionInternalStructure[];
  similarityPairs: StructureSimilarityPair[];
  averageSimilarity: number;
  maxSimilarity: number;
  headingDepthCv: number;
  argumentDensityCv: number;
  suspiciousPairs: StructureSimilarityPair[];
  issues: DetectionIssue[];
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs?: number;
}

// Step 2.4: Section Transition Types
// 步骤 2.4：章节衔接与过渡类型
export interface SectionTransitionInfo {
  fromSectionIndex: number;
  toSectionIndex: number;
  fromSectionRole: string;
  toSectionRole: string;
  hasExplicitTransition: boolean;
  explicitWords: string[];
  transitionStrength: string;
  semanticEchoScore: number;
  echoedKeywords: string[];
  openerText: string;
  openerPattern: string;
  isFormulaicOpener: boolean;
  transitionRiskScore: number;
}

export interface SectionTransitionResponse {
  riskScore: number;
  riskLevel: RiskLevel;
  totalTransitions: number;
  explicitTransitionCount: number;
  transitions: SectionTransitionInfo[];
  explicitRatio: number;
  avgSemanticEcho: number;
  formulaicOpenerCount: number;
  strengthDistribution: Record<string, number>;
  issues: DetectionIssue[];
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs?: number;
}

// Step 2.5: Inter-Section Logic Types
// 步骤 2.5：章节间逻辑关系类型
export interface ArgumentChainNode {
  sectionIndex: number;
  sectionRole: string;
  mainArgument: string;
  supportingPoints: string[];
  connectsToPrevious: boolean;
  connectionType: string;
}

export interface RedundancyInfo {
  sectionAIndex: number;
  sectionBIndex: number;
  redundantContent: string;
  redundancyType: string;
  severity: string;
}

export interface ProgressionPatternInfo {
  patternType: string;
  description: string;
  descriptionZh: string;
  isAiTypical: boolean;
  sectionsInvolved: number[];
}

export interface InterSectionLogicResponse {
  riskScore: number;
  riskLevel: RiskLevel;
  argumentChain: ArgumentChainNode[];
  chainCoherenceScore: number;
  redundancies: RedundancyInfo[];
  totalRedundancies: number;
  progressionPatterns: ProgressionPatternInfo[];
  dominantPattern: string;
  patternVarietyScore: number;
  issues: DetectionIssue[];
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs?: number;
}

// Paragraph Layer Types
// 段落层类型

// Step 3.0: Paragraph Identification Types
// 步骤 3.0：段落识别类型
export interface ParagraphMeta {
  index: number;
  wordCount: number;
  sentenceCount: number;
  charCount: number;
  preview: string;
  sectionIndex?: number;
  contentType: string;
}

export interface ParagraphIdentificationResponse {
  paragraphs: string[];
  paragraphCount: number;
  paragraphSectionMap: number[];
  paragraphMetadata: ParagraphMeta[];
  filteredCount: number;
  totalWordCount: number;
  riskLevel: RiskLevel;
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs: number;
}

// Step 3.5: Paragraph Transition Types
// 步骤 3.5：段落过渡类型
export interface ParagraphTransitionInfo {
  fromParagraph: number;
  toParagraph: number;
  hasExplicitConnector: boolean;
  connectorWords: string[];
  semanticEchoScore: number;
  echoedKeywords: string[];
  transitionQuality: 'smooth' | 'abrupt' | 'formulaic';
  openerText: string;
  openerPattern: string;
  isFormulaicOpener: boolean;
  riskScore: number;
}

export interface ParagraphTransitionResponse {
  riskScore: number;
  riskLevel: RiskLevel;
  totalTransitions: number;
  explicitConnectorCount: number;
  explicitRatio: number;
  avgSemanticEcho: number;
  formulaicOpenerCount: number;
  transitions: ParagraphTransitionInfo[];
  issues: DetectionIssue[];
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs: number;
}

// Combined Paragraph Analysis Response
// 综合段落分析响应
export interface ParagraphAnalysisResponse extends LayerAnalysisResult {
  paragraphs: string[];  // Filtered paragraphs (headers/keywords removed) 过滤后的段落
  paragraphCount: number;  // Transformed from paragraph_count by transformKeys
  roleDistribution: Record<string, number>;
  coherenceScore: number;
  anchorDensity: number;  // Transformed from anchor_density by transformKeys
  sentenceLengthAnalysis: {
    meanCv: number;
    lowBurstinessParagraphs: number[];
    uniformLengthRisk: boolean;
  };
  paragraphDetails: Array<{  // Transformed from paragraph_details by transformKeys
    index: number;
    role: string;
    preview?: string;  // First few words of paragraph / 段落前几个单词
    coherenceScore: number;
    anchorCount: number;
    sentenceLengthCv: number;
    issues: string[];
  }>;
}

// Sentence Layer Types
// 句子层类型
export interface SentenceAnalysisResponse extends LayerAnalysisResult {
  sentenceCount: number;
  patternScore: number;
  voidCount: number;
  roleDistribution: Record<string, number>;
  sentenceDetails: Array<{
    index: number;
    paragraphIndex: number;
    text: string;
    role: string;
    length: number;
    hasVoid: boolean;
    voidTypes?: string[];
    issues: string[];
  }>;
  polishContext?: {
    paragraphText: string;
    sentenceRole: string;
    prevSentence?: string;
    nextSentence?: string;
    paragraphRole?: string;
  };
}

// ============================================
// Layer 2 Sub-Step Types (Step 4.0 - 4.5)
// Layer 2 子步骤类型（步骤 4.0 - 4.5）
// ============================================

// Step 4.0: Sentence Identification
// 步骤 4.0：句子识别
export interface SentenceInfo {
  index: number;
  text: string;
  paragraphIndex: number;
  wordCount: number;
  sentenceType: 'simple' | 'compound' | 'complex' | 'compound_complex';
  functionRole: string;
  hasSubordinate: boolean;
  clauseDepth: number;
  voice: 'active' | 'passive';
  openerWord: string;
}

export interface SentenceIdentificationResponse {
  sentences: SentenceInfo[];
  sentenceCount: number;
  paragraphSentenceMap: Record<number, number[]>;
  typeDistribution: Record<string, number>;
  riskLevel: RiskLevel;
  riskScore: number;
  issues: Array<Record<string, unknown>>;
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs: number;
}

// Step 4.1: Pattern Analysis
// 步骤 4.1：句式结构分析
export interface TypeStats {
  count: number;
  percentage: number;
  isRisk: boolean;
  threshold: number;
}

export interface OpenerAnalysis {
  openerCounts: Record<string, number>;
  topRepeated: string[];
  repetitionRate: number;
  subjectOpeningRate: number;
  issues: string[];
}

// Syntactic Void Match (for step 4.1)
// 句法空洞匹配（用于步骤 4.1）
export interface SyntacticVoidMatch {
  patternType: string;
  matchedText: string;
  position: number;
  endPosition: number;
  severity: string;
  abstractWords: string[];
  suggestion: string;
  suggestionZh: string;
}

export interface PatternAnalysisResponse {
  typeDistribution: Record<string, TypeStats>;
  openerAnalysis: OpenerAnalysis;
  voiceDistribution: Record<string, number>;
  clauseDepthStats: Record<string, number>;
  parallelStructureCount: number;
  issues: Array<Record<string, unknown>>;
  riskLevel: RiskLevel;
  riskScore: number;
  highRiskParagraphs: Array<{
    paragraphIndex: number;
    riskScore: number;
    riskLevel: RiskLevel;
    simpleRatio: number;
    lengthCv: number;
    openerRepetition: number;
    sentenceCount: number;
  }>;
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs: number;
  // Syntactic Void Detection fields (integrated from core/analyzer/syntactic_void.py)
  // 句法空洞检测字段（从 core/analyzer/syntactic_void.py 集成）
  syntacticVoids?: SyntacticVoidMatch[];
  voidScore?: number;
  voidDensity?: number;
  hasCriticalVoid?: boolean;
}

// Step 4.2: Length Analysis
// 步骤 4.2：句长分析
export interface LengthAnalysisResponse {
  paragraphLengthStats: Array<{
    paragraphIndex: number;
    sentenceCount: number;
    lengthCv: number;
    minLength: number;
    maxLength: number;
    avgLength: number;
    lengths: number[];
  }>;
  overallLengthCv: number;
  uniformityIssues: Array<{
    paragraphIndex: number;
    lengthCv: number;
    issue: string;
    issueZh: string;
  }>;
  mergeCandidates: Array<{
    paragraphIndex: number;
    sentenceIndices: number[];
    sentences: string[];
    combinedLength: number;
    reason: string;
    reasonZh: string;
  }>;
  splitCandidates: Array<{
    paragraphIndex: number;
    sentenceIndex: number;
    sentence: string;
    wordCount: number;
    reason: string;
    reasonZh: string;
  }>;
  riskLevel: RiskLevel;
  riskScore: number;
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs: number;
}

// Step 4.3: Merge Suggestions
// 步骤 4.3：句子合并建议
export interface MergeCandidate {
  sentenceIndices: number[];
  originalSentences: string[];
  mergedText: string;
  mergeType: 'causal' | 'contrast' | 'temporal' | 'addition';
  similarityScore: number;
  readabilityScore: number;
  wordCountBefore: number;
  wordCountAfter: number;
  complexityGain: string;
}

export interface MergeSuggestionResponse {
  paragraphIndex: number;
  candidates: MergeCandidate[];
  estimatedImprovement: Record<string, number>;
  riskLevel: RiskLevel;
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs: number;
}

// Step 4.4: Connector Optimization
// 步骤 4.4：连接词优化
export interface ConnectorIssue {
  sentenceIndex: number;
  connector: string;
  connectorType: 'addition' | 'causal' | 'contrast' | 'sequence' | 'summary';
  position: 'start' | 'middle';
  riskLevel: RiskLevel;
  context: string;
}

export interface ReplacementSuggestion {
  originalConnector: string;
  sentenceIndex: number;
  replacementType: 'semantic_echo' | 'remove' | 'subordinate' | 'pronoun' | 'lexical';
  newText: string;
  explanation: string;
  explanationZh: string;
}

export interface ConnectorOptimizationResponse {
  paragraphIndex: number;
  connectorIssues: ConnectorIssue[];
  totalConnectors: number;
  explicitRatio: number;
  connectorTypeDistribution: Record<string, number>;
  replacementSuggestions: ReplacementSuggestion[];
  optimizedText?: string;
  riskLevel: RiskLevel;
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs: number;
}

// Step 4.5: Diversification
// 步骤 4.5：句式多样化
export interface ChangeRecord {
  sentenceIndex: number;
  original: string;
  modified: string;
  changeType: string;
  strategy: string;
  improvementType: string;
}

export interface PatternMetrics {
  simpleRatio: number;
  compoundRatio: number;
  complexRatio: number;
  compoundComplexRatio: number;
  openerDiversity: number;
  voiceBalance: number;
  lengthCv: number;
  overallScore: number;
}

export interface DiversificationResponse {
  paragraphIndex: number;
  originalText: string;
  diversifiedText: string;
  changes: ChangeRecord[];
  appliedStrategies: Record<string, number>;
  beforeMetrics: PatternMetrics;
  afterMetrics: PatternMetrics;
  improvementSummary: Record<string, number>;
  riskLevel: RiskLevel;
  recommendations: string[];
  recommendationsZh: string[];
  processingTimeMs: number;
}

// Paragraph Config Types
// 段落配置类型
export interface ParagraphParams {
  targetPassiveRatio?: number;
  allowMerge: boolean;
  maxMergeCount: number;
  preserveConnectors: string[];
  rewriteIntensity: 'conservative' | 'moderate' | 'aggressive';
}

export interface ParagraphVersion {
  version: number;
  step: string;
  text: string;
  timestamp: string;
  changes: ChangeRecord[];
  metrics?: Record<string, number>;
}

export interface ParagraphProcessingConfig {
  paragraphIndex: number;
  status: 'pending' | 'in_progress' | 'completed' | 'skipped' | 'locked';
  mode: 'auto' | 'merge_only' | 'connector_only' | 'diversify_only' | 'custom';
  enabledSteps: string[];
  params: ParagraphParams;
  versions: ParagraphVersion[];
  currentVersion: number;
}

// PPL (Perplexity) Analysis Result (for step 5.1)
// PPL（困惑度）分析结果（用于步骤 5.1）
export interface PPLParagraphAnalysis {
  index: number;
  ppl: number;
  riskLevel: RiskLevel;
  wordCount: number;
  preview: string;
}

export interface PPLAnalysisResult {
  pplScore?: number;
  pplRiskLevel?: RiskLevel;
  usedOnnx: boolean;
  paragraphs: PPLParagraphAnalysis[];
  highRiskParagraphs: number[];
  available: boolean;
  modelInfo?: Record<string, unknown>;
  reason?: string;
}

// Lexical Layer Types
// 词汇层类型
export interface LexicalAnalysisResponse extends LayerAnalysisResult {
  fingerprintMatches: {
    typeA: Array<{ word: string; count: number; positions: number[] }>;
    typeB: Array<{ word: string; count: number; positions: number[] }>;
    phrases: Array<{ phrase: string; count: number; positions: number[] }>;
  };
  fingerprintDensity: number;
  connectorMatches: Array<{ connector: string; count: number; positions: number[] }>;
  connectorRatio: number;
  replacementSuggestions: Record<string, string[]>;
  // PPL Analysis fields (integrated from core/analyzer/ppl_calculator.py)
  // PPL分析字段（从 core/analyzer/ppl_calculator.py 集成）
  pplScore?: number;
  pplRiskLevel?: RiskLevel;
  pplUsedOnnx?: boolean;
  pplAnalysis?: PPLAnalysisResult;
}

// Step 5.0: Lexical Context Preparation Types
// 步骤 5.0：词汇环境准备类型
export interface WordFrequency {
  word: string;
  count: number;
  percentage: number;
}

export interface LockedTermStatus {
  term: string;
  found: boolean;
  count: number;
}

export interface LexicalContextResponse extends LayerAnalysisResult {
  vocabularyStats: {
    totalWords: number;
    uniqueWords: number;
    vocabularyRichness: number;
    ttr: number;
  };
  topWords: WordFrequency[];
  overusedWords: string[];
  lockedTermsStatus: LockedTermStatus[];
}

// Step 5.1: Fingerprint Detection Types
// 步骤 5.1：AI指纹检测类型
export interface FingerprintMatch {
  word?: string;
  phrase?: string;
  count: number;
  positions: string[];
  severity: IssueSeverity;
}

export interface FingerprintDetectionResponse extends LayerAnalysisResult {
  typeAWords: FingerprintMatch[];
  typeBWords: FingerprintMatch[];
  typeCPhrases: FingerprintMatch[];
  totalFingerprints: number;
  fingerprintDensity: number;
  pplScore?: number;
  pplRiskLevel?: RiskLevel;
}

// Step 5.2: Human Feature Analysis Types
// 步骤 5.2：人类特征分析类型
export interface HumanFeature {
  type: 'colloquialism' | 'personal_voice' | 'imperfection' | 'emotion' | 'idiosyncratic' | 'conversational';
  text: string;
  position: string;
  strength: 'strong' | 'moderate' | 'weak';
}

export interface HumanFeatureResponse extends LayerAnalysisResult {
  humanFeatures: HumanFeature[];
  featureScore: number;
  featureDensity: number;
  missingFeatures: string[];
}

// Step 5.3: Replacement Generation Types
// 步骤 5.3：替换词生成类型
export interface ReplacementSuggestion {
  original: string;
  position: string;
  reason: 'ai_fingerprint' | 'variety' | 'formality' | 'collocation';
  suggestions: string[];
  recommended: string;
  context: string;
}

export interface ReplacementGenerationResponse extends LayerAnalysisResult {
  replacements: ReplacementSuggestion[];
  replacementCount: number;
  byCategory: {
    aiFingerprint: number;
    variety: number;
    formality: number;
    collocation: number;
  };
}

// Step 5.4: Paragraph Rewriting Types
// 步骤 5.4：段落级改写类型
export interface ParagraphRewriteInfo {
  index: number;
  needsRewrite: boolean;
  fingerprintDensity: number;
  vocabularyVariety: number;
  formalityScore: number;
  humanFeatures: number;
  issues: string[];
}

export interface ParagraphRewriteResponse extends LayerAnalysisResult {
  paragraphs: ParagraphRewriteInfo[];
  paragraphsToRewrite: number[];
}

// Step 5.5: Validation Types
// 步骤 5.5：验证类型
export interface ValidationResult {
  lockedTermsCheck: {
    passed: boolean;
    missingTerms: string[];
    alteredTerms: string[];
  };
  semanticSimilarity: number;
  qualityScore: number;
  remainingIssues: Array<{
    type: string;
    description: string;
    descriptionZh: string;
    position: string;
  }>;
  validationPassed: boolean;
}

export interface ValidationResponse extends LayerAnalysisResult {
  originalRiskScore: number;
  finalRiskScore: number;
  improvement: number;
  validation: ValidationResult;
}

// Pipeline Types
// 流水线类型
export interface PipelineAnalysisRequest {
  text: string;
  layers?: LayerLevel[];
  stopOnLowRisk?: boolean;
  includeContext?: boolean;
}

export interface PipelineAnalysisResponse {
  overallRiskScore: number;
  overallRiskLevel: RiskLevel;
  layersAnalyzed: LayerLevel[];
  layerResults: Record<string, LayerAnalysisResult>;
  totalIssues: number;
  priorityIssues: DetectionIssue[];
  processingTimeMs: number;
  timestamp: string;
}

// Rewrite Context Types
// 改写上下文类型
export interface RewriteContext {
  sentenceText: string;
  paragraphText: string;
  sentenceRole: string;
  sentenceIndex: number;
  paragraphIndex: number;
  paragraphRole?: string;
  prevSentence?: string;
  nextSentence?: string;
  sectionContext?: string;
  issues: DetectionIssue[];
}

// ============================================
// Term Lock API (Step 1.0)
// 词汇锁定 API（步骤 1.0）
// ============================================

export type TermType = 'technical_term' | 'proper_noun' | 'acronym' | 'key_phrase' | 'core_word';

export interface ExtractedTerm {
  term: string;
  termType: TermType;
  frequency: number;
  reason: string;
  reasonZh: string;
  recommended: boolean;
}

export interface ExtractTermsResponse {
  extractedTerms: ExtractedTerm[];
  totalCount: number;
  byType: Record<string, number>;
  processingTimeMs: number;
}

export interface ConfirmLockResponse {
  lockedCount: number;
  lockedTerms: string[];
  message: string;
  messageZh: string;
}

export interface LockedTermsResponse {
  sessionId: string;
  lockedTerms: string[];
  lockedCount: number;
  createdAt?: string;
}

export const termLockApi = {
  /**
   * Step 1.0.1: Extract candidate terms for locking
   * 步骤 1.0.1：提取待锁定的候选术语
   */
  extractTerms: async (documentText: string, sessionId: string): Promise<ExtractTermsResponse> => {
    const response = await api.post('/term-lock/extract-terms', {
      document_text: documentText,
      session_id: sessionId,
    });
    return transformKeys<ExtractTermsResponse>(response.data);
  },

  /**
   * Step 1.0.2: Confirm and lock selected terms
   * 步骤 1.0.2：确认并锁定选中的术语
   */
  confirmLock: async (
    sessionId: string,
    lockedTerms: string[],
    customTerms: string[] = []
  ): Promise<ConfirmLockResponse> => {
    const response = await api.post('/term-lock/confirm-lock', {
      session_id: sessionId,
      locked_terms: lockedTerms,
      custom_terms: customTerms,
    });
    return transformKeys<ConfirmLockResponse>(response.data);
  },

  /**
   * Get current locked terms for session
   * 获取当前会话的锁定术语
   */
  getLockedTerms: async (sessionId: string): Promise<LockedTermsResponse> => {
    const response = await api.get('/term-lock/locked-terms', {
      params: { session_id: sessionId },
    });
    return transformKeys<LockedTermsResponse>(response.data);
  },

  /**
   * Clear locked terms for session
   * 清除会话的锁定术语
   */
  clearLockedTerms: async (sessionId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete('/term-lock/locked-terms', {
      params: { session_id: sessionId },
    });
    return transformKeys(response.data);
  },
};

// ============================================
// Document Layer API (Layer 5)
// 文章层 API（第5层）
// ============================================
export const documentLayerApi = {
  /**
   * Step 1.1: Structure Analysis
   * 步骤 1.1：结构分析
   */
  analyzeStructure: async (text: string, sessionId?: string): Promise<DocumentAnalysisResponse> => {
    const response = await api.post('/document/structure', {
      text,
      session_id: sessionId  // Add session_id for caching
    });
    return transformKeys<DocumentAnalysisResponse>(response.data);
  },

  /**
   * Step 1.2: Global Risk Assessment
   * 步骤 1.2：全局风险评估
   */
  analyzeRisk: async (text: string): Promise<DocumentAnalysisResponse> => {
    const response = await api.post('/document/risk', { text });
    return transformKeys<DocumentAnalysisResponse>(response.data);
  },

  /**
   * Combined Document Analysis
   * 综合文章分析
   */
  analyze: async (text: string): Promise<DocumentAnalysisResponse> => {
    const response = await api.post('/document/analyze', { text });
    return transformKeys<DocumentAnalysisResponse>(response.data);
  },

  /**
   * Get Document Context for Lower Layers
   * 获取文章上下文供下层使用
   */
  getContext: async (text: string): Promise<{
    sections: Array<{ index: number; role: string; boundaries: [number, number] }>;
    structurePattern: string;
    globalRisk: number;
  }> => {
    const response = await api.post('/document/context', { text });
    return transformKeys(response.data);
  },

  /**
   * Step 1.4: Connector & Transition Analysis
   * 步骤 1.4：连接词与衔接分析
   *
   * Analyzes paragraph transitions for AI-like patterns including:
   * - Explicit connectors at paragraph openings
   * - Formulaic topic sentences
   * - Summary endings
   * - Too-smooth transitions
   */
  analyzeConnectors: async (text: string, sessionId?: string): Promise<ConnectorAnalysisResponse> => {
    const response = await api.post('/document/connectors', {
      text,
      session_id: sessionId,
    });
    return transformKeys<ConnectorAnalysisResponse>(response.data);
  },

  /**
   * Step 1.2: Paragraph Length Regularity Analysis
   * 步骤 1.2：段落长度规律性分析
   *
   * Analyzes paragraph length distribution to detect AI-like uniformity:
   * - CV (Coefficient of Variation) < 0.3 indicates too uniform (AI-like)
   * - Target CV >= 0.4 for human-like writing
   * - Provides merge/split/expand/compress suggestions
   */
  analyzeParagraphLength: async (text: string, sessionId?: string): Promise<ParagraphLengthAnalysisResponse> => {
    const response = await api.post('/document/paragraph-length', {
      text,
      session_id: sessionId,
    });
    return transformKeys<ParagraphLengthAnalysisResponse>(response.data);
  },

  /**
   * Step 1.3: Progression & Closure Analysis
   * 步骤 1.3：推进模式与闭合分析
   *
   * Analyzes document progression patterns and closure strength:
   * - Monotonic (AI-like): sequential, additive, one-directional flow
   * - Non-monotonic (Human-like): returns, conditionals, reversals
   * - Strong closure (AI-like): definitive conclusions
   * - Weak closure (Human-like): open questions, unresolved tensions
   */
  analyzeProgressionClosure: async (text: string, sessionId?: string): Promise<ProgressionClosureResponse> => {
    const response = await api.post('/document/progression-closure', {
      text,
      session_id: sessionId,
    });
    return transformKeys<ProgressionClosureResponse>(response.data);
  },

  /**
   * Step 1.5: Content Substantiality Analysis
   * 步骤 1.5：内容实质性分析
   *
   * Analyzes content for specificity vs. generic AI-like patterns:
   * - Detects generic phrases common in AI text
   * - Identifies filler words
   * - Looks for specific details (numbers, names, dates)
   */
  analyzeContentSubstantiality: async (text: string, sessionId?: string): Promise<ContentSubstantialityResponse> => {
    const response = await api.post('/document/content-substantiality', {
      text,
      session_id: sessionId,
    });
    return transformKeys<ContentSubstantialityResponse>(response.data);
  },

  /**
   * Get detailed suggestion for a specific issue (calls legacy API)
   * 获取针对特定问题的详细建议（调用旧版API）
   * Note: Uses legacy API at /api/v1/structure, not /api/v1/analysis
   */
  getIssueSuggestion: async (
    documentId: string,
    issue: DetectionIssue,
    quickMode: boolean = false
  ): Promise<{
    diagnosisZh: string;
    strategies: Array<{
      nameZh: string;
      descriptionZh: string;
      exampleBefore?: string;
      exampleAfter?: string;
      difficulty: string;
      effectiveness: number;
    }>;
    modificationPrompt: string;
    priorityTipsZh: string[];
    cautionZh: string;
  }> => {
    // Use legacy API endpoint (baseURL is /api/v1/analysis, so we need ../structure)
    const response = await api.post('../structure/issue-suggestion', {
      documentId,
      issueType: issue.type,
      issueDescription: issue.description,
      issueDescriptionZh: issue.descriptionZh,
      severity: issue.severity,
      affectedPositions: issue.position ? [issue.position] : [],
      quickMode,
    });
    return transformKeys(response.data);
  },

  /**
   * Generate modification prompt for selected issues (calls legacy API)
   * 为选定问题生成修改提示词（调用旧版API）
   * Note: Uses legacy API at /api/v1/structure, not /api/v1/analysis
   */
  generateModifyPrompt: async (
    documentId: string,
    selectedIssues: DetectionIssue[],
    options?: {
      sessionId?: string;
      userNotes?: string;
    }
  ): Promise<{
    prompt: string;
    promptZh: string;
    issuesSummaryZh: string;
    colloquialismLevel: number;
    estimatedChanges: number;
  }> => {
    // Use legacy API endpoint
    // Note: Use location string for affected_positions, not position object
    // 使用 location 字符串作为 affected_positions，而不是 position 对象
    const response = await api.post('../structure/merge-modify/prompt', {
      document_id: documentId,
      selected_issues: selectedIssues.map(issue => {
        const issueAny = issue as Record<string, unknown>;
        const locationStr = typeof issueAny.location === 'string' ? issueAny.location : '';
        return {
          type: issue.type,
          description: issue.description || '',
          description_zh: issue.descriptionZh || '',
          severity: issue.severity || 'medium',
          affected_positions: locationStr ? [locationStr] : [],
        };
      }),
      session_id: options?.sessionId,
      user_notes: options?.userNotes,
    });
    return transformKeys(response.data);
  },

  /**
   * Apply AI modification directly (calls legacy API)
   * AI直接修改（调用旧版API）
   * Note: Uses legacy API at /api/v1/structure, not /api/v1/analysis
   */
  applyModify: async (
    documentId: string,
    selectedIssues: DetectionIssue[],
    options?: {
      sessionId?: string;
      userNotes?: string;
    }
  ): Promise<{
    modifiedText: string;
    changesSummaryZh: string;
    changesCount: number;
    remainingAttempts: number;
    colloquialismLevel: number;
  }> => {
    // Use legacy API endpoint
    // Note: Use location string for affected_positions, not position object
    // 使用 location 字符串作为 affected_positions，而不是 position 对象
    const response = await api.post('../structure/merge-modify/apply', {
      document_id: documentId,
      selected_issues: selectedIssues.map(issue => {
        // Get location string from issue - check multiple possible fields
        // 从 issue 获取位置字符串 - 检查多个可能的字段
        const issueAny = issue as Record<string, unknown>;
        const locationStr = typeof issueAny.location === 'string' ? issueAny.location : '';
        return {
          type: issue.type,
          description: issue.description || '',
          description_zh: issue.descriptionZh || '',
          severity: issue.severity || 'medium',
          affected_positions: locationStr ? [locationStr] : [],
        };
      }),
      session_id: options?.sessionId,
      user_notes: options?.userNotes,
    });
    return transformKeys(response.data);
  },

  /**
   * Get detailed issue suggestion using step-specific LLM handler
   * 使用步骤特定的LLM处理器获取详细问题建议
   *
   * This function calls the step's merge-modify/prompt endpoint to get
   * LLM-based detailed suggestions for selected issues.
   * 此函数调用步骤的merge-modify/prompt端点，获取基于LLM的详细建议
   */
  getStepIssueSuggestion: async (
    documentText: string,
    selectedIssues: DetectionIssue[],
    stepName: string,
    sessionId?: string
  ): Promise<{
    diagnosisZh: string;
    strategies: Array<{
      nameZh: string;
      descriptionZh: string;
      exampleBefore?: string;
      exampleAfter?: string;
      difficulty: string;
      effectiveness: number;
    }>;
    modificationPrompt: string;
    priorityTipsZh: string[];
    cautionZh: string;
  }> => {
    // Map step name to endpoint
    // 将步骤名称映射到端点
    const stepEndpointMap: Record<string, string> = {
      'step1_1': '/document/step1-1/merge-modify/prompt',
      'step1_2': '/document/step1-2/merge-modify/prompt',
      'step1_3': '/document/step1-3/merge-modify/prompt',
      'step1_4': '/document/step1-4/merge-modify/prompt',
      'step1_5': '/document/step1-5/merge-modify/prompt',
    };

    const endpoint = stepEndpointMap[stepName];
    if (!endpoint) {
      // Fallback to legacy API for unknown steps
      // 对于未知步骤回退到旧版API
      const response = await api.post('../structure/issue-suggestion', {
        documentId: 'temp',
        issueType: selectedIssues[0]?.type || 'unknown',
        issueDescription: selectedIssues[0]?.description || '',
        issueDescriptionZh: selectedIssues[0]?.descriptionZh || '',
        severity: selectedIssues[0]?.severity || 'medium',
        affectedPositions: [],
        quickMode: false,
      });
      return transformKeys(response.data);
    }

    // Call step-specific merge-modify/prompt endpoint
    // 调用步骤特定的merge-modify/prompt端点
    // Pass document_text directly instead of document_id for better reliability
    // 直接传递document_text而不是document_id，更可靠
    const response = await api.post(endpoint, {
      session_id: sessionId,
      document_text: documentText,
      selected_issues: selectedIssues.map(issue => {
        const issueAny = issue as Record<string, unknown>;
        const locationStr = typeof issueAny.location === 'string'
          ? issueAny.location
          : (typeof issueAny.position === 'string' ? issueAny.position : '');
        return {
          type: issue.type,
          description: issue.description || '',
          description_zh: issue.descriptionZh || '',
          severity: issue.severity || 'medium',
          affected_positions: locationStr ? [locationStr] : [],
        };
      }),
      user_notes: '',
    });

    // Transform the merge-modify/prompt response to match expected format
    // 将merge-modify/prompt响应转换为预期格式
    const data = transformKeys(response.data);

    // Build strategies from the prompt
    // 从prompt构建策略
    const strategies = [];
    if (data.prompt) {
      // Extract issue types from selected issues to build strategies
      // 从选中的问题中提取问题类型以构建策略
      const issueTypes = new Set(selectedIssues.map(i => i.type));

      if (issueTypes.has('explicit_connector_overuse')) {
        strategies.push({
          nameZh: 'Replace explicit connectors / 替换显性连接词',
          descriptionZh: 'Use semantic echo instead of explicit connectors like "Furthermore", "Moreover"',
          difficulty: 'medium',
          effectiveness: 85,
        });
      }
      if (issueTypes.has('missing_semantic_echo')) {
        strategies.push({
          nameZh: 'Add semantic echo / 添加语义回声',
          descriptionZh: 'Reference key concepts from previous paragraph to create natural flow',
          difficulty: 'medium',
          effectiveness: 80,
        });
      }
      if (issueTypes.has('logic_break_point')) {
        strategies.push({
          nameZh: 'Bridge logic gaps / 弥合逻辑断层',
          descriptionZh: 'Add bridging phrases to connect ideas naturally',
          difficulty: 'high',
          effectiveness: 75,
        });
      }
      if (issueTypes.has('formulaic_transitions')) {
        strategies.push({
          nameZh: 'Vary transition patterns / 变化过渡模式',
          descriptionZh: 'Use different transition techniques: rhetorical questions, contrasts, etc.',
          difficulty: 'medium',
          effectiveness: 80,
        });
      }

      // Step 1.5 specific issue types (Content Substantiality)
      // 步骤 1.5 特有的问题类型（内容实质性）
      if (issueTypes.has('generic_phrases') || issueTypes.has('generic_phrase_detected')) {
        strategies.push({
          nameZh: 'Replace generic phrases / 替换泛化短语',
          descriptionZh: 'Replace vague expressions like "it is important" with specific claims backed by evidence',
          difficulty: 'medium',
          effectiveness: 85,
        });
      }
      if (issueTypes.has('filler_words') || issueTypes.has('excessive_filler')) {
        strategies.push({
          nameZh: 'Remove filler words / 删除填充词',
          descriptionZh: 'Remove words like "very", "really", "actually" that add no meaning',
          difficulty: 'low',
          effectiveness: 90,
        });
      }
      if (issueTypes.has('low_substantiality') || issueTypes.has('low_specificity')) {
        strategies.push({
          nameZh: 'Add specific details / 添加具体细节',
          descriptionZh: 'Include specific data, names, dates, or examples to support claims',
          difficulty: 'high',
          effectiveness: 80,
        });
      }
      if (issueTypes.has('missing_evidence') || issueTypes.has('abstract_claims')) {
        strategies.push({
          nameZh: 'Support with evidence / 用证据支持',
          descriptionZh: 'Add citations, statistics, or concrete examples to back up abstract statements',
          difficulty: 'high',
          effectiveness: 75,
        });
      }

      // Default strategy if no specific ones matched
      // 如果没有匹配的特定策略则使用默认策略
      if (strategies.length === 0) {
        strategies.push({
          nameZh: 'Apply LLM suggestions / 应用LLM建议',
          descriptionZh: data.prompt,
          difficulty: 'medium',
          effectiveness: 75,
        });
      }
    }

    return {
      diagnosisZh: data.issuesSummaryZh || `Detected ${selectedIssues.length} issues / 检测到${selectedIssues.length}个问题`,
      strategies: strategies,
      modificationPrompt: data.prompt || '',
      priorityTipsZh: [
        'Focus on improving transitions naturally / 专注于自然改进过渡',
        'Preserve the original meaning / 保持原意',
      ],
      cautionZh: 'Review modifications to ensure academic tone is maintained / 审核修改以确保学术语气得以保持',
    };
  },
};

// ============================================
// Section Layer API (Layer 4)
// 章节层 API（第4层）
// ============================================
export const sectionLayerApi = {
  // --------------------------------
  // New Sub-step APIs (Step 2.0 - 2.5)
  // 新子步骤API（步骤 2.0 - 2.5）
  // --------------------------------

  /**
   * Step 2.0: Section Identification
   * 步骤 2.0：章节识别与角色标注
   */
  identifySections: async (
    text: string,
    paragraphs?: string[],
    sessionId?: string
  ): Promise<SectionIdentificationResponse> => {
    const response = await api.post('/section/step2-0/identify', {
      text,
      paragraphs,
      session_id: sessionId,
    });
    return transformKeys<SectionIdentificationResponse>(response.data);
  },

  /**
   * Step 2.1: Section Order & Structure
   * 步骤 2.1：章节顺序与结构分析
   */
  analyzeOrder: async (
    text: string,
    paragraphs?: string[],
    sections?: SectionInfo[],
    sessionId?: string
  ): Promise<SectionOrderResponse> => {
    const response = await api.post('/section/step2-1/order', {
      text,
      paragraphs,
      sections,
      session_id: sessionId,
    });
    return transformKeys<SectionOrderResponse>(response.data);
  },

  /**
   * Step 2.2: Section Length Distribution
   * 步骤 2.2：章节长度分布分析
   */
  analyzeLengthDistribution: async (
    text: string,
    paragraphs?: string[],
    sections?: SectionInfo[],
    sessionId?: string
  ): Promise<SectionLengthResponse> => {
    const response = await api.post('/section/step2-2/length', {
      text,
      paragraphs,
      sections,
      session_id: sessionId,
    });
    return transformKeys<SectionLengthResponse>(response.data);
  },

  /**
   * Step 2.3: Internal Structure Similarity (NEW)
   * 步骤 2.3：章节内部结构相似性分析（新）
   */
  analyzeSimilarity: async (
    text: string,
    paragraphs?: string[],
    sections?: SectionInfo[],
    sessionId?: string
  ): Promise<InternalStructureSimilarityResponse> => {
    const response = await api.post('/section/step2-3/similarity', {
      text,
      paragraphs,
      sections,
      session_id: sessionId,
    });
    return transformKeys<InternalStructureSimilarityResponse>(response.data);
  },

  /**
   * Step 2.4: Section Transition Detection
   * 步骤 2.4：章节衔接与过渡检测
   */
  analyzeTransitions: async (
    text: string,
    paragraphs?: string[],
    sections?: SectionInfo[],
    sessionId?: string
  ): Promise<SectionTransitionResponse> => {
    const response = await api.post('/section/step2-4/transition', {
      text,
      paragraphs,
      sections,
      session_id: sessionId,
    });
    return transformKeys<SectionTransitionResponse>(response.data);
  },

  /**
   * Step 2.5: Inter-Section Logic
   * 步骤 2.5：章节间逻辑关系分析
   */
  analyzeInterSectionLogic: async (
    text: string,
    paragraphs?: string[],
    sections?: SectionInfo[],
    sessionId?: string
  ): Promise<InterSectionLogicResponse> => {
    const response = await api.post('/section/step2-5/logic', {
      text,
      paragraphs,
      sections,
      session_id: sessionId,
    });
    return transformKeys<InterSectionLogicResponse>(response.data);
  },

  // --------------------------------
  // Legacy APIs (kept for backward compatibility)
  // 旧API（保持向后兼容）
  // --------------------------------

  /**
   * Legacy Step 2.1: Section Logic Flow
   * 旧步骤 2.1：章节逻辑流
   */
  analyzeLogic: async (
    text: string,
    documentContext?: Record<string, unknown>
  ): Promise<SectionAnalysisResponse> => {
    const response = await api.post('/section/logic', {
      text,
      document_context: documentContext,
    });
    return transformKeys<SectionAnalysisResponse>(response.data);
  },

  /**
   * Legacy Step 2.2: Section Transitions
   * 旧步骤 2.2：章节衔接
   */
  analyzeTransition: async (
    text: string,
    documentContext?: Record<string, unknown>
  ): Promise<SectionAnalysisResponse> => {
    const response = await api.post('/section/transition', {
      text,
      document_context: documentContext,
    });
    return transformKeys<SectionAnalysisResponse>(response.data);
  },

  /**
   * Legacy Step 2.3: Section Length Distribution
   * 旧步骤 2.3：章节长度分布
   */
  analyzeLength: async (
    text: string,
    documentContext?: Record<string, unknown>
  ): Promise<SectionAnalysisResponse> => {
    const response = await api.post('/section/length', {
      text,
      document_context: documentContext,
    });
    return transformKeys<SectionAnalysisResponse>(response.data);
  },

  /**
   * Combined Section Analysis
   * 综合章节分析
   */
  analyze: async (
    text: string,
    documentContext?: Record<string, unknown>
  ): Promise<SectionAnalysisResponse> => {
    const response = await api.post('/section/analyze', {
      text,
      document_context: documentContext,
    });
    return transformKeys<SectionAnalysisResponse>(response.data);
  },

  /**
   * Get Section Context for Lower Layers
   * 获取章节上下文供下层使用
   */
  getContext: async (
    text: string,
    documentContext?: Record<string, unknown>
  ): Promise<{
    sections: Array<{
      index: number;
      role: string;
      paragraphIndices: number[];
      transitionQuality: number;
    }>;
    logicFlowPattern: string;
  }> => {
    const response = await api.post('/section/context', {
      text,
      document_context: documentContext,
    });
    return transformKeys(response.data);
  },
};

// ============================================
// Paragraph Layer API (Layer 3)
// 段落层 API（第3层）
// ============================================
export const paragraphLayerApi = {
  /**
   * Step 3.0: Paragraph Identification & Segmentation
   * 步骤 3.0：段落识别与分割
   *
   * This is the foundational step for Layer 3.
   * Identifies paragraph boundaries and filters non-body content.
   */
  identifyParagraphs: async (
    text: string,
    sessionId?: string,
    sectionContext?: Record<string, unknown>
  ): Promise<ParagraphIdentificationResponse> => {
    const response = await api.post('/paragraph/step3-0/identify', {
      text,
      session_id: sessionId,
      section_context: sectionContext,
    });
    return transformKeys<ParagraphIdentificationResponse>(response.data);
  },

  /**
   * Step 3.1: Paragraph Role Detection
   * 步骤 3.1：段落角色识别
   */
  analyzeRole: async (
    text: string,
    sectionContext?: Record<string, unknown>
  ): Promise<ParagraphAnalysisResponse> => {
    const response = await api.post('/paragraph/role', {
      text,
      section_context: sectionContext,
    });
    return transformKeys<ParagraphAnalysisResponse>(response.data);
  },

  /**
   * Step 3.2: Paragraph Internal Coherence
   * 步骤 3.2：段落内部连贯性
   */
  analyzeCoherence: async (
    text: string,
    sectionContext?: Record<string, unknown>
  ): Promise<ParagraphAnalysisResponse> => {
    const response = await api.post('/paragraph/coherence', {
      text,
      section_context: sectionContext,
    });
    return transformKeys<ParagraphAnalysisResponse>(response.data);
  },

  /**
   * Step 3.3: Anchor Density Analysis
   * 步骤 3.3：锚点密度分析
   */
  analyzeAnchor: async (
    text: string,
    sectionContext?: Record<string, unknown>,
    sessionId?: string
  ): Promise<ParagraphAnalysisResponse> => {
    const response = await api.post('/paragraph/anchor', {
      text,
      section_context: sectionContext,
      session_id: sessionId,
    });
    return transformKeys<ParagraphAnalysisResponse>(response.data);
  },

  /**
   * Step 3.4: Sentence Length Distribution (within paragraphs)
   * 步骤 3.4：段内句子长度分布
   */
  analyzeSentenceLength: async (
    text: string,
    sectionContext?: Record<string, unknown>
  ): Promise<ParagraphAnalysisResponse> => {
    const response = await api.post('/paragraph/sentence-length', {
      text,
      section_context: sectionContext,
    });
    return transformKeys<ParagraphAnalysisResponse>(response.data);
  },

  /**
   * Combined Paragraph Analysis
   * 综合段落分析
   */
  analyze: async (
    text: string,
    sectionContext?: Record<string, unknown>
  ): Promise<ParagraphAnalysisResponse> => {
    const response = await api.post('/paragraph/analyze', {
      text,
      section_context: sectionContext,
    });
    return transformKeys<ParagraphAnalysisResponse>(response.data);
  },

  /**
   * Get Paragraph Context for Sentence Layer
   * 获取段落上下文供句子层使用
   */
  getContext: async (
    text: string,
    sectionContext?: Record<string, unknown>
  ): Promise<{
    paragraphs: Array<{
      index: number;
      role: string;
      text: string;
      sentenceIndices: number[];
      coherenceScore: number;
    }>;
  }> => {
    const response = await api.post('/paragraph/context', {
      text,
      section_context: sectionContext,
    });
    return transformKeys(response.data);
  },

  /**
   * Step 3.5: Paragraph Transition Analysis
   * 步骤 3.5：段落间过渡分析
   *
   * Analyzes transitions between adjacent paragraphs:
   * - Detects explicit connectors at paragraph openings
   * - Calculates semantic echo scores
   * - Identifies formulaic opener patterns
   */
  analyzeTransitions: async (
    text: string,
    paragraphs?: string[],
    sessionId?: string,
    sectionContext?: Record<string, unknown>
  ): Promise<ParagraphTransitionResponse> => {
    const response = await api.post('/paragraph/step3-5/transition', {
      text,
      paragraphs,
      session_id: sessionId,
      section_context: sectionContext,
    });
    return transformKeys<ParagraphTransitionResponse>(response.data);
  },
};

// ============================================
// Sentence Layer API (Layer 2)
// 句子层 API（第2层）
// ============================================
export const sentenceLayerApi = {
  // --------------------------------
  // New Sub-step APIs (Step 4.0 - 4.5)
  // 新子步骤API（步骤 4.0 - 4.5）
  // --------------------------------

  /**
   * Step 4.0: Sentence Identification & Labeling
   * 步骤 4.0：句子识别与标注
   *
   * Identifies all sentences and labels each with type, role, voice, opener.
   * 识别所有句子并标注类型、角色、语态、句首词。
   */
  identifySentences: async (
    text?: string,
    paragraphs?: string[],
    sessionId?: string
  ): Promise<SentenceIdentificationResponse> => {
    const response = await api.post('/sentence/step4-0/identify', {
      text,
      paragraphs,
      session_id: sessionId,
    });
    return transformKeys<SentenceIdentificationResponse>(response.data);
  },

  /**
   * Step 4.1: Sentence Pattern Analysis
   * 步骤 4.1：句式结构分析
   *
   * Analyzes sentence type distribution, opener repetition, voice balance.
   * 分析句式类型分布、句首重复、语态平衡。
   */
  analyzePatterns: async (
    text?: string,
    paragraphs?: string[],
    sessionId?: string
  ): Promise<PatternAnalysisResponse> => {
    const response = await api.post('/sentence/step4-1/pattern', {
      text,
      paragraphs,
      session_id: sessionId,
    });
    return transformKeys<PatternAnalysisResponse>(response.data);
  },

  /**
   * Step 4.2: In-Paragraph Length Analysis
   * 步骤 4.2：段内句长分析
   *
   * Analyzes sentence length CV within each paragraph.
   * 分析每个段落内的句长变异系数。
   */
  analyzeLength: async (
    text?: string,
    paragraphs?: string[],
    paragraphIndex?: number,
    sessionId?: string
  ): Promise<LengthAnalysisResponse> => {
    const response = await api.post('/sentence/step4-2/length', {
      text,
      paragraphs,
      paragraph_index: paragraphIndex,
      session_id: sessionId,
    });
    return transformKeys<LengthAnalysisResponse>(response.data);
  },

  /**
   * Step 4.3: Sentence Merge Suggestions
   * 步骤 4.3：句子合并建议
   *
   * Generates merge suggestions for a specific paragraph.
   * 为特定段落生成合并建议。
   */
  suggestMerges: async (
    paragraphText: string,
    paragraphIndex: number,
    maxMergeCount?: number,
    sessionId?: string
  ): Promise<MergeSuggestionResponse> => {
    const response = await api.post('/sentence/step4-3/merge', {
      paragraph_text: paragraphText,
      paragraph_index: paragraphIndex,
      max_merge_count: maxMergeCount || 2,
      session_id: sessionId,
    });
    return transformKeys<MergeSuggestionResponse>(response.data);
  },

  /**
   * Step 4.4: Connector Optimization
   * 步骤 4.4：连接词优化
   *
   * Analyzes and optimizes explicit connectors in a paragraph.
   * 分析并优化段落中的显性连接词。
   */
  optimizeConnectors: async (
    paragraphText: string,
    paragraphIndex: number,
    preserveConnectors?: string[],
    sessionId?: string
  ): Promise<ConnectorOptimizationResponse> => {
    const response = await api.post('/sentence/step4-4/connector', {
      paragraph_text: paragraphText,
      paragraph_index: paragraphIndex,
      preserve_connectors: preserveConnectors || [],
      session_id: sessionId,
    });
    return transformKeys<ConnectorOptimizationResponse>(response.data);
  },

  /**
   * Step 4.5: Pattern Diversification
   * 步骤 4.5：句式多样化
   *
   * Comprehensive sentence pattern diversification for a paragraph.
   * 对段落进行综合句式多样化处理。
   */
  diversifyPatterns: async (
    paragraphText: string,
    paragraphIndex: number,
    rewriteIntensity?: 'conservative' | 'moderate' | 'aggressive',
    targetPassiveRatio?: number,
    sessionId?: string
  ): Promise<DiversificationResponse> => {
    const response = await api.post('/sentence/step4-5/diversify', {
      paragraph_text: paragraphText,
      paragraph_index: paragraphIndex,
      rewrite_intensity: rewriteIntensity || 'moderate',
      target_passive_ratio: targetPassiveRatio,
      session_id: sessionId,
    });
    return transformKeys<DiversificationResponse>(response.data);
  },

  // --------------------------------
  // Paragraph Config APIs
  // 段落配置API
  // --------------------------------

  /**
   * Set paragraph processing configuration
   * 设置段落处理配置
   */
  setParagraphConfig: async (
    paragraphIndex: number,
    config: Partial<ParagraphProcessingConfig>,
    sessionId?: string
  ): Promise<{ status: string; paragraphIndex: number; config: ParagraphProcessingConfig }> => {
    const response = await api.post(`/sentence/paragraph/${paragraphIndex}/config`, config, {
      params: { session_id: sessionId },
    });
    return transformKeys(response.data);
  },

  /**
   * Get paragraph processing configuration
   * 获取段落处理配置
   */
  getParagraphConfig: async (
    paragraphIndex: number,
    sessionId?: string
  ): Promise<ParagraphProcessingConfig | { status: string; message: string }> => {
    const response = await api.get(`/sentence/paragraph/${paragraphIndex}/config`, {
      params: { session_id: sessionId },
    });
    return transformKeys(response.data);
  },

  /**
   * Get paragraph version history
   * 获取段落版本历史
   */
  getParagraphVersions: async (
    paragraphIndex: number,
    sessionId?: string
  ): Promise<{ paragraphIndex: number; currentVersion: number; versions: ParagraphVersion[] }> => {
    const response = await api.get(`/sentence/paragraph/${paragraphIndex}/versions`, {
      params: { session_id: sessionId },
    });
    return transformKeys(response.data);
  },

  /**
   * Revert paragraph to specific version
   * 将段落回退到指定版本
   */
  revertParagraph: async (
    paragraphIndex: number,
    targetVersion: number,
    sessionId?: string
  ): Promise<{ status: string; paragraphIndex: number; revertedTo: number; text: string }> => {
    const response = await api.post(`/sentence/paragraph/${paragraphIndex}/revert`, null, {
      params: { target_version: targetVersion, session_id: sessionId },
    });
    return transformKeys(response.data);
  },

  // --------------------------------
  // Batch Operation APIs
  // 批量操作API
  // --------------------------------

  /**
   * Batch set configuration for multiple paragraphs
   * 批量设置多个段落的配置
   */
  batchSetConfig: async (
    paragraphIndices: number[],
    config: Record<string, unknown>,
    sessionId?: string
  ): Promise<{ status: string; updatedParagraphs: number[] }> => {
    const response = await api.post('/sentence/batch/config', {
      paragraph_indices: paragraphIndices,
      config,
    }, {
      params: { session_id: sessionId },
    });
    return transformKeys(response.data);
  },

  /**
   * Batch lock/unlock paragraphs
   * 批量锁定/解锁段落
   */
  batchLock: async (
    paragraphIndices: number[],
    locked: boolean,
    sessionId?: string
  ): Promise<{ status: string; locked: boolean; updatedParagraphs: number[] }> => {
    const response = await api.post('/sentence/batch/lock', {
      paragraph_indices: paragraphIndices,
      locked,
    }, {
      params: { session_id: sessionId },
    });
    return transformKeys(response.data);
  },

  // --------------------------------
  // Legacy APIs (kept for backward compatibility)
  // 旧API（保持向后兼容）
  // --------------------------------

  /**
   * Legacy Step 4.1: Sentence Pattern Detection
   * 旧步骤 4.1：句式模式检测
   */
  analyzePattern: async (
    text: string,
    paragraphContext?: Record<string, unknown>
  ): Promise<SentenceAnalysisResponse> => {
    const response = await api.post('/sentence/pattern', {
      text,
      paragraph_context: paragraphContext,
    });
    return transformKeys<SentenceAnalysisResponse>(response.data);
  },

  /**
   * Legacy Step 4.2: Syntactic Void Detection
   * 旧步骤 4.2：句法空洞检测
   */
  analyzeVoid: async (
    text: string,
    paragraphContext?: Record<string, unknown>
  ): Promise<SentenceAnalysisResponse> => {
    const response = await api.post('/sentence/void', {
      text,
      paragraph_context: paragraphContext,
    });
    return transformKeys<SentenceAnalysisResponse>(response.data);
  },

  /**
   * Legacy Step 4.3: Sentence Role Classification
   * 旧步骤 4.3：句子角色分类
   */
  analyzeRole: async (
    text: string,
    paragraphContext?: Record<string, unknown>
  ): Promise<SentenceAnalysisResponse> => {
    const response = await api.post('/sentence/role', {
      text,
      paragraph_context: paragraphContext,
    });
    return transformKeys<SentenceAnalysisResponse>(response.data);
  },

  /**
   * Legacy Step 4.4: Sentence Polish Context (for rewriting)
   * 旧步骤 4.4：句子润色上下文（用于改写）
   */
  getPolishContext: async (
    text: string,
    sentenceIndex: number,
    paragraphContext?: Record<string, unknown>
  ): Promise<{
    sentenceText: string;
    paragraphText: string;
    sentenceRole: string;
    prevSentence?: string;
    nextSentence?: string;
    paragraphRole?: string;
    issues: DetectionIssue[];
  }> => {
    const response = await api.post('/sentence/polish-context', {
      text,
      sentence_index: sentenceIndex,
      paragraph_context: paragraphContext,
    });
    return transformKeys(response.data);
  },

  /**
   * Combined Sentence Analysis
   * 综合句子分析
   */
  analyze: async (
    text: string,
    paragraphContext?: Record<string, unknown>
  ): Promise<SentenceAnalysisResponse> => {
    const response = await api.post('/sentence/analyze', {
      text,
      paragraph_context: paragraphContext,
    });
    return transformKeys<SentenceAnalysisResponse>(response.data);
  },

  /**
   * Get Rewrite Context for a Sentence (Context-Critical)
   * 获取句子改写上下文（上下文关键）
   *
   * IMPORTANT: This endpoint provides full context for sentence rewriting.
   * 重要：此端点为句子改写提供完整上下文。
   */
  getRewriteContext: async (
    text: string,
    sentenceIndex: number,
    paragraphIndex: number
  ): Promise<RewriteContext> => {
    const response = await api.post('/sentence/rewrite-context', {
      text,
      sentence_index: sentenceIndex,
      paragraph_index: paragraphIndex,
    });
    return transformKeys<RewriteContext>(response.data);
  },

  /**
   * Get Sentence Context for Lexical Layer
   * 获取句子上下文供词汇层使用
   */
  getContext: async (
    text: string,
    paragraphContext?: Record<string, unknown>
  ): Promise<{
    sentences: Array<{
      index: number;
      paragraphIndex: number;
      text: string;
      role: string;
      length: number;
    }>;
  }> => {
    const response = await api.post('/sentence/context', {
      text,
      paragraph_context: paragraphContext,
    });
    return transformKeys(response.data);
  },
};

// ============================================
// Lexical Layer API (Layer 1)
// 词汇层 API（第1层）
// ============================================
export const lexicalLayerApi = {
  /**
   * Step 5.0: Lexical Context Preparation
   * 步骤 5.0：词汇环境准备
   */
  prepareContext: async (
    text: string,
    sessionId?: string,
    lockedTerms?: string[]
  ): Promise<LexicalContextResponse> => {
    const response = await api.post('../layer1/step5-0/prepare', {
      text,
      session_id: sessionId,
      locked_terms: lockedTerms,
    });
    return transformKeys<LexicalContextResponse>(response.data);
  },

  /**
   * Step 5.1: Fingerprint Detection
   * 步骤 5.1：AI指纹检测
   */
  detectFingerprints: async (
    text: string,
    sessionId?: string,
    lockedTerms?: string[]
  ): Promise<FingerprintDetectionResponse> => {
    const response = await api.post('../layer1/step5-1/analyze', {
      text,
      session_id: sessionId,
      locked_terms: lockedTerms,
    });
    return transformKeys<FingerprintDetectionResponse>(response.data);
  },

  /**
   * Step 5.2: Human Feature Analysis
   * 步骤 5.2：人类特征分析
   */
  analyzeHumanFeatures: async (
    text: string,
    sessionId?: string,
    lockedTerms?: string[]
  ): Promise<HumanFeatureResponse> => {
    const response = await api.post('../layer1/step5-2/analyze', {
      text,
      session_id: sessionId,
      locked_terms: lockedTerms,
    });
    return transformKeys<HumanFeatureResponse>(response.data);
  },

  /**
   * Step 5.3: Replacement Generation
   * 步骤 5.3：替换词生成
   */
  generateReplacements: async (
    text: string,
    sessionId?: string,
    lockedTerms?: string[]
  ): Promise<ReplacementGenerationResponse> => {
    const response = await api.post('../layer1/step5-3/analyze', {
      text,
      session_id: sessionId,
      locked_terms: lockedTerms,
    });
    return transformKeys<ReplacementGenerationResponse>(response.data);
  },

  /**
   * Step 5.4: Paragraph Rewriting Analysis
   * 步骤 5.4：段落级改写分析
   * Note: Uses substeps API at /api/v1/layer1
   */
  analyzeParagraphRewrite: async (
    text: string,
    sessionId?: string,
    lockedTerms?: string[]
  ): Promise<ParagraphRewriteResponse> => {
    const response = await api.post('../layer1/step5-4/analyze', {
      text,
      session_id: sessionId,
      locked_terms: lockedTerms,
    });
    return transformKeys<ParagraphRewriteResponse>(response.data);
  },

  /**
   * Step 5.5: Validation
   * 步骤 5.5：验证
   * Note: Uses substeps API at /api/v1/layer1
   */
  validate: async (
    text: string,
    sessionId?: string,
    lockedTerms?: string[]
  ): Promise<ValidationResponse> => {
    const response = await api.post('../layer1/step5-5/validate', {
      text,
      session_id: sessionId,
      locked_terms: lockedTerms,
    });
    return transformKeys<ValidationResponse>(response.data);
  },

  /**
   * Legacy: Combined Lexical Analysis
   * 旧版：综合词汇分析
   */
  analyze: async (
    text: string,
    sentences?: string[],
    sentenceContext?: Record<string, unknown>
  ): Promise<LexicalAnalysisResponse> => {
    const response = await api.post('/lexical/analyze', {
      text,
      sentences,
      sentence_context: sentenceContext,
    });
    return transformKeys<LexicalAnalysisResponse>(response.data);
  },

  /**
   * Legacy: Fingerprint Detection (old endpoint)
   * 旧版：指纹词检测（旧端点）
   */
  analyzeFingerprint: async (
    text: string,
    sentences?: string[]
  ): Promise<LexicalAnalysisResponse> => {
    const response = await api.post('/lexical/fingerprint', {
      text,
      sentences,
    });
    return transformKeys<LexicalAnalysisResponse>(response.data);
  },

  /**
   * Legacy: Get Replacement Suggestions
   * 旧版：获取替换建议
   */
  getReplacements: async (
    text: string,
    sentences?: string[]
  ): Promise<{
    replacementSuggestions: Record<string, string[]>;
    typeAWords: string[];
    typeBWords: string[];
    flaggedConnectors: string[];
    fingerprintDensity: number;
  }> => {
    const response = await api.post('/lexical/replacements', {
      text,
      sentences,
    });
    return transformKeys(response.data);
  },
};

// ============================================
// Pipeline API (Full Flow)
// 流水线 API（完整流程）
// ============================================
export const pipelineApi = {
  /**
   * Full Pipeline Analysis (All 5 Layers)
   * 全流水线分析（所有5层）
   *
   * Runs all layers in sequence with context passing:
   * Document → Section → Paragraph → Sentence → Lexical
   */
  analyzeFull: async (request: PipelineAnalysisRequest): Promise<PipelineAnalysisResponse> => {
    const response = await api.post('/pipeline/full', {
      text: request.text,
      layers: request.layers || ['document', 'section', 'paragraph', 'sentence', 'lexical'],
      stop_on_low_risk: request.stopOnLowRisk ?? false,
      include_context: request.includeContext ?? true,
    });
    return transformKeys<PipelineAnalysisResponse>(response.data);
  },

  /**
   * Partial Pipeline Analysis (Selected Layers)
   * 部分流水线分析（选定层）
   */
  analyzePartial: async (request: PipelineAnalysisRequest): Promise<PipelineAnalysisResponse> => {
    const response = await api.post('/pipeline/partial', {
      text: request.text,
      layers: request.layers || ['document'],
      stop_on_low_risk: request.stopOnLowRisk ?? false,
      include_context: request.includeContext ?? true,
    });
    return transformKeys<PipelineAnalysisResponse>(response.data);
  },

  /**
   * Get Available Layers Information
   * 获取可用层级信息
   */
  getLayers: async (): Promise<{
    layers: Array<{
      level: LayerLevel;
      name: string;
      steps: Array<{ id: string; name: string }>;
      weight: number;
      note?: string;
    }>;
    defaultOrder: LayerLevel[];
    contextFlow: string;
  }> => {
    const response = await api.get('/pipeline/layers');
    return transformKeys(response.data);
  },
};

// ============================================
// Add auth token interceptor
// 添加认证令牌拦截器
// ============================================
api.interceptors.request.use((config) => {
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
  (error) => {
    if (error.response) {
      const data = error.response.data as { detail?: string };
      throw new Error(data.detail || 'An error occurred');
    }
    throw error;
  }
);

export default {
  termLock: termLockApi,
  document: documentLayerApi,
  section: sectionLayerApi,
  paragraph: paragraphLayerApi,
  sentence: sentenceLayerApi,
  lexical: lexicalLayerApi,
  pipeline: pipelineApi,
};
