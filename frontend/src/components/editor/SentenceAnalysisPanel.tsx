import { useState } from 'react';
import {
  BookOpen,
  GitBranch,
  Link2,
  AlertTriangle,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  X,
} from 'lucide-react';
import { clsx } from 'clsx';
import type { DetailedSentenceAnalysis } from '../../types';

interface SentenceAnalysisPanelProps {
  analysis: DetailedSentenceAnalysis;
  onClose: () => void;
}

/**
 * Panel displaying detailed sentence analysis results
 * 显示详细句子分析结果的面板
 */
export default function SentenceAnalysisPanel({
  analysis,
  onClose,
}: SentenceAnalysisPanelProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['grammar', 'aiWords', 'rewrite'])
  );

  const toggleSection = (section: string) => {
    const newSet = new Set(expandedSections);
    if (newSet.has(section)) {
      newSet.delete(section);
    } else {
      newSet.add(section);
    }
    setExpandedSections(newSet);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg max-h-[70vh] overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <h3 className="font-semibold text-gray-800">句子分析 / Sentence Analysis</h3>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded transition-colors"
        >
          <X className="w-5 h-5 text-gray-500" />
        </button>
      </div>

      <div className="p-4 space-y-4">
        {/* Grammar Structure Section */}
        <AnalysisSection
          title="语法结构"
          titleEn="Grammar Structure"
          icon={<BookOpen className="w-4 h-4" />}
          iconColor="text-blue-600"
          bgColor="bg-blue-50"
          isExpanded={expandedSections.has('grammar')}
          onToggle={() => toggleSection('grammar')}
        >
          <div className="space-y-3">
            {/* Subject */}
            <div className="flex items-start">
              <span className="text-xs font-medium text-gray-500 w-16 flex-shrink-0 pt-0.5">
                主语
              </span>
              <div>
                <p className="text-sm text-gray-800 font-medium">{analysis.grammar.subject}</p>
                <p className="text-xs text-gray-500">{analysis.grammar.subjectZh}</p>
              </div>
            </div>

            {/* Predicate */}
            <div className="flex items-start">
              <span className="text-xs font-medium text-gray-500 w-16 flex-shrink-0 pt-0.5">
                谓语
              </span>
              <div>
                <p className="text-sm text-gray-800 font-medium">{analysis.grammar.predicate}</p>
                <p className="text-xs text-gray-500">{analysis.grammar.predicateZh}</p>
              </div>
            </div>

            {/* Object */}
            {analysis.grammar.object && (
              <div className="flex items-start">
                <span className="text-xs font-medium text-gray-500 w-16 flex-shrink-0 pt-0.5">
                  宾语
                </span>
                <div>
                  <p className="text-sm text-gray-800 font-medium">{analysis.grammar.object}</p>
                  <p className="text-xs text-gray-500">{analysis.grammar.objectZh}</p>
                </div>
              </div>
            )}

            {/* Modifiers */}
            {analysis.grammar.modifiers.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <p className="text-xs font-medium text-gray-500 mb-2">修饰成分</p>
                <div className="space-y-2">
                  {analysis.grammar.modifiers.map((mod, idx) => (
                    <div key={idx} className="flex items-start text-sm">
                      <span className={clsx(
                        'px-2 py-0.5 rounded text-xs mr-2 flex-shrink-0',
                        mod.type === 'attributive' && 'bg-purple-100 text-purple-700',
                        mod.type === 'adverbial' && 'bg-green-100 text-green-700',
                        mod.type === 'complement' && 'bg-orange-100 text-orange-700'
                      )}>
                        {mod.typeZh}
                      </span>
                      <div>
                        <span className="text-gray-800">{mod.text}</span>
                        <span className="text-gray-400 mx-1">→</span>
                        <span className="text-gray-500 text-xs">修饰 {mod.modifies}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </AnalysisSection>

        {/* Clauses Section */}
        {analysis.clauses.length > 0 && (
          <AnalysisSection
            title="从句分析"
            titleEn="Clause Analysis"
            icon={<GitBranch className="w-4 h-4" />}
            iconColor="text-purple-600"
            bgColor="bg-purple-50"
            isExpanded={expandedSections.has('clauses')}
            onToggle={() => toggleSection('clauses')}
          >
            <div className="space-y-3">
              {analysis.clauses.map((clause, idx) => (
                <div key={idx} className="p-2 bg-gray-50 rounded-lg">
                  <div className="flex items-center mb-1">
                    <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs mr-2">
                      {clause.typeZh}
                    </span>
                    <span className="text-xs text-gray-500">{clause.type}</span>
                  </div>
                  <p className="text-sm text-gray-800 mb-1">"{clause.text}"</p>
                  <p className="text-xs text-gray-600">
                    <span className="font-medium">作用:</span> {clause.functionZh}
                  </p>
                </div>
              ))}
            </div>
          </AnalysisSection>
        )}

        {/* Pronouns Section */}
        {analysis.pronouns.length > 0 && (
          <AnalysisSection
            title="代词指代"
            titleEn="Pronoun References"
            icon={<Link2 className="w-4 h-4" />}
            iconColor="text-teal-600"
            bgColor="bg-teal-50"
            isExpanded={expandedSections.has('pronouns')}
            onToggle={() => toggleSection('pronouns')}
          >
            <div className="space-y-2">
              {analysis.pronouns.map((pron, idx) => (
                <div key={idx} className="flex items-start text-sm">
                  <span className="px-2 py-0.5 bg-teal-100 text-teal-700 rounded text-xs mr-2 font-mono">
                    {pron.pronoun}
                  </span>
                  <div>
                    <span className="text-gray-400">→</span>
                    <span className="text-gray-800 ml-1">{pron.reference}</span>
                    <p className="text-xs text-gray-500">{pron.referenceZh}</p>
                  </div>
                </div>
              ))}
            </div>
          </AnalysisSection>
        )}

        {/* AI Words Section */}
        {analysis.aiWords.length > 0 && (
          <AnalysisSection
            title="AI词汇替换建议"
            titleEn="AI Word Replacements"
            icon={<AlertTriangle className="w-4 h-4" />}
            iconColor="text-amber-600"
            bgColor="bg-amber-50"
            isExpanded={expandedSections.has('aiWords')}
            onToggle={() => toggleSection('aiWords')}
          >
            <div className="space-y-3">
              {analysis.aiWords.map((word, idx) => (
                <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center">
                      <span className={clsx(
                        'px-2 py-0.5 rounded text-xs font-medium mr-2',
                        word.level === 1
                          ? 'bg-red-100 text-red-700'
                          : 'bg-amber-100 text-amber-700'
                      )}>
                        {word.level === 1 ? '一级词' : '二级词'}
                      </span>
                      <span className="font-mono text-gray-800 font-medium">{word.word}</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mb-2">{word.levelDesc}</p>
                  <div className="flex flex-wrap gap-1 mb-2">
                    <span className="text-xs text-gray-500">替换:</span>
                    {word.alternatives.map((alt, altIdx) => (
                      <span
                        key={altIdx}
                        className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs cursor-pointer hover:bg-green-200 transition-colors"
                        title="点击复制"
                        onClick={() => navigator.clipboard.writeText(alt)}
                      >
                        {alt}
                      </span>
                    ))}
                  </div>
                  <p className="text-xs text-gray-600">{word.contextSuggestion}</p>
                </div>
              ))}
            </div>
          </AnalysisSection>
        )}

        {/* Rewrite Suggestions Section */}
        {analysis.rewriteSuggestions.length > 0 && (
          <AnalysisSection
            title="改写建议"
            titleEn="Rewrite Suggestions"
            icon={<Lightbulb className="w-4 h-4" />}
            iconColor="text-yellow-600"
            bgColor="bg-yellow-50"
            isExpanded={expandedSections.has('rewrite')}
            onToggle={() => toggleSection('rewrite')}
          >
            <div className="space-y-3">
              {analysis.rewriteSuggestions.map((suggestion, idx) => (
                <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center mb-2">
                    <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs font-medium">
                      {suggestion.typeZh}
                    </span>
                  </div>
                  <p className="text-sm text-gray-800 mb-1">{suggestion.descriptionZh}</p>
                  <p className="text-xs text-gray-500">{suggestion.description}</p>
                  {suggestion.example && (
                    <div className="mt-2 p-2 bg-white border border-gray-200 rounded text-sm">
                      <span className="text-xs text-gray-500 block mb-1">示例:</span>
                      <p className="text-gray-800">{suggestion.example}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </AnalysisSection>
        )}

        {/* Empty state for AI words */}
        {analysis.aiWords.length === 0 && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-center">
            <p className="text-green-700 text-sm">
              未检测到明显的AI词汇特征
            </p>
            <p className="text-green-600 text-xs mt-1">
              No obvious AI vocabulary patterns detected
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Collapsible analysis section component
 * 可折叠的分析区块组件
 */
function AnalysisSection({
  title,
  titleEn,
  icon,
  iconColor,
  bgColor,
  isExpanded,
  onToggle,
  children,
}: {
  title: string;
  titleEn: string;
  icon: React.ReactNode;
  iconColor: string;
  bgColor: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className={clsx(
          'w-full px-4 py-3 flex items-center justify-between transition-colors',
          isExpanded ? bgColor : 'hover:bg-gray-50'
        )}
      >
        <div className="flex items-center">
          <div className={clsx('p-1.5 rounded-lg mr-3', bgColor, iconColor)}>
            {icon}
          </div>
          <div className="text-left">
            <p className="font-medium text-gray-800 text-sm">{title}</p>
            <p className="text-xs text-gray-500">{titleEn}</p>
          </div>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 pt-2">
          {children}
        </div>
      )}
    </div>
  );
}
