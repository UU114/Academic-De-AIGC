import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Link,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  SkipForward,
  CheckCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import LoadingMessage from '../components/common/LoadingMessage';
import TransitionPanel from '../components/editor/TransitionPanel';
import { transitionApi } from '../services/api';
import type { DocumentTransitionSummary, TransitionAnalysisResponse } from '../types';

/**
 * Level 2 Page: Transition Analysis
 * Level 2 页面：衔接分析
 *
 * Analyzes paragraph transitions and provides repair options
 * 分析段落衔接并提供修复选项
 */
export default function Level2() {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Processing mode from URL parameter
  // 从URL参数获取处理模式
  const mode = searchParams.get('mode') || 'intervention';

  // Analysis result state
  // 分析结果状态
  const [result, setResult] = useState<DocumentTransitionSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Expanded transition index
  // 展开的衔接索引
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  // Prevent duplicate API calls
  // 防止重复API调用
  const isAnalyzingRef = useRef(false);

  // Load analysis on mount
  // 挂载时加载分析
  useEffect(() => {
    if (documentId && !isAnalyzingRef.current) {
      analyzeTransitions(documentId);
    }
  }, [documentId]);

  // Analyze document transitions
  // 分析文档衔接
  const analyzeTransitions = async (docId: string) => {
    if (isAnalyzingRef.current) return;
    isAnalyzingRef.current = true;

    setIsLoading(true);
    setError(null);
    try {
      console.log('Level 2: Analyzing transitions for ID:', docId);
      const data = await transitionApi.analyzeDocument(docId);
      console.log('Level 2 result:', data);
      setResult(data);
    } catch (err: unknown) {
      console.error('Failed to analyze transitions:', err);
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.status === 404) {
        setError('文档不存在或未完成前置分析 / Document not found or prerequisites not completed');
      } else if (axiosErr.response?.data?.detail) {
        setError(axiosErr.response.data.detail);
      } else {
        setError(err instanceof Error ? err.message : 'Analysis failed');
      }
    } finally {
      setIsLoading(false);
      isAnalyzingRef.current = false;
    }
  };

  // Handle continue to Level 3 (Intervention)
  // 处理继续到 Level 3（干预页面）
  const handleContinue = useCallback(() => {
    // Level 3 goes to intervention page with the document
    // Level 3 跳转到干预页面
    navigate(`/intervention/${documentId}?mode=${mode}`);
  }, [documentId, mode, navigate]);

  // Handle skip to Level 3
  // 处理跳过到 Level 3
  const handleSkip = useCallback(() => {
    navigate(`/intervention/${documentId}?mode=${mode}`);
  }, [documentId, mode, navigate]);

  // Handle back to Step 1-2
  // 处理返回 Step 1-2
  const handleBack = useCallback(() => {
    navigate(`/flow/step1-2/${documentId}?mode=${mode}`);
  }, [documentId, mode, navigate]);

  // Toggle transition expansion
  // 切换衔接展开状态
  const toggleExpand = useCallback((index: number) => {
    setExpandedIndex(prev => prev === index ? null : index);
  }, []);

  // Loading state
  // 加载状态
  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex items-center justify-center min-h-[50vh]">
          <LoadingMessage category="transition" size="lg" showEnglish={true} />
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
          <Button variant="outline" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回 Step 1-2
          </Button>
        </div>
      </div>
    );
  }

  // Get risk color for score display
  // 获取分数显示的风险颜色
  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="p-2 rounded-lg bg-teal-100 text-teal-600 mr-3">
              <Link className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Level 2: 段落衔接
              </h1>
              <p className="text-gray-600 mt-1">
                Paragraph Transition Analysis
              </p>
            </div>
          </div>
          <Button variant="outline" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回
          </Button>
        </div>

        {/* Progress indicator */}
        {/* 进度指示器 */}
        <div className="mt-4 flex items-center text-sm text-gray-500">
          <span className="text-green-600">Step 1-1 ✓</span>
          <span className="mx-2">→</span>
          <span className="text-green-600">Step 1-2 ✓</span>
          <span className="mx-2">→</span>
          <span className="font-medium text-teal-600">Level 2</span>
          <span className="mx-2">→</span>
          <span>Level 3</span>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Score Card */}
          {/* 分数卡片 */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-1">
                  平均衔接分数 / Average Smoothness Score
                </h3>
                <p className="text-sm text-gray-500">
                  越高表示段落间过渡越自然
                </p>
              </div>
              <div className="text-right">
                <p className={clsx('text-4xl font-bold', getScoreColor(result.avgSmoothnessScore))}>
                  {result.avgSmoothnessScore}
                </p>
              </div>
            </div>

            {/* Statistics */}
            {/* 统计信息 */}
            <div className="grid grid-cols-4 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-gray-600">
                  {result.totalTransitions}
                </p>
                <p className="text-sm text-gray-600">总衔接数</p>
              </div>
              <div className="p-3 bg-red-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-red-600">
                  {result.highRiskCount}
                </p>
                <p className="text-sm text-gray-600">高风险</p>
              </div>
              <div className="p-3 bg-amber-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-amber-600">
                  {result.mediumRiskCount}
                </p>
                <p className="text-sm text-gray-600">中风险</p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-green-600">
                  {result.lowRiskCount}
                </p>
                <p className="text-sm text-gray-600">低风险</p>
              </div>
            </div>
          </div>

          {/* Common Issues */}
          {/* 常见问题 */}
          {result.commonIssues && result.commonIssues.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <AlertTriangle className="w-5 h-5 text-amber-500 mr-2" />
                常见问题类型
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.commonIssues.map((issue, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 bg-amber-100 text-amber-700 rounded-full text-sm"
                  >
                    {issue}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Transitions List */}
          {/* 衔接列表 */}
          {result.transitions && result.transitions.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800">
                衔接详情 ({result.transitions.length} 处)
              </h3>

              {result.transitions.map((transition: TransitionAnalysisResponse, idx: number) => (
                <div key={idx} className="space-y-2">
                  {/* Compact Card Header */}
                  {/* 紧凑卡片头部 */}
                  <div
                    className={clsx(
                      'p-4 rounded-lg border-2 cursor-pointer transition-all',
                      transition.riskLevel === 'high' && 'border-red-300 bg-red-50 hover:bg-red-100',
                      transition.riskLevel === 'medium' && 'border-amber-300 bg-amber-50 hover:bg-amber-100',
                      transition.riskLevel === 'low' && 'border-green-300 bg-green-50 hover:bg-green-100'
                    )}
                    onClick={() => toggleExpand(idx)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span className="font-medium text-gray-700">
                          衔接 #{idx + 1}
                        </span>
                        <span className={clsx(
                          'px-2 py-0.5 rounded text-xs font-medium',
                          transition.riskLevel === 'high' && 'bg-red-200 text-red-700',
                          transition.riskLevel === 'medium' && 'bg-amber-200 text-amber-700',
                          transition.riskLevel === 'low' && 'bg-green-200 text-green-700'
                        )}>
                          {transition.smoothnessScore} 分
                        </span>
                        {transition.explicitConnectors.length > 0 && (
                          <span className="text-xs text-red-600">
                            显性连接词: {transition.explicitConnectors.slice(0, 2).join(', ')}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        {transition.issues.length > 0 && (
                          <span className="text-xs text-gray-500">
                            {transition.issues.length} 个问题
                          </span>
                        )}
                        {expandedIndex === idx ? (
                          <ChevronUp className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                    </div>

                    {/* Preview text */}
                    {/* 预览文本 */}
                    {expandedIndex !== idx && (
                      <p className="text-sm text-gray-600 mt-2 line-clamp-1">
                        {transition.paraBOpening.slice(0, 100)}...
                      </p>
                    )}
                  </div>

                  {/* Expanded Panel */}
                  {/* 展开面板 */}
                  {expandedIndex === idx && (
                    <TransitionPanel
                      analysis={transition}
                      transitionIndex={idx + 1}
                      onSkip={() => setExpandedIndex(null)}
                    />
                  )}
                </div>
              ))}
            </div>
          )}

          {/* No transitions */}
          {/* 无衔接 */}
          {(!result.transitions || result.transitions.length === 0) && (
            <div className="card p-6 text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-gray-800">
                无需分析衔接
              </h3>
              <p className="text-gray-600 mt-1">
                Document has only one paragraph or no transitions to analyze
              </p>
            </div>
          )}

          {/* All low risk message */}
          {/* 全部低风险消息 */}
          {result.transitions &&
           result.transitions.length > 0 &&
           result.highRiskCount === 0 &&
           result.mediumRiskCount === 0 && (
            <div className="card p-6 bg-green-50 border border-green-200 text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-green-800">
                衔接质量良好
              </h3>
              <p className="text-green-600 mt-1">
                All transitions are natural and low risk
              </p>
            </div>
          )}

          {/* Action Buttons */}
          {/* 操作按钮 */}
          <div className="flex justify-end space-x-4 pt-4">
            <Button variant="outline" onClick={handleSkip}>
              <SkipForward className="w-4 h-4 mr-2" />
              跳过此步
            </Button>
            <Button variant="primary" onClick={handleContinue}>
              继续 Level 3
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
