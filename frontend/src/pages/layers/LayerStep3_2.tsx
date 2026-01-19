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
  Link2,
  FileText,
  RefreshCw,
  Users,
  GitBranch,
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
  paragraphLayerApi,
  documentLayerApi,
  ParagraphAnalysisResponse,
  DetectionIssue,
} from '../../services/analysisApi';

/**
 * Layer Step 3.2 - Paragraph Internal Coherence
 * 步骤 3.2 - 段落内部连贯性
 *
 * Analyzes sentence relationships within paragraphs:
 * - Subject diversity (避免重复主语)
 * - Logic structure (线性 vs 层次结构)
 * - Connector density (连接词密度)
 * - First-person usage (第一人称使用)
 *
 * 分析段落内句子关系：
 * - 主语多样性
 * - 逻辑结构
 * - 连接词密度
 * - 第一人称使用率
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

interface LayerStep3_2Props {
  documentIdProp?: string;
  onComplete?: (result: ParagraphAnalysisResponse) => void;
  showNavigation?: boolean;
  sectionContext?: Record<string, unknown>;
}

export default function LayerStep3_2({
  documentIdProp,
  onComplete,
  showNavigation = true,
  sectionContext,
}: LayerStep3_2Props) {
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
      sessionApi.updateStep(sessionId, 'layer3-step3-2').catch(console.error);
    }
  }, [sessionId]);

  const [result, setResult] = useState<ParagraphAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  // Issues derived from analysis result
  // 从分析结果派生的问题列表
  const [structureIssues, setStructureIssues] = useState<DetectionIssue[]>([]);

  // Issue selection for merge modify
  // 用于合并修改的问题选择
  const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());

  // Click-expand state for individual issue analysis
  // 点击展开状态，用于单个问题分析
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

  // Issue suggestion state (LLM-based detailed suggestions)
  // 问题建议状态（基于LLM的详细建议）
  const [issueSuggestion, setIssueSuggestion] = useState<IssueSuggestionResponse | null>(null);
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);

  // Per-issue suggestion cache to avoid redundant API calls
  // 每个问题的建议缓存，避免重复API调用
  const suggestionCacheRef = useRef<Map<number, IssueSuggestionResponse>>(new Map());

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

  // Substep state store for document text handling
  // 子步骤状态存储用于文档文本处理
  const substepStore = useSubstepStateStore();

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
      // Initialize substep store for session if needed
      // 如果需要，为会话初始化子步骤存储
      if (sessionId && substepStore.currentSessionId !== sessionId) {
        await substepStore.initForSession(sessionId);
      }

      // Check previous steps for modified text (step3-1, step3-0, then Layer 4 steps, then Layer 5 steps)
      // 检查前面步骤的修改文本（先检查step3-1, step3-0，再检查第4层，再检查第5层）
      const previousSteps = ['step3-1', 'step3-0',
                            'step2-5', 'step2-4', 'step2-3', 'step2-2', 'step2-1', 'step2-0',
                            'step1-5', 'step1-4', 'step1-3', 'step1-2', 'step1-1'];
      let foundModifiedText: string | null = null;

      for (const stepName of previousSteps) {
        const stepState = substepStore.getState(stepName);
        if (stepState?.modifiedText) {
          console.log(`[LayerStep3_2] Using modified text from ${stepName}`);
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
          setError('Document text not found / 未找到文档文本');
        }
      }
    } catch (err) {
      console.error('Failed to load document:', err);
      setError('Failed to load document / 加载文档失败');
    } finally {
      setIsLoading(false);
    }
  };

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
      const analysisResult = await paragraphLayerApi.analyzeCoherence(documentText, sectionContext);
      setResult(analysisResult);

      // Create issues from analysis result
      // 从分析结果创建问题列表
      const issues: DetectionIssue[] = [];

      // Check for low coherence score
      // 检查低连贯性分数
      if (analysisResult.coherenceScore !== undefined && analysisResult.coherenceScore < 60) {
        issues.push({
          type: 'low_overall_coherence',
          description: `Overall coherence score is low (${analysisResult.coherenceScore.toFixed(1)}/100)`,
          descriptionZh: `整体连贯性分数较低 (${analysisResult.coherenceScore.toFixed(1)}/100)`,
          severity: analysisResult.coherenceScore < 40 ? 'high' : 'medium',
          layer: 'paragraph',
        });
      }

      // Check paragraph details for structure problems
      // 检查段落详情中的结构问题
      if (analysisResult.paragraphDetails) {
        analysisResult.paragraphDetails.forEach((para, index) => {
          // Check for low coherence score in individual paragraphs
          // 检查单个段落的低连贯性分数
          if (para.coherenceScore !== undefined && para.coherenceScore < 0.5) {
            issues.push({
              type: 'low_paragraph_coherence',
              description: `Paragraph ${index + 1} has low coherence (${(para.coherenceScore * 100).toFixed(0)}%)`,
              descriptionZh: `段落${index + 1}连贯性低 (${(para.coherenceScore * 100).toFixed(0)}%)`,
              severity: para.coherenceScore < 0.3 ? 'high' : 'medium',
              layer: 'paragraph',
              position: { paragraphIndex: index },
            });
          }

          // Check for low sentence length CV (uniformity issue)
          // 检查句子长度CV过低（均匀性问题）
          if (para.sentenceLengthCv !== undefined && para.sentenceLengthCv < 0.25) {
            issues.push({
              type: 'uniform_sentence_length',
              description: `Paragraph ${index + 1} has uniform sentence lengths (CV: ${para.sentenceLengthCv.toFixed(2)}) - may appear AI-generated`,
              descriptionZh: `段落${index + 1}句子长度过于均匀 (CV: ${para.sentenceLengthCv.toFixed(2)}) - 可能显得像AI生成`,
              severity: 'medium',
              layer: 'paragraph',
              position: { paragraphIndex: index },
            });
          }

          // Check for paragraph-level issues
          // 检查段落级问题
          if (para.issues && para.issues.length > 0) {
            para.issues.forEach((issue) => {
              issues.push({
                type: 'paragraph_structure_issue',
                description: `Paragraph ${index + 1}: ${issue}`,
                descriptionZh: `段落${index + 1}: ${issue}`,
                severity: 'medium',
                layer: 'paragraph',
                position: { paragraphIndex: index },
              });
            });
          }
        });
      }

      // Check sentence length analysis for uniformity issues
      // 检查句子长度分析中的均匀性问题
      if (analysisResult.sentenceLengthAnalysis) {
        const { meanCv, lowBurstinessParagraphs, uniformLengthRisk } = analysisResult.sentenceLengthAnalysis;

        if (uniformLengthRisk) {
          issues.push({
            type: 'uniform_length_risk',
            description: `Document shows uniform sentence length risk (CV: ${meanCv?.toFixed(2) || 'N/A'})`,
            descriptionZh: `文档存在句子长度均匀风险 (CV: ${meanCv?.toFixed(2) || 'N/A'})`,
            severity: 'high',
            layer: 'paragraph',
          });
        }

        if (lowBurstinessParagraphs && lowBurstinessParagraphs.length > 0) {
          issues.push({
            type: 'low_burstiness',
            description: `${lowBurstinessParagraphs.length} paragraph(s) have low burstiness (uniform rhythm)`,
            descriptionZh: `${lowBurstinessParagraphs.length}个段落的节奏变化较低（过于均匀）`,
            severity: 'medium',
            layer: 'paragraph',
            details: { paragraphs: lowBurstinessParagraphs },
          });
        }
      }

      // Add issues from result if any
      // 添加结果中的问题（如果有）
      if (analysisResult.issues) {
        analysisResult.issues.forEach((issue) => {
          // Avoid duplicates
          // 避免重复
          if (!issues.some(i => i.description === issue.description)) {
            issues.push(issue);
          }
        });
      }

      setStructureIssues(issues);

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

  // Load detailed suggestion for a specific issue (LLM-based) with caching
  // 为特定问题加载详细建议（基于LLM），带缓存
  const loadIssueSuggestion = useCallback(async (index: number) => {
    const issue = structureIssues[index];
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
      const suggestion: IssueSuggestionResponse = {
        analysis: response.diagnosisZh || '',
        suggestions: response.strategies?.map((s: { nameZh?: string; descriptionZh?: string }) => `${s.nameZh}: ${s.descriptionZh}`) || [],
        exampleFix: response.strategies?.[0]?.exampleAfter || '',
      };
      // Store in cache
      // 存入缓存
      suggestionCacheRef.current.set(index, suggestion);
      setIssueSuggestion(suggestion);
    } catch (err) {
      console.error('Failed to load suggestion:', err);
      setSuggestionError('Failed to load detailed suggestion / 加载详细建议失败');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [structureIssues, documentId]);

  // Handle issue click - toggle expand and auto-load suggestion
  // 处理问题点击 - 切换展开并自动加载建议
  const handleIssueClick = useCallback(async (index: number) => {
    const issue = structureIssues[index];
    if (!issue || !documentId) return;

    // Collapse if already expanded
    // 如果已展开则收起
    if (expandedIssueIndex === index) {
      setExpandedIssueIndex(null);
      setIssueSuggestion(null);
      return;
    }

    // Expand and load suggestion (from cache if available)
    // 展开并加载建议（如有缓存则从缓存加载）
    setExpandedIssueIndex(index);
    await loadIssueSuggestion(index);
  }, [structureIssues, documentId, expandedIssueIndex, loadIssueSuggestion]);

  // Toggle issue selection (for checkbox only)
  // 切换问题选择（仅用于复选框）
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
    setSelectedIssueIndices(new Set(structureIssues.map((_, idx) => idx)));
  }, [structureIssues]);

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
      const selectedIssues = Array.from(selectedIssueIndices).map(i => structureIssues[i]);

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
  }, [selectedIssueIndices, documentId, structureIssues, mergeMode, mergeUserNotes, sessionId]);

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
      // Extract modified text from file or text input
      // 从文件或文本输入中提取修改后的文本
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

      // Save modified text to substep store
      // 将修改后的文本保存到子步骤存储
      if (sessionId && modifiedText) {
        await substepStore.saveModifiedText('step3-2', modifiedText);
        await substepStore.markCompleted('step3-2');
        console.log('[LayerStep3_2] Saved modified text to substep store');
      }

      // Navigate to next step
      // 导航到下一步
      const params = new URLSearchParams();
      if (mode) params.set('mode', mode);
      if (sessionId) params.set('session', sessionId);
      navigate(`/flow/layer3-step3-3/${documentId}?${params.toString()}`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload modified document / 上传修改后的文档失败');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate, documentId, substepStore]);

  const goToNextStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-3/${documentId}?${params.toString()}`);
  };

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer3-step3-1/${documentId}?${params.toString()}`);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
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
        <Button onClick={runAnalysis} className="mt-4" variant="outline">
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
            <div className="p-2 bg-green-100 rounded-lg">
              <Link2 className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3.2: Internal Coherence Analysis
              </h2>
              <p className="text-sm text-gray-500">
                步骤 3.2: 段落内部连贯性分析
              </p>
            </div>
          </div>
          {isAnalyzing && (
            <div className="flex items-center gap-2 text-green-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing... / 分析中...</span>
            </div>
          )}
        </div>

        <p className="text-gray-600 mb-4">
          Analyzes logical relationships between sentences within each paragraph. Detects AI-like patterns such as linear structure, subject repetition, and connector stacking.
          <br />
          <span className="text-gray-500">
            分析每个段落内句子之间的逻辑关系。检测AI式模式如线性结构、主语重复和连接词堆砌。
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
                {result.coherenceScore?.toFixed(1) || 'N/A'}
              </div>
              <div className="text-sm text-blue-600">Coherence / 连贯性</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-700">
                {result.paragraphCount || 0}
              </div>
              <div className="text-sm text-purple-600">Paragraphs / 段落数</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-orange-700">
                {structureIssues?.length || 0}
              </div>
              <div className="text-sm text-orange-600">Issues / 问题数</div>
            </div>
          </div>
        )}

        {/* Start Analysis / Skip Step */}
        {/* 开始分析 / 跳过此步 */}
        {documentText && !analysisStarted && !isAnalyzing && !result && (
          <div className="mt-4 p-6 bg-gray-50 border border-gray-200 rounded-lg">
            <div className="text-center">
              <Link2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Analyze / 准备分析</h3>
              <p className="text-gray-600 mb-6">
                Click to analyze internal coherence and detect AI-like patterns
                <br />
                <span className="text-gray-500">点击分析内部连贯性并检测AI式模式</span>
              </p>
              <div className="flex items-center justify-center gap-4">
                <Button variant="primary" size="lg" onClick={() => setAnalysisStarted(true)}>
                  <Sparkles className="w-5 h-5 mr-2" />
                  Start Analysis / 开始分析
                </Button>
                <Button variant="secondary" size="lg" onClick={() => setShowSkipConfirm(true)}>
                  <ArrowRight className="w-5 h-5 mr-2" />
                  Skip Step / 跳过此步
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Issues Section with Selection */}
      {/* 问题部分（带选择功能） */}
      {structureIssues.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              Detected Issues / 检测到的问题
              <span className="text-sm font-normal text-gray-500">
                ({selectedIssueIndices.size}/{structureIssues.length} selected / 已选择)
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
            {structureIssues.map((issue, idx) => (
              <div
                key={idx}
                className={clsx(
                  'rounded-lg border transition-all',
                  selectedIssueIndices.has(idx)
                    ? 'bg-blue-50 border-blue-300 ring-2 ring-blue-200'
                    : expandedIssueIndex === idx
                    ? 'bg-gray-50 border-gray-300'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                )}
              >
                <div className="p-3 flex items-start gap-3">
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
                      <span className="text-xs text-blue-500 ml-auto">
                        {expandedIssueIndex === idx ? '▼ Click to collapse' : '▶ Click for AI analysis'}
                      </span>
                    </div>
                    <p className="text-gray-900 mt-1">{issue.description}</p>
                    <p className="text-gray-600 text-sm">{issue.descriptionZh}</p>
                  </button>
                </div>
                {expandedIssueIndex === idx && (
                  <div className="px-3 pb-3 pt-0 ml-8 border-t border-gray-200">
                    {isLoadingSuggestion ? (
                      <div className="flex items-center gap-2 py-3 text-blue-600">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-sm">Loading AI analysis... / 加载AI分析中...</span>
                      </div>
                    ) : issueSuggestion ? (
                      <div className="py-3 space-y-3">
                        <div>
                          <h5 className="text-sm font-medium text-purple-800">Analysis / 分析:</h5>
                          <p className="text-purple-700 text-sm mt-1">{issueSuggestion.analysis}</p>
                        </div>
                        {issueSuggestion.suggestions && issueSuggestion.suggestions.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium text-purple-800">Suggestions / 建议:</h5>
                            <ul className="list-disc list-inside mt-1 space-y-1">
                              {issueSuggestion.suggestions.map((s, i) => (
                                <li key={i} className="text-purple-700 text-sm">{s}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {issueSuggestion.exampleFix && (
                          <div>
                            <h5 className="text-sm font-medium text-purple-800">Example / 示例:</h5>
                            <pre className="mt-1 p-2 bg-white rounded text-xs text-gray-800 overflow-x-auto">
                              {issueSuggestion.exampleFix}
                            </pre>
                          </div>
                        )}
                        {suggestionCacheRef.current.has(idx) && (
                          <p className="text-xs text-gray-400">✓ Cached / 已缓存</p>
                        )}
                      </div>
                    ) : suggestionError ? (
                      <div className="py-3 text-red-600 text-sm">{suggestionError}</div>
                    ) : null}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons for Selected Issues */}
      {hasSelectedIssues && (
        <div className="mb-6 pb-6 border-b">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">{selectedIssueIndices.size} selected / 已选择 {selectedIssueIndices.size} 个问题</div>
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

      {/* Paragraph Coherence Details */}
      {result && result.paragraphDetails && result.paragraphDetails.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-green-600" />
            Paragraph Coherence Details / 段落连贯性详情
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-2 text-left">Para</th>
                  <th className="px-4 py-2 text-left">Role / 角色</th>
                  <th className="px-4 py-2 text-center">Coherence / 连贯</th>
                  <th className="px-4 py-2 text-center">Length CV</th>
                  <th className="px-4 py-2 text-center">Issues</th>
                  <th className="px-4 py-2 text-center">Status</th>
                </tr>
              </thead>
              <tbody>
                {result.paragraphDetails.map((para, index) => (
                  <tr
                    key={index}
                    className={clsx(
                      'border-t hover:bg-gray-50 cursor-pointer',
                      expandedIndex === index && 'bg-blue-50'
                    )}
                    onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}
                  >
                    <td className="px-4 py-3">
                      <span className="w-6 h-6 inline-flex items-center justify-center bg-gray-200 rounded-full text-xs font-medium">
                        {index + 1}
                      </span>
                    </td>
                    <td className="px-4 py-3">{para.role || 'body'}</td>
                    <td className={clsx('px-4 py-3 text-center font-medium', getScoreColor((para.coherenceScore || 0) * 100))}>
                      {((para.coherenceScore || 0) * 100).toFixed(0)}%
                    </td>
                    <td className={clsx(
                      'px-4 py-3 text-center',
                      (para.sentenceLengthCv || 0) < 0.25 ? 'text-red-600' : 'text-green-600'
                    )}>
                      {(para.sentenceLengthCv || 0).toFixed(2)}
                      {(para.sentenceLengthCv || 0) < 0.25 && (
                        <span className="ml-1 text-xs text-red-500">[!]</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {para.issues?.length || 0}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {!para.issues || para.issues.length === 0 ? (
                        <CheckCircle className="w-4 h-4 text-green-500 inline" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-yellow-500 inline" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {expandedIndex !== null && result.paragraphDetails[expandedIndex] && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-medium text-blue-800 mb-2">
                Paragraph {expandedIndex + 1} Details
              </h4>
              {result.paragraphDetails[expandedIndex].issues && result.paragraphDetails[expandedIndex].issues.length > 0 ? (
                <ul className="space-y-1">
                  {result.paragraphDetails[expandedIndex].issues.map((issue, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-blue-700">
                      <AlertCircle className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                      <span>{issue}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-green-700">No issues detected in this paragraph.</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* No issues message */}
      {structureIssues.length === 0 && result && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-green-800">
              Paragraph Structure Looks Good
            </h3>
            <p className="text-green-600 mt-1">
              段落结构良好。未检测到明显的连贯性问题。
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
                  ? 'bg-green-600 text-white'
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
                  ? 'bg-green-600 text-white'
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
                className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-green-400 hover:bg-green-50 transition-colors"
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 min-h-[200px]"
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
                <span className="text-green-500 mt-1">*</span>
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
            Previous: Step 3.1
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
