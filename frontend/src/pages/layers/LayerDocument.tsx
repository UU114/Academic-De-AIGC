import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  FileText,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Layers,
  BarChart3,
  Target,
  Link2,
  AlertTriangle,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import {
  documentLayerApi,
  DocumentAnalysisResponse,
  DetectionIssue,
  ConnectorAnalysisResponse,
  TransitionResult,
  ParagraphLengthAnalysisResponse,
  ParagraphLengthInfo,
  ProgressionClosureResponse,
  ProgressionMarker,
  ContentSubstantialityResponse,
  ParagraphSubstantiality,
} from '../../services/analysisApi';

/**
 * Layer Document (Layer 5) - Document Structure Analysis
 * 文章层（第5层）- 文档结构分析
 *
 * Steps:
 * - Step 1.1: Structure Analysis (结构分析)
 * - Step 1.2: Global Risk Assessment (全局风险评估)
 *
 * Part of the 5-layer detection architecture.
 * 5层检测架构的一部分。
 */

// Predictability dimension name mapping (English to Chinese)
// 可预测性维度名称映射（英文到中文）
const DIMENSION_LABELS: Record<string, string> = {
  'Progression': '递进性 Progression',
  'Uniformity': '均匀性 Uniformity',
  'Closure': '闭合性 Closure',
  'Length': '段落长度 Length',
  'Connectors': '连接词 Connectors',
  'progression': '递进性 Progression',
  'uniformity': '均匀性 Uniformity',
  'closure': '闭合性 Closure',
  'length': '段落长度 Length',
  'connectors': '连接词 Connectors',
};

interface LayerDocumentProps {
  // Optional document ID from props (useful for embedded use)
  // 可选的文档ID（用于嵌入使用）
  documentIdProp?: string;
  // Callback when layer analysis completes
  // 层分析完成时的回调
  onComplete?: (result: DocumentAnalysisResponse) => void;
  // Whether to show navigation buttons
  // 是否显示导航按钮
  showNavigation?: boolean;
}

export default function LayerDocument({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerDocumentProps) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Processing mode and session from URL parameter
  // 从URL参数获取处理模式和会话ID
  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // Update session step on mount
  // 挂载时更新会话步骤
  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer-document').catch(console.error);
    }
  }, [sessionId]);

  // Analysis state
  // 分析状态
  const [result, setResult] = useState<DocumentAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<'1.1' | '1.2' | '1.3' | '1.4' | '1.5'>('1.1');

  // Step 1.4: Connector analysis state
  // 步骤 1.4：连接词分析状态
  const [connectorResult, setConnectorResult] = useState<ConnectorAnalysisResponse | null>(null);
  const [isLoadingConnectors, setIsLoadingConnectors] = useState(false);
  const [expandedTransitionIndex, setExpandedTransitionIndex] = useState<number | null>(null);

  // Step 1.2: Paragraph length analysis state
  // 步骤 1.2：段落长度分析状态
  const [paragraphLengthResult, setParagraphLengthResult] = useState<ParagraphLengthAnalysisResponse | null>(null);
  const [isLoadingParagraphLength, setIsLoadingParagraphLength] = useState(false);
  const [expandedParagraphIndex, setExpandedParagraphIndex] = useState<number | null>(null);

  // Step 1.3: Progression & Closure state
  // 步骤 1.3：推进模式与闭合状态
  const [progressionClosureResult, setProgressionClosureResult] = useState<ProgressionClosureResponse | null>(null);
  const [isLoadingProgressionClosure, setIsLoadingProgressionClosure] = useState(false);

  // Step 1.5: Content Substantiality state
  // 步骤 1.5：内容实质性状态
  const [substantialityResult, setSubstantialityResult] = useState<ContentSubstantialityResponse | null>(null);
  const [isLoadingSubstantiality, setIsLoadingSubstantiality] = useState(false);
  const [expandedSubstantialityIndex, setExpandedSubstantialityIndex] = useState<number | null>(null);

  // Document text for analysis
  // 用于分析的文档文本
  const [documentText, setDocumentText] = useState<string>('');

  // Issue expansion state
  // 问题展开状态
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

  // Prevent duplicate API calls
  // 防止重复API调用
  const isAnalyzingRef = useRef(false);

  // Load document text
  // 加载文档文本
  useEffect(() => {
    if (documentId) {
      loadDocumentText(documentId);
    }
  }, [documentId]);

  // Load document text from API
  // 从API加载文档文本
  const loadDocumentText = async (docId: string) => {
    try {
      const doc = await documentApi.get(docId);
      // Use originalText field from API (camelCase transformed from original_text)
      // 使用API返回的originalText字段（从original_text转换为驼峰命名）
      if (doc.originalText) {
        setDocumentText(doc.originalText);
      } else {
        console.error('Document has no original text');
        setError('Document text not found');
      }
    } catch (err) {
      console.error('Failed to load document:', err);
      setError('Failed to load document');
    }
  };

  // Analyze document when text is loaded
  // 当文本加载完成时分析文档
  useEffect(() => {
    if (documentText && !isAnalyzingRef.current) {
      analyzeDocument();
    }
  }, [documentText]);

  // Perform document analysis
  // 执行文档分析
  const analyzeDocument = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;

    setIsLoading(true);
    setError(null);

    try {
      console.log('Layer 5: Analyzing document structure...');

      // Run full document analysis (combines Step 1.1 and 1.2)
      // 运行完整的文档分析（结合步骤1.1和1.2）
      const analysisResult = await documentLayerApi.analyze(documentText);
      console.log('Layer 5 result:', analysisResult);

      setResult(analysisResult);

      // Notify parent if callback provided
      // 如果提供了回调则通知父组件
      if (onComplete) {
        onComplete(analysisResult);
      }
    } catch (err: unknown) {
      console.error('Document analysis failed:', err);
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.data?.detail) {
        setError(axiosErr.response.data.detail);
      } else {
        setError(err instanceof Error ? err.message : 'Analysis failed');
      }
    } finally {
      setIsLoading(false);
      isAnalyzingRef.current = false;
    }
  };

  // Load connector analysis when Step 1.4 is selected
  // 当选择步骤1.4时加载连接词分析
  useEffect(() => {
    if (currentStep === '1.4' && documentText && !connectorResult && !isLoadingConnectors) {
      loadConnectorAnalysis();
    }
  }, [currentStep, documentText]);

  // Load paragraph length analysis when Step 1.2 is selected
  // 当选择步骤1.2时加载段落长度分析
  useEffect(() => {
    if (currentStep === '1.2' && documentText && !paragraphLengthResult && !isLoadingParagraphLength) {
      loadParagraphLengthAnalysis();
    }
  }, [currentStep, documentText]);

  // Load connector analysis
  // 加载连接词分析
  const loadConnectorAnalysis = async () => {
    if (!documentText || isLoadingConnectors) return;

    setIsLoadingConnectors(true);
    try {
      console.log('Step 1.4: Analyzing connectors and transitions...');
      const result = await documentLayerApi.analyzeConnectors(documentText, sessionId || undefined);
      console.log('Step 1.4 result:', result);
      setConnectorResult(result);
    } catch (err) {
      console.error('Connector analysis failed:', err);
      setError(err instanceof Error ? err.message : 'Connector analysis failed');
    } finally {
      setIsLoadingConnectors(false);
    }
  };

  // Load paragraph length analysis
  // 加载段落长度分析
  const loadParagraphLengthAnalysis = async () => {
    if (!documentText || isLoadingParagraphLength) return;

    setIsLoadingParagraphLength(true);
    try {
      console.log('Step 1.2: Analyzing paragraph length regularity...');
      const result = await documentLayerApi.analyzeParagraphLength(documentText, sessionId || undefined);
      console.log('Step 1.2 result:', result);
      setParagraphLengthResult(result);
    } catch (err) {
      console.error('Paragraph length analysis failed:', err);
      setError(err instanceof Error ? err.message : 'Paragraph length analysis failed');
    } finally {
      setIsLoadingParagraphLength(false);
    }
  };

  // Load progression & closure analysis when Step 1.3 is selected
  // 当选择步骤1.3时加载推进与闭合分析
  useEffect(() => {
    if (currentStep === '1.3' && documentText && !progressionClosureResult && !isLoadingProgressionClosure) {
      loadProgressionClosureAnalysis();
    }
  }, [currentStep, documentText]);

  // Load progression & closure analysis
  // 加载推进与闭合分析
  const loadProgressionClosureAnalysis = async () => {
    if (!documentText || isLoadingProgressionClosure) return;

    setIsLoadingProgressionClosure(true);
    try {
      console.log('Step 1.3: Analyzing progression & closure...');
      const result = await documentLayerApi.analyzeProgressionClosure(documentText, sessionId || undefined);
      console.log('Step 1.3 result:', result);
      setProgressionClosureResult(result);
    } catch (err) {
      console.error('Progression/closure analysis failed:', err);
      setError(err instanceof Error ? err.message : 'Progression/closure analysis failed');
    } finally {
      setIsLoadingProgressionClosure(false);
    }
  };

  // Load content substantiality analysis when Step 1.5 is selected
  // 当选择步骤1.5时加载内容实质性分析
  useEffect(() => {
    if (currentStep === '1.5' && documentText && !substantialityResult && !isLoadingSubstantiality) {
      loadSubstantialityAnalysis();
    }
  }, [currentStep, documentText]);

  // Load content substantiality analysis
  // 加载内容实质性分析
  const loadSubstantialityAnalysis = async () => {
    if (!documentText || isLoadingSubstantiality) return;

    setIsLoadingSubstantiality(true);
    try {
      console.log('Step 1.5: Analyzing content substantiality...');
      const result = await documentLayerApi.analyzeContentSubstantiality(documentText, sessionId || undefined);
      console.log('Step 1.5 result:', result);
      setSubstantialityResult(result);
    } catch (err) {
      console.error('Content substantiality analysis failed:', err);
      setError(err instanceof Error ? err.message : 'Content substantiality analysis failed');
    } finally {
      setIsLoadingSubstantiality(false);
    }
  };

  // Toggle issue expansion
  // 切换问题展开
  const handleIssueClick = useCallback((index: number) => {
    setExpandedIssueIndex(prev => prev === index ? null : index);
  }, []);

  // Toggle transition expansion
  // 切换衔接展开
  const handleTransitionClick = useCallback((index: number) => {
    setExpandedTransitionIndex(prev => prev === index ? null : index);
  }, []);

  // Toggle paragraph expansion (Step 1.2)
  // 切换段落展开（步骤1.2）
  const handleParagraphClick = useCallback((index: number) => {
    setExpandedParagraphIndex(prev => prev === index ? null : index);
  }, []);

  // Toggle substantiality paragraph expansion (Step 1.5)
  // 切换实质性段落展开（步骤1.5）
  const handleSubstantialityClick = useCallback((index: number) => {
    setExpandedSubstantialityIndex(prev => prev === index ? null : index);
  }, []);

  // Navigate to next layer (Section)
  // 导航到下一层（章节层）
  const handleNext = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/layer-section/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

  // Navigate back
  // 返回导航
  const handleBack = useCallback(() => {
    navigate('/upload');
  }, [navigate]);

  // Render risk level badge
  // 渲染风险等级徽章
  const renderRiskBadge = (level: string) => {
    return (
      <span className={clsx(
        'px-2 py-1 rounded text-xs font-medium',
        level === 'high' && 'bg-red-100 text-red-700',
        level === 'medium' && 'bg-yellow-100 text-yellow-700',
        level === 'low' && 'bg-green-100 text-green-700'
      )}>
        {level === 'high' ? '高风险 High' :
         level === 'medium' ? '中风险 Medium' : '低风险 Low'}
      </span>
    );
  };

  // Render severity badge
  // 渲染严重程度徽章
  const renderSeverityBadge = (severity: string) => {
    return (
      <span className={clsx(
        'px-2 py-0.5 rounded text-xs font-medium',
        severity === 'high' && 'bg-red-100 text-red-700',
        severity === 'medium' && 'bg-yellow-100 text-yellow-700',
        severity === 'low' && 'bg-blue-100 text-blue-700'
      )}>
        {severity === 'high' ? '高' : severity === 'medium' ? '中' : '低'}
      </span>
    );
  };

  // Loading state
  // 加载状态
  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex items-center justify-center min-h-[50vh]">
          <LoadingMessage category="structure" size="lg" showEnglish={true} />
        </div>
      </div>
    );
  }

  // Error state
  // 错误状态
  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex flex-col items-center justify-center min-h-[50vh]">
          <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
          <p className="text-red-600 text-lg mb-4">{error}</p>
          {showNavigation && (
            <Button variant="outline" onClick={handleBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回上传 / Back
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="p-2 rounded-lg bg-indigo-100 text-indigo-600 mr-3">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Layer 5: 文章层分析
              </h1>
              <p className="text-gray-600 mt-1">
                Document Layer Analysis
              </p>
            </div>
          </div>
          {showNavigation && (
            <Button variant="outline" onClick={handleBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回
            </Button>
          )}
        </div>

        {/* 5-Layer Progress with Step 1.0 Term Lock */}
        {/* 5层进度（含Step 1.0词汇锁定）*/}
        <div className="mt-4 flex items-center text-sm text-gray-500 flex-wrap gap-y-1">
          <button
            onClick={() => navigate(`/flow/term-lock/${documentId}?mode=${mode}${sessionId ? `&session=${sessionId}` : ''}`)}
            className="text-gray-600 hover:text-indigo-600 hover:underline transition-colors"
          >
            Step 1.0 词汇锁定
          </button>
          <span className="mx-2">→</span>
          <span className="font-medium text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
            Layer 5 文章
          </span>
          <span className="mx-2">→</span>
          <span>Layer 4 章节</span>
          <span className="mx-2">→</span>
          <span>Layer 3 段落</span>
          <span className="mx-2">→</span>
          <span>Layer 2 句子</span>
          <span className="mx-2">→</span>
          <span>Layer 1 词汇</span>
        </div>

        {/* Step tabs within layer */}
        {/* 层内步骤标签 */}
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            onClick={() => setCurrentStep('1.1')}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              currentStep === '1.1'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            1.1 结构框架
          </button>
          <button
            onClick={() => setCurrentStep('1.2')}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              currentStep === '1.2'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            1.2 段落长度
          </button>
          <button
            onClick={() => setCurrentStep('1.3')}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              currentStep === '1.3'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            1.3 推进闭合
          </button>
          <button
            onClick={() => setCurrentStep('1.4')}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              currentStep === '1.4'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            1.4 连接词衔接
          </button>
          <button
            onClick={() => setCurrentStep('1.5')}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              currentStep === '1.5'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            1.5 内容实质
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Score Card */}
          {/* 分数卡片 */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-1 flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2 text-indigo-600" />
                  文章层风险分数 / Document Layer Risk Score
                </h3>
                <p className="text-sm text-gray-500">
                  分数越高表示AI生成特征越明显
                </p>
              </div>
              <div className="text-right">
                <p className={clsx(
                  'text-4xl font-bold',
                  result.riskScore <= 30 && 'text-green-600',
                  result.riskScore > 30 && result.riskScore <= 60 && 'text-yellow-600',
                  result.riskScore > 60 && 'text-red-600'
                )}>
                  {result.riskScore}
                </p>
                {renderRiskBadge(result.riskLevel)}
              </div>
            </div>

            {/* Score Legend */}
            {/* 分数说明 */}
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <p className="text-xs font-medium text-gray-600 mb-2">分数段含义 / Score Ranges:</p>
              <div className="flex flex-wrap gap-4 text-xs">
                <div className="flex items-center">
                  <span className="w-3 h-3 bg-green-500 rounded-full mr-1.5"></span>
                  <span className="text-gray-600">0-30: 低风险 Low Risk (人类写作特征明显)</span>
                </div>
                <div className="flex items-center">
                  <span className="w-3 h-3 bg-yellow-500 rounded-full mr-1.5"></span>
                  <span className="text-gray-600">31-60: 中风险 Medium Risk (需进一步检查)</span>
                </div>
                <div className="flex items-center">
                  <span className="w-3 h-3 bg-red-500 rounded-full mr-1.5"></span>
                  <span className="text-gray-600">61-100: 高风险 High Risk (AI特征明显)</span>
                </div>
              </div>
            </div>

            {/* Statistics */}
            {/* 统计信息 */}
            <div className="mt-4 grid grid-cols-3 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-indigo-600">
                  {result.sections?.length || 0}
                </p>
                <p className="text-sm text-gray-600">章节数 Sections</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-indigo-600">
                  {result.structureScore || 0}
                </p>
                <p className="text-sm text-gray-600">结构分 Structure</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-indigo-600">
                  {result.structurePattern || 'N/A'}
                </p>
                <p className="text-sm text-gray-600">结构模式 Pattern</p>
              </div>
            </div>
          </div>

          {/* Step 1.1: Structure Analysis */}
          {/* 步骤 1.1：结构分析 */}
          {currentStep === '1.1' && (
            <>
              {/* Sections Overview */}
              {/* 章节概览 */}
              {result.sections && result.sections.length > 0 && (
                <div className="card p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                    <Layers className="w-5 h-5 mr-2 text-indigo-600" />
                    文档结构概览 / Document Structure Overview
                  </h3>
                  <div className="space-y-3">
                    {result.sections.map((section, idx) => (
                      <div
                        key={idx}
                        className="p-4 bg-gray-50 rounded-lg border border-gray-200"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-800">
                            {section.title || `Section ${idx + 1}`}
                          </span>
                          <span className="text-sm text-gray-500">
                            {section.role}
                          </span>
                        </div>
                        <div className="flex items-center text-sm text-gray-600 space-x-4">
                          <span>{section.paragraphCount} 段落</span>
                          <span>{section.wordCount} 词</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Predictability Scores */}
              {/* 可预测性分数 */}
              {result.predictabilityScores && Object.keys(result.predictabilityScores).length > 0 && (
                <div className="card p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                    <Target className="w-5 h-5 mr-2 text-indigo-600" />
                    结构可预测性分析 / Structure Predictability
                  </h3>
                  {/* Predictability Score Legend */}
                  {/* 可预测性分数说明 */}
                  <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-blue-700">
                      <strong>说明 / Note:</strong> 分数越高表示该维度越可预测/越规律，AI生成文本通常在各维度上得分较高。
                      Higher scores indicate more predictable/regular patterns, which is typical of AI-generated text.
                    </p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(result.predictabilityScores).map(([dimension, score]) => (
                      <div key={dimension} className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">
                            {DIMENSION_LABELS[dimension] || dimension}
                          </span>
                          <span className={clsx(
                            'text-sm font-bold',
                            score <= 30 && 'text-green-600',
                            score > 30 && score <= 60 && 'text-yellow-600',
                            score > 60 && 'text-red-600'
                          )}>
                            {score}
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={clsx(
                              'h-2 rounded-full',
                              score <= 30 && 'bg-green-500',
                              score > 30 && score <= 60 && 'bg-yellow-500',
                              score > 60 && 'bg-red-500'
                            )}
                            style={{ width: `${score}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Structure Issues in Step 1.1 */}
              {/* 步骤1.1中的结构问题 */}
              {result.issues && result.issues.length > 0 && (
                <div className="card p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                    <AlertCircle className="w-5 h-5 mr-2 text-amber-600" />
                    结构问题 / Structure Issues
                  </h3>
                  <p className="text-sm text-gray-500 mb-4">
                    以下是在文档结构中检测到的问题，点击可查看详情
                  </p>
                  <div className="space-y-3">
                    {result.issues.map((issue: DetectionIssue, idx: number) => (
                      <div key={idx} className="space-y-2">
                        <div
                          onClick={() => handleIssueClick(idx)}
                          className={clsx(
                            'p-4 rounded-lg border-l-4 cursor-pointer transition-all hover:shadow-md',
                            issue.severity === 'high' && 'bg-red-50 border-red-500 hover:bg-red-100',
                            issue.severity === 'medium' && 'bg-yellow-50 border-yellow-500 hover:bg-yellow-100',
                            issue.severity === 'low' && 'bg-blue-50 border-blue-500 hover:bg-blue-100'
                          )}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="font-medium text-gray-800">{issue.descriptionZh}</p>
                              <p className="text-sm text-gray-500 mt-1">{issue.description}</p>
                            </div>
                            <div className="flex items-center space-x-2 ml-4">
                              {renderSeverityBadge(issue.severity)}
                              {expandedIssueIndex === idx ? (
                                <ChevronUp className="w-5 h-5 text-gray-400" />
                              ) : (
                                <ChevronDown className="w-5 h-5 text-gray-400" />
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Expanded details in Step 1.1 */}
                        {/* 步骤1.1中展开的详情 */}
                        {expandedIssueIndex === idx && (
                          <div className="ml-4 p-4 bg-white border rounded-lg shadow-sm">
                            {issue.suggestion && (
                              <div className="mb-3">
                                <h4 className="font-medium text-gray-800 mb-1">建议 / Suggestion</h4>
                                <p className="text-sm text-gray-600">{issue.suggestionZh || issue.suggestion}</p>
                              </div>
                            )}
                            {issue.details && Object.keys(issue.details).length > 0 && (
                              <div>
                                <h4 className="font-medium text-gray-800 mb-1">详情 / Details</h4>
                                <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
                                  {JSON.stringify(issue.details, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Step 1.2: Paragraph Length Regularity */}
          {/* 步骤 1.2：段落长度规律性 */}
          {currentStep === '1.2' && (
            <>
              {isLoadingParagraphLength ? (
                <div className="flex items-center justify-center min-h-[30vh]">
                  <LoadingMessage category="structure" size="lg" showEnglish={true} />
                </div>
              ) : paragraphLengthResult ? (
                <>
                  {/* Statistics Card */}
                  {/* 统计卡片 */}
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                      <BarChart3 className="w-5 h-5 mr-2 text-indigo-600" />
                      段落长度规律性分析 / Paragraph Length Regularity
                    </h3>

                    {/* Statistics Grid */}
                    {/* 统计网格 */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className="text-2xl font-bold text-indigo-600">
                          {paragraphLengthResult.paragraphCount}
                        </p>
                        <p className="text-xs text-gray-600">段落数</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className="text-2xl font-bold text-indigo-600">
                          {paragraphLengthResult.meanLength.toFixed(0)}
                        </p>
                        <p className="text-xs text-gray-600">平均词数</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className={clsx(
                          'text-2xl font-bold',
                          paragraphLengthResult.cv >= 0.4 && 'text-green-600',
                          paragraphLengthResult.cv >= 0.3 && paragraphLengthResult.cv < 0.4 && 'text-yellow-600',
                          paragraphLengthResult.cv < 0.3 && 'text-red-600'
                        )}>
                          {paragraphLengthResult.cv.toFixed(2)}
                        </p>
                        <p className="text-xs text-gray-600">变异系数CV</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className={clsx(
                          'text-2xl font-bold',
                          paragraphLengthResult.lengthRegularityScore <= 30 && 'text-green-600',
                          paragraphLengthResult.lengthRegularityScore > 30 && paragraphLengthResult.lengthRegularityScore <= 60 && 'text-yellow-600',
                          paragraphLengthResult.lengthRegularityScore > 60 && 'text-red-600'
                        )}>
                          {paragraphLengthResult.lengthRegularityScore}
                        </p>
                        <p className="text-xs text-gray-600">均匀度分数</p>
                      </div>
                    </div>

                    {/* Risk Badge */}
                    {/* 风险徽章 */}
                    <div className="flex items-center justify-center mb-4">
                      {renderRiskBadge(paragraphLengthResult.riskLevel)}
                    </div>

                    {/* CV Explanation */}
                    {/* CV说明 */}
                    <div className="p-3 bg-blue-50 rounded-lg mb-4">
                      <p className="text-xs text-blue-700">
                        <strong>CV (变异系数):</strong> 当前 {paragraphLengthResult.cv.toFixed(2)}，
                        目标 &gt;= {paragraphLengthResult.targetCv}。
                        CV越低表示段落长度越均匀，是AI生成的典型特征。
                        人类写作通常有更大的长度变化。
                      </p>
                    </div>

                    {/* Length Range */}
                    {/* 长度范围 */}
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>最短: {paragraphLengthResult.minLength} 词</span>
                      <span>最长: {paragraphLengthResult.maxLength} 词</span>
                    </div>
                  </div>

                  {/* Paragraph Length Visualization */}
                  {/* 段落长度可视化 */}
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">
                      段落长度分布 / Paragraph Length Distribution
                    </h3>
                    <div className="space-y-3">
                      {paragraphLengthResult.paragraphs.map((para: ParagraphLengthInfo, idx: number) => (
                        <div key={idx} className="space-y-2">
                          <div
                            onClick={() => handleParagraphClick(idx)}
                            className={clsx(
                              'p-3 rounded-lg cursor-pointer transition-all hover:shadow-md',
                              para.suggestedStrategy !== 'none' && 'border-l-4',
                              para.suggestedStrategy === 'merge' && 'bg-blue-50 border-blue-500',
                              para.suggestedStrategy === 'split' && 'bg-orange-50 border-orange-500',
                              para.suggestedStrategy === 'expand' && 'bg-green-50 border-green-500',
                              para.suggestedStrategy === 'compress' && 'bg-purple-50 border-purple-500',
                              para.suggestedStrategy === 'none' && 'bg-gray-50'
                            )}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium text-gray-800">
                                段落 {idx + 1}
                              </span>
                              <div className="flex items-center space-x-2">
                                <span className="text-sm text-gray-600">
                                  {para.wordCount} 词
                                </span>
                                {para.suggestedStrategy !== 'none' && (
                                  <span className={clsx(
                                    'px-2 py-0.5 rounded text-xs font-medium',
                                    para.suggestedStrategy === 'merge' && 'bg-blue-100 text-blue-700',
                                    para.suggestedStrategy === 'split' && 'bg-orange-100 text-orange-700',
                                    para.suggestedStrategy === 'expand' && 'bg-green-100 text-green-700',
                                    para.suggestedStrategy === 'compress' && 'bg-purple-100 text-purple-700'
                                  )}>
                                    {para.suggestedStrategy === 'merge' && '建议合并'}
                                    {para.suggestedStrategy === 'split' && '建议拆分'}
                                    {para.suggestedStrategy === 'expand' && '建议扩展'}
                                    {para.suggestedStrategy === 'compress' && '建议压缩'}
                                  </span>
                                )}
                                {expandedParagraphIndex === idx ? (
                                  <ChevronUp className="w-4 h-4 text-gray-400" />
                                ) : (
                                  <ChevronDown className="w-4 h-4 text-gray-400" />
                                )}
                              </div>
                            </div>

                            {/* Length Bar */}
                            {/* 长度条 */}
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className={clsx(
                                  'h-2 rounded-full transition-all',
                                  para.deviationFromMean > 1 && 'bg-orange-500',
                                  para.deviationFromMean < -1 && 'bg-blue-500',
                                  Math.abs(para.deviationFromMean) <= 1 && 'bg-indigo-500'
                                )}
                                style={{
                                  width: `${Math.min(100, (para.wordCount / paragraphLengthResult.maxLength) * 100)}%`
                                }}
                              />
                            </div>
                          </div>

                          {/* Expanded details */}
                          {/* 展开的详情 */}
                          {expandedParagraphIndex === idx && (
                            <div className="ml-4 p-4 bg-white border rounded-lg shadow-sm">
                              <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
                                <div>
                                  <span className="text-gray-500">词数:</span>
                                  <span className="ml-2 font-medium">{para.wordCount}</span>
                                </div>
                                <div>
                                  <span className="text-gray-500">句数:</span>
                                  <span className="ml-2 font-medium">{para.sentenceCount}</span>
                                </div>
                                <div>
                                  <span className="text-gray-500">偏离:</span>
                                  <span className={clsx(
                                    'ml-2 font-medium',
                                    para.deviationFromMean > 0 && 'text-orange-600',
                                    para.deviationFromMean < 0 && 'text-blue-600',
                                    para.deviationFromMean === 0 && 'text-gray-600'
                                  )}>
                                    {para.deviationFromMean > 0 ? '+' : ''}{para.deviationFromMean.toFixed(1)} stddev
                                  </span>
                                </div>
                              </div>

                              {para.strategyReasonZh && (
                                <div className="p-2 bg-amber-50 rounded text-sm text-amber-800">
                                  {para.strategyReasonZh}
                                </div>
                              )}

                              <div className="mt-3">
                                <p className="text-xs text-gray-500 mb-1">预览:</p>
                                <p className="text-sm text-gray-600 italic">
                                  "{para.preview}"
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>

                    {/* Strategy Legend */}
                    {/* 策略图例 */}
                    <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                      <p className="text-xs font-medium text-gray-600 mb-2">策略说明 / Strategy Legend:</p>
                      <div className="flex flex-wrap gap-3 text-xs">
                        <span className="flex items-center">
                          <span className="w-3 h-3 bg-blue-500 rounded mr-1"></span>
                          合并 Merge (短段落)
                        </span>
                        <span className="flex items-center">
                          <span className="w-3 h-3 bg-orange-500 rounded mr-1"></span>
                          拆分 Split (长段落)
                        </span>
                        <span className="flex items-center">
                          <span className="w-3 h-3 bg-green-500 rounded mr-1"></span>
                          扩展 Expand (偏短)
                        </span>
                        <span className="flex items-center">
                          <span className="w-3 h-3 bg-purple-500 rounded mr-1"></span>
                          压缩 Compress (偏长)
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Recommendations */}
                  {/* 建议 */}
                  {paragraphLengthResult.recommendationsZh.length > 0 && (
                    <div className="card p-6">
                      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                        <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                        改进建议 / Recommendations
                      </h3>
                      <div className="space-y-2">
                        {paragraphLengthResult.recommendationsZh.map((rec, idx) => (
                          <div key={idx} className="p-3 bg-green-50 rounded-lg">
                            <p className="text-sm text-green-800">{rec}</p>
                            {paragraphLengthResult.recommendations[idx] && (
                              <p className="text-xs text-green-600 mt-1">
                                {paragraphLengthResult.recommendations[idx]}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Processing Time */}
                  {paragraphLengthResult.processingTimeMs && (
                    <p className="text-xs text-gray-400 text-center">
                      分析耗时 {paragraphLengthResult.processingTimeMs}ms
                    </p>
                  )}
                </>
              ) : (
                <div className="card p-6">
                  <p className="text-gray-500 text-center py-8">
                    点击分析开始检测段落长度规律性
                  </p>
                  <div className="flex justify-center">
                    <Button onClick={loadParagraphLengthAnalysis}>
                      开始分析
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Step 1.3: Progression & Closure */}
          {/* 步骤 1.3：推进模式与闭合 */}
          {currentStep === '1.3' && (
            <>
              {isLoadingProgressionClosure ? (
                <div className="flex items-center justify-center min-h-[30vh]">
                  <LoadingMessage category="structure" size="lg" showEnglish={true} />
                </div>
              ) : progressionClosureResult ? (
                <>
                  {/* Statistics Card */}
                  {/* 统计卡片 */}
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                      <Target className="w-5 h-5 mr-2 text-indigo-600" />
                      推进模式与闭合分析 / Progression & Closure Analysis
                    </h3>

                    {/* Statistics Grid */}
                    {/* 统计网格 */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className={clsx(
                          'text-2xl font-bold',
                          progressionClosureResult.progressionScore <= 30 && 'text-green-600',
                          progressionClosureResult.progressionScore > 30 && progressionClosureResult.progressionScore <= 60 && 'text-yellow-600',
                          progressionClosureResult.progressionScore > 60 && 'text-red-600'
                        )}>
                          {progressionClosureResult.progressionScore}
                        </p>
                        <p className="text-xs text-gray-600">推进可预测性</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className={clsx(
                          'text-2xl font-bold',
                          progressionClosureResult.closureScore <= 30 && 'text-green-600',
                          progressionClosureResult.closureScore > 30 && progressionClosureResult.closureScore <= 60 && 'text-yellow-600',
                          progressionClosureResult.closureScore > 60 && 'text-red-600'
                        )}>
                          {progressionClosureResult.closureScore}
                        </p>
                        <p className="text-xs text-gray-600">闭合强度</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className="text-2xl font-bold text-indigo-600">
                          {progressionClosureResult.monotonicCount}
                        </p>
                        <p className="text-xs text-gray-600">单调标记</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className="text-2xl font-bold text-green-600">
                          {progressionClosureResult.nonMonotonicCount}
                        </p>
                        <p className="text-xs text-gray-600">非单调标记</p>
                      </div>
                    </div>

                    {/* Risk Badge */}
                    {/* 风险徽章 */}
                    <div className="flex items-center justify-center mb-4">
                      {renderRiskBadge(progressionClosureResult.riskLevel)}
                    </div>

                    {/* Progression Type and Closure Type */}
                    {/* 推进类型和闭合类型 */}
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="p-3 bg-blue-50 rounded-lg">
                        <p className="text-xs text-blue-700 mb-1">推进类型 / Progression Type:</p>
                        <p className={clsx(
                          'font-medium',
                          progressionClosureResult.progressionType === 'monotonic' && 'text-red-600',
                          progressionClosureResult.progressionType === 'non_monotonic' && 'text-green-600',
                          progressionClosureResult.progressionType === 'mixed' && 'text-yellow-600'
                        )}>
                          {progressionClosureResult.progressionType === 'monotonic' && '单调 Monotonic (AI-like)'}
                          {progressionClosureResult.progressionType === 'non_monotonic' && '非单调 Non-monotonic (Human-like)'}
                          {progressionClosureResult.progressionType === 'mixed' && '混合 Mixed'}
                          {progressionClosureResult.progressionType === 'unknown' && '未知 Unknown'}
                        </p>
                      </div>
                      <div className="p-3 bg-purple-50 rounded-lg">
                        <p className="text-xs text-purple-700 mb-1">闭合类型 / Closure Type:</p>
                        <p className={clsx(
                          'font-medium',
                          progressionClosureResult.closureType === 'strong' && 'text-red-600',
                          progressionClosureResult.closureType === 'open' && 'text-green-600',
                          (progressionClosureResult.closureType === 'moderate' || progressionClosureResult.closureType === 'weak') && 'text-yellow-600'
                        )}>
                          {progressionClosureResult.closureType === 'strong' && '强闭合 Strong (AI-like)'}
                          {progressionClosureResult.closureType === 'moderate' && '中等闭合 Moderate'}
                          {progressionClosureResult.closureType === 'weak' && '弱闭合 Weak'}
                          {progressionClosureResult.closureType === 'open' && '开放式 Open (Human-like)'}
                        </p>
                      </div>
                    </div>

                    {/* Sequential Markers Warning */}
                    {/* 顺序标记警告 */}
                    {progressionClosureResult.sequentialMarkersFound >= 3 && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg mb-4">
                        <p className="text-sm text-red-700">
                          <AlertTriangle className="w-4 h-4 inline mr-1" />
                          检测到 {progressionClosureResult.sequentialMarkersFound} 个顺序标记（First, Second, Third...）
                          - 这是强烈的AI信号！
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Progression Markers */}
                  {/* 推进标记 */}
                  {progressionClosureResult.progressionMarkers.length > 0 && (
                    <div className="card p-6">
                      <h3 className="text-lg font-semibold text-gray-800 mb-4">
                        检测到的推进标记 / Detected Progression Markers
                      </h3>
                      <div className="space-y-2">
                        {progressionClosureResult.progressionMarkers.map((marker: ProgressionMarker, idx: number) => (
                          <div
                            key={idx}
                            className={clsx(
                              'p-2 rounded flex items-center justify-between',
                              marker.isMonotonic ? 'bg-red-50' : 'bg-green-50'
                            )}
                          >
                            <div>
                              <span className={clsx(
                                'font-medium',
                                marker.isMonotonic ? 'text-red-700' : 'text-green-700'
                              )}>
                                "{marker.marker}"
                              </span>
                              <span className="text-xs text-gray-500 ml-2">
                                段落 {marker.paragraphIndex + 1} - {marker.category}
                              </span>
                            </div>
                            <span className={clsx(
                              'px-2 py-0.5 rounded text-xs',
                              marker.isMonotonic ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                            )}>
                              {marker.isMonotonic ? '单调' : '非单调'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Last Paragraph Preview */}
                  {/* 末段预览 */}
                  {progressionClosureResult.lastParagraphPreview && (
                    <div className="card p-6">
                      <h3 className="text-lg font-semibold text-gray-800 mb-4">
                        末段预览 / Last Paragraph Preview
                      </h3>
                      <p className="text-sm text-gray-600 italic bg-gray-50 p-3 rounded">
                        "{progressionClosureResult.lastParagraphPreview}"
                      </p>
                      {progressionClosureResult.strongClosurePatterns.length > 0 && (
                        <div className="mt-3 p-2 bg-red-50 rounded">
                          <p className="text-xs text-red-700">
                            检测到强闭合模式: {progressionClosureResult.strongClosurePatterns.join(', ')}
                          </p>
                        </div>
                      )}
                      {progressionClosureResult.weakClosurePatterns.length > 0 && (
                        <div className="mt-3 p-2 bg-green-50 rounded">
                          <p className="text-xs text-green-700">
                            检测到弱/开放闭合模式: {progressionClosureResult.weakClosurePatterns.join(', ')}
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Recommendations */}
                  {/* 建议 */}
                  {progressionClosureResult.recommendationsZh.length > 0 && (
                    <div className="card p-6">
                      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                        <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                        改进建议 / Recommendations
                      </h3>
                      <div className="space-y-2">
                        {progressionClosureResult.recommendationsZh.map((rec, idx) => (
                          <div key={idx} className="p-3 bg-green-50 rounded-lg">
                            <p className="text-sm text-green-800">{rec}</p>
                            {progressionClosureResult.recommendations[idx] && (
                              <p className="text-xs text-green-600 mt-1">
                                {progressionClosureResult.recommendations[idx]}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Processing Time */}
                  {progressionClosureResult.processingTimeMs && (
                    <p className="text-xs text-gray-400 text-center">
                      分析耗时 {progressionClosureResult.processingTimeMs}ms
                    </p>
                  )}
                </>
              ) : (
                <div className="card p-6">
                  <p className="text-gray-500 text-center py-8">
                    点击分析开始检测推进模式与闭合
                  </p>
                  <div className="flex justify-center">
                    <Button onClick={loadProgressionClosureAnalysis}>
                      开始分析
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Step 1.4: Connector & Transition Analysis */}
          {/* 步骤 1.4：连接词与衔接分析 */}
          {currentStep === '1.4' && (
            <>
              {isLoadingConnectors ? (
                <div className="flex items-center justify-center min-h-[30vh]">
                  <LoadingMessage category="transition" size="lg" showEnglish={true} />
                </div>
              ) : connectorResult ? (
                <>
                  {/* Connector Statistics Card */}
                  {/* 连接词统计卡片 */}
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                      <Link2 className="w-5 h-5 mr-2 text-indigo-600" />
                      连接词与衔接分析 / Connector & Transition Analysis
                    </h3>

                    {/* Statistics Grid */}
                    {/* 统计网格 */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className="text-2xl font-bold text-indigo-600">
                          {connectorResult.totalTransitions}
                        </p>
                        <p className="text-xs text-gray-600">段落衔接数</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className={clsx(
                          'text-2xl font-bold',
                          connectorResult.problematicTransitions === 0 && 'text-green-600',
                          connectorResult.problematicTransitions > 0 && connectorResult.problematicTransitions <= 2 && 'text-yellow-600',
                          connectorResult.problematicTransitions > 2 && 'text-red-600'
                        )}>
                          {connectorResult.problematicTransitions}
                        </p>
                        <p className="text-xs text-gray-600">问题衔接数</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className={clsx(
                          'text-2xl font-bold',
                          connectorResult.overallSmoothnessScore <= 30 && 'text-green-600',
                          connectorResult.overallSmoothnessScore > 30 && connectorResult.overallSmoothnessScore <= 60 && 'text-yellow-600',
                          connectorResult.overallSmoothnessScore > 60 && 'text-red-600'
                        )}>
                          {connectorResult.overallSmoothnessScore}
                        </p>
                        <p className="text-xs text-gray-600">AI平滑度分数</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className={clsx(
                          'text-2xl font-bold',
                          connectorResult.connectorDensity <= 20 && 'text-green-600',
                          connectorResult.connectorDensity > 20 && connectorResult.connectorDensity <= 40 && 'text-yellow-600',
                          connectorResult.connectorDensity > 40 && 'text-red-600'
                        )}>
                          {connectorResult.connectorDensity.toFixed(1)}%
                        </p>
                        <p className="text-xs text-gray-600">连接词密度</p>
                      </div>
                    </div>

                    {/* Risk Badge */}
                    {/* 风险徽章 */}
                    <div className="flex items-center justify-center mb-4">
                      {renderRiskBadge(connectorResult.overallRiskLevel)}
                    </div>

                    {/* Explicit Connectors Found */}
                    {/* 发现的显性连接词 */}
                    {connectorResult.connectorList.length > 0 && (
                      <div className="mt-4 p-3 bg-amber-50 rounded-lg">
                        <p className="text-sm font-medium text-amber-800 mb-2">
                          检测到的显性连接词 / Explicit Connectors Found:
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {connectorResult.connectorList.map((connector, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-amber-100 text-amber-700 rounded text-xs"
                            >
                              {connector}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Transition Details */}
                  {/* 衔接详情 */}
                  {connectorResult.transitions.length > 0 && (
                    <div className="card p-6">
                      <h3 className="text-lg font-semibold text-gray-800 mb-4">
                        段落衔接详情 / Transition Details
                      </h3>
                      <p className="text-sm text-gray-500 mb-4">
                        点击查看每个段落衔接的详细分析
                      </p>
                      <div className="space-y-3">
                        {connectorResult.transitions.map((transition, idx) => (
                          <div key={idx} className="space-y-2">
                            <div
                              onClick={() => handleTransitionClick(idx)}
                              className={clsx(
                                'p-4 rounded-lg border-l-4 cursor-pointer transition-all hover:shadow-md',
                                transition.riskLevel === 'high' && 'bg-red-50 border-red-500 hover:bg-red-100',
                                transition.riskLevel === 'medium' && 'bg-yellow-50 border-yellow-500 hover:bg-yellow-100',
                                transition.riskLevel === 'low' && 'bg-green-50 border-green-500 hover:bg-green-100'
                              )}
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <p className="font-medium text-gray-800">
                                    段落 {transition.paraAIndex + 1} → 段落 {transition.paraBIndex + 1}
                                  </p>
                                  <p className="text-sm text-gray-500 mt-1">
                                    平滑度: {transition.smoothnessScore} | 问题数: {transition.issues.length}
                                    {transition.explicitConnectors.length > 0 && (
                                      <span className="ml-2 text-amber-600">
                                        连接词: {transition.explicitConnectors.join(', ')}
                                      </span>
                                    )}
                                  </p>
                                </div>
                                <div className="flex items-center space-x-2 ml-4">
                                  {renderRiskBadge(transition.riskLevel)}
                                  {expandedTransitionIndex === idx ? (
                                    <ChevronUp className="w-5 h-5 text-gray-400" />
                                  ) : (
                                    <ChevronDown className="w-5 h-5 text-gray-400" />
                                  )}
                                </div>
                              </div>
                            </div>

                            {/* Expanded transition details */}
                            {/* 展开的衔接详情 */}
                            {expandedTransitionIndex === idx && (
                              <div className="ml-4 p-4 bg-white border rounded-lg shadow-sm space-y-4">
                                {/* Paragraph A Ending */}
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-1">
                                    段落 {transition.paraAIndex + 1} 结尾:
                                  </h4>
                                  <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded italic">
                                    "{transition.paraAEnding}"
                                  </p>
                                  {transition.hasSummaryEnding && (
                                    <span className="inline-block mt-1 px-2 py-0.5 bg-amber-100 text-amber-700 rounded text-xs">
                                      总结性结尾
                                    </span>
                                  )}
                                </div>

                                {/* Paragraph B Opening */}
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-1">
                                    段落 {transition.paraBIndex + 1} 开头:
                                  </h4>
                                  <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded italic">
                                    "{transition.paraBOpening}"
                                  </p>
                                  {transition.hasTopicSentencePattern && (
                                    <span className="inline-block mt-1 px-2 py-0.5 bg-amber-100 text-amber-700 rounded text-xs">
                                      公式化主题句
                                    </span>
                                  )}
                                </div>

                                {/* Issues */}
                                {transition.issues.length > 0 && (
                                  <div>
                                    <h4 className="font-medium text-gray-700 mb-2">检测到的问题:</h4>
                                    <div className="space-y-2">
                                      {transition.issues.map((issue, issueIdx) => (
                                        <div
                                          key={issueIdx}
                                          className="p-2 bg-red-50 border-l-2 border-red-400 rounded-r"
                                        >
                                          <p className="text-sm text-red-800">{issue.descriptionZh}</p>
                                          <p className="text-xs text-red-600 mt-1">{issue.description}</p>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Semantic Overlap */}
                                <div className="flex items-center text-sm text-gray-500">
                                  <span>语义重叠率: {(transition.semanticOverlap * 100).toFixed(1)}%</span>
                                  {transition.semanticOverlap > 0.4 && (
                                    <span className="ml-2 text-amber-600">(过高)</span>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommendations */}
                  {/* 建议 */}
                  {connectorResult.recommendationsZh.length > 0 && (
                    <div className="card p-6">
                      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                        <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                        改进建议 / Recommendations
                      </h3>
                      <div className="space-y-2">
                        {connectorResult.recommendationsZh.map((rec, idx) => (
                          <div key={idx} className="p-3 bg-green-50 rounded-lg">
                            <p className="text-sm text-green-800">{rec}</p>
                            {connectorResult.recommendations[idx] && (
                              <p className="text-xs text-green-600 mt-1">
                                {connectorResult.recommendations[idx]}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Processing Time */}
                  {connectorResult.processingTimeMs && (
                    <p className="text-xs text-gray-400 text-center">
                      分析耗时 {connectorResult.processingTimeMs}ms
                    </p>
                  )}
                </>
              ) : (
                <div className="card p-6">
                  <p className="text-gray-500 text-center py-8">
                    点击分析开始检测连接词与衔接问题
                  </p>
                  <div className="flex justify-center">
                    <Button onClick={loadConnectorAnalysis}>
                      开始分析
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Step 1.5: Content Substantiveness */}
          {/* 步骤 1.5：内容实质性 */}
          {currentStep === '1.5' && (
            <>
              {isLoadingSubstantiality && (
                <div className="card p-6">
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-indigo-600 mr-3" />
                    <span className="text-gray-600">分析内容实质性... / Analyzing content substantiality...</span>
                  </div>
                </div>
              )}

              {substantialityResult && (
                <div className="space-y-6">
                  {/* Overview Card / 概览卡片 */}
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                      <Target className="w-5 h-5 mr-2 text-indigo-600" />
                      内容实质性检测 / Content Substantiveness
                    </h3>

                    {/* Score and Level / 得分和等级 */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-lg p-4 text-center">
                        <div className="text-3xl font-bold text-indigo-700">{substantialityResult.overallSpecificityScore}</div>
                        <div className="text-sm text-indigo-600">具体性得分 / Specificity</div>
                      </div>
                      <div className={clsx(
                        'rounded-lg p-4 text-center',
                        substantialityResult.overallSubstantiality === 'high' ? 'bg-green-50' :
                        substantialityResult.overallSubstantiality === 'medium' ? 'bg-yellow-50' : 'bg-red-50'
                      )}>
                        <div className={clsx(
                          'text-2xl font-bold',
                          substantialityResult.overallSubstantiality === 'high' ? 'text-green-700' :
                          substantialityResult.overallSubstantiality === 'medium' ? 'text-yellow-700' : 'text-red-700'
                        )}>
                          {substantialityResult.overallSubstantiality === 'high' ? '高 HIGH' :
                           substantialityResult.overallSubstantiality === 'medium' ? '中 MEDIUM' : '低 LOW'}
                        </div>
                        <div className="text-sm text-gray-600">实质性等级 / Level</div>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4 text-center">
                        <div className="text-2xl font-bold text-gray-700">{substantialityResult.totalGenericPhrases}</div>
                        <div className="text-sm text-gray-600">通用短语 / Generic Phrases</div>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4 text-center">
                        <div className="text-2xl font-bold text-gray-700">{substantialityResult.totalSpecificDetails}</div>
                        <div className="text-sm text-gray-600">具体细节 / Specific Details</div>
                      </div>
                    </div>

                    {/* Statistics Row / 统计行 */}
                    <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                      <div className="bg-gray-50 rounded p-3">
                        <span className="text-gray-500">平均填充词比例 / Avg Filler Ratio:</span>
                        <span className="ml-2 font-semibold">{(substantialityResult.averageFillerRatio * 100).toFixed(1)}%</span>
                      </div>
                      <div className="bg-gray-50 rounded p-3">
                        <span className="text-gray-500">低实质性段落 / Low Substantiality:</span>
                        <span className="ml-2 font-semibold text-red-600">{substantialityResult.lowSubstantialityParagraphs.length}</span>
                      </div>
                      <div className={clsx(
                        'rounded p-3',
                        substantialityResult.riskLevel === 'high' ? 'bg-red-50' :
                        substantialityResult.riskLevel === 'medium' ? 'bg-yellow-50' : 'bg-green-50'
                      )}>
                        <span className="text-gray-500">风险等级 / Risk:</span>
                        <span className={clsx(
                          'ml-2 font-semibold',
                          substantialityResult.riskLevel === 'high' ? 'text-red-600' :
                          substantialityResult.riskLevel === 'medium' ? 'text-yellow-600' : 'text-green-600'
                        )}>
                          {substantialityResult.riskLevel === 'high' ? '高风险 HIGH' :
                           substantialityResult.riskLevel === 'medium' ? '中风险 MEDIUM' : '低风险 LOW'}
                        </span>
                      </div>
                    </div>

                    {/* Common Generic Phrases / 常见通用短语 */}
                    {substantialityResult.commonGenericPhrases.length > 0 && (
                      <div className="mt-4 p-3 bg-amber-50 rounded-lg">
                        <h4 className="text-sm font-semibold text-amber-700 mb-2">
                          高频通用短语 / Common Generic Phrases ({substantialityResult.commonGenericPhrases.length})
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {substantialityResult.commonGenericPhrases.map((phrase, i) => (
                            <span key={i} className="px-2 py-1 bg-amber-100 text-amber-800 text-xs rounded-full">
                              {phrase}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Paragraph Details / 段落详情 */}
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">
                      段落实质性详情 / Paragraph Substantiality Details
                    </h3>

                    <div className="space-y-3">
                      {substantialityResult.paragraphs.map((para) => (
                        <div
                          key={para.index}
                          className={clsx(
                            'border rounded-lg transition-all cursor-pointer',
                            para.substantialityLevel === 'low' ? 'border-red-200 bg-red-50' :
                            para.substantialityLevel === 'medium' ? 'border-yellow-200 bg-yellow-50' :
                            'border-green-200 bg-green-50',
                            expandedSubstantialityIndex === para.index && 'ring-2 ring-indigo-300'
                          )}
                          onClick={() => handleSubstantialityClick(para.index)}
                        >
                          {/* Paragraph Header / 段落头部 */}
                          <div className="p-4">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center space-x-3">
                                <span className="text-sm font-semibold text-gray-700">
                                  段落 {para.index + 1}
                                </span>
                                <span className={clsx(
                                  'px-2 py-0.5 text-xs rounded-full font-medium',
                                  para.substantialityLevel === 'high' ? 'bg-green-200 text-green-800' :
                                  para.substantialityLevel === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                                  'bg-red-200 text-red-800'
                                )}>
                                  {para.substantialityLevel === 'high' ? '高实质性' :
                                   para.substantialityLevel === 'medium' ? '中实质性' : '低实质性'}
                                </span>
                                <span className="text-xs text-gray-500">
                                  得分: {para.specificityScore}
                                </span>
                              </div>
                              <div className="flex items-center space-x-4 text-xs text-gray-500">
                                <span>通用短语: {para.genericPhraseCount}</span>
                                <span>具体细节: {para.specificDetailCount}</span>
                                <span>填充词: {(para.fillerRatio * 100).toFixed(1)}%</span>
                                {expandedSubstantialityIndex === para.index ? (
                                  <ChevronUp className="w-4 h-4" />
                                ) : (
                                  <ChevronDown className="w-4 h-4" />
                                )}
                              </div>
                            </div>

                            {/* Preview / 预览 */}
                            <p className="text-sm text-gray-600 line-clamp-2">{para.preview}</p>
                          </div>

                          {/* Expanded Content / 展开内容 */}
                          {expandedSubstantialityIndex === para.index && (
                            <div className="px-4 pb-4 space-y-3 border-t border-gray-200 pt-3">
                              {/* Generic Phrases Found / 发现的通用短语 */}
                              {para.genericPhrases.length > 0 && (
                                <div>
                                  <h5 className="text-xs font-semibold text-red-600 mb-1">
                                    发现的通用短语 / Generic Phrases Found:
                                  </h5>
                                  <div className="flex flex-wrap gap-1">
                                    {para.genericPhrases.map((phrase, i) => (
                                      <span key={i} className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded">
                                        {phrase}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Specific Details Found / 发现的具体细节 */}
                              {para.specificDetails.length > 0 && (
                                <div>
                                  <h5 className="text-xs font-semibold text-green-600 mb-1">
                                    发现的具体细节 / Specific Details Found:
                                  </h5>
                                  <div className="flex flex-wrap gap-1">
                                    {para.specificDetails.map((detail, i) => (
                                      <span key={i} className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                                        {detail}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Suggestion / 建议 */}
                              <div className="p-2 bg-blue-50 rounded text-sm">
                                <span className="font-medium text-blue-700">建议: </span>
                                <span className="text-blue-600">{para.suggestionZh}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Recommendations / 建议 */}
                  {substantialityResult.recommendationsZh.length > 0 && (
                    <div className="card p-6">
                      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                        <AlertTriangle className="w-5 h-5 mr-2 text-amber-500" />
                        改进建议 / Recommendations
                      </h3>
                      <ul className="space-y-2">
                        {substantialityResult.recommendationsZh.map((rec, i) => (
                          <li key={i} className="flex items-start text-sm">
                            <span className="text-amber-500 mr-2">•</span>
                            <span className="text-gray-700">{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* Processing Time */}
          {/* 处理时间 */}
          {result.processingTimeMs && (
            <p className="text-xs text-gray-400 text-center">
              分析耗时 {result.processingTimeMs}ms
            </p>
          )}

          {/* Navigation */}
          {/* 导航 */}
          {showNavigation && (
            <div className="flex justify-between pt-4">
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                返回上传
              </Button>
              <Button onClick={handleNext}>
                继续到章节层
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
