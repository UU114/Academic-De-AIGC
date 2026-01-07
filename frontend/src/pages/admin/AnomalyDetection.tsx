/**
 * Anomaly Detection Page - Monitor order call count anomalies
 * 异常检测页面 - 监控订单调用次数异常
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, ReferenceLine, Legend
} from 'recharts';
import {
  AlertTriangle, Activity, Filter, RefreshCw, ArrowLeft,
  TrendingUp, Package, AlertCircle
} from 'lucide-react';
import Button from '../../components/common/Button';
import { useAdminStore } from '../../stores/adminStore';
import { adminApi } from '../../services/api';

// Types
// 类型定义
interface AnomalyOverview {
  totalTasks: number;
  anomalyCount: number;
  anomalyRate: number;
  sigma: number;
  priceRanges: Array<{
    rangeLabel: string;
    minPrice: number;
    maxPrice: number;
    taskCount: number;
    meanCalls: number;
    stdCalls: number;
    threshold: number;
    anomalyCount: number;
  }>;
}

interface DistributionData {
  scatterData: Array<{
    taskId: string;
    price: number;
    calls: number;
    isAnomaly: boolean;
    wordCount?: number;
  }>;
  histogramData: Array<{
    rangeLabel: string;
    rangeMin: number;
    rangeMax: number;
    count: number;
    isAboveThreshold: boolean;
  }>;
  stats: {
    mean: number;
    std: number;
    threshold: number;
    sigma: number;
    totalCount: number;
  } | null;
}

interface AnomalyOrder {
  taskId: string;
  userId: string | null;
  priceFinal: number;
  apiCallCount: number;
  expectedCalls: number;
  deviation: number;
  wordCount: number | null;
  createdAt: string;
  status: string;
}

// Stat Card Component
// 统计卡片组件
function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'text-primary-600',
  bgColor = 'bg-primary-100',
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
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
        </div>
        <div className={`${bgColor} p-3 rounded-lg`}>
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
      </div>
    </div>
  );
}

export default function AnomalyDetection() {
  const navigate = useNavigate();
  const { isAdminLoggedIn } = useAdminStore();

  // State
  // 状态
  const [overview, setOverview] = useState<AnomalyOverview | null>(null);
  const [distribution, setDistribution] = useState<DistributionData | null>(null);
  const [anomalyOrders, setAnomalyOrders] = useState<AnomalyOrder[]>([]);
  const [ordersTotal, setOrdersTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  // 筛选状态
  const [minPrice, setMinPrice] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');
  const [sigma, setSigma] = useState<number>(2.0);
  const [page, setPage] = useState(1);
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
      setLoading(true);
      setError(null);

      const params = {
        minPrice: minPrice ? parseFloat(minPrice) : undefined,
        maxPrice: maxPrice ? parseFloat(maxPrice) : undefined,
        sigma,
      };

      const [overviewRes, distRes, ordersRes] = await Promise.all([
        adminApi.getAnomalyOverview(sigma),
        adminApi.getAnomalyDistribution(params),
        adminApi.getAnomalyOrders({ ...params, page, pageSize: 20 }),
      ]);

      setOverview(overviewRes);
      setDistribution(distRes);
      setAnomalyOrders(ordersRes.orders);
      setOrdersTotal(ordersRes.total);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load data';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdminLoggedIn) {
      loadData();
    }
  }, [isAdminLoggedIn]);

  // Delay chart rendering
  // 延迟图表渲染
  useEffect(() => {
    if (!loading) {
      const frame = requestAnimationFrame(() => {
        const timer = setTimeout(() => setChartsReady(true), 50);
        return () => clearTimeout(timer);
      });
      return () => cancelAnimationFrame(frame);
    }
  }, [loading]);

  const handleApplyFilter = () => {
    setPage(1);
    setChartsReady(false);
    loadData();
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    adminApi.getAnomalyOrders({
      minPrice: minPrice ? parseFloat(minPrice) : undefined,
      maxPrice: maxPrice ? parseFloat(maxPrice) : undefined,
      sigma,
      page: newPage,
      pageSize: 20,
    }).then(res => {
      setAnomalyOrders(res.orders);
      setOrdersTotal(res.total);
    });
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

  const totalPages = Math.ceil(ordersTotal / 20);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/admin')}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                返回
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  异常检测
                </h1>
                <p className="text-sm text-gray-500">Anomaly Detection</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => { setChartsReady(false); loadData(); }}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              刷新
            </Button>
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard
            title="总订单数 | Total Orders"
            value={overview?.totalTasks || 0}
            subtitle="有价格记录的订单"
            icon={Package}
            color="text-blue-600"
            bgColor="bg-blue-100"
          />
          <StatCard
            title="异常订单 | Anomalies"
            value={overview?.anomalyCount || 0}
            subtitle={`检测阈值: ${sigma}σ`}
            icon={AlertTriangle}
            color="text-red-600"
            bgColor="bg-red-100"
          />
          <StatCard
            title="异常率 | Anomaly Rate"
            value={`${overview?.anomalyRate || 0}%`}
            subtitle="异常占比"
            icon={TrendingUp}
            color="text-amber-600"
            bgColor="bg-amber-100"
          />
        </div>

        {/* Filter Controls */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
          <div className="flex items-center space-x-2 mb-4">
            <Filter className="w-5 h-5 text-gray-500" />
            <h2 className="text-lg font-semibold text-gray-900">筛选条件 | Filters</h2>
          </div>
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                最低金额 | Min Price
              </label>
              <input
                type="number"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
                placeholder="¥50"
                className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                最高金额 | Max Price
              </label>
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                placeholder="¥500"
                className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                标准差倍数 | Sigma
              </label>
              <select
                value={sigma}
                onChange={(e) => setSigma(parseFloat(e.target.value))}
                className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
                <option value={1.5}>1.5σ</option>
                <option value={2.0}>2.0σ</option>
                <option value={2.5}>2.5σ</option>
                <option value={3.0}>3.0σ</option>
              </select>
            </div>
            <Button variant="primary" onClick={handleApplyFilter}>
              应用筛选 | Apply
            </Button>
          </div>
        </div>

        {/* Scatter Chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            订单金额 vs 调用次数 | Price vs API Calls
          </h2>
          <div className="h-80">
            {chartsReady && distribution?.scatterData && distribution.scatterData.length > 0 && (
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    type="number"
                    dataKey="price"
                    name="金额"
                    unit="¥"
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis
                    type="number"
                    dataKey="calls"
                    name="调用次数"
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip
                    formatter={(value: number, name: string) => {
                      if (name === '金额') return [`¥${value}`, name];
                      return [value, name];
                    }}
                    content={({ payload }) => {
                      if (!payload || !payload.length) return null;
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-3 border rounded shadow-lg text-sm">
                          <p><strong>订单ID:</strong> {data.taskId.slice(0, 8)}...</p>
                          <p><strong>金额:</strong> ¥{data.price.toFixed(2)}</p>
                          <p><strong>调用次数:</strong> {data.calls}</p>
                          {data.wordCount && <p><strong>字数:</strong> {data.wordCount}</p>}
                          <p className={data.isAnomaly ? 'text-red-600 font-bold' : 'text-green-600'}>
                            {data.isAnomaly ? '异常' : '正常'}
                          </p>
                        </div>
                      );
                    }}
                  />
                  {distribution.stats && (
                    <ReferenceLine
                      y={distribution.stats.threshold}
                      stroke="#ef4444"
                      strokeDasharray="5 5"
                      label={{ value: `阈值: ${distribution.stats.threshold.toFixed(1)}`, position: 'right', fill: '#ef4444' }}
                    />
                  )}
                  <Legend />
                  <Scatter
                    name="正常订单"
                    data={distribution.scatterData.filter(d => !d.isAnomaly)}
                    fill="#3b82f6"
                  />
                  <Scatter
                    name="异常订单"
                    data={distribution.scatterData.filter(d => d.isAnomaly)}
                    fill="#ef4444"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            )}
            {(!distribution?.scatterData || distribution.scatterData.length === 0) && (
              <div className="h-full flex items-center justify-center text-gray-500">
                暂无数据 | No data available
              </div>
            )}
          </div>
        </div>

        {/* Histogram */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            调用次数分布 | API Calls Distribution
          </h2>
          <div className="h-64">
            {chartsReady && distribution?.histogramData && distribution.histogramData.length > 0 && (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distribution.histogramData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="rangeLabel" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(value: number) => [value, '订单数']}
                    labelFormatter={(label) => `调用次数: ${label}`}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {distribution.histogramData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.isAboveThreshold ? '#ef4444' : '#3b82f6'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
            {(!distribution?.histogramData || distribution.histogramData.length === 0) && (
              <div className="h-full flex items-center justify-center text-gray-500">
                暂无数据 | No data available
              </div>
            )}
          </div>
          {distribution?.stats && (
            <div className="mt-4 flex justify-center space-x-6 text-sm text-gray-600">
              <span>平均值: <strong>{distribution.stats.mean.toFixed(1)}</strong></span>
              <span>标准差: <strong>{distribution.stats.std.toFixed(1)}</strong></span>
              <span>阈值 ({sigma}σ): <strong className="text-red-600">{distribution.stats.threshold.toFixed(1)}</strong></span>
            </div>
          )}
        </div>

        {/* Anomaly Orders Table */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            异常订单详情 | Anomaly Order Details
            <span className="ml-2 text-sm font-normal text-gray-500">
              ({ordersTotal} 条记录)
            </span>
          </h2>

          {anomalyOrders.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        订单ID
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        金额
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        调用次数
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        期望值
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        偏离倍数
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        字数
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        状态
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        创建时间
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {anomalyOrders.map((order) => (
                      <tr key={order.taskId} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-mono text-gray-900">
                          {order.taskId.slice(0, 8)}...
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          ¥{order.priceFinal.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-sm font-bold text-red-600">
                          {order.apiCallCount}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {order.expectedCalls.toFixed(1)}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
                            {order.deviation.toFixed(1)}x
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {order.wordCount || '-'}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            order.status === 'completed' ? 'bg-green-100 text-green-800' :
                            order.status === 'paid' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {order.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {order.createdAt ? new Date(order.createdAt).toLocaleString('zh-CN') : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-4 flex justify-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => handlePageChange(page - 1)}
                  >
                    上一页
                  </Button>
                  <span className="px-4 py-2 text-sm text-gray-600">
                    {page} / {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= totalPages}
                    onClick={() => handlePageChange(page + 1)}
                  >
                    下一页
                  </Button>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>暂无异常订单 | No anomaly orders found</p>
              <p className="text-sm mt-2">当前筛选条件下没有检测到异常</p>
            </div>
          )}
        </div>

        {/* Price Range Stats */}
        {overview?.priceRanges && overview.priceRanges.length > 0 && (
          <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              各价格区间统计 | Price Range Statistics
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      价格区间
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      订单数
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      平均调用
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      标准差
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      阈值
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      异常数
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {overview.priceRanges.map((range) => (
                    <tr key={range.rangeLabel} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        {range.rangeLabel}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {range.taskCount}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {range.meanCalls.toFixed(1)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {range.stdCalls.toFixed(1)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {range.threshold.toFixed(1)}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {range.anomalyCount > 0 ? (
                          <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
                            {range.anomalyCount}
                          </span>
                        ) : (
                          <span className="text-green-600">0</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
