import { useState, useRef, useEffect } from 'react';
import { Info } from 'lucide-react';
import { clsx } from 'clsx';

interface InfoTooltipProps {
  content: string;
  title?: string;
  className?: string;
  iconSize?: 'sm' | 'md';
  position?: 'top' | 'bottom' | 'left' | 'right';
}

/**
 * Info icon with tooltip on click/hover
 * 带点击/悬停提示的信息图标
 */
export default function InfoTooltip({
  content,
  title,
  className,
  iconSize = 'sm',
  position = 'top',
}: InfoTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close tooltip when clicking outside
  // 点击外部时关闭提示
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        tooltipRef.current &&
        !tooltipRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsVisible(false);
      }
    };

    if (isVisible) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isVisible]);

  const iconSizeClass = iconSize === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4';

  // Position styles for tooltip
  // 提示框位置样式
  const positionStyles = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  // Arrow styles for tooltip
  // 提示框箭头样式
  const arrowStyles = {
    top: 'top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-gray-800',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-gray-800',
    left: 'left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-gray-800',
    right: 'right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-gray-800',
  };

  return (
    <div className={clsx('relative inline-flex items-center', className)}>
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setIsVisible(!isVisible)}
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="text-gray-400 hover:text-gray-600 transition-colors focus:outline-none"
        aria-label="More information"
      >
        <Info className={iconSizeClass} />
      </button>

      {isVisible && (
        <div
          ref={tooltipRef}
          className={clsx(
            'absolute z-50 w-64 p-3 bg-gray-800 text-white text-sm rounded-lg shadow-lg',
            positionStyles[position]
          )}
        >
          {/* Arrow */}
          <div
            className={clsx(
              'absolute w-0 h-0 border-4',
              arrowStyles[position]
            )}
          />

          {/* Content */}
          {title && (
            <p className="font-medium text-gray-100 mb-1">{title}</p>
          )}
          <p className="text-gray-300 text-xs leading-relaxed">{content}</p>
        </div>
      )}
    </div>
  );
}
