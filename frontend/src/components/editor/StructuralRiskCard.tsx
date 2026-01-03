import { useState, useEffect } from 'react';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../common/Button';
import InfoTooltip from '../common/InfoTooltip';

interface StructuralIndicator {
  id: string;
  name: string;
  nameZh: string;
  triggered: boolean;
  riskLevel: number;
  emoji: string;
  color: string;
  description: string;
  descriptionZh: string;
  details?: string;
  detailsZh?: string;
}

interface StructuralRiskCardProps {
  indicators?: StructuralIndicator[];
  triggeredCount?: number;
  overallRisk?: 'low' | 'medium' | 'high';
  overallRiskZh?: string;
  summary?: string;
  summaryZh?: string;
  totalScore?: number;
  isLoading?: boolean;
  onRefresh?: () => void;
}

/**
 * Structural Risk Card - 7-Indicator Visualization
 * 结构风险卡片 - 7指征可视化
 *
 * Displays at-a-glance view of AI structural patterns with:
 * - 7 indicators with emoji and color coding
 * - Triggered count and overall risk level
 * - One-line summary with emoji
 */
export default function StructuralRiskCard({
  indicators = [],
  triggeredCount = 0,
  overallRisk = 'low',
  overallRiskZh = '低风险',
  summary = '',
  summaryZh = '',
  totalScore = 0,
  isLoading = false,
  onRefresh,
}: StructuralRiskCardProps) {
  const [showDetails, setShowDetails] = useState(false);

  // Get overall risk color
  // 获取整体风险颜色
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
        return 'text-amber-600 bg-amber-50 border-amber-200';
      default:
        return 'text-green-600 bg-green-50 border-green-200';
    }
  };

  // Get risk level stars
  // 获取风险等级星星
  const getStars = (level: number) => {
    return '★'.repeat(level) + '☆'.repeat(3 - level);
  };

  // Get indicator background based on triggered state
  // 根据触发状态获取指标背景
  const getIndicatorBg = (indicator: StructuralIndicator) => {
    if (indicator.triggered) {
      return 'bg-red-50 border-red-200';
    }
    return 'bg-gray-50 border-gray-200';
  };

  if (isLoading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-center space-x-3">
          <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
          <span className="text-gray-600">分析结构特征中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="card p-4 space-y-4">
      {/* Header */}
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Shield className="w-5 h-5 text-indigo-600" />
          <h3 className="font-semibold text-gray-800">
            结构风险卡片 / Risk Card
          </h3>
          <InfoTooltip
            title="7-Indicator Analysis"
            content="分析7个AI结构特征指标：对称性、功能均匀、连接词依赖、线性推进、节奏均衡、过度闭合、缺乏回指。"
          />
        </div>
        <div className="flex items-center space-x-2">
          {onRefresh && (
            <Button variant="ghost" size="sm" onClick={onRefresh}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          )}
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

      {/* Summary */}
      {/* 摘要 */}
      <div className={clsx(
        'p-4 rounded-lg border-2 flex items-center justify-between',
        getRiskColor(overallRisk)
      )}>
        <div className="flex items-center space-x-3">
          {overallRisk === 'high' ? (
            <AlertTriangle className="w-6 h-6" />
          ) : overallRisk === 'medium' ? (
            <AlertTriangle className="w-6 h-6" />
          ) : (
            <CheckCircle className="w-6 h-6" />
          )}
          <div>
            <div className="font-semibold text-lg">
              {triggeredCount}/7 指标触发
            </div>
            <div className="text-sm opacity-80">
              {summaryZh || summary}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold">{totalScore}</div>
          <div className="text-sm">{overallRiskZh}</div>
        </div>
      </div>

      {/* Indicator Grid */}
      {/* 指标网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {indicators.map((indicator) => (
          <div
            key={indicator.id}
            className={clsx(
              'p-3 rounded-lg border transition-all',
              getIndicatorBg(indicator),
              indicator.triggered && 'ring-1 ring-red-300'
            )}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-xl">{indicator.emoji}</span>
                <div>
                  <div className="font-medium text-sm text-gray-800">
                    {indicator.nameZh}
                  </div>
                  <div className="text-xs text-gray-500">
                    {indicator.name}
                  </div>
                </div>
              </div>
              <div className={clsx(
                'px-1.5 py-0.5 rounded text-xs font-medium',
                indicator.triggered
                  ? 'bg-red-100 text-red-700'
                  : 'bg-green-100 text-green-700'
              )}>
                {indicator.triggered ? '触发' : 'OK'}
              </div>
            </div>

            {/* Risk Level Stars */}
            <div className="mt-2 flex items-center space-x-2">
              <span className="text-xs text-gray-500">风险:</span>
              <span className={clsx(
                'text-sm',
                indicator.riskLevel >= 3 ? 'text-red-500' :
                indicator.riskLevel >= 2 ? 'text-amber-500' : 'text-green-500'
              )}>
                {getStars(indicator.riskLevel)}
              </span>
            </div>

            {/* Details (when expanded) */}
            {showDetails && (
              <div className="mt-2 pt-2 border-t border-gray-200">
                <p className="text-xs text-gray-600">
                  {indicator.descriptionZh || indicator.description}
                </p>
                {indicator.detailsZh && (
                  <p className="text-xs text-gray-500 mt-1 italic">
                    {indicator.detailsZh}
                  </p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* The 7 Indicators Legend */}
      {/* 7指标图例 */}
      {showDetails && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg text-xs text-gray-600">
          <div className="font-medium mb-2">7 结构 AI 指标说明:</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <div>⚖️ 对称性 - 逻辑推进过于对称</div>
            <div>📊 均匀性 - 段落功能分布均匀</div>
            <div>🔗 连接词 - 过度依赖显性连接词</div>
            <div>📝 线性化 - 单一线性推进模式</div>
            <div>📏 节奏 - 句段节奏过于均衡</div>
            <div>🔒 闭合 - 结尾过度闭合公式化</div>
            <div>🔄 回指 - 缺乏跨段落回指结构</div>
          </div>
        </div>
      )}
    </div>
  );
}
