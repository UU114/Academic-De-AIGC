/**
 * Admin Dashboard Page - Statistics and overview
 * 管理员仪表板页面 - 统计和概览
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, Legend
} from 'recharts';
import {
  DollarSign, Users, FileText, TrendingUp,
  Activity, LogOut, RefreshCw, AlertCircle, AlertTriangle
} from 'lucide-react';
import Button from '../../components/common/Button';
import { useAdminStore } from '../../stores/adminStore';
import { adminApi } from '../../services/api';

// Chart colors
// 图表颜色
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

// Types
// 类型定义
interface OverviewStats {
  totalRevenue: number;
  todayRevenue: number;
  thisWeekRevenue: number;
  thisMonthRevenue: number;
  totalTasks: number;
  paidTasks: number;
  pendingTasks: number;
  completedTasks: number;
  failedTasks: number;
  totalUsers: number;
  activeUsersToday: number;
  activeUsersWeek: number;
  newUsersToday: number;
  totalWordsProcessed: number;
  totalDocuments: number;
}

interface RevenueData {
  date: string;
  revenue: number;
  taskCount: number;
}

interface TaskStats {
  statusDistribution: Array<{ status: string; count: number; percentage: number }>;
  paymentDistribution: Array<{ status: string; count: number; percentage: number }>;
  tasksByDate: Array<{ date: string; count: number }>;
}

// Stat Card Component
// 统计卡片组件
function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color = 'text-primary-600',
  bgColor = 'bg-primary-100',
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  trend?: string;
  color?: string;
  bgColor?: string;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
          {subtitle && (
            <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
          )}
          {trend && (
            <p className="mt-1 text-sm text-green-600 flex items-center">
              <TrendingUp className="w-4 h-4 mr-1" />
              {trend}
            </p>
          )}
        </div>
        <div className={`${bgColor} p-3 rounded-lg`}>
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const navigate = useNavigate();
  const { isAdminLoggedIn, adminLogout } = useAdminStore();

  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [revenueData, setRevenueData] = useState<RevenueData[]>([]);
  const [taskStats, setTaskStats] = useState<TaskStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [chartsReady, setChartsReady] = useState(false);

  // Check authentication
  // 检查认证
  useEffect(() => {
    if (!isAdminLoggedIn) {
      navigate('/admin/login');
    }
  }, [isAdminLoggedIn, navigate]);

  // Load data
  // 加载数据
  const loadData = async () => {
    try {
      setError(null);
      const [overviewRes, revenueRes, tasksRes] = await Promise.all([
        adminApi.getOverview(),
        adminApi.getRevenue({ period: 'daily', days: 30 }),
        adminApi.getTasks({ days: 30 }),
      ]);

      setOverview(overviewRes);
      setRevenueData(revenueRes.data);
      setTaskStats(tasksRes);
    } catch (err) {
      const message = err instanceof Error ? err.message : '加载数据失败';
      setError(message);
      // If unauthorized, redirect to login
      // 如果未授权，重定向到登录
      if (message.includes('401') || message.includes('认证')) {
        adminLogout();
        navigate('/admin/login');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (isAdminLoggedIn) {
      loadData();
    }
  }, [isAdminLoggedIn]);

  // Delay chart rendering to ensure containers have dimensions
  // 延迟图表渲染以确保容器有尺寸
  useEffect(() => {
    if (!loading) {
      // Use requestAnimationFrame + timeout for more reliable timing
      // 使用 requestAnimationFrame + timeout 以获得更可靠的时序
      const frame = requestAnimationFrame(() => {
        const timer = setTimeout(() => setChartsReady(true), 50);
        return () => clearTimeout(timer);
      });
      return () => cancelAnimationFrame(frame);
    }
  }, [loading]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const handleLogout = () => {
    adminLogout();
    navigate('/admin/login');
  };

  if (!isAdminLoggedIn) {
    return null;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-12 h-12 text-primary-600 animate-pulse mx-auto" />
          <p className="mt-4 text-gray-600">加载中... | Loading...</p>
        </div>
      </div>
    );
  }

  // Prepare chart data
  // 准备图表数据
  const paymentPieData = taskStats?.paymentDistribution.map(item => ({
    name: item.status === 'paid' ? '已付款' : item.status === 'unpaid' ? '未付款' : item.status,
    value: item.count,
  })) || [];

  const statusPieData = taskStats?.statusDistribution.map(item => ({
    name: getStatusLabel(item.status),
    value: item.count,
  })) || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                管理员仪表板
              </h1>
              <p className="text-sm text-gray-500">Admin Dashboard</p>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/admin/anomaly')}
              >
                <AlertTriangle className="w-4 h-4 mr-2" />
                异常检测
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                刷新
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
              >
                <LogOut className="w-4 h-4 mr-2" />
                退出
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Alert */}
        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Stat Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="总营收 | Total Revenue"
            value={`¥${(overview?.totalRevenue || 0).toFixed(2)}`}
            subtitle={`今日: ¥${(overview?.todayRevenue || 0).toFixed(2)}`}
            icon={DollarSign}
            color="text-green-600"
            bgColor="bg-green-100"
          />
          <StatCard
            title="已付款任务 | Paid Tasks"
            value={overview?.paidTasks || 0}
            subtitle={`总任务: ${overview?.totalTasks || 0}`}
            icon={FileText}
            color="text-blue-600"
            bgColor="bg-blue-100"
          />
          <StatCard
            title="用户数 | Users"
            value={overview?.totalUsers || 0}
            subtitle={`今日活跃: ${overview?.activeUsersToday || 0}`}
            icon={Users}
            color="text-purple-600"
            bgColor="bg-purple-100"
          />
          <StatCard
            title="处理字数 | Words"
            value={formatNumber(overview?.totalWordsProcessed || 0)}
            subtitle={`文档数: ${overview?.totalDocuments || 0}`}
            icon={Activity}
            color="text-amber-600"
            bgColor="bg-amber-100"
          />
        </div>

        {/* Revenue Chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            营收趋势 | Revenue Trend (30天)
          </h2>
          <div className="h-80">
            {chartsReady && (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => value.slice(5)}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(value: number) => [`¥${value.toFixed(2)}`, '营收']}
                    labelFormatter={(label) => `日期: ${label}`}
                  />
                  <Line
                    type="monotone"
                    dataKey="revenue"
                    stroke="#0088FE"
                    strokeWidth={2}
                    dot={{ fill: '#0088FE', strokeWidth: 2 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Payment Status Pie */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              支付状态分布 | Payment Status
            </h2>
            <div className="h-64">
              {chartsReady && (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={paymentPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {paymentPieData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Task Status Pie */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              任务状态分布 | Task Status
            </h2>
            <div className="h-64">
              {chartsReady && (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {statusPieData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>

        {/* Tasks by Date Bar Chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            每日任务数 | Daily Tasks
          </h2>
          <div className="h-64">
            {chartsReady && (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={taskStats?.tasksByDate || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => value.slice(5)}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(value: number) => [value, '任务数']}
                    labelFormatter={(label) => `日期: ${label}`}
                  />
                  <Bar dataKey="count" fill="#82CA9D" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Additional Stats */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">本周营收</h3>
            <p className="text-2xl font-bold text-green-600">
              ¥{(overview?.thisWeekRevenue || 0).toFixed(2)}
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">本月营收</h3>
            <p className="text-2xl font-bold text-green-600">
              ¥{(overview?.thisMonthRevenue || 0).toFixed(2)}
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">今日新用户</h3>
            <p className="text-2xl font-bold text-purple-600">
              {overview?.newUsersToday || 0}
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

// Helper functions
// 辅助函数

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    created: '已创建',
    quoted: '已报价',
    paying: '支付中',
    paid: '已付款',
    processing: '处理中',
    completed: '已完成',
    expired: '已过期',
    failed: '失败',
  };
  return labels[status] || status;
}
