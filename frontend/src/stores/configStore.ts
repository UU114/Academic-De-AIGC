/**
 * Configuration state management
 * 配置状态管理
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { RiskLevel, ColloquialismLevelInfo } from '../types';

// Colloquialism level definitions
// 口语化等级定义
export const COLLOQUIALISM_LEVELS: ColloquialismLevelInfo[] = [
  { level: 0, name: 'Most Academic', nameZh: '最学术化', description: 'Journal paper level' },
  { level: 1, name: 'Very Academic', nameZh: '非常学术', description: 'Journal paper level' },
  { level: 2, name: 'Academic', nameZh: '学术化', description: 'Journal paper level' },
  { level: 3, name: 'Thesis Level', nameZh: '论文级', description: 'Thesis/Dissertation' },
  { level: 4, name: 'Moderate Academic', nameZh: '适度学术', description: 'Default thesis level' },
  { level: 5, name: 'Semi-formal', nameZh: '半正式', description: 'Conference paper' },
  { level: 6, name: 'Conference Level', nameZh: '会议级', description: 'Conference paper' },
  { level: 7, name: 'Technical Blog', nameZh: '技术博客', description: 'Professional blog' },
  { level: 8, name: 'Casual Professional', nameZh: '休闲专业', description: 'Technical blog' },
  { level: 9, name: 'Casual', nameZh: '休闲', description: 'Informal discussion' },
  { level: 10, name: 'Most Casual', nameZh: '最口语化', description: 'Casual discussion' },
];

interface ConfigState {
  // Settings
  // 设置
  colloquialismLevel: number;
  targetLang: string;
  processLevels: RiskLevel[];
  includeTurnitin: boolean;
  includeGptzero: boolean;

  // UI preferences
  // UI偏好
  showTranslation: boolean;
  showDetectorViews: boolean;
  autoLoadSuggestions: boolean;

  // Actions
  // 动作
  setColloquialismLevel: (level: number) => void;
  setTargetLang: (lang: string) => void;
  setProcessLevels: (levels: RiskLevel[]) => void;
  toggleProcessLevel: (level: RiskLevel) => void;
  setIncludeTurnitin: (include: boolean) => void;
  setIncludeGptzero: (include: boolean) => void;
  setShowTranslation: (show: boolean) => void;
  setShowDetectorViews: (show: boolean) => void;
  setAutoLoadSuggestions: (auto: boolean) => void;
  resetToDefaults: () => void;
}

const defaultState = {
  colloquialismLevel: 4,
  targetLang: 'zh',
  processLevels: ['high', 'medium'] as RiskLevel[],
  includeTurnitin: true,
  includeGptzero: true,
  showTranslation: true,
  showDetectorViews: true,
  autoLoadSuggestions: true,
};

export const useConfigStore = create<ConfigState>()(
  persist(
    (set) => ({
      ...defaultState,

      setColloquialismLevel: (level) =>
        set({ colloquialismLevel: Math.max(0, Math.min(10, level)) }),

      setTargetLang: (lang) => set({ targetLang: lang }),

      setProcessLevels: (levels) => set({ processLevels: levels }),

      toggleProcessLevel: (level) =>
        set((state) => {
          const levels = state.processLevels.includes(level)
            ? state.processLevels.filter((l) => l !== level)
            : [...state.processLevels, level];
          // Ensure at least high risk is always processed
          // 确保至少处理高风险
          if (levels.length === 0) {
            return { processLevels: ['high'] };
          }
          return { processLevels: levels };
        }),

      setIncludeTurnitin: (include) => set({ includeTurnitin: include }),

      setIncludeGptzero: (include) => set({ includeGptzero: include }),

      setShowTranslation: (show) => set({ showTranslation: show }),

      setShowDetectorViews: (show) => set({ showDetectorViews: show }),

      setAutoLoadSuggestions: (auto) => set({ autoLoadSuggestions: auto }),

      resetToDefaults: () => set(defaultState),
    }),
    {
      name: 'academicguard-config',
    }
  )
);

// Helper function to get level info
// 获取等级信息的辅助函数
export const getLevelInfo = (level: number): ColloquialismLevelInfo => {
  return COLLOQUIALISM_LEVELS[level] || COLLOQUIALISM_LEVELS[4];
};

// Helper function to get recommended level
// 获取推荐等级的辅助函数
export const getRecommendedLevel = (useCase: string): number => {
  switch (useCase) {
    case 'journal':
      return 1;
    case 'thesis':
      return 4;
    case 'conference':
      return 5;
    case 'assignment':
      return 5;
    case 'blog':
      return 7;
    default:
      return 4;
  }
};
