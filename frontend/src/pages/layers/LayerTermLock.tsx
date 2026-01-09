import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Lock,
  Unlock,
  ArrowRight,
  AlertCircle,
  CheckCircle,
  Loader2,
  Plus,
  X,
  Search,
  BookOpen,
  Tag,
  Hash,
  FileText,
  Key,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import {
  termLockApi,
  ExtractedTerm,
  TermType,
} from '../../services/analysisApi';

/**
 * Layer Term Lock (Step 1.0) - Term Locking
 * 词汇锁定（步骤 1.0）
 *
 * Extracts and locks professional terms that should not be modified
 * during the De-AIGC rewriting process.
 *
 * Part of the 5-layer detection architecture.
 * 5层检测架构的一部分。
 */

// Term type display configuration
// 术语类型显示配置
const TERM_TYPE_CONFIG: Record<TermType, { label: string; labelZh: string; icon: typeof Tag; color: string }> = {
  technical_term: { label: 'Technical Term', labelZh: '专业术语', icon: BookOpen, color: 'text-blue-600 bg-blue-50' },
  proper_noun: { label: 'Proper Noun', labelZh: '专有名词', icon: Tag, color: 'text-purple-600 bg-purple-50' },
  acronym: { label: 'Acronym', labelZh: '缩写词', icon: Hash, color: 'text-green-600 bg-green-50' },
  key_phrase: { label: 'Key Phrase', labelZh: '关键词组', icon: FileText, color: 'text-orange-600 bg-orange-50' },
  core_word: { label: 'Core Word', labelZh: '核心词', icon: Key, color: 'text-gray-600 bg-gray-50' },
};

interface LayerTermLockProps {
  // Optional document ID from props
  documentIdProp?: string;
  // Callback when term locking completes
  onComplete?: (lockedTerms: string[]) => void;
  // Whether to show navigation buttons
  showNavigation?: boolean;
}

export default function LayerTermLock({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerTermLockProps) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Processing mode and session from URL parameter
  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session') || `session_${Date.now()}`;

  // Update session step on mount
  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'term-lock').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [documentText, setDocumentText] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Extracted terms
  const [extractedTerms, setExtractedTerms] = useState<ExtractedTerm[]>([]);
  const [selectedTerms, setSelectedTerms] = useState<Set<string>>(new Set());
  const [processingTime, setProcessingTime] = useState<number>(0);
  const [byType, setByType] = useState<Record<string, number>>({});

  // Custom term input
  const [customTerm, setCustomTerm] = useState('');
  const [customTerms, setCustomTerms] = useState<string[]>([]);

  // Filter state
  const [filterType, setFilterType] = useState<TermType | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Completion state
  const [isCompleted, setIsCompleted] = useState(false);
  const [lockedTerms, setLockedTerms] = useState<string[]>([]);

  // Prevent duplicate API calls
  const isExtractingRef = useRef(false);

  // Load document text
  useEffect(() => {
    if (documentId) {
      loadDocumentText(documentId);
    }
  }, [documentId]);

  const loadDocumentText = async (docId: string) => {
    try {
      const doc = await documentApi.get(docId);
      if (doc.originalText) {
        setDocumentText(doc.originalText);
      } else {
        setError('Document text not found');
      }
    } catch (err) {
      console.error('Failed to load document:', err);
      setError('Failed to load document');
    } finally {
      setIsLoading(false);
    }
  };

  // Extract terms when text is loaded
  useEffect(() => {
    if (documentText && !isExtractingRef.current) {
      extractTerms();
    }
  }, [documentText]);

  const extractTerms = async () => {
    if (isExtractingRef.current || !documentText) return;
    isExtractingRef.current = true;
    setIsExtracting(true);
    setError(null);

    try {
      const result = await termLockApi.extractTerms(documentText, sessionId);
      setExtractedTerms(result.extractedTerms);
      setProcessingTime(result.processingTimeMs);
      setByType(result.byType);

      // Pre-select recommended terms
      const recommended = new Set(
        result.extractedTerms
          .filter(t => t.recommended)
          .map(t => t.term)
      );
      setSelectedTerms(recommended);
    } catch (err) {
      console.error('Term extraction failed:', err);
      setError('Failed to extract terms. Please try again.');
    } finally {
      setIsExtracting(false);
      isExtractingRef.current = false;
    }
  };

  // Toggle term selection
  const toggleTerm = (term: string) => {
    const newSelected = new Set(selectedTerms);
    if (newSelected.has(term)) {
      newSelected.delete(term);
    } else {
      newSelected.add(term);
    }
    setSelectedTerms(newSelected);
  };

  // Select/deselect all
  const selectAll = () => {
    setSelectedTerms(new Set(extractedTerms.map(t => t.term)));
  };

  const deselectAll = () => {
    setSelectedTerms(new Set());
  };

  // Select all recommended
  const selectRecommended = () => {
    setSelectedTerms(new Set(extractedTerms.filter(t => t.recommended).map(t => t.term)));
  };

  // Add custom term
  const addCustomTerm = () => {
    if (customTerm.trim() && !customTerms.includes(customTerm.trim())) {
      setCustomTerms([...customTerms, customTerm.trim()]);
      setCustomTerm('');
    }
  };

  // Remove custom term
  const removeCustomTerm = (term: string) => {
    setCustomTerms(customTerms.filter(t => t !== term));
  };

  // Confirm and lock terms
  const confirmLock = async () => {
    setIsLoading(true);
    try {
      const result = await termLockApi.confirmLock(
        sessionId,
        Array.from(selectedTerms),
        customTerms
      );
      setLockedTerms(result.lockedTerms);
      setIsCompleted(true);

      if (onComplete) {
        onComplete(result.lockedTerms);
      }
    } catch (err) {
      console.error('Term locking failed:', err);
      setError('Failed to lock terms. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Skip term locking
  const skipTermLocking = () => {
    setIsCompleted(true);
    if (onComplete) {
      onComplete([]);
    }
  };

  // Navigate to next step (Layer 5 Step 1.1: Section Structure & Order)
  // 导航到下一步（Layer 5 步骤 1.1：章节结构与顺序）
  const goToNextStep = () => {
    const params = new URLSearchParams();
    params.set('mode', mode);
    params.set('session', sessionId);
    navigate(`/flow/layer5-step1-1/${documentId}?${params.toString()}`);
  };

  // Filter terms
  const filteredTerms = extractedTerms.filter(term => {
    const matchesType = filterType === 'all' || term.termType === filterType;
    const matchesSearch = searchQuery === '' ||
      term.term.toLowerCase().includes(searchQuery.toLowerCase()) ||
      term.reason.toLowerCase().includes(searchQuery.toLowerCase()) ||
      term.reasonZh.includes(searchQuery);
    return matchesType && matchesSearch;
  });

  // Loading state
  if (isLoading && !documentText) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage category="general" centered />
      </div>
    );
  }

  // Completion state
  if (isCompleted) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Term Locking Complete / 词汇锁定完成
            </h2>
            <p className="text-gray-600">
              {lockedTerms.length > 0
                ? `${lockedTerms.length} terms have been locked and will be protected in all subsequent steps.`
                : 'No terms were locked. You can proceed to the next step.'}
            </p>
            <p className="text-gray-500 mt-1">
              {lockedTerms.length > 0
                ? `${lockedTerms.length} 个词汇已锁定，将在后续所有步骤中保持不变。`
                : '没有锁定任何词汇。您可以继续下一步。'}
            </p>
          </div>

          {lockedTerms.length > 0 && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold mb-3">Locked Terms / 锁定的词汇:</h3>
              <div className="flex flex-wrap gap-2">
                {lockedTerms.map((term, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium flex items-center gap-1"
                  >
                    <Lock className="w-3 h-3" />
                    {term}
                  </span>
                ))}
              </div>
            </div>
          )}

          {showNavigation && (
            <div className="flex justify-center">
              <Button onClick={goToNextStep} className="flex items-center gap-2">
                Continue to Step 1.1 / 继续步骤 1.1
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Lock className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Step 1.0: Term Locking / 词汇锁定
              </h1>
              <p className="text-gray-600">
                Select terms to protect during rewriting / 选择需要在改写中保护的词汇
              </p>
            </div>
          </div>
          {processingTime > 0 && (
            <div className="text-sm text-gray-500">
              Extracted in {processingTime}ms
            </div>
          )}
        </div>

        {/* 5-Layer Progress - Step 1.0 is current */}
        {/* 5层进度 - Step 1.0为当前步骤 */}
        <div className="mt-4 flex items-center text-sm text-gray-500 flex-wrap gap-y-1">
          <span className="font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
            1.0 词汇锁定
          </span>
          <span className="mx-2">→</span>
          <span>1.1 章节结构</span>
          <span className="mx-2">→</span>
          <span>1.2 均匀性</span>
          <span className="mx-2">→</span>
          <span>1.3 逻辑模式</span>
          <span className="mx-2">→</span>
          <span>1.4 段落长度</span>
          <span className="mx-2">→</span>
          <span>1.5 过渡衔接</span>
          <span className="mx-2">→</span>
          <span>Layer 4-1...</span>
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm mt-4">
          <p className="text-blue-800">
            <strong>Instructions / 说明：</strong> The system has identified professional terms, proper nouns, and key phrases
            from your document. Select the terms you want to protect - these will remain unchanged during all subsequent
            rewriting steps.
          </p>
          <p className="text-blue-700 mt-2">
            系统已从您的文档中识别出专业术语、专有名词和关键词组。请选择需要保护的词汇，这些词汇将在后续所有改写步骤中保持不变。
          </p>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-red-800">{error}</span>
        </div>
      )}

      {/* Extracting state */}
      {isExtracting && (
        <div className="bg-white rounded-lg shadow-lg p-8 mb-6 text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Analyzing document and extracting terms...</p>
          <p className="text-gray-500">正在分析文档并提取术语...</p>
        </div>
      )}

      {/* Main content */}
      {!isExtracting && extractedTerms.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Term list */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-lg p-6">
              {/* Filters */}
              <div className="flex flex-wrap items-center gap-4 mb-4">
                {/* Search */}
                <div className="relative flex-1 min-w-[200px]">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search terms..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Type filter */}
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value as TermType | 'all')}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All Types / 所有类型</option>
                  {Object.entries(TERM_TYPE_CONFIG).map(([type, config]) => (
                    <option key={type} value={type}>
                      {config.labelZh} ({byType[type] || 0})
                    </option>
                  ))}
                </select>
              </div>

              {/* Quick actions */}
              <div className="flex flex-wrap gap-2 mb-4">
                <button
                  onClick={selectAll}
                  className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  Select All / 全选
                </button>
                <button
                  onClick={selectRecommended}
                  className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg transition-colors"
                >
                  Select Recommended / 选择推荐
                </button>
                <button
                  onClick={deselectAll}
                  className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  Deselect All / 清除选择
                </button>
              </div>

              {/* Term list */}
              <div className="space-y-2 max-h-[500px] overflow-y-auto">
                {filteredTerms.map((term, idx) => {
                  const config = TERM_TYPE_CONFIG[term.termType];
                  const Icon = config.icon;
                  const isSelected = selectedTerms.has(term.term);

                  return (
                    <div
                      key={idx}
                      onClick={() => toggleTerm(term.term)}
                      className={clsx(
                        'p-3 border rounded-lg cursor-pointer transition-all',
                        isSelected
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {/* Checkbox */}
                          <div
                            className={clsx(
                              'w-5 h-5 rounded border-2 flex items-center justify-center',
                              isSelected
                                ? 'bg-blue-600 border-blue-600'
                                : 'border-gray-300'
                            )}
                          >
                            {isSelected && <CheckCircle className="w-3 h-3 text-white" />}
                          </div>

                          {/* Term info */}
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-gray-900">{term.term}</span>
                              <span className={clsx('px-2 py-0.5 text-xs rounded-full flex items-center gap-1', config.color)}>
                                <Icon className="w-3 h-3" />
                                {config.labelZh}
                              </span>
                              {term.recommended && (
                                <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                                  Recommended / 推荐
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-500 mt-1">{term.reasonZh}</p>
                          </div>
                        </div>

                        {/* Frequency */}
                        <div className="text-sm text-gray-500">
                          {term.frequency}x
                        </div>
                      </div>
                    </div>
                  );
                })}

                {filteredTerms.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No terms found matching your criteria.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right: Summary and actions */}
          <div className="space-y-6">
            {/* Selection summary */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Selection Summary / 选择概览</h3>

              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total extracted / 总提取:</span>
                  <span className="font-medium">{extractedTerms.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Selected / 已选择:</span>
                  <span className="font-medium text-blue-600">{selectedTerms.size}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Custom added / 自定义:</span>
                  <span className="font-medium text-purple-600">{customTerms.length}</span>
                </div>
                <div className="border-t pt-3">
                  <div className="flex justify-between">
                    <span className="font-semibold">Total to lock / 总锁定:</span>
                    <span className="font-bold text-green-600">{selectedTerms.size + customTerms.length}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Custom term input */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Add Custom Terms / 添加自定义词汇</h3>

              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  placeholder="Enter term..."
                  value={customTerm}
                  onChange={(e) => setCustomTerm(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addCustomTerm()}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <Button onClick={addCustomTerm} disabled={!customTerm.trim()}>
                  <Plus className="w-4 h-4" />
                </Button>
              </div>

              {customTerms.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {customTerms.map((term, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm flex items-center gap-2"
                    >
                      {term}
                      <button
                        onClick={() => removeCustomTerm(term)}
                        className="hover:text-purple-900"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Action buttons */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="space-y-3">
                <Button
                  onClick={confirmLock}
                  disabled={selectedTerms.size + customTerms.length === 0}
                  className="w-full flex items-center justify-center gap-2"
                >
                  <Lock className="w-4 h-4" />
                  Confirm & Lock ({selectedTerms.size + customTerms.length} terms)
                </Button>

                <button
                  onClick={skipTermLocking}
                  className="w-full py-2 text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Skip this step / 跳过此步骤
                </button>
              </div>

              <p className="text-sm text-gray-500 mt-4">
                Locked terms will be protected in all subsequent De-AIGC rewriting steps.
              </p>
              <p className="text-sm text-gray-400">
                锁定的词汇将在后续所有De-AIGC改写步骤中保持不变。
              </p>
            </div>
          </div>
        </div>
      )}

      {/* No terms extracted */}
      {!isExtracting && extractedTerms.length === 0 && !error && (
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <Unlock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No terms were extracted from the document.</p>
          <p className="text-gray-500 mb-4">未从文档中提取到术语。</p>
          <div className="flex justify-center gap-4">
            <Button onClick={extractTerms} variant="outline">
              Try Again / 重试
            </Button>
            <Button onClick={skipTermLocking}>
              Skip & Continue / 跳过继续
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
