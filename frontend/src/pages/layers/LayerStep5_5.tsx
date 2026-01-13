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
  ShieldCheck,
  Lock,
  TrendingDown,
  TrendingUp,
  Target,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import {
  lexicalLayerApi,
  documentLayerApi,
  ValidationResponse,
  DetectionIssue,
} from '../../services/analysisApi';

/**
 * Layer Step 5.5 - Validation
 * 步骤 5.5 - 验证
 *
 * Validates rewriting results:
 * - Checks locked terms preservation
 * - Measures semantic similarity
 * - Calculates risk improvement
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

interface LayerStep5_5Props {
  documentIdProp?: string;
  onComplete?: (result: ValidationResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep5_5({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep5_5Props) {
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
      sessionApi.updateStep(sessionId, 'layer1-step5-5').catch(console.error);
    }
  }, [sessionId]);

  const [result, setResult] = useState<ValidationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedSection, setExpandedSection] = useState<string | null>('summary');

  const [validationIssues, setValidationIssues] = useState<DetectionIssue[]>([]);
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
      const analysisResult = await lexicalLayerApi.validate(
        documentText,
        sessionId || undefined
      );

      setResult(analysisResult);

      // Convert to issues for display
      // 转换为显示用的问题列表
      const issues: DetectionIssue[] = [];

      if (!analysisResult.validationPassed) {
        issues.push({
          type: 'validation_failed',
          description: 'Validation did not pass',
          descriptionZh: '验证未通过',
          severity: 'high',
          layer: 'lexical',
        });
      }

      if (!analysisResult.lockedTermsCheck) {
        issues.push({
          type: 'locked_terms_altered',
          description: 'Some locked terms were altered during rewriting',
          descriptionZh: '改写过程中部分锁定词汇被修改',
          severity: 'high',
          layer: 'lexical',
        });
      }

      if (analysisResult.improvement < 0) {
        issues.push({
          type: 'risk_increased',
          description: `Risk score increased by ${Math.abs(analysisResult.improvement)} points`,
          descriptionZh: `风险分数增加了 ${Math.abs(analysisResult.improvement)} 分`,
          severity: 'high',
          layer: 'lexical',
        });
      }

      if (analysisResult.semanticSimilarity < 0.7) {
        issues.push({
          type: 'low_similarity',
          description: `Semantic similarity is low (${(analysisResult.semanticSimilarity * 100).toFixed(1)}%)`,
          descriptionZh: `语义相似度较低 (${(analysisResult.semanticSimilarity * 100).toFixed(1)}%)`,
          severity: analysisResult.semanticSimilarity < 0.5 ? 'high' : 'medium',
          layer: 'lexical',
        });
      }

      if (analysisResult.issues) {
        issues.push(...analysisResult.issues);
      }

      setValidationIssues(issues);

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
      const selectedIssues = Array.from(selectedIssueIndices).map(i => validationIssues[i]);
      const response = await documentLayerApi.getIssueSuggestion(documentText, selectedIssues, 'step5_5', sessionId || undefined);
      setIssueSuggestion(response as IssueSuggestionResponse);
    } catch (err) {
      setSuggestionError('Failed to load suggestion');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [selectedIssueIndices, documentText, validationIssues, sessionId]);

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
      const selectedIssues = Array.from(selectedIssueIndices).map(i => validationIssues[i]);
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
  }, [selectedIssueIndices, documentId, validationIssues, mergeMode, mergeUserNotes, sessionId]);

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
        const result = await documentApi.uploadText(newText, `step5_5_final_${Date.now()}.txt`);
        newDocId = result.documentId;
      } else {
        setError('Please select a file or enter text');
        setIsUploading(false);
        return;
      }

      // Navigate to completion or export page
      // 导航到完成或导出页面
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/complete/${newDocId}?${params.toString()}`);
    } catch (err) {
      setError('Failed to upload');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate]);

  const goToNextStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/complete/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer1-step5-4/${documentId}?${params.toString()}`);
  };

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const hasSelectedIssues = selectedIssueIndices.size > 0;

  // Calculate improvement percentage
  // 计算改进百分比
  const getImprovementPercent = () => {
    if (!result || !result.originalRiskScore || result.originalRiskScore === 0) return 0;
    return Math.round((result.improvement / result.originalRiskScore) * 100);
  };

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
            <div className="p-2 bg-emerald-100 rounded-lg"><ShieldCheck className="w-6 h-6 text-emerald-600" /></div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Step 5.5: Validation</h2>
              <p className="text-sm text-gray-500">步骤 5.5: 验证</p>
            </div>
          </div>
          {isAnalyzing && <div className="flex items-center gap-2 text-emerald-600"><Loader2 className="w-5 h-5 animate-spin" /><span>Validating...</span></div>}
        </div>

        <p className="text-gray-600 mb-4">
          Validates rewriting results for quality, locked term preservation, and risk improvement.
          <br /><span className="text-gray-500">验证改写结果的质量、锁定词汇保留和风险改进。</span>
        </p>

        {/* Stats */}
        {result && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-4">
            <div className={clsx('rounded-lg p-4', result.validationPassed ? 'bg-green-50' : 'bg-red-50')}>
              <div className={clsx('flex items-center gap-2 mb-1', result.validationPassed ? 'text-green-600' : 'text-red-600')}>
                {result.validationPassed ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                <span className="text-sm font-medium">Status</span>
              </div>
              <div className={clsx('text-2xl font-bold', result.validationPassed ? 'text-green-700' : 'text-red-700')}>
                {result.validationPassed ? 'PASS' : 'FAIL'}
              </div>
              <div className={clsx('text-xs', result.validationPassed ? 'text-green-500' : 'text-red-500')}>验证状态</div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-600 mb-1"><Target className="w-4 h-4" /><span className="text-sm font-medium">Original</span></div>
              <div className="text-2xl font-bold text-gray-700">{result.originalRiskScore || 0}</div>
              <div className="text-xs text-gray-500">原始风险</div>
            </div>

            <div className={clsx('rounded-lg p-4', result.finalRiskScore <= 30 ? 'bg-green-50' : result.finalRiskScore <= 60 ? 'bg-yellow-50' : 'bg-red-50')}>
              <div className={clsx('flex items-center gap-2 mb-1', result.finalRiskScore <= 30 ? 'text-green-600' : result.finalRiskScore <= 60 ? 'text-yellow-600' : 'text-red-600')}>
                <Target className="w-4 h-4" /><span className="text-sm font-medium">Final</span>
              </div>
              <div className={clsx('text-2xl font-bold', result.finalRiskScore <= 30 ? 'text-green-700' : result.finalRiskScore <= 60 ? 'text-yellow-700' : 'text-red-700')}>
                {result.finalRiskScore || 0}
              </div>
              <div className={clsx('text-xs', result.finalRiskScore <= 30 ? 'text-green-500' : result.finalRiskScore <= 60 ? 'text-yellow-500' : 'text-red-500')}>最终风险</div>
            </div>

            <div className={clsx('rounded-lg p-4', result.improvement >= 0 ? 'bg-green-50' : 'bg-red-50')}>
              <div className={clsx('flex items-center gap-2 mb-1', result.improvement >= 0 ? 'text-green-600' : 'text-red-600')}>
                {result.improvement >= 0 ? <TrendingDown className="w-4 h-4" /> : <TrendingUp className="w-4 h-4" />}
                <span className="text-sm font-medium">Change</span>
              </div>
              <div className={clsx('text-2xl font-bold', result.improvement >= 0 ? 'text-green-700' : 'text-red-700')}>
                {result.improvement >= 0 ? '-' : '+'}{Math.abs(result.improvement)}
              </div>
              <div className={clsx('text-xs', result.improvement >= 0 ? 'text-green-500' : 'text-red-500')}>
                {result.improvement >= 0 ? '风险降低' : '风险上升'} ({getImprovementPercent()}%)
              </div>
            </div>

            <div className={clsx('rounded-lg p-4', result.lockedTermsCheck ? 'bg-green-50' : 'bg-red-50')}>
              <div className={clsx('flex items-center gap-2 mb-1', result.lockedTermsCheck ? 'text-green-600' : 'text-red-600')}>
                <Lock className="w-4 h-4" /><span className="text-sm font-medium">Locked</span>
              </div>
              <div className={clsx('text-2xl font-bold', result.lockedTermsCheck ? 'text-green-700' : 'text-red-700')}>
                {result.lockedTermsCheck ? 'OK' : 'WARN'}
              </div>
              <div className={clsx('text-xs', result.lockedTermsCheck ? 'text-green-500' : 'text-red-500')}>锁定词状态</div>
            </div>
          </div>
        )}
      </div>

      {/* Validation Summary */}
      {result && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between cursor-pointer" onClick={() => toggleSection('summary')}>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              Validation Summary
            </h3>
            {expandedSection === 'summary' ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
          </div>

          {expandedSection === 'summary' && (
            <div className="mt-4 space-y-4">
              {/* Semantic Similarity */}
              <div className="p-4 rounded-lg bg-gray-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-700">Semantic Similarity / 语义相似度</span>
                  <span className={clsx('font-bold', result.semanticSimilarity >= 0.8 ? 'text-green-600' : result.semanticSimilarity >= 0.6 ? 'text-yellow-600' : 'text-red-600')}>
                    {(result.semanticSimilarity * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={clsx('h-2 rounded-full', result.semanticSimilarity >= 0.8 ? 'bg-green-500' : result.semanticSimilarity >= 0.6 ? 'bg-yellow-500' : 'bg-red-500')}
                    style={{ width: `${result.semanticSimilarity * 100}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">Measures how well the meaning is preserved after rewriting</p>
              </div>

              {/* Risk Comparison */}
              <div className="p-4 rounded-lg bg-gray-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-700">Risk Score Comparison / 风险分对比</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="text-sm text-gray-500 mb-1">Before</div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div className="h-3 rounded-full bg-red-400" style={{ width: `${result.originalRiskScore}%` }} />
                    </div>
                    <div className="text-sm text-gray-600 mt-1">{result.originalRiskScore}</div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-400" />
                  <div className="flex-1">
                    <div className="text-sm text-gray-500 mb-1">After</div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div className={clsx('h-3 rounded-full', result.finalRiskScore <= 30 ? 'bg-green-400' : result.finalRiskScore <= 60 ? 'bg-yellow-400' : 'bg-red-400')} style={{ width: `${result.finalRiskScore}%` }} />
                    </div>
                    <div className="text-sm text-gray-600 mt-1">{result.finalRiskScore}</div>
                  </div>
                </div>
              </div>

              {/* Final Verdict */}
              <div className={clsx('p-4 rounded-lg', result.validationPassed ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200')}>
                <div className="flex items-center gap-2">
                  {result.validationPassed ? <CheckCircle className="w-6 h-6 text-green-600" /> : <AlertCircle className="w-6 h-6 text-red-600" />}
                  <div>
                    <div className={clsx('font-semibold', result.validationPassed ? 'text-green-700' : 'text-red-700')}>
                      {result.validationPassed ? 'Validation Passed' : 'Validation Failed'}
                    </div>
                    <div className={clsx('text-sm', result.validationPassed ? 'text-green-600' : 'text-red-600')}>
                      {result.validationPassed ? '验证通过 - 文档可以导出' : '验证失败 - 需要进一步修改'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Issues */}
      {validationIssues.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />Issues ({validationIssues.length})
          </h3>
          <div className="space-y-2">
            {validationIssues.map((issue, idx) => (
              <button key={idx} onClick={() => handleIssueClick(idx)} className={clsx(
                'w-full text-left p-3 rounded-lg border transition-all',
                selectedIssueIndices.has(idx) ? 'bg-emerald-50 border-emerald-300 ring-2 ring-emerald-200' : 'bg-white border-gray-200 hover:border-gray-300'
              )}>
                <div className="flex items-start gap-3">
                  <div className={clsx('w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5', selectedIssueIndices.has(idx) ? 'bg-emerald-600 border-emerald-600' : 'border-gray-300')}>
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

      {/* Validation Passed */}
      {validationIssues.length === 0 && result && result.validationPassed && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-green-800">Validation Passed</h3>
            <p className="text-green-600 mt-1">文档验证通过，可以导出。</p>
          </div>
        </div>
      )}

      {/* Document Modification / Export */}
      {result && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            {result.validationPassed ? 'Export Document' : 'Document Modification'}
          </h3>
          <div className="flex gap-2 mb-4">
            <button onClick={() => setModifyMode('file')} className={clsx('px-4 py-2 rounded-lg text-sm font-medium', modifyMode === 'file' ? 'bg-emerald-600 text-white' : 'bg-white border border-gray-300')}>
              <Upload className="w-4 h-4 inline mr-2" />Upload
            </button>
            <button onClick={() => setModifyMode('text')} className={clsx('px-4 py-2 rounded-lg text-sm font-medium', modifyMode === 'text' ? 'bg-emerald-600 text-white' : 'bg-white border border-gray-300')}>
              <Edit3 className="w-4 h-4 inline mr-2" />Text
            </button>
          </div>
          {modifyMode === 'file' && (
            <div>
              <input ref={fileInputRef} type="file" accept=".txt,.md,.doc,.docx" onChange={handleFileSelect} className="hidden" />
              <div onClick={() => fileInputRef.current?.click()} className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-emerald-400">
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600">{newFile ? newFile.name : 'Click to select'}</p>
              </div>
            </div>
          )}
          {modifyMode === 'text' && (
            <div>
              <textarea value={newText} onChange={(e) => setNewText(e.target.value)} placeholder="Paste final text..." className="w-full px-3 py-2 border border-gray-300 rounded-lg min-h-[200px]" />
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
              {isUploading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
              {result.validationPassed ? 'Complete & Export' : 'Apply & Continue'}
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
          <Button variant="outline" onClick={goToPreviousStep}><ArrowLeft className="w-4 h-4 mr-2" />Previous: Step 5.4</Button>
          <Button onClick={() => setShowSkipConfirm(true)} disabled={!result || !result.validationPassed}>Skip and Continue / 跳过并继续<ArrowRight className="w-4 h-4 ml-2" /></Button>
        </div>
      )}
    </div>
  );
}
