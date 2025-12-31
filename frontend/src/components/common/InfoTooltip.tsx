import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Info } from 'lucide-react';
import { clsx } from 'clsx';

interface InfoTooltipProps {
  content: string;
  title?: string;
  className?: string;
  iconSize?: 'sm' | 'md';
}

/**
 * Info icon with tooltip on click/hover
 * Uses React Portal to render tooltip outside of overflow:hidden containers
 * 带点击/悬停提示的信息图标
 * 使用React Portal渲染到body，避免被overflow:hidden容器裁剪
 */
export default function InfoTooltip({
  content,
  title,
  className,
  iconSize = 'sm',
}: InfoTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLSpanElement>(null);

  // Calculate tooltip position when showing
  // 显示时计算tooltip位置
  const showTooltip = () => {
    if (!triggerRef.current) return;

    const rect = triggerRef.current.getBoundingClientRect();
    const tooltipWidth = 256;

    // Position above the button, centered horizontally
    // 定位在按钮上方，水平居中
    let left = rect.left + rect.width / 2 - tooltipWidth / 2;
    let top = rect.top - 8; // 8px gap above button

    // Keep within viewport horizontally
    // 保持在视口水平范围内
    if (left < 8) left = 8;
    if (left + tooltipWidth > window.innerWidth - 8) {
      left = window.innerWidth - tooltipWidth - 8;
    }

    setTooltipPos({ top, left });
    setIsVisible(true);
  };

  // Close tooltip when clicking outside
  // 点击外部时关闭提示
  useEffect(() => {
    if (!isVisible) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (triggerRef.current && !triggerRef.current.contains(e.target as Node)) {
        setIsVisible(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isVisible]);

  const iconSizeClass = iconSize === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4';

  return (
    <div className={clsx('relative inline-flex items-center', className)}>
      {/* Use span instead of button to avoid nesting buttons */}
      {/* 使用span代替button以避免按钮嵌套问题 */}
      <span
        ref={triggerRef}
        role="button"
        tabIndex={0}
        onClick={(e) => {
          e.stopPropagation(); // Prevent parent button click
          isVisible ? setIsVisible(false) : showTooltip();
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            e.stopPropagation();
            isVisible ? setIsVisible(false) : showTooltip();
          }
        }}
        onMouseEnter={showTooltip}
        onMouseLeave={() => setIsVisible(false)}
        className="text-gray-400 hover:text-gray-600 transition-colors focus:outline-none cursor-pointer"
        aria-label="More information"
      >
        <Info className={iconSizeClass} />
      </span>

      {isVisible && createPortal(
        <div
          style={{
            position: 'fixed',
            top: tooltipPos.top,
            left: tooltipPos.left,
            transform: 'translateY(-100%)',
          }}
          className="z-[9999] w-64 p-3 bg-gray-800 text-white text-sm rounded-lg shadow-lg"
        >
          {title && (
            <p className="font-medium text-gray-100 mb-1">{title}</p>
          )}
          <p className="text-gray-300 text-xs leading-relaxed">{content}</p>
        </div>,
        document.body
      )}
    </div>
  );
}
