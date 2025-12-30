import { useMemo } from 'react';
import { AlertTriangle, Lock } from 'lucide-react';
import { clsx } from 'clsx';
import type { SentenceAnalysis } from '../../types';
import RiskBadge from '../common/RiskBadge';
import InfoTooltip from '../common/InfoTooltip';

interface SentenceCardProps {
  sentence: SentenceAnalysis;
  translation?: string;
  showTranslation?: boolean;
  showDetectorViews?: boolean;
  isActive?: boolean;
}

/**
 * Sentence card component with analysis display
 * 带分析显示的句子卡片组件
 */
export default function SentenceCard({
  sentence,
  translation,
  showTranslation = true,
  showDetectorViews = true,
  isActive = false,
}: SentenceCardProps) {
  // Highlight fingerprint words in text
  // 高亮文本中的指纹词
  const highlightedText = useMemo(() => {
    if (!sentence.fingerprints.length) {
      return sentence.text;
    }

    // Sort fingerprints by position (descending) for replacement
    // 按位置降序排列指纹词用于替换
    const sorted = [...sentence.fingerprints].sort(
      (a, b) => b.position - a.position
    );

    let text = sentence.text;
    sorted.forEach((fp) => {
      const before = text.slice(0, fp.position);
      const word = text.slice(fp.position, fp.position + fp.word.length);
      const after = text.slice(fp.position + fp.word.length);

      const className =
        fp.riskWeight >= 0.8
          ? 'fingerprint-high'
          : fp.riskWeight >= 0.6
          ? 'fingerprint-medium'
          : 'fingerprint-low';

      text = `${before}<span class="${className}" title="AI指纹词: ${fp.word}">${word}</span>${after}`;
    });

    // Highlight locked terms
    // 高亮锁定术语
    sentence.lockedTerms.forEach((term) => {
      const regex = new RegExp(`\\b(${term})\\b`, 'gi');
      text = text.replace(
        regex,
        `<span class="locked-term" title="锁定术语">$1</span>`
      );
    });

    return text;
  }, [sentence]);

  return (
    <div
      className={clsx(
        'card p-4 transition-all duration-200',
        isActive && 'ring-2 ring-primary-500 shadow-md'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">
            #{sentence.index + 1}
          </span>
          <RiskBadge
            level={sentence.riskLevel}
            score={sentence.riskScore}
          />
        </div>

        {/* Locked terms indicator */}
        {sentence.lockedTerms.length > 0 && (
          <div className="flex items-center text-blue-600 text-sm">
            <Lock className="w-4 h-4 mr-1" />
            <span>{sentence.lockedTerms.length} 锁定</span>
          </div>
        )}
      </div>

      {/* Original sentence with highlights */}
      <div className="mb-3">
        <p
          className="text-gray-800 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: highlightedText }}
        />
      </div>

      {/* Translation */}
      {showTranslation && translation && (
        <div className="mb-3 p-2 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">{translation}</p>
        </div>
      )}

      {/* Issues */}
      {sentence.issues.length > 0 && (
        <div className="mb-3">
          <div className="flex items-center text-sm text-gray-500 mb-2">
            <AlertTriangle className="w-4 h-4 mr-1" />
            <span>检测到的问题</span>
          </div>
          <div className="space-y-1">
            {sentence.issues.map((issue, idx) => (
              <div
                key={idx}
                className={clsx(
                  'text-sm px-2 py-1 rounded',
                  issue.severity === 'high' && 'bg-red-50 text-red-700',
                  issue.severity === 'medium' && 'bg-amber-50 text-amber-700',
                  issue.severity === 'low' && 'bg-yellow-50 text-yellow-700'
                )}
              >
                {issue.descriptionZh || issue.description}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fingerprint words list */}
      {sentence.fingerprints.length > 0 && (
        <div className="mb-3">
          <p className="text-sm text-gray-500 mb-1">
            指纹词 ({sentence.fingerprints.length}):
          </p>
          <div className="flex flex-wrap gap-1">
            {sentence.fingerprints.map((fp, idx) => (
              <span
                key={idx}
                className={clsx(
                  'px-2 py-0.5 text-xs rounded-full',
                  fp.riskWeight >= 0.8
                    ? 'bg-red-100 text-red-700'
                    : fp.riskWeight >= 0.6
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-yellow-100 text-yellow-700'
                )}
                title={`替换建议: ${fp.replacements.slice(0, 3).join(', ')}`}
              >
                {fp.word}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Detector views */}
      {showDetectorViews && (sentence.turnitinView || sentence.gptzeroView) && (
        <div className="grid grid-cols-2 gap-2 pt-3 border-t border-gray-100">
          {sentence.turnitinView && (
            <DetectorViewCard
              title="Turnitin"
              score={sentence.turnitinView.riskScore}
              issues={sentence.turnitinView.keyIssuesZh}
            />
          )}
          {sentence.gptzeroView && (
            <DetectorViewCard
              title="GPTZero"
              score={sentence.gptzeroView.riskScore}
              issues={sentence.gptzeroView.keyIssuesZh}
            />
          )}
        </div>
      )}

      {/* PPL and density indicators */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100 text-sm">
        <div className="flex items-center text-gray-500">
          <span className="mr-1">PPL: {sentence.ppl.toFixed(1)}</span>
          <InfoTooltip
            title="PPL (困惑度)"
            content="使用zlib压缩比计算。AI生成文本通常有更高的压缩率（更低的信息密度）。PPL越高，越可能是AI生成。阈值：>2.5可疑，>3.0高风险。"
            position="top"
          />
        </div>
        <div className="flex items-center text-gray-500">
          <span className="mr-1">密度: {(sentence.fingerprintDensity * 100).toFixed(1)}%</span>
          <InfoTooltip
            title="指纹词密度"
            content="指纹词数量占总词数的比例。指纹词是AI常用但人类少用的词汇，如'delve'、'tapestry'、'multifaceted'等。密度越高，AI特征越明显。"
            position="top"
          />
        </div>
      </div>
    </div>
  );
}

// Detector view sub-component
// 检测器视图子组件
function DetectorViewCard({
  title,
  score,
  issues,
}: {
  title: string;
  score: number;
  issues: string[];
}) {
  return (
    <div className="p-2 bg-gray-50 rounded-lg">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium text-gray-600">{title}</span>
        <span
          className={clsx(
            'text-xs font-bold',
            score >= 61 ? 'text-red-600' : score >= 31 ? 'text-amber-600' : 'text-green-600'
          )}
        >
          {score}
        </span>
      </div>
      {issues.length > 0 && (
        <ul className="text-xs text-gray-500 space-y-0.5">
          {issues.slice(0, 2).map((issue, idx) => (
            <li key={idx}>• {issue}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
