/**
 * User Profile Page
 * 用户中心页面
 *
 * Displays user info, statistics, and order history.
 * 显示用户信息、统计数据和订单历史。
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User,
  Phone,
  Calendar,
  FileText,
  CreditCard,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Loader2
} from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { useModeStore } from '../stores/modeStore';

// ==========================================
// Types
// 类型定义
// ==========================================

interface UserProfile {
  user_id: string;
  platform_user_id?: string;
  nickname?: string;
  phone?: string;
  created_at?: string;
  last_login_at?: string;
  is_debug: boolean;
  total_tasks: number;
  total_spent: number;
}

interface OrderItem {
  task_id: string;
  document_name?: string;
  word_count: number;
  price: number;
  status: string;
  payment_status: string;
  created_at: string;
  paid_at?: string;
}

interface OrderListResponse {
  orders: OrderItem[];
  total: number;
  page: number;
  page_size: number;
}

// ==========================================
// Helper Functions
// 辅助函数
// ==========================================

/**
 * Format date string to localized format
 * 将日期字符串格式化为本地化格式
 */
function formatDate(dateStr?: string): string {
  if (!dateStr) return '-';
  try {
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
}

/**
 * Get status display info
 * 获取状态显示信息
 */
function getStatusInfo(status: string, paymentStatus: string): {
  label: string;
  labelZh: string;
  color: string;
  icon: React.ReactNode;
} {
  if (paymentStatus === 'paid') {
    if (status === 'completed') {
      return {
        label: 'Completed',
        labelZh: '已完成',
        color: 'text-green-600 bg-green-50',
        icon: <CheckCircle className="w-4 h-4" />
      };
    }
    if (status === 'processing') {
      return {
        label: 'Processing',
        labelZh: '处理中',
        color: 'text-blue-600 bg-blue-50',
        icon: <Loader2 className="w-4 h-4 animate-spin" />
      };
    }
    return {
      label: 'Paid',
      labelZh: '已支付',
      color: 'text-green-600 bg-green-50',
      icon: <CheckCircle className="w-4 h-4" />
    };
  }

  if (paymentStatus === 'pending') {
    return {
      label: 'Pending',
      labelZh: '待支付',
      color: 'text-amber-600 bg-amber-50',
      icon: <Clock className="w-4 h-4" />
    };
  }

  if (paymentStatus === 'failed' || status === 'expired') {
    return {
      label: 'Failed/Expired',
      labelZh: '失败/过期',
      color: 'text-red-600 bg-red-50',
      icon: <XCircle className="w-4 h-4" />
    };
  }

  return {
    label: 'Unpaid',
    labelZh: '未支付',
    color: 'text-gray-600 bg-gray-50',
    icon: <AlertCircle className="w-4 h-4" />
  };
}

// ==========================================
// Main Component
// 主组件
// ==========================================

export default function Profile() {
  const navigate = useNavigate();
  const { isLoggedIn, token } = useAuthStore();
  const { isDebug } = useModeStore();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [totalOrders, setTotalOrders] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  const [isLoadingOrders, setIsLoadingOrders] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const pageSize = 10;
  const totalPages = Math.ceil(totalOrders / pageSize);

  // Redirect if not logged in (unless in debug mode)
  // 未登录时重定向（调试模式除外）
  useEffect(() => {
    if (!isDebug && !isLoggedIn) {
      navigate('/');
    }
  }, [isDebug, isLoggedIn, navigate]);

  // Fetch user profile
  // 获取用户资料
  useEffect(() => {
    const fetchProfile = async () => {
      setIsLoadingProfile(true);
      setError(null);

      try {
        const headers: Record<string, string> = {
          'Content-Type': 'application/json'
        };
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch('/api/v1/auth/profile', { headers });

        if (!response.ok) {
          throw new Error('Failed to fetch profile');
        }

        const data = await response.json();
        setProfile(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoadingProfile(false);
      }
    };

    if (isLoggedIn || isDebug) {
      fetchProfile();
    }
  }, [isLoggedIn, isDebug, token]);

  // Fetch orders
  // 获取订单
  useEffect(() => {
    const fetchOrders = async () => {
      setIsLoadingOrders(true);

      try {
        const headers: Record<string, string> = {
          'Content-Type': 'application/json'
        };
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(
          `/api/v1/auth/orders?page=${currentPage}&page_size=${pageSize}`,
          { headers }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch orders');
        }

        const data: OrderListResponse = await response.json();
        setOrders(data.orders);
        setTotalOrders(data.total);
      } catch (err) {
        console.error('Failed to fetch orders:', err);
      } finally {
        setIsLoadingOrders(false);
      }
    };

    if (isLoggedIn || isDebug) {
      fetchOrders();
    }
  }, [isLoggedIn, isDebug, token, currentPage]);

  // Loading state
  // 加载状态
  if (isLoadingProfile) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  // Error state
  // 错误状态
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
        <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Failed to load profile
        </h2>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Retry 重试
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Center 用户中心</h1>
          <p className="text-gray-600 text-sm">
            Manage your account and view order history
          </p>
        </div>
      </div>

      {/* Debug Mode Notice */}
      {isDebug && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-amber-700">
            <AlertCircle className="w-5 h-5" />
            <span className="font-medium">Debug Mode</span>
          </div>
          <p className="text-amber-600 text-sm mt-1">
            调试模式下显示模拟数据，订单历史为空。
          </p>
        </div>
      )}

      {/* User Profile Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <User className="w-5 h-5 text-blue-600" />
          Profile Information 个人信息
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Nickname */}
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <User className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-xs text-gray-500">Nickname 昵称</p>
              <p className="font-medium text-gray-900">
                {profile?.nickname || 'Not set 未设置'}
              </p>
            </div>
          </div>

          {/* Phone */}
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <Phone className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-xs text-gray-500">Phone 手机号</p>
              <p className="font-medium text-gray-900">
                {profile?.phone || 'Not set 未设置'}
              </p>
            </div>
          </div>

          {/* Created At */}
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <Calendar className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-xs text-gray-500">Registered 注册时间</p>
              <p className="font-medium text-gray-900">
                {formatDate(profile?.created_at)}
              </p>
            </div>
          </div>

          {/* Last Login */}
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <Clock className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-xs text-gray-500">Last Login 最后登录</p>
              <p className="font-medium text-gray-900">
                {formatDate(profile?.last_login_at)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Statistics Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <CreditCard className="w-5 h-5 text-blue-600" />
          Usage Statistics 使用统计
        </h2>

        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-3xl font-bold text-blue-600">
              {profile?.total_tasks || 0}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              Total Tasks 总任务数
            </p>
          </div>

          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-3xl font-bold text-green-600">
              ¥{(profile?.total_spent || 0).toFixed(2)}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              Total Spent 总消费
            </p>
          </div>
        </div>
      </div>

      {/* Order History */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          Order History 订单历史
        </h2>

        {isLoadingOrders ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : orders.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="w-12 h-12 mx-auto text-gray-300 mb-3" />
            <p>No orders yet 暂无订单</p>
          </div>
        ) : (
          <>
            {/* Order List */}
            <div className="space-y-3">
              {orders.map((order) => {
                const statusInfo = getStatusInfo(order.status, order.payment_status);
                return (
                  <div
                    key={order.task_id}
                    className="flex items-center justify-between p-4 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">
                        {order.document_name || 'Untitled 未命名'}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        {order.word_count.toLocaleString()} words · {formatDate(order.created_at)}
                      </p>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="font-semibold text-gray-900">
                          ¥{order.price.toFixed(2)}
                        </p>
                      </div>

                      <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm ${statusInfo.color}`}>
                        {statusInfo.icon}
                        <span>{statusInfo.labelZh}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <p className="text-sm text-gray-500">
                  Page {currentPage} of {totalPages} · {totalOrders} orders
                </p>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>

                  <button
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
