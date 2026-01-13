/**
 * Loading Overlay Component
 * 加载遮罩组件
 *
 * Displays a prominent loading overlay during long operations like LLM calls
 * 在长时间操作（如LLM调用）期间显示明显的加载遮罩层
 */

import { Loader2, Clock, Sparkles, Wand2 } from 'lucide-react';
import { useEffect, useState } from 'react';

interface LoadingOverlayProps {
  /** Whether the overlay is visible */
  isVisible: boolean;
  /** Operation type: 'prompt' for generating prompt, 'apply' for AI modification */
  operationType?: 'prompt' | 'apply';
  /** Custom title message in Chinese */
  titleZh?: string;
  /** Custom title message in English */
  titleEn?: string;
  /** Custom subtitle message in Chinese */
  subtitleZh?: string;
  /** Custom subtitle message in English */
  subtitleEn?: string;
  /** Optional: number of issues being processed */
  issueCount?: number;
}

// Rotating tip messages during loading
// 加载时轮换显示的提示消息
const loadingTips = [
  { zh: 'AI正在分析您的文本...', en: 'AI is analyzing your text...' },
  { zh: '正在生成最佳修改建议...', en: 'Generating optimal suggestions...' },
  { zh: '处理中，请稍候...', en: 'Processing, please wait...' },
  { zh: '这可能需要一些时间...', en: 'This may take a moment...' },
  { zh: '几乎完成了...', en: 'Almost there...' },
];

/**
 * LoadingOverlay - A prominent loading overlay for long operations
 * 用于长时间操作的明显加载遮罩层
 */
export default function LoadingOverlay({
  isVisible,
  operationType = 'apply',
  titleZh,
  titleEn,
  subtitleZh,
  subtitleEn,
  issueCount,
}: LoadingOverlayProps) {
  const [tipIndex, setTipIndex] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Rotate tips every 3 seconds
  // 每3秒轮换提示
  useEffect(() => {
    if (!isVisible) {
      setTipIndex(0);
      setElapsedTime(0);
      return;
    }

    const tipInterval = setInterval(() => {
      setTipIndex((prev) => (prev + 1) % loadingTips.length);
    }, 3000);

    const timeInterval = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);

    return () => {
      clearInterval(tipInterval);
      clearInterval(timeInterval);
    };
  }, [isVisible]);

  if (!isVisible) return null;

  // Default messages based on operation type
  // 根据操作类型设置默认消息
  const defaultTitleZh = operationType === 'prompt'
    ? '正在生成修改提示词...'
    : '正在进行AI修改...';
  const defaultTitleEn = operationType === 'prompt'
    ? 'Generating Modification Prompt...'
    : 'AI Modification in Progress...';
  const defaultSubtitleZh = operationType === 'prompt'
    ? 'AI正在分析问题并生成专业的修改建议'
    : 'AI正在根据检测结果智能修改您的文本';
  const defaultSubtitleEn = operationType === 'prompt'
    ? 'AI is analyzing issues and generating professional suggestions'
    : 'AI is intelligently modifying your text based on detection results';

  const Icon = operationType === 'prompt' ? Sparkles : Wand2;

  // Format elapsed time
  // 格式化已用时间
  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds}s`;
    }
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md mx-4 text-center transform animate-fade-in">
        {/* Icon with animation */}
        {/* 带动画的图标 */}
        <div className="relative mx-auto w-20 h-20 mb-6">
          <div className="absolute inset-0 bg-blue-100 rounded-full animate-ping opacity-25"></div>
          <div className="absolute inset-0 bg-blue-50 rounded-full flex items-center justify-center">
            <Icon className="w-10 h-10 text-blue-500 animate-pulse" />
          </div>
          <Loader2 className="absolute inset-0 w-20 h-20 text-blue-500 animate-spin" style={{ animationDuration: '3s' }} />
        </div>

        {/* Main title */}
        {/* 主标题 */}
        <h2 className="text-xl font-bold text-gray-800 mb-2">
          {titleZh || defaultTitleZh}
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          {titleEn || defaultTitleEn}
        </p>

        {/* Issue count badge */}
        {/* 问题数量徽章 */}
        {issueCount !== undefined && issueCount > 0 && (
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm mb-4">
            <span>正在处理 {issueCount} 个问题</span>
            <span className="text-blue-400">|</span>
            <span>Processing {issueCount} issue{issueCount > 1 ? 's' : ''}</span>
          </div>
        )}

        {/* Subtitle */}
        {/* 副标题 */}
        <p className="text-sm text-gray-600 mb-2">
          {subtitleZh || defaultSubtitleZh}
        </p>
        <p className="text-xs text-gray-400 mb-6">
          {subtitleEn || defaultSubtitleEn}
        </p>

        {/* Rotating tips */}
        {/* 轮换提示 */}
        <div className="bg-gray-50 rounded-lg p-4 mb-4 min-h-[60px] flex flex-col justify-center">
          <p className="text-sm text-gray-700 transition-opacity duration-300">
            {loadingTips[tipIndex].zh}
          </p>
          <p className="text-xs text-gray-400 mt-1 transition-opacity duration-300">
            {loadingTips[tipIndex].en}
          </p>
        </div>

        {/* Elapsed time */}
        {/* 已用时间 */}
        <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
          <Clock className="w-4 h-4" />
          <span>已等待 / Elapsed: {formatTime(elapsedTime)}</span>
        </div>

        {/* Progress dots */}
        {/* 进度点 */}
        <div className="flex justify-center gap-1 mt-4">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-2 h-2 rounded-full bg-blue-500 animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
