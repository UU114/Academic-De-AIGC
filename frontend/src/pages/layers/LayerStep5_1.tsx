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
  Fingerprint,
  FileText,
  RefreshCw,
  AlertTriangle,
  Sparkles,
  Edit3,
  Upload,
  Check,
  X,
  Target,
  Zap,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import {
  lexicalLayerApi,
  documentLayerApi,
  FingerprintDetectionResponse,
  FingerprintMatch,
  DetectionIssue,
} from '../../services/analysisApi';

/**
 * Layer Step 5.1 - AI Fingerprint Detection
 * 步骤 5.1 - AI指纹检测
 *
 * Detects AI-typical words and phrases in the document.
 * 检测文档中AI典型词汇和短语。
 *
 * Three types of fingerprints:
 * - Type A: Dead giveaways (delve, utilize, facilitate, etc.)
 * - Type B: Cliches (plays a crucial role, etc.)
 * - Type C: Filler phrases (as previously mentioned, etc.)
 *
 * 三类指纹：
 * - A类：明显标记词（delve, utilize等）
 * - B类：陈词滥调（plays a crucial role等）
 * - C类：填充短语（as previously mentioned等）
 */

// Response type for issue suggestions
// 问题建议响应类型
interface IssueSuggestionResponse {
  analysis: string;
  suggestions: string[];
  exampleFix?: string;
}

// Response type for modify prompt
// 修改提示响应类型
interface ModifyPromptResponse {
  prompt: string;
  promptZh?: string;
  issuesSummaryZh?: string;
}

// Response type for apply modify
// 应用修改响应类型
interface ApplyModifyResponse {
  modifiedText: string;
  changesSummary?: string;
  changesCount?: number;
}

interface LayerStep5_1Props {
  documentIdProp?: string;
  onComplete?: (result: FingerprintDetectionResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep5_1({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep5_1Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // Helper function to check if documentId is valid
  // 检查documentId是否有效的辅助函数
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
          if (sessionState.documentId) {
            setDocumentId(sessionState.documentId);
          }
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

  // Update session step
  // 更新会话步骤
  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer1-step5-1').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<FingerprintDetectionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedSection, setExpandedSection] = useState<string | null>('typeA');

  // Issues derived from analysis result
  // 从分析结果派生的问题列表
  const [fingerprintIssues, setFingerprintIssues] = useState<DetectionIssue[]>([]);

  // Issue selection for merge modify
  // 用于合并修改的问题选择
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());

  // Issue suggestion state
  // 问题建议状态
  const [issueSuggestion, setIssueSuggestion] = useState<IssueSuggestionResponse | null>(null);
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);

  // Merge modify state
  // 合并修改状态
  const [showMergeConfirm, setShowMergeConfirm] = useState(false);
  const [mergeMode, setMergeMode] = useState<'prompt' | 'apply'>('prompt');
  const [mergeUserNotes, setMergeUserNotes] = useState('');
  const [isMerging, setIsMerging] = useState(false);
  const [mergeResult, setMergeResult] = useState<ModifyPromptResponse | ApplyModifyResponse | null>(null);

  // Document modification state
  // 文档修改状态
  const [modifyMode, setModifyMode] = useState<'file' | 'text'>('file');
  const [newFile, setNewFile] = useState<File | null>(null);
  const [newText, setNewText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Skip confirmation state
  // 跳过确认状态
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);

  const isAnalyzingRef = useRef(false);

  // Load document
  // 加载文档
  useEffect(() => {
    if (!sessionFetchAttempted) return;
    if (isValidDocumentId(documentId)) {
      loadDocumentText(documentId!);
    } else {
      setError('Document ID not found. / 未找到文档ID。');
      setIsLoading(false);
    }
  }, [documentId, sessionFetchAttempted]);

  const loadDocumentText = async (docId: string) => {
    try {
      const doc = await documentApi.get(docId);
      if (doc.originalText) {
        setDocumentText(doc.originalText);
      } else {
        setError('Document text not found / 未找到文档文本');
      }
    } catch (err) {
      console.error('Failed to load document:', err);
      setError('Failed to load document / 加载文档失败');
    } finally {
      setIsLoading(false);
    }
  };

  // Run analysis when document is loaded
  // 文档加载后运行分析
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
      const analysisResult = await lexicalLayerApi.detectFingerprints(
        documentText,
        sessionId || undefined
      );

      setResult(analysisResult);

      // Create issues from analysis result
      // 从分析结果创建问题列表
      const issues: DetectionIssue[] = [];

      // Type A fingerprints (most severe)
      // A类指纹（最严重）
      if (analysisResult.typeAWords && analysisResult.typeAWords.length > 0) {
        analysisResult.typeAWords.forEach((match: FingerprintMatch) => {
          issues.push({
            type: 'type_a_fingerprint',
            description: `AI fingerprint word "${match.word}" found ${match.count} time(s)`,
            descriptionZh: `发现AI指纹词 "${match.word}" ${match.count} 次`,
            severity: 'high',
            layer: 'lexical',
            position: { positions: match.positions },
          });
        });
      }

      // Type B cliches
      // B类陈词滥调
      if (analysisResult.typeBWords && analysisResult.typeBWords.length > 0) {
        analysisResult.typeBWords.forEach((match: FingerprintMatch) => {
          issues.push({
            type: 'type_b_cliche',
            description: `AI cliche phrase "${match.phrase}" found ${match.count} time(s)`,
            descriptionZh: `发现AI陈词滥调 "${match.phrase}" ${match.count} 次`,
            severity: 'high',
            layer: 'lexical',
            position: { positions: match.positions },
          });
        });
      }

      // Type C filler phrases
      // C类填充短语
      if (analysisResult.typeCPhrases && analysisResult.typeCPhrases.length > 0) {
        analysisResult.typeCPhrases.forEach((match: FingerprintMatch) => {
          issues.push({
            type: 'type_c_filler',
            description: `Filler phrase "${match.phrase}" found ${match.count} time(s)`,
            descriptionZh: `发现填充短语 "${match.phrase}" ${match.count} 次`,
            severity: 'medium',
            layer: 'lexical',
            position: { positions: match.positions },
          });
        });
      }

      // High fingerprint density
      // 高指纹密度
      if (analysisResult.fingerprintDensity && analysisResult.fingerprintDensity > 0.02) {
        issues.push({
          type: 'high_fingerprint_density',
          description: `High fingerprint density (${(analysisResult.fingerprintDensity * 100).toFixed(1)}%) - strong AI signal`,
          descriptionZh: `指纹密度过高 (${(analysisResult.fingerprintDensity * 100).toFixed(1)}%) - 强AI信号`,
          severity: 'high',
          layer: 'lexical',
        });
      }

      // Add API issues
      // 添加API返回的问题
      if (analysisResult.issues) {
        issues.push(...analysisResult.issues);
      }

      setFingerprintIssues(issues);

      if (onComplete) {
        onComplete(analysisResult);
      }
    } catch (err) {
      console.error('Analysis failed:', err);
      setError('Analysis failed / 分析失败');
    } finally {
      setIsAnalyzing(false);
      isAnalyzingRef.current = false;
    }
  };

  // Load detailed suggestion
  // 加载详细建议
  const loadIssueSuggestion = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentText) return;

    setIsLoadingSuggestion(true);
    setSuggestionError(null);

    try {
      const selectedIssues = Array.from(selectedIssueIndices).map(i => fingerprintIssues[i]);
      const response = await documentLayerApi.getIssueSuggestion(
        documentText,
        selectedIssues,
        'step5_1',
        sessionId || undefined
      );
      setIssueSuggestion(response as IssueSuggestionResponse);
    } catch (err) {
      console.error('Failed to load suggestion:', err);
      setSuggestionError('Failed to load detailed suggestion / 加载详细建议失败');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [selectedIssueIndices, documentText, fingerprintIssues, sessionId]);

  // Handle issue selection toggle
  // 处理问题选择切换
  const handleIssueClick = useCallback((index: number) => {
    setSelectedIssueIndices(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
    setIssueSuggestion(null);
    setMergeResult(null);
  }, []);

  // Execute merge modify
  // 执行合并修改
  const executeMergeModify = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentId) return;

    setIsMerging(true);
    setShowMergeConfirm(false);

    try {
      const selectedIssues = Array.from(selectedIssueIndices).map(i => fingerprintIssues[i]);

      if (mergeMode === 'prompt') {
        const response = await documentLayerApi.generateModifyPrompt(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult(response as ModifyPromptResponse);
      } else {
        const response = await documentLayerApi.applyModify(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult(response as ApplyModifyResponse);
      }
    } catch (err) {
      console.error('Merge modify failed:', err);
      setError('Merge modify failed / 合并修改失败');
    } finally {
      setIsMerging(false);
    }
  }, [selectedIssueIndices, documentId, fingerprintIssues, mergeMode, mergeUserNotes, sessionId]);

  // Handle regenerate
  // 处理重新生成
  const handleRegenerate = useCallback(() => {
    setMergeResult(null);
    setShowMergeConfirm(true);
    setMergeMode('apply');
  }, []);

  // Handle accept modification
  // 处理接受修改
  const handleAcceptModification = useCallback(() => {
    if (mergeResult && 'modifiedText' in mergeResult && mergeResult.modifiedText) {
      setNewText(mergeResult.modifiedText);
      setModifyMode('text');
      setMergeResult(null);
    }
  }, [mergeResult]);

  // Handle file selection
  // 处理文件选择
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setNewFile(file);
    }
  }, []);

  // Handle confirm modification
  // 处理确认修改
  const handleConfirmModify = useCallback(async () => {
    setIsUploading(true);
    setError(null);

    try {
      let newDocId: string;

      if (modifyMode === 'file' && newFile) {
        const result = await documentApi.upload(newFile);
        newDocId = result.documentId;
      } else if (modifyMode === 'text' && newText.trim()) {
        const result = await documentApi.uploadText(newText, `step5_1_modified_${Date.now()}.txt`);
        newDocId = result.documentId;
      } else {
        setError('Please select a file or enter text / 请选择文件或输入文本');
        setIsUploading(false);
        return;
      }

      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer1-step5-2/${newDocId}?${params.toString()}`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload modified document / 上传修改后的文档失败');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate]);

  // Navigate to next step
  // 导航到下一步
  const goToNextStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer1-step5-2/${documentId}?${params.toString()}`);
  };

  // Navigate to previous step
  // 导航到上一步
  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer1-step5-0/${documentId}?${params.toString()}`);
  };

  // Toggle section expansion
  // 切换部分展开状态
  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const hasSelectedIssues = selectedIssueIndices.size > 0;

  // Render fingerprint list
  // 渲染指纹列表
  const renderFingerprintList = (
    matches: FingerprintMatch[] | undefined,
    type: 'A' | 'B' | 'C',
    sectionKey: string
  ) => {
    if (!matches || matches.length === 0) return null;

    const typeConfig = {
      A: { label: 'Type A: Dead Giveaways', labelZh: 'A类：明显标记词', color: 'red', icon: Zap },
      B: { label: 'Type B: Cliches', labelZh: 'B类：陈词滥调', color: 'orange', icon: Target },
      C: { label: 'Type C: Fillers', labelZh: 'C类：填充短语', color: 'yellow', icon: AlertTriangle },
    };

    const config = typeConfig[type];
    const IconComponent = config.icon;

    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div
          className="flex items-center justify-between cursor-pointer"
          onClick={() => toggleSection(sectionKey)}
        >
          <h3 className={clsx(
            'text-lg font-semibold flex items-center gap-2',
            `text-${config.color}-700`
          )}>
            <IconComponent className={`w-5 h-5 text-${config.color}-600`} />
            {config.label} ({matches.length})
            <span className="text-sm font-normal text-gray-500 ml-2">
              {config.labelZh}
            </span>
          </h3>
          {expandedSection === sectionKey ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>

        {expandedSection === sectionKey && (
          <div className="mt-4 space-y-2">
            {matches.map((match, index) => (
              <div
                key={index}
                className={clsx(
                  'p-3 rounded-lg border',
                  `bg-${config.color}-50 border-${config.color}-200`
                )}
              >
                <div className="flex items-center justify-between">
                  <span className={`font-medium text-${config.color}-700`}>
                    "{match.word || match.phrase}"
                  </span>
                  <span className={`text-sm text-${config.color}-600`}>
                    {match.count} occurrence(s)
                  </span>
                </div>
                {match.positions && match.positions.length > 0 && (
                  <div className="mt-2 text-xs text-gray-500">
                    Positions: {match.positions.slice(0, 5).join(', ')}
                    {match.positions.length > 5 && ` ... (+${match.positions.length - 5} more)`}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Render loading state
  // 渲染加载状态
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage message="Loading document... / 加载文档中..." />
      </div>
    );
  }

  // Render error state
  // 渲染错误状态
  if (error && !result) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center gap-2 text-red-700">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
        <Button onClick={runAnalysis} className="mt-4" variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry / 重试
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Loading Overlay */}
      <LoadingOverlay
        isVisible={isMerging}
        operationType={mergeMode}
        issueCount={selectedIssueIndices.size}
      />

      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <Fingerprint className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 5.1: AI Fingerprint Detection
              </h2>
              <p className="text-sm text-gray-500">
                步骤 5.1: AI指纹检测
              </p>
            </div>
          </div>
          {isAnalyzing && (
            <div className="flex items-center gap-2 text-red-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing... / 分析中...</span>
            </div>
          )}
        </div>

        <p className="text-gray-600 mb-4">
          Detects AI-typical words and phrases that are strong indicators of AI-generated content.
          <br />
          <span className="text-gray-500">
            检测AI典型词汇和短语，这些是AI生成内容的强指标。
          </span>
        </p>

        {/* Summary Stats */}
        {result && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className="bg-red-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-red-600 mb-1">
                <Zap className="w-4 h-4" />
                <span className="text-sm font-medium">Type A</span>
              </div>
              <div className="text-2xl font-bold text-red-700">
                {result.typeAWords?.length || 0}
              </div>
              <div className="text-xs text-red-500">明显标记词</div>
            </div>

            <div className="bg-orange-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-orange-600 mb-1">
                <Target className="w-4 h-4" />
                <span className="text-sm font-medium">Type B</span>
              </div>
              <div className="text-2xl font-bold text-orange-700">
                {result.typeBWords?.length || 0}
              </div>
              <div className="text-xs text-orange-500">陈词滥调</div>
            </div>

            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-yellow-600 mb-1">
                <AlertTriangle className="w-4 h-4" />
                <span className="text-sm font-medium">Type C</span>
              </div>
              <div className="text-2xl font-bold text-yellow-700">
                {result.typeCPhrases?.length || 0}
              </div>
              <div className="text-xs text-yellow-500">填充短语</div>
            </div>

            <div className={clsx(
              'rounded-lg p-4',
              result.riskLevel === 'low' ? 'bg-green-50' :
              result.riskLevel === 'medium' ? 'bg-yellow-50' : 'bg-red-50'
            )}>
              <div className={clsx(
                'flex items-center gap-2 mb-1',
                result.riskLevel === 'low' ? 'text-green-600' :
                result.riskLevel === 'medium' ? 'text-yellow-600' : 'text-red-600'
              )}>
                {result.riskLevel === 'low' ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <AlertCircle className="w-4 h-4" />
                )}
                <span className="text-sm font-medium">Risk Level</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                result.riskLevel === 'low' ? 'text-green-700' :
                result.riskLevel === 'medium' ? 'text-yellow-700' : 'text-red-700'
              )}>
                {result.riskLevel?.toUpperCase() || 'N/A'}
              </div>
              <div className={clsx(
                'text-xs',
                result.riskLevel === 'low' ? 'text-green-500' :
                result.riskLevel === 'medium' ? 'text-yellow-500' : 'text-red-500'
              )}>风险等级</div>
            </div>
          </div>
        )}
      </div>

      {/* Fingerprint Lists */}
      {result && (
        <>
          {renderFingerprintList(result.typeAWords, 'A', 'typeA')}
          {renderFingerprintList(result.typeBWords, 'B', 'typeB')}
          {renderFingerprintList(result.typeCPhrases, 'C', 'typeC')}
        </>
      )}

      {/* Issues Section */}
      {fingerprintIssues.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              Issues to Address / 需要处理的问题
            </h3>
            {hasSelectedIssues && (
              <span className="text-sm text-red-600">
                {selectedIssueIndices.size} selected / 已选择
              </span>
            )}
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {fingerprintIssues.map((issue, idx) => (
              <button
                key={idx}
                onClick={() => handleIssueClick(idx)}
                className={clsx(
                  'w-full text-left p-3 rounded-lg border transition-all',
                  selectedIssueIndices.has(idx)
                    ? 'bg-red-50 border-red-300 ring-2 ring-red-200'
                    : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                )}
              >
                <div className="flex items-start gap-3">
                  <div className={clsx(
                    'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5',
                    selectedIssueIndices.has(idx)
                      ? 'bg-red-600 border-red-600'
                      : 'border-gray-300'
                  )}>
                    {selectedIssueIndices.has(idx) && (
                      <Check className="w-3 h-3 text-white" />
                    )}
                  </div>
                  <div className="flex-1">
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
                    </div>
                    <p className="text-gray-900 mt-1">{issue.description}</p>
                    <p className="text-gray-600 text-sm">{issue.descriptionZh}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {hasSelectedIssues && (
        <div className="mb-6 pb-6 border-b">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">{selectedIssueIndices.size} selected / 已选择 {selectedIssueIndices.size} 个问题</div>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={loadIssueSuggestion}
                disabled={isLoadingSuggestion || selectedIssueIndices.size === 0}
              >
                {isLoadingSuggestion ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4 mr-2" />
                )}
                Load Suggestions / 加载建议
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={selectedIssueIndices.size === 0}
                onClick={() => {
                  setMergeMode('prompt');
                  setShowMergeConfirm(true);
                }}
              >
                <Edit3 className="w-4 h-4 mr-2" />
                Generate Prompt / 生成提示
              </Button>
              <Button
                variant="primary"
                size="sm"
                disabled={selectedIssueIndices.size === 0}
                onClick={() => {
                  setMergeMode('apply');
                  setShowMergeConfirm(true);
                }}
              >
                <Sparkles className="w-4 h-4 mr-2" />
                AI Modify / AI修改
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Suggestion Error */}
      {suggestionError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-600">{suggestionError}</p>
            <Button
              variant="secondary"
              size="sm"
              className="mt-2"
              onClick={() => setSuggestionError(null)}
            >
              Dismiss
            </Button>
          </div>
        </div>
      )}

      {/* Issue Suggestion Display */}
      {issueSuggestion && (
        <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
          <h4 className="font-semibold text-purple-900 mb-3 flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            AI Suggestions / AI建议
          </h4>
          <div className="space-y-3">
            <div>
              <h5 className="text-sm font-medium text-purple-800">Analysis:</h5>
              <p className="text-purple-700 mt-1">{issueSuggestion.analysis}</p>
            </div>
            {issueSuggestion.suggestions?.length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-purple-800">Suggestions:</h5>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  {issueSuggestion.suggestions.map((s, i) => (
                    <li key={i} className="text-purple-700">{s}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Merge Confirm Dialog */}
      {showMergeConfirm && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h4 className="font-semibold text-yellow-900 mb-3">
            {mergeMode === 'prompt' ? 'Generate Modification Prompt' : 'Apply AI Modification'}
          </h4>
          <div className="mb-3">
            <textarea
              value={mergeUserNotes}
              onChange={(e) => setMergeUserNotes(e.target.value)}
              placeholder="Add any specific instructions..."
              className="w-full px-3 py-2 border border-yellow-300 rounded-lg"
              rows={2}
            />
          </div>
          <div className="flex gap-2">
            <Button variant="primary" size="sm" onClick={executeMergeModify} disabled={isMerging}>
              {isMerging ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Check className="w-4 h-4 mr-2" />}
              Confirm
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setShowMergeConfirm(false)}>
              <X className="w-4 h-4 mr-2" />
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Merge Result Display */}
      {mergeResult && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <h4 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            {'modifiedText' in mergeResult ? 'AI Modification Result' : 'Generated Prompt'}
          </h4>
          {'prompt' in mergeResult && (
            <pre className="p-3 bg-white rounded text-sm text-gray-800 overflow-x-auto whitespace-pre-wrap">
              {mergeResult.prompt}
            </pre>
          )}
          {'modifiedText' in mergeResult && (
            <>
              <pre className="p-3 bg-white rounded text-sm text-gray-800 overflow-x-auto whitespace-pre-wrap max-h-96 overflow-y-auto">
                {mergeResult.modifiedText}
              </pre>
              <div className="flex gap-2 mt-4">
                <Button variant="primary" size="sm" onClick={handleAcceptModification}>
                  <Check className="w-4 h-4 mr-2" />
                  Accept
                </Button>
                <Button variant="secondary" size="sm" onClick={handleRegenerate}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Regenerate
                </Button>
                <Button variant="secondary" size="sm" onClick={() => setMergeResult(null)}>
                  <X className="w-4 h-4 mr-2" />
                  Cancel
                </Button>
              </div>
            </>
          )}
        </div>
      )}

      {/* No issues message */}
      {fingerprintIssues.length === 0 && result && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-green-800">No AI Fingerprints Detected</h3>
            <p className="text-green-600 mt-1">未检测到AI指纹。文档看起来很自然。</p>
          </div>
        </div>
      )}

      {/* Document Modification Section */}
      {result && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Document Modification / 文档修改
          </h3>
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setModifyMode('file')}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                modifyMode === 'file' ? 'bg-red-600 text-white' : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              )}
            >
              <Upload className="w-4 h-4 inline mr-2" />
              Upload File
            </button>
            <button
              onClick={() => setModifyMode('text')}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                modifyMode === 'text' ? 'bg-red-600 text-white' : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              )}
            >
              <Edit3 className="w-4 h-4 inline mr-2" />
              Input Text
            </button>
          </div>

          {modifyMode === 'file' && (
            <div>
              <input ref={fileInputRef} type="file" accept=".txt,.md,.doc,.docx" onChange={handleFileSelect} className="hidden" />
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-red-400 hover:bg-red-50 transition-colors"
              >
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600">{newFile ? newFile.name : 'Click to select file'}</p>
              </div>
            </div>
          )}

          {modifyMode === 'text' && (
            <div>
              <textarea
                value={newText}
                onChange={(e) => setNewText(e.target.value)}
                placeholder="Paste modified text here..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg min-h-[200px]"
              />
              <p className="text-gray-500 text-sm mt-1">{newText.length} characters</p>
            </div>
          )}

          <div className="mt-4 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              {modifyMode === 'file'
                ? (newFile ? 'File selected, ready to apply / 文件已选择，可以应用' : 'Please select a file first / 请先选择文件')
                : (newText.trim() ? 'Content entered, ready to apply / 内容已输入，可以应用' : 'Please enter content first / 请先输入内容')}
            </p>
            <Button
              variant="primary"
              onClick={handleConfirmModify}
              disabled={isUploading || (modifyMode === 'file' && !newFile) || (modifyMode === 'text' && !newText.trim())}
            >
              {isUploading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <ArrowRight className="w-4 h-4 mr-2" />}
              Apply and Continue / 应用并继续
            </Button>
          </div>

          {error && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}
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
          <Button variant="outline" onClick={goToPreviousStep} className="flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Previous: Step 5.0
          </Button>
          <Button onClick={() => setShowSkipConfirm(true)} disabled={!result} className="flex items-center gap-2">
            Skip and Continue / 跳过并继续
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
