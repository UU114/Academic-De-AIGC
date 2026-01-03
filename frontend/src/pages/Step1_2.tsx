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
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import LoadingMessage from '../components/common/LoadingMessage';
import { structureApi } from '../services/api';

/**
 * Step 1-2 Page: Paragraph Relationship Analysis
 * 步骤 1-2 页面：段落关系分析
 *
 * Analyzes paragraph relationships: connectors, logic breaks, AI risks
 * 分析段落关系：连接词、逻辑断层、AI风险
 */
export default function Step1_2() {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Processing mode from URL parameter
  // 从URL参数获取处理模式
  const mode = searchParams.get('mode') || 'intervention';

  // Analysis result state
  // 分析结果状态
  const [result, setResult] = useState<{
    explicitConnectors: Array<{
      word: string;
      position: string;
      location: string;
      severity: string;
    }>;
    logicBreaks: Array<{
      fromPosition: string;
      toPosition: string;
      transitionType: string;
      issue: string;
      issueZh: string;
      suggestion: string;
      suggestionZh: string;
    }>;
    paragraphRisks: Array<{
      position: string;
      aiRisk: string;
      aiRiskReason: string;
      openingConnector: string | null;
      rewriteSuggestionZh: string;
    }>;
    relationshipScore: number;
    relationshipIssues: Array<{
      type: string;
      description: string;
      descriptionZh: string;
      severity: string;
      affectedPositions: string[];
    }>;
    scoreBreakdown: Record<string, number>;
  } | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Prevent duplicate API calls
  // 防止重复API调用
  const isAnalyzingRef = useRef(false);

  // Load analysis on mount
  // 挂载时加载分析
  useEffect(() => {
    if (documentId && !isAnalyzingRef.current) {
      analyzeRelationships(documentId);
    }
  }, [documentId]);

  // Analyze paragraph relationships
  // 分析段落关系
  const analyzeRelationships = async (docId: string) => {
    if (isAnalyzingRef.current) return;
    isAnalyzingRef.current = true;

    setIsLoading(true);
    setError(null);
    try {
      console.log('Step 1-2: Analyzing paragraph relationships for ID:', docId);
      const data = await structureApi.analyzeStep1_2(docId);
      console.log('Step 1-2 result:', data);
      setResult(data);
    } catch (err: unknown) {
      console.error('Failed to analyze paragraph relationships:', err);
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.status === 404) {
        setError('文档不存在或未完成 Step 1-1 分析 / Document not found or Step 1-1 not completed');
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

  // Handle continue to Level 2
  // 处理继续到 Level 2
  const handleContinue = useCallback(() => {
    navigate(`/flow/level2/${documentId}?mode=${mode}`);
  }, [documentId, mode, navigate]);

  // Handle skip to Level 2
  // 处理跳过到 Level 2
  const handleSkip = useCallback(() => {
    navigate(`/flow/level2/${documentId}?mode=${mode}`);
  }, [documentId, mode, navigate]);

  // Handle back to Step 1-1
  // 处理返回 Step 1-1
  const handleBack = useCallback(() => {
    navigate(`/flow/step1-1/${documentId}?mode=${mode}`);
  }, [documentId, mode, navigate]);

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
          <Button variant="outline" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回 Step 1-1
          </Button>
        </div>
      </div>
    );
  }

  const highRiskCount = result?.paragraphRisks?.filter(r => r.aiRisk === 'high').length || 0;

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="p-2 rounded-lg bg-blue-100 text-blue-600 mr-3">
              <Link className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Step 1-2: 段落关系分析
              </h1>
              <p className="text-gray-600 mt-1">
                Paragraph Relationship Analysis
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
          <span className="font-medium text-blue-600">Step 1-2</span>
          <span className="mx-2">→</span>
          <span>Level 2</span>
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
                  关系风险分数 / Relationship Risk Score
                </h3>
                <p className="text-sm text-gray-500">
                  越高表示段落关系越可能被检测为AI生成
                </p>
              </div>
              <div className="text-right">
                <p className={clsx(
                  'text-4xl font-bold',
                  result.relationshipScore <= 30 && 'text-green-600',
                  result.relationshipScore > 30 && result.relationshipScore <= 60 && 'text-yellow-600',
                  result.relationshipScore > 60 && 'text-red-600'
                )}>
                  {result.relationshipScore}
                </p>
              </div>
            </div>

            {/* Statistics */}
            {/* 统计信息 */}
            <div className="grid grid-cols-3 gap-4">
              <div className="p-3 bg-amber-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-amber-600">
                  {result.explicitConnectors?.length || 0}
                </p>
                <p className="text-sm text-gray-600">显性连接词</p>
              </div>
              <div className="p-3 bg-red-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-red-600">
                  {result.logicBreaks?.length || 0}
                </p>
                <p className="text-sm text-gray-600">逻辑断层</p>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-purple-600">
                  {highRiskCount}
                </p>
                <p className="text-sm text-gray-600">高风险段落</p>
              </div>
            </div>
          </div>

          {/* Explicit Connectors */}
          {/* 显性连接词 */}
          {result.explicitConnectors && result.explicitConnectors.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <AlertTriangle className="w-5 h-5 text-amber-500 mr-2" />
                显性连接词 ({result.explicitConnectors.length})
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                这些连接词是AI写作的典型特征，建议替换为更自然的表达
              </p>
              <div className="flex flex-wrap gap-2">
                {result.explicitConnectors.map((conn, idx) => (
                  <span
                    key={idx}
                    className={clsx(
                      'px-3 py-1.5 rounded-full text-sm',
                      conn.severity === 'high' && 'bg-red-100 text-red-700',
                      conn.severity === 'medium' && 'bg-yellow-100 text-yellow-700',
                      conn.severity === 'low' && 'bg-gray-100 text-gray-700'
                    )}
                  >
                    "{conn.word}" @ 段落{conn.position}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Logic Breaks */}
          {/* 逻辑断层 */}
          {result.logicBreaks && result.logicBreaks.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                逻辑断层 ({result.logicBreaks.length})
              </h3>
              <div className="space-y-4">
                {result.logicBreaks.map((lb, idx) => (
                  <div key={idx} className="p-4 bg-red-50 rounded-lg border-l-4 border-red-500">
                    <div className="flex items-center text-sm text-red-700 mb-2">
                      <span className="font-medium">
                        段落 {lb.fromPosition} → {lb.toPosition}
                      </span>
                      <span className="mx-2">|</span>
                      <span>{lb.transitionType}</span>
                    </div>
                    <p className="text-red-800 mb-2">{lb.issueZh}</p>
                    <p className="text-green-700 text-sm">
                      <strong>建议：</strong>{lb.suggestionZh}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* High Risk Paragraphs */}
          {/* 高风险段落 */}
          {result.paragraphRisks && result.paragraphRisks.filter(r => r.aiRisk === 'high').length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <AlertTriangle className="w-5 h-5 text-purple-500 mr-2" />
                高风险段落
              </h3>
              <div className="space-y-3">
                {result.paragraphRisks
                  .filter(r => r.aiRisk === 'high')
                  .map((risk, idx) => (
                    <div key={idx} className="p-4 bg-purple-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-purple-800">
                          段落 {risk.position}
                        </span>
                        {risk.openingConnector && (
                          <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                            开头: "{risk.openingConnector}"
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{risk.aiRiskReason}</p>
                      {risk.rewriteSuggestionZh && (
                        <p className="text-sm text-green-700">
                          <strong>改写建议：</strong>{risk.rewriteSuggestionZh}
                        </p>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* No Issues */}
          {/* 无问题 */}
          {(!result.explicitConnectors || result.explicitConnectors.length === 0) &&
           (!result.logicBreaks || result.logicBreaks.length === 0) &&
           highRiskCount === 0 && (
            <div className="card p-6 text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-gray-800">
                段落关系良好
              </h3>
              <p className="text-gray-600 mt-1">
                No obvious relationship issues detected
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
              继续 Level 2
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
