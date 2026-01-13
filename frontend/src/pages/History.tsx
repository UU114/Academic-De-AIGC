import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Clock, Play, CheckCircle, Pause, Trash2, AlertCircle, RefreshCw } from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import RiskBadge from '../components/common/RiskBadge';
import LoadingMessage from '../components/common/LoadingMessage';
import { sessionApi, documentApi } from '../services/api';
import type { SessionInfo, DocumentInfo, SessionStep } from '../types';

/**
 * Task item combining session and document info
 * 任务项：合并会话和文档信息
 */
interface TaskItem {
  sessionId: string;
  documentId: string;
  documentName: string;
  mode: 'intervention' | 'yolo';
  status: 'active' | 'paused' | 'completed' | 'pending';
  currentStep: SessionStep;
  totalSentences: number;
  processed: number;
  progressPercent: number;
  colloquialismLevel: number;  // Colloquialism level (0-10) / 口语化程度
  highRiskCount: number;
  mediumRiskCount: number;
  lowRiskCount: number;
  createdAt: string;
  completedAt?: string;
}

/**
 * History page - Unified task list view
 * 历史页面 - 统一任务列表视图
 */
export default function History() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load data on mount
  // 组件挂载时加载数据
  useEffect(() => {
    loadData();
  }, []);

  // Merge sessions and documents into unified task list
  // 合并会话和文档为统一任务列表
  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [sessionsData, documentsData] = await Promise.all([
        sessionApi.list(),
        documentApi.list(),
      ]);

      // Create a map of document info by id
      // 创建文档信息映射
      const docMap = new Map<string, DocumentInfo>();
      documentsData.forEach((doc: DocumentInfo) => {
        docMap.set(doc.id, doc);
      });

      // Merge session with document risk info
      // 合并会话与文档风险信息
      const taskList: TaskItem[] = sessionsData.map((session: SessionInfo) => {
        const doc = docMap.get(session.documentId);
        return {
          sessionId: session.sessionId,
          documentId: session.documentId,
          documentName: session.documentName,
          mode: session.mode,
          status: session.status as TaskItem['status'],
          currentStep: session.currentStep || 'step1-1',
          totalSentences: session.totalSentences,
          processed: session.processed,
          progressPercent: session.progressPercent,
          colloquialismLevel: session.colloquialismLevel ?? 4,
          highRiskCount: doc?.highRiskCount || 0,
          mediumRiskCount: doc?.mediumRiskCount || 0,
          lowRiskCount: doc?.lowRiskCount || 0,
          createdAt: session.createdAt,
          completedAt: session.completedAt,
        };
      });

      // Sort by creation date (newest first)
      // 按创建时间排序（最新在前）
      taskList.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

      setTasks(taskList);
    } catch (err) {
      setError((err as Error).message || '加载失败');
    } finally {
      setIsLoading(false);
    }
  };

  // Resume a task - navigate to the correct step
  // 恢复任务 - 导航到正确的步骤
  const handleResumeTask = (task: TaskItem) => {
    // Base URL params for all routes
    // 所有路由的基础URL参数
    const params = `?mode=${task.mode}&session=${task.sessionId}`;
    const docBase = `/flow`;

    // Navigate based on current step (5-layer architecture with granular sub-steps)
    // 根据当前步骤导航（5层架构含细粒度子步骤）
    const stepRoutes: Record<string, string> = {
      // Step 1.0: Term Locking
      // 步骤 1.0：词汇锁定
      'term-lock': `${docBase}/term-lock/${task.documentId}${params}`,

      // Layer 5 (Document Level): Step 1.1 - 1.5
      // Layer 5（全文层）：步骤 1.1 - 1.5
      'layer5-step1-1': `${docBase}/layer5-step1-1/${task.documentId}${params}`,
      'layer5-step1-2': `${docBase}/layer5-step1-2/${task.documentId}${params}`,
      'layer5-step1-3': `${docBase}/layer5-step1-3/${task.documentId}${params}`,
      'layer5-step1-4': `${docBase}/layer5-step1-4/${task.documentId}${params}`,
      'layer5-step1-5': `${docBase}/layer5-step1-5/${task.documentId}${params}`,

      // Layer 4 (Section Level): Step 2.0 - 2.5
      // Layer 4（章节层）：步骤 2.0 - 2.5
      'layer4-step2-0': `${docBase}/layer4-step2-0/${task.documentId}${params}`,
      'layer4-step2-1': `${docBase}/layer4-step2-1/${task.documentId}${params}`,
      'layer4-step2-2': `${docBase}/layer4-step2-2/${task.documentId}${params}`,
      'layer4-step2-3': `${docBase}/layer4-step2-3/${task.documentId}${params}`,
      'layer4-step2-4': `${docBase}/layer4-step2-4/${task.documentId}${params}`,
      'layer4-step2-5': `${docBase}/layer4-step2-5/${task.documentId}${params}`,

      // Layer 3 (Paragraph Level): Step 3.0 - 3.5
      // Layer 3（段落层）：步骤 3.0 - 3.5
      'layer3-step3-0': `${docBase}/layer3-step3-0/${task.documentId}${params}`,
      'layer3-step3-1': `${docBase}/layer3-step3-1/${task.documentId}${params}`,
      'layer3-step3-2': `${docBase}/layer3-step3-2/${task.documentId}${params}`,
      'layer3-step3-3': `${docBase}/layer3-step3-3/${task.documentId}${params}`,
      'layer3-step3-4': `${docBase}/layer3-step3-4/${task.documentId}${params}`,
      'layer3-step3-5': `${docBase}/layer3-step3-5/${task.documentId}${params}`,

      // Layer 2 (Sentence Level): Step 4.0 - 4.1, Console
      // Layer 2（句子层）：步骤 4.0 - 4.1, Console
      'layer2-step4-0': `${docBase}/layer2-step4-0/${task.documentId}${params}`,
      'layer2-step4-1': `${docBase}/layer2-step4-1/${task.documentId}${params}`,
      'layer2-step4-console': `${docBase}/layer2-step4-console/${task.documentId}${params}`,

      // Layer 1 (Lexical Level): Step 5.0 - 5.5
      // Layer 1（词汇层）：步骤 5.0 - 5.5
      'layer1-step5-0': `${docBase}/layer1-step5-0/${task.documentId}${params}`,
      'layer1-step5-1': `${docBase}/layer1-step5-1/${task.documentId}${params}`,
      'layer1-step5-2': `${docBase}/layer1-step5-2/${task.documentId}${params}`,
      'layer1-step5-3': `${docBase}/layer1-step5-3/${task.documentId}${params}`,
      'layer1-step5-4': `${docBase}/layer1-step5-4/${task.documentId}${params}`,
      'layer1-step5-5': `${docBase}/layer1-step5-5/${task.documentId}${params}`,
      'layer-lexical-v2': `${docBase}/layer1-lexical-v2/${task.documentId}${params}`,

      // Legacy combined layer routes (for backward compatibility)
      // 旧版组合层级路由（向后兼容）
      'layer-document': `${docBase}/layer-document/${task.documentId}${params}`,
      'layer-section': `${docBase}/layer-section/${task.documentId}${params}`,
      'layer-paragraph': `${docBase}/layer-paragraph/${task.documentId}${params}`,
      'layer-sentence': `${docBase}/layer-sentence/${task.documentId}${params}`,
      'layer-lexical': `${docBase}/layer-lexical/${task.documentId}${params}`,

      // Legacy 4-step routes (for backward compatibility)
      // 旧版4步流程路由（向后兼容）
      'step1-1': `${docBase}/layer5-step1-1/${task.documentId}${params}`,
      'step1-2': `${docBase}/layer4-step2-0/${task.documentId}${params}`,
      'step2': `${docBase}/layer3-step3-0/${task.documentId}${params}`,
      'level2': `${docBase}/layer3-step3-0/${task.documentId}${params}`,
      'step3': task.mode === 'intervention'
        ? `/intervention/${task.sessionId}`
        : `/yolo/${task.sessionId}`,
      'level3': task.mode === 'intervention'
        ? `/intervention/${task.sessionId}`
        : `/yolo/${task.sessionId}`,
      'review': `/review/${task.sessionId}`,
    };

    // Default to term-lock (first step) if currentStep is not found
    // 如果 currentStep 未找到，默认跳转到 term-lock（第一步）
    const route = stepRoutes[task.currentStep] || `${docBase}/term-lock/${task.documentId}${params}`;
    navigate(route);
  };

  // Delete a task (document and all sessions)
  // 删除任务（文档及所有会话）
  const handleDeleteTask = async (task: TaskItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('确定要删除此任务及其所有数据吗？\nAre you sure to delete this task and all its data?')) return;

    try {
      await documentApi.delete(task.documentId);
      loadData();
    } catch (err) {
      setError((err as Error).message || '删除失败');
    }
  };

  // Get status icon and label
  // 获取状态图标和标签
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'completed':
        return { icon: <CheckCircle className="w-4 h-4 text-green-500" />, label: '已完成', color: 'text-green-600' };
      case 'active':
        return { icon: <Play className="w-4 h-4 text-blue-500" />, label: '进行中', color: 'text-blue-600' };
      case 'paused':
        return { icon: <Pause className="w-4 h-4 text-amber-500" />, label: '已暂停', color: 'text-amber-600' };
      default:
        return { icon: <Clock className="w-4 h-4 text-gray-400" />, label: '待处理', color: 'text-gray-500' };
    }
  };

  // Get step label
  // 获取步骤标签
  const getStepLabel = (step: string) => {
    const stepLabels: Record<string, string> = {
      // Step 1.0: Term Locking
      'term-lock': '1.0 词汇锁定',

      // Layer 5 (Document Level): Step 1.1 - 1.5
      'layer5-step1-1': '1.1 结构框架',
      'layer5-step1-2': '1.2 段落长度',
      'layer5-step1-3': '1.3 推进闭合',
      'layer5-step1-4': '1.4 连接词衔接',
      'layer5-step1-5': '1.5 内容实质',

      // Layer 4 (Section Level): Step 2.0 - 2.5
      'layer4-step2-0': '2.0 章节概览',
      'layer4-step2-1': '2.1 章节结构',
      'layer4-step2-2': '2.2 段落长度',
      'layer4-step2-3': '2.3 推进闭合',
      'layer4-step2-4': '2.4 连接词衔接',
      'layer4-step2-5': '2.5 内容实质',

      // Layer 3 (Paragraph Level): Step 3.0 - 3.5
      'layer3-step3-0': '3.0 段落概览',
      'layer3-step3-1': '3.1 段落结构',
      'layer3-step3-2': '3.2 句子长度',
      'layer3-step3-3': '3.3 推进闭合',
      'layer3-step3-4': '3.4 连接词衔接',
      'layer3-step3-5': '3.5 内容实质',

      // Layer 2 (Sentence Level): Step 4.0 - 4.1, Console
      'layer2-step4-0': '4.0 句子概览',
      'layer2-step4-1': '4.1 句子结构',
      'layer2-step4-console': '4.x 句子控制台',

      // Layer 1 (Lexical Level): Step 5.0 - 5.5
      'layer1-step5-0': '5.0 词汇概览',
      'layer1-step5-1': '5.1 词汇结构',
      'layer1-step5-2': '5.2 词汇密度',
      'layer1-step5-3': '5.3 词汇多样性',
      'layer1-step5-4': '5.4 词汇正式度',
      'layer1-step5-5': '5.5 词汇一致性',
      'layer-lexical-v2': '5.x 增强词汇分析',

      // Legacy combined layer routes
      'layer-document': 'L5 全文层',
      'layer-section': 'L4 章节层',
      'layer-paragraph': 'L3 段落层',
      'layer-sentence': 'L2 句子层',
      'layer-lexical': 'L1 词汇层',

      // Legacy 4-step routes
      'step1-1': '1.1 结构分析',
      'step1-2': '1.2 段落分析',
      'step2': 'Step2 衔接优化',
      'level2': 'Step2 衔接优化',
      'step3': 'Step3 句子处理',
      'level3': 'Step3 句子处理',
      'review': '审核完成',
    };
    return stepLabels[step] || step;
  };

  // Format date
  // 格式化日期
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingMessage category="general" size="md" showEnglish={true} />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">任务列表</h1>
          <p className="text-gray-600">Task List - View and manage all your tasks</p>
        </div>
        <div className="flex space-x-3">
          <Button variant="secondary" onClick={loadData} title="刷新列表">
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Button variant="primary" onClick={() => navigate('/upload')}>
            新建任务
          </Button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="flex items-center p-4 mb-6 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Task count */}
      <div className="mb-4 text-sm text-gray-500">
        共 {tasks.length} 个任务 | Total {tasks.length} task{tasks.length !== 1 ? 's' : ''}
      </div>

      {/* Task List */}
      <div className="space-y-4">
        {tasks.length === 0 ? (
          <div className="text-center py-16 text-gray-500">
            <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p className="text-lg mb-2">暂无任务</p>
            <p className="text-sm mb-6">No tasks yet</p>
            <Button variant="primary" onClick={() => navigate('/upload')}>
              上传文档开始第一个任务
            </Button>
          </div>
        ) : (
          tasks.map((task) => {
            const statusInfo = getStatusInfo(task.status);
            return (
              <div
                key={task.sessionId}
                className={clsx(
                  'card p-5 hover:shadow-md transition-all cursor-pointer border-l-4',
                  task.status === 'completed' ? 'border-l-green-500' :
                  task.status === 'active' ? 'border-l-blue-500' :
                  task.status === 'paused' ? 'border-l-amber-500' : 'border-l-gray-300'
                )}
                onClick={() => handleResumeTask(task)}
              >
                {/* Top row: document name, status, mode */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-6 h-6 text-gray-400 flex-shrink-0" />
                    <div>
                      <h3 className="font-semibold text-gray-800 text-lg">
                        {task.documentName}
                      </h3>
                      <div className="flex items-center flex-wrap gap-x-3 gap-y-1 text-sm text-gray-500 mt-1">
                        <span className={clsx('flex items-center', statusInfo.color)}>
                          {statusInfo.icon}
                          <span className="ml-1 font-medium">{statusInfo.label}</span>
                        </span>
                        <span>•</span>
                        <span className="px-2 py-0.5 bg-gray-100 rounded text-xs font-medium">
                          {getStepLabel(task.currentStep)}
                        </span>
                        <span>•</span>
                        <span className={task.mode === 'yolo' ? 'text-amber-600' : 'text-primary-600'}>
                          {task.mode === 'intervention' ? '干预模式' : 'YOLO模式'}
                        </span>
                        <span>•</span>
                        <span className="text-purple-600" title="表达风格：0=最学术，10=最通俗 / Style: 0=Academic, 10=Casual">
                          风格: {task.colloquialismLevel} (学术↔通俗)
                        </span>
                        <span>•</span>
                        <span>{formatDate(task.createdAt)}</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDeleteTask(task, e)}
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors rounded-lg hover:bg-red-50"
                    title="删除任务"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>

                {/* Middle row: risk badges */}
                <div className="flex items-center space-x-2 mb-3">
                  {task.highRiskCount > 0 && (
                    <RiskBadge level="high" score={task.highRiskCount} size="sm" />
                  )}
                  {task.mediumRiskCount > 0 && (
                    <RiskBadge level="medium" score={task.mediumRiskCount} size="sm" />
                  )}
                  {task.lowRiskCount > 0 && (
                    <RiskBadge level="low" score={task.lowRiskCount} size="sm" />
                  )}
                  {task.highRiskCount === 0 && task.mediumRiskCount === 0 && task.lowRiskCount === 0 && (
                    <span className="text-sm text-gray-400">风险信息待分析</span>
                  )}
                </div>

                {/* Bottom row: action button */}
                <div className="flex items-center justify-end">
                  <Button
                    variant={task.status === 'completed' ? 'secondary' : 'primary'}
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleResumeTask(task);
                    }}
                  >
                    {task.status === 'completed' ? '查看结果' : '继续处理'}
                  </Button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
