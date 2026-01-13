import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  Layers,
  AlertTriangle,
  RefreshCw,
  GitCompare,
  Grid3X3,
  FileText,
  Zap,
  ChevronDown,
  ChevronUp,
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
  sectionLayerApi,
  documentLayerApi,
  InternalStructureSimilarityResponse,
  DetectionIssue,
  IssueSuggestionResponse,
  ModifyPromptResponse,
  ApplyModifyResponse,
} from '../../services/analysisApi';

/**
 * Layer Step 2.3 - Internal Structure Similarity Detection
 * 步骤 2.3 - 章节内部结构相似性检测
 *
 * This is a NEW core detection feature for Layer 4.
 * 这是第4层新增的核心检测功能。
 *
 * Detects:
 * - R: Internal Structure Similarity (章节内部逻辑结构相似性) - NEW
 * - M: Heading Depth Variance (子标题深度变异)
 * - N: Argument Density (章节内论点密度)
 *
 * AI Pattern: AI tends to use the same internal template for all sections
 * AI模式: AI倾向于为所有章节使用相同的内部模板
 */

// Paragraph function types
// 段落功能类型
const PARAGRAPH_FUNCTIONS = {
  topic_sentence: { label: 'Topic', labelZh: '主题句', color: 'blue' },
  evidence: { label: 'Evidence', labelZh: '证据', color: 'green' },
  analysis: { label: 'Analysis', labelZh: '分析', color: 'purple' },
  transition: { label: 'Transition', labelZh: '过渡', color: 'yellow' },
  mini_conclusion: { label: 'Summary', labelZh: '小结', color: 'red' },
  example: { label: 'Example', labelZh: '举例', color: 'orange' },
};

interface LayerStep2_3Props {
  documentIdProp?: string;
  onComplete?: (result: InternalStructureSimilarityResponse) => void;
  showNavigation?: boolean;
}

export default function LayerStep2_3({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerStep2_3Props) {
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
      sessionApi.updateStep(sessionId, 'layer4-step2-3').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [result, setResult] = useState<InternalStructureSimilarityResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [expandedSection, setExpandedSection] = useState<number | null>(null);
  const [showAiSuggestion, setShowAiSuggestion] = useState(false);

  // Issues derived from analysis result
  // 从分析结果派生的问题列表
  const [contentIssues, setContentIssues] = useState<DetectionIssue[]>([]);

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
      const analysisResult = await sectionLayerApi.analyzeSimilarity(
        documentText,
        undefined,
        undefined,
        sessionId || undefined
      );

      setResult(analysisResult);

      // Create issues from analysis result
      // 从分析结果创建问题列表
      const issues: DetectionIssue[] = [];

      // Check for high similarity pairs
      // 检查高相似度对
      if (analysisResult.suspiciousPairs && analysisResult.suspiciousPairs.length > 0) {
        analysisResult.suspiciousPairs.forEach((pair) => {
          issues.push({
            type: 'high_structure_similarity',
            description: `Sections ${pair.sectionAIndex + 1} and ${pair.sectionBIndex + 1} have similar internal structure (${Math.round(pair.structureSimilarity)}%)`,
            descriptionZh: `章节${pair.sectionAIndex + 1}和${pair.sectionBIndex + 1}内部结构相似 (${Math.round(pair.structureSimilarity)}%)`,
            severity: pair.structureSimilarity > 90 ? 'high' : 'medium',
            layer: 'section',
            location: `Section ${pair.sectionAIndex + 1} <-> Section ${pair.sectionBIndex + 1}`,
          });
        });
      }

      // Check for low heading depth variance
      // 检查子标题深度变异过低
      if (analysisResult.headingDepthCv < 0.1) {
        issues.push({
          type: 'uniform_heading_depth',
          description: `Heading depth is too uniform (CV: ${analysisResult.headingDepthCv.toFixed(2)})`,
          descriptionZh: `子标题深度过于统一 (变异系数: ${analysisResult.headingDepthCv.toFixed(2)})`,
          severity: 'medium',
          layer: 'section',
          location: 'All sections',
        });
      }

      // Check for average similarity
      // 检查平均相似度
      if (analysisResult.averageSimilarity > 80) {
        issues.push({
          type: 'high_average_similarity',
          description: `Average structure similarity is high (${analysisResult.averageSimilarity}%) - AI template pattern detected`,
          descriptionZh: `平均结构相似度过高 (${analysisResult.averageSimilarity}%) - 检测到AI模板模式`,
          severity: 'high',
          layer: 'section',
          location: 'Document structure',
        });
      }

      // Add issues from the result if available
      // 如果有结果中的问题也添加进来
      if (analysisResult.issues) {
        issues.push(...analysisResult.issues);
      }

      setContentIssues(issues);

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
      const selectedIssues = Array.from(selectedIssueIndices).map(i => contentIssues[i]);
      const response = await documentLayerApi.getIssueSuggestion(
        documentId,
        selectedIssues[0],
        false
      );
      setIssueSuggestion({
        analysis: response.diagnosisZh || '',
        suggestions: response.strategies?.map(s => `${s.nameZh}: ${s.descriptionZh}`) || [],
        exampleFix: response.strategies?.[0]?.exampleAfter || '',
      });
    } catch (err) {
      console.error('Failed to load suggestion:', err);
      setSuggestionError('Failed to load detailed suggestion / 加载详细建议失败');
    } finally {
      setIsLoadingSuggestion(false);
    }
  }, [selectedIssueIndices, documentId, contentIssues]);

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
      const selectedIssues = Array.from(selectedIssueIndices).map(i => contentIssues[i]);

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
        } as ApplyModifyResponse);
      }
    } catch (err) {
      console.error('Merge modify failed:', err);
      setError('Merge modify failed / 合并修改失败');
    } finally {
      setIsMerging(false);
    }
  }, [selectedIssueIndices, documentId, contentIssues, mergeMode, mergeUserNotes, sessionId]);

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
        const result = await documentApi.uploadText(newText, `step2_3_modified_${Date.now()}.txt`);
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
      navigate(`/flow/layer4-step2-4/${newDocId}?${params.toString()}`);
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
    navigate(`/flow/layer4-step2-2/${documentId}?${params.toString()}`);
  };

  const handleNext = () => {
    const params = new URLSearchParams();
    if (mode) params.set('mode', mode);
    if (sessionId) params.set('session', sessionId);
    navigate(`/flow/layer4-step2-4/${documentId}?${params.toString()}`);
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
  const hasSimilarityIssue = (result?.averageSimilarity || 0) > 80;
  const hasHeadingIssue = (result?.headingDepthCv || 0) < 0.1;

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
          <span className="text-gray-900 font-medium">Step 2.3 内部结构</span>
          <span className="ml-2 px-2 py-0.5 bg-orange-100 text-orange-700 rounded text-xs">NEW</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Internal Structure Similarity Detection
        </h1>
        <p className="text-gray-600 mt-1">
          章节内部结构相似性检测 - 比较不同章节的内部逻辑模式是否高度相似（AI模板特征）
        </p>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            <div>
              <p className="text-blue-800 font-medium">Analyzing internal structures... / 分析内部结构中...</p>
              <p className="text-blue-600 text-sm">Labeling paragraph functions and calculating similarity</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <>
          {/* Summary Stats */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Average Similarity */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasSimilarityIssue ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <GitCompare className={clsx('w-5 h-5', hasSimilarityIssue ? 'text-red-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Avg Similarity / 平均相似度</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasSimilarityIssue ? 'text-red-600' : 'text-green-600'
              )}>
                {result.averageSimilarity}%
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {hasSimilarityIssue ? 'High risk (>80% = AI pattern)' : 'Good diversity (<80%)'}
              </p>
            </div>

            {/* Heading Depth CV */}
            <div className={clsx(
              'p-4 rounded-lg border',
              hasHeadingIssue ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'
            )}>
              <div className="flex items-center gap-2 mb-2">
                <Grid3X3 className={clsx('w-5 h-5', hasHeadingIssue ? 'text-yellow-600' : 'text-green-600')} />
                <span className="font-medium text-gray-900">Heading Depth CV</span>
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                hasHeadingIssue ? 'text-yellow-600' : 'text-green-600'
              )}>
                {result.headingDepthCv.toFixed(2)}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {hasHeadingIssue ? 'Too uniform heading depth' : 'Good depth variety'}
              </p>
            </div>

            {/* Argument Density CV */}
            <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">Argument Density CV</span>
              </div>
              <div className="text-2xl font-bold text-gray-700">
                {result.argumentDensityCv.toFixed(2)}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Variance in argument count
              </p>
            </div>
          </div>

          {/* High Risk Alert */}
          {hasHighRisk && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">
                  High AI Risk: Template-Like Internal Structure
                </h3>
                <p className="text-red-600 mt-1">
                  高AI风险：不同章节的内部逻辑结构高度相似。
                  AI倾向于为所有章节使用相同的"主题句→证据→分析→小结"模板。
                  建议为不同章节采用不同的内部结构。
                </p>
              </div>
            </div>
          )}

          {/* Issues Section with Selection */}
          {/* 问题部分（带选择功能） */}
          {contentIssues.length > 0 && (
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
                {contentIssues.map((issue, idx) => (
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
          {contentIssues.length > 0 && (
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

          {/* Section Structure Comparison */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <GitCompare className="w-5 h-5 text-blue-600" />
              Section Internal Structure / 章节内部结构对比
            </h3>
            <div className="bg-white border rounded-lg divide-y">
              {result.sectionStructures.map((section) => {
                const isExpanded = expandedSection === section.sectionIndex;
                return (
                  <div key={section.sectionIndex}>
                    <button
                      onClick={() => setExpandedSection(isExpanded ? null : section.sectionIndex)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-8 h-8 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-medium">
                          {section.sectionIndex + 1}
                        </span>
                        <div className="text-left">
                          <span className="font-medium text-gray-900">
                            {section.sectionRole.charAt(0).toUpperCase() + section.sectionRole.slice(1).replace('_', ' ')}
                          </span>
                          <div className="flex gap-1 mt-1">
                            {section.functionSequence.map((func, idx) => {
                              const config = PARAGRAPH_FUNCTIONS[func as keyof typeof PARAGRAPH_FUNCTIONS];
                              return (
                                <span
                                  key={idx}
                                  className={clsx(
                                    'px-1.5 py-0.5 rounded text-xs',
                                    `bg-${config?.color || 'gray'}-100 text-${config?.color || 'gray'}-700`
                                  )}
                                >
                                  {config?.label || func}
                                </span>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm text-gray-500">
                          H{section.headingDepth} | {section.argumentCount} args
                        </span>
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                    </button>
                    {isExpanded && (
                      <div className="px-4 py-3 bg-gray-50 border-t">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <h5 className="font-medium text-gray-700 mb-2">Function Sequence / 功能序列</h5>
                            <div className="flex flex-wrap gap-1">
                              {section.functionSequence.map((func, idx) => {
                                const config = PARAGRAPH_FUNCTIONS[func as keyof typeof PARAGRAPH_FUNCTIONS];
                                return (
                                  <span key={idx} className="flex items-center gap-1">
                                    <span
                                      className={clsx(
                                        'px-2 py-1 rounded',
                                        `bg-${config?.color || 'gray'}-100 text-${config?.color || 'gray'}-700`
                                      )}
                                    >
                                      {config?.labelZh || func}
                                    </span>
                                    {idx < section.functionSequence.length - 1 && (
                                      <span className="text-gray-400">→</span>
                                    )}
                                  </span>
                                );
                              })}
                            </div>
                          </div>
                          <div>
                            <h5 className="font-medium text-gray-700 mb-2">Similarity with Others / 与其他章节相似度</h5>
                            <div className="space-y-1">
                              {result.similarityPairs
                                .filter(p => p.sectionAIndex === section.sectionIndex || p.sectionBIndex === section.sectionIndex)
                                .map((pair, idx) => {
                                  const otherIndex = pair.sectionAIndex === section.sectionIndex ? pair.sectionBIndex : pair.sectionAIndex;
                                  return (
                                    <div key={idx} className="flex items-center justify-between">
                                      <span className="text-gray-600">
                                        vs Section {otherIndex + 1}
                                      </span>
                                      <span className={clsx(
                                        'px-2 py-0.5 rounded text-xs',
                                        pair.structureSimilarity > 85 ? 'bg-red-100 text-red-700' :
                                        pair.structureSimilarity > 70 ? 'bg-yellow-100 text-yellow-700' :
                                        'bg-green-100 text-green-700'
                                      )}>
                                        {Math.round(pair.structureSimilarity)}%
                                      </span>
                                    </div>
                                  );
                                })}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Suspicious Pairs */}
          {result.suspiciousPairs.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                Suspicious Similar Pairs / 可疑相似对
              </h3>
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="space-y-2">
                  {result.suspiciousPairs.map((pair, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-white rounded">
                      <span className="text-gray-700">
                        Section {pair.sectionAIndex + 1} ({pair.sectionARole}) &harr; Section {pair.sectionBIndex + 1} ({pair.sectionBRole})
                      </span>
                      <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-sm">
                        {Math.round(pair.structureSimilarity)}% similar
                      </span>
                    </div>
                  ))}
                </div>
                <p className="text-red-600 text-sm mt-3">
                  These section pairs have highly similar internal structures, which is a common AI writing pattern.
                </p>
                <p className="text-red-500 text-sm mt-1">
                  这些章节对具有高度相似的内部结构，这是常见的AI写作模式。
                </p>
              </div>
            </div>
          )}

          {/* No issues message */}
          {contentIssues.length === 0 && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">
                  Internal Structure Looks Good
                </h3>
                <p className="text-green-600 mt-1">
                  章节内部结构差异性良好。未检测到高度相似的结构模式。
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

          {/* AI Suggestions */}
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
                    Structure Differentiation Suggestions / 结构差异化建议
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
            Back: Length Distribution / 上一步：长度分布
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
