import { clsx } from 'clsx';
import { AlertTriangle, CheckCircle, AlertCircle, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

/**
 * SubstepRiskCard Component
 * 子步骤风险卡片组件
 *
 * Displays risk assessment for a single substep with:
 * - Risk score and level
 * - Dimension scores with progress bars
 * - Issues and recommendations
 * - Human features detected
 */

// Type definitions based on backend schemas
// 基于后端schema的类型定义
export interface DimensionScore {
  dimension_id: string;
  dimension_name: string;
  dimension_name_zh: string;
  value: number;
  threshold_ai: number;
  threshold_human: number;
  weight: number;
  risk_contribution: number;
  status: 'ai_like' | 'borderline' | 'human_like';
  description: string;
  description_zh: string;
}

export interface DetectionIssue {
  type: string;
  description: string;
  description_zh: string;
  severity: 'low' | 'medium' | 'high';
  layer: string;
  position?: string;
  suggestion: string;
  suggestion_zh: string;
  details?: Record<string, unknown>;
}

export interface SubstepRiskAssessment {
  substep_id: string;
  substep_name: string;
  substep_name_zh: string;
  layer: string;
  risk_score: number;
  risk_level: 'safe' | 'low' | 'medium' | 'high';
  dimension_scores: Record<string, DimensionScore>;
  issues: DetectionIssue[];
  recommendations: string[];
  recommendations_zh: string[];
  processing_time_ms?: number;
  human_features_detected: string[];
  human_features_detected_zh: string[];
}

interface SubstepRiskCardProps {
  assessment: SubstepRiskAssessment;
  showDetails?: boolean;
  className?: string;
}

// Risk level color mapping
// 风险等级颜色映射
const riskColors = {
  safe: { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-200', bar: 'bg-green-500' },
  low: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-200', bar: 'bg-blue-500' },
  medium: { bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-200', bar: 'bg-yellow-500' },
  high: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-200', bar: 'bg-red-500' },
};

// Status indicator mapping
// 状态指示映射
const statusColors = {
  ai_like: { bg: 'bg-red-100', text: 'text-red-600', label: 'AI-like', label_zh: 'AI特征' },
  borderline: { bg: 'bg-yellow-100', text: 'text-yellow-600', label: 'Borderline', label_zh: '边界' },
  human_like: { bg: 'bg-green-100', text: 'text-green-600', label: 'Human-like', label_zh: '人类特征' },
};

export default function SubstepRiskCard({
  assessment,
  showDetails = true,
  className = '',
}: SubstepRiskCardProps) {
  const [isExpanded, setIsExpanded] = useState(showDetails);

  const colors = riskColors[assessment.risk_level] || riskColors.low;
  const dimensionEntries = Object.entries(assessment.dimension_scores);

  return (
    <div className={clsx('rounded-lg border shadow-sm', colors.border, className)}>
      {/* Header */}
      <div
        className={clsx('px-4 py-3 rounded-t-lg flex items-center justify-between cursor-pointer', colors.bg)}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          {/* Risk indicator */}
          <div className={clsx(
            'w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg',
            colors.text,
            colors.bg
          )}>
            {assessment.risk_score}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">
              {assessment.substep_name}
            </h3>
            <p className="text-sm text-gray-600">{assessment.substep_name_zh}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={clsx(
            'px-2 py-1 rounded text-xs font-medium uppercase',
            colors.bg,
            colors.text
          )}>
            {assessment.risk_level}
          </span>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-500" />
          )}
        </div>
      </div>

      {/* Expandable content */}
      {isExpanded && (
        <div className="p-4 space-y-4 bg-white rounded-b-lg">
          {/* Dimension Scores */}
          {dimensionEntries.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Dimension Scores / 维度分数
              </h4>
              <div className="space-y-2">
                {dimensionEntries.map(([key, dim]) => (
                  <DimensionScoreBar key={key} dimension={dim} />
                ))}
              </div>
            </div>
          )}

          {/* Human Features */}
          {assessment.human_features_detected.length > 0 && (
            <div className="p-3 bg-green-50 rounded-lg">
              <div className="flex items-center gap-2 text-green-700 mb-2">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm font-medium">Human Features Detected / 检测到的人类特征</span>
              </div>
              <ul className="space-y-1">
                {assessment.human_features_detected.map((feature, idx) => (
                  <li key={idx} className="text-sm text-green-600 flex items-start gap-1">
                    <span className="text-green-400 mt-1">•</span>
                    <span>{feature}</span>
                    {assessment.human_features_detected_zh[idx] && (
                      <span className="text-gray-500">({assessment.human_features_detected_zh[idx]})</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Issues */}
          {assessment.issues.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                Issues Detected / 检测到的问题 ({assessment.issues.length})
              </h4>
              <div className="space-y-2">
                {assessment.issues.map((issue, idx) => (
                  <IssueCard key={idx} issue={issue} />
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {assessment.recommendations.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <Info className="w-4 h-4 text-blue-500" />
                Recommendations / 建议
              </h4>
              <ul className="space-y-1">
                {assessment.recommendations.map((rec, idx) => (
                  <li key={idx} className="text-sm">
                    <p className="text-gray-700">{rec}</p>
                    {assessment.recommendations_zh[idx] && (
                      <p className="text-gray-500 text-xs">{assessment.recommendations_zh[idx]}</p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Processing time */}
          {assessment.processing_time_ms !== undefined && (
            <div className="text-xs text-gray-400 text-right">
              Processed in {assessment.processing_time_ms}ms
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Dimension score progress bar component
// 维度分数进度条组件
function DimensionScoreBar({ dimension }: { dimension: DimensionScore }) {
  const statusStyle = statusColors[dimension.status] || statusColors.borderline;

  // Calculate position markers for thresholds
  // 计算阈值的位置标记
  const valuePercent = Math.min(100, Math.max(0, dimension.value));
  const aiThresholdPercent = Math.min(100, Math.max(0, dimension.threshold_ai));
  const humanThresholdPercent = Math.min(100, Math.max(0, dimension.threshold_human));

  // Determine bar color based on status
  // 根据状态确定进度条颜色
  const barColor = {
    ai_like: 'bg-red-400',
    borderline: 'bg-yellow-400',
    human_like: 'bg-green-400',
  }[dimension.status] || 'bg-gray-400';

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-700">{dimension.dimension_name}</span>
          <span className="text-xs text-gray-400">({dimension.dimension_name_zh})</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={clsx(
            'px-1.5 py-0.5 rounded text-xs',
            statusStyle.bg,
            statusStyle.text
          )}>
            {statusStyle.label_zh}
          </span>
          <span className="text-sm font-medium text-gray-700">
            {typeof dimension.value === 'number' ? dimension.value.toFixed(2) : dimension.value}
          </span>
        </div>
      </div>
      <div className="relative h-2 bg-gray-200 rounded-full">
        {/* Progress bar */}
        <div
          className={clsx('h-full rounded-full transition-all', barColor)}
          style={{ width: `${valuePercent}%` }}
        />
        {/* Threshold markers */}
        <div
          className="absolute top-0 h-full w-0.5 bg-red-600 opacity-50"
          style={{ left: `${aiThresholdPercent}%` }}
          title={`AI Threshold: ${dimension.threshold_ai}`}
        />
        <div
          className="absolute top-0 h-full w-0.5 bg-green-600 opacity-50"
          style={{ left: `${humanThresholdPercent}%` }}
          title={`Human Threshold: ${dimension.threshold_human}`}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-400">
        <span>Risk: +{dimension.risk_contribution}</span>
        <span>Weight: {(dimension.weight * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
}

// Issue card component
// 问题卡片组件
function IssueCard({ issue }: { issue: DetectionIssue }) {
  const severityColors = {
    low: 'border-blue-200 bg-blue-50',
    medium: 'border-yellow-200 bg-yellow-50',
    high: 'border-red-200 bg-red-50',
  };

  const severityIcons = {
    low: <Info className="w-4 h-4 text-blue-500" />,
    medium: <AlertCircle className="w-4 h-4 text-yellow-500" />,
    high: <AlertTriangle className="w-4 h-4 text-red-500" />,
  };

  return (
    <div className={clsx(
      'p-2 rounded border',
      severityColors[issue.severity] || severityColors.medium
    )}>
      <div className="flex items-start gap-2">
        {severityIcons[issue.severity] || severityIcons.medium}
        <div className="flex-1">
          <p className="text-sm text-gray-700">{issue.description}</p>
          <p className="text-xs text-gray-500">{issue.description_zh}</p>
          {issue.suggestion && (
            <p className="text-xs text-blue-600 mt-1">
              → {issue.suggestion}
            </p>
          )}
        </div>
        <span className={clsx(
          'text-xs px-1.5 py-0.5 rounded uppercase',
          issue.severity === 'high' ? 'bg-red-100 text-red-600' :
          issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-600' :
          'bg-blue-100 text-blue-600'
        )}>
          {issue.severity}
        </span>
      </div>
    </div>
  );
}
