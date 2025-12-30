import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Zap,
  Pause,
  Play,
  StopCircle,
  Loader2,
  AlertCircle,
  CheckCircle,
  ArrowRight,
} from 'lucide-react';
import Button from '../components/common/Button';
import ProgressBar from '../components/common/ProgressBar';
import { sessionApi } from '../services/api';
import { clsx } from 'clsx';

interface ProcessingLog {
  index: number;
  sentence: string;
  action: 'modified' | 'skipped' | 'error';
  message: string;
  timestamp: Date;
}

/**
 * YOLO mode page - Automatic processing with progress display
 * YOLO模式页面 - 自动处理并显示进度
 */
export default function Yolo() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  // State
  // 状态
  const [status, setStatus] = useState<'running' | 'paused' | 'completed' | 'error'>('running');
  const [progress, setProgress] = useState({
    total: 0,
    processed: 0,
    skipped: 0,
    flagged: 0,
    percent: 0,
  });
  const [logs, setLogs] = useState<ProcessingLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [estimatedRemaining, setEstimatedRemaining] = useState<number | null>(null);

  // Refs
  // 引用
  const logsEndRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Scroll to bottom of logs
  // 滚动到日志底部
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Start polling for progress
  // 开始轮询进度
  useEffect(() => {
    if (!sessionId) return;

    const pollProgress = async () => {
      try {
        const data = await sessionApi.getProgress(sessionId);

        setProgress({
          total: data.total,
          processed: data.processed,
          skipped: data.skipped,
          flagged: data.flagged,
          percent: data.progressPercent,
        });

        // Simulate processing logs (in real app, would come from backend)
        // 模拟处理日志（实际应用中会从后端获取）
        if (data.processed > logs.length) {
          const newLog: ProcessingLog = {
            index: data.processed,
            sentence: `Sentence ${data.processed} processed...`,
            action: Math.random() > 0.2 ? 'modified' : 'skipped',
            message: Math.random() > 0.2 ? '已应用LLM建议修改' : '风险较低，已跳过',
            timestamp: new Date(),
          };
          setLogs((prev) => [...prev, newLog]);
        }

        // Estimate remaining time (simplified calculation)
        // 估算剩余时间（简化计算）
        if (data.processed > 0) {
          const avgTimePerSentence = 2; // seconds
          const remaining = (data.total - data.processed) * avgTimePerSentence;
          setEstimatedRemaining(remaining);
        }

        // Check if completed
        // 检查是否完成
        if (data.status === 'completed' || data.processed >= data.total) {
          setStatus('completed');
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
          }
        }
      } catch (err) {
        setError((err as Error).message);
        setStatus('error');
        if (pollingRef.current) {
          clearInterval(pollingRef.current);
        }
      }
    };

    // Initial poll
    // 初始轮询
    pollProgress();

    // Set up polling interval
    // 设置轮询间隔
    pollingRef.current = setInterval(pollProgress, 2000);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [sessionId]);

  // Handle pause/resume
  // 处理暂停/继续
  const handlePauseResume = () => {
    if (status === 'running') {
      setStatus('paused');
      // In real implementation, would call API to pause session
      // 实际实现中会调用API暂停会话
    } else if (status === 'paused') {
      setStatus('running');
      // In real implementation, would call API to resume session
      // 实际实现中会调用API继续会话
    }
  };

  // Handle stop
  // 处理停止
  const handleStop = async () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }
    setStatus('paused');
    // Navigate to intervention mode for manual review
    // 导航到干预模式进行手动审核
    navigate(`/intervention/${sessionId}`);
  };

  // Handle complete
  // 处理完成
  const handleComplete = async () => {
    if (sessionId) {
      try {
        await sessionApi.complete(sessionId);
        navigate(`/review/${sessionId}`);
      } catch (err) {
        setError((err as Error).message);
      }
    }
  };

  // Format time remaining
  // 格式化剩余时间
  const formatTimeRemaining = (seconds: number): string => {
    if (seconds < 60) {
      return `${Math.round(seconds)} 秒`;
    } else if (seconds < 3600) {
      return `${Math.round(seconds / 60)} 分钟`;
    } else {
      return `${Math.round(seconds / 3600)} 小时`;
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <div className="p-2 rounded-lg bg-amber-100 text-amber-600 mr-3">
            <Zap className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">YOLO 模式</h1>
            <p className="text-gray-600">Auto Mode - 自动处理中</p>
          </div>
        </div>

        {/* Status Badge */}
        <div
          className={clsx(
            'px-3 py-1 rounded-full text-sm font-medium',
            status === 'running' && 'bg-green-100 text-green-700',
            status === 'paused' && 'bg-amber-100 text-amber-700',
            status === 'completed' && 'bg-blue-100 text-blue-700',
            status === 'error' && 'bg-red-100 text-red-700'
          )}
        >
          {status === 'running' && '运行中'}
          {status === 'paused' && '已暂停'}
          {status === 'completed' && '已完成'}
          {status === 'error' && '错误'}
        </div>
      </div>

      {/* Progress Section */}
      <div className="card p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <span className="font-medium text-gray-800">处理进度</span>
          <span className="text-sm text-gray-500">
            {progress.processed} / {progress.total} 句
          </span>
        </div>

        <ProgressBar
          value={progress.percent}
          color={status === 'completed' ? 'success' : 'primary'}
          size="lg"
          showLabel
        />

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-primary-600">{progress.processed}</p>
            <p className="text-sm text-gray-500">已处理</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-600">{progress.skipped}</p>
            <p className="text-sm text-gray-500">已跳过</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-amber-600">{progress.flagged}</p>
            <p className="text-sm text-gray-500">需审核</p>
          </div>
        </div>

        {/* Estimated Time */}
        {status === 'running' && estimatedRemaining !== null && (
          <p className="text-sm text-gray-500 text-center mt-4">
            预计剩余时间: {formatTimeRemaining(estimatedRemaining)}
          </p>
        )}
      </div>

      {/* Control Buttons */}
      <div className="flex justify-center space-x-4 mb-6">
        {status !== 'completed' && (
          <>
            <Button
              variant="outline"
              onClick={handlePauseResume}
              disabled={status === 'error'}
            >
              {status === 'running' ? (
                <>
                  <Pause className="w-4 h-4 mr-2" />
                  暂停
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  继续
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={handleStop}
            >
              <StopCircle className="w-4 h-4 mr-2" />
              切换为干预模式
            </Button>
          </>
        )}

        {status === 'completed' && (
          <Button variant="primary" onClick={handleComplete}>
            查看结果
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center p-4 mb-6 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Processing Logs */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          处理日志 / Processing Logs
        </h2>

        <div className="h-64 overflow-y-auto bg-gray-50 rounded-lg p-4 font-mono text-sm">
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
                    log.action === 'modified' && 'bg-green-50',
                    log.action === 'skipped' && 'bg-gray-100',
                    log.action === 'error' && 'bg-red-50'
                  )}
                >
                  <span className="text-gray-400 mr-2">
                    [{log.timestamp.toLocaleTimeString()}]
                  </span>
                  <span
                    className={clsx(
                      'font-medium mr-2',
                      log.action === 'modified' && 'text-green-600',
                      log.action === 'skipped' && 'text-gray-500',
                      log.action === 'error' && 'text-red-600'
                    )}
                  >
                    #{log.index}
                  </span>
                  <span className="text-gray-700">{log.message}</span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Completion Message */}
      {status === 'completed' && (
        <div className="card p-6 mt-6 bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
          <div className="flex items-center">
            <CheckCircle className="w-8 h-8 text-green-500 mr-4" />
            <div>
              <h3 className="text-lg font-semibold text-gray-800">
                自动处理完成！
              </h3>
              <p className="text-gray-600">
                已处理 {progress.processed} 句，{progress.flagged} 句需要人工审核
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
