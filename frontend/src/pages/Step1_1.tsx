import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Layers,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  SkipForward,
  CheckCircle,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import LoadingMessage from '../components/common/LoadingMessage';
import { structureApi } from '../services/api';

/**
 * Step 1-1 Page: Document Structure Analysis
 * 步骤 1-1 页面：全文结构分析
 *
 * Analyzes document structure: sections, paragraphs, global patterns
 * 分析文档结构：章节、段落、全局模式
 */
export default function Step1_1() {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Processing mode from URL parameter
  // 从URL参数获取处理模式
  const mode = searchParams.get('mode') || 'intervention';

  // Analysis result state
  // 分析结果状态
  const [result, setResult] = useState<{
    sections: Array<{
      number: string;
      title: string;
      paragraphs: Array<{
        position: string;
        summary: string;
        summaryZh: string;
        firstSentence: string;
        lastSentence: string;
        wordCount: number;
      }>;
    }>;
    totalParagraphs: number;
    totalSections: number;
    structureScore: number;
    riskLevel: string;
    structureIssues: Array<{
      type: string;
      description: string;
      descriptionZh: string;
      severity: string;
      affectedPositions: string[];
    }>;
    scoreBreakdown: Record<string, number>;
    recommendationZh: string;
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
      analyzeStructure(documentId);
    }
  }, [documentId]);

  // Analyze document structure
  // 分析文档结构
  const analyzeStructure = async (docId: string) => {
    if (isAnalyzingRef.current) return;
    isAnalyzingRef.current = true;

    setIsLoading(true);
    setError(null);
    try {
      console.log('Step 1-1: Analyzing document structure for ID:', docId);
      const data = await structureApi.analyzeStep1_1(docId);
      console.log('Step 1-1 result:', data);
      setResult(data);
    } catch (err: unknown) {
      console.error('Failed to analyze document structure:', err);
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.status === 404) {
        setError('文档不存在，请返回上传页面重新上传 / Document not found');
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

  // Handle continue to Step 1-2
  // 处理继续到 Step 1-2
  const handleContinue = useCallback(() => {
    navigate(`/flow/step1-2/${documentId}?mode=${mode}`);
  }, [documentId, mode, navigate]);

  // Handle skip to Step 1-2
  // 处理跳过到 Step 1-2
  const handleSkip = useCallback(() => {
    navigate(`/flow/step1-2/${documentId}?mode=${mode}`);
  }, [documentId, mode, navigate]);

  // Handle back to upload
  // 处理返回上传页面
  const handleBack = useCallback(() => {
    navigate('/upload');
  }, [navigate]);

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
            返回上传
          </Button>
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
              <Layers className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Step 1-1: 全文结构分析
              </h1>
              <p className="text-gray-600 mt-1">
                Document Structure Analysis
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
          <span className="font-medium text-indigo-600">Step 1-1</span>
          <span className="mx-2">→</span>
          <span>Step 1-2</span>
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
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-1">
                  结构风险分数 / Structure Risk Score
                </h3>
                <p className="text-sm text-gray-500">
                  越高表示越容易被检测为AI生成
                </p>
              </div>
              <div className="text-right">
                <p className={clsx(
                  'text-4xl font-bold',
                  result.structureScore <= 30 && 'text-green-600',
                  result.structureScore > 30 && result.structureScore <= 60 && 'text-yellow-600',
                  result.structureScore > 60 && 'text-red-600'
                )}>
                  {result.structureScore}
                </p>
                <p className={clsx(
                  'text-sm font-medium',
                  result.riskLevel === 'low' && 'text-green-600',
                  result.riskLevel === 'medium' && 'text-yellow-600',
                  result.riskLevel === 'high' && 'text-red-600'
                )}>
                  {result.riskLevel === 'low' ? '低风险 Low Risk' :
                   result.riskLevel === 'medium' ? '中风险 Medium Risk' : '高风险 High Risk'}
                </p>
              </div>
            </div>

            {/* Statistics */}
            {/* 统计信息 */}
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-indigo-600">{result.totalSections}</p>
                <p className="text-sm text-gray-600">章节数 Sections</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-indigo-600">{result.totalParagraphs}</p>
                <p className="text-sm text-gray-600">段落数 Paragraphs</p>
              </div>
            </div>
          </div>

          {/* Structure Issues */}
          {/* 结构问题 */}
          {result.structureIssues && result.structureIssues.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                检测到 {result.structureIssues.length} 个结构问题
              </h3>
              <div className="space-y-3">
                {result.structureIssues.map((issue, idx) => (
                  <div
                    key={idx}
                    className={clsx(
                      'p-4 rounded-lg border-l-4',
                      issue.severity === 'high' && 'bg-red-50 border-red-500',
                      issue.severity === 'medium' && 'bg-yellow-50 border-yellow-500',
                      issue.severity === 'low' && 'bg-blue-50 border-blue-500'
                    )}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-gray-800">{issue.descriptionZh}</p>
                        <p className="text-sm text-gray-500 mt-1">{issue.description}</p>
                      </div>
                      <span className={clsx(
                        'px-2 py-1 rounded text-xs font-medium',
                        issue.severity === 'high' && 'bg-red-100 text-red-700',
                        issue.severity === 'medium' && 'bg-yellow-100 text-yellow-700',
                        issue.severity === 'low' && 'bg-blue-100 text-blue-700'
                      )}>
                        {issue.severity === 'high' ? '高' : issue.severity === 'medium' ? '中' : '低'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No Issues */}
          {/* 无问题 */}
          {(!result.structureIssues || result.structureIssues.length === 0) && (
            <div className="card p-6 text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-gray-800">
                未检测到明显结构问题
              </h3>
              <p className="text-gray-600 mt-1">
                No obvious structure issues detected
              </p>
            </div>
          )}

          {/* Recommendation */}
          {/* 建议 */}
          {result.recommendationZh && (
            <div className="card p-6 bg-blue-50 border border-blue-200">
              <h3 className="font-semibold text-blue-800 mb-2">改进建议</h3>
              <p className="text-blue-700">{result.recommendationZh}</p>
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
              继续 Step 1-2
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
