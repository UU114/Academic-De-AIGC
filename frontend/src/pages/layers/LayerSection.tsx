import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  BookOpen,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  GitBranch,
  ArrowRightLeft,
  BarChart3,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';
import {
  sectionLayerApi,
  documentLayerApi,
  SectionAnalysisResponse,
  DetectionIssue,
  RiskLevel,
} from '../../services/analysisApi';
import { Loader2, AlertTriangle } from 'lucide-react';

/**
 * Layer Section (Layer 4) - Section Analysis
 * 章节层（第4层）- 章节分析
 *
 * Steps:
 * - Step 2.1: Section Logic Flow (章节逻辑流)
 * - Step 2.2: Section Transitions (章节衔接)
 * - Step 2.3: Section Length Distribution (章节长度分布)
 *
 * Receives context from Layer 5 (Document).
 * 从第5层（文章层）接收上下文。
 */

interface LayerSectionProps {
  documentIdProp?: string;
  onComplete?: (result: SectionAnalysisResponse) => void;
  showNavigation?: boolean;
}

export default function LayerSection({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerSectionProps) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  // Update session step on mount
  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer-section').catch(console.error);
    }
  }, [sessionId]);

  // Analysis state
  const [result, setResult] = useState<SectionAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<'2.1' | '2.2' | '2.3'>('2.1');

  // Document context
  const [documentText, setDocumentText] = useState<string>('');
  const [documentContext, setDocumentContext] = useState<Record<string, unknown> | null>(null);

  // Step 2.1: Logic Flow state
  // 步骤 2.1：逻辑流状态
  const [logicResult, setLogicResult] = useState<SectionAnalysisResponse | null>(null);
  const [isLoadingLogic, setIsLoadingLogic] = useState(false);

  // Step 2.2: Transitions state
  // 步骤 2.2：衔接状态
  const [transitionResult, setTransitionResult] = useState<SectionAnalysisResponse | null>(null);
  const [isLoadingTransition, setIsLoadingTransition] = useState(false);

  // Step 2.3: Length Distribution state
  // 步骤 2.3：长度分布状态
  const [lengthResult, setLengthResult] = useState<SectionAnalysisResponse | null>(null);
  const [isLoadingLength, setIsLoadingLength] = useState(false);

  // Expanded section index for details
  // 展开的章节索引
  const [expandedSectionIndex, setExpandedSectionIndex] = useState<number | null>(null);

  // Issue expansion
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

  // Prevent duplicate API calls
  const isAnalyzingRef = useRef(false);

  // Load document text
  useEffect(() => {
    if (documentId) {
      loadDocumentText(documentId);
    }
  }, [documentId]);

  const loadDocumentText = async (docId: string) => {
    try {
      const doc = await documentApi.get(docId);
      // Use originalText field from API (camelCase transformed from original_text)
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

  // Analyze when text is loaded
  useEffect(() => {
    if (documentText && !isAnalyzingRef.current) {
      analyzeSection();
    }
  }, [documentText]);

  // Perform section analysis with document context
  const analyzeSection = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;

    setIsLoading(true);
    setError(null);

    try {
      console.log('Layer 4: Getting document context from Layer 5...');

      // First get document context from Layer 5
      const docContext = await documentLayerApi.getContext(documentText);
      setDocumentContext(docContext as Record<string, unknown>);

      console.log('Layer 4: Analyzing sections with document context...');

      // Run section analysis with context
      const analysisResult = await sectionLayerApi.analyze(
        documentText,
        docContext as Record<string, unknown>
      );
      console.log('Layer 4 result:', analysisResult);
      console.log('Layer 4 sectionDetails:', analysisResult.sectionDetails);
      console.log('Layer 4 lengthDistribution:', analysisResult.lengthDistribution);

      setResult(analysisResult);

      if (onComplete) {
        onComplete(analysisResult);
      }
    } catch (err: unknown) {
      console.error('Section analysis failed:', err);
      const axiosErr = err as { response?: { data?: { detail?: string } } };
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

  // Load Step 2.1 Logic Flow when selected
  // 选择步骤2.1时加载逻辑流分析
  useEffect(() => {
    if (currentStep === '2.1' && documentText && !logicResult && !isLoadingLogic) {
      loadLogicAnalysis();
    }
  }, [currentStep, documentText]);

  // Load Step 2.2 Transitions when selected
  // 选择步骤2.2时加载衔接分析
  useEffect(() => {
    if (currentStep === '2.2' && documentText && !transitionResult && !isLoadingTransition) {
      loadTransitionAnalysis();
    }
  }, [currentStep, documentText]);

  // Load Step 2.3 Length Distribution when selected
  // 选择步骤2.3时加载长度分布分析
  useEffect(() => {
    if (currentStep === '2.3' && documentText && !lengthResult && !isLoadingLength) {
      loadLengthAnalysis();
    }
  }, [currentStep, documentText]);

  // Load Step 2.1 Logic Flow
  // 加载步骤2.1逻辑流分析
  const loadLogicAnalysis = async () => {
    if (!documentText || isLoadingLogic) return;

    setIsLoadingLogic(true);
    try {
      console.log('Step 2.1: Analyzing section logic flow...');
      const result = await sectionLayerApi.analyzeLogic(documentText, documentContext || undefined);
      console.log('Step 2.1 result:', result);
      setLogicResult(result);
    } catch (err) {
      console.error('Logic flow analysis failed:', err);
    } finally {
      setIsLoadingLogic(false);
    }
  };

  // Load Step 2.2 Transitions
  // 加载步骤2.2衔接分析
  const loadTransitionAnalysis = async () => {
    if (!documentText || isLoadingTransition) return;

    setIsLoadingTransition(true);
    try {
      console.log('Step 2.2: Analyzing section transitions...');
      const result = await sectionLayerApi.analyzeTransition(documentText, documentContext || undefined);
      console.log('Step 2.2 result:', result);
      setTransitionResult(result);
    } catch (err) {
      console.error('Transition analysis failed:', err);
    } finally {
      setIsLoadingTransition(false);
    }
  };

  // Load Step 2.3 Length Distribution
  // 加载步骤2.3长度分布分析
  const loadLengthAnalysis = async () => {
    if (!documentText || isLoadingLength) return;

    setIsLoadingLength(true);
    try {
      console.log('Step 2.3: Analyzing section length distribution...');
      const result = await sectionLayerApi.analyzeLength(documentText, documentContext || undefined);
      console.log('Step 2.3 result:', result);
      setLengthResult(result);
    } catch (err) {
      console.error('Length distribution analysis failed:', err);
    } finally {
      setIsLoadingLength(false);
    }
  };

  const handleIssueClick = useCallback((index: number) => {
    setExpandedIssueIndex(prev => prev === index ? null : index);
  }, []);

  // Toggle section expansion
  // 切换章节展开
  const handleSectionClick = useCallback((index: number) => {
    setExpandedSectionIndex(prev => prev === index ? null : index);
  }, []);

  const handleNext = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/layer-paragraph/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

  const handleBack = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/layer-document/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

  const renderRiskBadge = (level: string) => (
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

  const renderSeverityBadge = (severity: string) => (
    <span className={clsx(
      'px-2 py-0.5 rounded text-xs font-medium',
      severity === 'high' && 'bg-red-100 text-red-700',
      severity === 'medium' && 'bg-yellow-100 text-yellow-700',
      severity === 'low' && 'bg-blue-100 text-blue-700'
    )}>
      {severity === 'high' ? '高' : severity === 'medium' ? '中' : '低'}
    </span>
  );

  // Loading state
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
  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex flex-col items-center justify-center min-h-[50vh]">
          <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
          <p className="text-red-600 text-lg mb-4">{error}</p>
          {showNavigation && (
            <Button variant="outline" onClick={handleBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回文章层 / Back to Document Layer
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
            <div className="p-2 rounded-lg bg-purple-100 text-purple-600 mr-3">
              <BookOpen className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Layer 4: 章节层分析
              </h1>
              <p className="text-gray-600 mt-1">
                Section Layer Analysis
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
            className="text-gray-400 hover:text-indigo-600 hover:underline transition-colors"
          >
            Step 1.0 词汇锁定
          </button>
          <span className="mx-2">→</span>
          <span className="text-gray-400">Layer 5 文章</span>
          <span className="mx-2">→</span>
          <span className="font-medium text-purple-600 bg-purple-50 px-2 py-1 rounded">
            Layer 4 章节
          </span>
          <span className="mx-2">→</span>
          <span>Layer 3 段落</span>
          <span className="mx-2">→</span>
          <span>Layer 2 句子</span>
          <span className="mx-2">→</span>
          <span>Layer 1 词汇</span>
        </div>

        {/* Step tabs */}
        <div className="mt-4 flex space-x-2">
          <button
            onClick={() => setCurrentStep('2.1')}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '2.1'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <GitBranch className="w-4 h-4 mr-1" />
            2.1 逻辑流
          </button>
          <button
            onClick={() => setCurrentStep('2.2')}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '2.2'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <ArrowRightLeft className="w-4 h-4 mr-1" />
            2.2 衔接
          </button>
          <button
            onClick={() => setCurrentStep('2.3')}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '2.3'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <BarChart3 className="w-4 h-4 mr-1" />
            2.3 长度分布
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Score Card */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-1">
                  章节层风险分数 / Section Layer Risk Score
                </h3>
                <p className="text-sm text-gray-500">
                  分析章节之间的逻辑关系和衔接质量
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

            {/* Statistics */}
            <div className="mt-4 grid grid-cols-4 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">{result.sectionCount || 0}</p>
                <p className="text-sm text-gray-600">章节数</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">{result.logicFlowScore || 0}</p>
                <p className="text-sm text-gray-600">逻辑流分</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">{result.transitionQuality || 0}</p>
                <p className="text-sm text-gray-600">衔接质量</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">
                  {result.lengthDistribution?.cv?.toFixed(2) || 'N/A'}
                </p>
                <p className="text-sm text-gray-600">长度CV</p>
              </div>
            </div>
          </div>

          {/* Step 2.1: Logic Flow */}
          {/* 步骤 2.1：逻辑流 */}
          {currentStep === '2.1' && (
            <>
              {isLoadingLogic && (
                <div className="card p-6">
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-purple-600 mr-3" />
                    <span className="text-gray-600">分析章节逻辑流... / Analyzing section logic flow...</span>
                  </div>
                </div>
              )}

              {(logicResult || result) && !isLoadingLogic && (
                <div className="space-y-6">
                  {/* Logic Flow Overview / 逻辑流概览 */}
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                      <GitBranch className="w-5 h-5 mr-2 text-purple-600" />
                      章节逻辑流分析 / Section Logic Flow
                    </h3>

                    {/* Detected Roles Flow / 检测到的角色流 */}
                    <div className="mb-6">
                      <h4 className="text-sm font-medium text-gray-600 mb-3">检测到的章节结构 / Detected Section Structure</h4>
                      <div className="flex items-center flex-wrap gap-2">
                        {result.sectionDetails?.map((section, idx) => (
                          <div key={idx} className="flex items-center">
                            <span className={clsx(
                              'px-3 py-2 rounded-lg text-sm font-medium',
                              section.role === 'introduction' && 'bg-blue-100 text-blue-700',
                              section.role === 'literature_review' && 'bg-indigo-100 text-indigo-700',
                              section.role === 'methodology' && 'bg-green-100 text-green-700',
                              section.role === 'results' && 'bg-yellow-100 text-yellow-700',
                              section.role === 'discussion' && 'bg-orange-100 text-orange-700',
                              section.role === 'conclusion' && 'bg-red-100 text-red-700',
                              section.role === 'body' && 'bg-gray-100 text-gray-700',
                              section.role === 'unknown' && 'bg-gray-100 text-gray-500'
                            )}>
                              {section.role === 'introduction' ? '引言 Introduction' :
                               section.role === 'literature_review' ? '文献综述 Literature' :
                               section.role === 'methodology' ? '方法 Methods' :
                               section.role === 'results' ? '结果 Results' :
                               section.role === 'discussion' ? '讨论 Discussion' :
                               section.role === 'conclusion' ? '结论 Conclusion' :
                               section.role === 'body' ? '正文 Body' : section.role}
                            </span>
                            {idx < (result.sectionDetails?.length || 0) - 1 && (
                              <span className="mx-2 text-gray-400">→</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Expected vs Detected / 预期与检测对比 */}
                    <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-600 mb-2">学术论文标准结构 / Expected Academic Structure</h4>
                      <div className="flex items-center flex-wrap gap-2 text-xs text-gray-500">
                        <span className="px-2 py-1 bg-white rounded border">Introduction</span>
                        <span>→</span>
                        <span className="px-2 py-1 bg-white rounded border">Literature Review</span>
                        <span>→</span>
                        <span className="px-2 py-1 bg-white rounded border">Methodology</span>
                        <span>→</span>
                        <span className="px-2 py-1 bg-white rounded border">Results</span>
                        <span>→</span>
                        <span className="px-2 py-1 bg-white rounded border">Discussion</span>
                        <span>→</span>
                        <span className="px-2 py-1 bg-white rounded border">Conclusion</span>
                      </div>
                      <p className="mt-2 text-xs text-gray-500">
                        AI生成文本通常严格遵循此结构，人类写作可能有更灵活的顺序。
                      </p>
                    </div>

                    {/* Order Match Warning / 顺序匹配警告 */}
                    {(logicResult?.details as Record<string, unknown>)?.order_match_score !== undefined &&
                     ((logicResult?.details as Record<string, unknown>)?.order_match_score as number) >= 0.8 && (
                      <div className="p-4 bg-amber-50 border-l-4 border-amber-500 rounded-r-lg mb-4">
                        <div className="flex items-start">
                          <AlertTriangle className="w-5 h-5 text-amber-500 mr-2 mt-0.5" />
                          <div>
                            <p className="font-medium text-amber-800">章节顺序高度可预测</p>
                            <p className="text-sm text-amber-600 mt-1">
                              检测到顺序匹配度: {(((logicResult?.details as Record<string, unknown>)?.order_match_score as number) * 100).toFixed(0)}%。
                              这是AI生成文本的典型特征。考虑打乱章节顺序或整合讨论与结果。
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Section Details / 章节详情 */}
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">
                      章节详情 / Section Details
                    </h3>
                    <div className="space-y-3">
                      {result.sectionDetails?.map((section, idx) => (
                        <div
                          key={idx}
                          onClick={() => handleSectionClick(idx)}
                          className={clsx(
                            'p-4 rounded-lg border transition-all cursor-pointer',
                            section.issues.length > 0 ? 'border-amber-200 bg-amber-50' : 'border-gray-200 bg-gray-50',
                            expandedSectionIndex === idx && 'ring-2 ring-purple-300'
                          )}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-3">
                              <span className="font-medium text-gray-800">
                                章节 {section.index + 1}
                              </span>
                              <span className={clsx(
                                'text-sm px-2 py-1 rounded',
                                section.role === 'introduction' && 'bg-blue-100 text-blue-700',
                                section.role === 'methodology' && 'bg-green-100 text-green-700',
                                section.role === 'results' && 'bg-yellow-100 text-yellow-700',
                                section.role === 'conclusion' && 'bg-red-100 text-red-700',
                                !['introduction', 'methodology', 'results', 'conclusion'].includes(section.role) && 'bg-purple-100 text-purple-700'
                              )}>
                                {section.role}
                              </span>
                            </div>
                            <div className="flex items-center space-x-4 text-sm text-gray-600">
                              <span>{section.wordCount} 词</span>
                              {section.issues.length > 0 && (
                                <span className="text-amber-600 font-medium">
                                  {section.issues.length} 个问题
                                </span>
                              )}
                              {expandedSectionIndex === idx ? (
                                <ChevronUp className="w-4 h-4" />
                              ) : (
                                <ChevronDown className="w-4 h-4" />
                              )}
                            </div>
                          </div>

                          {/* Expanded Issues / 展开的问题 */}
                          {expandedSectionIndex === idx && section.issues.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
                              {section.issues.map((issue, iIdx) => (
                                <p key={iIdx} className="text-sm text-amber-700 bg-amber-100 px-3 py-2 rounded">
                                  {issue}
                                </p>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Step 2.2: Transitions */}
          {/* 步骤 2.2：衔接 */}
          {currentStep === '2.2' && (
            <>
              {isLoadingTransition && (
                <div className="card p-6">
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-purple-600 mr-3" />
                    <span className="text-gray-600">分析章节衔接... / Analyzing section transitions...</span>
                  </div>
                </div>
              )}

              {(transitionResult || result) && !isLoadingTransition && (
                <div className="space-y-6">
                  {/* Transition Overview / 衔接概览 */}
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                      <ArrowRightLeft className="w-5 h-5 mr-2 text-purple-600" />
                      章节衔接分析 / Section Transitions
                    </h3>

                    {/* Transition Quality Score / 衔接质量分数 */}
                    <div className="grid grid-cols-3 gap-4 mb-6">
                      <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 text-center">
                        <div className="text-3xl font-bold text-purple-700">{result.transitionQuality || 0}</div>
                        <div className="text-sm text-purple-600">整体衔接质量</div>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4 text-center">
                        <div className="text-2xl font-bold text-gray-700">{(result.sectionDetails?.length || 1) - 1}</div>
                        <div className="text-sm text-gray-600">衔接点数量</div>
                      </div>
                      <div className={clsx(
                        'rounded-lg p-4 text-center',
                        (result.transitionQuality || 0) >= 70 ? 'bg-green-50' :
                        (result.transitionQuality || 0) >= 40 ? 'bg-yellow-50' : 'bg-red-50'
                      )}>
                        <div className={clsx(
                          'text-2xl font-bold',
                          (result.transitionQuality || 0) >= 70 ? 'text-green-700' :
                          (result.transitionQuality || 0) >= 40 ? 'text-yellow-700' : 'text-red-700'
                        )}>
                          {(result.transitionQuality || 0) >= 70 ? '自然' :
                           (result.transitionQuality || 0) >= 40 ? '一般' : '生硬'}
                        </div>
                        <div className="text-sm text-gray-600">衔接风格</div>
                      </div>
                    </div>

                    {/* Transition Explanation / 衔接说明 */}
                    <div className="p-4 bg-gray-50 rounded-lg mb-4">
                      <p className="text-sm text-gray-600">
                        <strong>衔接分数说明：</strong> 分数越低表示衔接越自然（人类风格），分数越高表示使用显性连接词过多（AI风格）。
                        AI生成文本常使用 "Furthermore", "Moreover", "Additionally" 等显性连接词。
                      </p>
                    </div>
                  </div>

                  {/* Transition Details / 衔接详情 */}
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">
                      衔接点详情 / Transition Details
                    </h3>
                    <div className="space-y-3">
                      {result.sectionDetails?.map((section, idx) => (
                        idx < (result.sectionDetails?.length || 0) - 1 && (
                          <div
                            key={idx}
                            className={clsx(
                              'p-4 rounded-lg border transition-all',
                              (section.transitionScore || 0) >= 70 ? 'border-red-200 bg-red-50' :
                              (section.transitionScore || 0) >= 40 ? 'border-yellow-200 bg-yellow-50' :
                              'border-green-200 bg-green-50'
                            )}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-3">
                                <span className="px-2 py-1 bg-white rounded text-sm font-medium">
                                  {section.role}
                                </span>
                                <span className="text-gray-500">→</span>
                                <span className="px-2 py-1 bg-white rounded text-sm font-medium">
                                  {result.sectionDetails?.[idx + 1]?.role || 'Next'}
                                </span>
                              </div>
                              <div className="flex items-center space-x-3">
                                <span className={clsx(
                                  'px-3 py-1 rounded-full text-sm font-medium',
                                  (section.transitionScore || 0) >= 70 ? 'bg-red-200 text-red-800' :
                                  (section.transitionScore || 0) >= 40 ? 'bg-yellow-200 text-yellow-800' :
                                  'bg-green-200 text-green-800'
                                )}>
                                  {(section.transitionScore || 0) >= 70 ? '显性连接' :
                                   (section.transitionScore || 0) >= 40 ? '中性' : '语义回声'}
                                </span>
                                <span className="text-sm text-gray-600">
                                  分数: {section.transitionScore || 'N/A'}
                                </span>
                              </div>
                            </div>
                          </div>
                        )
                      ))}
                    </div>
                  </div>

                  {/* Transition Issues / 衔接问题 */}
                  {transitionResult?.issues && transitionResult.issues.length > 0 && (
                    <div className="card p-6">
                      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                        <AlertTriangle className="w-5 h-5 mr-2 text-amber-500" />
                        衔接问题 / Transition Issues
                      </h3>
                      <div className="space-y-2">
                        {transitionResult.issues.map((issue: DetectionIssue, idx: number) => (
                          <div key={idx} className="p-3 bg-amber-50 rounded-lg border-l-4 border-amber-500">
                            <p className="font-medium text-amber-800">{issue.descriptionZh}</p>
                            <p className="text-sm text-amber-600 mt-1">{issue.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* Step 2.3: Length Distribution */}
          {/* 步骤 2.3：长度分布 */}
          {currentStep === '2.3' && (
            <>
              {isLoadingLength && (
                <div className="card p-6">
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-purple-600 mr-3" />
                    <span className="text-gray-600">分析章节长度分布... / Analyzing length distribution...</span>
                  </div>
                </div>
              )}

              {(lengthResult || result) && !isLoadingLength && (
                <div className="space-y-6">
                  {/* Length Statistics / 长度统计 */}
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                      <BarChart3 className="w-5 h-5 mr-2 text-purple-600" />
                      章节长度分布 / Section Length Distribution
                    </h3>

                    {/* Statistics Grid / 统计网格 */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 text-center">
                        <div className="text-3xl font-bold text-purple-700">
                          {result.lengthDistribution?.mean?.toFixed(0) || 'N/A'}
                        </div>
                        <div className="text-sm text-purple-600">平均长度 / Mean</div>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4 text-center">
                        <div className="text-2xl font-bold text-gray-700">
                          {result.lengthDistribution?.stdDev?.toFixed(1) || 'N/A'}
                        </div>
                        <div className="text-sm text-gray-600">标准差 / Std Dev</div>
                      </div>
                      <div className={clsx(
                        'rounded-lg p-4 text-center',
                        (result.lengthDistribution?.cv || 0) < 0.4 ? 'bg-red-50' : 'bg-green-50'
                      )}>
                        <div className={clsx(
                          'text-2xl font-bold',
                          (result.lengthDistribution?.cv || 0) < 0.4 ? 'text-red-700' : 'text-green-700'
                        )}>
                          {result.lengthDistribution?.cv?.toFixed(2) || 'N/A'}
                        </div>
                        <div className="text-sm text-gray-600">变异系数 CV</div>
                      </div>
                      <div className={clsx(
                        'rounded-lg p-4 text-center',
                        result.lengthDistribution?.isUniform ? 'bg-amber-50' : 'bg-green-50'
                      )}>
                        <div className={clsx(
                          'text-lg font-bold',
                          result.lengthDistribution?.isUniform ? 'text-amber-700' : 'text-green-700'
                        )}>
                          {result.lengthDistribution?.isUniform ? '过于均匀' : '自然变化'}
                        </div>
                        <div className="text-sm text-gray-600">均匀度判定</div>
                      </div>
                    </div>

                    {/* CV Explanation / CV说明 */}
                    <div className="p-4 bg-gray-50 rounded-lg mb-4">
                      <p className="text-sm text-gray-600">
                        <strong>CV (变异系数):</strong> 当前 {result.lengthDistribution?.cv?.toFixed(2) || 'N/A'}，
                        目标 &gt;= 0.4。CV越低表示章节长度越均匀，是AI生成的典型特征。
                        人类写作通常有更大的长度变化。
                      </p>
                    </div>

                    {/* Uniform Warning / 均匀警告 */}
                    {result.lengthDistribution?.isUniform && (
                      <div className="p-4 bg-amber-50 border-l-4 border-amber-500 rounded-r-lg">
                        <div className="flex items-start">
                          <AlertTriangle className="w-5 h-5 text-amber-500 mr-2 mt-0.5" />
                          <div>
                            <p className="font-medium text-amber-800">章节长度过于均匀</p>
                            <p className="text-sm text-amber-600 mt-1">
                              建议调整章节长度，增加变化。可以合并一些短章节，或将长章节拆分。
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Section Length Visualization / 章节长度可视化 */}
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">
                      章节长度对比 / Section Length Comparison
                    </h3>
                    <div className="space-y-3">
                      {result.sectionDetails?.map((section, idx) => {
                        const maxWordCount = Math.max(...(result.sectionDetails?.map(s => s.wordCount) || [1]));
                        const percentage = (section.wordCount / maxWordCount) * 100;
                        const meanLength = result.lengthDistribution?.mean || 0;
                        const deviation = meanLength > 0 ? ((section.wordCount - meanLength) / meanLength) * 100 : 0;

                        return (
                          <div key={idx} className="space-y-1">
                            <div className="flex items-center justify-between text-sm">
                              <div className="flex items-center space-x-2">
                                <span className="font-medium text-gray-700">
                                  章节 {section.index + 1}
                                </span>
                                <span className="text-gray-500">({section.role})</span>
                              </div>
                              <div className="flex items-center space-x-3">
                                <span className="text-gray-600">{section.wordCount} 词</span>
                                <span className={clsx(
                                  'text-xs px-2 py-0.5 rounded',
                                  Math.abs(deviation) < 20 ? 'bg-green-100 text-green-700' :
                                  Math.abs(deviation) < 50 ? 'bg-yellow-100 text-yellow-700' :
                                  'bg-red-100 text-red-700'
                                )}>
                                  {deviation > 0 ? '+' : ''}{deviation.toFixed(0)}%
                                </span>
                              </div>
                            </div>
                            <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className={clsx(
                                  'h-full rounded-full transition-all',
                                  Math.abs(deviation) < 20 ? 'bg-purple-400' :
                                  Math.abs(deviation) < 50 ? 'bg-purple-500' :
                                  'bg-purple-600'
                                )}
                                style={{ width: `${percentage}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Range Info / 范围信息 */}
                    <div className="mt-4 flex justify-between text-xs text-gray-500">
                      <span>最短: {Math.min(...(result.sectionDetails?.map(s => s.wordCount) || [0]))} 词</span>
                      <span>平均: {result.lengthDistribution?.mean?.toFixed(0) || 'N/A'} 词</span>
                      <span>最长: {Math.max(...(result.sectionDetails?.map(s => s.wordCount) || [0]))} 词</span>
                    </div>
                  </div>

                  {/* Recommendations / 建议 */}
                  {lengthResult?.recommendations && lengthResult.recommendations.length > 0 && (
                    <div className="card p-6">
                      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                        <AlertTriangle className="w-5 h-5 mr-2 text-amber-500" />
                        改进建议 / Recommendations
                      </h3>
                      <ul className="space-y-2">
                        {(lengthResult.recommendationsZh || lengthResult.recommendations).map((rec, idx) => (
                          <li key={idx} className="flex items-start text-sm">
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

          {/* Issues */}
          {result.issues && result.issues.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                检测到 {result.issues.length} 个问题 / {result.issues.length} Issues Detected
              </h3>
              <div className="space-y-3">
                {result.issues.map((issue: DetectionIssue, idx: number) => (
                  <div key={idx}>
                    <div
                      onClick={() => handleIssueClick(idx)}
                      className={clsx(
                        'p-4 rounded-lg border-l-4 cursor-pointer transition-all hover:shadow-md',
                        issue.severity === 'high' && 'bg-red-50 border-red-500',
                        issue.severity === 'medium' && 'bg-yellow-50 border-yellow-500',
                        issue.severity === 'low' && 'bg-blue-50 border-blue-500'
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
                    {expandedIssueIndex === idx && issue.suggestion && (
                      <div className="ml-4 p-4 bg-white border rounded-lg shadow-sm mt-2">
                        <h4 className="font-medium text-gray-800 mb-1">建议 / Suggestion</h4>
                        <p className="text-sm text-gray-600">{issue.suggestionZh || issue.suggestion}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations && result.recommendations.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                改进建议 / Recommendations
              </h3>
              <div className="space-y-2">
                {(result.recommendationsZh || result.recommendations).map((rec, idx) => (
                  <div key={idx} className="p-3 bg-green-50 rounded-lg">
                    <p className="text-sm text-green-800">{rec}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Processing Time */}
          {result.processingTimeMs && (
            <p className="text-xs text-gray-400 text-center">
              分析耗时 {result.processingTimeMs}ms
            </p>
          )}

          {/* Navigation */}
          {showNavigation && (
            <div className="flex justify-between pt-4">
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                返回文章层
              </Button>
              <Button onClick={handleNext}>
                继续到段落层
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
