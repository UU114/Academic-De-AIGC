import { useState, useCallback } from 'react';
import {
  FileText,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  ArrowLeftRight,
  CornerDownRight,
  RotateCw,
  XCircle,
  Layers,
  GitBranch,
  Loader2,
  Lightbulb,
  Link2,
  Unlink,
  Wand2,
  Copy,
  Check,
  X,
  Info,
} from 'lucide-react';
import { clsx } from 'clsx';
import type {
  StructureAnalysisResponse,
  StructureOption,
  StructureStrategy,
  LogicDiagnosisResponse,
  FlowRelation,
  ParagraphInfo,
} from '../../types';
import Button from '../common/Button';
import InfoTooltip from '../common/InfoTooltip';
import { InlineLoading } from '../common/LoadingMessage';
import { structureApi } from '../../services/api';

interface StructurePanelProps {
  analysis: StructureAnalysisResponse;
  diagnosis?: LogicDiagnosisResponse;
  onApplyOption?: (option: StructureOption) => void;
  onSkip?: () => void;
  isLoading?: boolean;
}

/**
 * Structure Analysis Panel - Level 1 De-AIGC
 * 结构分析面板 - Level 1 De-AIGC
 *
 * Displays document structure analysis and restructuring options
 * 显示文档结构分析和重组选项
 */
export default function StructurePanel({
  analysis,
  diagnosis,
  onApplyOption,
  onSkip,
  isLoading = false,
}: StructurePanelProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<StructureStrategy | null>(null);
  const [showFlowMap, setShowFlowMap] = useState(true);
  const [showFullOutline, setShowFullOutline] = useState(false);
  const [showConnectors, setShowConnectors] = useState(true);
  const [showLogicBreaks, setShowLogicBreaks] = useState(true);
  // Track expanded paragraphs for showing detailed suggestions
  // 跟踪展开的段落以显示详细建议
  const [expandedParagraphs, setExpandedParagraphs] = useState<Set<number>>(new Set());

  // Track loading state for paragraphs being fetched
  // 跟踪正在获取建议的段落的加载状态
  const [loadingParagraphs, setLoadingParagraphs] = useState<Set<number>>(new Set());

  // Store fetched suggestions for paragraphs (keyed by position)
  // 存储已获取的段落建议（按位置索引）
  const [fetchedSuggestions, setFetchedSuggestions] = useState<Record<string, {
    rewriteSuggestionZh: string;
    rewriteExample?: string;  // English example
  }>>({});

  // State for prompt generation modal
  // 提示词生成弹窗状态
  const [showPromptModal, setShowPromptModal] = useState(false);
  const [generatedPrompt, setGeneratedPrompt] = useState('');
  const [promptType, setPromptType] = useState<'full' | 'section'>('full');
  const [copiedPrompt, setCopiedPrompt] = useState(false);

  // Generate prompt based on analysis results
  // 根据分析结果生成提示词
  const generatePrompt = useCallback((type: 'full' | 'section' = 'full') => {
    setPromptType(type);

    let prompt = '';

    if (type === 'full') {
      // Generate full document revision prompt
      // 生成全文修改提示词
      prompt = `# 学术论文De-AIGC修改任务

## 任务目标
根据以下分析结果，对论文进行修改以降低AI生成内容的检测风险，同时保持学术严谨性和内容完整性。

## 文档分析结果

### 整体评估
- 结构风险分数: ${analysis.structureScore}/100 (${analysis.riskLevel === 'high' ? '高风险' : analysis.riskLevel === 'medium' ? '中风险' : '低风险'})
- 总段落数: ${analysis.totalParagraphs}
- 总章节数: ${analysis.totalSections || '-'}

### 检测到的问题
`;

      // Add pattern issues
      // 添加模式问题
      if (analysis.hasLinearFlow) {
        prompt += `- ⚠️ 线性流程模式：文档采用过于规则的"首先-其次-然后"推进方式\n`;
      }
      if (analysis.hasRepetitivePattern) {
        prompt += `- ⚠️ 重复模式：段落结构高度相似，缺乏变化\n`;
      }
      if (analysis.hasUniformLength) {
        prompt += `- ⚠️ 均匀长度：段落字数过于均匀，方差极低\n`;
      }
      if (analysis.hasPredictableOrder) {
        prompt += `- ⚠️ 可预测结构：遵循过于公式化的学术结构\n`;
      }

      // Add explicit connectors if any
      // 添加显性连接词
      if (analysis.explicit_connectors && analysis.explicit_connectors.length > 0) {
        prompt += `\n### 需要移除的显性连接词（AI指纹）\n`;
        analysis.explicit_connectors.forEach(c => {
          prompt += `- "${c.word}" 在位置 ${c.position}\n`;
        });
      }

      // Add detailed suggestions if available
      // 添加详细建议
      if (analysis.detailedSuggestions) {
        const ds = analysis.detailedSuggestions;

        if (ds.logicSuggestions && ds.logicSuggestions.length > 0) {
          prompt += `\n### 结构调整建议\n`;
          ds.logicSuggestions.forEach(s => {
            prompt += `- ${s}\n`;
          });
        }

        if (ds.abstractSuggestions && ds.abstractSuggestions.length > 0) {
          prompt += `\n### 摘要改进建议\n`;
          ds.abstractSuggestions.forEach(s => {
            prompt += `- ${s}\n`;
          });
        }

        if (ds.sectionSuggestions && ds.sectionSuggestions.length > 0) {
          prompt += `\n### 分章节修改建议\n`;
          ds.sectionSuggestions.forEach(sec => {
            prompt += `\n**第${sec.sectionNumber}章 ${sec.sectionTitle}** [${sec.severity === 'high' ? '高优先' : sec.severity === 'medium' ? '中优先' : '低优先'}]\n`;
            prompt += `建议类型: ${sec.suggestionType === 'merge' ? '合并' : sec.suggestionType === 'split' ? '拆分' : sec.suggestionType === 'add_content' ? '补充内容' : sec.suggestionType === 'reorder' ? '调整顺序' : sec.suggestionType === 'remove_connector' ? '移除连接词' : sec.suggestionType === 'add_citation' ? '补充引用' : '重组'}\n`;
            prompt += `说明: ${sec.suggestionZh}\n`;
            if (sec.details && sec.details.length > 0) {
              prompt += `具体操作:\n`;
              sec.details.forEach((d, i) => {
                prompt += `  ${i + 1}. ${d}\n`;
              });
            }
          });
        }
      }

      prompt += `
## 修改原则

1. **保持学术严谨性**：修改时必须保持论点的逻辑性和数据的准确性
2. **打破模式化结构**：避免"首先、其次、然后"等线性推进，使用更自然的过渡
3. **增加变化性**：段落长度、句式结构应有自然的变化
4. **语义回声替代连接词**：用重复上段关键概念的方式承接，而非使用显性连接词
5. **保留核心数据**：所有实验数据、统计结果必须准确保留

## 输出要求

请输出修改后的完整论文，并在每处重大修改后用【修改说明】标注修改原因。

---

**请在下方粘贴您的论文原文：**

[在此粘贴论文全文]

---

**⚠️ 重要提示：**
- 如有参考文献，请一并提供完整的参考文献列表
- 如有实验数据表格，请确保数据完整准确
- 如有图表描述，请提供图表的详细信息`;

    } else {
      // Generate section-specific prompt
      // 生成章节修改提示词
      prompt = `# 学术论文章节修改任务

## 任务目标
根据分析结果，对指定章节进行针对性修改。

## 当前分析结果
- 结构风险分数: ${analysis.structureScore}/100
`;

      if (analysis.detailedSuggestions?.sectionSuggestions) {
        prompt += `\n## 各章节修改建议\n`;
        analysis.detailedSuggestions.sectionSuggestions.forEach(sec => {
          prompt += `\n### 第${sec.sectionNumber}章 ${sec.sectionTitle}\n`;
          prompt += `- 优先级: ${sec.severity === 'high' ? '高' : sec.severity === 'medium' ? '中' : '低'}\n`;
          prompt += `- 建议: ${sec.suggestionZh}\n`;
          if (sec.details && sec.details.length > 0) {
            sec.details.forEach((d, i) => {
              prompt += `  ${i + 1}. ${d}\n`;
            });
          }
        });
      }

      prompt += `
## 修改原则
1. 保持段落间的语义连贯，使用关键词回声而非显性连接词
2. 打破过于规整的段落结构，增加自然的变化
3. 保持学术严谨性，确保数据和论点准确

---

**请粘贴需要修改的章节内容：**

[在此粘贴章节内容]

---

**⚠️ 重要提示：**
- 请提供该章节涉及的所有参考文献
- 如有数据引用，请确保提供完整数据来源`;
    }

    setGeneratedPrompt(prompt);
    setShowPromptModal(true);
  }, [analysis]);

  // Copy prompt to clipboard
  // 复制提示词到剪贴板
  const copyPromptToClipboard = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(generatedPrompt);
      setCopiedPrompt(true);
      setTimeout(() => setCopiedPrompt(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }, [generatedPrompt]);

  // Fetch suggestion for a specific paragraph
  // 为特定段落获取建议
  const fetchParagraphSuggestion = useCallback(async (para: ParagraphInfo, idx: number) => {
    const position = para.position || `P${idx + 1}`;

    // Skip if already has suggestion or already loading
    // 如果已有建议或正在加载则跳过
    if (para.rewriteSuggestionZh || fetchedSuggestions[position] || loadingParagraphs.has(idx)) {
      return;
    }

    // Mark as loading
    // 标记为加载中
    setLoadingParagraphs(prev => new Set([...prev, idx]));

    try {
      // Get paragraph text from first and last sentence
      // 从首句和尾句获取段落文本
      const paragraphText = para.firstSentence + (para.lastSentence !== para.firstSentence ? ' ... ' + para.lastSentence : '');

      const result = await structureApi.getParagraphSuggestion(
        paragraphText,
        position,
        {
          aiRisk: para.aiRisk,
          aiRiskReason: para.aiRiskReason,
        }
      );

      // Store the fetched suggestion
      // 存储获取到的建议
      setFetchedSuggestions(prev => ({
        ...prev,
        [position]: {
          rewriteSuggestionZh: result.rewriteSuggestionZh,
          rewriteExample: result.rewriteExample,
        }
      }));
    } catch (error) {
      console.error('Failed to fetch paragraph suggestion:', error);
      // Store error message as suggestion
      // 将错误消息存储为建议
      setFetchedSuggestions(prev => ({
        ...prev,
        [position]: {
          rewriteSuggestionZh: '【问题诊断】获取建议失败\n【修改策略】请稍后重试\n【改写提示】建议删除段首显性连接词，改用语义承接',
        }
      }));
    } finally {
      // Remove from loading set
      // 从加载集合中移除
      setLoadingParagraphs(prev => {
        const newSet = new Set(prev);
        newSet.delete(idx);
        return newSet;
      });
    }
  }, [fetchedSuggestions, loadingParagraphs]);

  // Toggle paragraph expansion and auto-fetch suggestion if needed
  // 切换段落展开状态，并在需要时自动获取建议
  const toggleParagraphExpansion = useCallback((idx: number, para: ParagraphInfo) => {
    setExpandedParagraphs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(idx)) {
        newSet.delete(idx);
      } else {
        newSet.add(idx);
        // Auto-fetch suggestion when expanding if needed
        // 展开时自动获取建议（如果需要）
        const position = para.position || `P${idx + 1}`;
        if ((para.aiRisk === 'high' || para.aiRisk === 'medium') &&
            !para.rewriteSuggestionZh &&
            !fetchedSuggestions[position]) {
          fetchParagraphSuggestion(para, idx);
        }
      }
      return newSet;
    });
  }, [fetchedSuggestions, fetchParagraphSuggestion]);

  // Strategy icon mapping
  // 策略图标映射
  const getStrategyIcon = (strategy: StructureStrategy) => {
    switch (strategy) {
      case 'optimize_connection':
        return <GitBranch className="w-4 h-4" />;
      case 'deep_restructure':
        return <Layers className="w-4 h-4" />;
    }
  };

  // Strategy color mapping
  // 策略颜色映射
  const getStrategyColor = (strategy: StructureStrategy) => {
    switch (strategy) {
      case 'optimize_connection':
        return 'bg-teal-50 border-teal-200 text-teal-700';
      case 'deep_restructure':
        return 'bg-indigo-50 border-indigo-200 text-indigo-700';
    }
  };

  // Risk level color
  // 风险等级颜色
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'bg-red-100 text-red-700';
      case 'medium':
        return 'bg-amber-100 text-amber-700';
      default:
        return 'bg-green-100 text-green-700';
    }
  };

  // Flow relation icon
  // 流关系图标
  const getFlowIcon = (relation: FlowRelation) => {
    switch (relation.symbol) {
      case '→':
        return <ArrowRight className="w-4 h-4 text-gray-500" />;
      case '↔':
        return <ArrowLeftRight className="w-4 h-4 text-blue-500" />;
      case '⤵':
        return <CornerDownRight className="w-4 h-4 text-green-500" />;
      case '⟳':
        return <RotateCw className="w-4 h-4 text-purple-500" />;
      case '✗':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <ArrowRight className="w-4 h-4 text-gray-400" />;
    }
  };

  // Pattern badge color
  // 模式徽章颜色
  const getPatternColor = (pattern: string) => {
    switch (pattern) {
      case 'linear':
        return 'bg-red-100 text-red-700';
      case 'parallel':
        return 'bg-amber-100 text-amber-700';
      case 'nested':
        return 'bg-blue-100 text-blue-700';
      case 'circular':
        return 'bg-purple-100 text-purple-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="card p-4 space-y-4">
      {/* Header */}
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText className="w-5 h-5 text-indigo-600" />
          <h3 className="font-semibold text-gray-800">
            逻辑诊断卡
          </h3>
          <span className="text-sm text-gray-500">/ Logic Diagnosis</span>
          <InfoTooltip
            title="Level 1: 骨架重组"
            content="分析全文宏观结构，检测AI常见的线性流程、重复模式和可预测结构，提供两种重组策略。"
          />
        </div>

        {/* Risk Badge with Tooltip */}
        <div className="flex items-center space-x-2">
          <div className="relative group">
            <span className={clsx(
              'px-2 py-0.5 rounded-full text-xs font-medium cursor-help',
              getRiskColor(analysis.riskLevel)
            )}>
              结构分数: {analysis.structureScore}
            </span>
            {/* Score explanation tooltip */}
            <div className="absolute right-0 top-full mt-1 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
              <p className="font-medium mb-1">评分依据 / Score Breakdown:</p>
              <ul className="space-y-0.5 text-gray-300">
                {/* Use scoreBreakdown if available */}
                {analysis.scoreBreakdown ? (
                  <>
                    {analysis.scoreBreakdown.linear_flow > 0 && (
                      <li>• 线性流程模式 +{analysis.scoreBreakdown.linear_flow}分</li>
                    )}
                    {analysis.scoreBreakdown.repetitive_pattern > 0 && (
                      <li>• 重复段落模式 +{analysis.scoreBreakdown.repetitive_pattern}分</li>
                    )}
                    {analysis.scoreBreakdown.uniform_length > 0 && (
                      <li>• 均匀段落长度 +{analysis.scoreBreakdown.uniform_length}分</li>
                    )}
                    {analysis.scoreBreakdown.predictable_order > 0 && (
                      <li>• 可预测结构顺序 +{analysis.scoreBreakdown.predictable_order}分</li>
                    )}
                    {analysis.scoreBreakdown.connector_overuse > 0 && (
                      <li>• 连接词过度使用 +{analysis.scoreBreakdown.connector_overuse}分</li>
                    )}
                    {analysis.scoreBreakdown.missing_semantic_echo > 0 && (
                      <li>• 缺少语义回声 +{analysis.scoreBreakdown.missing_semantic_echo}分</li>
                    )}
                  </>
                ) : (
                  <>
                    {analysis.hasLinearFlow && <li>• 线性流程模式 +20分</li>}
                    {analysis.hasRepetitivePattern && <li>• 重复段落模式 +15分</li>}
                    {analysis.hasUniformLength && <li>• 均匀段落长度 +10分</li>}
                    {analysis.hasPredictableOrder && <li>• 可预测结构顺序 +15分</li>}
                  </>
                )}
                {analysis.issues && analysis.issues.length > 0 && (
                  <li>• 检测到 {analysis.issues.length} 个问题</li>
                )}
                {!analysis.hasLinearFlow && !analysis.hasRepetitivePattern &&
                 !analysis.hasUniformLength && !analysis.hasPredictableOrder && (
                  <li>• 未检测到明显AI模式</li>
                )}
              </ul>
              <p className="mt-1 text-gray-400 border-t border-gray-700 pt-1">
                分数越高 = AI痕迹越明显
              </p>
            </div>
          </div>
          {analysis.riskLevel === 'low' && (
            <CheckCircle className="w-4 h-4 text-green-500" />
          )}
          {analysis.riskLevel !== 'low' && (
            <AlertTriangle className={clsx(
              'w-4 h-4',
              analysis.riskLevel === 'high' ? 'text-red-500' : 'text-amber-500'
            )} />
          )}
        </div>
      </div>

      {/* Statistics Overview */}
      {/* 统计概览 */}
      <div className="grid grid-cols-4 gap-3 p-3 bg-gray-50 rounded-lg">
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-800">{analysis.totalParagraphs}</p>
          <p className="text-xs text-gray-500">正文段落</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-800">{analysis.totalSections || '-'}</p>
          <p className="text-xs text-gray-500">章节数</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-800">{analysis.totalWords || '-'}</p>
          <p className="text-xs text-gray-500">词数</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-800">{analysis.avgParagraphLength?.toFixed(0) || '-'}</p>
          <p className="text-xs text-gray-500">平均段长</p>
        </div>
      </div>

      {/* Pattern Detection Flags */}
      {/* 模式检测标志 */}
      <div className="flex flex-wrap gap-2">
        {analysis.hasLinearFlow && (
          <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">
            线性流程 Linear Flow
          </span>
        )}
        {analysis.hasRepetitivePattern && (
          <span className="px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded-full">
            重复模式 Repetitive
          </span>
        )}
        {analysis.hasUniformLength && (
          <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
            均匀长度 Uniform Length
          </span>
        )}
        {analysis.hasPredictableOrder && (
          <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded-full">
            可预测结构 Predictable
          </span>
        )}
        {!analysis.hasLinearFlow && !analysis.hasRepetitivePattern &&
         !analysis.hasUniformLength && !analysis.hasPredictableOrder && (
          <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
            结构自然 Natural Structure
          </span>
        )}
      </div>

      {/* Explicit Connectors Detection (AI Fingerprints) */}
      {/* 显性连接词检测（AI指纹） */}
      {analysis.explicit_connectors && analysis.explicit_connectors.length > 0 && (
        <div className="space-y-2">
          <button
            onClick={() => setShowConnectors(!showConnectors)}
            className="flex items-center text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            {showConnectors ? (
              <ChevronUp className="w-4 h-4 mr-1" />
            ) : (
              <ChevronDown className="w-4 h-4 mr-1" />
            )}
            <Link2 className="w-4 h-4 mr-1 text-red-500" />
            检测到 {analysis.explicit_connectors.length} 个显性连接词
            <span className="ml-2 text-xs text-red-500">(AI指纹)</span>
          </button>

          {showConnectors && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-xs text-red-600 mb-2">
                这些连接词是典型的AI写作特征，建议移除或替换为语义承接
              </p>
              <div className="flex flex-wrap gap-2">
                {analysis.explicit_connectors.map((connector, idx) => (
                  <div
                    key={idx}
                    className={clsx(
                      'px-2 py-1 rounded text-xs flex items-center space-x-1',
                      connector.severity === 'high'
                        ? 'bg-red-100 text-red-700 border border-red-300'
                        : 'bg-amber-100 text-amber-700 border border-amber-300'
                    )}
                    title={`位置: ${connector.position}, 位于: ${connector.location === 'paragraph_start' ? '段首' : '句首'}`}
                  >
                    <span className="font-medium">{connector.word}</span>
                    <span className="text-gray-500">@{connector.position}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2 italic">
                建议: 使用语义回声（重复上段关键概念）代替显性连接词
              </p>
            </div>
          )}
        </div>
      )}

      {/* Logic Break Points Between Paragraphs */}
      {/* 段落间逻辑断裂点 */}
      {analysis.logic_breaks && analysis.logic_breaks.length > 0 && (
        <div className="space-y-2">
          <button
            onClick={() => setShowLogicBreaks(!showLogicBreaks)}
            className="flex items-center text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            {showLogicBreaks ? (
              <ChevronUp className="w-4 h-4 mr-1" />
            ) : (
              <ChevronDown className="w-4 h-4 mr-1" />
            )}
            <Unlink className="w-4 h-4 mr-1 text-amber-500" />
            检测到 {analysis.logic_breaks.length} 个逻辑断裂点
          </button>

          {showLogicBreaks && (
            <div className="space-y-2">
              {analysis.logic_breaks.map((lb, idx) => (
                <div
                  key={idx}
                  className={clsx(
                    'p-3 rounded-lg border',
                    lb.transition_type === 'glue_word_only' && 'bg-red-50 border-red-200',
                    lb.transition_type === 'abrupt' && 'bg-amber-50 border-amber-200',
                    lb.transition_type === 'smooth' && 'bg-green-50 border-green-200'
                  )}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center space-x-2">
                      <span className="px-1.5 py-0.5 bg-gray-200 text-gray-700 text-xs font-mono rounded">
                        {lb.from_position}
                      </span>
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      <span className="px-1.5 py-0.5 bg-gray-200 text-gray-700 text-xs font-mono rounded">
                        {lb.to_position}
                      </span>
                    </div>
                    <span className={clsx(
                      'px-2 py-0.5 text-xs rounded',
                      lb.transition_type === 'glue_word_only' && 'bg-red-100 text-red-600',
                      lb.transition_type === 'abrupt' && 'bg-amber-100 text-amber-600',
                      lb.transition_type === 'smooth' && 'bg-green-100 text-green-600'
                    )}>
                      {lb.transition_type === 'glue_word_only' ? '仅靠连接词'
                        : lb.transition_type === 'abrupt' ? '突兀断裂'
                        : '流畅'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-700 mt-1">{lb.issue_zh || lb.issue}</p>
                  {lb.suggestion_zh && lb.transition_type !== 'smooth' && (
                    <p className="text-xs text-blue-600 mt-1 flex items-start">
                      <Lightbulb className="w-3 h-3 mr-1 mt-0.5 flex-shrink-0" />
                      {lb.suggestion_zh}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Paragraph Structure with Positions and Summaries */}
      {/* 段落结构（位置和摘要） */}
      {analysis.paragraphs && analysis.paragraphs.length > 0 && analysis.paragraphs[0].position && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-700">段落结构 / Paragraph Structure</p>
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              {showDetails ? '收起' : '展开全部'}
            </button>
          </div>

          <div className="max-h-96 overflow-y-auto space-y-2 pr-1">
            {/* Filter out paragraphs with 0 words (non-content elements) */}
            {/* 过滤掉0词的段落（非内容元素） */}
            {(showDetails
              ? analysis.paragraphs.filter(p => p.wordCount > 0)
              : analysis.paragraphs.filter(p => p.wordCount > 0).slice(0, 5)
            ).map((para, idx) => (
              <div
                key={idx}
                className={clsx(
                  'rounded border text-sm transition-all',
                  para.aiRisk === 'high' && 'bg-red-50 border-red-200',
                  para.aiRisk === 'medium' && 'bg-amber-50 border-amber-200',
                  para.aiRisk === 'low' && 'bg-green-50 border-green-200',
                  !para.aiRisk && 'bg-gray-50 border-gray-200'
                )}
              >
                {/* Clickable header */}
                {/* 可点击的头部 */}
                <button
                  onClick={() => toggleParagraphExpansion(idx, para)}
                  className="w-full p-2 text-left hover:bg-black/5 transition-colors rounded-t"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2">
                      {/* Position badge */}
                      <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 text-xs font-mono rounded">
                        {para.position || `P${idx + 1}`}
                      </span>
                      {/* AI risk indicator */}
                      {para.aiRisk && (
                        <span className={clsx(
                          'px-1.5 py-0.5 text-xs rounded',
                          para.aiRisk === 'high' && 'bg-red-100 text-red-600',
                          para.aiRisk === 'medium' && 'bg-amber-100 text-amber-600',
                          para.aiRisk === 'low' && 'bg-green-100 text-green-600'
                        )}>
                          {para.aiRisk === 'high' ? '高风险' : para.aiRisk === 'medium' ? '中风险' : '低风险'}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-400">{para.wordCount}词</span>
                      {(para.aiRisk === 'high' || para.aiRisk === 'medium') && (
                        expandedParagraphs.has(idx) ? (
                          <ChevronUp className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        )
                      )}
                    </div>
                  </div>

                  {/* Summary */}
                  <p className="mt-1 text-gray-700 text-xs leading-relaxed">
                    {para.summaryZh || para.summary || para.functionType}
                  </p>

                  {/* Risk reason if exists */}
                  {para.aiRiskReason && para.aiRisk !== 'low' && (
                    <p className="mt-1 text-xs text-gray-500 italic">
                      → {para.aiRiskReason}
                    </p>
                  )}
                </button>

                {/* Expanded detailed suggestion panel */}
                {/* 展开的详细建议面板 */}
                {expandedParagraphs.has(idx) && (para.aiRisk === 'high' || para.aiRisk === 'medium') && (
                  <div className="px-3 pb-3 pt-1 border-t border-current/10">
                    {(() => {
                      // Get suggestion from paragraph data or fetched suggestions
                      // 从段落数据或已获取的建议中获取建议
                      const position = para.position || `P${idx + 1}`;
                      const suggestion = para.rewriteSuggestionZh || fetchedSuggestions[position]?.rewriteSuggestionZh;
                      const example = para.rewriteExample || fetchedSuggestions[position]?.rewriteExample;
                      const isLoading = loadingParagraphs.has(idx);

                      if (isLoading) {
                        // Show loading state with fun message
                        // 显示趣味加载状态
                        return (
                          <div className="p-2 bg-blue-50 rounded">
                            <InlineLoading category="paragraph" showEnglish={false} />
                          </div>
                        );
                      }

                      if (suggestion) {
                        // Show suggestion
                        // 显示建议
                        return (
                          <div className="space-y-2">
                            {/* Parse and display structured suggestion */}
                            {/* 解析并显示结构化建议 */}
                            {suggestion.includes('【问题诊断】') ? (
                              <>
                                {/* Problem diagnosis */}
                                {suggestion.match(/【问题诊断】([^【]*)/)?.[1] && (
                                  <div className="text-xs">
                                    <span className="font-medium text-red-600">【问题诊断】</span>
                                    <span className="text-gray-700">
                                      {suggestion.match(/【问题诊断】([^【]*)/)?.[1]?.trim()}
                                    </span>
                                  </div>
                                )}
                                {/* Modification strategy */}
                                {suggestion.match(/【修改策略】([^【]*)/)?.[1] && (
                                  <div className="text-xs">
                                    <span className="font-medium text-blue-600">【修改策略】</span>
                                    <span className="text-gray-700">
                                      {suggestion.match(/【修改策略】([^【]*)/)?.[1]?.trim()}
                                    </span>
                                  </div>
                                )}
                                {/* Rewrite hint */}
                                {suggestion.match(/【改写提示】([^【]*)/)?.[1] && (
                                  <div className="text-xs">
                                    <span className="font-medium text-green-600">【改写提示】</span>
                                    <span className="text-gray-700">
                                      {suggestion.match(/【改写提示】([^【]*)/)?.[1]?.trim()}
                                    </span>
                                  </div>
                                )}
                              </>
                            ) : (
                              <p className="text-xs text-gray-700">{suggestion}</p>
                            )}

                            {/* Rewrite example if available (in English) */}
                            {example && (
                              <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded">
                                <p className="text-xs font-medium text-green-700 mb-1">📝 Rewrite Example / 改写示例：</p>
                                <p className="text-xs text-green-800 italic font-serif">"{example}"</p>
                              </div>
                            )}
                          </div>
                        );
                      }

                      // Should not reach here normally, but show retry option
                      // 通常不应到达此处，但显示重试选项
                      return (
                        <div className="p-2 bg-gray-100 rounded">
                          <p className="text-xs text-gray-500 flex items-center">
                            <Lightbulb className="w-3 h-3 mr-1" />
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                fetchParagraphSuggestion(para, idx);
                              }}
                              className="text-blue-600 hover:text-blue-800 hover:underline ml-1"
                            >
                              点击获取修改建议
                            </button>
                          </p>
                        </div>
                      );
                    })()}
                  </div>
                )}
              </div>
            ))}

            {/* Show more button only if filtered paragraphs > 5 */}
            {/* 仅在过滤后的段落数>5时显示更多按钮 */}
            {!showDetails && analysis.paragraphs.filter(p => p.wordCount > 0).length > 5 && (
              <button
                onClick={() => setShowDetails(true)}
                className="w-full py-2 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
              >
                +{analysis.paragraphs.filter(p => p.wordCount > 0).length - 5} 更多段落...
              </button>
            )}
          </div>
        </div>
      )}

      {/* Detailed Improvement Suggestions */}
      {/* 详细改进建议 */}
      {analysis.detailedSuggestions && (
        <div className="space-y-3">
          {/* Disclaimer Banner */}
          {/* 免责声明横幅 */}
          <div className="p-2 bg-amber-50 border border-amber-300 rounded-lg">
            <p className="text-xs text-amber-700 flex items-center">
              <AlertTriangle className="w-3 h-3 mr-1 flex-shrink-0" />
              <span>
                <strong>基于AI的DEAIGC分析，不保证逻辑和语义，请自行斟酌</strong>
                <span className="text-amber-600 ml-1">/ AI-based analysis, use with discretion</span>
              </span>
            </p>
          </div>

          {/* Overall Assessment */}
          {/* 总体评估 */}
          {analysis.detailedSuggestions.overallAssessmentZh && (
            <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
              <div className="flex items-center text-sm mb-2">
                <Lightbulb className="w-4 h-4 text-indigo-600 mr-2" />
                <span className="text-indigo-700 font-medium">总体评估 / Overall Assessment</span>
              </div>
              <p className="text-xs text-indigo-600">{analysis.detailedSuggestions.overallAssessmentZh}</p>
            </div>
          )}

          {/* Abstract Suggestions */}
          {/* 摘要建议 */}
          {analysis.detailedSuggestions.abstractSuggestions && analysis.detailedSuggestions.abstractSuggestions.length > 0 && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center text-sm mb-2">
                <FileText className="w-4 h-4 text-blue-600 mr-2" />
                <span className="text-blue-700 font-medium">摘要改进 / Abstract Improvements</span>
              </div>
              <ul className="text-xs text-blue-600 space-y-1">
                {analysis.detailedSuggestions.abstractSuggestions.map((s, i) => (
                  <li key={i} className="flex items-start">
                    <span className="mr-1">•</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Logic/Order Suggestions */}
          {/* 逻辑顺序建议 */}
          {analysis.detailedSuggestions.logicSuggestions && analysis.detailedSuggestions.logicSuggestions.length > 0 && (
            <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
              <div className="flex items-center text-sm mb-2">
                <GitBranch className="w-4 h-4 text-purple-600 mr-2" />
                <span className="text-purple-700 font-medium">结构调整 / Structure Adjustments</span>
              </div>
              <ul className="text-xs text-purple-600 space-y-1">
                {analysis.detailedSuggestions.logicSuggestions.map((s, i) => (
                  <li key={i} className="flex items-start">
                    <span className="mr-1">•</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Section-by-Section Suggestions */}
          {/* 分章节建议 */}
          {analysis.detailedSuggestions.sectionSuggestions && analysis.detailedSuggestions.sectionSuggestions.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700">分章节建议 / Section Suggestions</p>
              {analysis.detailedSuggestions.sectionSuggestions.map((section, idx) => (
                <div
                  key={idx}
                  className={clsx(
                    'p-3 rounded-lg border',
                    section.severity === 'high' && 'bg-red-50 border-red-200',
                    section.severity === 'medium' && 'bg-amber-50 border-amber-200',
                    section.severity === 'low' && 'bg-green-50 border-green-200'
                  )}
                >
                  {/* Section Header */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 bg-gray-200 text-gray-700 text-xs font-mono rounded">
                        第{section.sectionNumber}章
                      </span>
                      <span className="text-sm font-medium text-gray-700">{section.sectionTitle}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={clsx(
                        'px-1.5 py-0.5 text-xs rounded',
                        section.suggestionType === 'merge' && 'bg-purple-100 text-purple-600',
                        section.suggestionType === 'split' && 'bg-blue-100 text-blue-600',
                        section.suggestionType === 'add_content' && 'bg-green-100 text-green-600',
                        section.suggestionType === 'reorder' && 'bg-orange-100 text-orange-600',
                        section.suggestionType === 'restructure' && 'bg-indigo-100 text-indigo-600',
                        section.suggestionType === 'remove_connector' && 'bg-red-100 text-red-600',
                        section.suggestionType === 'add_citation' && 'bg-teal-100 text-teal-600'
                      )}>
                        {section.suggestionType === 'merge' && '合并'}
                        {section.suggestionType === 'split' && '拆分'}
                        {section.suggestionType === 'add_content' && '补充内容'}
                        {section.suggestionType === 'reorder' && '调整顺序'}
                        {section.suggestionType === 'restructure' && '重组'}
                        {section.suggestionType === 'remove_connector' && '移除连接词'}
                        {section.suggestionType === 'add_citation' && '补充引用'}
                      </span>
                      <span className={clsx(
                        'px-1.5 py-0.5 text-xs rounded',
                        section.severity === 'high' && 'bg-red-100 text-red-600',
                        section.severity === 'medium' && 'bg-amber-100 text-amber-600',
                        section.severity === 'low' && 'bg-green-100 text-green-600'
                      )}>
                        {section.severity === 'high' ? '高优先' : section.severity === 'medium' ? '中优先' : '低优先'}
                      </span>
                    </div>
                  </div>

                  {/* Suggestion Content */}
                  <p className="text-xs text-gray-700 mb-2">{section.suggestionZh}</p>

                  {/* Details List */}
                  {section.details && section.details.length > 0 && (
                    <div className="mt-2 pl-3 border-l-2 border-gray-300">
                      <p className="text-xs text-gray-500 mb-1">具体操作：</p>
                      <ul className="text-xs text-gray-600 space-y-1">
                        {section.details.map((detail, i) => (
                          <li key={i} className="flex items-start">
                            <span className="mr-1 text-gray-400">{i + 1}.</span>
                            <span>{detail}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Affected Paragraphs */}
                  {section.affectedParagraphs && section.affectedParagraphs.length > 0 && (
                    <div className="mt-2 flex items-center flex-wrap gap-1">
                      <span className="text-xs text-gray-500">涉及段落：</span>
                      {section.affectedParagraphs.map((p, i) => (
                        <span key={i} className="px-1 py-0.5 bg-gray-100 text-gray-600 text-xs font-mono rounded">
                          {p}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Generate Prompt Buttons */}
      {/* 生成提示词按钮 */}
      {(analysis.detailedSuggestions || analysis.recommendationZh || analysis.issues?.length) && (
        <div className="p-3 bg-gradient-to-r from-violet-50 to-purple-50 border border-violet-200 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center text-sm">
              <Wand2 className="w-4 h-4 text-violet-600 mr-2" />
              <span className="text-violet-700 font-medium">AI辅助修改 / AI-Assisted Revision</span>
            </div>
          </div>
          <p className="text-xs text-violet-600 mb-3">
            生成修改提示词，配合其他AI工具进行论文修改
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => generatePrompt('full')}
              className="px-3 py-1.5 bg-violet-600 text-white text-xs rounded-lg hover:bg-violet-700 transition-colors flex items-center"
            >
              <Wand2 className="w-3 h-3 mr-1" />
              生成全文修改提示词
            </button>
            <button
              onClick={() => generatePrompt('section')}
              className="px-3 py-1.5 bg-white text-violet-600 border border-violet-300 text-xs rounded-lg hover:bg-violet-50 transition-colors flex items-center"
            >
              <FileText className="w-3 h-3 mr-1" />
              生成章节修改提示词
            </button>
          </div>
        </div>
      )}

      {/* Prompt Generation Modal */}
      {/* 提示词生成弹窗 */}
      {showPromptModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="p-4 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                  <Wand2 className="w-5 h-5 text-violet-600 mr-2" />
                  {promptType === 'full' ? '全文修改提示词' : '章节修改提示词'}
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  复制此提示词到ChatGPT、Claude等AI工具中使用
                </p>
              </div>
              <button
                onClick={() => setShowPromptModal(false)}
                className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Disclaimer Banner */}
            <div className="mx-4 mt-4 p-3 bg-amber-50 border border-amber-300 rounded-lg flex-shrink-0">
              <div className="flex items-start">
                <AlertTriangle className="w-5 h-5 text-amber-600 mr-2 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-amber-800">
                    基于AI的DEAIGC分析，不保证逻辑和语义，请自行斟酌
                  </p>
                  <p className="text-xs text-amber-600 mt-1">
                    AI-based analysis results. Please review and verify all suggestions carefully.
                  </p>
                </div>
              </div>
            </div>

            {/* Usage Instructions */}
            <div className="mx-4 mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg flex-shrink-0">
              <div className="flex items-start">
                <Info className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-blue-700 space-y-1">
                  <p className="font-medium">使用说明 / How to Use:</p>
                  <ol className="list-decimal ml-4 space-y-1">
                    <li>点击下方"复制提示词"按钮</li>
                    <li>打开ChatGPT、Claude或其他AI对话工具</li>
                    <li>粘贴提示词，并在指定位置粘贴您的论文原文</li>
                    <li>发送后等待AI返回修改建议</li>
                  </ol>
                  <div className="mt-2 p-2 bg-amber-100 rounded border border-amber-200">
                    <p className="font-medium text-amber-800">⚠️ 重要提醒:</p>
                    <ul className="list-disc ml-4 mt-1 text-amber-700">
                      <li><strong>参考文献</strong>: 请务必提供完整的参考文献列表，AI无法凭空生成准确的引用</li>
                      <li><strong>实验数据</strong>: 所有数据、统计结果必须由您提供，AI不会编造数据</li>
                      <li><strong>专业术语</strong>: 如有特定领域的专业术语，请在提示词中说明</li>
                      <li><strong>格式要求</strong>: 如有特定的格式要求（如期刊模板），请额外说明</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Prompt Content */}
            <div className="flex-1 overflow-auto p-4">
              <div className="bg-gray-50 rounded-lg border border-gray-200 p-3">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed">
                  {generatedPrompt}
                </pre>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-gray-200 flex items-center justify-between flex-shrink-0">
              <p className="text-xs text-gray-500">
                提示词长度: {generatedPrompt.length} 字符
              </p>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setShowPromptModal(false)}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors text-sm"
                >
                  关闭
                </button>
                <button
                  onClick={copyPromptToClipboard}
                  className={clsx(
                    'px-4 py-2 rounded-lg transition-colors text-sm flex items-center',
                    copiedPrompt
                      ? 'bg-green-600 text-white'
                      : 'bg-violet-600 text-white hover:bg-violet-700'
                  )}
                >
                  {copiedPrompt ? (
                    <>
                      <Check className="w-4 h-4 mr-1" />
                      已复制
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4 mr-1" />
                      复制提示词
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Legacy simple recommendation (fallback) */}
      {/* 旧版简单建议（后备） */}
      {!analysis.detailedSuggestions && analysis.recommendationZh && (
        <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
          <div className="flex items-center text-sm">
            <Lightbulb className="w-4 h-4 text-indigo-600 mr-2" />
            <span className="text-indigo-700 font-medium">改进建议</span>
          </div>
          <p className="text-xs text-indigo-600 mt-1">{analysis.recommendationZh}</p>
          {/* Disclaimer for simple recommendation too */}
          <p className="text-xs text-amber-600 mt-2 flex items-center">
            <AlertTriangle className="w-3 h-3 mr-1" />
            基于AI的DEAIGC分析，不保证逻辑和语义，请自行斟酌
          </p>
        </div>
      )}

      {/* Flow Map Visualization */}
      {/* 流程图可视化 */}
      {diagnosis && diagnosis.flowMap.length > 0 && (
        <div className="space-y-2">
          <button
            onClick={() => setShowFlowMap(!showFlowMap)}
            className="flex items-center text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            {showFlowMap ? (
              <ChevronUp className="w-4 h-4 mr-1" />
            ) : (
              <ChevronDown className="w-4 h-4 mr-1" />
            )}
            逻辑流程图 / Flow Map
          </button>

          {showFlowMap && (
            <div className="p-3 bg-gray-50 rounded-lg">
              {/* Pattern Badge */}
              <div className="flex items-center mb-3">
                <span className={clsx(
                  'px-2 py-0.5 rounded text-xs font-medium',
                  getPatternColor(diagnosis.structurePattern)
                )}>
                  {diagnosis.structurePatternZh}模式 / {diagnosis.structurePattern}
                </span>
                <span className="ml-2 text-xs text-gray-500">
                  {diagnosis.patternDescriptionZh}
                </span>
              </div>

              {/* Flow Visualization */}
              <div className="flex flex-wrap items-center gap-1">
                {diagnosis.flowMap.map((flow, idx) => (
                  <div key={idx} className="flex items-center">
                    <span className={clsx(
                      'px-2 py-1 rounded text-xs font-medium',
                      diagnosis.riskAreas.some(r => r.paragraph === flow.from)
                        ? 'bg-red-100 text-red-700'
                        : 'bg-gray-200 text-gray-700'
                    )}>
                      P{flow.from + 1}
                    </span>
                    <div className="mx-1" title={flow.relation}>
                      {getFlowIcon(flow)}
                    </div>
                    {idx === diagnosis.flowMap.length - 1 && (
                      <span className={clsx(
                        'px-2 py-1 rounded text-xs font-medium',
                        diagnosis.riskAreas.some(r => r.paragraph === flow.to)
                          ? 'bg-red-100 text-red-700'
                          : 'bg-gray-200 text-gray-700'
                      )}>
                        P{flow.to + 1}
                      </span>
                    )}
                  </div>
                ))}
              </div>

              {/* Recommendation */}
              <div className="mt-3 p-2 bg-indigo-50 rounded border border-indigo-200">
                <div className="flex items-center text-sm">
                  <Lightbulb className="w-4 h-4 text-indigo-600 mr-2" />
                  <span className="text-indigo-700 font-medium">
                    推荐策略: {diagnosis.recommendedStrategy === 'optimize_connection'
                      ? '优化连接' : '深度重组'}
                  </span>
                </div>
                <p className="text-xs text-indigo-600 mt-1">
                  {diagnosis.recommendationReasonZh}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Core Thesis */}
      {/* 核心论点 */}
      {analysis.coreThesis && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-xs text-blue-600 mb-1">核心论点 / Core Thesis</p>
          <p className="text-sm text-blue-800">{analysis.coreThesis}</p>
        </div>
      )}

      {/* Key Arguments */}
      {/* 关键论据 */}
      {analysis.keyArguments && analysis.keyArguments.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-600 font-medium">关键论据 / Key Arguments</p>
          <div className="space-y-1">
            {analysis.keyArguments.slice(0, 3).map((arg, idx) => (
              <div key={idx} className="flex items-start text-xs text-gray-700">
                <span className="w-4 h-4 bg-gray-200 rounded-full flex items-center justify-center mr-2 flex-shrink-0 text-gray-600">
                  {idx + 1}
                </span>
                <span className="line-clamp-2">{arg}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Issues Summary */}
      {/* 问题摘要 */}
      {analysis.issues && analysis.issues.length > 0 && (
        <div className="space-y-2">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center text-sm text-gray-600 hover:text-gray-800"
          >
            {showDetails ? (
              <ChevronUp className="w-4 h-4 mr-1" />
            ) : (
              <ChevronDown className="w-4 h-4 mr-1" />
            )}
            检测到 {analysis.issues.length} 个结构问题
          </button>

          {showDetails && (
            <div className="space-y-2 pl-5">
              {analysis.issues.map((issue, idx) => (
                <div
                  key={idx}
                  className={clsx(
                    'text-sm px-3 py-2 rounded',
                    issue.severity === 'high' && 'bg-red-50 text-red-700',
                    issue.severity === 'medium' && 'bg-amber-50 text-amber-700',
                    issue.severity === 'low' && 'bg-yellow-50 text-yellow-700'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">[{issue.severity}] {issue.type}</span>
                    <span className="text-xs">
                      {issue.affectedParagraphs ? `段落: ${issue.affectedParagraphs.map(p => p + 1).join(', ')}` : ''}
                    </span>
                  </div>
                  <p className="text-xs mt-1">{issue.descriptionZh}</p>
                  {issue.suggestionZh && (
                    <p className="text-xs text-gray-600 mt-1">
                      建议: {issue.suggestionZh}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Strategy Options */}
      {/* 策略选项 */}
      {analysis.options && analysis.options.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm font-medium text-gray-700">重组策略 / Restructure Strategies</p>

          <div className="grid gap-3">
            {analysis.options.map((option) => (
              <div
                key={option.strategy}
                className={clsx(
                  'p-3 rounded-lg border-2 cursor-pointer transition-all',
                  selectedStrategy === option.strategy
                    ? getStrategyColor(option.strategy)
                    : 'bg-white border-gray-200 hover:border-gray-300'
                )}
                onClick={() => setSelectedStrategy(
                  selectedStrategy === option.strategy ? null : option.strategy
                )}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getStrategyIcon(option.strategy)}
                    <span className="font-medium text-sm">
                      {option.strategyNameZh}
                    </span>
                    <span className="text-xs text-gray-500">
                      / {option.strategy.replace('_', ' ')}
                    </span>
                  </div>
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                    -{option.predictedImprovement}分
                  </span>
                </div>

                <p className="text-xs text-gray-600 mb-2">
                  {option.explanationZh}
                </p>

                {/* Strategy-specific details */}
                {option.strategy === 'optimize_connection' && option.modifications.length > 0 && (
                  <div className="mt-2 text-xs text-gray-500">
                    {option.modifications.length} 处修改建议
                  </div>
                )}

                {option.strategy === 'deep_restructure' && option.newOrder.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-500 mb-1">新顺序:</p>
                    <div className="flex flex-wrap gap-1">
                      {option.newOrder.map((idx, i) => (
                        <span key={i} className="px-1.5 py-0.5 bg-indigo-100 text-indigo-700 text-xs rounded">
                          P{idx + 1}
                        </span>
                      ))}
                    </div>
                    {option.restructureTypeZh && (
                      <p className="text-xs text-gray-500 mt-1">
                        重组类型: {option.restructureTypeZh}
                      </p>
                    )}
                  </div>
                )}

                {/* Preview when selected */}
                {selectedStrategy === option.strategy && (
                  <div className="mt-3 pt-3 border-t border-current border-opacity-20 space-y-2">
                    <p className="text-xs font-medium">大纲预览:</p>
                    <div className="space-y-1">
                      {(showFullOutline ? option.outline : option.outline.slice(0, 5)).map((item, idx) => (
                        <div key={idx} className="text-xs text-gray-700 pl-2 border-l-2 border-gray-300">
                          {item}
                        </div>
                      ))}
                      {option.outline.length > 5 && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setShowFullOutline(!showFullOutline);
                          }}
                          className="text-xs text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
                        >
                          {showFullOutline
                            ? '收起'
                            : `+${option.outline.length - 5} 更多...`}
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Low risk message */}
      {/* 低风险消息 */}
      {analysis.riskLevel === 'low' && (!analysis.options || analysis.options.length === 0) && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-center">
          <CheckCircle className="w-5 h-5 text-green-500 mx-auto mb-1" />
          <p className="text-sm text-green-700">文档结构自然，无需重组</p>
          <p className="text-xs text-green-600">Document structure appears natural</p>
        </div>
      )}

      {/* Action Buttons */}
      {/* 操作按钮 */}
      <div className="flex justify-end space-x-3 pt-2 border-t border-gray-100">
        {onSkip && (
          <Button variant="ghost" onClick={onSkip} disabled={isLoading}>
            跳过
          </Button>
        )}
        {selectedStrategy && onApplyOption && (
          <Button
            onClick={() => {
              const option = analysis.options.find(o => o.strategy === selectedStrategy);
              if (option) onApplyOption(option);
            }}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                应用中...
              </>
            ) : (
              '应用此策略'
            )}
          </Button>
        )}
      </div>

      {/* Analysis summary */}
      {/* 分析摘要 */}
      <div className="text-xs text-gray-500 text-center pt-2">
        {analysis.messageZh}
      </div>
    </div>
  );
}

/**
 * Compact structure card for document overview
 * 用于文档概览的紧凑结构卡片
 */
export function StructureCard({
  analysis,
  onClick,
}: {
  analysis: StructureAnalysisResponse;
  onClick?: () => void;
}) {
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'border-red-300 bg-red-50';
      case 'medium':
        return 'border-amber-300 bg-amber-50';
      default:
        return 'border-green-300 bg-green-50';
    }
  };

  return (
    <div
      className={clsx(
        'p-3 rounded-lg border-2 cursor-pointer transition-all hover:shadow-md',
        getRiskColor(analysis.riskLevel)
      )}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">
          骨架重组 / Structure
        </span>
        <span className={clsx(
          'px-2 py-0.5 rounded text-xs',
          analysis.riskLevel === 'high' && 'bg-red-100 text-red-700',
          analysis.riskLevel === 'medium' && 'bg-amber-100 text-amber-700',
          analysis.riskLevel === 'low' && 'bg-green-100 text-green-700'
        )}>
          {analysis.structureScore}分
        </span>
      </div>

      <div className="text-xs text-gray-600 space-y-1">
        <p>{analysis.totalParagraphs} 段落 {analysis.totalSections ? `· ${analysis.totalSections} 章节` : analysis.totalSentences ? `· ${analysis.totalSentences} 句子` : ''}</p>
        {analysis.issues && analysis.issues.length > 0 && (
          <p className="text-amber-600">{analysis.issues.length} 个问题</p>
        )}
      </div>

      {/* Pattern flags */}
      <div className="flex flex-wrap gap-1 mt-2">
        {analysis.hasLinearFlow && (
          <span className="px-1 bg-red-100 text-red-600 text-xs rounded">线性</span>
        )}
        {analysis.hasRepetitivePattern && (
          <span className="px-1 bg-amber-100 text-amber-600 text-xs rounded">重复</span>
        )}
      </div>
    </div>
  );
}
