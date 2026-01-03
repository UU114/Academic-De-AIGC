/**
 * Loading Message Component with Fun Messages
 * 趣味等待提示组件
 *
 * Displays rotating fun messages while users wait for AI processing
 * 在用户等待AI处理时显示轮播趣味提示语
 */

// React hooks imported as needed by child components
import { Loader2, Clock } from 'lucide-react';
import { useRotatingLoadingMessage, estimateWaitTime, useCountdownTimer } from '../../utils/loadingMessages';
import type { LoadingMessageProps } from '../../utils/loadingMessages';

interface Props extends LoadingMessageProps {
  /** Optional custom icon component */
  icon?: React.ReactNode;
  /** Size variant: 'sm' | 'md' | 'lg' */
  size?: 'sm' | 'md' | 'lg';
  /** Center the loading message */
  centered?: boolean;
  /** Document character count for time estimation */
  charCount?: number;
  /** Show countdown timer */
  showCountdown?: boolean;
}

/**
 * LoadingMessage - A fun, rotating loading indicator
 * 趣味轮播加载指示器
 */
export default function LoadingMessage({
  category = 'general',
  rotate = true,
  intervalMs = 3500,
  showEnglish = true,
  className = '',
  icon,
  size = 'md',
  centered = false,
  charCount,
  showCountdown = false,
}: Props) {
  const message = useRotatingLoadingMessage(category, rotate ? intervalMs : 999999);

  // Calculate estimated time if charCount provided
  // 如果提供了字符数则计算预估时间
  const analysisType = category === 'structure' ? 'structure'
    : category === 'suggestion' ? 'suggestion'
    : category === 'transition' ? 'transition'
    : category === 'paragraph' ? 'paragraph'
    : 'structure';
  const estimate = charCount ? estimateWaitTime(charCount, analysisType) : null;

  // Countdown timer
  // 倒计时
  const countdown = useCountdownTimer(estimate?.seconds || 60, showCountdown && !!estimate);

  // Size classes
  // 尺寸样式
  const sizeClasses = {
    sm: {
      icon: 'w-4 h-4',
      textZh: 'text-sm',
      textEn: 'text-xs',
      gap: 'ml-2',
    },
    md: {
      icon: 'w-5 h-5',
      textZh: 'text-base',
      textEn: 'text-sm',
      gap: 'ml-3',
    },
    lg: {
      icon: 'w-6 h-6',
      textZh: 'text-lg',
      textEn: 'text-base',
      gap: 'ml-4',
    },
  };

  const sizes = sizeClasses[size];

  return (
    <div
      className={`flex items-center ${centered ? 'justify-center' : ''} ${className}`}
    >
      {icon || (
        <Loader2 className={`${sizes.icon} animate-spin text-blue-500`} />
      )}
      <div className={sizes.gap}>
        <p className={`${sizes.textZh} text-gray-700 font-medium`}>
          {message.zh}
        </p>
        {showEnglish && (
          <p className={`${sizes.textEn} text-gray-400 mt-0.5`}>
            {message.en}
          </p>
        )}
        {/* Estimated time display */}
        {/* 预估时间显示 */}
        {estimate && (
          <div className="flex items-center mt-1.5 text-xs">
            <Clock className="w-3 h-3 mr-1 text-gray-400" />
            {showCountdown ? (
              <span className={countdown.isOvertime ? 'text-amber-500' : 'text-gray-500'}>
                {countdown.formatted}
              </span>
            ) : (
              <span className="text-gray-500">
                预计等待 {estimate.formatted}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * FullPageLoading - Full page loading overlay with fun messages
 * 全页加载遮罩层
 */
export function FullPageLoading({
  category = 'general',
  showEnglish = true,
  charCount,
  showCountdown = true,
}: {
  category?: LoadingMessageProps['category'];
  showEnglish?: boolean;
  charCount?: number;
  showCountdown?: boolean;
}) {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-10 h-10 animate-spin text-blue-500 mx-auto mb-4" />
        <LoadingMessage
          category={category}
          showEnglish={showEnglish}
          centered
          size="lg"
          charCount={charCount}
          showCountdown={showCountdown}
        />
      </div>
    </div>
  );
}

/**
 * InlineLoading - Compact inline loading indicator
 * 紧凑型内联加载指示器
 */
export function InlineLoading({
  category = 'general',
  showEnglish = false,
  className = '',
}: {
  category?: LoadingMessageProps['category'];
  showEnglish?: boolean;
  className?: string;
}) {
  return (
    <LoadingMessage
      category={category}
      showEnglish={showEnglish}
      size="sm"
      className={className}
    />
  );
}

/**
 * CardLoading - Loading state for card components
 * 卡片组件加载状态
 */
export function CardLoading({
  category = 'general',
  showEnglish = true,
}: {
  category?: LoadingMessageProps['category'];
  showEnglish?: boolean;
}) {
  return (
    <div className="p-6 flex items-center justify-center bg-gray-50 rounded-lg">
      <LoadingMessage
        category={category}
        showEnglish={showEnglish}
        size="md"
        centered
      />
    </div>
  );
}
