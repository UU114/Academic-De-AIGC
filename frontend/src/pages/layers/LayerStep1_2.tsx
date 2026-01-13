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
  Layers,
  AlertTriangle,
  BarChart2,
  RefreshCw,
  Scale,
  Sparkles,
  Wand2,
  Copy,
  Check,
  X,
  Upload,
  Type,
  Square,
  CheckSquare,
  RotateCcw,
  FileText,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import { documentLayerApi, DocumentAnalysisResponse, DetectionIssue } from '../../services/analysisApi';

/**
 * Layer Step 1.2 - Section Uniformity Detection
 * 步骤 1.2 - 章节均匀性检测
 *
 * Detects (Merged Group 1):
 * - A: Section Symmetry (章节对称结构)
 * - D: Uniform Paragraph Count per Section (章节均匀段落数量)
 * - C: Uniform Section Length (章节均匀长度)
 *
 * Priority: ★★★★☆ (Depends on 1.1 section boundaries)
 * 优先级: ★★★★☆ (依赖1.1的章节边界)
 *
 * Part of the 5-layer detection architecture - Layer 5 Sub-steps.
 * 5层检测架构的一部分 - 第5层子步骤。
 */

interface SectionUniformityData {
  index: number;
  role: string;
  title?: string;
  paragraphCount: number;
  wordCount: number;
}

interface UniformityMetrics {
  // Paragraph count uniformity
  paragraphCountMean: number;
  paragraphCountCV: number;
  paragraphCountIsUniform: boolean;
  // Word count uniformity
  wordCountMean: number;
  wordCountCV: number;
  wordCountIsUniform: boolean;
  // Overall symmetry
  isSymmetric: boolean;
  symmetryScore: number;
}

interface LayerStep1_2Props {
  documentIdProp?: string;
  onComplete?: (result: DocumentAnalysisResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep1_2({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep1_2Props) {
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

  // Update session step on mount
  // 挂载时更新会话步骤
  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer5-step1-2').catch(console.error);
    }
  }, [sessionId]);

  // Analysis state
  // 分析状态
  const [result, setResult] = useState<DocumentAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');

  // Uniformity data
  // 均匀性数据
  const [sections, setSections] = useState<SectionUniformityData[]>([]);
  const [metrics, setMetrics] = useState<UniformityMetrics | null>(null);
  const [uniformityIssues, setUniformityIssues] = useState<DetectionIssue[]>([]);
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

  // Issue selection for merge modify
  // 问题选择（用于合并修改）
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());

  // Issue suggestion state
  // 问题建议状态
  const [issueSuggestion, setIssueSuggestion] = useState<{
    diagnosisZh: string;
    strategies: Array<{
      nameZh: string;
      descriptionZh: string;
      exampleBefore?: string;
      exampleAfter?: string;
      difficulty: string;
      effectiveness: number;
    }>;
    modificationPrompt: string;
    priorityTipsZh: string[];
    cautionZh: string;
  } | null>(null);
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);

  // Merge modify state
  // 合并修改状态
  const [showMergeConfirm, setShowMergeConfirm] = useState(false);
  const [mergeMode, setMergeMode] = useState<'prompt' | 'apply'>('prompt');
  const [mergeUserNotes, setMergeUserNotes] = useState('');
  const [isMerging, setIsMerging] = useState(false);
  const [mergeResult, setMergeResult] = useState<{
    type: 'prompt' | 'apply';
    prompt?: string;
    promptZh?: string;
    modifiedText?: string;
    changesSummaryZh?: string;
    changesCount?: number;
    remainingAttempts?: number;
    colloquialismLevel?: number;
  } | null>(null);
  const [copiedMergePrompt, setCopiedMergePrompt] = useState(false);
  const [regenerateCount, setRegenerateCount] = useState(0);
  const MAX_REGENERATE = 3;

  // Skip confirmation state
  // 跳过确认状态
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);

  // Document modification state
  // 文档修改状态
  const [modifyMode, setModifyMode] = useState<'file' | 'text'>('file');
  const [newFile, setNewFile] = useState<File | null>(null);
  const [newText, setNewText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

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
      // Prioritize processedText (modified by previous step) over originalText
      // 优先使用 processedText（前一步修改后的文本），否则使用 originalText
      const textToUse = doc.processedText || doc.originalText;
      if (textToUse) {
        setDocumentText(textToUse);
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

  // Run analysis
  // 运行分析
  useEffect(() => {
    if (documentText && !isAnalyzingRef.current) {
      runAnalysis();
    }
  }, [documentText]);

  // Calculate uniformity metrics from sections
  // 从章节数据计算均匀性指标
  const calculateMetrics = (sectionData: SectionUniformityData[]): UniformityMetrics => {
    if (sectionData.length < 2) {
      return {
        paragraphCountMean: sectionData[0]?.paragraphCount || 0,
        paragraphCountCV: 0,
        paragraphCountIsUniform: false,
        wordCountMean: sectionData[0]?.wordCount || 0,
        wordCountCV: 0,
        wordCountIsUniform: false,
        isSymmetric: false,
        symmetryScore: 0,
      };
    }

    // Calculate paragraph count stats
    const paraCountArray = sectionData.map(s => s.paragraphCount);
    const paraMean = paraCountArray.reduce((a, b) => a + b, 0) / paraCountArray.length;
    const paraStd = Math.sqrt(
      paraCountArray.reduce((sum, val) => sum + Math.pow(val - paraMean, 2), 0) / paraCountArray.length
    );
    const paraCV = paraMean > 0 ? paraStd / paraMean : 0;

    // Calculate word count stats
    const wordCountArray = sectionData.map(s => s.wordCount);
    const wordMean = wordCountArray.reduce((a, b) => a + b, 0) / wordCountArray.length;
    const wordStd = Math.sqrt(
      wordCountArray.reduce((sum, val) => sum + Math.pow(val - wordMean, 2), 0) / wordCountArray.length
    );
    const wordCV = wordMean > 0 ? wordStd / wordMean : 0;

    // Determine uniformity (CV < 0.3 is considered too uniform / AI-like)
    const paraIsUniform = paraCV < 0.3;
    const wordIsUniform = wordCV < 0.3;

    // Calculate symmetry score (0-100)
    // Lower CV = higher symmetry = more AI-like
    const symmetryScore = Math.round((1 - Math.min(paraCV + wordCV, 2) / 2) * 100);
    const isSymmetric = symmetryScore > 70;

    return {
      paragraphCountMean: paraMean,
      paragraphCountCV: paraCV,
      paragraphCountIsUniform: paraIsUniform,
      wordCountMean: wordMean,
      wordCountCV: wordCV,
      wordCountIsUniform: wordIsUniform,
      isSymmetric,
      symmetryScore,
    };
  };

  const runAnalysis = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;
    setIsAnalyzing(true);
    setError(null);

    try {
      // Step 1.2: Paragraph Length Regularity Analysis with LLM
      // 步骤 1.2：使用LLM进行段落长度规律性分析
      // This API re-calculates all statistics from the current text
      // 此API会从当前文本重新计算所有统计数据
      const paragraphAnalysisResult = await documentLayerApi.analyzeParagraphLength(
        documentText,
        sessionId || undefined
      );

      // Also get sections for UI display from Step 1.1
      // 同时从步骤1.1获取章节信息用于UI显示
      const structureResult = await documentLayerApi.analyzeStructure(documentText, sessionId || undefined);

      if (structureResult.sections) {
        setSections(structureResult.sections);
        // Calculate section-level uniformity metrics for UI
        // 计算章节级别的均匀性指标用于UI
        const calculatedMetrics = calculateMetrics(structureResult.sections);
        setMetrics(calculatedMetrics);
      }

      // Use LLM analysis results directly
      // 直接使用LLM分析结果
      // Convert LLM issues to DetectionIssue format for UI
      // 将LLM issues转换为UI的DetectionIssue格式
      const llmIssues: DetectionIssue[] = [];

      // Use issues from LLM response
      // 使用LLM返回的issues
      const apiIssues = (paragraphAnalysisResult as any).issues || [];
      for (const issue of apiIssues) {
        llmIssues.push({
          type: issue.type || 'uniform_length',
          description: issue.description || '',
          descriptionZh: issue.description_zh || issue.descriptionZh || '',
          severity: issue.severity || 'medium',
          layer: 'document',
          suggestion: issue.fix_suggestions?.join('; ') || '',
          suggestionZh: issue.fix_suggestions_zh?.join('；') || '',
          details: {
            currentCV: issue.current_cv || paragraphAnalysisResult.cv,
            targetCV: issue.target_cv || 0.4,
            meanLength: paragraphAnalysisResult.meanLength,
            stdevLength: paragraphAnalysisResult.stdevLength,
            paragraphCount: paragraphAnalysisResult.paragraphCount,
            evidence: issue.evidence,
            detailedExplanation: issue.detailed_explanation,
            detailedExplanationZh: issue.detailed_explanation_zh,
          }
        });
      }

      // If no issues from LLM but CV >= 0.4, add a "pass" status issue for display
      // 如果LLM没有返回issues且CV >= 0.4，添加一个"通过"状态用于显示
      if (llmIssues.length === 0) {
        const summary = (paragraphAnalysisResult as any).summary || '';
        const summaryZh = (paragraphAnalysisResult as any).summaryZh || (paragraphAnalysisResult as any).summary_zh || '';
        llmIssues.push({
          type: 'length_variation_ok',
          description: summary || `Paragraph length variation is healthy (CV=${paragraphAnalysisResult.cv.toFixed(3)} ≥ 0.40)`,
          descriptionZh: summaryZh || `段落长度变化健康（CV=${paragraphAnalysisResult.cv.toFixed(3)} ≥ 0.40）`,
          severity: 'low',
          layer: 'document',
          suggestion: 'No changes needed',
          suggestionZh: '无需修改',
          details: {
            currentCV: paragraphAnalysisResult.cv,
            targetCV: 0.4,
            status: 'pass'
          }
        });
      }

      setUniformityIssues(llmIssues);

      // Store paragraph analysis result for UI display
      // 存储段落分析结果供UI显示
      setResult(paragraphAnalysisResult as any);

      if (onComplete) {
        onComplete(paragraphAnalysisResult as any);
      }
    } catch (err) {
      console.error('Analysis failed:', err);
      setError('Analysis failed / 分析失败');
    } finally {
      setIsAnalyzing(false);
      isAnalyzingRef.current = false;
    }
  };

  // Navigation
  // 导航处理
  const handleBack = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer5-step1-1/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer5-step1-3/${documentId}?${params.toString()}`);
  };

  // Toggle issue expansion
  // 切换问题展开
  const toggleIssue = (index: number) => {
    setExpandedIssueIndex(expandedIssueIndex === index ? null : index);
  };

  // Toggle issue selection
  // 切换问题选择
  const toggleIssueSelection = (index: number) => {
    const newSelected = new Set(selectedIssueIndices);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedIssueIndices(newSelected);
  };

  // Load suggestion for a specific issue
  // 为特定问题加载建议
  const loadIssueSuggestion = useCallback(async (index: number) => {
    const issue = uniformityIssues[index];
    if (!issue || !documentId) return;

    setIsLoadingSuggestion(true);
    setIssueSuggestion(null);

    try {
      const suggestion = await documentLayerApi.getIssueSuggestion(documentId, issue, false);
      setIssueSuggestion(suggestion);
    } catch (err) {
      console.error('Failed to load issue suggestion:', err);
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [uniformityIssues, documentId]);

  // Handle issue click - toggle expand and load suggestion
  // 处理问题点击 - 切换展开并加载建议
  const handleIssueClick = useCallback(async (index: number) => {
    const issue = uniformityIssues[index];
    if (!issue || !documentId) return;

    // Collapse if already expanded
    if (expandedIssueIndex === index) {
      setExpandedIssueIndex(null);
      setIssueSuggestion(null);
      return;
    }

    // Expand and load suggestion
    setExpandedIssueIndex(index);
    await loadIssueSuggestion(index);
  }, [uniformityIssues, documentId, expandedIssueIndex, loadIssueSuggestion]);

  // Execute merge modify
  // 执行合并修改
  const executeMergeModify = useCallback(async () => {
    if (!documentId || selectedIssueIndices.size === 0) return;

    const selectedIssues = Array.from(selectedIssueIndices).map(idx => uniformityIssues[idx]);

    setIsMerging(true);
    setShowMergeConfirm(false);

    try {
      if (mergeMode === 'prompt') {
        // Generate prompt mode
        const response = await documentLayerApi.generateModifyPrompt(
          documentId,
          selectedIssues,
          { sessionId: sessionId || undefined, userNotes: mergeUserNotes || undefined }
        );
        setMergeResult({
          type: 'prompt',
          prompt: response.prompt,
          promptZh: response.promptZh,
          colloquialismLevel: response.colloquialismLevel,
        });
      } else {
        // AI direct modify mode
        const response = await documentLayerApi.applyModify(
          documentId,
          selectedIssues,
          { sessionId: sessionId || undefined, userNotes: mergeUserNotes || undefined }
        );
        setMergeResult({
          type: 'apply',
          modifiedText: response.modifiedText,
          changesSummaryZh: response.changesSummaryZh,
          changesCount: response.changesCount,
          remainingAttempts: response.remainingAttempts,
          colloquialismLevel: response.colloquialismLevel,
        });
        setRegenerateCount(1);
      }
    } catch (err) {
      console.error('Merge modify failed:', err);
      alert('操作失败，请重试 / Operation failed, please try again');
    } finally {
      setIsMerging(false);
    }
  }, [documentId, selectedIssueIndices, uniformityIssues, mergeMode, mergeUserNotes, sessionId]);

  // Handle regenerate
  // 处理重新生成
  const handleRegenerate = useCallback(async () => {
    if (regenerateCount >= MAX_REGENERATE || !documentId || selectedIssueIndices.size === 0) return;

    const selectedIssues = Array.from(selectedIssueIndices).map(idx => uniformityIssues[idx]);

    setIsMerging(true);

    try {
      const response = await documentLayerApi.applyModify(
        documentId,
        selectedIssues,
        { sessionId: sessionId || undefined, userNotes: mergeUserNotes || undefined }
      );
      setMergeResult({
        type: 'apply',
        modifiedText: response.modifiedText,
        changesSummaryZh: response.changesSummaryZh,
        changesCount: response.changesCount,
        remainingAttempts: response.remainingAttempts,
        colloquialismLevel: response.colloquialismLevel,
      });
      setRegenerateCount(prev => prev + 1);
    } catch (err) {
      console.error('Regenerate failed:', err);
      alert('重新生成失败，请重试 / Regeneration failed, please try again');
    } finally {
      setIsMerging(false);
    }
  }, [documentId, regenerateCount, selectedIssueIndices, uniformityIssues, sessionId, mergeUserNotes]);

  // Handle accept modification - fill into text input and scroll
  // 处理接受修改 - 填入文本输入框并滚动
  const handleAcceptModification = useCallback(() => {
    if (mergeResult?.modifiedText) {
      setNewText(mergeResult.modifiedText);
      setModifyMode('text');
      setMergeResult(null);
      setTimeout(() => {
        const modifySection = document.getElementById('modify-section');
        if (modifySection) {
          modifySection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
    }
  }, [mergeResult?.modifiedText]);

  // Handle confirm modify
  // 处理确认修改
  const handleConfirmModify = useCallback(async () => {
    if (modifyMode === 'file' && !newFile) {
      setUploadError('请选择一个文件 / Please select a file');
      return;
    }

    if (modifyMode === 'text' && !newText.trim()) {
      setUploadError('请输入文本内容 / Please enter text content');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      let newDocumentId: string;

      if (modifyMode === 'file' && newFile) {
        const result = await documentApi.upload(newFile);
        newDocumentId = result.id;
      } else {
        const result = await documentApi.uploadText(newText);
        newDocumentId = result.id;
      }

      // Navigate to Step 1.3 with new document
      const sessionParam = sessionId ? `&session=${sessionId}` : '';
      navigate(`/flow/layer5-step1-3/${newDocumentId}?mode=${mode}${sessionParam}`);
    } catch (err) {
      setUploadError((err as Error).message || '上传失败，请重试 / Upload failed, please try again');
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, sessionId, mode, navigate]);

  // Validate and set file
  // 验证并设置文件
  const validateAndSetFile = (selectedFile: File) => {
    const allowedTypes = [
      'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(selectedFile.type)) {
      setUploadError('仅支持 TXT 和 DOCX 格式 / Only TXT and DOCX formats are supported');
      return;
    }

    if (selectedFile.size > maxSize) {
      setUploadError('文件大小不能超过 10MB / File size cannot exceed 10MB');
      return;
    }

    setNewFile(selectedFile);
    setUploadError(null);
  };

  // Handle file change
  // 处理文件变化
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  // Copy prompt to clipboard
  // 复制提示词到剪贴板
  const copyToClipboard = (text: string, setCopied: (value: boolean) => void) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  // Get bar width for visualization
  // 获取可视化条宽度
  const getBarWidth = (value: number, max: number) => {
    return `${Math.min((value / max) * 100, 100)}%`;
  };

  // Loading state
  // 加载状态
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage category="structure" centered />
      </div>
    );
  }

  // Error state
  // 错误状态
  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-red-800">Error / 错误</h3>
            <p className="text-red-600 mt-1">{error}</p>
            <Button
              variant="secondary"
              size="sm"
              className="mt-3"
              onClick={() => {
                setError(null);
                isAnalyzingRef.current = false;
                runAnalysis();
              }}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry / 重试
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Find max values for visualization
  const maxParagraphs = Math.max(...sections.map(s => s.paragraphCount), 1);
  const maxWords = Math.max(...sections.map(s => s.wordCount), 1);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Loading Overlay for LLM operations */}
      {/* LLM操作加载遮罩 */}
      <LoadingOverlay
        isVisible={isMerging}
        operationType={mergeMode}
        issueCount={selectedIssueIndices.size}
      />

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Layers className="w-4 h-4" />
          <span>Layer 5 / 第5层</span>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Step 1.2 章节均匀性</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Section Uniformity Detection
        </h1>
        <p className="text-gray-600 mt-1">
          章节均匀性检测 - 检测章节对称结构、均匀段落数、均匀长度
        </p>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing uniformity... / 分析均匀性中...</p>
              <p className="text-blue-600 text-sm">Calculating section symmetry and balance</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* Paragraph Length Statistics - LLM Analysis Results */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Paragraph Length CV (Main Metric) */}
            <div className={clsx(
              'p-4 rounded-lg border',
              (result as any).cv < 0.3 ? 'bg-red-50 border-red-200' :
              (result as any).cv < 0.4 ? 'bg-yellow-50 border-yellow-200' :
              'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <BarChart2 className={clsx(
                  'w-5 h-5',
                  (result as any).cv < 0.3 ? 'text-red-600' :
                  (result as any).cv < 0.4 ? 'text-yellow-600' :
                  'text-green-600'
                )} />
                <span className="font-medium text-gray-900">Paragraph Length CV / 段落长度CV</span>
              </div>
              <div className={clsx(
                'text-3xl font-bold',
                (result as any).cv < 0.3 ? 'text-red-600' :
                (result as any).cv < 0.4 ? 'text-yellow-600' :
                'text-green-600'
              )}>
                {((result as any).cv * 100).toFixed(1)}%
              </div>
              <p className={clsx(
                'text-sm mt-1',
                (result as any).cv < 0.3 ? 'text-red-600' :
                (result as any).cv < 0.4 ? 'text-yellow-600' :
                'text-green-600'
              )}>
                {(result as any).cv < 0.3 ? 'Too uniform (AI-like) / 过于均匀（AI风格）' :
                 (result as any).cv < 0.4 ? 'Moderate / 中等' :
                 'Natural variation / 自然变化'}
                {' '}(Target ≥ 40%)
              </p>
            </div>

            {/* Paragraph Count */}
            <div className="p-4 rounded-lg border bg-blue-50 border-blue-200">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-5 h-5 text-blue-600" />
                <span className="font-medium text-gray-900">Paragraph Count / 段落数量</span>
              </div>
              <div className="text-3xl font-bold text-blue-600">
                {(result as any).paragraphCount || 0}
              </div>
              <p className="text-sm mt-1 text-blue-600">
                Mean: {((result as any).meanLength || 0).toFixed(1)} words / 词
              </p>
            </div>

            {/* Length Range */}
            <div className="p-4 rounded-lg border bg-purple-50 border-purple-200">
              <div className="flex items-center gap-2 mb-2">
                <Scale className="w-5 h-5 text-purple-600" />
                <span className="font-medium text-gray-900">Length Range / 长度范围</span>
              </div>
              <div className="text-2xl font-bold text-purple-600">
                {(result as any).minLength || 0} - {(result as any).maxLength || 0}
              </div>
              <p className="text-sm mt-1 text-purple-600">
                Stdev: {((result as any).stdevLength || 0).toFixed(1)} words / 词
              </p>
            </div>
          </div>

          {/* Risk alert if too uniform */}
          {(result as any).cv < 0.3 && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Uniform Paragraph Lengths Detected
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：检测到段落长度过于均匀。CV值 {((result as any).cv * 100).toFixed(1)}% 低于目标值 40%。
                  建议拆分部分段落、扩展短段落或合并相关段落以增加长度变化。
                </p>
              </div>
            </div>
          )}

          {/* Section Visualization */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <BarChart2 className="w-5 h-5" />
              Section Distribution / 章节分布
            </h3>
            <div className="bg-white border rounded-lg overflow-hidden">
              <div className="p-4">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 border-b">
                      <th className="pb-2 w-24">Section</th>
                      <th className="pb-2">Paragraphs / 段落数</th>
                      <th className="pb-2">Words / 字数</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sections.map((section, idx) => (
                      <tr key={idx} className="border-b last:border-b-0">
                        <td className="py-3 text-sm font-medium text-gray-900">
                          {section.title || `Section ${idx + 1}`}
                        </td>
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-blue-500 rounded-full transition-all"
                                style={{ width: getBarWidth(section.paragraphCount, maxParagraphs) }}
                              />
                            </div>
                            <span className="text-sm text-gray-600 w-8">{section.paragraphCount}</span>
                          </div>
                        </td>
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-green-500 rounded-full transition-all"
                                style={{ width: getBarWidth(section.wordCount, maxWords) }}
                              />
                            </div>
                            <span className="text-sm text-gray-600 w-12">{section.wordCount}</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="px-4 py-2 bg-gray-50 border-t text-sm text-gray-500">
                Mean paragraphs: {metrics.paragraphCountMean.toFixed(1)} |
                Mean words: {metrics.wordCountMean.toFixed(0)}
              </div>
            </div>
          </div>

          {/* Analysis Result / Issues */}
          {uniformityIssues.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                {uniformityIssues.some(i => i.type === 'length_variation_ok' || i.severity === 'low') &&
                 !uniformityIssues.some(i => i.severity === 'high' || i.severity === 'medium') ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                )}
                Analysis Result / 分析结果
                <span className="text-sm font-normal text-gray-500">
                  ({uniformityIssues.length} {uniformityIssues.length === 1 ? 'item' : 'items'})
                </span>
              </h3>
              <div className="space-y-2">
                {uniformityIssues.map((issue, idx) => {
                  const isExpanded = expandedIssueIndex === idx;
                  const isSelected = selectedIssueIndices.has(idx);
                  // Determine colors based on issue type/severity
                  const isPass = issue.type === 'length_variation_ok' || (issue.details as any)?.status === 'pass';
                  const bgColor = isPass ? 'bg-green-50' : issue.severity === 'high' ? 'bg-red-50' : 'bg-yellow-50';
                  const borderColor = isPass ? 'border-green-200' : issue.severity === 'high' ? 'border-red-200' : 'border-yellow-200';
                  const hoverColor = isPass ? 'hover:bg-green-100' : issue.severity === 'high' ? 'hover:bg-red-100' : 'hover:bg-yellow-100';
                  const iconColor = isPass ? 'text-green-600' : issue.severity === 'high' ? 'text-red-600' : 'text-yellow-600';
                  const textColor = isPass ? 'text-green-800' : issue.severity === 'high' ? 'text-red-800' : 'text-yellow-800';
                  return (
                    <div
                      key={idx}
                      className={`${bgColor} border ${borderColor} rounded-lg overflow-hidden`}
                    >
                      <div className="flex items-start">
                        {/* Selection checkbox - hide for pass status */}
                        {!isPass && (
                          <button
                            onClick={() => toggleIssueSelection(idx)}
                            className={`p-4 ${hoverColor} transition-colors`}
                          >
                            {isSelected ? (
                              <CheckSquare className="w-5 h-5 text-blue-600" />
                            ) : (
                              <Square className="w-5 h-5 text-gray-400" />
                            )}
                          </button>
                        )}

                        {/* Issue content */}
                        <button
                          onClick={() => !isPass && handleIssueClick(idx)}
                          className={`flex-1 px-4 py-3 flex items-center justify-between ${isPass ? '' : hoverColor} transition-colors text-left ${isPass ? 'cursor-default' : ''}`}
                        >
                          <div className="flex items-center gap-3">
                            {isPass ? (
                              <CheckCircle className={`w-5 h-5 ${iconColor}`} />
                            ) : (
                              <AlertCircle className={`w-5 h-5 ${iconColor}`} />
                            )}
                            <p className={`font-medium ${textColor}`}>
                              {issue.descriptionZh || issue.description}
                            </p>
                          </div>
                          {!isPass && (
                            isExpanded ? (
                              <ChevronUp className="w-5 h-5 text-gray-400" />
                            ) : (
                              <ChevronDown className="w-5 h-5 text-gray-400" />
                            )
                          )}
                        </button>
                      </div>

                      {/* Expanded content with detailed suggestion */}
                      {isExpanded && !isPass && (
                        <div className={`px-4 py-3 border-t ${borderColor}`}>
                          {isLoadingSuggestion && (
                            <div className="flex items-center justify-center py-6">
                              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                              <span className="ml-2 text-gray-600">Loading suggestion...</span>
                            </div>
                          )}

                          {!isLoadingSuggestion && issueSuggestion && (
                            <div className="space-y-4">
                              {/* Diagnosis */}
                              <div>
                                <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                  诊断 / Diagnosis
                                </h4>
                                <p className="text-sm text-gray-700">
                                  {issueSuggestion.diagnosisZh}
                                </p>
                              </div>

                              {/* Strategies */}
                              {issueSuggestion.strategies && issueSuggestion.strategies.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                    修改策略 / Modification Strategies
                                  </h4>
                                  <div className="space-y-3">
                                    {issueSuggestion.strategies.map((strategy, sIdx) => (
                                      <div key={sIdx} className="bg-white p-3 rounded border border-gray-200">
                                        <div className="flex items-center justify-between mb-2">
                                          <h5 className="font-medium text-gray-900">{strategy.nameZh}</h5>
                                          <span className="text-xs text-gray-500">
                                            效果: {strategy.effectiveness}/100
                                          </span>
                                        </div>
                                        <p className="text-sm text-gray-600 mb-2">
                                          {strategy.descriptionZh}
                                        </p>
                                        {strategy.exampleBefore && strategy.exampleAfter && (
                                          <div className="mt-2 text-xs space-y-1">
                                            <div>
                                              <span className="text-red-600">修改前: </span>
                                              <span className="text-gray-700">{strategy.exampleBefore}</span>
                                            </div>
                                            <div>
                                              <span className="text-green-600">修改后: </span>
                                              <span className="text-gray-700">{strategy.exampleAfter}</span>
                                            </div>
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Priority Tips */}
                              {issueSuggestion.priorityTipsZh && issueSuggestion.priorityTipsZh.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                    优先建议 / Priority Tips
                                  </h4>
                                  <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                                    {issueSuggestion.priorityTipsZh.map((tip, tIdx) => (
                                      <li key={tIdx}>{tip}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}

                          {!isLoadingSuggestion && !issueSuggestion && (
                            <button
                              onClick={() => loadIssueSuggestion(idx)}
                              className="w-full text-left text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 p-2 rounded transition-colors"
                            >
                              🔍 点击加载详细建议 / Click to load detailed suggestion
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Batch Actions - only show if there are issues that need fixing */}
          {uniformityIssues.some(i => i.type !== 'length_variation_ok' && (i.details as any)?.status !== 'pass') && (
            <div className="mb-6 pb-6 border-b">
              <div className="flex items-center justify-between mb-4">
                <div className="text-sm text-gray-600">
                  {selectedIssueIndices.size} selected / 已选择 {selectedIssueIndices.size} 个问题
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setMergeMode('prompt');
                      setShowMergeConfirm(true);
                    }}
                    disabled={selectedIssueIndices.size === 0}
                  >
                    <Sparkles className="w-4 h-4 mr-2" />
                    生成Prompt / Generate Prompt
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
                    <Wand2 className="w-4 h-4 mr-2" />
                    AI修改 / AI Modify
                  </Button>
                </div>
              </div>

              {/* Confirm Dialog */}
              {showMergeConfirm && (
                <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-semibold text-blue-900 mb-2">
                    {mergeMode === 'prompt' ? '生成修改提示词 / Generate Prompt' : 'AI直接修改 / AI Direct Modify'}
                  </h4>
                  <p className="text-sm text-blue-700 mb-3">
                    已选择 {selectedIssueIndices.size} 个问题
                  </p>
                  <textarea
                    placeholder="附加说明（可选）/ Additional notes (optional)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mb-3"
                    rows={2}
                    value={mergeUserNotes}
                    onChange={(e) => setMergeUserNotes(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={executeMergeModify}
                      disabled={isMerging}
                    >
                      {isMerging ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>确认 / Confirm</>
                      )}
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setShowMergeConfirm(false)}
                      disabled={isMerging}
                    >
                      取消 / Cancel
                    </Button>
                  </div>
                </div>
              )}

              {/* Merge Result */}
              {mergeResult && (
                <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  {mergeResult.type === 'prompt' ? (
                    <>
                      <h4 className="font-semibold text-green-900 mb-2">
                        ✅ 提示词已生成 / Prompt Generated
                      </h4>
                      <div className="bg-white p-3 rounded border border-green-300 mb-3">
                        <pre className="text-sm whitespace-pre-wrap text-gray-800">
                          {mergeResult.promptZh || mergeResult.prompt}
                        </pre>
                      </div>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => copyToClipboard(mergeResult.promptZh || mergeResult.prompt || '', setCopiedMergePrompt)}
                      >
                        {copiedMergePrompt ? (
                          <>
                            <Check className="w-4 h-4 mr-2" />
                            已复制 / Copied
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4 mr-2" />
                            复制 / Copy
                          </>
                        )}
                      </Button>
                    </>
                  ) : (
                    <>
                      <h4 className="font-semibold text-green-900 mb-2">
                        ✅ AI修改完成 / AI Modification Complete
                      </h4>
                      <p className="text-sm text-green-700 mb-2">
                        {mergeResult.changesSummaryZh} ({mergeResult.changesCount} 处修改)
                      </p>

                      {/* Preview of modified text - full content with scrollable area */}
                      {/* 修改后内容预览 - 完整内容可滚动 */}
                      <div className="bg-white p-3 rounded border border-green-300 mb-3 max-h-96 overflow-y-auto">
                        <p className="text-xs text-gray-500 mb-1">
                          修改后内容 / Modified Content ({mergeResult.modifiedText?.length || 0} 字符):
                        </p>
                        <pre className="text-sm whitespace-pre-wrap text-gray-800 font-mono">
                          {mergeResult.modifiedText}
                        </pre>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={handleAcceptModification}
                        >
                          <Check className="w-4 h-4 mr-2" />
                          采纳修改（填入下方输入框）
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={handleRegenerate}
                          disabled={regenerateCount >= MAX_REGENERATE || isMerging}
                        >
                          {isMerging ? (
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          ) : (
                            <RotateCcw className="w-4 h-4 mr-2" />
                          )}
                          重新生成 ({regenerateCount}/{MAX_REGENERATE})
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setMergeResult(null)}
                        >
                          <X className="w-4 h-4 mr-2" />
                          取消
                        </Button>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        💡 点击"采纳修改"后，内容会自动填入下方文本框，您可以继续编辑后再应用
                      </p>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {/* No issues */}
          {!metrics.isSymmetric && uniformityIssues.length === 0 && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">
                  No Uniformity Issues Detected
                </h3>
                <p className="text-green-600 mt-1">
                  未检测到均匀性问题。章节分布看起来是自然的。
                </p>
              </div>
            </div>
          )}

          {/* Processing time */}
          {result.processingTimeMs && (
            <p className="text-sm text-gray-500 mb-6">
              Analysis completed in {result.processingTimeMs}ms
            </p>
          )}

          {/* Document Modification Section */}
          <div id="modify-section" className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              修改文档并应用 / Modify Document and Apply
            </h3>

            {/* Mode selector */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setModifyMode('file')}
                className={clsx(
                  'flex-1 py-3 px-4 rounded-lg border-2 transition-colors flex flex-col items-center',
                  modifyMode === 'file'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-600 hover:border-gray-400'
                )}
              >
                <Upload className="w-5 h-5 mb-1" />
                <span className="text-sm font-medium">上传修改后的文件</span>
                <span className="text-xs text-gray-500">Upload Modified File</span>
              </button>
              <button
                onClick={() => setModifyMode('text')}
                className={clsx(
                  'flex-1 py-3 px-4 rounded-lg border-2 transition-colors flex flex-col items-center',
                  modifyMode === 'text'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-600 hover:border-gray-400'
                )}
              >
                <Type className="w-5 h-5 mb-1" />
                <span className="text-sm font-medium">输入修改后的内容</span>
                <span className="text-xs text-gray-500">Input Modified Content</span>
              </button>
            </div>

            {/* File upload mode */}
            {modifyMode === 'file' && (
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-600 mb-3">
                  支持 TXT 和 DOCX 格式，最大 10MB
                  <br />
                  <span className="text-gray-400">Supports TXT and DOCX formats, max 10MB</span>
                </p>
                <input
                  type="file"
                  accept=".txt,.docx"
                  onChange={handleFileChange}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                {newFile && (
                  <p className="mt-2 text-sm text-green-600">
                    ✓ {newFile.name} ({(newFile.size / 1024).toFixed(2)} KB)
                  </p>
                )}
              </div>
            )}

            {/* Text input mode */}
            {modifyMode === 'text' && (
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-600 mb-3">
                  在下方输入修改后的文本内容，AI修改结果会自动填入此处
                  <br />
                  <span className="text-gray-400">Enter modified text below. AI modification results will auto-fill here.</span>
                </p>
                <textarea
                  value={newText}
                  onChange={(e) => setNewText(e.target.value)}
                  placeholder="粘贴或输入修改后的文本内容... / Paste or type modified text content..."
                  className="w-full h-64 px-3 py-2 border border-gray-300 rounded-lg resize-y font-mono text-sm"
                />
                <div className="mt-2 flex items-center justify-between">
                  <p className="text-sm text-gray-500">
                    {newText.length} 字符 / characters
                  </p>
                  {newText && (
                    <button
                      onClick={() => setNewText('')}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      清空 / Clear
                    </button>
                  )}
                </div>
              </div>
            )}

            {uploadError && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                {uploadError}
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
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    处理中...
                  </>
                ) : (
                  <>
                    <ArrowRight className="w-4 h-4 mr-2" />
                    应用并进行下一步 / Apply and Continue
                  </>
                )}
              </Button>
            </div>
          </div>
        </>
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
                  handleNext();
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
        <div className="flex items-center justify-between pt-6 border-t">
          <Button variant="secondary" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back: Structure / 上一步：结构
          </Button>
          <Button variant="primary" onClick={() => setShowSkipConfirm(true)} disabled={isAnalyzing}>
            Skip and Continue / 跳过并继续
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
