import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  BarChart3,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  Sparkles,
  Lightbulb,
  Edit3,
  Check,
  X,
  Upload,
  FileText,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import { useSubstepStateStore } from '../../stores/substepStateStore';
import {
  sentenceLayerApi,
  documentLayerApi,
  PatternAnalysisResponse,
  SyntacticVoidMatch,
  DetectionIssue,
  ModifyPromptResponse,
  ApplyModifyResponse,
} from '../../services/analysisApi';

/**
 * Layer Step 4.1 - Sentence Pattern Analysis
 * 步骤 4.1 - 句式结构分析
 *
 * Analyzes sentence patterns across the document:
 * - Sentence type distribution (simple/compound/complex/compound_complex)
 * - Sentence opener analysis (repetition, subject-first ratio)
 * - Voice distribution (active/passive)
 * - Identifies high-risk paragraphs for processing
 *
 * 分析全文的句式模式：
 * - 句式类型分布
 * - 句首词分析
 * - 语态分布
 * - 识别需要处理的高风险段落
 */

interface LayerStep4_1Props {
  documentIdProp?: string;
  onComplete?: (result: PatternAnalysisResponse) => void;
  showNavigation?: boolean;
}

// Issue Suggestion Response type (LLM-based)
// 问题建议响应类型（基于LLM）
interface IssueSuggestionResponseLocal {
  analysis: string;
  suggestions: string[];
  exampleFix?: string;
}

export default function LayerStep4_1({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep4_1Props) {
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
      sessionApi.updateStep(sessionId, 'layer2-step4-1').catch(console.error);
    }
  }, [sessionId]);

  // Substep state store for caching and persistence
  // 用于缓存和持久化的子步骤状态存储
  const substepStore = useSubstepStateStore();

  // State
  const [result, setResult] = useState<PatternAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [documentText, setDocumentText] = useState<string>('');

  // Issues derived from analysis result
  // 从分析结果派生的问题列表
  const [patternIssues, setPatternIssues] = useState<DetectionIssue[]>([]);

  // Issue selection for merge modify
  // 用于合并修改的问题选择
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());

  // Click-expand state for individual issue analysis
  // 点击展开状态，用于单个问题分析
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

  // Issue suggestion state (LLM-based detailed suggestions)
  // 问题建议状态（基于LLM的详细建议）
  const [issueSuggestion, setIssueSuggestion] = useState<IssueSuggestionResponseLocal | null>(null);
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);
  // Per-issue suggestion cache to avoid redundant API calls
  // 每个问题的建议缓存，避免重复API调用
  const suggestionCacheRef = useRef<Map<number, IssueSuggestionResponseLocal>>(new Map());

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

  const loadDocumentText = useCallback(async (docId: string) => {
    try {
      // Initialize substep store for session if needed
      // 如果需要，为会话初始化子步骤存储
      if (sessionId && substepStore.currentSessionId !== sessionId) {
        await substepStore.initForSession(sessionId);
      }

      // Check previous steps for modified text (step4-0 first, then Layer 3 -> Layer 4)
      // 检查先前步骤的修改文本（先检查step4-0，然后是层3 -> 层4）
      const previousSteps = [
        'step4-0',
        'step3-5', 'step3-4', 'step3-3', 'step3-2', 'step3-1', 'step3-0',
        'step2-5', 'step2-4', 'step2-3', 'step2-2', 'step2-1', 'step2-0',
        'step1-5', 'step1-4', 'step1-3', 'step1-2', 'step1-1'
      ];
      let foundModifiedText: string | null = null;

      for (const stepName of previousSteps) {
        const stepState = substepStore.getState(stepName);
        if (stepState?.modifiedText) {
          console.log(`[LayerStep4_1] Using modified text from ${stepName}`);
          foundModifiedText = stepState.modifiedText;
          break;
        }
      }

      if (foundModifiedText) {
        setDocumentText(foundModifiedText);
      } else {
        // Fall back to original document text
        // 回退到原始文档文本
        const doc = await documentApi.get(docId);
        if (doc.originalText) {
          setDocumentText(doc.originalText);
        } else {
          setError('Document text not found / 未找到文档文本');
        }
      }
    } catch (err) {
      console.error('Failed to load document:', err);
      setError('Failed to load document / 加载文档失败');
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
      const analysisResult = await sentenceLayerApi.analyzePatterns(documentText, undefined, sessionId || undefined);
      setResult(analysisResult);

      // Create issues from analysis result
      // 从分析结果创建问题列表
      const issues: DetectionIssue[] = [];

      // Check type distribution issues
      // 检查类型分布问题
      if (analysisResult.typeDistribution) {
        Object.entries(analysisResult.typeDistribution).forEach(([type, stats]) => {
          if (stats.isRisk) {
            issues.push({
              type: `${type}_distribution_risk`,
              description: `${type.replace('_', ' ')} sentences: ${stats.count} (${Math.round(stats.percentage * 100)}%) - exceeds threshold of ${Math.round(stats.threshold * 100)}%`,
              descriptionZh: `${type === 'simple' ? '简单句' : type === 'compound' ? '并列句' : type === 'complex' ? '复杂句' : '复合复杂句'}: ${stats.count}个 (${Math.round(stats.percentage * 100)}%) - 超过阈值${Math.round(stats.threshold * 100)}%`,
              severity: stats.percentage > stats.threshold * 1.5 ? 'high' : 'medium',
              layer: 'sentence',
              location: 'Document-wide',
            });
          }
        });
      }

      // Check opener analysis issues
      // 检查句首词分析问题
      if (analysisResult.openerAnalysis) {
        if (analysisResult.openerAnalysis.repetitionRate > 0.3) {
          issues.push({
            type: 'opener_repetition_high',
            description: `High opener repetition rate (${Math.round(analysisResult.openerAnalysis.repetitionRate * 100)}%)`,
            descriptionZh: `句首词重复率过高 (${Math.round(analysisResult.openerAnalysis.repetitionRate * 100)}%)`,
            severity: analysisResult.openerAnalysis.repetitionRate > 0.4 ? 'high' : 'medium',
            layer: 'sentence',
            location: `Most repeated: ${analysisResult.openerAnalysis.topRepeated.slice(0, 3).join(', ')}`,
          });
        }

        if (analysisResult.openerAnalysis.subjectOpeningRate > 0.8) {
          issues.push({
            type: 'subject_first_overuse',
            description: `High subject-first rate (${Math.round(analysisResult.openerAnalysis.subjectOpeningRate * 100)}%) - monotonous sentence beginnings`,
            descriptionZh: `主语开头率过高 (${Math.round(analysisResult.openerAnalysis.subjectOpeningRate * 100)}%) - 句式单调`,
            severity: 'medium',
            layer: 'sentence',
            location: 'Document-wide',
          });
        }

        // Add issues from opener analysis
        // 添加句首词分析中的问题
        analysisResult.openerAnalysis.issues.forEach((issueText, idx) => {
          issues.push({
            type: `opener_issue_${idx}`,
            description: issueText,
            descriptionZh: issueText,
            severity: 'medium',
            layer: 'sentence',
          });
        });
      }

      // Check for high-risk paragraphs
      // 检查高风险段落
      if (analysisResult.highRiskParagraphs && analysisResult.highRiskParagraphs.length > 0) {
        analysisResult.highRiskParagraphs.forEach(para => {
          if (para.riskLevel === 'high') {
            issues.push({
              type: 'high_risk_paragraph',
              description: `Paragraph ${para.paragraphIndex + 1} has high risk (score: ${para.riskScore}) - simple ratio: ${Math.round(para.simpleRatio * 100)}%, length CV: ${para.lengthCv.toFixed(2)}`,
              descriptionZh: `段落${para.paragraphIndex + 1}风险较高 (分数: ${para.riskScore}) - 简单句比例: ${Math.round(para.simpleRatio * 100)}%, 句长变异系数: ${para.lengthCv.toFixed(2)}`,
              severity: 'high',
              layer: 'sentence',
              location: `Paragraph ${para.paragraphIndex + 1}`,
            });
          }
        });
      }

      // Check for syntactic voids
      // 检查句法空洞
      if (analysisResult.syntacticVoids && analysisResult.syntacticVoids.length > 0) {
        const criticalVoids = analysisResult.syntacticVoids.filter(v => v.severity === 'high');
        if (criticalVoids.length > 0) {
          issues.push({
            type: 'syntactic_void_critical',
            description: `${criticalVoids.length} critical syntactic void(s) detected - flowery but semantically empty phrases`,
            descriptionZh: `检测到${criticalVoids.length}个严重句法空洞 - 华丽但语义空洞的短语`,
            severity: 'high',
            layer: 'sentence',
            location: `${criticalVoids.length} occurrences`,
          });
        }

        if (analysisResult.voidDensity && analysisResult.voidDensity > 0.1) {
          issues.push({
            type: 'high_void_density',
            description: `High syntactic void density (${(analysisResult.voidDensity * 100).toFixed(1)}%) - typical AI writing pattern`,
            descriptionZh: `句法空洞密度过高 (${(analysisResult.voidDensity * 100).toFixed(1)}%) - 典型AI写作特征`,
            severity: analysisResult.voidDensity > 0.15 ? 'high' : 'medium',
            layer: 'sentence',
            location: 'Document-wide',
          });
        }
      }

      // Add any issues from the API response
      // 添加API响应中的问题
      if (analysisResult.issues && Array.isArray(analysisResult.issues)) {
        analysisResult.issues.forEach((issue: Record<string, unknown>) => {
          if (issue.description) {
            issues.push({
              type: String(issue.type || 'api_issue'),
              description: String(issue.description),
              descriptionZh: String(issue.descriptionZh || issue.description),
              severity: (issue.severity as 'low' | 'medium' | 'high') || 'medium',
              layer: 'sentence',
              location: issue.location ? String(issue.location) : undefined,
            });
          }
        });
      }

      setPatternIssues(issues);

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

  // Load detailed suggestion for a specific issue (LLM-based, with caching)
  // 为特定问题加载详细建议（基于LLM，带缓存）
  const loadIssueSuggestion = useCallback(async (index: number) => {
    const issue = patternIssues[index];
    if (!issue || !documentId) return;

    // Check cache first
    // 首先检查缓存
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
      const suggestion = {
        analysis: response.diagnosisZh || '',
        suggestions: response.strategies?.map((s) => `${s.nameZh}: ${s.descriptionZh}`) || [],
        exampleFix: response.strategies?.[0]?.exampleAfter || '',
      };
      suggestionCacheRef.current.set(index, suggestion);
      setIssueSuggestion(suggestion);
    } catch (err) {
      console.error('Failed to load suggestion:', err);
      setSuggestionError('Failed to load detailed suggestion / 加载详细建议失败');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [patternIssues, documentId]);

  // Handle issue click - toggle expand and auto-load suggestion
  // 处理问题点击 - 切换展开并自动加载建议
  const handleIssueClick = useCallback(async (index: number) => {
    if (expandedIssueIndex === index) {
      setExpandedIssueIndex(null);
      setIssueSuggestion(null);
      return;
    }
    setExpandedIssueIndex(index);
    await loadIssueSuggestion(index);
  }, [expandedIssueIndex, loadIssueSuggestion]);

  // Toggle issue selection (checkbox only)
  // 切换问题选择（仅复选框）
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
    setSelectedIssueIndices(new Set(patternIssues.map((_, idx) => idx)));
  }, [patternIssues]);

  // Deselect all issues
  // 取消全选所有问题
  const deselectAllIssues = useCallback(() => {
    setSelectedIssueIndices(new Set());
  }, []);

  // Execute merge modify (generate prompt or apply modification)
  // 执行合并修改（生成提示或应用修改）
  const executeMergeModify = useCallback(async () => {
    if (selectedIssueIndices.size === 0 || !documentId) return;

    setIsMerging(true);
    setShowMergeConfirm(false);

    try {
      const selectedIssues = Array.from(selectedIssueIndices).map(i => patternIssues[i]);

      if (mergeMode === 'prompt') {
        const response = await documentLayerApi.generateModifyPrompt(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult({
          prompt: response.prompt,
          promptZh: response.promptZh,
          issuesSummaryZh: response.issuesSummaryZh,
          colloquialismLevel: response.colloquialismLevel,
          estimatedChanges: response.estimatedChanges,
        } as ModifyPromptResponse);
      } else {
        const response = await documentLayerApi.applyModify(
          documentId,
          selectedIssues,
          {
            sessionId: sessionId || undefined,
            userNotes: mergeUserNotes || undefined,
          }
        );
        setMergeResult({
          modifiedText: response.modifiedText,
          changesSummary: response.changesSummaryZh,
          changesCount: response.changesCount,
        } as ApplyModifyResponse);
      }
    } catch (err) {
      console.error('Merge modify failed:', err);
      setError('Merge modify failed / 合并修改失败');
    } finally {
      setIsMerging(false);
    }
  }, [selectedIssueIndices, documentId, patternIssues, mergeMode, mergeUserNotes, sessionId]);

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
      // Get modified text from file or text input
      // 从文件或文本输入获取修改后的文本
      let modifiedText: string = '';
      if (modifyMode === 'file' && newFile) {
        modifiedText = await newFile.text();
      } else if (modifyMode === 'text' && newText.trim()) {
        modifiedText = newText.trim();
      } else {
        setError('Please select a file or enter text / 请选择文件或输入文本');
        setIsUploading(false);
        return;
      }

      // Save modified text to substep store for next step to use
      // 将修改后的文本保存到子步骤存储，供下一步使用
      if (sessionId && modifiedText) {
        await substepStore.saveModifiedText('step4-1', modifiedText);
        await substepStore.markCompleted('step4-1');
        console.log('[LayerStep4_1] Saved modified text to substep store');
      }

      // Navigate to next step (Processing Console) with current document ID
      // 使用当前文档ID导航到下一步（处理控制台）
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer2-step4-console/${documentId}?${params.toString()}`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload modified document / 上传修改后的文档失败');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate, documentId, substepStore]);

  // Navigation handlers
  // 导航处理
  const goToNextStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer2-step4-console/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer2-step4-0/${documentId}?${params.toString()}`);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'simple': return 'bg-blue-500';
      case 'compound': return 'bg-green-500';
      case 'complex': return 'bg-purple-500';
      case 'compound_complex': return 'bg-orange-500';
      default: return 'bg-gray-500';
    }
  };

  const hasSelectedIssues = selectedIssueIndices.size > 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage category="general" />
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
        <Button onClick={() => {
          setError(null);
          isAnalyzingRef.current = false;
          runAnalysis();
        }} className="mt-4" variant="outline">
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
            <div className="p-2 bg-purple-100 rounded-lg">
              <BarChart3 className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 4.1: Sentence Pattern Analysis
              </h2>
              <p className="text-sm text-gray-500">
                步骤 4.1: 句式结构分析
              </p>
            </div>
          </div>
          {isAnalyzing && (
            <div className="flex items-center gap-2 text-purple-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing... / 分析中...</span>
            </div>
          )}
        </div>

        <p className="text-gray-600 mb-4">
          Analyzes sentence type distribution, opener repetition, and voice balance across the document.
          <br />
          <span className="text-gray-500">
            分析全文的句式类型分布、句首重复率和语态平衡。
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
                {result.openerAnalysis?.repetitionRate ? `${(result.openerAnalysis.repetitionRate * 100).toFixed(0)}%` : 'N/A'}
              </div>
              <div className="text-sm text-blue-600">Opener Repeat / 句首重复</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-700">
                {result.voiceDistribution?.passive || 0}
              </div>
              <div className="text-sm text-purple-600">Passive / 被动句</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-orange-700">
                {result.highRiskParagraphs?.length || 0}
              </div>
              <div className="text-sm text-orange-600">High Risk Para / 高风险段</div>
            </div>
          </div>
        )}
      </div>

      {/* Start Analysis / Skip Step */}
      {/* 开始分析 / 跳过此步 */}
      {documentText && !analysisStarted && !isAnalyzing && !result && (
        <div className="mb-6 p-6 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="text-center">
            <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Analyze / 准备分析</h3>
            <p className="text-gray-600 mb-6">
              Click "Start Analysis" to analyze sentence patterns, opener repetition, and voice distribution.
              <br />
              <span className="text-gray-500">点击"开始分析"以分析句式模式、句首重复率和语态分布。</span>
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

      {/* Issues Section with Selection */}
      {/* 问题部分（带选择功能） */}
      {patternIssues.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              Detected Issues / 检测到的问题
              <span className="text-sm font-normal text-gray-500">
                ({selectedIssueIndices.size}/{patternIssues.length} selected / 已选择)
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
            {patternIssues.map((issue, idx) => (
              <div key={idx} className="rounded-lg border overflow-hidden">
                {/* Issue item with separate checkbox and content click areas */}
                {/* 问题项，复选框和内容点击区域分开 */}
                <div
                  className={clsx(
                    'flex items-start gap-3 p-3 transition-all',
                    expandedIssueIndex === idx
                      ? 'bg-purple-50 border-b border-purple-200'
                      : selectedIssueIndices.has(idx)
                        ? 'bg-blue-50'
                        : 'bg-white hover:bg-gray-50'
                  )}
                >
                  {/* Checkbox button - only toggles selection */}
                  {/* 复选框按钮 - 仅切换选择 */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleIssueSelection(idx);
                    }}
                    className={clsx(
                      'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors',
                      selectedIssueIndices.has(idx)
                        ? 'bg-blue-600 border-blue-600'
                        : 'border-gray-300 hover:border-blue-400'
                    )}
                  >
                    {selectedIssueIndices.has(idx) && (
                      <Check className="w-3 h-3 text-white" />
                    )}
                  </button>

                  {/* Content area - click to expand/collapse */}
                  {/* 内容区域 - 点击展开/收起 */}
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
                      <span className="text-xs text-gray-500">{issue.layer}</span>
                      {expandedIssueIndex === idx && (
                        <span className="text-xs text-purple-600 ml-auto">Click to collapse / 点击收起</span>
                      )}
                    </div>
                    <p className="text-gray-900 mt-1">{issue.description}</p>
                    <p className="text-gray-600 text-sm">{issue.descriptionZh}</p>
                    {issue.location && (
                      <p className="text-gray-500 text-xs mt-1 font-mono">{issue.location}</p>
                    )}
                  </button>
                </div>

                {/* Expanded content section showing AI suggestions */}
                {/* 展开的内容区域显示AI建议 */}
                {expandedIssueIndex === idx && (
                  <div className="p-4 bg-purple-50 border-t border-purple-200">
                    {isLoadingSuggestion ? (
                      <div className="flex items-center gap-2 text-purple-600">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Loading suggestions... / 加载建议中...</span>
                      </div>
                    ) : suggestionError ? (
                      <div className="text-red-600 text-sm">{suggestionError}</div>
                    ) : issueSuggestion ? (
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
                    ) : (
                      <div className="text-gray-500 text-sm">No suggestions available / 暂无建议</div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons for Selected Issues */}
      {/* 选中问题的操作按钮 */}
      {hasSelectedIssues && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-blue-800 font-medium">
              Actions for {selectedIssueIndices.size} issue(s) / 对{selectedIssueIndices.size}个问题的操作:
            </span>
            <Button
              variant="secondary"
              size="sm"
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

          {'changesSummary' in mergeResult && mergeResult.changesSummary && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-green-800">Changes Summary / 修改摘要:</h5>
              <p className="mt-1 text-green-700">{mergeResult.changesSummary}</p>
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

      {/* Type Distribution Chart */}
      {result && result.typeDistribution && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-600" />
            Type Distribution / 句式类型分布
          </h3>

          <div className="space-y-4">
            {Object.entries(result.typeDistribution).map(([type, stats]) => {
              const percentage = stats.percentage * 100;
              const isRisk = stats.isRisk;
              const threshold = stats.threshold * 100;

              return (
                <div key={type} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={clsx(
                        'w-3 h-3 rounded-full',
                        getTypeColor(type)
                      )} />
                      <span className="text-sm font-medium text-gray-700 capitalize">
                        {type.replace('_', ' ')}
                      </span>
                      {isRisk && (
                        <AlertTriangle className="w-4 h-4 text-yellow-500" />
                      )}
                    </div>
                    <span className="text-sm text-gray-600">
                      {stats.count} ({percentage.toFixed(0)}%)
                      <span className="text-gray-400 ml-1">
                        threshold: {threshold}%
                      </span>
                    </span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={clsx(
                        'h-full rounded-full transition-all',
                        getTypeColor(type),
                        isRisk ? 'opacity-100' : 'opacity-70'
                      )}
                      style={{ width: `${Math.min(percentage, 100)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Opener Analysis */}
      {result && result.openerAnalysis && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Opener Analysis / 句首词分析
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Top Repeated Openers */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Top Repeated Openers / 最常用句首:</h4>
              <div className="flex flex-wrap gap-2">
                {result.openerAnalysis.topRepeated.map((opener, i) => (
                  <span
                    key={i}
                    className={clsx(
                      'px-3 py-1 rounded-full text-sm',
                      i === 0 ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'
                    )}
                  >
                    "{opener}" ({result.openerAnalysis.openerCounts[opener] || 0}x)
                  </span>
                ))}
              </div>
            </div>

            {/* Metrics */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Repetition Rate / 重复率:</span>
                <span className={clsx(
                  'font-medium',
                  result.openerAnalysis.repetitionRate > 0.3 ? 'text-red-600' : 'text-green-600'
                )}>
                  {(result.openerAnalysis.repetitionRate * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Subject-First Rate / 主语开头率:</span>
                <span className={clsx(
                  'font-medium',
                  result.openerAnalysis.subjectOpeningRate > 0.8 ? 'text-red-600' : 'text-green-600'
                )}>
                  {(result.openerAnalysis.subjectOpeningRate * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          {/* Opener Issues */}
          {result.openerAnalysis.issues.length > 0 && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h4 className="text-sm font-medium text-yellow-800 mb-2">Issues:</h4>
              <ul className="space-y-1">
                {result.openerAnalysis.issues.map((issue, i) => (
                  <li key={i} className="text-sm text-yellow-700 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* High Risk Paragraphs */}
      {result && result.highRiskParagraphs && result.highRiskParagraphs.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            High Risk Paragraphs / 高风险段落
          </h3>

          <p className="text-sm text-gray-600 mb-4">
            These paragraphs need processing in the next steps.
            <span className="text-gray-500 ml-1">这些段落需要在后续步骤中处理。</span>
          </p>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-2 text-left">Para</th>
                  <th className="px-4 py-2 text-center">Risk</th>
                  <th className="px-4 py-2 text-center">Simple %</th>
                  <th className="px-4 py-2 text-center">Length CV</th>
                  <th className="px-4 py-2 text-center">Opener Rep</th>
                  <th className="px-4 py-2 text-center">Sentences</th>
                </tr>
              </thead>
              <tbody>
                {result.highRiskParagraphs.map((para) => (
                  <tr key={para.paragraphIndex} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className="w-6 h-6 inline-flex items-center justify-center bg-orange-200 text-orange-700 rounded-full text-xs font-medium">
                        {para.paragraphIndex + 1}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={clsx(
                        'px-2 py-0.5 rounded text-xs font-medium',
                        getRiskColor(para.riskLevel)
                      )}>
                        {para.riskScore}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={para.simpleRatio > 0.6 ? 'text-red-600 font-medium' : ''}>
                        {(para.simpleRatio * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={para.lengthCv < 0.25 ? 'text-red-600 font-medium' : ''}>
                        {para.lengthCv.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={para.openerRepetition > 0.3 ? 'text-red-600 font-medium' : ''}>
                        {(para.openerRepetition * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">{para.sentenceCount}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* No issues message */}
      {patternIssues.length === 0 && result && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-green-800">
              Sentence Patterns Look Good
            </h3>
            <p className="text-green-600 mt-1">
              句式结构良好。未检测到显著的AI特征问题。
            </p>
          </div>
        </div>
      )}

      {/* Document Modification Section */}
      {/* 文档修改部分 */}
      {result && (
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
      )}

      {/* Syntactic Void Detection */}
      {/* 句法空洞检测 */}
      {result && result.syntacticVoids && result.syntacticVoids.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-600" />
            Syntactic Voids Detected / 检测到的句法空洞
            {result.hasCriticalVoid && (
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
                Critical / 严重
              </span>
            )}
          </h3>

          {/* Void Score Summary */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className={clsx(
              'rounded-lg p-4',
              (result.voidScore || 0) > 50 ? 'bg-red-50' : (result.voidScore || 0) > 30 ? 'bg-yellow-50' : 'bg-green-50'
            )}>
              <div className={clsx(
                'text-2xl font-bold',
                (result.voidScore || 0) > 50 ? 'text-red-700' : (result.voidScore || 0) > 30 ? 'text-yellow-700' : 'text-green-700'
              )}>
                {result.voidScore || 0}
              </div>
              <div className="text-sm text-gray-600">Void Score / 空洞分数</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-700">
                {((result.voidDensity || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-purple-600">Void Density / 空洞密度</div>
            </div>
            <div className="bg-amber-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-amber-700">
                {result.syntacticVoids.length}
              </div>
              <div className="text-sm text-amber-600">Patterns Found / 发现模式</div>
            </div>
          </div>

          {/* Void Pattern List */}
          <div className="space-y-3">
            {result.syntacticVoids.slice(0, 10).map((voidMatch: SyntacticVoidMatch, index: number) => (
              <div
                key={index}
                className={clsx(
                  'p-4 rounded-lg border',
                  voidMatch.severity === 'high' ? 'bg-red-50 border-red-200' :
                  voidMatch.severity === 'medium' ? 'bg-yellow-50 border-yellow-200' :
                  'bg-gray-50 border-gray-200'
                )}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={clsx(
                      'px-2 py-0.5 rounded text-xs font-medium',
                      voidMatch.severity === 'high' ? 'bg-red-200 text-red-800' :
                      voidMatch.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                      'bg-gray-200 text-gray-800'
                    )}>
                      {(voidMatch.patternType || 'unknown').replace(/_/g, ' ')}
                    </span>
                    <span className={clsx(
                      'text-xs',
                      voidMatch.severity === 'high' ? 'text-red-600' : 'text-gray-500'
                    )}>
                      {voidMatch.severity}
                    </span>
                  </div>
                </div>
                <div className="font-mono text-sm bg-white p-2 rounded border mb-2">
                  <span className="text-red-600 underline decoration-wavy decoration-red-300">
                    "{voidMatch.matchedText || ''}"
                  </span>
                </div>
                {voidMatch.suggestion && (
                  <div className="flex items-start gap-2 text-sm">
                    <Lightbulb className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="text-gray-700">{voidMatch.suggestion}</span>
                      {voidMatch.suggestionZh && (
                        <span className="text-gray-500 ml-1">/ {voidMatch.suggestionZh}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            {result.syntacticVoids.length > 10 && (
              <p className="text-sm text-gray-500 text-center">
                ... and {result.syntacticVoids.length - 10} more patterns / 还有 {result.syntacticVoids.length - 10} 个模式
              </p>
            )}
          </div>

          <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm text-amber-800">
              <strong>What are Syntactic Voids?</strong> These are "flowery but semantically empty" phrases typical of AI-generated text.
              They sound impressive but lack concrete meaning.
            </p>
            <p className="text-sm text-amber-700 mt-1">
              <strong>什么是句法空洞？</strong> 这些是AI生成文本的典型特征——"华丽但语义空洞"的短语。
              听起来很高级，但缺乏具体含义。
            </p>
          </div>
        </div>
      )}

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
            Previous: Step 4.0
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
