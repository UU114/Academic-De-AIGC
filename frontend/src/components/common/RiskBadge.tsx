import { clsx } from 'clsx';
import type { RiskLevel } from '../../types';

interface RiskBadgeProps {
  level: RiskLevel;
  score?: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const levelConfig: Record<RiskLevel, { label: string; labelZh: string; bgClass: string; textClass: string }> = {
  safe: {
    label: 'Safe',
    labelZh: '安全',
    bgClass: 'bg-blue-100',
    textClass: 'text-blue-800',
  },
  low: {
    label: 'Low Risk',
    labelZh: '低风险',
    bgClass: 'bg-green-100',
    textClass: 'text-green-800',
  },
  medium: {
    label: 'Medium Risk',
    labelZh: '中风险',
    bgClass: 'bg-amber-100',
    textClass: 'text-amber-800',
  },
  high: {
    label: 'High Risk',
    labelZh: '高风险',
    bgClass: 'bg-red-100',
    textClass: 'text-red-800',
  },
};

const sizeConfig: Record<'sm' | 'md' | 'lg', string> = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base',
};

/**
 * Risk level badge component
 * 风险等级徽章组件
 */
export default function RiskBadge({
  level,
  score,
  size = 'md',
  showLabel = true,
}: RiskBadgeProps) {
  const config = levelConfig[level];

  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium rounded-full',
        config.bgClass,
        config.textClass,
        sizeConfig[size]
      )}
    >
      {score !== undefined && (
        <span className="font-bold mr-1">{score}</span>
      )}
      {showLabel && <span>{config.labelZh}</span>}
    </span>
  );
}
