import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  Link2,
  FileText,
  RefreshCw,
  ArrowRightLeft,
  AlertTriangle,
  Edit3,
  Sparkles,
  Upload,
  Check,
  X,
  GitMerge,
  Link,
  Repeat,
  ArrowDown,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import {
  paragraphLayerApi,
  documentLayerApi,
  ParagraphTransitionResponse,
  ParagraphTransitionInfo,
  DetectionIssue,
  IssueSeverity,
} from '../../services/analysisApi';

/**
 * Layer Step 3.5 - Paragraph Transition Analysis
 * 步骤 3.5 - 段落过渡分析
 *
 * Analyzes transitions between paragraphs:
 * - Detects explicit connectors at paragraph openings
 * - Calculates semantic echo scores
 * - Identifies formulaic opener patterns
 * - Flags abrupt or overly smooth transitions
 *
 * 分析段落间过渡：
 * - 检测段落开头的显性连接词
 * - 计算语义回声分数
 * - 识别程式化开头模式
 * - 标记突兀或过于平滑的过渡
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

interface LayerStep3_5Props {
  documentIdProp?: string;
  onComplete?: (result: ParagraphTransitionResponse) => void;
  showNavigation?: boolean;
  sectionContext?: Record<string, unknown>;
}

export default function LayerStep3_5({
  documentIdProp,
  onComplete,
  showNavigation = true,
  sectionContext,
}: LayerStep3_5Props) {
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
      sessionApi.updateStep(sessionId, 'layer3-step3-5').catch(console.error);
    }
  }, [sessionId]);

  // Basic state
  // 基本状态
  const [result, setResult] = useState<ParagraphTransitionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');

  // Issues derived from analysis result
  // 从分析结果派生的问题列表
  const [transitionIssues, setTransitionIssues] = useState<DetectionIssue[]>([]);

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
      const analysisResult = await paragraphLayerApi.analyzeTransitions(
        documentText,
        undefined,
        sessionId || undefined,
        sectionContext
      );
      setResult(analysisResult);

      // Create issues from analysis result
      // 从分析结果创建问题列表
      const issues: DetectionIssue[] = [];

      // Check each transition for problems
      // 检查每个过渡的问题
      if (analysisResult.transitions) {
        analysisResult.transitions.forEach((trans: ParagraphTransitionInfo, index: number) => {
          // Formulaic opener pattern
          if (trans.isFormulaicOpener) {
            issues.push({
              type: 'formulaic_opener',
              description: `Transition ${trans.fromParagraph + 1} -> ${trans.toParagraph + 1} uses formulaic opener pattern`,
              descriptionZh: `过渡 ${trans.fromParagraph + 1} -> ${trans.toParagraph + 1} 使用程式化开头模式`,
              severity: 'medium' as IssueSeverity,
              layer: 'paragraph',
              position: { transition: index, pattern: trans.openerPattern },
              location: `Transition ${trans.fromParagraph + 1} -> ${trans.toParagraph + 1}`,
            });
          }

          // Abrupt transition (low semantic echo)
          if (trans.transitionQuality === 'abrupt') {
            issues.push({
              type: 'abrupt_transition',
              description: `Transition ${trans.fromParagraph + 1} -> ${trans.toParagraph + 1} is abrupt (semantic echo: ${trans.semanticEchoScore.toFixed(2)})`,
              descriptionZh: `过渡 ${trans.fromParagraph + 1} -> ${trans.toParagraph + 1} 突兀 (语义回声: ${trans.semanticEchoScore.toFixed(2)})`,
              severity: 'high' as IssueSeverity,
              layer: 'paragraph',
              position: { transition: index },
              location: `Transition ${trans.fromParagraph + 1} -> ${trans.toParagraph + 1}`,
            });
          }

          // High risk transition
          if (trans.riskScore >= 70) {
            issues.push({
              type: 'high_risk_transition',
              description: `Transition ${trans.fromParagraph + 1} -> ${trans.toParagraph + 1} has high risk score (${trans.riskScore})`,
              descriptionZh: `过渡 ${trans.fromParagraph + 1} -> ${trans.toParagraph + 1} 风险分数高 (${trans.riskScore})`,
              severity: 'high' as IssueSeverity,
              layer: 'paragraph',
              position: { transition: index },
              location: `Transition ${trans.fromParagraph + 1} -> ${trans.toParagraph + 1}`,
            });
          }
        });
      }

      // Check overall transition metrics
      // 检查整体过渡指标
      if (analysisResult.formulaicOpenerCount > 2) {
        issues.push({
          type: 'too_many_formulaic_openers',
          description: `Document has ${analysisResult.formulaicOpenerCount} formulaic openers, which is a common AI pattern`,
          descriptionZh: `文档有 ${analysisResult.formulaicOpenerCount} 个程式化开头，这是常见的AI模式`,
          severity: 'medium' as IssueSeverity,
          layer: 'paragraph',
          location: 'Document-wide',
        });
      }

      if (analysisResult.explicitRatio > 0.8) {
        issues.push({
          type: 'high_explicit_connector_ratio',
          description: `Explicit connector ratio is too high (${(analysisResult.explicitRatio * 100).toFixed(1)}%) - AI tends to overuse connectors`,
          descriptionZh: `显性连接词比例过高 (${(analysisResult.explicitRatio * 100).toFixed(1)}%) - AI倾向于过度使用连接词`,
          severity: 'medium' as IssueSeverity,
          layer: 'paragraph',
          location: 'Document-wide',
        });
      }

      setTransitionIssues(issues);

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
      const selectedIssues = Array.from(selectedIssueIndices).map(i => transitionIssues[i]);
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
  }, [selectedIssueIndices, documentId, transitionIssues]);

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
      const selectedIssues = Array.from(selectedIssueIndices).map(i => transitionIssues[i]);

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
  }, [selectedIssueIndices, documentId, transitionIssues, mergeMode, mergeUserNotes, sessionId]);

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

  // Handle confirm modification and navigate to next step (Layer 2 Step 4.0)
  // 处理确认修改并导航到下一步（Layer 2 Step 4.0）
  const handleConfirmModify = useCallback(async () => {
    setIsUploading(true);
    setError(null);

    try {
      let newDocId: string;

      if (modifyMode === 'file' && newFile) {
        const result = await documentApi.upload(newFile);
        newDocId = result.documentId;
      } else if (modifyMode === 'text' && newText.trim()) {
        const result = await documentApi.uploadText(newText, `step3_5_modified_${Date.now()}.txt`);
        newDocId = result.documentId;
      } else {
        setError('Please select a file or enter text / 请选择文件或输入文本');
        setIsUploading(false);
        return;
      }

      // Navigate to Layer 2 Step 4.0 (Sentence Layer) with new document
      // 使用新文档导航到 Layer 2 Step 4.0（句子层）
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer2-step4-0/${newDocId}?${params.toString()}`);
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
    // Navigate to Layer 2 Step 4.0 (Sentence Layer)
    navigate(`/flow/layer2-step4-0/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-4/${documentId}?${params.toString()}`);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getTransitionQualityColor = (quality: string) => {
    switch (quality) {
      case 'smooth': return 'text-green-600 bg-green-100 border-green-300';
      case 'abrupt': return 'text-red-600 bg-red-100 border-red-300';
      case 'formulaic': return 'text-yellow-600 bg-yellow-100 border-yellow-300';
      default: return 'text-gray-600 bg-gray-100 border-gray-300';
    }
  };

  const getQualityLabel = (quality: string): { en: string; zh: string } => {
    switch (quality) {
      case 'smooth': return { en: 'Smooth', zh: '流畅' };
      case 'abrupt': return { en: 'Abrupt', zh: '突兀' };
      case 'formulaic': return { en: 'Formulaic', zh: '公式化' };
      default: return { en: 'Unknown', zh: '未知' };
    }
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
            <div className="p-2 bg-teal-100 rounded-lg">
              <GitMerge className="w-6 h-6 text-teal-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3.5: Paragraph Transition Analysis
              </h2>
              <p className="text-sm text-gray-500">
                步骤 3.5: 段落过渡分析
              </p>
            </div>
          </div>
          {isAnalyzing && (
            <div className="flex items-center gap-2 text-teal-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing... / 分析中...</span>
            </div>
          )}
        </div>

        <p className="text-gray-600 mb-4">
          Analyzes how paragraphs connect to each other. Detects formulaic transitions, abrupt topic shifts, and semantic echo patterns.
          <br />
          <span className="text-gray-500">
            分析段落之间的连接方式。检测公式化过渡、突兀的主题转换和语义回响模式。
          </span>
        </p>

        {/* Overall Metrics */}
        {result && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className={clsx('rounded-lg p-4', getRiskColor(result.riskLevel))}>
              <div className="text-2xl font-bold">{result.riskScore}/100</div>
              <div className="text-sm">Risk Score / 风险分数</div>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-700">
                {result.transitions?.length || 0}
              </div>
              <div className="text-sm text-blue-600">Transitions / 过渡数</div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-yellow-700">
                {result.transitions?.filter(t => t.isFormulaicOpener).length || 0}
              </div>
              <div className="text-sm text-yellow-600">Formulaic / 公式化</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-red-700">
                {result.transitions?.filter(t => t.transitionQuality === 'abrupt').length || 0}
              </div>
              <div className="text-sm text-red-600">Abrupt / 突兀</div>
            </div>
          </div>
        )}

        {/* Quality Legend */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Transition Quality / 过渡质量:</h4>
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-green-500"></div>
              <span className="text-sm">Smooth (Natural / 自然)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-yellow-500"></div>
              <span className="text-sm">Formulaic (AI pattern / AI模式)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-red-500"></div>
              <span className="text-sm">Abrupt (Topic shift / 主题跳跃)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Issues Section with Selection */}
      {/* 问题部分（带选择功能） */}
      {transitionIssues.length > 0 && (
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
            {transitionIssues.map((issue, idx) => (
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

      {/* Transition Details */}
      {result && result.transitions && result.transitions.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Link className="w-5 h-5 text-teal-600" />
            Paragraph Transitions / 段落过渡详情
          </h3>

          <div className="space-y-4">
            {result.transitions.map((transition: ParagraphTransitionInfo, index: number) => {
              const qualityLabel = getQualityLabel(transition.transitionQuality);
              return (
                <div
                  key={index}
                  className={clsx(
                    'border rounded-lg p-4',
                    getTransitionQualityColor(transition.transitionQuality)
                  )}
                >
                  {/* Transition Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-1">
                        <span className="w-7 h-7 flex items-center justify-center bg-gray-200 rounded-full text-sm font-medium">
                          {transition.fromParagraph + 1}
                        </span>
                        <ArrowDown className="w-4 h-4 text-gray-400" />
                        <span className="w-7 h-7 flex items-center justify-center bg-gray-200 rounded-full text-sm font-medium">
                          {transition.toParagraph + 1}
                        </span>
                      </div>
                      <span className="font-medium text-gray-700">
                        Para {transition.fromParagraph + 1} &rarr; Para {transition.toParagraph + 1}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className={clsx(
                        'px-3 py-1 rounded-full text-sm font-medium',
                        getTransitionQualityColor(transition.transitionQuality)
                      )}>
                        {qualityLabel.en} / {qualityLabel.zh}
                      </div>
                      {transition.isFormulaicOpener && (
                        <div className="flex items-center gap-1 text-yellow-600">
                          <AlertTriangle className="w-4 h-4" />
                          <span className="text-sm">Formulaic</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Opener Text */}
                  {transition.openerText && (
                    <div className="bg-white bg-opacity-50 rounded p-3 mb-3">
                      <div className="text-xs text-gray-500 mb-1">Opening text / 开头文本:</div>
                      <div className="text-sm text-gray-700 italic">
                        "{transition.openerText}"
                      </div>
                      {transition.openerPattern && (
                        <div className="text-xs text-gray-500 mt-1">
                          Pattern: {transition.openerPattern}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Transition Analysis */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {/* Connector */}
                    <div className="bg-white bg-opacity-50 rounded p-2">
                      <div className="text-xs text-gray-500">Connector</div>
                      <div className="flex items-center gap-1 mt-1">
                        {transition.hasExplicitConnector ? (
                          <>
                            <CheckCircle className="w-3 h-3 text-green-500" />
                            <span className="text-sm font-medium text-green-700">Yes</span>
                          </>
                        ) : (
                          <>
                            <AlertCircle className="w-3 h-3 text-gray-400" />
                            <span className="text-sm text-gray-500">No</span>
                          </>
                        )}
                      </div>
                      {transition.connectorWords && transition.connectorWords.length > 0 && (
                        <div className="text-xs text-blue-600 mt-1">
                          {transition.connectorWords.join(', ')}
                        </div>
                      )}
                    </div>

                    {/* Semantic Echo */}
                    <div className="bg-white bg-opacity-50 rounded p-2">
                      <div className="text-xs text-gray-500">Semantic Echo</div>
                      <div className="text-sm font-medium mt-1">
                        {(transition.semanticEchoScore * 100).toFixed(0)}%
                      </div>
                      {transition.echoedKeywords && transition.echoedKeywords.length > 0 && (
                        <div className="text-xs text-purple-600 mt-1">
                          {transition.echoedKeywords.slice(0, 3).join(', ')}
                          {transition.echoedKeywords.length > 3 && '...'}
                        </div>
                      )}
                    </div>

                    {/* Formulaic */}
                    <div className="bg-white bg-opacity-50 rounded p-2">
                      <div className="text-xs text-gray-500">Formulaic Opener</div>
                      <div className="flex items-center gap-1 mt-1">
                        {transition.isFormulaicOpener ? (
                          <>
                            <AlertTriangle className="w-3 h-3 text-yellow-500" />
                            <span className="text-sm font-medium text-yellow-700">Yes</span>
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-3 h-3 text-green-500" />
                            <span className="text-sm text-green-600">No</span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Risk Score */}
                    <div className="bg-white bg-opacity-50 rounded p-2">
                      <div className="text-xs text-gray-500">Risk Score</div>
                      <div className={clsx(
                        'text-sm font-medium mt-1',
                        transition.riskScore >= 70 ? 'text-red-600' :
                        transition.riskScore >= 40 ? 'text-yellow-600' : 'text-green-600'
                      )}>
                        {transition.riskScore}/100
                      </div>
                    </div>
                  </div>

                  {/* Warning for problematic transitions */}
                  {(transition.transitionQuality === 'formulaic' || transition.transitionQuality === 'abrupt') && (
                    <div className="mt-3 p-2 bg-white rounded border text-sm">
                      {transition.transitionQuality === 'formulaic' ? (
                        <>
                          <strong className="text-yellow-700">Formulaic Pattern:</strong>
                          <span className="text-gray-600 ml-1">
                            This transition uses common AI patterns. Consider more natural phrasing.
                          </span>
                          <br />
                          <span className="text-yellow-600">公式化模式：此过渡使用常见的AI模式。建议使用更自然的表达。</span>
                        </>
                      ) : (
                        <>
                          <strong className="text-red-700">Abrupt Transition:</strong>
                          <span className="text-gray-600 ml-1">
                            Topic shift without proper connection. Add transitional sentences.
                          </span>
                          <br />
                          <span className="text-red-600">突兀过渡：主题转换缺乏适当衔接。建议添加过渡句。</span>
                        </>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Formulaic Opener Patterns */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Repeat className="w-5 h-5 text-yellow-600" />
          Common Formulaic Openers / 常见公式化开头
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            { en: 'Furthermore, ...', zh: '此外，...' },
            { en: 'In addition, ...', zh: '另外，...' },
            { en: 'Moreover, ...', zh: '而且，...' },
            { en: 'It is worth noting that...', zh: '值得注意的是...' },
            { en: 'In this context, ...', zh: '在这种情况下，...' },
            { en: 'Building upon this, ...', zh: '在此基础上，...' },
          ].map((pattern, index) => (
            <div key={index} className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="text-sm font-medium text-yellow-700">{pattern.en}</div>
              <div className="text-xs text-yellow-600">{pattern.zh}</div>
            </div>
          ))}
        </div>
        <p className="mt-3 text-sm text-gray-600">
          These openers are commonly overused by AI. While valid in moderation, excessive use signals AI generation.
          <br />
          <span className="text-gray-500">
            这些开头常被AI过度使用。适度使用是有效的，但过度使用则表明AI生成。
          </span>
        </p>
      </div>

      {/* No issues message */}
      {transitionIssues.length === 0 && result && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-green-800">
              Paragraph Transitions Look Good
            </h3>
            <p className="text-green-600 mt-1">
              段落过渡良好。过渡自然流畅，没有检测到明显的AI模式。
            </p>
          </div>
        </div>
      )}

      {/* Document Modification Section */}
      {/* 文档修改部分 */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Document Modification / 文档修改
        </h3>
        <p className="text-gray-600 text-sm mb-4">
          Upload a modified file or paste modified text to continue to Layer 2 (Sentence Layer).
          上传修改后的文件或粘贴修改后的文本以继续到第2层（句子层）。
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
            Apply and Continue to Layer 2 / 应用并继续到第2层
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

      {/* Layer 3 Completion Summary */}
      {result && (
        <div className="bg-teal-50 rounded-lg shadow-sm border border-teal-200 p-6">
          <h3 className="text-lg font-semibold text-teal-900 mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-teal-600" />
            Layer 3 Complete / 第3层完成
          </h3>
          <p className="text-teal-700">
            Paragraph-level analysis is complete. Proceed to Layer 2 for sentence-level analysis.
            <br />
            <span className="text-teal-600">
              段落级分析已完成。继续进行第2层句子级分析。
            </span>
          </p>
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
            Previous: Step 3.4
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
