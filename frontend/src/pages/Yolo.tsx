import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Zap,
  StopCircle,
  Loader2,
  AlertCircle,
  CheckCircle,
  ArrowRight,
  TrendingDown,
} from 'lucide-react';
import Button from '../components/common/Button';
import ProgressBar from '../components/common/ProgressBar';
import { sessionApi } from '../services/api';
import { clsx } from 'clsx';

interface ProcessingLog {
  index: number;
  action: 'modified' | 'skipped' | 'already_processed' | 'no_improvement' | 'error';
  message: string;
  originalRisk: number;
  newRisk: number;
  source?: string;
  timestamp: Date;
}

/**
 * YOLO mode page - Automatic processing with real LLM calls
 * YOLO模式页面 - 使用真实 LLM 调用进行自动处理
 */
export default function Yolo() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  // State
  // 状态
  const [status, setStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');
  const [progress, setProgress] = useState({
    total: 0,
    processed: 0,
    skipped: 0,
    avgRiskReduction: 0,
    percent: 0,
  });
  const [logs, setLogs] = useState<ProcessingLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [startTime, setStartTime] = useState<Date | null>(null);

  // Refs
  // 引用
  const logsEndRef = useRef<HTMLDivElement>(null);
  const hasStartedRef = useRef(false);

  // Scroll to bottom of logs
  // 滚动到日志底部
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Start YOLO processing
  // 开始 YOLO 处理
  const startYoloProcessing = useCallback(async () => {
    if (!sessionId || hasStartedRef.current) return;
    hasStartedRef.current = true;

    setStatus('running');
    setStartTime(new Date());

    // Add initial log
    // 添加初始日志
    setLogs([{
      index: 0,
      action: 'modified',
      message: '开始 YOLO 自动处理...',
      originalRisk: 0,
      newRisk: 0,
      timestamp: new Date(),
    }]);

    try {
      // Update session step
      // 更新会话步骤
      await sessionApi.updateStep(sessionId, 'step3');

      // Call the real YOLO processing API
      // 调用真实的 YOLO 处理 API
      const result = await sessionApi.yoloProcess(sessionId);

      // Update progress with final results
      // 用最终结果更新进度
      setProgress({
        total: result.totalSentences,
        processed: result.processed,
        skipped: result.skipped,
        avgRiskReduction: result.avgRiskReduction,
        percent: 100,
      });

      // Convert backend logs to frontend format
      // 将后端日志转换为前端格式
      const processedLogs: ProcessingLog[] = result.logs.map((log) => ({
        index: log.index,
        action: log.action as ProcessingLog['action'],
        message: log.message,
        originalRisk: log.originalRisk,
        newRisk: log.newRisk,
        source: log.source,
        timestamp: new Date(),
      }));

      setLogs(processedLogs);
      setStatus('completed');

    } catch (err) {
      console.error('YOLO processing error:', err);
      setError((err as Error).message);
      setStatus('error');
      setLogs((prev) => [...prev, {
        index: prev.length,
        action: 'error',
        message: `处理失败: ${(err as Error).message}`,
        originalRisk: 0,
        newRisk: 0,
        timestamp: new Date(),
      }]);
    }
  }, [sessionId]);

  // Start processing on mount
  // 挂载时开始处理
  useEffect(() => {
    startYoloProcessing();
  }, [startYoloProcessing]);

  // Handle stop - switch to intervention mode
  // 处理停止 - 切换到干预模式
  const handleStop = async () => {
    navigate(`/intervention/${sessionId}`);
  };

  // Handle complete - go to review page
  // 处理完成 - 前往审核页面
  const handleComplete = async () => {
    if (sessionId) {
      navigate(`/review/${sessionId}`);
    }
  };

  // Calculate elapsed time
  // 计算已用时间
  const getElapsedTime = (): string => {
    if (!startTime) return '0 秒';
    const elapsed = Math.round((new Date().getTime() - startTime.getTime()) / 1000);
    if (elapsed < 60) {
      return `${elapsed} 秒`;
    } else if (elapsed < 3600) {
      return `${Math.floor(elapsed / 60)} 分 ${elapsed % 60} 秒`;
    } else {
      return `${Math.floor(elapsed / 3600)} 小时 ${Math.floor((elapsed % 3600) / 60)} 分`;
    }
  };

  // Get action color class
  // 获取操作颜色类
  const getActionColor = (action: ProcessingLog['action']) => {
    switch (action) {
      case 'modified':
        return 'text-green-600';
      case 'skipped':
      case 'no_improvement':
        return 'text-gray-500';
      case 'already_processed':
        return 'text-blue-500';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-500';
    }
  };

  // Get action background class
  // 获取操作背景类
  const getActionBg = (action: ProcessingLog['action']) => {
    switch (action) {
      case 'modified':
        return 'bg-green-50';
      case 'skipped':
      case 'no_improvement':
        return 'bg-gray-100';
      case 'already_processed':
        return 'bg-blue-50';
      case 'error':
        return 'bg-red-50';
      default:
        return 'bg-gray-50';
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      {/* Header */}
      {/* 头部 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <div className="p-2 rounded-lg bg-amber-100 text-amber-600 mr-3">
            <Zap className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">YOLO 模式</h1>
            <p className="text-gray-600">Auto Mode - 使用 LLM 自动处理句子</p>
          </div>
        </div>

        {/* Status Badge */}
        {/* 状态标签 */}
        <div
          className={clsx(
            'px-3 py-1 rounded-full text-sm font-medium',
            status === 'idle' && 'bg-gray-100 text-gray-700',
            status === 'running' && 'bg-green-100 text-green-700',
            status === 'completed' && 'bg-blue-100 text-blue-700',
            status === 'error' && 'bg-red-100 text-red-700'
          )}
        >
          {status === 'idle' && '准备中'}
          {status === 'running' && (
            <span className="flex items-center">
              <Loader2 className="w-3 h-3 animate-spin mr-1" />
              处理中
            </span>
          )}
          {status === 'completed' && '已完成'}
          {status === 'error' && '错误'}
        </div>
      </div>

      {/* Progress Section */}
      {/* 进度区域 */}
      <div className="card p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <span className="font-medium text-gray-800">处理进度 / Processing Progress</span>
          <span className="text-sm text-gray-500">
            {status === 'running' ? '处理中...' : `${progress.processed + progress.skipped} / ${progress.total} 句`}
          </span>
        </div>

        <ProgressBar
          value={progress.percent}
          color={status === 'completed' ? 'success' : 'primary'}
          size="lg"
          showLabel
        />

        {/* Stats */}
        {/* 统计 */}
        <div className="grid grid-cols-4 gap-4 mt-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-primary-600">{progress.total}</p>
            <p className="text-sm text-gray-500">总句子</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-green-600">{progress.processed}</p>
            <p className="text-sm text-gray-500">已修改</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-600">{progress.skipped}</p>
            <p className="text-sm text-gray-500">已跳过</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center">
              <TrendingDown className="w-4 h-4 text-green-500 mr-1" />
              <p className="text-2xl font-bold text-green-600">{progress.avgRiskReduction}</p>
            </div>
            <p className="text-sm text-gray-500">平均降风险</p>
          </div>
        </div>

        {/* Elapsed Time */}
        {/* 已用时间 */}
        {startTime && (
          <p className="text-sm text-gray-500 text-center mt-4">
            已用时间: {getElapsedTime()}
          </p>
        )}
      </div>

      {/* Control Buttons */}
      {/* 控制按钮 */}
      <div className="flex justify-center space-x-4 mb-6">
        {status === 'running' && (
          <Button variant="outline" onClick={handleStop}>
            <StopCircle className="w-4 h-4 mr-2" />
            切换为干预模式
          </Button>
        )}

        {status === 'completed' && (
          <Button variant="primary" onClick={handleComplete}>
            查看结果
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        )}

        {status === 'error' && (
          <>
            <Button variant="outline" onClick={handleStop}>
              切换为干预模式
            </Button>
            <Button variant="primary" onClick={() => navigate('/upload')}>
              返回上传
            </Button>
          </>
        )}
      </div>

      {/* Error Message */}
      {/* 错误消息 */}
      {error && (
        <div className="flex items-center p-4 mb-6 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Processing Logs */}
      {/* 处理日志 */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          处理日志 / Processing Logs
        </h2>

        <div className="h-80 overflow-y-auto bg-gray-50 rounded-lg p-4 font-mono text-sm">
          {logs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-400">
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              等待处理开始...
            </div>
          ) : (
            <div className="space-y-2">
              {logs.map((log, idx) => (
                <div
                  key={idx}
                  className={clsx(
                    'flex items-start p-2 rounded',
                    getActionBg(log.action)
                  )}
                >
                  <span className="text-gray-400 mr-2 flex-shrink-0">
                    [{log.timestamp.toLocaleTimeString()}]
                  </span>
                  <span
                    className={clsx(
                      'font-medium mr-2 flex-shrink-0',
                      getActionColor(log.action)
                    )}
                  >
                    #{log.index}
                  </span>
                  <span className="text-gray-700 flex-1">{log.message}</span>
                  {log.action === 'modified' && (
                    <span className="text-xs text-green-600 flex-shrink-0 ml-2">
                      {log.originalRisk} → {log.newRisk}
                      {log.source && ` (${log.source.toUpperCase()})`}
                    </span>
                  )}
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Completion Message */}
      {/* 完成消息 */}
      {status === 'completed' && (
        <div className="card p-6 mt-6 bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
          <div className="flex items-center">
            <CheckCircle className="w-8 h-8 text-green-500 mr-4" />
            <div>
              <h3 className="text-lg font-semibold text-gray-800">
                YOLO 自动处理完成！
              </h3>
              <p className="text-gray-600">
                已处理 {progress.processed} 句，跳过 {progress.skipped} 句，
                平均风险降低 {progress.avgRiskReduction} 分
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
