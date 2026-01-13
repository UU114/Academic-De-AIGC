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
  RefreshCw,
  GitBranch,
  ListOrdered,
  Shuffle,
  Zap,
  Edit3,
  Sparkles,
  Upload,
  Check,
  X,
  FileText,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { documentApi, sessionApi } from '../../services/api';
import {
  sectionLayerApi,
  documentLayerApi,
  SectionOrderResponse,
  DetectionIssue,
  IssueSuggestionResponse,
  ModifyPromptResponse,
  ApplyModifyResponse,
} from '../../services/analysisApi';

/**
 * Layer Step 2.1 - Section Order & Structure Detection
 * 步骤 2.1 - 章节顺序与结构检测
 *
 * Detects:
 * - B: Predictable Section Order (章节顺序可预测性)
 * - C: Missing Sections (缺失章节检测)
 * - D: Section Function Fusion (章节功能融合度)
 *
 * Priority: (High - depends on correct section identification from Step 2.0)
 * 优先级: (高 - 依赖步骤2.0的正确章节识别)
 */

// Expected academic section order (AI template)
// 期望的学术论文章节顺序（AI模板）
const EXPECTED_ORDER = [
  'introduction',
  'literature_review',
  'methodology',
  'results',
  'discussion',
  'conclusion',
];

const ORDER_LABELS: Record<string, { label: string; labelZh: string }> = {
  introduction: { label: 'Introduction', labelZh: '引言' },
  literature_review: { label: 'Literature Review', labelZh: '文献综述' },
  methodology: { label: 'Methodology', labelZh: '方法论' },
  results: { label: 'Results', labelZh: '结果' },
  discussion: { label: 'Discussion', labelZh: '讨论' },
  conclusion: { label: 'Conclusion', labelZh: '结论' },
};

interface LayerStep2_1Props {
  documentIdProp?: string;
  onComplete?: (result: SectionOrderResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep2_1({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep2_1Props) {
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
      sessionApi.updateStep(sessionId, 'layer4-step2-1').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<SectionOrderResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedIssue, setExpandedIssue] = useState<string | null>(null);
  const [showAiSuggestion, setShowAiSuggestion] = useState(false);

  // Issues derived from analysis result
  // 从分析结果派生的问题列表
  const [sectionIssues, setSectionIssues] = useState<DetectionIssue[]>([]);

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

  // Skip confirmation state
  // 跳过确认状态
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);

  // Document modification state
  // 文档修改状态
  const [modifyMode, setModifyMode] = useState<'file' | 'text'>('file');
  const [newFile, setNewFile] = useState<File | null>(null);
  const [newText, setNewText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isAnalyzingRef = useRef(false);

  // Load document - wait for session fetch to complete first
  // 加载文档 - 首先等待 session 获取完成
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

  // Run analysis
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
      // Call actual API
      // 调用实际API
      const analysisResult = await sectionLayerApi.analyzeOrder(
        documentText,
        undefined,
        undefined,
        sessionId || undefined
      );

      setResult(analysisResult);

      // Create issues from analysis result
      // 从分析结果创建问题列表
      const issues: DetectionIssue[] = [];

      // Always add section order comparison as a selectable issue
      // 始终将章节顺序对比作为可选择的问题
      const detectedOrderStr = analysisResult.orderAnalysis.detectedOrder
        .map(s => ORDER_LABELS[s]?.labelZh || s).join(' → ');
      const expectedOrderStr = EXPECTED_ORDER
        .map(s => ORDER_LABELS[s]?.labelZh || s).join(' → ');

      issues.push({
        type: 'section_order_comparison',
        description: `Detected: ${analysisResult.orderAnalysis.detectedOrder.map(s => ORDER_LABELS[s]?.label || s).join(' → ')} | Expected: Introduction → Literature Review → Methodology → Results → Discussion → Conclusion`,
        descriptionZh: `检测到: ${detectedOrderStr} | 期望: ${expectedOrderStr}`,
        severity: analysisResult.orderAnalysis.orderMatchScore >= 80 ? 'high' :
                  analysisResult.orderAnalysis.orderMatchScore >= 60 ? 'medium' : 'low',
        layer: 'section',
        location: 'Document structure',
        suggestion: 'Consider reordering sections or adding transitional content to make structure less predictable',
        suggestionZh: '考虑重新排列章节或添加过渡内容，使结构不那么可预测',
      });

      // Always add function fusion analysis as a selectable issue
      // 始终将功能融合分析作为可选择的问题
      const fusionScore = analysisResult.orderAnalysis.fusionScore;
      const isIsolated = fusionScore > 50; // Consider isolated if purity > 50%
      issues.push({
        type: 'function_fusion_analysis',
        description: isIsolated
          ? `Section functions are isolated (${fusionScore}% purity) - this is an AI writing pattern`
          : `Section functions have some mixing (${fusionScore}% purity) - more natural pattern`,
        descriptionZh: isIsolated
          ? `章节功能隔离 (${fusionScore}% 纯度) - 这是AI写作的特征`
          : `章节功能有一定融合 (${fusionScore}% 纯度) - 更自然的写作模式`,
        severity: fusionScore > 90 ? 'high' : fusionScore > 70 ? 'medium' : 'low',
        layer: 'section',
        location: 'All sections',
        suggestion: 'Add cross-references between sections, mention methodology in introduction, discuss results in context of literature',
        suggestionZh: '在章节之间添加交叉引用，在引言中预告方法，结合文献讨论结果',
      });

      // Check for missing sections (may actually be positive)
      // 检查缺失章节（实际上可能是正面信号）
      if (analysisResult.orderAnalysis.missingSections.length > 0) {
        issues.push({
          type: 'missing_sections',
          description: `Missing standard sections: ${analysisResult.orderAnalysis.missingSections.join(', ')}`,
          descriptionZh: `缺少标准章节：${analysisResult.orderAnalysis.missingSections.map(s => ORDER_LABELS[s]?.labelZh || s).join(', ')}`,
          severity: 'low',
          layer: 'section',
          location: 'Document structure',
          suggestion: 'Missing sections may indicate more natural writing - this could be positive',
          suggestionZh: '缺少章节可能表示更自然的写作风格 - 这可能是正面信号',
        });
      }

      // Check for predictable order (additional flag)
      // 检查可预测顺序（附加标记）
      if (analysisResult.orderAnalysis.isPredictable) {
        issues.push({
          type: 'predictable_order',
          description: 'Section order follows a predictable academic template pattern',
          descriptionZh: '章节顺序遵循可预测的学术模板模式',
          severity: 'medium',
          layer: 'section',
          location: 'Document structure',
          suggestion: 'Consider inserting a unique section or merging standard sections',
          suggestionZh: '考虑插入独特的章节或合并标准章节',
        });
      }

      setSectionIssues(issues);

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
      const selectedIssues = Array.from(selectedIssueIndices).map(i => sectionIssues[i]);
      const response = await documentLayerApi.getIssueSuggestion(
        documentId,
        selectedIssues[0],
        true
      );
      setIssueSuggestion({
        analysis: response.diagnosisZh || '',
        suggestions: response.strategies?.map(s => s.descriptionZh) || [],
        exampleFix: response.strategies?.[0]?.exampleAfter || '',
      });
    } catch (err) {
      console.error('Failed to load suggestion:', err);
      setSuggestionError('Failed to load detailed suggestion / 加载详细建议失败');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [selectedIssueIndices, documentId, sectionIssues]);

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
      const selectedIssues = Array.from(selectedIssueIndices).map(i => sectionIssues[i]);

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
        });
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
        });
      }
    } catch (err) {
      console.error('Merge modify failed:', err);
      setError('Merge modify failed / 合并修改失败');
    } finally {
      setIsMerging(false);
    }
  }, [selectedIssueIndices, documentId, sectionIssues, mergeMode, mergeUserNotes, sessionId]);

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
        const result = await documentApi.uploadText(newText, `step2_1_modified_${Date.now()}.txt`);
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
      navigate(`/flow/layer4-step2-2/${newDocId}?${params.toString()}`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload modified document / 上传修改后的文档失败');
    } finally {
      setIsUploading(false);
    }
  }, [modifyMode, newFile, newText, mode, sessionId, navigate]);

  // Navigation
  const handleBack = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer4-step2-0/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer4-step2-2/${documentId}?${params.toString()}`);
  };

  const hasSelectedIssues = selectedIssueIndices.size > 0;

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingMessage category="structure" centered />
      </div>
    );
  }

  // Error state
  if (error && !result) {
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

  const hasHighRisk = result?.riskLevel === 'high';
  const hasMissingSections = (result?.orderAnalysis?.missingSections?.length || 0) > 0;
  const hasHighFunctionPurity = (result?.orderAnalysis?.fusionScore || 0) > 90;

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
          <span>Layer 4 / 第4层</span>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Step 2.1 章节顺序</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Section Order & Structure Detection
        </h1>
        <p className="text-gray-600 mt-1">
          章节顺序与结构检测 - 检测章节顺序可预测性、缺失章节和功能融合度
        </p>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing section structure... / 分析章节结构中...</p>
              <p className="text-blue-600 text-sm">Checking order, missing sections, and function fusion</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* Summary Stats */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Order Match Score */}
            <div className={clsx(
              'p-4 rounded-lg border',
              result.orderAnalysis.orderMatchScore >= 80 ? 'bg-red-50 border-red-200' :
              result.orderAnalysis.orderMatchScore >= 60 ? 'bg-yellow-50 border-yellow-200' :
              'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <ListOrdered className={clsx(
                  'w-5 h-5',
                  result.orderAnalysis.orderMatchScore >= 80 ? 'text-red-600' :
                  result.orderAnalysis.orderMatchScore >= 60 ? 'text-yellow-600' : 'text-green-600'
                )} />
                <span className="font-medium text-gray-900">Order Match / 顺序匹配</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                result.orderAnalysis.orderMatchScore >= 80 ? 'text-red-600' :
                result.orderAnalysis.orderMatchScore >= 60 ? 'text-yellow-600' : 'text-green-600'
              )}>
                {result.orderAnalysis.orderMatchScore}%
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {result.orderAnalysis.orderMatchScore >= 80 ? 'High risk (AI template)' :
                 result.orderAnalysis.orderMatchScore >= 60 ? 'Medium risk' : 'Low risk (natural)'}
              </p>
            </div>

            {/* Missing Sections */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasMissingSections ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <Shuffle className={clsx(
                  'w-5 h-5',
                  hasMissingSections ? 'text-blue-600' : 'text-gray-600'
                )} />
                <span className="font-medium text-gray-900">Missing Sections / 缺失章节</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasMissingSections ? 'text-blue-600' : 'text-gray-700'
              )}>
                {result.orderAnalysis.missingSections.length}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {hasMissingSections ? 'Non-standard structure (more human)' : 'Complete standard structure'}
              </p>
            </div>

            {/* Function Fusion */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasHighFunctionPurity ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <GitBranch className={clsx(
                  'w-5 h-5',
                  hasHighFunctionPurity ? 'text-red-600' : 'text-green-600'
                )} />
                <span className="font-medium text-gray-900">Function Purity / 功能纯度</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasHighFunctionPurity ? 'text-red-600' : 'text-green-600'
              )}>
                {result.orderAnalysis.fusionScore}%
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {hasHighFunctionPurity ? 'High risk (isolated functions)' : 'Good (mixed functions)'}
              </p>
            </div>
          </div>

          {/* High Risk Alert */}
          {hasHighRisk && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Predictable Section Structure
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：章节结构高度匹配学术论文模板。
                  建议打乱章节顺序或合并相关内容。
                </p>
              </div>
            </div>
          )}

          {/* Issues Section with Selection */}
          {/* 问题部分（带选择功能） */}
          {sectionIssues.length > 0 && (
            <div className="mb-6">
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
                {sectionIssues.map((issue, idx) => (
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
          {/* 选中问题的操作按钮 - Style matched with LayerStep2_0 */}
          {sectionIssues.length > 0 && (
            <div className="mb-6 pb-6 border-b">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  {selectedIssueIndices.size} selected / 已选择 {selectedIssueIndices.size} 个问题
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={loadIssueSuggestion}
                    disabled={selectedIssueIndices.size === 0 || isLoadingSuggestion}
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
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
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
            <div className="mb-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
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
            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
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
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
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

          {/* Section Order Comparison */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <ListOrdered className="w-5 h-5 text-blue-600" />
              Section Order Comparison / 章节顺序对比
            </h3>
            <div className="bg-white border rounded-lg p-4">
              <div className="grid grid-cols-2 gap-4">
                {/* Detected Order */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Detected Order / 检测到的顺序
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {result.orderAnalysis.detectedOrder.map((section, idx) => (
                      <div key={idx} className="flex items-center gap-1">
                        <span className="w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm">
                          {idx + 1}
                        </span>
                        <span className="text-gray-700">
                          {ORDER_LABELS[section]?.labelZh || section}
                        </span>
                        {idx < result.orderAnalysis.detectedOrder.length - 1 && (
                          <span className="text-gray-400 mx-1">→</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Expected Order */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Expected Template / 期望模板
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {EXPECTED_ORDER.map((section, idx) => {
                      const isPresent = result.orderAnalysis.detectedOrder.includes(section);
                      return (
                        <div key={idx} className="flex items-center gap-1">
                          <span className={clsx(
                            'w-6 h-6 rounded-full flex items-center justify-center text-sm',
                            isPresent ? 'bg-gray-200 text-gray-600' : 'bg-red-100 text-red-600'
                          )}>
                            {idx + 1}
                          </span>
                          <span className={clsx(
                            isPresent ? 'text-gray-500' : 'text-red-600 line-through'
                          )}>
                            {ORDER_LABELS[section]?.labelZh || section}
                          </span>
                          {idx < EXPECTED_ORDER.length - 1 && (
                            <span className="text-gray-400 mx-1">→</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Missing Sections */}
          {hasMissingSections && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Shuffle className="w-5 h-5 text-blue-600" />
                Missing Sections / 缺失章节
                <span className="text-sm font-normal text-gray-500">
                  (This may indicate more human-like writing)
                </span>
              </h3>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex flex-wrap gap-2">
                  {result.orderAnalysis.missingSections.map((section, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                    >
                      {ORDER_LABELS[section]?.labelZh || section}
                    </span>
                  ))}
                </div>
                <p className="text-blue-700 text-sm mt-3">
                  Missing standard sections may actually be a positive sign - human writers often
                  deviate from strict templates.
                </p>
                <p className="text-blue-600 text-sm mt-1">
                  缺少标准章节可能是正面信号 - 人类写作者通常会偏离严格的模板。
                </p>
              </div>
            </div>
          )}

          {/* Function Fusion Details */}
          <div className="mb-6">
            <button
              onClick={() => setExpandedIssue(expandedIssue === 'function' ? null : 'function')}
              className="w-full"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <GitBranch className="w-5 h-5 text-blue-600" />
                  Function Fusion Analysis / 功能融合分析
                </div>
                {expandedIssue === 'function' ? (
                  <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
              </h3>
            </button>
            {expandedIssue === 'function' && (
              <div className="bg-white border rounded-lg p-4">
                {result.orderAnalysis.multiFunctionSections.length > 0 ? (
                  <>
                    <p className="text-gray-700 mb-3">
                      Sections with multi-function content (indicating more natural writing):
                    </p>
                    <p className="text-gray-600 text-sm mb-3">
                      包含多功能内容的章节（表示更自然的写作）：
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {result.orderAnalysis.multiFunctionSections.map((sectionIdx) => (
                        <span
                          key={sectionIdx}
                          className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                        >
                          Section {sectionIdx + 1}
                        </span>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-red-600">
                      All sections have isolated functions - this is an AI writing pattern.
                    </p>
                    <p className="text-red-500 text-sm mt-1">
                      所有章节功能隔离 - 这是AI写作的特征。
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* No issues message */}
          {sectionIssues.length === 0 && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">
                  Section Order Looks Good
                </h3>
                <p className="text-green-600 mt-1">
                  章节顺序良好。未检测到高风险的模板匹配问题。
                </p>
              </div>
            </div>
          )}

          {/* Document Modification Section */}
          {/* 文档修改部分 */}
          <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
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

            {/* Apply and Continue Button - Style matched with LayerStep2_0 */}
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

          {/* AI Suggestion Button */}
          {(result.recommendations.length > 0 || result.recommendationsZh.length > 0) && (
            <div className="mb-6">
              <Button
                variant="secondary"
                onClick={() => setShowAiSuggestion(!showAiSuggestion)}
                className="w-full"
              >
                <Zap className="w-4 h-4 mr-2" />
                {showAiSuggestion ? 'Hide Suggestions' : 'View Suggestions / 查看建议'}
              </Button>
              {showAiSuggestion && (
                <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                  <h4 className="font-medium text-purple-800 mb-2">
                    Structure Improvement Suggestions / 结构改进建议
                  </h4>
                  <ul className="space-y-2 text-purple-700 text-sm">
                    {result.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-purple-500">•</span>
                        <div>
                          <span>{rec}</span>
                          {result.recommendationsZh[idx] && (
                            <span className="block text-purple-600 mt-1">
                              {result.recommendationsZh[idx]}
                            </span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Processing time */}
          {result.processingTimeMs && (
            <p className="text-sm text-gray-500 mb-6">
              Analysis completed in {result.processingTimeMs}ms
            </p>
          )}
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
            Back: Section ID / 上一步：章节识别
          </Button>
          <Button variant="primary" onClick={() => setShowSkipConfirm(true)} disabled={isAnalyzing || !result}>
            Skip and Continue / 跳过并继续
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
