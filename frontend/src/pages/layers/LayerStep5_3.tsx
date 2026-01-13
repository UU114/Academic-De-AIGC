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
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedSection, setExpandedSection] = useState<string | null>('replacements');

  const [replacementIssues, setReplacementIssues] = useState<DetectionIssue[]>([]);
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());
  const [issueSuggestion, setIssueSuggestion] = useState<IssueSuggestionResponse | null>(null);
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

  const loadIssueSuggestion = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentText) return;
    setIsLoadingSuggestion(true);
    setSuggestionError(null);

    try {
      const selectedIssues = Array.from(selectedIssueIndices).map(i => replacementIssues[i]);
      const response = await documentLayerApi.getIssueSuggestion(documentText, selectedIssues, 'step5_3', sessionId || undefined);
      setIssueSuggestion(response as IssueSuggestionResponse);
    } catch (err) {
      setSuggestionError('Failed to load suggestion');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [selectedIssueIndices, documentText, replacementIssues, sessionId]);

  const handleIssueClick = useCallback((index: number) => {
    setSelectedIssueIndices(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) newSet.delete(index);
      else newSet.add(index);
      return newSet;
    });
    setIssueSuggestion(null);
    setMergeResult(null);
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
      let newDocId: string;
      if (modifyMode === 'file' && newFile) {
        const result = await documentApi.upload(newFile);
        newDocId = result.documentId;
      } else if (modifyMode === 'text' && newText.trim()) {
        const result = await documentApi.uploadText(newText, `step5_3_modified_${Date.now()}.txt`);
        newDocId = result.documentId;
      } else {
        setError('Please select a file or enter text');
        setIsUploading(false);
        return;
      }

      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer1-step5-4/${newDocId}?${params.toString()}`);
    } catch (err) {
      setError('Failed to upload');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate]);

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

      {/* Issues */}
      {replacementIssues.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />Issues ({replacementIssues.length})
          </h3>
          <div className="space-y-2">
            {replacementIssues.map((issue, idx) => (
              <button key={idx} onClick={() => handleIssueClick(idx)} className={clsx(
                'w-full text-left p-3 rounded-lg border transition-all',
                selectedIssueIndices.has(idx) ? 'bg-orange-50 border-orange-300 ring-2 ring-orange-200' : 'bg-white border-gray-200 hover:border-gray-300'
              )}>
                <div className="flex items-start gap-3">
                  <div className={clsx('w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5', selectedIssueIndices.has(idx) ? 'bg-orange-600 border-orange-600' : 'border-gray-300')}>
                    {selectedIssueIndices.has(idx) && <Check className="w-3 h-3 text-white" />}
                  </div>
                  <div className="flex-1">
                    <p className="text-gray-900">{issue.description}</p>
                    <p className="text-gray-600 text-sm">{issue.descriptionZh}</p>
                  </div>
                </div>
              </button>
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
              <Button variant="secondary" size="sm" onClick={loadIssueSuggestion} disabled={isLoadingSuggestion || selectedIssueIndices.size === 0}>
                {isLoadingSuggestion ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Sparkles className="w-4 h-4 mr-2" />}Suggestions
              </Button>
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

      {/* Suggestion */}
      {issueSuggestion && (
        <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
          <h4 className="font-semibold text-indigo-900 mb-3">AI Suggestions</h4>
          <p className="text-indigo-700">{issueSuggestion.analysis}</p>
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
