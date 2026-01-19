import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  Loader2,
  Settings,
  Lock,
  Unlock,
  Play,
  Pause,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  GripVertical,
  Zap,
  Target,
  Layers,
  Eye,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import { useSubstepStateStore } from '../../stores/substepStateStore';
import {
  sentenceLayerApi,
  PatternAnalysisResponse,
  DiversificationResponse,
} from '../../services/analysisApi';

/**
 * Layer Step 4 Console - Paragraph Processing Control Center
 * 步骤 4 控制台 - 段落处理控制中心
 *
 * Features:
 * - Paragraph queue with risk indicators
 * - Lock/unlock paragraphs
 * - Processing mode selection per paragraph
 * - Step 4.2-4.5 iteration controls
 * - Real-time processing status
 *
 * 功能：
 * - 段落队列与风险指示
 * - 锁定/解锁段落
 * - 每段落处理模式选择
 * - Step 4.2-4.5 迭代控制
 * - 实时处理状态
 */

interface ParagraphQueueItem {
  index: number;
  originalBlockIndex?: number;  // Original position in allBlocks (for reconstruction)
  text: string;
  preview: string;
  sentenceCount: number;
  simpleRatio: number;
  lengthCv: number;
  openerRepetition: number;
  riskScore: number;
  riskLevel: 'low' | 'medium' | 'high';
  status: 'pending' | 'in_progress' | 'completed' | 'skipped' | 'locked';
  mode: 'auto' | 'merge_only' | 'connector_only' | 'diversify_only' | 'custom';
  currentStep?: string;
  processedText?: string;
  changes?: Array<{ type: string; count: number }>;
}

interface LayerStep4ConsoleProps {
  documentIdProp?: string;
  showNavigation?: boolean;
  onComplete?: () => void;
  patternResult?: PatternAnalysisResponse;
}

export default function LayerStep4Console({
  documentIdProp,
  showNavigation = true,
  onComplete,
  patternResult: initialPatternResult,
}: LayerStep4ConsoleProps) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const sessionId = searchParams.get('session');

  // Helper function to check if documentId is valid
  // 辅助函数：检查documentId是否有效
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

  // Fetch documentId from session if not available
  // 如果documentId不可用，从session获取
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
      sessionApi.updateStep(sessionId, 'layer2-step4-console').catch(console.error);
    }
  }, [sessionId]);

  // Substep state store for caching and persistence
  // 用于缓存和持久化的子步骤状态存储
  const substepStore = useSubstepStateStore();

  const [paragraphQueue, setParagraphQueue] = useState<ParagraphQueueItem[]>([]);
  const [allBlocks, setAllBlocks] = useState<string[]>([]);  // All blocks including titles
  const [blockToQueueMap, setBlockToQueueMap] = useState<Map<number, number>>(new Map());  // Maps block index to queue index
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [patternResult, setPatternResult] = useState<PatternAnalysisResponse | null>(initialPatternResult || null);
  const [expandedParagraph, setExpandedParagraph] = useState<number | null>(null);
  const [selectedParagraphs, setSelectedParagraphs] = useState<Set<number>>(new Set());
  const [currentProcessingIndex, setCurrentProcessingIndex] = useState<number | null>(null);
  const [processingLogs, setProcessingLogs] = useState<string[]>([]);
  const [showPreview, setShowPreview] = useState(true);  // Default to show preview details

  // Load document and run pattern analysis - wait for session fetch to complete first
  // 加载文档并运行模式分析 - 首先等待 session 获取完成
  useEffect(() => {
    if (!sessionFetchAttempted) return;
    if (isValidDocumentId(documentId)) {
      loadDocumentAndAnalyze(documentId!);
    } else {
      setError('Document ID not found. Please start from the document upload page. / 未找到文档ID，请从文档上传页面开始。');
      setIsLoading(false);
    }
  }, [documentId, sessionFetchAttempted]);

  const loadDocumentAndAnalyze = useCallback(async (docId: string) => {
    try {
      setIsLoading(true);

      // Initialize substep store for session if needed
      // 如果需要，为会话初始化子步骤存储
      if (sessionId && substepStore.currentSessionId !== sessionId) {
        await substepStore.initForSession(sessionId);
      }

      // Check previous steps for modified text (step4-1, step4-0 first, then Layer 3 -> Layer 4)
      // 检查先前步骤的修改文本（先检查step4-1, step4-0，然后是层3 -> 层4）
      const previousSteps = [
        'step4-1', 'step4-0',
        'step3-5', 'step3-4', 'step3-3', 'step3-2', 'step3-1', 'step3-0',
        'step2-5', 'step2-4', 'step2-3', 'step2-2', 'step2-1', 'step2-0',
        'step1-5', 'step1-4', 'step1-3', 'step1-2', 'step1-1'
      ];
      let documentText: string | null = null;

      for (const stepName of previousSteps) {
        const stepState = substepStore.getState(stepName);
        if (stepState?.modifiedText) {
          console.log(`[LayerStep4Console] Using modified text from ${stepName}`);
          documentText = stepState.modifiedText;
          break;
        }
      }

      // Fall back to original document text if no modified text found
      // 如果没有找到修改文本，回退到原始文档文本
      if (!documentText) {
        const doc = await documentApi.get(docId);
        if (!doc.originalText) {
          setError('Document text not found / 未找到文档文本');
          return;
        }
        documentText = doc.originalText;
      }

      // Always fetch fresh pattern analysis results
      // 始终获取最新的模式分析结果
      console.log('Fetching pattern analysis for document:', docId);
      const result = await sentenceLayerApi.analyzePatterns(documentText, undefined, sessionId || undefined);
      console.log('Pattern analysis result:', result.highRiskParagraphs?.length, 'paragraphs');
      setPatternResult(result);
      buildParagraphQueue(documentText, result);
    } catch (err) {
      console.error('Failed to load document:', err);
      setError('Failed to load document / 加载文档失败');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, substepStore]);

  // Check if a text block is likely a title/heading (not a content paragraph)
  // 检查文本块是否可能是标题/章节头（而非内容段落）
  const isLikelyTitle = (text: string): boolean => {
    const trimmed = text.trim();
    const wordCount = trimmed.split(/\s+/).length;
    const sentenceCount = trimmed.split(/[.!?]+/).filter(s => s.trim()).length;

    // Title patterns: numbered sections, known headings, short text without sentences
    // 标题模式：编号章节、已知标题词、无完整句子的短文本
    const titlePatterns = [
      /^(Abstract|Introduction|Conclusion|References|Acknowledgments?|Bibliography|Appendix)$/i,
      /^\d+\.?\s+[A-Z]/,  // "1. Introduction", "2 Methods"
      /^\d+\.\d+\.?\s+/,  // "1.1 Background", "2.3.1 Results"
      /^(Chapter|Section|Part)\s+\d/i,
      /^[A-Z][A-Za-z\s:-]{0,50}$/,  // Short capitalized title without punctuation
    ];

    // Check if matches title pattern
    // 检查是否匹配标题模式
    for (const pattern of titlePatterns) {
      if (pattern.test(trimmed)) {
        return true;
      }
    }

    // Very short text (< 10 words) with no complete sentences is likely a title
    // 非常短的文本（<10词）且没有完整句子可能是标题
    if (wordCount < 10 && sentenceCount <= 1 && !trimmed.includes('.')) {
      return true;
    }

    // Single line with no period at end is likely a title
    // 单行且末尾没有句号的可能是标题
    if (!trimmed.includes('\n') && wordCount < 15 && !trimmed.endsWith('.')) {
      return true;
    }

    return false;
  };

  // Build paragraph queue from pattern analysis
  // 从模式分析结果构建段落队列
  const buildParagraphQueue = (text: string, result: PatternAnalysisResponse) => {
    // First try to split by double newlines
    // 首先尝试按双换行分割
    let blocks = text.split(/\n\n+/).filter(p => p.trim().length > 0);

    // If only 1 block, fall back to single newline splitting (for documents without double newlines)
    // 如果只有1个块，回退到单换行分割（用于没有双换行的文档）
    if (blocks.length <= 1 && text.includes('\n')) {
      blocks = text.split(/\n/).filter(p => p.trim().length > 0);
      console.log(`[buildParagraphQueue] Fallback to single newline: ${blocks.length} blocks`);
    }

    // Store all blocks for later reconstruction
    // 保存所有块以便后续重建
    setAllBlocks(blocks);

    // Build mapping from block index to queue index (for content paragraphs only)
    // 构建从块索引到队列索引的映射（仅针对内容段落）
    const blockToQueue = new Map<number, number>();
    let queueIdx = 0;

    const highRiskMap = new Map(
      result.highRiskParagraphs.map(p => [p.paragraphIndex, p])
    );

    const queue: ParagraphQueueItem[] = [];

    blocks.forEach((block, blockIdx) => {
      // Skip titles/headings
      // 跳过标题/章节头
      if (isLikelyTitle(block)) {
        return;
      }

      // Map this block to its queue position
      // 将此块映射到其队列位置
      blockToQueue.set(blockIdx, queueIdx);

      const highRiskInfo = highRiskMap.get(blockIdx);
      const preview = block.length > 100 ? block.substring(0, 100) + '...' : block;
      const sentenceCount = block.split(/[.!?]+/).filter(s => s.trim()).length;

      queue.push({
        index: queueIdx,
        originalBlockIndex: blockIdx,  // Store original block index for reconstruction
        text: block,
        preview,
        sentenceCount,
        simpleRatio: highRiskInfo?.simpleRatio || 0,
        lengthCv: highRiskInfo?.lengthCv || 0.3,
        openerRepetition: highRiskInfo?.openerRepetition || 0,
        riskScore: highRiskInfo?.riskScore || 30,
        riskLevel: (highRiskInfo?.riskLevel as 'low' | 'medium' | 'high') || 'low',
        status: 'pending',
        mode: 'auto',
      });

      queueIdx++;
    });

    setBlockToQueueMap(blockToQueue);

    // Auto-select high-risk paragraphs
    // 自动选择高风险段落
    const highRiskIndices = new Set(
      queue.filter(p => p.riskLevel === 'high' || p.riskLevel === 'medium').map(p => p.index)
    );
    setSelectedParagraphs(highRiskIndices);

    setParagraphQueue(queue);
  };

  // Toggle paragraph selection
  // 切换段落选择
  const toggleParagraphSelection = (index: number) => {
    setSelectedParagraphs(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  // Toggle paragraph lock status
  // 切换段落锁定状态
  const toggleParagraphLock = (index: number) => {
    setParagraphQueue(prev => prev.map(p => {
      if (p.index === index) {
        return {
          ...p,
          status: p.status === 'locked' ? 'pending' : 'locked',
        };
      }
      return p;
    }));
  };

  // Set paragraph processing mode
  // 设置段落处理模式
  const setParagraphMode = (index: number, mode: ParagraphQueueItem['mode']) => {
    setParagraphQueue(prev => prev.map(p => {
      if (p.index === index) {
        return { ...p, mode };
      }
      return p;
    }));
  };

  // Add log message
  // 添加日志消息
  const addLog = useCallback((message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setProcessingLogs(prev => [...prev, `[${timestamp}] ${message}`]);
  }, []);

  // Process a single paragraph through Step 4.2-4.5
  // 处理单个段落通过 Step 4.2-4.5
  const processParagraph = async (para: ParagraphQueueItem): Promise<DiversificationResponse | null> => {
    if (para.status === 'locked' || para.status === 'skipped') {
      addLog(`Skipping paragraph ${para.index + 1} (${para.status})`);
      return null;
    }

    setCurrentProcessingIndex(para.index);
    setParagraphQueue(prev => prev.map(p =>
      p.index === para.index ? { ...p, status: 'in_progress', currentStep: 'Starting...' } : p
    ));

    try {
      let currentText = para.text;
      const mode = para.mode;

      // Step 4.2: Length Analysis
      // 步骤 4.2：句长分析
      if (mode === 'auto' || mode === 'merge_only') {
        addLog(`Paragraph ${para.index + 1}: Analyzing length...`);
        setParagraphQueue(prev => prev.map(p =>
          p.index === para.index ? { ...p, currentStep: 'Step 4.2: Length Analysis' } : p
        ));
        // Use para.index for unique cache key per paragraph
        // 使用 para.index 作为每个段落的唯一缓存键
        await sentenceLayerApi.analyzeLength(currentText, undefined, para.index, sessionId || undefined);
      }

      // Step 4.3: Merge Suggestions
      // 步骤 4.3：合并建议
      if (mode === 'auto' || mode === 'merge_only') {
        addLog(`Paragraph ${para.index + 1}: Generating merge suggestions...`);
        setParagraphQueue(prev => prev.map(p =>
          p.index === para.index ? { ...p, currentStep: 'Step 4.3: Merge Suggestions' } : p
        ));
        // Use para.index for unique cache key per paragraph
        // 使用 para.index 作为每个段落的唯一缓存键
        const mergeResult = await sentenceLayerApi.suggestMerges(currentText, para.index, 2, sessionId || undefined);
        // Apply first merge if available
        // 如果可用，应用第一个合并
        if (mergeResult.candidates && mergeResult.candidates.length > 0) {
          currentText = mergeResult.candidates[0].mergedText || currentText;
          addLog(`Paragraph ${para.index + 1}: Applied merge suggestion`);
        }
      }

      // Step 4.4: Connector Optimization
      if (mode === 'auto' || mode === 'connector_only') {
        addLog(`Paragraph ${para.index + 1}: Optimizing connectors...`);
        setParagraphQueue(prev => prev.map(p =>
          p.index === para.index ? { ...p, currentStep: 'Step 4.4: Connector Optimization' } : p
        ));
        // Use para.index for unique cache key per paragraph
        // 使用 para.index 作为每个段落的唯一缓存键
        const connectorResult = await sentenceLayerApi.optimizeConnectors(currentText, para.index, [], sessionId || undefined);
        if (connectorResult.optimizedText) {
          currentText = connectorResult.optimizedText;
          addLog(`Paragraph ${para.index + 1}: Applied connector optimization`);
        }
      }

      // Step 4.5: Diversification
      // 步骤 4.5：句式多样化
      if (mode === 'auto' || mode === 'diversify_only') {
        addLog(`Paragraph ${para.index + 1}: Diversifying patterns...`);
        setParagraphQueue(prev => prev.map(p =>
          p.index === para.index ? { ...p, currentStep: 'Step 4.5: Diversification' } : p
        ));
        // Use para.index for unique cache key per paragraph
        // 使用 para.index 作为每个段落的唯一缓存键
        const diversifyResult = await sentenceLayerApi.diversifyPatterns(
          currentText,
          para.index,
          'moderate',
          undefined,
          sessionId || undefined
        );

        // Update paragraph with result
        // 用结果更新段落
        setParagraphQueue(prev => prev.map(p => {
          if (p.index === para.index) {
            return {
              ...p,
              status: 'completed',
              currentStep: 'Completed',
              processedText: diversifyResult.diversifiedText,
              changes: Object.entries(diversifyResult.appliedStrategies).map(([type, count]) => ({
                type,
                count: count as number,
              })),
            };
          }
          return p;
        }));

        addLog(`Paragraph ${para.index + 1}: Completed with ${diversifyResult.changes.length} changes`);
        return diversifyResult;
      }

      // Mark as completed if not auto mode
      // 如果不是自动模式，标记为完成
      setParagraphQueue(prev => prev.map(p =>
        p.index === para.index ? { ...p, status: 'completed', currentStep: 'Completed' } : p
      ));

      return null;
    } catch (err) {
      console.error(`Error processing paragraph ${para.index}:`, err);
      addLog(`Paragraph ${para.index + 1}: Error - ${err instanceof Error ? err.message : 'Unknown error'}`);
      setParagraphQueue(prev => prev.map(p =>
        p.index === para.index ? { ...p, status: 'pending', currentStep: 'Error' } : p
      ));
      return null;
    }
  };

  // Start processing selected paragraphs
  // 开始处理选中的段落
  const startProcessing = async () => {
    if (selectedParagraphs.size === 0) {
      setError('Please select at least one paragraph / 请至少选择一个段落');
      return;
    }

    setIsProcessing(true);
    setIsPaused(false);
    setProcessingLogs([]);
    addLog('Starting paragraph processing...');

    const paragraphsToProcess = paragraphQueue
      .filter(p => selectedParagraphs.has(p.index) && p.status !== 'locked')
      .sort((a, b) => b.riskScore - a.riskScore); // Process highest risk first

    try {
      for (const para of paragraphsToProcess) {
        await processParagraph(para);
      }
      addLog('Processing completed');
    } catch (err) {
      console.error('Processing error:', err);
      addLog(`Processing error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      // Always reset processing state when done
      // 处理完成后始终重置处理状态
      setIsProcessing(false);
      setCurrentProcessingIndex(null);
    }

    // Check if all selected are completed
    // 检查是否所有选中的都已完成
    const allCompleted = paragraphsToProcess.every(p => {
      const current = paragraphQueue.find(q => q.index === p.index);
      return current?.status === 'completed';
    });

    if (allCompleted && onComplete) {
      onComplete();
    }
  };

  // Pause/Resume processing
  // 暂停/恢复处理
  const togglePause = () => {
    setIsPaused(!isPaused);
  };


  // Navigation
  // 导航
  const handleSaveAndContinue = useCallback(async () => {
    // If no paragraphs were processed, just go to next step
    // 如果没有处理任何段落，直接进入下一步
    const anyProcessed = paragraphQueue.some(p => p.status === 'completed' && p.processedText);

    if (!anyProcessed) {
      const params = new URLSearchParams(searchParams);
      navigate(`/flow/layer1-lexical-v2/${documentId}?${params.toString()}`);
      return;
    }

    try {
      setIsSaving(true);
      addLog('Saving modified document...');

      // Reconstruct full document with titles preserved
      // 重建完整文档，保留标题
      const reconstructedBlocks = [...allBlocks];

      // Replace processed paragraphs in their original positions
      // 在原始位置替换已处理的段落
      for (const para of paragraphQueue) {
        if (para.originalBlockIndex !== undefined && para.status === 'completed' && para.processedText) {
          reconstructedBlocks[para.originalBlockIndex] = para.processedText;
        }
      }

      const fullText = reconstructedBlocks.join('\n\n');
      console.log('[LayerStep4Console] Reconstructed document with', reconstructedBlocks.length, 'blocks');

      // Save modified text to substep store for next step to use
      // 将修改后的文本保存到子步骤存储，供下一步使用
      if (sessionId && fullText) {
        await substepStore.saveModifiedText('step4-console', fullText);
        await substepStore.markCompleted('step4-console');
        console.log('[LayerStep4Console] Saved modified text to substep store');
      }

      const params = new URLSearchParams(searchParams);
      addLog('Document saved. Moving to Layer 1...');

      // Navigate to Layer 1 Lexical V2 analysis with current documentId
      // 使用当前的 documentId 导航到 Layer 1 词汇分析V2
      navigate(`/flow/layer1-lexical-v2/${documentId}?${params.toString()}`);
    } catch (err) {
      console.error('Failed to save document:', err);
      setError('Failed to save modified document / 保存修改后的文档失败');
    } finally {
      setIsSaving(false);
    }
  }, [paragraphQueue, allBlocks, searchParams, documentId, sessionId, substepStore, navigate, addLog]);

  const goToPreviousStep = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer2-step4-1/${documentId}?${params.toString()}`);
  };

  // Skip without saving and go to next step
  // 跳过不保存，直接进入下一步
  const skipAndContinue = () => {
    const params = new URLSearchParams(searchParams);
    navigate(`/flow/layer1-lexical-v2/${documentId}?${params.toString()}`);
  };

  // Risk color helper
  // 风险颜色辅助函数
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100 border-green-200';
      case 'medium': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'high': return 'text-red-600 bg-red-100 border-red-200';
      default: return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'in_progress': return 'text-blue-600 bg-blue-100';
      case 'locked': return 'text-gray-600 bg-gray-100';
      case 'skipped': return 'text-gray-400 bg-gray-50';
      default: return 'text-yellow-600 bg-yellow-100';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage category="general" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center gap-2 text-red-700">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
        <Button onClick={() => loadDocumentAndAnalyze(documentId!)} className="mt-4" variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry / 重试
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Layers className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 4 Console: Paragraph Processing
              </h2>
              <p className="text-sm text-gray-500">
                控制台：段落处理中心
              </p>
            </div>
          </div>
        </div>

        <p className="text-gray-600 mb-4">
          Select paragraphs and configure processing mode for each. High-risk paragraphs are pre-selected.
          <br />
          <span className="text-gray-500">
            选择段落并为每个段落配置处理模式。高风险段落已预选。
          </span>
        </p>

        {/* Summary Stats */}
        {patternResult && (
          <div className="grid grid-cols-4 gap-4 mt-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-700">{paragraphQueue.length}</div>
              <div className="text-sm text-blue-600">Total / 总数</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-red-700">
                {paragraphQueue.filter(p => p.riskLevel === 'high').length}
              </div>
              <div className="text-sm text-red-600">High Risk / 高风险</div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-yellow-700">
                {paragraphQueue.filter(p => p.riskLevel === 'medium').length}
              </div>
              <div className="text-sm text-yellow-600">Medium Risk / 中风险</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-700">
                {paragraphQueue.filter(p => p.status === 'completed').length}
              </div>
              <div className="text-sm text-green-600">Completed / 已完成</div>
            </div>
          </div>
        )}
      </div>

      {/* Paragraph Queue */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Target className="w-5 h-5 text-purple-600" />
          Paragraph Queue / 段落队列
        </h3>

        <div className="space-y-3">
          {paragraphQueue.map((para) => (
            <div
              key={para.index}
              className={clsx(
                'border rounded-lg overflow-hidden transition-all',
                currentProcessingIndex === para.index && 'ring-2 ring-blue-500',
                para.status === 'locked' && 'opacity-60'
              )}
            >
              {/* Paragraph Header */}
              <div
                className={clsx(
                  'flex items-center gap-3 p-4 cursor-pointer',
                  para.status === 'completed' ? 'bg-green-50' : 'bg-gray-50'
                )}
                onClick={() => setExpandedParagraph(expandedParagraph === para.index ? null : para.index)}
              >
                {/* Drag Handle */}
                <GripVertical className="w-4 h-4 text-gray-400" />

                {/* Selection Checkbox */}
                <input
                  type="checkbox"
                  checked={selectedParagraphs.has(para.index)}
                  onChange={() => toggleParagraphSelection(para.index)}
                  onClick={(e) => e.stopPropagation()}
                  className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                  disabled={para.status === 'locked'}
                />

                {/* Paragraph Number */}
                <span className="w-8 h-8 flex items-center justify-center bg-blue-200 text-blue-700 rounded-full font-medium">
                  {para.index + 1}
                </span>

                {/* Preview */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-700 truncate">{para.preview}</p>
                  <p className="text-xs text-gray-500">{para.sentenceCount} sentences</p>
                </div>

                {/* Risk Badge */}
                <span className={clsx(
                  'px-2 py-1 text-xs font-medium rounded border',
                  getRiskColor(para.riskLevel)
                )}>
                  {para.riskScore}
                </span>

                {/* Status Badge */}
                <span className={clsx(
                  'px-2 py-1 text-xs font-medium rounded',
                  getStatusColor(para.status)
                )}>
                  {para.status}
                </span>

                {/* Lock Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleParagraphLock(para.index);
                  }}
                  className="p-1.5 hover:bg-gray-200 rounded"
                  disabled={isProcessing}
                >
                  {para.status === 'locked' ? (
                    <Lock className="w-4 h-4 text-gray-500" />
                  ) : (
                    <Unlock className="w-4 h-4 text-gray-400" />
                  )}
                </button>

                {/* Expand Icon */}
                {expandedParagraph === para.index ? (
                  <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
              </div>

              {/* Expanded Content */}
              {expandedParagraph === para.index && (
                <div className="p-4 border-t bg-white">
                  {/* Full Text */}
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Original Text / 原文:</h4>
                    <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">{para.text}</p>
                  </div>

                  {/* Processed Text (if available) */}
                  {para.processedText && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-green-700 mb-2">
                        Processed Text / 处理后文本:
                      </h4>
                      <p className="text-sm text-gray-600 bg-green-50 p-3 rounded border border-green-200">
                        {para.processedText}
                      </p>
                    </div>
                  )}

                  {/* Risk Details */}
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="p-3 bg-gray-50 rounded">
                      <div className="text-lg font-semibold text-gray-700">
                        {(para.simpleRatio * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-gray-500">Simple Ratio / 简单句比例</div>
                    </div>
                    <div className="p-3 bg-gray-50 rounded">
                      <div className="text-lg font-semibold text-gray-700">
                        {para.lengthCv.toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-500">Length CV / 长度CV</div>
                    </div>
                    <div className="p-3 bg-gray-50 rounded">
                      <div className="text-lg font-semibold text-gray-700">
                        {(para.openerRepetition * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-gray-500">Opener Repetition / 句首重复</div>
                    </div>
                  </div>

                  {/* Mode Selection */}
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                      <Settings className="w-4 h-4" />
                      Processing Mode / 处理模式:
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {(['auto', 'merge_only', 'connector_only', 'diversify_only'] as const).map((mode) => (
                        <button
                          key={mode}
                          onClick={() => setParagraphMode(para.index, mode)}
                          className={clsx(
                            'px-3 py-1.5 text-sm rounded-lg border transition-colors',
                            para.mode === mode
                              ? 'bg-purple-100 border-purple-300 text-purple-700'
                              : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                          )}
                          disabled={para.status === 'locked' || isProcessing}
                        >
                          {mode === 'auto' && <Zap className="w-3 h-3 inline mr-1" />}
                          {mode.replace('_', ' ')}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Changes Summary */}
                  {para.changes && para.changes.length > 0 && (
                    <div className="p-3 bg-green-50 rounded border border-green-200">
                      <h4 className="text-sm font-medium text-green-700 mb-2">
                        Applied Changes / 应用的更改:
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {para.changes.map((change, idx) => (
                          <span key={idx} className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">
                            {change.type}: {change.count}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Current Step Indicator */}
                  {para.currentStep && para.status === 'in_progress' && (
                    <div className="mt-4 flex items-center gap-2 text-blue-600">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm">{para.currentStep}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Processing Logs */}
      {processingLogs.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-600" />
            Processing Log / 处理日志
          </h3>
          <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm max-h-60 overflow-y-auto">
            {processingLogs.map((log, idx) => (
              <div key={idx} className="py-0.5">{log}</div>
            ))}
          </div>
        </div>
      )}

      {/* Batch Actions */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Batch Actions / 批量操作</h3>
        <div className="flex flex-wrap gap-3">
          <Button
            variant="outline"
            onClick={() => setSelectedParagraphs(new Set(paragraphQueue.map(p => p.index)))}
            disabled={isProcessing}
          >
            Select All / 全选
          </Button>
          <Button
            variant="outline"
            onClick={() => setSelectedParagraphs(new Set())}
            disabled={isProcessing}
          >
            Deselect All / 取消全选
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              const highRisk = paragraphQueue.filter(p => p.riskLevel === 'high' || p.riskLevel === 'medium');
              setSelectedParagraphs(new Set(highRisk.map(p => p.index)));
            }}
            disabled={isProcessing}
          >
            Select High Risk / 选择高风险
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              const indices = Array.from(selectedParagraphs);
              setParagraphQueue(prev => prev.map(p =>
                indices.includes(p.index) ? { ...p, mode: 'auto' } : p
              ));
            }}
            disabled={isProcessing}
          >
            Set All to Auto / 全部设为自动
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              setParagraphQueue(prev => prev.map(p =>
                p.status === 'completed' ? { ...p, status: 'pending', processedText: undefined, changes: undefined } : p
              ));
            }}
            disabled={isProcessing}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Reset Completed / 重置已完成
          </Button>
        </div>

        {/* Processing Controls */}
        <div className="flex items-center justify-end gap-3 mt-4 pt-4 border-t">
          {isProcessing ? (
            <>
              <Button variant="outline" onClick={togglePause}>
                {isPaused ? <Play className="w-4 h-4 mr-2" /> : <Pause className="w-4 h-4 mr-2" />}
                {isPaused ? 'Resume / 继续' : 'Pause / 暂停'}
              </Button>
              <div className="flex items-center gap-2 text-blue-600">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Processing... / 处理中...</span>
              </div>
            </>
          ) : (
            <Button
              onClick={startProcessing}
              disabled={selectedParagraphs.size === 0}
              className="bg-purple-600 hover:bg-purple-700"
            >
              <Play className="w-4 h-4 mr-2" />
              Start Processing / 开始处理 ({selectedParagraphs.size})
            </Button>
          )}
        </div>
      </div>

      {/* Preview Changes Section - shows after processing */}
      {/* 预览修改部分 - 处理完成后显示 */}
      {paragraphQueue.some(p => p.status === 'completed' && p.processedText) && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Eye className="w-5 h-5 text-blue-600" />
              Preview Changes / 预览修改
            </h3>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={() => setShowPreview(!showPreview)}
                className="text-sm"
              >
                {showPreview ? 'Hide Preview / 隐藏预览' : 'Show Preview / 显示预览'}
              </Button>
              <Button
                onClick={handleSaveAndContinue}
                disabled={isSaving || isProcessing}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
              >
                {isSaving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <ArrowRight className="w-4 h-4" />
                )}
                {isSaving ? 'Saving...' : 'Save & Next / 保存并进行下一步'}
              </Button>
            </div>
          </div>

          {/* Summary of changes */}
          <div className="mb-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-700">
              <span className="font-semibold">
                {paragraphQueue.filter(p => p.status === 'completed' && p.processedText).length}
              </span> paragraphs processed / 已处理段落
            </p>
          </div>

          {/* Detailed Preview */}
          {showPreview && (
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {paragraphQueue
                .filter(p => p.status === 'completed' && p.processedText)
                .map((para) => (
                  <div key={para.index} className="border rounded-lg overflow-hidden">
                    <div className="bg-gray-100 px-4 py-2 border-b">
                      <span className="font-medium text-gray-700">
                        Paragraph {para.index + 1} / 第 {para.index + 1} 段
                      </span>
                      <span className="ml-2 text-sm text-gray-500">
                        ({para.changes?.reduce((sum, c) => sum + c.count, 0) || 0} changes)
                      </span>
                    </div>
                    <div className="grid grid-cols-2 divide-x">
                      {/* Original */}
                      <div className="p-4">
                        <h5 className="text-xs font-medium text-red-600 mb-2 uppercase">
                          Original / 原文
                        </h5>
                        <p className="text-sm text-gray-600 whitespace-pre-wrap leading-relaxed">
                          {para.text}
                        </p>
                      </div>
                      {/* Modified */}
                      <div className="p-4 bg-green-50">
                        <h5 className="text-xs font-medium text-green-600 mb-2 uppercase">
                          Modified / 修改后
                        </h5>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                          {para.processedText}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      {showNavigation && (
        <div className="flex justify-between items-center pt-4 border-t">
          <Button variant="outline" onClick={goToPreviousStep} className="flex items-center gap-2" disabled={isSaving || isProcessing}>
            <ArrowLeft className="w-4 h-4" />
            Previous: Pattern Analysis
          </Button>
          <Button
            variant="outline"
            onClick={skipAndContinue}
            disabled={isProcessing}
            className="flex items-center gap-2"
          >
            <ArrowRight className="w-4 h-4" />
            Skip & Next / 跳过并进行下一步
          </Button>
        </div>
      )}
    </div>
  );
}
