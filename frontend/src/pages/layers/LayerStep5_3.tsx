import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Replace,
  FileText,
  RefreshCw,
  AlertTriangle,
  Sparkles,
  Edit3,
  Upload,
  Check,
  X,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import { useSubstepStateStore } from '../../stores/substepStateStore';
import {
  lexicalLayerApi,
  documentLayerApi,
  ReplacementGenerationResponse,
  ReplacementSuggestion,
  DetectionIssue,
} from '../../services/analysisApi';

/**
 * Layer Step 5.3 - Replacement Generation
 * 步骤 5.3 - 替换词生成
 *
 * Generates word replacements for:
 * - AI fingerprint words
 * - Repeated words (variety)
 * - Overly formal words
 * - Awkward collocations
 */

interface IssueSuggestionResponse {
  analysis: string;
  suggestions: string[];
  exampleFix?: string;
}

interface ModifyPromptResponse {
  prompt: string;
}

interface ApplyModifyResponse {
  modifiedText: string;
  changesSummary?: string;
  changesCount?: number;
}

interface LayerStep5_3Props {
  documentIdProp?: string;
  onComplete?: (result: ReplacementGenerationResponse) => void;
  showNavigation?: boolean;
}

// Replacement reason config
// 替换原因配置
const REASON_CONFIG: Record<string, { label: string; labelZh: string; color: string }> = {
  ai_fingerprint: { label: 'AI Fingerprint', labelZh: 'AI指纹', color: 'red' },
  variety: { label: 'Variety', labelZh: '多样性', color: 'blue' },
  formality: { label: 'Formality', labelZh: '正式度', color: 'purple' },
  collocation: { label: 'Collocation', labelZh: '搭配', color: 'orange' },
};

export default function LayerStep5_3({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep5_3Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // Substep state store for caching modified text
  // 子步骤状态存储，用于缓存修改后的文本
  const substepStore = useSubstepStateStore();

  const isValidDocumentId = (id: string | undefined): boolean => {
    return !!(id && id !== 'undefined' && id !== 'null');
  };

  const getInitialDocumentId = (): string | undefined => {
    if (isValidDocumentId(documentIdProp)) return documentIdProp;
    if (isValidDocumentId(documentIdParam)) return documentIdParam;
    return undefined;
  };

  const [documentId, setDocumentId] = useState<string | undefined>(getInitialDocumentId());
  const [sessionFetchAttempted, setSessionFetchAttempted] = useState(
    isValidDocumentId(documentIdProp) || isValidDocumentId(documentIdParam)
  );

  useEffect(() => {
    const fetchDocumentIdFromSession = async () => {
      if (!isValidDocumentId(documentId) && sessionId) {
        try {
          const sessionState = await sessionApi.getCurrent(sessionId);
          if (sessionState.documentId) setDocumentId(sessionState.documentId);
        } catch (err) {
          console.error('Failed to get documentId from session:', err);
        }
      }
      setSessionFetchAttempted(true);
    };

    if (!sessionId) {
      setSessionFetchAttempted(true);
    } else if (!isValidDocumentId(documentId)) {
      fetchDocumentIdFromSession();
    } else {
      setSessionFetchAttempted(true);
    }
  }, [documentId, sessionId]);

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer1-step5-3').catch(console.error);
    }
  }, [sessionId]);

  const [result, setResult] = useState<ReplacementGenerationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedSection, setExpandedSection] = useState<string | null>('replacements');

  const [replacementIssues, setReplacementIssues] = useState<DetectionIssue[]>([]);
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());

  // Click-expand state for individual issue analysis
  // 点击展开状态，用于单个问题分析
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

  const [issueSuggestion, setIssueSuggestion] = useState<IssueSuggestionResponse | null>(null);
  // Per-issue suggestion cache to avoid redundant API calls
  // 每个问题的建议缓存，避免重复API调用
  const suggestionCacheRef = useRef<Map<number, IssueSuggestionResponse>>(new Map());
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);

  const [showMergeConfirm, setShowMergeConfirm] = useState(false);
  const [mergeMode, setMergeMode] = useState<'prompt' | 'apply'>('prompt');
  const [mergeUserNotes, setMergeUserNotes] = useState('');
  const [isMerging, setIsMerging] = useState(false);
  const [mergeResult, setMergeResult] = useState<ModifyPromptResponse | ApplyModifyResponse | null>(null);

  const [modifyMode, setModifyMode] = useState<'file' | 'text'>('file');
  const [newFile, setNewFile] = useState<File | null>(null);
  const [newText, setNewText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Skip confirmation state
  // 跳过确认状态
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);

  const isAnalyzingRef = useRef(false);

  useEffect(() => {
    if (!sessionFetchAttempted) return;
    if (isValidDocumentId(documentId)) {
      loadDocumentText(documentId!);
    } else {
      setError('Document ID not found.');
      setIsLoading(false);
    }
  }, [documentId, sessionFetchAttempted]);

  const loadDocumentText = useCallback(async (docId: string) => {
    try {
      // Initialize substep store for session if needed
      // 如果需要，为会话初始化子步骤存储
      if (sessionId && substepStore.currentSessionId !== sessionId) {
        await substepStore.initForSession(sessionId);
      }

      // Check previous steps for modified text (step1-2, step1-1, step1-0)
      // 检查前序步骤的修改文本
      const previousSteps = ['step1-2', 'step1-1', 'step1-0'];
      let foundModifiedText: string | null = null;

      for (const stepName of previousSteps) {
        const stepState = substepStore.getState(stepName);
        if (stepState?.modifiedText) {
          console.log(`[LayerStep5_3] Using modified text from ${stepName}`);
          foundModifiedText = stepState.modifiedText;
          break;
        }
      }

      if (foundModifiedText) {
        setDocumentText(foundModifiedText);
      } else {
        const doc = await documentApi.get(docId);
        if (doc.originalText) {
          setDocumentText(doc.originalText);
        } else {
          setError('Document text not found');
        }
      }
    } catch (err) {
      console.error('Failed to load document:', err);
      setError('Failed to load document');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, substepStore]);

  useEffect(() => {
    if (documentText && !isAnalyzingRef.current) {
      runAnalysis();
    }
  }, [documentText]);

  const runAnalysis = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;
    setIsAnalyzing(true);
    setError(null);

    try {
      const analysisResult = await lexicalLayerApi.generateReplacements(
        documentText,
        sessionId || undefined
      );

      setResult(analysisResult);

      const issues: DetectionIssue[] = [];

      if (analysisResult.replacementCount && analysisResult.replacementCount > 0) {
        issues.push({
          type: 'replacements_needed',
          description: `${analysisResult.replacementCount} words need replacement`,
          descriptionZh: `${analysisResult.replacementCount} 个词需要替换`,
          severity: analysisResult.replacementCount > 10 ? 'high' : 'medium',
          layer: 'lexical',
        });
      }

      if (analysisResult.byCategory) {
        if (analysisResult.byCategory.aiFingerprint > 0) {
          issues.push({
            type: 'ai_fingerprint_replacements',
            description: `${analysisResult.byCategory.aiFingerprint} AI fingerprint words to replace`,
            descriptionZh: `${analysisResult.byCategory.aiFingerprint} 个AI指纹词需要替换`,
            severity: 'high',
            layer: 'lexical',
          });
        }
      }

      if (analysisResult.issues) {
        issues.push(...analysisResult.issues);
      }

      setReplacementIssues(issues);

      if (onComplete) {
        onComplete(analysisResult);
      }
    } catch (err) {
      console.error('Analysis failed:', err);
      setError('Analysis failed');
    } finally {
      setIsAnalyzing(false);
      isAnalyzingRef.current = false;
    }
  };

  // Load detailed suggestion for a single issue with caching
  // 为单个问题加载详细建议，支持缓存
  const loadIssueSuggestion = useCallback(async (index: number) => {
    const issue = replacementIssues[index];
    if (!issue || !documentId) return;

    // Check cache first
    // 先检查缓存
    const cached = suggestionCacheRef.current.get(index);
    if (cached) {
      setIssueSuggestion(cached);
      return;
    }

    setIsLoadingSuggestion(true);
    setSuggestionError(null);

    try {
      const response = await documentLayerApi.getIssueSuggestion(
        documentId,
        issue,
        false
      );
      const suggestion: IssueSuggestionResponse = {
        analysis: response.diagnosisZh || '',
        suggestions: response.strategies?.map((s: { nameZh: string; descriptionZh: string }) => `${s.nameZh}: ${s.descriptionZh}`) || [],
        exampleFix: response.strategies?.[0]?.exampleAfter || '',
      };
      suggestionCacheRef.current.set(index, suggestion);
      setIssueSuggestion(suggestion);
    } catch (err) {
      console.error('Failed to load suggestion:', err);
      setSuggestionError('Failed to load suggestion / 加载建议失败');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [replacementIssues, documentId]);

  // Handle issue click to expand and auto-load suggestions
  // 处理问题点击展开并自动加载建议
  const handleIssueClick = useCallback(async (index: number) => {
    if (expandedIssueIndex === index) {
      setExpandedIssueIndex(null);
      setIssueSuggestion(null);
      return;
    }
    setExpandedIssueIndex(index);
    await loadIssueSuggestion(index);
  }, [expandedIssueIndex, loadIssueSuggestion]);

  // Toggle issue selection for checkbox only
  // 仅用于复选框的问题选择切换
  const toggleIssueSelection = useCallback((index: number) => {
    setSelectedIssueIndices(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
    setMergeResult(null);
  }, []);

  // Select all issues
  // 全选所有问题
  const selectAllIssues = useCallback(() => {
    setSelectedIssueIndices(new Set(replacementIssues.map((_, idx) => idx)));
  }, [replacementIssues]);

  // Deselect all issues
  // 取消全选所有问题
  const deselectAllIssues = useCallback(() => {
    setSelectedIssueIndices(new Set());
  }, []);

  const executeMergeModify = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentId) return;
    setIsMerging(true);
    setShowMergeConfirm(false);

    try {
      const selectedIssues = Array.from(selectedIssueIndices).map(i => replacementIssues[i]);
      if (mergeMode === 'prompt') {
        const response = await documentLayerApi.generateModifyPrompt(documentId, selectedIssues, { sessionId: sessionId || undefined, userNotes: mergeUserNotes || undefined });
        setMergeResult(response as ModifyPromptResponse);
      } else {
        const response = await documentLayerApi.applyModify(documentId, selectedIssues, { sessionId: sessionId || undefined, userNotes: mergeUserNotes || undefined });
        setMergeResult(response as ApplyModifyResponse);
      }
    } catch (err) {
      setError('Merge modify failed');
    } finally {
      setIsMerging(false);
    }
  }, [selectedIssueIndices, documentId, replacementIssues, mergeMode, mergeUserNotes, sessionId]);

  const handleRegenerate = useCallback(() => {
    setMergeResult(null);
    setShowMergeConfirm(true);
    setMergeMode('apply');
  }, []);

  const handleAcceptModification = useCallback(() => {
    if (mergeResult && 'modifiedText' in mergeResult && mergeResult.modifiedText) {
      setNewText(mergeResult.modifiedText);
      setModifyMode('text');
      setMergeResult(null);
    }
  }, [mergeResult]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setNewFile(file);
  }, []);

  const handleConfirmModify = useCallback(async () => {
    setIsUploading(true);
    setError(null);

    try {
      let modifiedText: string = '';

      if (modifyMode === 'file' && newFile) {
        modifiedText = await newFile.text();
      } else if (modifyMode === 'text' && newText.trim()) {
        modifiedText = newText.trim();
      } else {
        setError('Please select a file or enter text');
        setIsUploading(false);
        return;
      }

      // Save modified text to substep store
      // 将修改后的文本保存到子步骤存储
      if (sessionId && modifiedText) {
        await substepStore.saveModifiedText('step1-3', modifiedText);
        await substepStore.markCompleted('step1-3');
        console.log('[LayerStep5_3] Saved modified text to substep store');
      }

      // Navigate to next step with same document ID
      // 使用相同的文档ID导航到下一步
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer1-step5-4/${documentId}?${params.toString()}`);
    } catch (err) {
      setError('Failed to upload');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate, documentId, substepStore]);

  const goToNextStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer1-step5-4/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer1-step5-2/${documentId}?${params.toString()}`);
  };

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const hasSelectedIssues = selectedIssueIndices.size > 0;

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-[400px]"><LoadingMessage message="Loading..." /></div>;
  }

  if (error && !result) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center gap-2 text-red-700"><AlertCircle className="w-5 h-5" /><span>{error}</span></div>
        <Button onClick={runAnalysis} className="mt-4" variant="outline"><RefreshCw className="w-4 h-4 mr-2" />Retry</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <LoadingOverlay isVisible={isMerging} operationType={mergeMode} issueCount={selectedIssueIndices.size} />

      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg"><Replace className="w-6 h-6 text-orange-600" /></div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Step 5.3: Replacement Generation</h2>
              <p className="text-sm text-gray-500">步骤 5.3: 替换词生成</p>
            </div>
          </div>
          {isAnalyzing && <div className="flex items-center gap-2 text-orange-600"><Loader2 className="w-5 h-5 animate-spin" /><span>Analyzing...</span></div>}
        </div>

        <p className="text-gray-600 mb-4">
          Generates word replacement suggestions to improve vocabulary diversity and remove AI markers.
          <br /><span className="text-gray-500">生成词汇替换建议，提高词汇多样性并移除AI标记。</span>
        </p>

        {/* Stats */}
        {result && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-orange-600 mb-1"><Replace className="w-4 h-4" /><span className="text-sm font-medium">Total</span></div>
              <div className="text-2xl font-bold text-orange-700">{result.replacementCount || 0}</div>
              <div className="text-xs text-orange-500">需替换</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-red-600 mb-1"><AlertTriangle className="w-4 h-4" /><span className="text-sm font-medium">AI Words</span></div>
              <div className="text-2xl font-bold text-red-700">{result.byCategory?.aiFingerprint || 0}</div>
              <div className="text-xs text-red-500">AI指纹</div>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-blue-600 mb-1"><Sparkles className="w-4 h-4" /><span className="text-sm font-medium">Variety</span></div>
              <div className="text-2xl font-bold text-blue-700">{result.byCategory?.variety || 0}</div>
              <div className="text-xs text-blue-500">多样性</div>
            </div>
            <div className={clsx('rounded-lg p-4', result.riskLevel === 'low' ? 'bg-green-50' : result.riskLevel === 'medium' ? 'bg-yellow-50' : 'bg-red-50')}>
              <div className={clsx('flex items-center gap-2 mb-1', result.riskLevel === 'low' ? 'text-green-600' : result.riskLevel === 'medium' ? 'text-yellow-600' : 'text-red-600')}>
                {result.riskLevel === 'low' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                <span className="text-sm font-medium">Risk</span>
              </div>
              <div className={clsx('text-2xl font-bold', result.riskLevel === 'low' ? 'text-green-700' : result.riskLevel === 'medium' ? 'text-yellow-700' : 'text-red-700')}>
                {result.riskLevel?.toUpperCase() || 'N/A'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Replacements List */}
      {result && result.replacements && result.replacements.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between cursor-pointer" onClick={() => toggleSection('replacements')}>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Replace className="w-5 h-5 text-orange-600" />
              Replacement Suggestions ({result.replacements.length})
            </h3>
            {expandedSection === 'replacements' ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
          </div>

          {expandedSection === 'replacements' && (
            <div className="mt-4 space-y-3 max-h-96 overflow-y-auto">
              {result.replacements.map((rep: ReplacementSuggestion, index: number) => {
                const config = REASON_CONFIG[rep.reason] || REASON_CONFIG.variety;
                return (
                  <div key={index} className={`p-4 rounded-lg border bg-${config.color}-50 border-${config.color}-200`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-900">"{rep.original}"</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium bg-${config.color}-100 text-${config.color}-700`}>
                        {config.label}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-gray-500">→</span>
                      <span className="font-medium text-green-700">{rep.recommended}</span>
                    </div>
                    {rep.suggestions && rep.suggestions.length > 1 && (
                      <div className="text-sm text-gray-500">
                        Alternatives: {rep.suggestions.filter(s => s !== rep.recommended).join(', ')}
                      </div>
                    )}
                    <div className="text-xs text-gray-400 mt-2 truncate">Context: {rep.context}</div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Issues with Click-Expand */}
      {/* 问题部分（带点击展开功能） */}
      {replacementIssues.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              Issues ({replacementIssues.length})
              <span className="text-sm font-normal text-gray-500">
                ({selectedIssueIndices.size}/{replacementIssues.length} selected / 已选择)
              </span>
            </h3>
            <div className="flex items-center gap-2">
              {/* Select All / Deselect All buttons */}
              {/* 全选/取消全选按钮 */}
              <Button variant="secondary" size="sm" onClick={selectAllIssues}>
                Select All / 全选
              </Button>
              <Button variant="secondary" size="sm" onClick={deselectAllIssues}>
                Deselect All / 取消全选
              </Button>
            </div>
          </div>
          <div className="space-y-2">
            {replacementIssues.map((issue, idx) => (
              <div key={idx} className="space-y-0">
                <div
                  className={clsx(
                    'w-full text-left p-3 rounded-lg border transition-all',
                    expandedIssueIndex === idx
                      ? 'bg-orange-50 border-orange-300'
                      : 'bg-white border-gray-200 hover:border-gray-300'
                  )}
                >
                  <div className="flex items-start gap-3">
                    {/* Checkbox - separate click handler */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleIssueSelection(idx);
                      }}
                      className={clsx(
                        'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5 cursor-pointer',
                        selectedIssueIndices.has(idx)
                          ? 'bg-orange-600 border-orange-600'
                          : 'border-gray-300 hover:border-orange-400'
                      )}
                    >
                      {selectedIssueIndices.has(idx) && <Check className="w-3 h-3 text-white" />}
                    </button>
                    {/* Content - click to expand */}
                    <button
                      onClick={() => handleIssueClick(idx)}
                      className="flex-1 text-left"
                    >
                      <div className="flex items-center gap-2">
                        <span className={clsx(
                          'px-2 py-0.5 rounded text-xs font-medium',
                          issue.severity === 'high' ? 'bg-red-100 text-red-700' :
                          issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        )}>
                          {issue.severity === 'high' ? 'High / 高' :
                           issue.severity === 'medium' ? 'Medium / 中' : 'Low / 低'}
                        </span>
                        {expandedIssueIndex === idx ? (
                          <ChevronUp className="w-4 h-4 text-gray-400 ml-auto" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-gray-400 ml-auto" />
                        )}
                      </div>
                      <p className="text-gray-900 mt-1">{issue.description}</p>
                      <p className="text-gray-600 text-sm">{issue.descriptionZh}</p>
                    </button>
                  </div>
                </div>
                {/* Expanded content section */}
                {expandedIssueIndex === idx && (
                  <div className="ml-8 mt-2 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                    {isLoadingSuggestion ? (
                      <div className="flex items-center gap-2 text-indigo-600">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Loading suggestions... / 加载建议中...</span>
                      </div>
                    ) : suggestionError ? (
                      <div className="text-red-600">{suggestionError}</div>
                    ) : issueSuggestion ? (
                      <div className="space-y-3">
                        <h4 className="font-semibold text-indigo-900 flex items-center gap-2">
                          <Sparkles className="w-4 h-4" />
                          AI Suggestions / AI建议
                        </h4>
                        <div>
                          <h5 className="text-sm font-medium text-indigo-800">Analysis / 分析:</h5>
                          <p className="text-indigo-700 mt-1">{issueSuggestion.analysis}</p>
                        </div>
                        {issueSuggestion.suggestions && issueSuggestion.suggestions.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium text-indigo-800">Suggestions / 建议:</h5>
                            <ul className="list-disc list-inside mt-1 space-y-1">
                              {issueSuggestion.suggestions.map((s, i) => (
                                <li key={i} className="text-indigo-700">{s}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {issueSuggestion.exampleFix && (
                          <div>
                            <h5 className="text-sm font-medium text-indigo-800">Example Fix / 示例修复:</h5>
                            <pre className="mt-1 p-2 bg-white rounded text-sm text-gray-800 overflow-x-auto">
                              {issueSuggestion.exampleFix}
                            </pre>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-gray-500">No suggestions available / 暂无建议</p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      {hasSelectedIssues && (
        <div className="mb-6 pb-6 border-b">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">{selectedIssueIndices.size} selected / 已选择 {selectedIssueIndices.size} 个问题</div>
            <div className="flex gap-2">
              <Button variant="secondary" size="sm" disabled={selectedIssueIndices.size === 0} onClick={() => { setMergeMode('prompt'); setShowMergeConfirm(true); }}>
                <Edit3 className="w-4 h-4 mr-2" />Prompt / 提示
              </Button>
              <Button variant="primary" size="sm" disabled={selectedIssueIndices.size === 0} onClick={() => { setMergeMode('apply'); setShowMergeConfirm(true); }}>
                <Sparkles className="w-4 h-4 mr-2" />AI Modify / AI修改
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Merge Confirm */}
      {showMergeConfirm && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h4 className="font-semibold text-yellow-900 mb-3">{mergeMode === 'prompt' ? 'Generate Prompt' : 'Apply AI Modification'}</h4>
          <textarea value={mergeUserNotes} onChange={(e) => setMergeUserNotes(e.target.value)} placeholder="Additional instructions..." className="w-full px-3 py-2 border border-yellow-300 rounded-lg mb-3" rows={2} />
          <div className="flex gap-2">
            <Button variant="primary" size="sm" onClick={executeMergeModify} disabled={isMerging}>
              {isMerging ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Check className="w-4 h-4 mr-2" />}Confirm
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setShowMergeConfirm(false)}><X className="w-4 h-4 mr-2" />Cancel</Button>
          </div>
        </div>
      )}

      {/* Merge Result */}
      {mergeResult && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <h4 className="font-semibold text-green-900 mb-3 flex items-center gap-2"><CheckCircle className="w-5 h-5" />Result</h4>
          {'prompt' in mergeResult && <pre className="p-3 bg-white rounded text-sm overflow-x-auto whitespace-pre-wrap">{mergeResult.prompt}</pre>}
          {'modifiedText' in mergeResult && (
            <>
              <pre className="p-3 bg-white rounded text-sm overflow-x-auto whitespace-pre-wrap max-h-96 overflow-y-auto">{mergeResult.modifiedText}</pre>
              <div className="flex gap-2 mt-4">
                <Button variant="primary" size="sm" onClick={handleAcceptModification}><Check className="w-4 h-4 mr-2" />Accept</Button>
                <Button variant="secondary" size="sm" onClick={handleRegenerate}><RefreshCw className="w-4 h-4 mr-2" />Regenerate</Button>
                <Button variant="secondary" size="sm" onClick={() => setMergeResult(null)}><X className="w-4 h-4 mr-2" />Cancel</Button>
              </div>
            </>
          )}
        </div>
      )}

      {/* No issues */}
      {replacementIssues.length === 0 && result && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div><h3 className="font-medium text-green-800">No Replacements Needed</h3><p className="text-green-600 mt-1">词汇使用良好，无需替换。</p></div>
        </div>
      )}

      {/* Document Modification */}
      {result && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2"><FileText className="w-5 h-5" />Document Modification</h3>
          <div className="flex gap-2 mb-4">
            <button onClick={() => setModifyMode('file')} className={clsx('px-4 py-2 rounded-lg text-sm font-medium', modifyMode === 'file' ? 'bg-orange-600 text-white' : 'bg-white border border-gray-300')}>
              <Upload className="w-4 h-4 inline mr-2" />Upload
            </button>
            <button onClick={() => setModifyMode('text')} className={clsx('px-4 py-2 rounded-lg text-sm font-medium', modifyMode === 'text' ? 'bg-orange-600 text-white' : 'bg-white border border-gray-300')}>
              <Edit3 className="w-4 h-4 inline mr-2" />Text
            </button>
          </div>
          {modifyMode === 'file' && (
            <div>
              <input ref={fileInputRef} type="file" accept=".txt,.md,.doc,.docx" onChange={handleFileSelect} className="hidden" />
              <div onClick={() => fileInputRef.current?.click()} className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-orange-400">
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600">{newFile ? newFile.name : 'Click to select'}</p>
              </div>
            </div>
          )}
          {modifyMode === 'text' && (
            <div>
              <textarea value={newText} onChange={(e) => setNewText(e.target.value)} placeholder="Paste text..." className="w-full px-3 py-2 border border-gray-300 rounded-lg min-h-[200px]" />
              <p className="text-gray-500 text-sm mt-1">{newText.length} chars</p>
            </div>
          )}
          <div className="mt-4 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              {modifyMode === 'file'
                ? (newFile ? 'File selected, ready to apply / 文件已选择，可以应用' : 'Please select a file first / 请先选择文件')
                : (newText.trim() ? 'Content entered, ready to apply / 内容已输入，可以应用' : 'Please enter content first / 请先输入内容')}
            </p>
            <Button variant="primary" onClick={handleConfirmModify} disabled={isUploading || (modifyMode === 'file' && !newFile) || (modifyMode === 'text' && !newText.trim())}>
              {isUploading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <ArrowRight className="w-4 h-4 mr-2" />}Apply & Continue
            </Button>
          </div>
        </div>
      )}

      {/* Skip Confirmation Dialog */}
      {/* 跳过确认对话框 */}
      {showSkipConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl">
            <div className="flex items-start gap-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-yellow-600 flex-shrink-0" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Skip without modifying? / 跳过不修改？
                </h3>
                <p className="text-gray-600 mt-2">
                  You have not applied any modifications on this page. Are you sure you want to skip to the next step?
                </p>
                <p className="text-gray-600 mt-1">
                  您尚未在此页面应用任何修改。确定要跳过到下一步吗？
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <Button
                variant="secondary"
                onClick={() => setShowSkipConfirm(false)}
              >
                Cancel / 取消
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  setShowSkipConfirm(false);
                  goToNextStep();
                }}
              >
                Confirm Skip / 确认跳过
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      {showNavigation && (
        <div className="flex justify-between items-center pt-4 border-t">
          <Button variant="outline" onClick={goToPreviousStep}><ArrowLeft className="w-4 h-4 mr-2" />Previous: Step 5.2</Button>
          <Button onClick={() => setShowSkipConfirm(true)} disabled={!result}>Skip and Continue / 跳过并继续<ArrowRight className="w-4 h-4 ml-2" /></Button>
        </div>
      )}
    </div>
  );
}
