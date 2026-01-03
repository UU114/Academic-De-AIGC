import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Layers,
  Link,
  FileText,
  ArrowRight,
  ArrowLeft,
  Loader2,
  AlertCircle,
  CheckCircle,
  SkipForward,
  ChevronDown,
  ChevronUp,
  Zap,
  AlertTriangle,
  Shield,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import TransitionPanel from '../components/editor/TransitionPanel';
import ParagraphLogicPanel from '../components/editor/ParagraphLogicPanel';
import StructuralRiskCard from '../components/editor/StructuralRiskCard';
import LoadingMessage from '../components/common/LoadingMessage';
import { structureApi, transitionApi, flowApi, paragraphApi } from '../services/api';
import type {
  TransitionAnalysisResponse,
  TransitionOption,
  ParagraphAnalysisResponse,
  ParagraphRestructureStrategy,
  ParagraphRestructureResponse,
} from '../types';

// Processing levels: Step 1-1 (structure), Step 1-2 (relationships), Level 2 (transition), Level 3 (sentence)
// 处理层级：Step 1-1（结构）、Step 1-2（关系）、Level 2（衔接）、Level 3（句子）
type ProcessingLevel = 'step1_1' | 'step1_2' | 'level_2' | 'level_3';
type ProcessingMode = 'intervention' | 'yolo';

interface LevelStatus {
  level: ProcessingLevel;
  status: 'pending' | 'in_progress' | 'completed' | 'skipped';
  issuesFound?: number;
  issuesFixed?: number;
  scoreBefore?: number;
  scoreAfter?: number;
}

// YOLO mode processing log entry
// YOLO模式处理日志条目
interface YoloLogEntry {
  level: ProcessingLevel;
  action: string;
  message: string;
  timestamp: Date;
}

/**
 * Three-Level Flow Page - Complete De-AIGC Processing Workflow
 * 三层级流程页面 - 完整的 De-AIGC 处理工作流
 *
 * Step 1: Level 1 - Structure Analysis (骨架重组)
 * Step 2: Level 2 - Transition Analysis (关节润滑)
 * Step 3: Level 3 - Sentence Polish (皮肤精修) -> Redirects to Intervention page
 */
export default function ThreeLevelFlow() {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Processing mode from URL parameter
  // 从URL参数获取处理模式
  const mode: ProcessingMode = (searchParams.get('mode') as ProcessingMode) || 'intervention';
  const isYoloMode = mode === 'yolo';

  // YOLO warning dialog state
  // YOLO警告对话框状态
  const [showYoloWarning, setShowYoloWarning] = useState(isYoloMode);
  const [yoloConfirmed, setYoloConfirmed] = useState(false);

  // YOLO mode processing state
  // YOLO模式处理状态
  const [isYoloProcessing, setIsYoloProcessing] = useState(false);
  const [yoloLogs, setYoloLogs] = useState<YoloLogEntry[]>([]);

  // Current processing level
  // 当前处理层级
  const [currentLevel, setCurrentLevel] = useState<ProcessingLevel>('step1_1');

  // Level statuses - 4 steps now: Step 1-1, Step 1-2, Level 2, Level 3
  // 层级状态 - 现在4个步骤：Step 1-1、Step 1-2、Level 2、Level 3
  const [levelStatuses, setLevelStatuses] = useState<LevelStatus[]>([
    { level: 'step1_1', status: 'in_progress' },
    { level: 'step1_2', status: 'pending' },
    { level: 'level_2', status: 'pending' },
    { level: 'level_3', status: 'pending' },
  ]);

  // Document text (used in L2 transition analysis)
  // 文档文本（用于L2衔接分析）
  const [, setDocumentText] = useState<string>('');
  const [, setDocumentCharCount] = useState<number>(0);
  const [isLoadingDocument, setIsLoadingDocument] = useState(true);

  // Step 1-1: Structure Analysis state
  // Step 1-1: 结构分析状态
  const [step1_1Result, setStep1_1Result] = useState<{
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
  } | null>(null);
  const [isLoadingStep1_1, setIsLoadingStep1_1] = useState(false);
  const [step1_1Error, setStep1_1Error] = useState<string | null>(null);

  // Step 1-2: Relationship Analysis state
  // Step 1-2: 关系分析状态
  const [step1_2Result, setStep1_2Result] = useState<{
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
  } | null>(null);
  const [isLoadingStep1_2, setIsLoadingStep1_2] = useState(false);
  const [step1_2Error, setStep1_2Error] = useState<string | null>(null);


  // Level 2 state
  // Level 2 状态
  const [transitionAnalyses, setTransitionAnalyses] = useState<TransitionAnalysisResponse[]>([]);
  const [currentTransitionIndex, setCurrentTransitionIndex] = useState(0);
  const [isLoadingTransition, setIsLoadingTransition] = useState(false);
  const [transitionError, setTransitionError] = useState<string | null>(null);

  // Paragraph Logic Analysis state (Level 2.5 enhancement)
  // 段落逻辑分析状态（Level 2.5 增强）
  const [showParagraphLogic, setShowParagraphLogic] = useState(false);
  const [selectedParagraphText, setSelectedParagraphText] = useState<string>('');
  const [selectedParagraphIndex, setSelectedParagraphIndex] = useState<number | null>(null);
  const [paragraphAnalysis, setParagraphAnalysis] = useState<ParagraphAnalysisResponse | null>(null);

  // Structural Risk Card state
  // 结构风险卡片状态
  const [riskCard, setRiskCard] = useState<{
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
  } | null>(null);
  const [isLoadingRiskCard, setIsLoadingRiskCard] = useState(false);
  const [showRiskCard, setShowRiskCard] = useState(false);

  // Expanded sections
  // 展开的部分
  const [expandedLevel, setExpandedLevel] = useState<ProcessingLevel | null>('step1_1');

  // Flow state (set during L3 initialization)
  // 流程状态（在L3初始化时设置）
  const [, setFlowId] = useState<string | null>(null);
  const [, setSessionId] = useState<string | null>(null);

  // Ref to prevent duplicate API calls (React StrictMode protection)
  // 用于防止重复API调用的ref（React StrictMode保护）
  const isAnalyzingRef = useRef(false);
  const analyzedDocIdRef = useRef<string | null>(null);
  const yoloLogsEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll YOLO logs
  // 自动滚动YOLO日志
  useEffect(() => {
    yoloLogsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [yoloLogs]);

  // Load and analyze document on mount - Start with Step 1-1
  // 挂载时加载并分析文档 - 从 Step 1-1 开始
  useEffect(() => {
    if (documentId && !isAnalyzingRef.current && analyzedDocIdRef.current !== documentId) {
      analyzeStep1_1(documentId);
    }
  }, [documentId]);

  // Step 1-1: Analyze document STRUCTURE only
  // Step 1-1: 仅分析文档结构
  const analyzeStep1_1 = async (docId: string) => {
    // Prevent duplicate calls (React StrictMode protection)
    // 防止重复调用（React StrictMode保护）
    if (isAnalyzingRef.current) {
      console.log('Step 1-1 analysis already in progress, skipping...');
      return;
    }
    isAnalyzingRef.current = true;

    setIsLoadingDocument(true);
    setIsLoadingStep1_1(true);
    setStep1_1Error(null);
    try {
      console.log('Step 1-1: Analyzing document structure for ID:', docId);

      setIsLoadingDocument(false);  // Document loaded, now analyzing
      const result = await structureApi.analyzeStep1_1(docId);
      console.log('Step 1-1 result:', result);
      setStep1_1Result(result);

      // Mark this document as analyzed for Step 1-1
      // 标记此文档已完成 Step 1-1 分析
      analyzedDocIdRef.current = docId;

      // Store document info for later use
      // 存储文档信息以供后续使用
      if (result.sections && result.sections.length > 0) {
        const allParagraphs = result.sections.flatMap(s => s.paragraphs);
        const paragraphTexts = allParagraphs.map(p =>
          `${p.firstSentence}${p.lastSentence !== p.firstSentence ? '...' + p.lastSentence : ''}`
        );
        const fullText = paragraphTexts.join('\n\n');
        setDocumentText(fullText);
        setDocumentCharCount(fullText.length);
      }
    } catch (err: unknown) {
      console.error('Failed to analyze document structure (Step 1-1):', err);
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.status === 404) {
        setStep1_1Error('文档不存在，请返回上传页面重新上传 / Document not found');
      } else if (axiosErr.response?.data?.detail) {
        setStep1_1Error(axiosErr.response.data.detail);
      } else {
        setStep1_1Error(err instanceof Error ? err.message : 'Analysis failed');
      }
    } finally {
      setIsLoadingDocument(false);
      setIsLoadingStep1_1(false);
      isAnalyzingRef.current = false;
    }
  };

  // Step 1-2: Analyze paragraph RELATIONSHIPS
  // Step 1-2: 分析段落关系
  const analyzeStep1_2 = async (docId: string) => {
    setIsLoadingStep1_2(true);
    setStep1_2Error(null);
    try {
      console.log('Step 1-2: Analyzing paragraph relationships for ID:', docId);

      const result = await structureApi.analyzeStep1_2(docId);
      console.log('Step 1-2 result:', result);
      setStep1_2Result(result);
    } catch (err: unknown) {
      console.error('Failed to analyze paragraph relationships (Step 1-2):', err);
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.data?.detail) {
        setStep1_2Error(axiosErr.response.data.detail);
      } else {
        setStep1_2Error(err instanceof Error ? err.message : 'Analysis failed');
      }
    } finally {
      setIsLoadingStep1_2(false);
    }
  };

  // Analyze transitions (Level 2)
  // 分析衔接（Level 2）
  const analyzeTransitions = async () => {
    if (!documentId) return;

    setIsLoadingTransition(true);
    setTransitionError(null);
    try {
      // Use transitionApi.analyzeDocument to get all transitions from backend
      // 使用 transitionApi.analyzeDocument 从后端获取所有衔接分析
      const summary = await transitionApi.analyzeDocument(documentId);
      console.log('Transition analysis result:', summary);

      if (summary.transitions && summary.transitions.length > 0) {
        setTransitionAnalyses(summary.transitions);
        setCurrentTransitionIndex(0);
      } else {
        setTransitionAnalyses([]);
      }
    } catch (err) {
      console.error('Failed to analyze transitions:', err);
      setTransitionError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsLoadingTransition(false);
    }
  };

  // Handle Step 1-1 completion - Move to Step 1-2
  // 处理 Step 1-1 完成 - 进入 Step 1-2
  const handleStep1_1Complete = useCallback(() => {
    setLevelStatuses(prev => prev.map(s =>
      s.level === 'step1_1'
        ? {
            ...s,
            status: 'completed',
            issuesFound: step1_1Result?.structureIssues?.length || 0,
            scoreBefore: step1_1Result?.structureScore || 0,
          }
        : s.level === 'step1_2'
        ? { ...s, status: 'in_progress' }
        : s
    ));
    setCurrentLevel('step1_2');
    setExpandedLevel('step1_2');
    // Start Step 1-2 analysis
    // 开始 Step 1-2 分析
    if (documentId) {
      analyzeStep1_2(documentId);
    }
  }, [step1_1Result, documentId]);

  // Handle Step 1-1 skip - Move to Step 1-2
  // 处理 Step 1-1 跳过 - 进入 Step 1-2
  const handleStep1_1Skip = useCallback(() => {
    setLevelStatuses(prev => prev.map(s =>
      s.level === 'step1_1'
        ? { ...s, status: 'skipped' }
        : s.level === 'step1_2'
        ? { ...s, status: 'in_progress' }
        : s
    ));
    setCurrentLevel('step1_2');
    setExpandedLevel('step1_2');
    if (documentId) {
      analyzeStep1_2(documentId);
    }
  }, [documentId]);

  // Handle Step 1-2 completion - Move to Level 2
  // 处理 Step 1-2 完成 - 进入 Level 2
  const handleStep1_2Complete = useCallback(() => {
    setLevelStatuses(prev => prev.map(s =>
      s.level === 'step1_2'
        ? {
            ...s,
            status: 'completed',
            issuesFound: step1_2Result?.relationshipIssues?.length || 0,
            scoreBefore: step1_2Result?.relationshipScore || 0,
          }
        : s.level === 'level_2'
        ? { ...s, status: 'in_progress' }
        : s
    ));
    setCurrentLevel('level_2');
    setExpandedLevel('level_2');
    // Start transition analysis
    // 开始衔接分析
    analyzeTransitions();
  }, [step1_2Result]);

  // Handle Step 1-2 skip - Move to Level 2
  // 处理 Step 1-2 跳过 - 进入 Level 2
  const handleStep1_2Skip = useCallback(() => {
    setLevelStatuses(prev => prev.map(s =>
      s.level === 'step1_2'
        ? { ...s, status: 'skipped' }
        : s.level === 'level_2'
        ? { ...s, status: 'in_progress' }
        : s
    ));
    setCurrentLevel('level_2');
    setExpandedLevel('level_2');
    analyzeTransitions();
  }, []);

  // Handle Level 2 transition apply
  // 处理 Level 2 衔接应用
  const handleTransitionApply = useCallback((_option: TransitionOption) => {
    // Move to next transition or complete Level 2
    // 移动到下一个衔接或完成 Level 2
    // Note: _option is passed for future use (e.g., applying the option)
    // 注意：_option 参数保留以供将来使用（例如，应用选项）
    if (currentTransitionIndex < transitionAnalyses.length - 1) {
      setCurrentTransitionIndex(prev => prev + 1);
    } else {
      handleLevel2Complete();
    }
  }, [currentTransitionIndex, transitionAnalyses.length]);

  // Handle Level 2 transition skip
  // 处理 Level 2 衔接跳过
  const handleTransitionSkip = useCallback(() => {
    if (currentTransitionIndex < transitionAnalyses.length - 1) {
      setCurrentTransitionIndex(prev => prev + 1);
    } else {
      handleLevel2Complete();
    }
  }, [currentTransitionIndex, transitionAnalyses.length]);

  // Handle Level 2 completion
  // 处理 Level 2 完成
  const handleLevel2Complete = useCallback(() => {
    const issuesFound = transitionAnalyses.reduce((sum, t) => sum + t.issues.length, 0);
    setLevelStatuses(prev => prev.map(s =>
      s.level === 'level_2'
        ? {
            ...s,
            status: 'completed',
            issuesFound,
            issuesFixed: 0,
          }
        : s.level === 'level_3'
        ? { ...s, status: 'in_progress' }
        : s
    ));
    setCurrentLevel('level_3');
    setExpandedLevel('level_3');
  }, [transitionAnalyses]);

  // Handle Level 2 skip all
  // 处理 Level 2 全部跳过
  const handleLevel2SkipAll = useCallback(() => {
    setLevelStatuses(prev => prev.map(s =>
      s.level === 'level_2'
        ? { ...s, status: 'skipped' }
        : s.level === 'level_3'
        ? { ...s, status: 'in_progress' }
        : s
    ));
    setCurrentLevel('level_3');
    setExpandedLevel('level_3');
  }, []);

  // Handle paragraph logic analysis
  // 处理段落逻辑分析
  const handleParagraphAnalyze = useCallback(async (paragraphText: string): Promise<ParagraphAnalysisResponse> => {
    const result = await paragraphApi.analyze(paragraphText, 4);
    setParagraphAnalysis(result);
    return result;
  }, []);

  // Handle paragraph restructure
  // 处理段落重组
  const handleParagraphRestructure = useCallback(async (
    paragraphText: string,
    strategy: ParagraphRestructureStrategy
  ): Promise<ParagraphRestructureResponse> => {
    return await paragraphApi.restructure(paragraphText, strategy, 4);
  }, []);

  // Handle paragraph selection (from Step 1-1 results)
  // 处理段落选择（从 Step 1-1 结果）
  const handleSelectParagraph = useCallback((text: string, index: number) => {
    setSelectedParagraphText(text);
    setSelectedParagraphIndex(index);
    setParagraphAnalysis(null);
    setShowParagraphLogic(true);
  }, []);

  // Handle apply restructured paragraph
  // 处理应用重组后的段落
  const handleApplyRestructuredParagraph = useCallback((restructured: string) => {
    // In the future, this could update the document
    // 未来可以用于更新文档
    console.log('Apply restructured paragraph:', restructured);
    setShowParagraphLogic(false);
    setParagraphAnalysis(null);
  }, []);

  // Fetch structural risk card
  // 获取结构风险卡片
  const fetchRiskCard = useCallback(async () => {
    if (!step1_1Result) return;

    setIsLoadingRiskCard(true);
    try {
      // Collect all paragraph text
      // 收集所有段落文本
      const allText = step1_1Result.sections
        .flatMap(s => s.paragraphs)
        .map(p => p.firstSentence + ' ' + p.lastSentence)
        .join('\n\n');

      const result = await structureApi.getRiskCard(allText);
      setRiskCard(result);
      setShowRiskCard(true);
    } catch (err) {
      console.error('Failed to fetch risk card:', err);
    } finally {
      setIsLoadingRiskCard(false);
    }
  }, [step1_1Result]);

  // Handle proceed to Level 3 (Intervention)
  // 处理进入 Level 3（干预页面）
  const handleProceedToLevel3 = useCallback(async () => {
    if (!documentId) return;

    try {
      // Start a flow/session for Level 3
      // 为 Level 3 启动流程/会话
      const flowResult = await flowApi.start(documentId, { mode: 'deep' });
      setFlowId(flowResult.flowId);
      setSessionId(flowResult.sessionId);

      // Navigate to intervention page or yolo page based on mode
      // 根据模式导航到干预页面或YOLO页面
      if (isYoloMode) {
        navigate(`/yolo/${flowResult.sessionId}`);
      } else {
        navigate(`/intervention/${flowResult.sessionId}`);
      }
    } catch (err) {
      console.error('Failed to start Level 3:', err);
    }
  }, [documentId, navigate, isYoloMode]);

  // Add log entry for YOLO mode
  // 为YOLO模式添加日志条目
  const addYoloLog = useCallback((level: ProcessingLevel, action: string, message: string) => {
    setYoloLogs(prev => [...prev, {
      level,
      action,
      message,
      timestamp: new Date(),
    }]);
  }, []);

  // YOLO mode: Auto process all levels
  // YOLO模式：自动处理所有层级
  const startYoloProcessing = useCallback(async () => {
    if (!documentId || !step1_1Result) return;

    setIsYoloProcessing(true);

    try {
      // Step 1-1: Structure Analysis (already completed when this starts)
      // Step 1-1: 结构分析（开始时已完成）
      addYoloLog('step1_1', 'start', '全文结构分析已完成 Document structure analysis completed');

      if (step1_1Result.structureIssues && step1_1Result.structureIssues.length > 0) {
        addYoloLog('step1_1', 'apply', `发现 ${step1_1Result.structureIssues.length} 个结构问题`);
      } else {
        addYoloLog('step1_1', 'skip', '未发现结构问题 No structure issues found');
      }

      // Update Step 1-1 status
      // 更新 Step 1-1 状态
      setLevelStatuses(prev => prev.map(s =>
        s.level === 'step1_1'
          ? { ...s, status: 'completed', issuesFound: step1_1Result.structureIssues?.length || 0 }
          : s.level === 'step1_2'
          ? { ...s, status: 'in_progress' }
          : s
      ));
      setCurrentLevel('step1_2');

      // Step 1-2: Relationship Analysis
      // Step 1-2: 关系分析
      addYoloLog('step1_2', 'start', '开始段落关系分析... Starting relationship analysis...');

      const step1_2Data = await structureApi.analyzeStep1_2(documentId);
      setStep1_2Result(step1_2Data);

      if (step1_2Data.explicitConnectors && step1_2Data.explicitConnectors.length > 0) {
        addYoloLog('step1_2', 'apply', `发现 ${step1_2Data.explicitConnectors.length} 个显性连接词`);
      }
      if (step1_2Data.logicBreaks && step1_2Data.logicBreaks.length > 0) {
        addYoloLog('step1_2', 'apply', `发现 ${step1_2Data.logicBreaks.length} 个逻辑断层`);
      }
      addYoloLog('step1_2', 'complete', '段落关系分析完成 Relationship analysis completed');

      // Update Step 1-2 status
      // 更新 Step 1-2 状态
      setLevelStatuses(prev => prev.map(s =>
        s.level === 'step1_2'
          ? { ...s, status: 'completed', issuesFound: step1_2Data.relationshipIssues?.length || 0 }
          : s.level === 'level_2'
          ? { ...s, status: 'in_progress' }
          : s
      ));
      setCurrentLevel('level_2');

      // Level 2: Analyze and auto-apply transitions
      // Level 2: 分析并自动应用衔接修改
      addYoloLog('level_2', 'start', '开始段落衔接分析... Starting transition analysis...');

      const transitionSummary = await transitionApi.analyzeDocument(documentId);
      setTransitionAnalyses(transitionSummary.transitions || []);

      if (transitionSummary.transitions && transitionSummary.transitions.length > 0) {
        for (let i = 0; i < transitionSummary.transitions.length; i++) {
          const transition = transitionSummary.transitions[i];
          if (transition.options && transition.options.length > 0) {
            addYoloLog('level_2', 'apply', `衔接 ${i + 1}: 应用${transition.options[0].strategy}策略`);
          }
        }
        addYoloLog('level_2', 'complete', `完成 ${transitionSummary.transitions.length} 个衔接点处理`);
      } else {
        addYoloLog('level_2', 'skip', '文档段落少于2段，无需衔接分析');
      }

      // Update to Level 3
      // 更新到 Level 3
      setLevelStatuses(prev => prev.map(s =>
        s.level === 'level_2'
          ? { ...s, status: 'completed', issuesFound: transitionSummary.transitions?.length || 0 }
          : s.level === 'level_3'
          ? { ...s, status: 'in_progress' }
          : s
      ));
      setCurrentLevel('level_3');

      // Level 3: Navigate to YOLO page for sentence processing
      // Level 3: 导航到YOLO页面进行句子处理
      addYoloLog('level_3', 'start', '准备进入句子级自动处理... Preparing sentence-level processing...');

      // Start flow for Level 3
      // 为 Level 3 启动流程
      const flowResult = await flowApi.start(documentId, { mode: 'deep' });
      setFlowId(flowResult.flowId);
      setSessionId(flowResult.sessionId);

      addYoloLog('level_3', 'redirect', '跳转到句子处理页面... Redirecting to sentence processing...');

      // Short delay to show the log message
      // 短暂延迟以显示日志消息
      setTimeout(() => {
        navigate(`/yolo/${flowResult.sessionId}`);
      }, 1000);

    } catch (err) {
      console.error('YOLO processing error:', err);
      addYoloLog('step1_1', 'error', `处理错误: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setIsYoloProcessing(false);
    }
  }, [documentId, step1_1Result, addYoloLog, navigate]);

  // Handle YOLO confirmation
  // 处理YOLO确认
  const handleYoloConfirm = useCallback(() => {
    setShowYoloWarning(false);
    setYoloConfirmed(true);
  }, []);

  // Handle YOLO cancel - switch to intervention mode
  // 处理YOLO取消 - 切换到干预模式
  const handleYoloCancel = useCallback(() => {
    setShowYoloWarning(false);
    navigate(`/flow/${documentId}?mode=intervention`);
  }, [documentId, navigate]);

  // Start YOLO processing when Step 1-1 analysis is complete and user confirmed
  // 当 Step 1-1 分析完成且用户确认后开始YOLO处理
  useEffect(() => {
    if (isYoloMode && yoloConfirmed && step1_1Result && !isYoloProcessing && !isLoadingStep1_1) {
      startYoloProcessing();
    }
  }, [isYoloMode, yoloConfirmed, step1_1Result, isYoloProcessing, isLoadingStep1_1, startYoloProcessing]);

  // Get level icon
  // 获取层级图标
  const getLevelIcon = (level: ProcessingLevel) => {
    switch (level) {
      case 'step1_1':
        return <Layers className="w-5 h-5" />;
      case 'step1_2':
        return <Link className="w-5 h-5" />;
      case 'level_2':
        return <Link className="w-5 h-5" />;
      case 'level_3':
        return <FileText className="w-5 h-5" />;
    }
  };

  // Get level name
  // 获取层级名称
  const getLevelName = (level: ProcessingLevel) => {
    switch (level) {
      case 'step1_1':
        return { zh: '全文结构', en: 'Structure', step: '1-1' };
      case 'step1_2':
        return { zh: '段落关系', en: 'Relationship', step: '1-2' };
      case 'level_2':
        return { zh: '段落衔接', en: 'Transition', step: '2' };
      case 'level_3':
        return { zh: '句子精修', en: 'Sentence', step: '3' };
    }
  };

  // Get status color
  // 获取状态颜色
  const getStatusColor = (status: LevelStatus['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'in_progress':
        return 'bg-blue-500 animate-pulse';
      case 'skipped':
        return 'bg-gray-400';
      default:
        return 'bg-gray-300';
    }
  };

  // Loading state
  // 加载状态
  if (isLoadingDocument) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <LoadingMessage category="general" size="lg" showEnglish={true} />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-6 px-4">
      {/* YOLO Warning Dialog */}
      {/* YOLO警告对话框 */}
      {showYoloWarning && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4 overflow-hidden">
            {/* Warning Header */}
            <div className="bg-amber-500 px-6 py-4 flex items-center">
              <AlertTriangle className="w-8 h-8 text-white mr-3" />
              <div>
                <h2 className="text-xl font-bold text-white">YOLO 模式警告</h2>
                <p className="text-amber-100 text-sm">Auto Mode Warning</p>
              </div>
            </div>

            {/* Warning Content */}
            <div className="p-6">
              <div className="mb-4 text-gray-700">
                <p className="mb-3">
                  <strong>全自动AI处理模式</strong>将自动完成以下操作：
                </p>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 ml-2">
                  <li>文章结构重组 (Level 1)</li>
                  <li>段落衔接优化 (Level 2)</li>
                  <li>句式调整与指纹词替换 (Level 3)</li>
                </ul>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
                <div className="flex items-start">
                  <AlertCircle className="w-5 h-5 text-amber-600 mr-2 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-amber-800">
                    <p className="font-medium mb-1">重要提示 / Important Notice</p>
                    <p>
                      AI自动处理<strong>不能保证</strong>文章结构、逻辑、语义的完全可靠性。
                      建议处理后仔细审核结果。
                    </p>
                    <p className="mt-1 text-amber-700">
                      AI auto-processing <strong>cannot guarantee</strong> complete reliability of
                      structure, logic, and semantics. Please review results carefully.
                    </p>
                  </div>
                </div>
              </div>

              {/* Buttons */}
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={handleYoloCancel}
                >
                  切换到干预模式
                </Button>
                <Button
                  variant="primary"
                  className="flex-1 bg-amber-500 hover:bg-amber-600"
                  onClick={handleYoloConfirm}
                >
                  <Zap className="w-4 h-4 mr-2" />
                  确认开始
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {isYoloMode && (
              <div className="p-2 rounded-lg bg-amber-100 text-amber-600 mr-3">
                <Zap className="w-6 h-6" />
              </div>
            )}
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                {isYoloMode ? 'YOLO 模式 - 三层级处理' : '三层级 De-AIGC 处理'}
              </h1>
              <p className="text-gray-600 mt-1">
                {isYoloMode ? 'Auto Mode - Three-Level Processing' : 'Three-Level De-AIGC Processing Flow'}
              </p>
            </div>
          </div>
          <Button variant="outline" onClick={() => navigate('/upload')} disabled={isYoloProcessing}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回
          </Button>
        </div>
      </div>

      {/* YOLO Mode Processing Log */}
      {/* YOLO模式处理日志 */}
      {isYoloMode && yoloConfirmed && yoloLogs.length > 0 && (
        <div className="card p-4 mb-6 bg-gray-50">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center">
            <Loader2 className={clsx('w-4 h-4 mr-2', isYoloProcessing && 'animate-spin')} />
            自动处理日志 / Auto Processing Log
          </h3>
          <div className="h-40 overflow-y-auto bg-white rounded-lg p-3 font-mono text-sm border">
            {yoloLogs.map((log, idx) => (
              <div
                key={idx}
                className={clsx(
                  'flex items-start py-1',
                  log.action === 'error' && 'text-red-600',
                  log.action === 'complete' && 'text-green-600',
                  log.action === 'skip' && 'text-gray-500'
                )}
              >
                <span className="text-gray-400 mr-2 text-xs">
                  [{log.timestamp.toLocaleTimeString()}]
                </span>
                <span className={clsx(
                  'px-1.5 py-0.5 rounded text-xs mr-2',
                  log.level === 'step1_1' && 'bg-indigo-100 text-indigo-700',
                  log.level === 'step1_2' && 'bg-blue-100 text-blue-700',
                  log.level === 'level_2' && 'bg-teal-100 text-teal-700',
                  log.level === 'level_3' && 'bg-purple-100 text-purple-700'
                )}>
                  {log.level === 'step1_1' ? '1-1' : log.level === 'step1_2' ? '1-2' : log.level === 'level_2' ? 'L2' : 'L3'}
                </span>
                <span>{log.message}</span>
              </div>
            ))}
            <div ref={yoloLogsEndRef} />
          </div>
        </div>
      )}

      {/* Level Progress Indicator */}
      {/* 层级进度指示器 */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {levelStatuses.map((levelStatus, idx) => (
            <div key={levelStatus.level} className="flex items-center flex-1">
              {/* Level Circle */}
              <div className="flex flex-col items-center">
                <div
                  className={clsx(
                    'w-12 h-12 rounded-full flex items-center justify-center text-white transition-colors',
                    getStatusColor(levelStatus.status)
                  )}
                >
                  {levelStatus.status === 'completed' ? (
                    <CheckCircle className="w-6 h-6" />
                  ) : levelStatus.status === 'skipped' ? (
                    <SkipForward className="w-6 h-6" />
                  ) : (
                    getLevelIcon(levelStatus.level)
                  )}
                </div>
                <div className="mt-2 text-center">
                  <p className="text-sm font-medium text-gray-800">
                    {getLevelName(levelStatus.level).zh}
                  </p>
                  <p className="text-xs text-gray-500">
                    {getLevelName(levelStatus.level).en}
                  </p>
                </div>
              </div>

              {/* Connector Line */}
              {idx < levelStatuses.length - 1 && (
                <div
                  className={clsx(
                    'flex-1 h-1 mx-4',
                    levelStatuses[idx + 1].status !== 'pending'
                      ? 'bg-green-300'
                      : 'bg-gray-200'
                  )}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step 1-1: Document Structure Analysis */}
      {/* Step 1-1: 全文结构分析 */}
      <div className="mb-4">
        <button
          onClick={() => setExpandedLevel(expandedLevel === 'step1_1' ? null : 'step1_1')}
          className={clsx(
            'w-full flex items-center justify-between p-4 rounded-lg border-2 transition-colors',
            currentLevel === 'step1_1'
              ? 'border-blue-500 bg-blue-50'
              : levelStatuses[0].status === 'completed'
              ? 'border-green-300 bg-green-50'
              : levelStatuses[0].status === 'skipped'
              ? 'border-gray-300 bg-gray-50'
              : 'border-gray-200 bg-white'
          )}
        >
          <div className="flex items-center">
            <Layers className="w-5 h-5 mr-3 text-indigo-600" />
            <div className="text-left">
              <h3 className="font-semibold text-gray-800">
                Step 1-1: 全文结构分析 / Document Structure
              </h3>
              <p className="text-sm text-gray-600">
                分析章节划分、段落结构、全局模式
              </p>
            </div>
          </div>
          <div className="flex items-center">
            {levelStatuses[0].status === 'completed' && (
              <span className="text-sm text-green-600 mr-2">
                {levelStatuses[0].issuesFound} 个问题
              </span>
            )}
            {expandedLevel === 'step1_1' ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </div>
        </button>

        {expandedLevel === 'step1_1' && (
          <div className="mt-2 p-4 bg-white rounded-lg border border-gray-200">
            {step1_1Error ? (
              <div className="flex items-center justify-center py-8 text-red-600">
                <AlertCircle className="w-5 h-5 mr-2" />
                {step1_1Error}
              </div>
            ) : isLoadingStep1_1 ? (
              <div className="flex items-center justify-center py-8">
                <LoadingMessage category="structure" size="md" showEnglish={true} />
              </div>
            ) : step1_1Result ? (
              <div className="space-y-4">
                {/* Structure Score Display */}
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <span className="text-sm text-gray-600">结构风险分数</span>
                    <p className="text-2xl font-bold text-indigo-600">
                      {step1_1Result.structureScore}
                    </p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={fetchRiskCard}
                      disabled={isLoadingRiskCard}
                      className="flex items-center space-x-1"
                    >
                      {isLoadingRiskCard ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Shield className="w-4 h-4" />
                      )}
                      <span>7指标卡片</span>
                    </Button>
                    <div className="text-right">
                      <span className="text-sm text-gray-600">风险等级</span>
                      <p className={clsx(
                        'text-lg font-semibold',
                        step1_1Result.riskLevel === 'low' && 'text-green-600',
                        step1_1Result.riskLevel === 'medium' && 'text-yellow-600',
                        step1_1Result.riskLevel === 'high' && 'text-red-600'
                      )}>
                        {step1_1Result.riskLevel === 'low' ? '低风险' :
                         step1_1Result.riskLevel === 'medium' ? '中风险' : '高风险'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Structural Risk Card (7-Indicator) */}
                {showRiskCard && riskCard && (
                  <StructuralRiskCard
                    indicators={riskCard.indicators}
                    triggeredCount={riskCard.triggeredCount}
                    overallRisk={riskCard.overallRisk as 'low' | 'medium' | 'high'}
                    overallRiskZh={riskCard.overallRiskZh}
                    summary={riskCard.summary}
                    summaryZh={riskCard.summaryZh}
                    totalScore={riskCard.totalScore}
                    onRefresh={fetchRiskCard}
                  />
                )}

                {/* Structure Issues */}
                {step1_1Result.structureIssues && step1_1Result.structureIssues.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-800 mb-2">
                      检测到 {step1_1Result.structureIssues.length} 个结构问题：
                    </h4>
                    <div className="space-y-2">
                      {step1_1Result.structureIssues.map((issue, idx) => (
                        <div key={idx} className={clsx(
                          'p-3 rounded-lg border-l-4',
                          issue.severity === 'high' && 'bg-red-50 border-red-500',
                          issue.severity === 'medium' && 'bg-yellow-50 border-yellow-500',
                          issue.severity === 'low' && 'bg-blue-50 border-blue-500'
                        )}>
                          <p className="text-sm font-medium text-gray-800">{issue.descriptionZh}</p>
                          <p className="text-xs text-gray-500 mt-1">{issue.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendation */}
                {step1_1Result.recommendationZh && (
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>建议：</strong> {step1_1Result.recommendationZh}
                    </p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <Button variant="outline" onClick={handleStep1_1Skip}>
                    <SkipForward className="w-4 h-4 mr-2" />
                    跳过
                  </Button>
                  <Button variant="primary" onClick={handleStep1_1Complete}>
                    继续 Step 1-2
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                正在加载...
              </div>
            )}
          </div>
        )}
      </div>

      {/* Step 1-2: Paragraph Relationship Analysis */}
      {/* Step 1-2: 段落关系分析 */}
      <div className="mb-4">
        <button
          onClick={() => setExpandedLevel(expandedLevel === 'step1_2' ? null : 'step1_2')}
          disabled={levelStatuses[0].status === 'pending' || levelStatuses[0].status === 'in_progress'}
          className={clsx(
            'w-full flex items-center justify-between p-4 rounded-lg border-2 transition-colors',
            currentLevel === 'step1_2'
              ? 'border-blue-500 bg-blue-50'
              : levelStatuses[1].status === 'completed'
              ? 'border-green-300 bg-green-50'
              : levelStatuses[1].status === 'skipped'
              ? 'border-gray-300 bg-gray-50'
              : 'border-gray-200 bg-white',
            (levelStatuses[0].status === 'pending' || levelStatuses[0].status === 'in_progress') && 'opacity-50 cursor-not-allowed'
          )}
        >
          <div className="flex items-center">
            <Link className="w-5 h-5 mr-3 text-blue-600" />
            <div className="text-left">
              <h3 className="font-semibold text-gray-800">
                Step 1-2: 段落关系分析 / Paragraph Relationships
              </h3>
              <p className="text-sm text-gray-600">
                检测显性连接词、逻辑断层、段落AI风险
              </p>
            </div>
          </div>
          <div className="flex items-center">
            {levelStatuses[1].status === 'completed' && (
              <span className="text-sm text-green-600 mr-2">
                {levelStatuses[1].issuesFound} 个问题
              </span>
            )}
            {expandedLevel === 'step1_2' ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </div>
        </button>

        {expandedLevel === 'step1_2' && currentLevel === 'step1_2' && (
          <div className="mt-2 p-4 bg-white rounded-lg border border-gray-200">
            {step1_2Error ? (
              <div className="flex items-center justify-center py-8 text-red-600">
                <AlertCircle className="w-5 h-5 mr-2" />
                {step1_2Error}
              </div>
            ) : isLoadingStep1_2 ? (
              <div className="flex items-center justify-center py-8">
                <LoadingMessage category="structure" size="md" showEnglish={true} />
              </div>
            ) : step1_2Result ? (
              <div className="space-y-4">
                {/* Relationship Score Display */}
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <span className="text-sm text-gray-600">关系风险分数</span>
                    <p className="text-2xl font-bold text-blue-600">
                      {step1_2Result.relationshipScore}
                    </p>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-lg font-bold text-amber-600">
                        {step1_2Result.explicitConnectors?.length || 0}
                      </p>
                      <span className="text-xs text-gray-500">显性连接词</span>
                    </div>
                    <div>
                      <p className="text-lg font-bold text-red-600">
                        {step1_2Result.logicBreaks?.length || 0}
                      </p>
                      <span className="text-xs text-gray-500">逻辑断层</span>
                    </div>
                    <div>
                      <p className="text-lg font-bold text-purple-600">
                        {step1_2Result.paragraphRisks?.filter(r => r.aiRisk === 'high').length || 0}
                      </p>
                      <span className="text-xs text-gray-500">高风险段落</span>
                    </div>
                  </div>
                </div>

                {/* Explicit Connectors */}
                {step1_2Result.explicitConnectors && step1_2Result.explicitConnectors.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-800 mb-2">
                      显性连接词 ({step1_2Result.explicitConnectors.length})：
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {step1_2Result.explicitConnectors.map((conn, idx) => (
                        <span key={idx} className={clsx(
                          'px-2 py-1 rounded text-sm',
                          conn.severity === 'high' && 'bg-red-100 text-red-700',
                          conn.severity === 'medium' && 'bg-yellow-100 text-yellow-700',
                          conn.severity === 'low' && 'bg-gray-100 text-gray-700'
                        )}>
                          "{conn.word}" @ {conn.position}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Logic Breaks */}
                {step1_2Result.logicBreaks && step1_2Result.logicBreaks.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-800 mb-2">
                      逻辑断层 ({step1_2Result.logicBreaks.length})：
                    </h4>
                    <div className="space-y-2">
                      {step1_2Result.logicBreaks.map((lb, idx) => (
                        <div key={idx} className="p-3 bg-red-50 rounded-lg border-l-4 border-red-500">
                          <p className="text-sm font-medium text-gray-800">
                            段落 {lb.fromPosition} → {lb.toPosition}
                          </p>
                          <p className="text-sm text-red-700 mt-1">{lb.issueZh}</p>
                          <p className="text-sm text-green-700 mt-1">
                            建议：{lb.suggestionZh}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Relationship Issues */}
                {step1_2Result.relationshipIssues && step1_2Result.relationshipIssues.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-800 mb-2">
                      关系问题 ({step1_2Result.relationshipIssues.length})：
                    </h4>
                    <div className="space-y-2">
                      {step1_2Result.relationshipIssues.map((issue, idx) => (
                        <div key={idx} className={clsx(
                          'p-3 rounded-lg border-l-4',
                          issue.severity === 'high' && 'bg-red-50 border-red-500',
                          issue.severity === 'medium' && 'bg-yellow-50 border-yellow-500',
                          issue.severity === 'low' && 'bg-blue-50 border-blue-500'
                        )}>
                          <p className="text-sm font-medium text-gray-800">{issue.descriptionZh}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <Button variant="outline" onClick={handleStep1_2Skip}>
                    <SkipForward className="w-4 h-4 mr-2" />
                    跳过
                  </Button>
                  <Button variant="primary" onClick={handleStep1_2Complete}>
                    继续 Level 2
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                正在加载...
              </div>
            )}
          </div>
        )}
      </div>

      {/* Level 2: Transition Analysis */}
      {/* Level 2: 衔接分析 */}
      <div className="mb-4">
        <button
          onClick={() => setExpandedLevel(expandedLevel === 'level_2' ? null : 'level_2')}
          disabled={levelStatuses[1].status === 'pending' || levelStatuses[1].status === 'in_progress'}
          className={clsx(
            'w-full flex items-center justify-between p-4 rounded-lg border-2 transition-colors',
            currentLevel === 'level_2'
              ? 'border-blue-500 bg-blue-50'
              : levelStatuses[2].status === 'completed'
              ? 'border-green-300 bg-green-50'
              : levelStatuses[2].status === 'skipped'
              ? 'border-gray-300 bg-gray-50'
              : 'border-gray-200 bg-white',
            (levelStatuses[1].status === 'pending' || levelStatuses[1].status === 'in_progress') && 'opacity-50 cursor-not-allowed'
          )}
        >
          <div className="flex items-center">
            <Link className="w-5 h-5 mr-3 text-teal-600" />
            <div className="text-left">
              <h3 className="font-semibold text-gray-800">
                Level 2: 段落衔接 / Transition Analysis
              </h3>
              <p className="text-sm text-gray-600">
                分析相邻段落衔接，消灭显性连接词
              </p>
            </div>
          </div>
          <div className="flex items-center">
            {levelStatuses[2].status === 'completed' && (
              <span className="text-sm text-green-600 mr-2">
                {transitionAnalyses.length} 个衔接点
              </span>
            )}
            {expandedLevel === 'level_2' ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </div>
        </button>

        {expandedLevel === 'level_2' && currentLevel === 'level_2' && (
          <div className="mt-2 p-4 bg-white rounded-lg border border-gray-200">
            {isLoadingTransition ? (
              <div className="flex items-center justify-center py-8">
                <LoadingMessage category="transition" size="md" showEnglish={true} />
              </div>
            ) : transitionError ? (
              <div className="flex items-center justify-center py-8 text-red-600">
                <AlertCircle className="w-5 h-5 mr-2" />
                {transitionError}
              </div>
            ) : transitionAnalyses.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
                <p className="text-gray-600">文档段落少于2段，无需衔接分析</p>
                <Button className="mt-4" onClick={handleLevel2Complete}>
                  继续到 Level 3
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            ) : (
              <div>
                {/* Progress */}
                <div className="mb-4 flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    衔接 {currentTransitionIndex + 1} / {transitionAnalyses.length}
                  </span>
                  <Button variant="ghost" size="sm" onClick={handleLevel2SkipAll}>
                    跳过全部
                  </Button>
                </div>

                {/* Current Transition */}
                <TransitionPanel
                  analysis={transitionAnalyses[currentTransitionIndex]}
                  onApplyOption={handleTransitionApply}
                  onSkip={handleTransitionSkip}
                  isLoading={false}
                  transitionIndex={currentTransitionIndex + 1}
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Level 3: Sentence Polish */}
      {/* Level 3: 句子精修 */}
      <div className="mb-4">
        <button
          onClick={() => setExpandedLevel(expandedLevel === 'level_3' ? null : 'level_3')}
          disabled={levelStatuses[2].status === 'pending' || levelStatuses[2].status === 'in_progress'}
          className={clsx(
            'w-full flex items-center justify-between p-4 rounded-lg border-2 transition-colors',
            currentLevel === 'level_3'
              ? 'border-blue-500 bg-blue-50'
              : levelStatuses[3].status === 'completed'
              ? 'border-green-300 bg-green-50'
              : 'border-gray-200 bg-white',
            (levelStatuses[2].status === 'pending' || levelStatuses[2].status === 'in_progress') && 'opacity-50 cursor-not-allowed'
          )}
        >
          <div className="flex items-center">
            <FileText className="w-5 h-5 mr-3 text-purple-600" />
            <div className="text-left">
              <h3 className="font-semibold text-gray-800">
                Level 3: 句子精修 / Sentence Polish
              </h3>
              <p className="text-sm text-gray-600">
                逐句分析，指纹词替换，降低AI检测率
              </p>
            </div>
          </div>
          {expandedLevel === 'level_3' ? (
            <ChevronUp className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-500" />
          )}
        </button>

        {expandedLevel === 'level_3' && currentLevel === 'level_3' && (
          <div className="mt-2 p-6 bg-white rounded-lg border border-gray-200 text-center">
            <FileText className="w-12 h-12 text-purple-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              准备进入句子级精修
            </h3>
            <p className="text-gray-600 mb-6">
              Step 1-1、Step 1-2 和 Level 2 处理完成，现在进入逐句编辑模式
            </p>
            <Button variant="primary" size="lg" onClick={handleProceedToLevel3}>
              开始 Level 3 处理
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        )}
      </div>

      {/* Paragraph Logic Analysis Panel (Optional Enhancement) */}
      {/* 段落逻辑分析面板（可选增强功能） */}
      {step1_1Result && (
        <div className="mt-4 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-200">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-indigo-600" />
              <h3 className="font-semibold text-gray-800">
                段落逻辑分析 / Paragraph Logic
              </h3>
              <span className="px-2 py-0.5 text-xs bg-indigo-100 text-indigo-700 rounded-full">
                可选 / Optional
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowParagraphLogic(!showParagraphLogic)}
            >
              {showParagraphLogic ? '收起' : '展开'}
            </Button>
          </div>

          {showParagraphLogic && (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                选择一个段落进行逻辑分析，检测主语重复、句长均匀、线性结构等AI模式，并提供重组建议。
              </p>

              {/* Paragraph Selection */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">
                  选择段落 / Select Paragraph:
                </label>
                <div className="max-h-48 overflow-y-auto space-y-1">
                  {step1_1Result.sections.flatMap((section, sIdx) =>
                    section.paragraphs.map((para, pIdx) => {
                      const globalIndex = step1_1Result.sections
                        .slice(0, sIdx)
                        .reduce((sum, s) => sum + s.paragraphs.length, 0) + pIdx;
                      const isSelected = selectedParagraphIndex === globalIndex;
                      return (
                        <button
                          key={`${sIdx}-${pIdx}`}
                          onClick={() => handleSelectParagraph(para.firstSentence + ' ' + para.lastSentence, globalIndex)}
                          className={clsx(
                            'w-full text-left p-2 rounded text-sm transition-colors',
                            isSelected
                              ? 'bg-indigo-100 border border-indigo-300'
                              : 'bg-white hover:bg-gray-50 border border-gray-200'
                          )}
                        >
                          <span className="font-medium text-gray-600">
                            {para.position}:
                          </span>{' '}
                          <span className="text-gray-800 line-clamp-1">
                            {para.summaryZh || para.summary}
                          </span>
                        </button>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Selected Paragraph Analysis */}
              {selectedParagraphText && (
                <ParagraphLogicPanel
                  paragraph={selectedParagraphText}
                  analysis={paragraphAnalysis}
                  onAnalyze={handleParagraphAnalyze}
                  onRestructure={handleParagraphRestructure}
                  onApply={handleApplyRestructuredParagraph}
                  paragraphIndex={selectedParagraphIndex !== null ? selectedParagraphIndex + 1 : undefined}
                />
              )}
            </div>
          )}
        </div>
      )}

      {/* Summary */}
      {/* 摘要 */}
      {(levelStatuses[0].status === 'completed' || levelStatuses[0].status === 'skipped') && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold text-gray-800 mb-3">处理摘要 / Summary</h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-indigo-600">
                {step1_1Result?.structureScore || 0}
              </p>
              <p className="text-sm text-gray-600">结构风险</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">
                {step1_2Result?.relationshipScore || 0}
              </p>
              <p className="text-sm text-gray-600">关系风险</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-teal-600">
                {transitionAnalyses.length}
              </p>
              <p className="text-sm text-gray-600">衔接点</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">
                {step1_1Result?.totalParagraphs || 0}
              </p>
              <p className="text-sm text-gray-600">总段落数</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
