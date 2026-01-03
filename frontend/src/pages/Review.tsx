import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Download,
  FileText,
  BarChart2,
  CheckCircle,
  AlertTriangle,
  ArrowLeft,
  Loader2,
  Copy,
  Check,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import LoadingMessage from '../components/common/LoadingMessage';
import { exportApi, sessionApi } from '../services/api';

interface ReviewStats {
  totalSentences: number;
  modified: number;
  skipped: number;
  flagged: number;
  avgRiskReduction: number;
  sourceDistribution: { llm: number; rule: number; custom: number };
}

interface ModificationRecord {
  index: number;
  original: string;
  modified: string;
  source: 'llm' | 'rule' | 'custom';
  riskBefore: number;
  riskAfter: number;
}

/**
 * Review page - View results and export documents
 * 审核页面 - 查看结果并导出文档
 */
export default function Review() {
  const { sessionId } = useParams<{ sessionId: string }>();

  // State
  // 状态
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [modifications, setModifications] = useState<ModificationRecord[]>([]);
  const [activeTab, setActiveTab] = useState<'summary' | 'details' | 'export'>('summary');
  const [isExporting, setIsExporting] = useState(false);
  const [copied, setCopied] = useState(false);

  // Load session data
  // 加载会话数据
  useEffect(() => {
    if (!sessionId) return;

    const loadData = async () => {
      setIsLoading(true);
      try {
        // Get session progress and review stats
        // 获取会话进度和审核统计数据
        const [progress, reviewStats] = await Promise.all([
          sessionApi.getProgress(sessionId),
          sessionApi.getReviewStats(sessionId)
        ]);

        // Use real data from backend
        // 使用后端返回的真实数据
        setStats({
          totalSentences: reviewStats.totalSentences,
          modified: reviewStats.modifiedCount,
          skipped: progress.skipped,
          flagged: progress.flagged,
          avgRiskReduction: reviewStats.avgRiskReduction,
          sourceDistribution: reviewStats.sourceDistribution,
        });

        // Note: Modification details would need another API call
        // 注意：修改详情需要另一个API调用
        setModifications([]);
      } catch (error) {
        console.error('Failed to load review data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [sessionId]);

  // Handle export
  // 处理导出
  const handleExport = async (type: 'document' | 'report', format: string) => {
    if (!sessionId) return;

    setIsExporting(true);
    try {
      let result;
      if (type === 'document') {
        result = await exportApi.exportDocument(sessionId, format);
      } else {
        result = await exportApi.exportReport(sessionId, format);
      }

      // Trigger download
      // 触发下载
      const downloadUrl = exportApi.download(result.filename);
      window.open(downloadUrl, '_blank');
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  // Handle copy to clipboard
  // 处理复制到剪贴板
  const handleCopy = async () => {
    const text = modifications.map((m) => m.modified).join('\n\n');
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Loading state
  // 加载状态
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <LoadingMessage category="general" size="lg" showEnglish={true} />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">处理结果</h1>
          <p className="text-gray-600">Review & Export - 查看并导出</p>
        </div>
        <Link to="/upload">
          <Button variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" />
            处理新文档
          </Button>
        </Link>
      </div>

      {/* Success Banner */}
      {/* 成功提示 */}
      <div className={clsx(
        "card p-6 mb-6 bg-gradient-to-r border",
        stats && stats.modified > 0
          ? "from-green-50 to-blue-50 border-green-200"
          : "from-gray-50 to-blue-50 border-gray-200"
      )}>
        <div className="flex items-center">
          <CheckCircle className={clsx(
            "w-10 h-10 mr-4",
            stats && stats.modified > 0 ? "text-green-500" : "text-gray-400"
          )} />
          <div>
            <h2 className="text-xl font-semibold text-gray-800">
              {stats && stats.modified > 0 ? '处理完成！' : '会话已结束'}
            </h2>
            <p className="text-gray-600">
              {stats && stats.modified > 0
                ? `已修改 ${stats.modified} 个句子，平均降低风险 ${stats.avgRiskReduction} 分`
                : '未进行任何修改'}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 mb-6">
        {[
          { id: 'summary', label: '概览', icon: BarChart2 },
          { id: 'details', label: '详情', icon: FileText },
          { id: 'export', label: '导出', icon: Download },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={clsx(
              'flex items-center px-4 py-2 rounded-lg font-medium transition-colors',
              activeTab === tab.id
                ? 'bg-primary-100 text-primary-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <tab.icon className="w-4 h-4 mr-2" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'summary' && stats && (
        <div className="space-y-6">
          {/* Risk Reduction Summary */}
          {/* 风险降低摘要 */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              风险降低效果 / Risk Reduction Effect
            </h3>
            <div className="text-center">
              <p className="text-sm text-gray-500 mb-2">已修改句子平均降低风险分数</p>
              <div className="text-5xl font-bold text-green-500">
                {stats.avgRiskReduction > 0 ? '-' : ''}{stats.avgRiskReduction}
              </div>
              <p className="text-sm text-gray-400 mt-2">
                Average risk score reduction per modified sentence
              </p>
            </div>
          </div>

          {/* Processing Stats */}
          {/* 处理统计 */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              处理统计 / Processing Statistics
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="总句子数" value={stats.totalSentences} color="blue" />
              <StatCard label="已修改" value={stats.modified} color="green" />
              <StatCard label="已跳过" value={stats.skipped} color="gray" />
              <StatCard label="待审核" value={stats.flagged} color="amber" />
            </div>
          </div>

          {/* Source Distribution */}
          {/* 修改来源分布 */}
          {stats.modified > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                修改来源分布 / Modification Sources
              </h3>
              <div className="space-y-3">
                <SourceBar label="LLM智能改写" percent={stats.sourceDistribution.llm} color="purple" />
                <SourceBar label="规则建议" percent={stats.sourceDistribution.rule} color="blue" />
                <SourceBar label="自定义修改" percent={stats.sourceDistribution.custom} color="gray" />
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'details' && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">
              修改记录 / Modification Records
            </h3>
            <Button variant="outline" size="sm" onClick={handleCopy}>
              {copied ? (
                <>
                  <Check className="w-4 h-4 mr-1" />
                  已复制
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 mr-1" />
                  复制全部
                </>
              )}
            </Button>
          </div>

          {modifications.length === 0 ? (
            <p className="text-center text-gray-500 py-8">暂无修改记录</p>
          ) : (
            <div className="space-y-4">
              {modifications.map((mod) => (
                <div key={mod.index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-600">
                      #{mod.index}
                    </span>
                    <div className="flex items-center space-x-2">
                      <span
                        className={clsx(
                          'px-2 py-0.5 text-xs rounded-full',
                          mod.source === 'llm' && 'bg-purple-100 text-purple-700',
                          mod.source === 'rule' && 'bg-blue-100 text-blue-700',
                          mod.source === 'custom' && 'bg-gray-100 text-gray-700'
                        )}
                      >
                        {mod.source === 'llm' ? 'LLM' : mod.source === 'rule' ? '规则' : '自定义'}
                      </span>
                      <span className="text-xs text-gray-500">
                        风险: {Math.round(mod.riskBefore)} → {Math.round(mod.riskAfter)}
                      </span>
                    </div>
                  </div>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="p-3 bg-red-50 rounded-lg">
                      <p className="text-xs text-red-500 mb-1">原文</p>
                      <p className="text-sm text-gray-700">{mod.original}</p>
                    </div>
                    <div className="p-3 bg-green-50 rounded-lg">
                      <p className="text-xs text-green-500 mb-1">修改后</p>
                      <p className="text-sm text-gray-700">{mod.modified}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'export' && (
        <div className="grid md:grid-cols-2 gap-6">
          {/* Export Document */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              导出文档 / Export Document
            </h3>
            <p className="text-gray-600 mb-4">
              导出优化后的文档，可选择不同格式
            </p>
            <div className="space-y-3">
              <ExportButton
                label="TXT 纯文本"
                description="简单文本格式"
                onClick={() => handleExport('document', 'txt')}
                isLoading={isExporting}
              />
              <ExportButton
                label="DOCX 文档"
                description="Microsoft Word 格式"
                onClick={() => handleExport('document', 'docx')}
                isLoading={isExporting}
              />
            </div>
          </div>

          {/* Export Report */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              导出报告 / Export Report
            </h3>
            <p className="text-gray-600 mb-4">
              导出详细的处理报告，包含修改记录和统计信息
            </p>
            <div className="space-y-3">
              <ExportButton
                label="JSON 数据"
                description="结构化数据格式"
                onClick={() => handleExport('report', 'json')}
                isLoading={isExporting}
              />
              <ExportButton
                label="PDF 报告"
                description="可打印的报告格式"
                onClick={() => handleExport('report', 'pdf')}
                isLoading={isExporting}
              />
            </div>
          </div>
        </div>
      )}

      {/* Flagged Items Warning */}
      {stats && stats.flagged > 0 && (
        <div className="card p-4 mt-6 bg-amber-50 border-amber-200">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-amber-500 mr-3" />
            <div>
              <p className="font-medium text-amber-800">
                有 {stats.flagged} 个句子需要人工审核
              </p>
              <p className="text-sm text-amber-600">
                这些句子可能需要更仔细的检查，建议在干预模式中单独处理
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Stat card sub-component
// 统计卡片子组件
function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: 'blue' | 'green' | 'gray' | 'amber';
}) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    gray: 'bg-gray-50 text-gray-600',
    amber: 'bg-amber-50 text-amber-600',
  };

  return (
    <div className={clsx('p-4 rounded-lg text-center', colors[color])}>
      <p className="text-3xl font-bold">{value}</p>
      <p className="text-sm opacity-80">{label}</p>
    </div>
  );
}

// Source bar sub-component
// 来源条子组件
function SourceBar({
  label,
  percent,
  color,
}: {
  label: string;
  percent: number;
  color: 'purple' | 'blue' | 'gray';
}) {
  const colors = {
    purple: 'bg-purple-500',
    blue: 'bg-blue-500',
    gray: 'bg-gray-400',
  };

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="text-gray-500">{percent}%</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all', colors[color])}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

// Export button sub-component
// 导出按钮子组件
function ExportButton({
  label,
  description,
  onClick,
  isLoading,
}: {
  label: string;
  description: string;
  onClick: () => void;
  isLoading: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      className="w-full p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors text-left disabled:opacity-50"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium text-gray-800">{label}</p>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
        {isLoading ? (
          <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
        ) : (
          <Download className="w-5 h-5 text-gray-400" />
        )}
      </div>
    </button>
  );
}
