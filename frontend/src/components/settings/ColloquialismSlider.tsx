import { useMemo } from 'react';
import { useConfigStore, getLevelInfo } from '../../stores/configStore';

interface ColloquialismSliderProps {
  value?: number;
  onChange?: (value: number) => void;
  showRecommendations?: boolean;
}

/**
 * Colloquialism level slider component
 * 口语化程度滑块组件
 */
export default function ColloquialismSlider({
  value,
  onChange,
  showRecommendations = true,
}: ColloquialismSliderProps) {
  const { colloquialismLevel, setColloquialismLevel } = useConfigStore();

  const currentValue = value ?? colloquialismLevel;
  const handleChange = onChange ?? setColloquialismLevel;

  const currentLevel = useMemo(() => getLevelInfo(currentValue), [currentValue]);

  // Recommendation labels
  // 推荐标签
  const recommendations = [
    { level: 1, label: '期刊' },
    { level: 4, label: '论文' },
    { level: 5, label: '作业' },
    { level: 6, label: '会议' },
  ];

  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-gray-700">
          口语化程度 (Colloquialism Level)
        </label>
        <span className="text-sm text-gray-500">
          {currentValue}/10
        </span>
      </div>

      {/* Slider */}
      <div className="relative">
        <input
          type="range"
          min="0"
          max="10"
          value={currentValue}
          onChange={(e) => handleChange(parseInt(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer
                     [&::-webkit-slider-thumb]:appearance-none
                     [&::-webkit-slider-thumb]:w-5
                     [&::-webkit-slider-thumb]:h-5
                     [&::-webkit-slider-thumb]:bg-primary-600
                     [&::-webkit-slider-thumb]:rounded-full
                     [&::-webkit-slider-thumb]:cursor-pointer
                     [&::-webkit-slider-thumb]:shadow-md
                     [&::-webkit-slider-thumb]:transition-transform
                     [&::-webkit-slider-thumb]:hover:scale-110"
        />

        {/* Tick marks */}
        <div className="flex justify-between px-0.5 mt-1">
          {[0, 2, 4, 6, 8, 10].map((tick) => (
            <div
              key={tick}
              className="flex flex-col items-center"
            >
              <div className="w-0.5 h-1.5 bg-gray-300" />
              <span className="text-xs text-gray-400 mt-0.5">{tick}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Labels */}
      <div className="flex justify-between mt-1 text-xs text-gray-500">
        <span>学术化</span>
        <span>口语化</span>
      </div>

      {/* Current level info */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="font-medium text-gray-800">
            {currentLevel.nameZh}
          </span>
          <span className="text-sm text-gray-500">
            {currentLevel.name}
          </span>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          {currentLevel.description}
        </p>
      </div>

      {/* Recommendations */}
      {showRecommendations && (
        <div className="mt-3">
          <p className="text-xs text-gray-500 mb-2">推荐设置:</p>
          <div className="flex flex-wrap gap-2">
            {recommendations.map((rec) => (
              <button
                key={rec.level}
                onClick={() => handleChange(rec.level)}
                className={`
                  px-2 py-1 text-xs rounded-full transition-colors
                  ${currentValue === rec.level
                    ? 'bg-primary-100 text-primary-700 font-medium'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }
                `}
              >
                {rec.label}: {rec.level}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
