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
  FileText,
  RefreshCw,
  AlertTriangle,
  Sparkles,
  Edit3,
  Upload,
  Check,
  X,
  PenTool,
  Lock,
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
  ParagraphRewriteResponse,
  DetectionIssue,
} from '../../services/analysisApi';

/**
 * Layer Step 5.4 - Paragraph Rewriting
 * 步骤 5.4 - 段落级改写
 *
 * Rewrites paragraphs to:
 * - Reduce AI fingerprints
 * - Preserve locked terms
 * - Improve human-like features
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

interface ChangeInfo {
  original: string;
  modified: string;
  reason?: string;
  reasonZh?: string;
}

interface LayerStep5_4Props {
  documentIdProp?: string;
  onComplete?: (result: ParagraphRewriteResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep5_4({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep5_4Props) {
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
      sessionApi.updateStep(sessionId, 'layer1-step5-4').catch(console.error);
    }
  }, [sessionId]);

  const [result, setResult] = useState<ParagraphRewriteResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedSection, setExpandedSection] = useState<string | null>('rewrite');

  const [rewriteIssues, setRewriteIssues] = useState<DetectionIssue[]>([]);
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

      // Check previous steps for modified text (step1-3, step1-2, step1-1, step1-0)
      // 检查前序步骤的修改文本
      const previousSteps = ['step1-3', 'step1-2', 'step1-1', 'step1-0'];
      let foundModifiedText: string | null = null;

      for (const stepName of previousSteps) {
        const stepState = substepStore.getState(stepName);
        if (stepState?.modifiedText) {
          console.log(`[LayerStep5_4] Using modified text from ${stepName}`);
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

  // Run analysis when document is loaded and user starts analysis
  // 文档加载后且用户开始分析时运行分析
  useEffect(() => {
    if (documentText && analysisStarted && !isAnalyzingRef.current) {
      runAnalysis();
    }
  }, [documentText, analysisStarted]);

  const runAnalysis = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;
    setIsAnalyzing(true);
    setError(null);

    try {
      const analysisResult = await lexicalLayerApi.analyzeParagraphRewrite(
        documentText,
        sessionId || undefined
      );

      setResult(analysisResult);

      // Convert to issues for display
      // 转换为显示用的问题列表
      const issues: DetectionIssue[] = [];

      if (analysisResult.rewrittenText && analysisResult.rewrittenText !== analysisResult.originalText) {
        issues.push({
          type: 'rewrite_available',
          description: 'Paragraph rewriting is available',
          descriptionZh: '段落改写可用',
          severity: 'medium',
          layer: 'lexical',
        });
      }

      if (analysisResult.changes && analysisResult.changes.length > 0) {
        issues.push({
          type: 'changes_made',
          description: `${analysisResult.changes.length} changes suggested`,
          descriptionZh: `${analysisResult.changes.length} 处建议修改`,
          severity: analysisResult.changes.length > 5 ? 'high' : 'medium',
          layer: 'lexical',
        });
      }

      if (!analysisResult.lockedTermsPreserved) {
        issues.push({
          type: 'locked_terms_issue',
          description: 'Warning: Some locked terms may have been altered',
          descriptionZh: '警告：部分锁定词汇可能被修改',
          severity: 'high',
          layer: 'lexical',
        });
      }

      if (analysisResult.issues) {
        issues.push(...analysisResult.issues);
      }

      setRewriteIssues(issues);

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

  // Load suggestion for a single issue with caching
  // 加载单个问题的建议，带缓存功能
  const loadIssueSuggestion = useCallback(async (index: number) => {
    const issue = rewriteIssues[index];
    if (!issue || !documentId) return;
    const cached = suggestionCacheRef.current.get(index);
    if (cached) { setIssueSuggestion(cached); return; }
    setIsLoadingSuggestion(true);
    setSuggestionError(null);
    try {
      const response = await documentLayerApi.getIssueSuggestion(documentText, [issue], 'step5_4', sessionId || undefined);
      const suggestion = response as IssueSuggestionResponse;
      suggestionCacheRef.current.set(index, suggestion);
      setIssueSuggestion(suggestion);
    } catch (err) {
      console.error('Failed to load suggestion:', err);
      setSuggestionError('Failed to load detailed suggestion / 加载详细建议失败');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [rewriteIssues, documentId, documentText, sessionId]);

  // Handle clicking on issue content to expand/collapse
  // 处理点击问题内容以展开/折叠
  const handleIssueClick = useCallback(async (index: number) => {
    if (expandedIssueIndex === index) {
      setExpandedIssueIndex(null);
      setIssueSuggestion(null);
      return;
    }
    setExpandedIssueIndex(index);
    await loadIssueSuggestion(index);
  }, [expandedIssueIndex, loadIssueSuggestion]);

  // Toggle issue selection via checkbox only
  // 仅通过复选框切换问题选择
  const toggleIssueSelection = useCallback((index: number) => {
    setSelectedIssueIndices(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) newSet.delete(index);
      else newSet.add(index);
      return newSet;
    });
    setMergeResult(null);
  }, []);

  // Select all issues
  // 全选所有问题
  const selectAllIssues = useCallback(() => {
    setSelectedIssueIndices(new Set(rewriteIssues.map((_, idx) => idx)));
  }, [rewriteIssues]);

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
      const selectedIssues = Array.from(selectedIssueIndices).map(i => rewriteIssues[i]);
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
  }, [selectedIssueIndices, documentId, rewriteIssues, mergeMode, mergeUserNotes, sessionId]);

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

  const handleAcceptRewrite = useCallback(() => {
    if (result?.rewrittenText) {
      setNewText(result.rewrittenText);
      setModifyMode('text');
    }
  }, [result]);

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
        await substepStore.saveModifiedText('step1-4', modifiedText);
        await substepStore.markCompleted('step1-4');
        console.log('[LayerStep5_4] Saved modified text to substep store');
      }

      // Navigate to next step with same document ID
      // 使用相同的文档ID导航到下一步
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer1-step5-5/${documentId}?${params.toString()}`);
    } catch (err) {
      setError('Failed to upload');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate, documentId, substepStore]);

  const goToNextStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer1-step5-5/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer1-step5-3/${documentId}?${params.toString()}`);
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
            <div className="p-2 bg-teal-100 rounded-lg"><PenTool className="w-6 h-6 text-teal-600" /></div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Step 5.4: Paragraph Rewriting</h2>
              <p className="text-sm text-gray-500">步骤 5.4: 段落级改写</p>
            </div>
          </div>
          {isAnalyzing && <div className="flex items-center gap-2 text-teal-600"><Loader2 className="w-5 h-5 animate-spin" /><span>Analyzing...</span></div>}
        </div>

        <p className="text-gray-600 mb-4">
          Rewrites paragraphs to reduce AI fingerprints while preserving locked terms.
          <br /><span className="text-gray-500">改写段落以减少AI指纹，同时保留锁定词汇。</span>
        </p>

        {/* Stats */}
        {result && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className="bg-teal-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-teal-600 mb-1"><PenTool className="w-4 h-4" /><span className="text-sm font-medium">Changes</span></div>
              <div className="text-2xl font-bold text-teal-700">{result.changes?.length || 0}</div>
              <div className="text-xs text-teal-500">修改数</div>
            </div>
            <div className={clsx('rounded-lg p-4', result.lockedTermsPreserved ? 'bg-green-50' : 'bg-red-50')}>
              <div className={clsx('flex items-center gap-2 mb-1', result.lockedTermsPreserved ? 'text-green-600' : 'text-red-600')}>
                <Lock className="w-4 h-4" /><span className="text-sm font-medium">Locked</span>
              </div>
              <div className={clsx('text-2xl font-bold', result.lockedTermsPreserved ? 'text-green-700' : 'text-red-700')}>
                {result.lockedTermsPreserved ? 'OK' : 'WARN'}
              </div>
              <div className={clsx('text-xs', result.lockedTermsPreserved ? 'text-green-500' : 'text-red-500')}>锁定词状态</div>
            </div>
            <div className={clsx('rounded-lg p-4', result.riskLevel === 'low' ? 'bg-green-50' : result.riskLevel === 'medium' ? 'bg-yellow-50' : 'bg-red-50')}>
              <div className={clsx('flex items-center gap-2 mb-1', result.riskLevel === 'low' ? 'text-green-600' : result.riskLevel === 'medium' ? 'text-yellow-600' : 'text-red-600')}>
                {result.riskLevel === 'low' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                <span className="text-sm font-medium">Risk</span>
              </div>
              <div className={clsx('text-2xl font-bold', result.riskLevel === 'low' ? 'text-green-700' : result.riskLevel === 'medium' ? 'text-yellow-700' : 'text-red-700')}>
                {result.riskScore || 0}
              </div>
              <div className={clsx('text-xs', result.riskLevel === 'low' ? 'text-green-500' : result.riskLevel === 'medium' ? 'text-yellow-500' : 'text-red-500')}>风险分</div>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-blue-600 mb-1"><FileText className="w-4 h-4" /><span className="text-sm font-medium">Status</span></div>
              <div className="text-2xl font-bold text-blue-700">{result.rewrittenText ? 'Ready' : 'N/A'}</div>
              <div className="text-xs text-blue-500">改写状态</div>
            </div>
          </div>
        )}
      </div>

      {/* Start Analysis / Skip Step */}
      {/* 开始分析 / 跳过此步 */}
      {documentText && !analysisStarted && !isAnalyzing && !result && (
        <div className="mb-6 p-6 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="text-center">
            <PenTool className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Analyze / 准备分析</h3>
            <p className="text-gray-600 mb-6">
              Click "Start Analysis" to rewrite paragraphs to reduce AI fingerprints while preserving locked terms.
              <br />
              <span className="text-gray-500">点击"开始分析"以改写段落，减少AI指纹同时保留锁定词汇。</span>
            </p>
            <div className="flex items-center justify-center gap-4">
              <Button
                variant="primary"
                size="lg"
                onClick={() => setAnalysisStarted(true)}
              >
                <Sparkles className="w-5 h-5 mr-2" />
                Start Analysis / 开始分析
              </Button>
              <Button
                variant="secondary"
                size="lg"
                onClick={() => setShowSkipConfirm(true)}
              >
                <ArrowRight className="w-5 h-5 mr-2" />
                Skip Step / 跳过此步
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Rewritten Text Preview */}
      {result && result.rewrittenText && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between cursor-pointer" onClick={() => toggleSection('rewrite')}>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <PenTool className="w-5 h-5 text-teal-600" />
              Rewritten Text Preview
            </h3>
            {expandedSection === 'rewrite' ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
          </div>

          {expandedSection === 'rewrite' && (
            <div className="mt-4">
              <div className="p-4 bg-teal-50 rounded-lg border border-teal-200 max-h-96 overflow-y-auto">
                <pre className="whitespace-pre-wrap text-sm text-gray-700">{result.rewrittenText}</pre>
              </div>
              <div className="mt-4 flex gap-2">
                <Button variant="primary" size="sm" onClick={handleAcceptRewrite}>
                  <Check className="w-4 h-4 mr-2" />Accept Rewrite / 接受改写
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Changes List */}
      {result && result.changes && result.changes.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between cursor-pointer" onClick={() => toggleSection('changes')}>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Edit3 className="w-5 h-5 text-teal-600" />
              Changes ({result.changes.length})
            </h3>
            {expandedSection === 'changes' ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
          </div>

          {expandedSection === 'changes' && (
            <div className="mt-4 space-y-3 max-h-96 overflow-y-auto">
              {result.changes.map((change: ChangeInfo, index: number) => (
                <div key={index} className="p-4 rounded-lg border bg-gray-50">
                  <div className="flex items-start gap-4">
                    <div className="flex-1">
                      <div className="text-sm text-gray-500 mb-1">Original:</div>
                      <div className="text-red-700 line-through">{change.original}</div>
                    </div>
                    <div className="text-gray-400">→</div>
                    <div className="flex-1">
                      <div className="text-sm text-gray-500 mb-1">Modified:</div>
                      <div className="text-green-700">{change.modified}</div>
                    </div>
                  </div>
                  {change.reasonZh && <div className="text-xs text-gray-500 mt-2">{change.reasonZh}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Issues */}
      {rewriteIssues.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              Issues ({rewriteIssues.length})
              <span className="text-sm font-normal text-gray-500">
                ({selectedIssueIndices.size}/{rewriteIssues.length} selected / 已选择)
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
            {rewriteIssues.map((issue, idx) => (
              <div key={idx} className={clsx(
                'rounded-lg border transition-all',
                selectedIssueIndices.has(idx) ? 'bg-teal-50 border-teal-300 ring-2 ring-teal-200' : 'bg-white border-gray-200'
              )}>
                <div className="flex items-start gap-3 p-3">
                  {/* Checkbox button - separate click handler */}
                  {/* 复选框按钮 - 单独的点击处理 */}
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleIssueSelection(idx); }}
                    className={clsx('w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors', selectedIssueIndices.has(idx) ? 'bg-teal-600 border-teal-600' : 'border-gray-300 hover:border-teal-400')}
                  >
                    {selectedIssueIndices.has(idx) && <Check className="w-3 h-3 text-white" />}
                  </button>
                  {/* Content button - click to expand */}
                  {/* 内容按钮 - 点击展开 */}
                  <button
                    onClick={() => handleIssueClick(idx)}
                    className="flex-1 text-left"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="text-gray-900">{issue.description}</p>
                        <p className="text-gray-600 text-sm">{issue.descriptionZh}</p>
                      </div>
                      {expandedIssueIndex === idx ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                    </div>
                  </button>
                </div>
                {/* Expanded content section */}
                {/* 展开内容区域 */}
                {expandedIssueIndex === idx && (
                  <div className="px-3 pb-3 pt-0 ml-8 border-t border-gray-100">
                    {isLoadingSuggestion ? (
                      <div className="flex items-center gap-2 text-teal-600 py-3">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-sm">Loading suggestions... / 加载建议中...</span>
                      </div>
                    ) : suggestionError ? (
                      <div className="text-red-600 text-sm py-3">{suggestionError}</div>
                    ) : issueSuggestion ? (
                      <div className="py-3 space-y-2">
                        <p className="text-sm text-gray-700"><span className="font-medium">Analysis:</span> {issueSuggestion.analysis}</p>
                        {issueSuggestion.suggestions && issueSuggestion.suggestions.length > 0 && (
                          <div>
                            <p className="text-sm font-medium text-gray-700">Suggestions:</p>
                            <ul className="list-disc list-inside text-sm text-gray-600 ml-2">
                              {issueSuggestion.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                            </ul>
                          </div>
                        )}
                        {issueSuggestion.exampleFix && (
                          <p className="text-sm text-gray-700"><span className="font-medium">Example:</span> {issueSuggestion.exampleFix}</p>
                        )}
                      </div>
                    ) : null}
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
                <Edit3 className="w-4 h-4 mr-2" />Prompt
              </Button>
              <Button variant="primary" size="sm" disabled={selectedIssueIndices.size === 0} onClick={() => { setMergeMode('apply'); setShowMergeConfirm(true); }}>
                <Sparkles className="w-4 h-4 mr-2" />AI Modify
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

      {/* No rewrite needed */}
      {rewriteIssues.length === 0 && result && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div><h3 className="font-medium text-green-800">No Rewriting Needed</h3><p className="text-green-600 mt-1">文档无需改写。</p></div>
        </div>
      )}

      {/* Document Modification */}
      {result && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2"><FileText className="w-5 h-5" />Document Modification</h3>
          <div className="flex gap-2 mb-4">
            <button onClick={() => setModifyMode('file')} className={clsx('px-4 py-2 rounded-lg text-sm font-medium', modifyMode === 'file' ? 'bg-teal-600 text-white' : 'bg-white border border-gray-300')}>
              <Upload className="w-4 h-4 inline mr-2" />Upload
            </button>
            <button onClick={() => setModifyMode('text')} className={clsx('px-4 py-2 rounded-lg text-sm font-medium', modifyMode === 'text' ? 'bg-teal-600 text-white' : 'bg-white border border-gray-300')}>
              <Edit3 className="w-4 h-4 inline mr-2" />Text
            </button>
          </div>
          {modifyMode === 'file' && (
            <div>
              <input ref={fileInputRef} type="file" accept=".txt,.md,.doc,.docx" onChange={handleFileSelect} className="hidden" />
              <div onClick={() => fileInputRef.current?.click()} className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-teal-400">
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
          <Button variant="outline" onClick={goToPreviousStep}><ArrowLeft className="w-4 h-4 mr-2" />Previous: Step 5.3</Button>
          <Button onClick={() => setShowSkipConfirm(true)} disabled={!result}>Skip and Continue / 跳过并继续<ArrowRight className="w-4 h-4 ml-2" /></Button>
        </div>
      )}
    </div>
  );
}
