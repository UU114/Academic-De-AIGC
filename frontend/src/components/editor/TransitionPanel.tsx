import { useState } from 'react';
import {
  Link,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Waves,
  MessageSquare,
  Shuffle,
  Loader2,
} from 'lucide-react';
import { clsx } from 'clsx';
import type {
  TransitionAnalysisResponse,
  TransitionOption,
  TransitionStrategy,
} from '../../types';
import Button from '../common/Button';
import InfoTooltip from '../common/InfoTooltip';

interface TransitionPanelProps {
  analysis: TransitionAnalysisResponse;
  onApplyOption?: (option: TransitionOption) => void;
  onSkip?: () => void;
  isLoading?: boolean;
  transitionIndex?: number;  // 1-based index for display
}

/**
 * Transition Analysis Panel - Level 2 De-AIGC
 * 衔接分析面板 - Level 2 De-AIGC
 *
 * Displays paragraph transition analysis and repair options
 * 显示段落衔接分析和修复选项
 */
export default function TransitionPanel({
  analysis,
  onApplyOption,
  onSkip,
  isLoading = false,
  transitionIndex,
}: TransitionPanelProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<TransitionStrategy | null>(null);

  // Strategy icon mapping
  // 策略图标映射
  const getStrategyIcon = (strategy: TransitionStrategy) => {
    switch (strategy) {
      case 'semantic_echo':
        return <Waves className="w-4 h-4" />;
      case 'logical_hook':
        return <MessageSquare className="w-4 h-4" />;
      case 'rhythm_break':
        return <Shuffle className="w-4 h-4" />;
    }
  };

  // Strategy color mapping
  // 策略颜色映射
  const getStrategyColor = (strategy: TransitionStrategy) => {
    switch (strategy) {
      case 'semantic_echo':
        return 'bg-blue-50 border-blue-200 text-blue-700';
      case 'logical_hook':
        return 'bg-purple-50 border-purple-200 text-purple-700';
      case 'rhythm_break':
        return 'bg-amber-50 border-amber-200 text-amber-700';
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

  return (
    <div className="card p-4 space-y-4">
      {/* Header */}
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Link className="w-5 h-5 text-indigo-600" />
          <h3 className="font-semibold text-gray-800">
            接缝修补 {transitionIndex && `#${transitionIndex}`}
          </h3>
          <span className="text-sm text-gray-500">/ Transition Repair</span>
          <InfoTooltip
            title="Level 2: 关节润滑"
            content="分析相邻段落的衔接方式，检测AI过度使用的显性连接词和公式化模式，提供三种策略建议来建立更自然的语义流。"
          />
        </div>

        {/* Risk Badge */}
        <div className="flex items-center space-x-2">
          <span className={clsx(
            'px-2 py-0.5 rounded-full text-xs font-medium',
            getRiskColor(analysis.riskLevel)
          )}>
            平滑度: {analysis.smoothnessScore}
          </span>
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

      {/* Transition Zone Display */}
      {/* 过渡区域显示 */}
      <div className="space-y-3">
        {/* Paragraph A Ending */}
        <div className="p-3 bg-gray-50 rounded-lg border-l-4 border-gray-300">
          <p className="text-xs text-gray-500 mb-1">段落A结尾 / Para A Ending</p>
          <p className="text-sm text-gray-800">{analysis.paraAEnding}</p>
          {analysis.hasSummaryEnding && (
            <span className="inline-block mt-2 px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded">
              检测到总结模式
            </span>
          )}
        </div>

        {/* Connection Indicator */}
        <div className="flex justify-center">
          <div className="flex items-center text-gray-400">
            <div className="w-8 h-px bg-gray-300"></div>
            <span className="px-2 text-xs">衔接</span>
            <div className="w-8 h-px bg-gray-300"></div>
          </div>
        </div>

        {/* Paragraph B Opening */}
        <div className="p-3 bg-gray-50 rounded-lg border-l-4 border-indigo-300">
          <p className="text-xs text-gray-500 mb-1">段落B开头 / Para B Opening</p>
          <p className="text-sm text-gray-800">{analysis.paraBOpening}</p>
          {analysis.explicitConnectors.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {analysis.explicitConnectors.map((connector, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded"
                >
                  {connector}
                </span>
              ))}
            </div>
          )}
          {analysis.hasTopicSentencePattern && (
            <span className="inline-block mt-2 px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded">
              检测到主题句模式
            </span>
          )}
        </div>
      </div>

      {/* Issues Summary */}
      {/* 问题摘要 */}
      {analysis.issues.length > 0 && (
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
            检测到 {analysis.issues.length} 个问题
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
                  <span className="font-medium">[{issue.severity}]</span>{' '}
                  {issue.descriptionZh}
                  {issue.word && (
                    <span className="ml-1 font-mono bg-white px-1 rounded">
                      {issue.word}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Strategy Options */}
      {/* 策略选项 */}
      {analysis.options.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm font-medium text-gray-700">修复策略 / Repair Strategies</p>

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
                {option.keyConcepts && option.keyConcepts.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    <span className="text-xs text-gray-500">回声概念:</span>
                    {option.keyConcepts.map((concept, idx) => (
                      <span
                        key={idx}
                        className="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-xs rounded"
                      >
                        {concept}
                      </span>
                    ))}
                  </div>
                )}

                {option.hookType && (
                  <div className="text-xs text-gray-500 mt-1">
                    设问类型: <span className="text-purple-600">{option.hookType}</span>
                  </div>
                )}

                {option.rhythmChange && (
                  <div className="text-xs text-gray-500 mt-1">
                    节奏变化: <span className="text-amber-600">{option.rhythmChange}</span>
                  </div>
                )}

                {/* Preview when selected */}
                {selectedStrategy === option.strategy && (
                  <div className="mt-3 pt-3 border-t border-current border-opacity-20 space-y-2">
                    <p className="text-xs font-medium">修改预览:</p>
                    <div className="p-2 bg-white bg-opacity-50 rounded text-xs">
                      <p className="text-gray-600 mb-1">段落A结尾:</p>
                      <p className="text-gray-800">{option.paraAEnding}</p>
                    </div>
                    <div className="p-2 bg-white bg-opacity-50 rounded text-xs">
                      <p className="text-gray-600 mb-1">段落B开头:</p>
                      <p className="text-gray-800">{option.paraBOpening}</p>
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
      {analysis.riskLevel === 'low' && analysis.options.length === 0 && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-center">
          <CheckCircle className="w-5 h-5 text-green-500 mx-auto mb-1" />
          <p className="text-sm text-green-700">衔接自然，无需修改</p>
          <p className="text-xs text-green-600">Transition appears natural</p>
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
 * Compact transition card for document overview
 * 用于文档概览的紧凑衔接卡片
 */
export function TransitionCard({
  analysis,
  index,
  onClick,
}: {
  analysis: TransitionAnalysisResponse;
  index: number;
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
          衔接 #{index + 1}
        </span>
        <span className={clsx(
          'px-2 py-0.5 rounded text-xs',
          analysis.riskLevel === 'high' && 'bg-red-100 text-red-700',
          analysis.riskLevel === 'medium' && 'bg-amber-100 text-amber-700',
          analysis.riskLevel === 'low' && 'bg-green-100 text-green-700'
        )}>
          {analysis.smoothnessScore}分
        </span>
      </div>

      <p className="text-xs text-gray-600 line-clamp-2 mb-1">
        {analysis.paraBOpening.slice(0, 100)}...
      </p>

      {analysis.issues.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {analysis.explicitConnectors.slice(0, 2).map((c, idx) => (
            <span key={idx} className="px-1 bg-red-100 text-red-600 text-xs rounded">
              {c}
            </span>
          ))}
          {analysis.issues.length > 2 && (
            <span className="text-xs text-gray-500">
              +{analysis.issues.length - 2}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
