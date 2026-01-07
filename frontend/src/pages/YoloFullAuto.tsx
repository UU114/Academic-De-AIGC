import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Loader2,
  CheckCircle,
  AlertCircle,
  FileText,
  Link,
  Type,
  Zap,
  ArrowRight,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import { sessionApi } from '../services/api';

/**
 * Step log entry type
 * 步骤日志条目类型
 */
interface StepLog {
  step: string;
  action: string;
  message: string;
  issuesCount?: number;
  changesCount?: number;
  processed?: number;
  skipped?: number;
  avgRiskReduction?: number;
}

/**
 * Step status type
 * 步骤状态类型
 */
type StepStatus = 'pending' | 'processing' | 'completed' | 'error';

/**
 * Step info type
 * 步骤信息类型
 */
interface StepInfo {
  id: string;
  name: string;
  nameEn: string;
  icon: React.ReactNode;
  status: StepStatus;
  logs: StepLog[];
}

/**
 * YOLO Full Auto Processing Page
 * YOLO 全自动处理页面
 *
 * This page automatically processes the document through all steps:
 * 1. Step 1-1: Structure analysis → Auto-select all issues → AI modify
 * 2. Step 1-2: Paragraph analysis → Auto-select all issues → AI modify
 * 3. Step 2: Transition analysis → Auto-select all issues → AI modify
 * 4. Step 3: Sentence-level processing (medium/high risk only)
 */
export default function YoloFullAuto() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const hasStartedRef = useRef(false);

  // Processing state
  // 处理状态
  const [isProcessing, setIsProcessing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<string>('step1-1');

  // Steps configuration
  // 步骤配置
  const [steps, setSteps] = useState<StepInfo[]>([
    {
      id: 'step1-1',
      name: '结构分析',
      nameEn: 'Structure Analysis',
      icon: <FileText className="w-5 h-5" />,
      status: 'pending',
      logs: [],
    },
    {
      id: 'step1-2',
      name: '段落关系',
      nameEn: 'Paragraph Relationships',
      icon: <Type className="w-5 h-5" />,
      status: 'pending',
      logs: [],
    },
    {
      id: 'step2',
      name: '段落衔接',
      nameEn: 'Paragraph Transitions',
      icon: <Link className="w-5 h-5" />,
      status: 'pending',
      logs: [],
    },
    {
      id: 'step3',
      name: '句子精修',
      nameEn: 'Sentence Polish',
      icon: <Zap className="w-5 h-5" />,
      status: 'pending',
      logs: [],
    },
  ]);

  // Start processing on mount
  // 挂载时开始处理
  useEffect(() => {
    if (sessionId && !hasStartedRef.current) {
      hasStartedRef.current = true;
      startFullAutoProcess();
    }
  }, [sessionId]);

  // Full auto process
  // 全自动处理
  const startFullAutoProcess = async () => {
    if (!sessionId) return;

    setIsProcessing(true);
    setError(null);

    // Set step1-1 as processing
    // 设置 step1-1 为处理中
    updateStepStatus('step1-1', 'processing');

    try {
      // Call the full auto API
      // 调用全自动API
      const result = await sessionApi.yoloFullAuto(sessionId);

      // Process logs and update steps
      // 处理日志并更新步骤
      if (result.logs) {
        const stepLogs: Record<string, StepLog[]> = {
          'step1-1': [],
          'step1-2': [],
          'step2': [],
          'step3': [],
          'complete': [],
        };

        // Group logs by step
        // 按步骤分组日志
        for (const log of result.logs) {
          const step = log.step || 'complete';
          if (stepLogs[step]) {
            stepLogs[step].push(log);
          }
        }

        // Update all steps with their logs
        // 用日志更新所有步骤
        setSteps((prev) =>
          prev.map((step) => {
            const logs = stepLogs[step.id] || [];
            const hasError = logs.some((l) => l.action === 'error');
            const isComplete = logs.some(
              (l) => l.action === 'completed' || l.action === 'modified' || l.action === 'no_issues' || l.action === 'no_changes'
            );
            return {
              ...step,
              logs,
              status: hasError ? 'error' : isComplete ? 'completed' : step.status,
            };
          })
        );
      }

      // Mark all steps as completed
      // 标记所有步骤为已完成
      setSteps((prev) =>
        prev.map((step) => ({
          ...step,
          status: step.status === 'pending' ? 'completed' : step.status,
        }))
      );

      setIsProcessing(false);

      // Auto-navigate to review page after 2 seconds
      // 2秒后自动跳转到审核页面
      setTimeout(() => {
        navigate(`/review/${sessionId}`);
      }, 2000);
    } catch (err: unknown) {
      console.error('YOLO full auto process error:', err);
      const errorMsg = err instanceof Error ? err.message : 'Processing failed';
      setError(errorMsg);
      setIsProcessing(false);

      // Mark current step as error
      // 标记当前步骤为错误
      setSteps((prev) =>
        prev.map((step) => ({
          ...step,
          status: step.status === 'processing' ? 'error' : step.status,
        }))
      );
    }
  };

  // Update step status
  // 更新步骤状态
  const updateStepStatus = (stepId: string, status: StepStatus) => {
    setSteps((prev) =>
      prev.map((step) => (step.id === stepId ? { ...step, status } : step))
    );
    setCurrentStep(stepId);
  };

  // Get step status icon
  // 获取步骤状态图标
  const getStepStatusIcon = (status: StepStatus) => {
    switch (status) {
      case 'processing':
        return <Loader2 className="w-5 h-5 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <div className="w-5 h-5 rounded-full border-2 border-gray-300" />;
    }
  };

  // Get step background color
  // 获取步骤背景颜色
  const getStepBgColor = (status: StepStatus) => {
    switch (status) {
      case 'processing':
        return 'bg-blue-50 border-blue-200';
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-8 text-center">
        <div className="inline-flex items-center justify-center p-3 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 text-white mb-4">
          <Zap className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-bold text-gray-800">
          YOLO 全自动处理
        </h1>
        <p className="text-gray-600 mt-2">
          YOLO Full Auto Processing
        </p>
        <p className="text-sm text-gray-500 mt-1">
          系统正在自动处理您的文档，请稍候...
        </p>
      </div>

      {/* Steps Progress */}
      <div className="space-y-4 mb-8">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={clsx(
              'rounded-lg border-2 p-4 transition-all',
              getStepBgColor(step.status)
            )}
          >
            {/* Step Header */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <div
                  className={clsx(
                    'w-8 h-8 rounded-full flex items-center justify-center mr-3',
                    step.status === 'processing' && 'bg-blue-100 text-blue-600',
                    step.status === 'completed' && 'bg-green-100 text-green-600',
                    step.status === 'error' && 'bg-red-100 text-red-600',
                    step.status === 'pending' && 'bg-gray-100 text-gray-400'
                  )}
                >
                  {step.icon}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800">
                    Step {index === 0 ? '1-1' : index === 1 ? '1-2' : index + 1 - 1}: {step.name}
                  </h3>
                  <p className="text-sm text-gray-500">{step.nameEn}</p>
                </div>
              </div>
              {getStepStatusIcon(step.status)}
            </div>

            {/* Step Logs */}
            {step.logs.length > 0 && (
              <div className="mt-3 space-y-1">
                {step.logs.map((log, logIdx) => (
                  <div
                    key={logIdx}
                    className={clsx(
                      'text-sm px-3 py-1 rounded',
                      log.action === 'error' && 'bg-red-100 text-red-700',
                      log.action === 'modified' && 'bg-green-100 text-green-700',
                      log.action === 'found_issues' && 'bg-amber-100 text-amber-700',
                      log.action === 'no_issues' && 'bg-blue-100 text-blue-700',
                      log.action === 'no_changes' && 'bg-gray-100 text-gray-600',
                      !['error', 'modified', 'found_issues', 'no_issues', 'no_changes'].includes(log.action) &&
                        'bg-gray-100 text-gray-600'
                    )}
                  >
                    {log.message}
                    {log.changesCount !== undefined && log.changesCount > 0 && (
                      <span className="ml-2 font-medium">
                        ({log.changesCount} changes)
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Processing indicator for current step */}
            {step.status === 'processing' && step.logs.length === 0 && (
              <div className="mt-2 flex items-center text-sm text-blue-600">
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                处理中... / Processing...
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Completion Message */}
      {!isProcessing && !error && (
        <div className="card p-6 bg-green-50 border border-green-200 text-center">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-green-800">
            处理完成！
          </h3>
          <p className="text-green-600 mt-1">
            Processing completed! Redirecting to review page...
          </p>
          <p className="text-sm text-green-500 mt-2">
            正在跳转到审核页面...
          </p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="card p-6 bg-red-50 border border-red-200">
          <div className="flex items-start">
            <AlertCircle className="w-6 h-6 text-red-500 mr-3 flex-shrink-0" />
            <div>
              <h3 className="text-lg font-semibold text-red-800">
                处理出错 / Processing Error
              </h3>
              <p className="text-red-600 mt-1">{error}</p>
            </div>
          </div>
          <div className="mt-4 flex justify-end space-x-3">
            <Button variant="outline" onClick={() => navigate('/upload')}>
              返回上传 / Back to Upload
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                hasStartedRef.current = false;
                startFullAutoProcess();
              }}
            >
              重试 / Retry
            </Button>
          </div>
        </div>
      )}

      {/* Manual Navigation (in case auto-redirect fails) */}
      {!isProcessing && !error && (
        <div className="mt-4 text-center">
          <Button
            variant="primary"
            onClick={() => navigate(`/review/${sessionId}`)}
          >
            立即查看结果 / View Results Now
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
