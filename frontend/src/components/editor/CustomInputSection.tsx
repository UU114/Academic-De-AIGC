import { useState, useEffect, useRef, useCallback } from 'react';
import { Check, X, Loader2, Search, Lightbulb } from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../common/Button';
import { suggestApi } from '../../services/api';
import { useSessionStore } from '../../stores/sessionStore';

interface WritingHint {
  type: string;
  title: string;
  titleZh: string;
  description: string;
  descriptionZh: string;
}

interface CustomInputSectionProps {
  originalText: string;
  customText: string;
  onCustomTextChange: (text: string) => void;
  onValidateCustom: () => void;
  validationResult?: {
    passed: boolean;
    similarity: number;
    message: string;
  } | null;
  onApplyCustom: () => void;
  onAnalysisToggle: (show: boolean) => void;
  showAnalysis: boolean;
  loadingAnalysis: boolean;
  hasAnalysisResult: boolean;
  sentenceId?: string;
}

/**
 * Custom input section for Track C
 * Separated from SuggestionPanel for flexible layout
 * 轨道C的自定义输入区域
 * 从SuggestionPanel分离以支持灵活布局
 */
export default function CustomInputSection({
  originalText,
  customText,
  onCustomTextChange,
  onValidateCustom,
  validationResult,
  onApplyCustom,
  onAnalysisToggle,
  showAnalysis,
  loadingAnalysis,
  hasAnalysisResult,
  sentenceId,
}: CustomInputSectionProps) {
  const [writingHints, setWritingHints] = useState<WritingHint[]>([]);
  const [loadingHints, setLoadingHints] = useState(false);
  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Get cache methods from store
  // 从 store 获取缓存方法
  const {
    setCustomTextForSentence,
    getCustomTextForSentence,
  } = useSessionStore();

  // Load cached custom text when sentence changes
  // 当句子变化时加载缓存的自定义文本
  useEffect(() => {
    if (sentenceId) {
      const cachedText = getCustomTextForSentence(sentenceId);
      if (cachedText && cachedText !== customText) {
        onCustomTextChange(cachedText);
      }
    }
  }, [sentenceId]);

  // Auto-save custom text to cache every 15 seconds
  // 每15秒自动保存自定义文本到缓存
  useEffect(() => {
    if (sentenceId && customText) {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
      autoSaveTimerRef.current = setTimeout(() => {
        setCustomTextForSentence(sentenceId, customText);
      }, 15000);
    }
    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, [customText, sentenceId, setCustomTextForSentence]);

  // Save custom text immediately on change
  // 变更时立即保存自定义文本
  const handleCustomTextChange = useCallback((text: string) => {
    onCustomTextChange(text);
    if (sentenceId && text) {
      setCustomTextForSentence(sentenceId, text);
    }
  }, [onCustomTextChange, sentenceId, setCustomTextForSentence]);

  // Load writing hints
  // 加载写作提示
  useEffect(() => {
    if (originalText && !showAnalysis) {
      loadWritingHints(originalText);
    }
  }, [originalText, showAnalysis]);

  const loadWritingHints = async (sentence: string) => {
    setLoadingHints(true);
    try {
      const result = await suggestApi.getWritingHints(sentence);
      setWritingHints(result.hints || []);
    } catch (err) {
      console.error('Failed to load writing hints:', err);
      setWritingHints([]);
    } finally {
      setLoadingHints(false);
    }
  };

  return (
    <div className="space-y-3">
      {/* Writing Hints - hide when analysis is shown */}
      {/* 写作提示 - 分析显示时隐藏 */}
      {!showAnalysis && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <div className="flex items-center text-amber-700 mb-2">
            <Lightbulb className="w-4 h-4 mr-2" />
            <span className="text-sm font-medium">改写建议 / Writing Hints</span>
          </div>
          {loadingHints ? (
            <div className="flex items-center text-amber-600 text-sm">
              <Loader2 className="w-3 h-3 mr-2 animate-spin" />
              加载中...
            </div>
          ) : (
            <div className="space-y-2">
              {writingHints.map((hint, idx) => (
                <div key={idx} className="text-sm">
                  <p className="font-medium text-amber-800">
                    {idx + 1}. {hint.titleZh}
                  </p>
                  <p className="text-amber-700 text-xs mt-0.5">
                    {hint.descriptionZh}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Text input */}
      {/* 文本输入框 */}
      <textarea
        value={customText}
        onChange={(e) => handleCustomTextChange(e.target.value)}
        placeholder="输入您的修改版本..."
        className="textarea h-24"
      />

      {/* Validation result */}
      {/* 验证结果 */}
      {validationResult && (
        <div
          className={clsx(
            'p-3 rounded-lg flex items-start',
            validationResult.passed
              ? 'bg-green-50 text-green-700'
              : 'bg-red-50 text-red-700'
          )}
        >
          {validationResult.passed ? (
            <Check className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
          ) : (
            <X className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
          )}
          <div className="text-sm">
            <p>{validationResult.message}</p>
            <p className="text-xs mt-1">
              语义相似度: {(validationResult.similarity * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      )}

      {/* Action buttons */}
      {/* 操作按钮 */}
      <div className="flex items-center space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onAnalysisToggle(!showAnalysis)}
          disabled={loadingAnalysis}
        >
          {loadingAnalysis ? (
            <>
              <Loader2 className="w-3 h-3 mr-1 animate-spin" />
              分析中...
            </>
          ) : hasAnalysisResult ? (
            <>
              <Search className="w-3 h-3 mr-1" />
              {showAnalysis ? '隐藏分析' : '显示分析'}
            </>
          ) : (
            <>
              <Search className="w-3 h-3 mr-1" />
              分析
            </>
          )}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onValidateCustom}
          disabled={!customText.trim()}
        >
          检测风险
        </Button>
        <Button
          variant="primary"
          size="sm"
          onClick={onApplyCustom}
          disabled={!customText.trim() || !validationResult?.passed}
        >
          确认提交
        </Button>
      </div>
    </div>
  );
}
