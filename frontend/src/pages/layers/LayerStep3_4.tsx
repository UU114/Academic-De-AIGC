import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  Ruler,
  FileText,
  RefreshCw,
  BarChart3,
  TrendingUp,
  AlertTriangle,
  Edit3,
  Sparkles,
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
  paragraphLayerApi,
  documentLayerApi,
  ParagraphAnalysisResponse,
  DetectionIssue,
  IssueSeverity,
} from '../../services/analysisApi';

/**
 * Layer Step 3.4 - Sentence Length Distribution Analysis
 * 步骤 3.4 - 句子长度分布分析
 *
 * Analyzes sentence length variation within paragraphs:
 * - Calculates CV (Coefficient of Variation)
 * - Flags low variation (CV < 0.25) as AI-like uniformity
 * - Visualizes sentence length patterns
 *
 * 分析段落内句子长度变化：
 * - 计算变异系数(CV)
 * - 标记低变异(CV < 0.25)为AI式均匀
 * - 可视化句子长度模式
 */

// Response types for merge modify operations
// 合并修改操作的响应类型
interface ModifyPromptResponse {
  prompt: string;
  promptZh: string;
  issuesSummaryZh: string;
  colloquialismLevel: number;
  estimatedChanges: number;
}

interface ApplyModifyResponse {
  modifiedText: string;
  changesSummaryZh: string;
  changesCount: number;
  remainingAttempts: number;
  colloquialismLevel: number;
}

// Issue suggestion response type
// 问题建议响应类型
interface IssueSuggestionResponse {
  analysis: string;
  suggestions: string[];
  exampleFix?: string;
}

interface LayerStep3_4Props {
  documentIdProp?: string;
  onComplete?: (result: ParagraphAnalysisResponse) => void;
  showNavigation?: boolean;
  sectionContext?: Record<string, unknown>;
}

export default function LayerStep3_4({
  documentIdProp,
  onComplete,
  showNavigation = true,
  sectionContext,
}: LayerStep3_4Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // Helper function to check if documentId is valid
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

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer3-step3-4').catch(console.error);
    }
  }, [sessionId]);

  // Basic state
  // 基本状态
  const [result, setResult] = useState<ParagraphAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');

  // Issues derived from analysis result
  // 从分析结果派生的问题列表
  const [lengthIssues, setLengthIssues] = useState<DetectionIssue[]>([]);

  // Issue selection for merge modify
  // 用于合并修改的问题选择
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());

  // Issue suggestion state (LLM-based detailed suggestions)
  // 问题建议状态（基于LLM的详细建议）
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
      setError('Document ID not found. Please start from the document upload page. / 未找到文档ID，请从文档上传页面开始。');
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
      const analysisResult = await paragraphLayerApi.analyzeSentenceLength(documentText, sectionContext);
      setResult(analysisResult);

      // Create issues from analysis result
      // 从分析结果创建问题列表
      const issues: DetectionIssue[] = [];

      // Check for low CV paragraphs (AI-like uniformity)
      // 检查低CV段落（AI式均匀）
      if (analysisResult.paragraphDetails) {
        analysisResult.paragraphDetails.forEach((para, index) => {
          const cv = para.sentenceLengthCv || 0;

          if (cv < 0.2) {
            issues.push({
              type: 'very_low_cv',
              description: `Paragraph ${index + 1} has very low sentence length variation (CV=${cv.toFixed(3)}) - highly uniform AI pattern`,
              descriptionZh: `段落${index + 1}句子长度变异极低 (CV=${cv.toFixed(3)}) - 高度均匀的AI模式`,
              severity: 'high' as IssueSeverity,
              layer: 'paragraph',
              location: `Paragraph ${index + 1}`,
            });
          } else if (cv < 0.25) {
            issues.push({
              type: 'low_cv',
              description: `Paragraph ${index + 1} has low sentence length variation (CV=${cv.toFixed(3)}) - AI-like uniformity`,
              descriptionZh: `段落${index + 1}句子长度变异较低 (CV=${cv.toFixed(3)}) - AI式均匀`,
              severity: 'medium' as IssueSeverity,
              layer: 'paragraph',
              location: `Paragraph ${index + 1}`,
            });
          }
        });
      }

      // Check overall sentence length CV
      // 检查整体句长CV
      // Get from details (backend returns in details.sentenceLengthAnalysis)
      // 从 details 获取（后端返回在 details.sentenceLengthAnalysis 中）
      const sentenceLengthAnalysis = (analysisResult.details as Record<string, unknown>)?.sentenceLengthAnalysis as { meanCv?: number } | undefined;
      const overallCv = sentenceLengthAnalysis?.meanCv;
      if (overallCv !== undefined && overallCv < 0.25) {
        issues.push({
          type: 'overall_low_cv',
          description: `Overall sentence length variation is low (mean CV=${overallCv.toFixed(3)})`,
          descriptionZh: `整体句子长度变异较低 (平均CV=${overallCv.toFixed(3)})`,
          severity: overallCv < 0.2 ? 'high' as IssueSeverity : 'medium' as IssueSeverity,
          layer: 'paragraph',
          location: 'Document-wide',
        });
      }

      setLengthIssues(issues);

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

  // Load detailed suggestion for selected issues (LLM-based)
  // 为选中的问题加载详细建议（基于LLM）
  const loadIssueSuggestion = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentId) return;

    setIsLoadingSuggestion(true);
    setSuggestionError(null);

    try {
      const selectedIssues = Array.from(selectedIssueIndices).map(i => lengthIssues[i]);
      // Use the first issue for suggestion (API expects single issue)
      const firstIssue = selectedIssues[0];
      const response = await documentLayerApi.getIssueSuggestion(
        documentId,
        firstIssue,
        false
      );
      // Transform response to match our interface
      setIssueSuggestion({
        analysis: response.diagnosisZh || '',
        suggestions: response.priorityTipsZh || [],
        exampleFix: response.strategies?.[0]?.exampleAfter || '',
      });
    } catch (err) {
      console.error('Failed to load suggestion:', err);
      setSuggestionError('Failed to load detailed suggestion / 加载详细建议失败');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [selectedIssueIndices, documentId, lengthIssues]);

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

  // Execute merge modify (generate prompt or apply modification)
  // 执行合并修改（生成提示或应用修改）
  const executeMergeModify = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentId) return;

    setIsMerging(true);
    setShowMergeConfirm(false);

    try {
      const selectedIssues = Array.from(selectedIssueIndices).map(i => lengthIssues[i]);

      if (mergeMode === 'prompt') {
        const response = await documentLayerApi.generateModifyPrompt(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult(response);
      } else {
        const response = await documentLayerApi.applyModify(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult(response);
      }
    } catch (err) {
      console.error('Merge modify failed:', err);
      setError('Merge modify failed / 合并修改失败');
    } finally {
      setIsMerging(false);
    }
  }, [selectedIssueIndices, documentId, lengthIssues, mergeMode, mergeUserNotes, sessionId]);

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

  // Handle confirm modification and navigate to next step
  // 处理确认修改并导航到下一步
  const handleConfirmModify = useCallback(async () => {
    setIsUploading(true);
    setError(null);

    try {
      let newDocId: string;

      if (modifyMode === 'file' && newFile) {
        const result = await documentApi.upload(newFile);
        newDocId = result.documentId;
      } else if (modifyMode === 'text' && newText.trim()) {
        const result = await documentApi.uploadText(newText, `step3_4_modified_${Date.now()}.txt`);
        newDocId = result.documentId;
      } else {
        setError('Please select a file or enter text / 请选择文件或输入文本');
        setIsUploading(false);
        return;
      }

      // Navigate to next step with new document
      // 使用新文档导航到下一步
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer3-step3-5/${newDocId}?${params.toString()}`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload modified document / 上传修改后的文档失败');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate]);

  // Navigation handlers
  // 导航处理
  const goToNextStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-5/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-3/${documentId}?${params.toString()}`);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // Get CV risk level based on threshold
  // CV < 0.25 is high risk (AI-like uniformity)
  const getCvRiskLevel = (cv: number): string => {
    if (cv >= 0.35) return 'low';
    if (cv >= 0.25) return 'medium';
    return 'high';
  };

  const getCvColor = (cv: number) => {
    const level = getCvRiskLevel(cv);
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // Render sentence length bar visualization
  // 渲染句子长度条形可视化
  const renderLengthBar = (length: number, maxLength: number) => {
    const percentage = Math.min((length / maxLength) * 100, 100);
    return (
      <div className="flex items-center gap-2">
        <div className="flex-1 h-4 bg-gray-100 rounded overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className="text-xs text-gray-500 w-12 text-right">{length} words</span>
      </div>
    );
  };

  const hasSelectedIssues = selectedIssueIndices.size > 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage message="Loading document... / 加载文档中..." />
      </div>
    );
  }

  if (error && !result) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center gap-2 text-red-700">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
        <Button onClick={() => { setError(null); isAnalyzingRef.current = false; runAnalysis(); }} className="mt-4" variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry / 重试
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Loading Overlay for LLM operations */}
      {/* LLM操作加载遮罩 */}
      <LoadingOverlay
        isVisible={isMerging}
        operationType={mergeMode}
        issueCount={selectedIssueIndices.size}
      />

      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <Ruler className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3.4: Sentence Length Distribution
              </h2>
              <p className="text-sm text-gray-500">
                步骤 3.4: 句子长度分布分析
              </p>
            </div>
          </div>
          {isAnalyzing && (
            <div className="flex items-center gap-2 text-indigo-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing... / 分析中...</span>
            </div>
          )}
        </div>

        <p className="text-gray-600 mb-4">
          Analyzes sentence length variation within each paragraph. Low variation (CV &lt; 0.25) indicates AI-generated uniform sentence patterns.
          <br />
          <span className="text-gray-500">
            分析每个段落内句子长度变化。低变异（CV &lt; 0.25）表示AI生成的均匀句式模式。
          </span>
        </p>

        {/* Overall Metrics */}
        {result && (() => {
          // Get sentenceLengthAnalysis from details (backend returns in details.sentenceLengthAnalysis)
          // 从 details 获取句长分析数据
          const slAnalysis = (result.details as Record<string, unknown>)?.sentenceLengthAnalysis as { meanCv?: number } | undefined;
          const meanCv = slAnalysis?.meanCv || 0;
          return (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className={clsx('rounded-lg p-4', getRiskColor(result.riskLevel))}>
              <div className="text-2xl font-bold">{result.riskScore}/100</div>
              <div className="text-sm">Risk Score / 风险分数</div>
            </div>
            <div className={clsx('rounded-lg p-4', getCvColor(meanCv))}>
              <div className="text-2xl font-bold">
                {meanCv.toFixed(3)}
              </div>
              <div className="text-sm">Overall CV / 总体变异系数</div>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-700">
                {result.paragraphCount || 0}
              </div>
              <div className="text-sm text-blue-600">Paragraphs / 段落数</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-red-700">
                {result.paragraphDetails?.filter(p => (p.sentenceLengthCv || 0) < 0.25).length || 0}
              </div>
              <div className="text-sm text-red-600">Low CV Paras / 低CV段落</div>
            </div>
          </div>
          );
        })()}

        {/* CV Scale Legend */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">CV Scale / 变异系数等级:</h4>
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-green-500"></div>
              <span className="text-sm">&gt;=0.35 (Natural / 自然)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-yellow-500"></div>
              <span className="text-sm">0.25-0.35 (Moderate / 中等)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-red-500"></div>
              <span className="text-sm">&lt;0.25 (AI-like Uniform / AI式均匀)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Issues Section with Selection */}
      {/* 问题部分（带选择功能） */}
      {lengthIssues.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              Detected Issues / 检测到的问题
              <span className="text-sm font-normal text-gray-500">
                (Click to select / 点击选择)
              </span>
            </h3>
            {hasSelectedIssues && (
              <span className="text-sm text-blue-600">
                {selectedIssueIndices.size} selected / 已选择
              </span>
            )}
          </div>
          <div className="space-y-2">
            {lengthIssues.map((issue, idx) => (
              <button
                key={idx}
                onClick={() => handleIssueClick(idx)}
                className={clsx(
                  'w-full text-left p-3 rounded-lg border transition-all',
                  selectedIssueIndices.has(idx)
                    ? 'bg-blue-50 border-blue-300 ring-2 ring-blue-200'
                    : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                )}
              >
                <div className="flex items-start gap-3">
                  <div className={clsx(
                    'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5',
                    selectedIssueIndices.has(idx)
                      ? 'bg-blue-600 border-blue-600'
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
                      <span className="text-xs text-gray-500">{issue.layer}</span>
                    </div>
                    <p className="text-gray-900 mt-1">{issue.description}</p>
                    <p className="text-gray-600 text-sm">{issue.descriptionZh}</p>
                    {issue.location && (
                      <p className="text-gray-500 text-xs mt-1 font-mono">{issue.location}</p>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons for Selected Issues */}
      {/* 选中问题的操作按钮 */}
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
                onClick={() => {
                  setMergeMode('prompt');
                  setShowMergeConfirm(true);
                }}
                disabled={selectedIssueIndices.size === 0}
              >
                <Edit3 className="w-4 h-4 mr-2" />
                Generate Prompt / 生成提示
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  setMergeMode('apply');
                  setShowMergeConfirm(true);
                }}
                disabled={selectedIssueIndices.size === 0}
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
              Dismiss / 关闭
            </Button>
          </div>
        </div>
      )}

      {/* Issue Suggestion Display (LLM-based) */}
      {/* 问题建议展示（基于LLM） */}
      {issueSuggestion && (
        <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
          <h4 className="font-semibold text-purple-900 mb-3 flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            AI Suggestions / AI建议
          </h4>
          <div className="space-y-3">
            <div>
              <h5 className="text-sm font-medium text-purple-800">Analysis / 分析:</h5>
              <p className="text-purple-700 mt-1">{issueSuggestion.analysis}</p>
            </div>
            {issueSuggestion.suggestions && issueSuggestion.suggestions.length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-purple-800">Suggestions / 建议:</h5>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  {issueSuggestion.suggestions.map((s, i) => (
                    <li key={i} className="text-purple-700">{s}</li>
                  ))}
                </ul>
              </div>
            )}
            {issueSuggestion.exampleFix && (
              <div>
                <h5 className="text-sm font-medium text-purple-800">Example Fix / 示例修复:</h5>
                <pre className="mt-1 p-2 bg-white rounded text-sm text-gray-800 overflow-x-auto">
                  {issueSuggestion.exampleFix}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Merge Confirm Dialog */}
      {/* 合并确认对话框 */}
      {showMergeConfirm && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h4 className="font-semibold text-yellow-900 mb-3">
            {mergeMode === 'prompt' ? 'Generate Modification Prompt / 生成修改提示' : 'Apply AI Modification / 应用AI修改'}
          </h4>
          <p className="text-yellow-800 text-sm mb-3">
            {mergeMode === 'prompt'
              ? 'Generate a prompt that you can use to modify the document manually / 生成一个提示，您可以用它来手动修改文档'
              : 'AI will automatically modify the document based on selected issues / AI将根据选中的问题自动修改文档'}
          </p>
          <div className="mb-3">
            <label className="block text-sm font-medium text-yellow-800 mb-1">
              Additional Notes (Optional) / 附加说明（可选）
            </label>
            <textarea
              value={mergeUserNotes}
              onChange={(e) => setMergeUserNotes(e.target.value)}
              placeholder="Add any specific instructions for modification... / 添加任何特定的修改指示..."
              className="w-full px-3 py-2 border border-yellow-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500"
              rows={2}
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant="primary"
              size="sm"
              onClick={executeMergeModify}
              disabled={isMerging}
            >
              {isMerging ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Check className="w-4 h-4 mr-2" />
              )}
              Confirm / 确认
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowMergeConfirm(false)}
            >
              <X className="w-4 h-4 mr-2" />
              Cancel / 取消
            </Button>
          </div>
        </div>
      )}

      {/* Merge Result Display */}
      {/* 合并结果展示 */}
      {mergeResult && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <h4 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            {'modifiedText' in mergeResult ? 'AI Modification Result / AI修改结果' : 'Generated Prompt / 生成的提示'}
          </h4>

          {'prompt' in mergeResult && mergeResult.prompt && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-green-800">Prompt / 提示:</h5>
              <pre className="mt-1 p-3 bg-white rounded text-sm text-gray-800 overflow-x-auto whitespace-pre-wrap">
                {mergeResult.prompt}
              </pre>
            </div>
          )}

          {'modifiedText' in mergeResult && mergeResult.modifiedText && (
            <div className="mb-3">
              {/* Modified text display - full content with scrollable area */}
              {/* 修改后内容显示 - 完整内容可滚动 */}
              <h5 className="text-sm font-medium text-green-800">
                Modified Text / 修改后的文本 ({mergeResult.modifiedText?.length || 0} 字符):
              </h5>
              <pre className="mt-1 p-3 bg-white rounded text-sm text-gray-800 overflow-x-auto whitespace-pre-wrap max-h-96 overflow-y-auto">
                {mergeResult.modifiedText}
              </pre>
            </div>
          )}

          {'changesSummaryZh' in mergeResult && mergeResult.changesSummaryZh && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-green-800">Changes Summary / 修改摘要:</h5>
              <p className="mt-1 text-green-700">{mergeResult.changesSummaryZh}</p>
            </div>
          )}

          {'modifiedText' in mergeResult && (
            <div className="flex gap-2 mt-4">
              <Button variant="primary" size="sm" onClick={handleAcceptModification}>
                <Check className="w-4 h-4 mr-2" />
                Accept / 接受
              </Button>
              <Button variant="secondary" size="sm" onClick={handleRegenerate}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Regenerate / 重新生成
              </Button>
              <Button variant="secondary" size="sm" onClick={() => setMergeResult(null)}>
                <X className="w-4 h-4 mr-2" />
                Cancel / 取消
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Paragraph Length Distribution Details */}
      {result && result.paragraphDetails && result.paragraphDetails.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            Paragraph Sentence Length Analysis / 段落句长分析
          </h3>

          <div className="space-y-4">
            {result.paragraphDetails.map((para, index) => {
              const cv = para.sentenceLengthCv || 0;
              const riskLevel = getCvRiskLevel(cv);
              // Note: sentenceLengths might not be available in the response
              // We'll show CV info only
              const sentenceLengths: number[] = [];
              const maxLength = sentenceLengths.length > 0 ? Math.max(...sentenceLengths, 1) : 1;

              return (
                <div
                  key={index}
                  className={clsx(
                    'border rounded-lg p-4',
                    riskLevel === 'high' ? 'border-red-300 bg-red-50' :
                    riskLevel === 'medium' ? 'border-yellow-300 bg-yellow-50' :
                    'border-green-300 bg-green-50'
                  )}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className={clsx(
                        'w-8 h-8 flex items-center justify-center rounded-full font-medium',
                        riskLevel === 'high' ? 'bg-red-200 text-red-700' :
                        riskLevel === 'medium' ? 'bg-yellow-200 text-yellow-700' :
                        'bg-green-200 text-green-700'
                      )}>
                        {index + 1}
                      </span>
                      <div>
                        <span className="font-medium text-gray-700">Paragraph {index + 1}</span>
                        <span className="text-sm text-gray-500 ml-2">
                          ({para.role || 'body'})
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className={clsx(
                        'px-3 py-1 rounded-full text-sm font-medium',
                        getCvColor(cv)
                      )}>
                        <TrendingUp className="w-3 h-3 inline mr-1" />
                        CV: {cv.toFixed(3)}
                      </div>
                      {riskLevel === 'high' && (
                        <div className="flex items-center gap-1 text-red-600">
                          <AlertTriangle className="w-4 h-4" />
                          <span className="text-sm font-medium">Uniform Pattern</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Sentence Length Bars (if available) */}
                  {sentenceLengths.length > 0 && (
                    <div className="space-y-1 mt-3">
                      <div className="text-xs text-gray-500 mb-2">
                        Sentence lengths (words):
                      </div>
                      {sentenceLengths.map((length, sIndex) => (
                        <div key={sIndex} className="flex items-center gap-2">
                          <span className="text-xs text-gray-400 w-6">S{sIndex + 1}</span>
                          {renderLengthBar(length, maxLength)}
                        </div>
                      ))}
                    </div>
                  )}

                  {riskLevel === 'high' && (
                    <div className="mt-3 p-2 bg-white rounded border border-red-200 text-sm text-red-700">
                      <strong>Warning:</strong> This paragraph has uniform sentence lengths, a common AI pattern. Consider varying sentence structure.
                      <br />
                      <span className="text-red-600">警告：此段落句子长度过于均匀，这是常见的AI模式。建议变化句式结构。</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* CV Explanation */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          Understanding CV / 理解变异系数
        </h3>
        <div className="prose prose-sm text-gray-600">
          <p>
            <strong>Coefficient of Variation (CV)</strong> measures how spread out sentence lengths are within a paragraph.
            <br />
            <span className="text-gray-500">
              <strong>变异系数(CV)</strong>衡量段落内句子长度的分散程度。
            </span>
          </p>
          <ul className="mt-2 space-y-1">
            <li>CV = Standard Deviation / Mean</li>
            <li>Higher CV - More varied sentence lengths - More natural</li>
            <li>Lower CV - More uniform sentence lengths - More AI-like</li>
          </ul>
          <p className="mt-2">
            Human writers naturally vary sentence length based on content and rhythm. AI tends to produce more uniform sentence lengths.
            <br />
            <span className="text-gray-500">
              人类作者自然地根据内容和节奏变化句子长度。AI倾向于产生更均匀的句子长度。
            </span>
          </p>
        </div>
      </div>

      {/* No issues message - only show "Looks Good" if risk is actually low */}
      {/* 仅当风险实际较低时显示"良好"消息 */}
      {lengthIssues.length === 0 && result && (() => {
        const slAnalysis = (result.details as Record<string, unknown>)?.sentenceLengthAnalysis as { meanCv?: number } | undefined;
        const meanCv = slAnalysis?.meanCv || 0;
        const isActuallyGood = (result.riskLevel === 'low' || result.riskLevel === 'safe') && meanCv >= 0.25;

        if (isActuallyGood) {
          return (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">
                  Sentence Length Variation Looks Good
                </h3>
                <p className="text-green-600 mt-1">
                  句子长度变异良好。段落内句子长度呈现自然的变化模式。
                </p>
              </div>
            </div>
          );
        } else {
          // High risk but no detailed issues - show warning
          // 高风险但无详细问题 - 显示警告
          return (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-yellow-800">
                  Sentence Length Uniformity Detected
                </h3>
                <p className="text-yellow-700 mt-1">
                  检测到句子长度均匀性风险。整体变异系数 (CV={meanCv.toFixed(3)}) 偏低，
                  表明文本可能具有AI生成的均匀句式特征。建议增加句子长度的变化。
                </p>
              </div>
            </div>
          );
        }
      })()}

      {/* Document Modification Section */}
      {/* 文档修改部分 */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Document Modification / 文档修改
        </h3>
        <p className="text-gray-600 text-sm mb-4">
          Upload a modified file or paste modified text to continue to the next step.
          上传修改后的文件或粘贴修改后的文本以继续下一步。
        </p>

        {/* Mode Toggle */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setModifyMode('file')}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              modifyMode === 'file'
                ? 'bg-blue-600 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            )}
          >
            <Upload className="w-4 h-4 inline mr-2" />
            Upload File / 上传文件
          </button>
          <button
            onClick={() => setModifyMode('text')}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              modifyMode === 'text'
                ? 'bg-blue-600 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            )}
          >
            <Edit3 className="w-4 h-4 inline mr-2" />
            Input Text / 输入文本
          </button>
        </div>

        {/* File Upload Mode */}
        {modifyMode === 'file' && (
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md,.doc,.docx"
              onChange={handleFileSelect}
              className="hidden"
            />
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
            >
              <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">
                {newFile ? newFile.name : 'Click to select file / 点击选择文件'}
              </p>
              <p className="text-gray-400 text-sm mt-1">
                Supported: .txt, .md, .doc, .docx
              </p>
            </div>
          </div>
        )}

        {/* Text Input Mode */}
        {modifyMode === 'text' && (
          <div>
            <textarea
              value={newText}
              onChange={(e) => setNewText(e.target.value)}
              placeholder="Paste modified text here... / 在此粘贴修改后的文本..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-[200px]"
            />
            <p className="text-gray-500 text-sm mt-1">
              {newText.length} characters / 字符
            </p>
          </div>
        )}

        {/* Apply and Continue Button */}
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
            {isUploading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <ArrowRight className="w-4 h-4 mr-2" />
            )}
            Apply and Continue / 应用并继续
          </Button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        )}
      </div>

      {/* Recommendations */}
      {result && result.recommendations && result.recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            Recommendations / 建议
          </h3>
          <ul className="space-y-2">
            {result.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-green-500 mt-1">-</span>
                <div>
                  <p className="text-gray-700">{rec}</p>
                  {result.recommendationsZh && result.recommendationsZh[index] && (
                    <p className="text-gray-500 text-sm">{result.recommendationsZh[index]}</p>
                  )}
                </div>
              </li>
            ))}
          </ul>
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
            Previous: Step 3.3
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
