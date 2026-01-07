import { useState, useEffect } from 'react';
import {
  FileText,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Users,
  Ruler,
  Link2,
  User,
  Loader2,
  Wand2,
  Copy,
  Check,
  RotateCcw,
  ArrowRight,
  Target,
  BarChart2,
  Lightbulb,
  AlertCircle,
  BookOpen,
} from 'lucide-react';
import { clsx } from 'clsx';
import type {
  ParagraphAnalysisResponse,
  ParagraphRestructureStrategy,
  ParagraphRestructureResponse,
} from '../../types';
import Button from '../common/Button';
import InfoTooltip from '../common/InfoTooltip';
import { paragraphApi } from '../../services/api';

/**
 * Sentence role color mapping
 * 句子角色颜色映射
 */
const ROLE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  CLAIM: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-300' },
  EVIDENCE: { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-300' },
  ANALYSIS: { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-300' },
  CRITIQUE: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-300' },
  CONCESSION: { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-300' },
  SYNTHESIS: { bg: 'bg-teal-100', text: 'text-teal-700', border: 'border-teal-300' },
  TRANSITION: { bg: 'bg-gray-100', text: 'text-gray-700', border: 'border-gray-300' },
  CONTEXT: { bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-300' },
  IMPLICATION: { bg: 'bg-indigo-100', text: 'text-indigo-700', border: 'border-indigo-300' },
  ELABORATION: { bg: 'bg-pink-100', text: 'text-pink-700', border: 'border-pink-300' },
  UNKNOWN: { bg: 'bg-gray-50', text: 'text-gray-500', border: 'border-gray-200' },
};

/**
 * Type definitions for advanced logic framework analysis result
 * 高级逻辑框架分析结果的类型定义
 */
interface LogicFrameworkResult {
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
}

interface ParagraphLogicPanelProps {
  paragraph: string;
  analysis?: ParagraphAnalysisResponse | null;
  onAnalyze?: (paragraph: string) => Promise<ParagraphAnalysisResponse>;
  onRestructure?: (
    paragraph: string,
    strategy: ParagraphRestructureStrategy
  ) => Promise<ParagraphRestructureResponse>;
  onApply?: (restructured: string) => void;
  isLoading?: boolean;
  toneLevel?: number;  // Reserved for future use
  paragraphIndex?: number;  // 1-based index for display
}

/**
 * Paragraph Logic Analysis Panel - Level 3 Enhancement
 * 段落逻辑分析面板 - Level 3 增强
 *
 * Analyzes and restructures paragraph-level logic patterns including:
 * - Subject diversity
 * - Sentence length variation
 * - Linear structure detection
 * - First-person overuse
 */
export default function ParagraphLogicPanel({
  paragraph,
  analysis: initialAnalysis,
  onAnalyze,
  onRestructure,
  onApply,
  isLoading = false,
  toneLevel: _toneLevel = 4,
  paragraphIndex,
}: ParagraphLogicPanelProps) {
  const [analysis, setAnalysis] = useState<ParagraphAnalysisResponse | null>(
    initialAnalysis || null
  );
  const [showDetails, setShowDetails] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<ParagraphRestructureStrategy | null>(null);
  const [restructureResult, setRestructureResult] = useState<ParagraphRestructureResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isRestructuring, setIsRestructuring] = useState(false);
  const [copied, setCopied] = useState(false);

  // Advanced logic framework analysis state
  // 高级逻辑框架分析状态
  const [activeTab, setActiveTab] = useState<'basic' | 'advanced'>('basic');
  const [advancedAnalysis, setAdvancedAnalysis] = useState<LogicFrameworkResult | null>(null);
  const [isAnalyzingAdvanced, setIsAnalyzingAdvanced] = useState(false);
  const [advancedError, setAdvancedError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['roles', 'framework', 'suggestions'])
  );

  // Update analysis when initialAnalysis changes
  // 当 initialAnalysis 变化时更新分析
  useEffect(() => {
    if (initialAnalysis) {
      setAnalysis(initialAnalysis);
    }
  }, [initialAnalysis]);

  // Issue type icon mapping
  // 问题类型图标映射
  const getIssueIcon = (type: string) => {
    switch (type) {
      case 'subject_repetition':
        return <Users className="w-4 h-4" />;
      case 'uniform_length':
        return <Ruler className="w-4 h-4" />;
      case 'linear_structure':
      case 'connector_overuse':
        return <Link2 className="w-4 h-4" />;
      case 'first_person_overuse':
        return <User className="w-4 h-4" />;
      default:
        return <AlertTriangle className="w-4 h-4" />;
    }
  };

  // Issue type color mapping
  // 问题类型颜色映射
  const getIssueColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-50 border-red-200 text-red-700';
      case 'medium':
        return 'bg-amber-50 border-amber-200 text-amber-700';
      default:
        return 'bg-blue-50 border-blue-200 text-blue-700';
    }
  };

  // Strategy info mapping
  // 策略信息映射
  const strategyInfo: Record<
    ParagraphRestructureStrategy,
    { name: string; nameZh: string; icon: React.ReactNode; color: string }
  > = {
    ani: {
      name: 'ANI Structure',
      nameZh: '断言-细微-深意',
      icon: <ArrowRight className="w-4 h-4" />,
      color: 'bg-purple-50 border-purple-200 text-purple-700',
    },
    subject_diversity: {
      name: 'Subject Diversity',
      nameZh: '主语多样性',
      icon: <Users className="w-4 h-4" />,
      color: 'bg-blue-50 border-blue-200 text-blue-700',
    },
    implicit_connector: {
      name: 'Implicit Connector',
      nameZh: '隐性连接',
      icon: <Link2 className="w-4 h-4" />,
      color: 'bg-green-50 border-green-200 text-green-700',
    },
    rhythm: {
      name: 'Rhythm Variation',
      nameZh: '节奏变化',
      icon: <Ruler className="w-4 h-4" />,
      color: 'bg-amber-50 border-amber-200 text-amber-700',
    },
    citation_entanglement: {
      name: 'Citation Style',
      nameZh: '引用句法纠缠',
      icon: <FileText className="w-4 h-4" />,
      color: 'bg-teal-50 border-teal-200 text-teal-700',
    },
    all: {
      name: 'All Strategies',
      nameZh: '综合策略',
      icon: <Wand2 className="w-4 h-4" />,
      color: 'bg-indigo-50 border-indigo-200 text-indigo-700',
    },
  };

  // Handle analyze
  // 处理分析
  const handleAnalyze = async () => {
    if (!onAnalyze || !paragraph.trim()) return;

    setIsAnalyzing(true);
    try {
      const result = await onAnalyze(paragraph);
      setAnalysis(result);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Handle restructure
  // 处理重组
  const handleRestructure = async (strategy: ParagraphRestructureStrategy) => {
    if (!onRestructure || !paragraph.trim()) return;

    setSelectedStrategy(strategy);
    setIsRestructuring(true);
    try {
      const result = await onRestructure(paragraph, strategy);
      setRestructureResult(result);
    } catch (error) {
      console.error('Restructure failed:', error);
    } finally {
      setIsRestructuring(false);
    }
  };

  // Handle copy
  // 处理复制
  const handleCopy = async () => {
    if (restructureResult?.restructured) {
      await navigator.clipboard.writeText(restructureResult.restructured);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Handle apply
  // 处理应用
  const handleApply = () => {
    if (restructureResult?.restructured && onApply) {
      onApply(restructureResult.restructured);
      setRestructureResult(null);
      setSelectedStrategy(null);
    }
  };

  // Handle reset
  // 处理重置
  const handleReset = () => {
    setRestructureResult(null);
    setSelectedStrategy(null);
  };

  // Handle advanced logic framework analysis
  // 处理高级逻辑框架分析
  const handleAdvancedAnalysis = async () => {
    if (!paragraph.trim()) return;

    setIsAnalyzingAdvanced(true);
    setAdvancedError(null);

    try {
      const result = await paragraphApi.analyzeLogicFramework(paragraph);
      setAdvancedAnalysis(result);
    } catch (error) {
      console.error('Advanced logic framework analysis failed:', error);
      setAdvancedError(error instanceof Error ? error.message : 'Analysis failed');
    } finally {
      setIsAnalyzingAdvanced(false);
    }
  };

  // Toggle section expansion
  // 切换章节展开
  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  // Get burstiness level color
  // 获取爆发度级别颜色
  const getBurstinessColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'very_low':
      case 'low':
        return 'text-red-600';
      case 'medium':
        return 'text-yellow-600';
      case 'high':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  // Get logic structure badge
  // 获取逻辑结构徽章
  const getLogicStructureBadge = (structure: string) => {
    switch (structure) {
      case 'linear':
        return (
          <span className="px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-700">
            Linear / 线性结构
          </span>
        );
      case 'mixed':
        return (
          <span className="px-2 py-0.5 text-xs rounded-full bg-amber-100 text-amber-700">
            Mixed / 混合结构
          </span>
        );
      case 'varied':
        return (
          <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700">
            Varied / 多样结构
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
            {structure}
          </span>
        );
    }
  };

  // Render metrics
  // 渲染指标
  const renderMetrics = () => {
    if (!analysis) return null;

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <div className="p-2 rounded-lg bg-gray-50">
          <div className="text-gray-500 text-xs">Subject Diversity</div>
          <div className="text-gray-500 text-xs">主语多样性</div>
          <div className={clsx(
            'font-semibold',
            analysis.subjectDiversityScore >= 0.7 ? 'text-green-600' :
            analysis.subjectDiversityScore >= 0.4 ? 'text-amber-600' : 'text-red-600'
          )}>
            {(analysis.subjectDiversityScore * 100).toFixed(0)}%
          </div>
        </div>

        <div className="p-2 rounded-lg bg-gray-50">
          <div className="text-gray-500 text-xs">Length Variation</div>
          <div className="text-gray-500 text-xs">长度变化</div>
          <div className={clsx(
            'font-semibold',
            analysis.lengthVariationCv >= 0.3 ? 'text-green-600' :
            analysis.lengthVariationCv >= 0.2 ? 'text-amber-600' : 'text-red-600'
          )}>
            CV: {analysis.lengthVariationCv.toFixed(2)}
          </div>
        </div>

        <div className="p-2 rounded-lg bg-gray-50">
          <div className="text-gray-500 text-xs">First Person</div>
          <div className="text-gray-500 text-xs">第一人称</div>
          <div className={clsx(
            'font-semibold',
            analysis.firstPersonRatio <= 0.3 ? 'text-green-600' :
            analysis.firstPersonRatio <= 0.5 ? 'text-amber-600' : 'text-red-600'
          )}>
            {(analysis.firstPersonRatio * 100).toFixed(0)}%
          </div>
        </div>

        <div className="p-2 rounded-lg bg-gray-50">
          <div className="text-gray-500 text-xs">Connector Density</div>
          <div className="text-gray-500 text-xs">连接词密度</div>
          <div className={clsx(
            'font-semibold',
            analysis.connectorDensity <= 0.2 ? 'text-green-600' :
            analysis.connectorDensity <= 0.4 ? 'text-amber-600' : 'text-red-600'
          )}>
            {(analysis.connectorDensity * 100).toFixed(0)}%
          </div>
        </div>
      </div>
    );
  };

  // Render issues
  // 渲染问题
  const renderIssues = () => {
    if (!analysis?.issues.length) {
      return (
        <div className="flex items-center space-x-2 text-green-600 py-2">
          <CheckCircle className="w-4 h-4" />
          <span className="text-sm">No logic issues detected / 未检测到逻辑问题</span>
        </div>
      );
    }

    return (
      <div className="space-y-2">
        {analysis.issues.map((issue, index) => (
          <div
            key={index}
            className={clsx(
              'p-3 rounded-lg border',
              getIssueColor(issue.severity)
            )}
          >
            <div className="flex items-start space-x-2">
              <div className="mt-0.5">{getIssueIcon(issue.type)}</div>
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-sm capitalize">
                    {issue.type.replace(/_/g, ' ')}
                  </span>
                  <span className={clsx(
                    'px-1.5 py-0.5 text-xs rounded',
                    issue.severity === 'high' ? 'bg-red-200' :
                    issue.severity === 'medium' ? 'bg-amber-200' : 'bg-blue-200'
                  )}>
                    {issue.severity}
                  </span>
                </div>
                <p className="text-sm mt-1">{issue.description}</p>
                <p className="text-xs text-gray-500 mt-0.5">{issue.descriptionZh}</p>
                {showDetails && (
                  <div className="mt-2 p-2 rounded bg-white/50 text-xs">
                    <div className="font-medium">Suggestion:</div>
                    <div>{issue.suggestion}</div>
                    <div className="text-gray-500 mt-1">{issue.suggestionZh}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Render restructure options
  // 渲染重组选项
  const renderRestructureOptions = () => {
    if (!analysis) return null;

    // Determine which strategies to suggest based on issues
    // 根据问题确定推荐哪些策略
    const suggestedStrategies: ParagraphRestructureStrategy[] = [];
    if (analysis.hasLinearStructure) suggestedStrategies.push('ani');
    if (analysis.hasSubjectRepetition) suggestedStrategies.push('subject_diversity');
    if (analysis.connectorDensity > 0.3) suggestedStrategies.push('implicit_connector');
    if (analysis.lengthVariationCv < 0.25) suggestedStrategies.push('rhythm');
    // Check for citation pattern issues
    // 检查引用模式问题
    if (analysis.issues.some(i => i.type === 'citation_pattern')) {
      suggestedStrategies.push('citation_entanglement');
    }
    if (analysis.issues.length >= 2) suggestedStrategies.push('all');

    const strategies: ParagraphRestructureStrategy[] = [
      'ani',
      'subject_diversity',
      'implicit_connector',
      'rhythm',
      'citation_entanglement',
      'all',
    ];

    return (
      <div className="space-y-3">
        <div className="text-sm font-medium text-gray-700">
          Restructure Strategies / 重组策略
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
          {strategies.map((strategy) => {
            const info = strategyInfo[strategy];
            const isSuggested = suggestedStrategies.includes(strategy);
            const isSelected = selectedStrategy === strategy;

            return (
              <button
                key={strategy}
                onClick={() => handleRestructure(strategy)}
                disabled={isRestructuring}
                className={clsx(
                  'p-3 rounded-lg border text-left transition-all',
                  isSelected
                    ? 'ring-2 ring-indigo-500 border-indigo-300'
                    : isSuggested
                    ? info.color + ' border-2'
                    : 'bg-gray-50 border-gray-200 hover:bg-gray-100',
                  isRestructuring && 'opacity-50 cursor-not-allowed'
                )}
              >
                <div className="flex items-center space-x-2">
                  {info.icon}
                  <span className="font-medium text-sm">{info.name}</span>
                  {isSuggested && (
                    <span className="px-1.5 py-0.5 text-xs rounded bg-indigo-100 text-indigo-700">
                      Suggested
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-500 mt-1">{info.nameZh}</div>
              </button>
            );
          })}
        </div>
      </div>
    );
  };

  // Render advanced analysis
  // 渲染高级分析
  const renderAdvancedAnalysis = () => {
    if (!advancedAnalysis) {
      return (
        <div className="text-center py-6">
          <BookOpen className="w-12 h-12 text-purple-300 mx-auto mb-3" />
          <p className="text-sm text-gray-500 mb-4">
            分析段落内句子的逻辑角色和框架结构
            <br />
            Analyze sentence roles and logic framework
          </p>
          <Button
            variant="primary"
            onClick={handleAdvancedAnalysis}
            disabled={isAnalyzingAdvanced || !paragraph.trim()}
            className="flex items-center space-x-2 mx-auto"
          >
            {isAnalyzingAdvanced ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Target className="w-4 h-4" />
            )}
            <span>开始分析 / Analyze</span>
          </Button>
          {advancedError && (
            <div className="mt-3 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
              <AlertCircle className="w-4 h-4 inline mr-1" />
              {advancedError}
            </div>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {/* Overall Assessment */}
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              AI 风险评分 / AI Risk Score
            </span>
            <span
              className={clsx(
                'px-2 py-1 rounded text-sm font-medium',
                advancedAnalysis.overallAssessment.aiRiskScore > 60
                  ? 'bg-red-100 text-red-700'
                  : advancedAnalysis.overallAssessment.aiRiskScore > 30
                  ? 'bg-orange-100 text-orange-700'
                  : 'bg-green-100 text-green-700'
              )}
            >
              {advancedAnalysis.overallAssessment.aiRiskScore}%
            </span>
          </div>
          <p className="text-sm text-gray-600">{advancedAnalysis.overallAssessment.summaryZh}</p>
        </div>

        {/* Sentence Roles Section */}
        <div className="border rounded-lg">
          <button
            onClick={() => toggleSection('roles')}
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50"
          >
            <div className="flex items-center space-x-2">
              <Target className="w-4 h-4 text-blue-600" />
              <span className="font-medium">句子角色分析 / Sentence Roles</span>
            </div>
            {expandedSections.has('roles') ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>

          {expandedSections.has('roles') && (
            <div className="p-3 border-t space-y-2">
              {advancedAnalysis.sentenceRoles.map((role, idx) => {
                const colors = ROLE_COLORS[role.role] || ROLE_COLORS.UNKNOWN;
                return (
                  <div
                    key={idx}
                    className={clsx(
                      'p-3 rounded-lg border',
                      colors.bg,
                      colors.border
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className={clsx('text-xs font-medium', colors.text)}>
                        [{role.role}] {role.roleZh}
                      </span>
                      <span className="text-xs text-gray-400">
                        置信度: {(role.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-700">
                      {advancedAnalysis.sentences[idx]}
                    </p>
                    {role.brief && (
                      <p className="text-xs text-gray-500 mt-1 italic">{role.brief}</p>
                    )}
                  </div>
                );
              })}

              {/* Role Distribution */}
              {Object.keys(advancedAnalysis.roleDistribution).length > 0 && (
                <div className="mt-3 pt-3 border-t">
                  <p className="text-xs text-gray-500 mb-2">角色分布 / Distribution:</p>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(advancedAnalysis.roleDistribution).map(([role, count]) => {
                      const colors = ROLE_COLORS[role] || ROLE_COLORS.UNKNOWN;
                      return (
                        <span
                          key={role}
                          className={clsx(
                            'px-2 py-1 rounded text-xs',
                            colors.bg,
                            colors.text
                          )}
                        >
                          {role}: {count}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Logic Framework Section */}
        <div className="border rounded-lg">
          <button
            onClick={() => toggleSection('framework')}
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50"
          >
            <div className="flex items-center space-x-2">
              <BarChart2 className="w-4 h-4 text-purple-600" />
              <span className="font-medium">逻辑框架 / Logic Framework</span>
            </div>
            {expandedSections.has('framework') ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>

          {expandedSections.has('framework') && (
            <div className="p-3 border-t space-y-3">
              {/* Framework Pattern */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">框架模式:</span>
                <span
                  className={clsx(
                    'px-2 py-1 rounded text-sm',
                    advancedAnalysis.logicFramework.isAiLike
                      ? 'bg-red-100 text-red-700'
                      : 'bg-green-100 text-green-700'
                  )}
                >
                  {advancedAnalysis.logicFramework.patternZh}
                  {advancedAnalysis.logicFramework.isAiLike && (
                    <AlertTriangle className="w-3 h-3 inline ml-1" />
                  )}
                </span>
              </div>

              <p className="text-sm text-gray-600">{advancedAnalysis.logicFramework.descriptionZh}</p>

              {/* Burstiness Analysis */}
              <div className="pt-3 border-t">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">爆发度 (Burstiness):</span>
                  <span
                    className={clsx(
                      'text-sm font-medium',
                      getBurstinessColor(advancedAnalysis.burstinessAnalysis.burstinessLevel)
                    )}
                  >
                    {advancedAnalysis.burstinessAnalysis.burstinessZh}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs text-gray-500">
                  <div>平均长度: {advancedAnalysis.burstinessAnalysis.meanLength.toFixed(1)}</div>
                  <div>标准差: {advancedAnalysis.burstinessAnalysis.stdDev.toFixed(2)}</div>
                  <div>CV: {advancedAnalysis.burstinessAnalysis.cv.toFixed(2)}</div>
                </div>

                {/* Sentence length visualization */}
                <div className="mt-2 flex items-end space-x-1 h-12">
                  {advancedAnalysis.burstinessAnalysis.sentenceLengths.map((len, idx) => (
                    <div
                      key={idx}
                      className={clsx(
                        'flex-1 rounded-t',
                        idx === advancedAnalysis.burstinessAnalysis.longestSentence.index
                          ? 'bg-purple-500'
                          : idx === advancedAnalysis.burstinessAnalysis.shortestSentence.index
                          ? 'bg-orange-400'
                          : 'bg-gray-300'
                      )}
                      style={{
                        height: `${Math.min(100, (len / advancedAnalysis.burstinessAnalysis.meanLength) * 50)}%`,
                      }}
                      title={`句子 ${idx + 1}: ${len} 词`}
                    />
                  ))}
                </div>
                <p className="text-xs text-gray-400 mt-1 text-center">
                  句子长度分布 (紫=最长, 橙=最短)
                </p>
              </div>

              {/* Missing Elements */}
              {advancedAnalysis.missingElements.roles.length > 0 && (
                <div className="pt-3 border-t">
                  <div className="flex items-center space-x-2 text-sm text-orange-600 mb-1">
                    <AlertCircle className="w-4 h-4" />
                    <span>缺失角色 / Missing Roles</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {advancedAnalysis.missingElements.roles.map((role) => (
                      <span key={role} className="px-2 py-0.5 bg-orange-50 text-orange-600 text-xs rounded">
                        {role}
                      </span>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {advancedAnalysis.missingElements.descriptionZh}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Improvement Suggestions Section */}
        {advancedAnalysis.improvementSuggestions.length > 0 && (
          <div className="border rounded-lg">
            <button
              onClick={() => toggleSection('suggestions')}
              className="w-full flex items-center justify-between p-3 hover:bg-gray-50"
            >
              <div className="flex items-center space-x-2">
                <Lightbulb className="w-4 h-4 text-yellow-600" />
                <span className="font-medium">
                  改进建议 / Suggestions ({advancedAnalysis.improvementSuggestions.length})
                </span>
              </div>
              {expandedSections.has('suggestions') ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>

            {expandedSections.has('suggestions') && (
              <div className="p-3 border-t space-y-3">
                {advancedAnalysis.improvementSuggestions.map((suggestion, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-yellow-50 rounded-lg border border-yellow-200"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-yellow-700">
                        [{suggestion.type}] 优先级: {suggestion.priority}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700">
                      {suggestion.suggestionZh || suggestion.suggestion}
                    </p>
                    {suggestion.example && (
                      <p className="text-xs text-gray-500 mt-2 italic bg-white p-2 rounded">
                        示例: {suggestion.example}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Re-analyze button */}
        <div className="text-center pt-2">
          <button
            onClick={handleAdvancedAnalysis}
            disabled={isAnalyzingAdvanced}
            className="text-sm text-purple-600 hover:text-purple-800 disabled:opacity-50"
          >
            {isAnalyzingAdvanced ? (
              <Loader2 className="w-4 h-4 animate-spin inline mr-1" />
            ) : null}
            重新分析 / Re-analyze
          </button>
        </div>
      </div>
    );
  };

  // Render restructure result
  // 渲染重组结果
  const renderRestructureResult = () => {
    if (!restructureResult) return null;

    return (
      <div className="space-y-4 p-4 rounded-lg bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Wand2 className="w-5 h-5 text-indigo-600" />
            <span className="font-semibold text-gray-800">
              {restructureResult.strategyName}
            </span>
            <span className="text-sm text-gray-500">
              / {restructureResult.strategyNameZh}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            {restructureResult.improvement > 0 && (
              <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700">
                -{restructureResult.improvement} risk
              </span>
            )}
          </div>
        </div>

        {/* Restructured text */}
        {/* 重组后的文本 */}
        <div className="p-3 rounded bg-white border border-gray-200">
          <div className="text-sm text-gray-500 mb-1">Restructured / 重组后:</div>
          <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
            {restructureResult.restructured}
          </div>
        </div>

        {/* Changes */}
        {/* 变更 */}
        {restructureResult.changes.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">Changes / 变更:</div>
            <div className="space-y-1">
              {restructureResult.changes.map((change, index) => (
                <div
                  key={index}
                  className="flex items-start space-x-2 text-sm p-2 rounded bg-white/70"
                >
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-gray-600">[{change.type}]</span>{' '}
                    <span className="text-gray-800">{change.description}</span>
                    {change.original && change.result && (
                      <div className="text-xs text-gray-500 mt-0.5">
                        "{change.original}" → "{change.result}"
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Explanation */}
        {/* 说明 */}
        <div className="text-sm text-gray-600">
          <div>{restructureResult.explanation}</div>
          <div className="text-gray-500 mt-1">{restructureResult.explanationZh}</div>
        </div>

        {/* Actions */}
        {/* 操作按钮 */}
        <div className="flex items-center space-x-2">
          <Button
            variant="primary"
            size="sm"
            onClick={handleApply}
            className="flex items-center space-x-1"
          >
            <Check className="w-4 h-4" />
            <span>Apply / 应用</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopy}
            className="flex items-center space-x-1"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-green-500" />
                <span>Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                <span>Copy / 复制</span>
              </>
            )}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReset}
            className="flex items-center space-x-1"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Reset / 重置</span>
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="card p-4 space-y-4">
      {/* Header */}
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText className="w-5 h-5 text-indigo-600" />
          <h3 className="font-semibold text-gray-800">
            段落逻辑分析 {paragraphIndex && `#${paragraphIndex}`}
          </h3>
          <span className="text-sm text-gray-500">/ Paragraph Logic</span>
          <InfoTooltip
            title="Level 3 Enhancement"
            content="分析段落内句子之间的逻辑关系，检测主语重复、句长均匀、线性结构等AI模式，提供ANI结构、主语多样性、隐性连接、节奏变化等重组策略。"
          />
        </div>
        <div className="flex items-center space-x-2">
          {analysis && activeTab === 'basic' && getLogicStructureBadge(analysis.logicStructure)}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="p-1 rounded hover:bg-gray-100"
          >
            {showDetails ? (
              <ChevronUp className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            )}
          </button>
        </div>
      </div>

      {/* Tab Switcher */}
      {/* 选项卡切换 */}
      <div className="flex space-x-1 p-1 bg-gray-100 rounded-lg">
        <button
          onClick={() => setActiveTab('basic')}
          className={clsx(
            'flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors',
            activeTab === 'basic'
              ? 'bg-white text-indigo-700 shadow-sm'
              : 'text-gray-600 hover:text-gray-800'
          )}
        >
          <FileText className="w-4 h-4 inline mr-1" />
          基础分析 / Basic
        </button>
        <button
          onClick={() => setActiveTab('advanced')}
          className={clsx(
            'flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors',
            activeTab === 'advanced'
              ? 'bg-white text-purple-700 shadow-sm'
              : 'text-gray-600 hover:text-gray-800'
          )}
        >
          <BookOpen className="w-4 h-4 inline mr-1" />
          句子角色 / Sentence Roles
        </button>
      </div>

      {/* Paragraph preview */}
      {/* 段落预览 */}
      <div className="p-3 rounded-lg bg-gray-50 border border-gray-200">
        <div className="text-sm text-gray-800 leading-relaxed line-clamp-3">
          {paragraph}
        </div>
        {analysis && (
          <div className="text-xs text-gray-500 mt-2">
            {analysis.sentenceCount} sentences / 句
          </div>
        )}
      </div>

      {/* Basic Tab Content */}
      {activeTab === 'basic' && (
        <>
          {/* Analyze button if no analysis yet */}
          {/* 如果还没有分析则显示分析按钮 */}
          {!analysis && onAnalyze && (
            <div className="flex justify-center">
              <Button
                variant="primary"
                onClick={handleAnalyze}
                disabled={isAnalyzing || !paragraph.trim()}
                className="flex items-center space-x-2"
              >
                {isAnalyzing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <FileText className="w-4 h-4" />
                )}
                <span>Analyze Logic / 分析逻辑</span>
              </Button>
            </div>
          )}

          {/* Analysis results */}
          {/* 分析结果 */}
          {analysis && (
        <>
          {/* Metrics */}
          {/* 指标 */}
          {showDetails && renderMetrics()}

          {/* Risk adjustment */}
          {/* 风险调整 */}
          {analysis.paragraphRiskAdjustment > 0 && (
            <div className="flex items-center space-x-2 text-sm">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <span className="text-gray-600">
                Risk contribution / 风险贡献:
              </span>
              <span className="font-semibold text-amber-600">
                +{analysis.paragraphRiskAdjustment}
              </span>
            </div>
          )}

          {/* Issues */}
          {/* 问题 */}
          {renderIssues()}

          {/* Restructure options */}
          {/* 重组选项 */}
          {analysis.issues.length > 0 && !restructureResult && onRestructure && (
            <>
              <div className="border-t border-gray-200 pt-4">
                {renderRestructureOptions()}
              </div>
              {isRestructuring && (
                <div className="flex items-center justify-center space-x-2 py-4">
                  <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
                  <span className="text-sm text-gray-600">
                    Restructuring... / 正在重组...
                  </span>
                </div>
              )}
            </>
          )}

          {/* Restructure result */}
          {/* 重组结果 */}
          {restructureResult && renderRestructureResult()}
          </>
        )}
        </>
      )}

      {/* Advanced Tab Content - Sentence Role Analysis */}
      {/* 高级选项卡内容 - 句子角色分析 */}
      {activeTab === 'advanced' && renderAdvancedAnalysis()}

      {/* Loading state */}
      {/* 加载状态 */}
      {isLoading && (
        <div className="flex items-center justify-center space-x-2 py-4">
          <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
          <span className="text-sm text-gray-600">Loading... / 加载中...</span>
        </div>
      )}
    </div>
  );
}
