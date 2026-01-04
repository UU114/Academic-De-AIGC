/**
 * Payment Status Component
 * 支付状态组件
 *
 * Polls payment status and shows progress.
 * 轮询支付状态并显示进度。
 */

import React, { useState, useEffect, useCallback } from 'react';
import { CheckCircle, XCircle, Clock, Loader2, QrCode } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';

interface PaymentStatusProps {
  taskId: string;
  paymentUrl?: string;
  qrCodeUrl?: string;
  onPaid: () => void;
  onFailed: () => void;
  onCancel: () => void;
}

type StatusType = 'pending' | 'paid' | 'failed' | 'cancelled';

export default function PaymentStatus({
  taskId,
  paymentUrl,
  qrCodeUrl,
  onPaid,
  onFailed,
  onCancel,
}: PaymentStatusProps) {
  const { token } = useAuthStore();

  const [status, setStatus] = useState<StatusType>('pending');
  const [isPolling, setIsPolling] = useState(true);

  // Poll payment status
  // 轮询支付状态
  const checkStatus = useCallback(async () => {
    try {
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`/api/v1/payment/status/${taskId}`, {
        headers,
      });

      if (!response.ok) {
        throw new Error('Failed to check status');
      }

      const data = await response.json();

      if (data.payment_status === 'paid') {
        setStatus('paid');
        setIsPolling(false);
        onPaid();
      } else if (data.payment_status === 'failed') {
        setStatus('failed');
        setIsPolling(false);
        onFailed();
      }
    } catch (error) {
      console.error('Status check error:', error);
    }
  }, [taskId, token, onPaid, onFailed]);

  // Start polling
  // 开始轮询
  useEffect(() => {
    if (!isPolling) return;

    // Initial check
    checkStatus();

    // Poll every 3 seconds
    const interval = setInterval(checkStatus, 3000);

    // Stop after 10 minutes
    const timeout = setTimeout(() => {
      setIsPolling(false);
    }, 10 * 60 * 1000);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [isPolling, checkStatus]);

  // Render status icon
  // 渲染状态图标
  const renderStatusIcon = () => {
    switch (status) {
      case 'paid':
        return <CheckCircle className="w-16 h-16 text-green-500" />;
      case 'failed':
        return <XCircle className="w-16 h-16 text-red-500" />;
      case 'cancelled':
        return <XCircle className="w-16 h-16 text-gray-500" />;
      default:
        return <Loader2 className="w-16 h-16 text-blue-500 animate-spin" />;
    }
  };

  // Render status message
  // 渲染状态消息
  const renderStatusMessage = () => {
    switch (status) {
      case 'paid':
        return (
          <>
            <h3 className="text-xl font-semibold text-green-600">Payment Successful</h3>
            <p className="text-gray-600 mt-2">支付成功，即将开始处理...</p>
          </>
        );
      case 'failed':
        return (
          <>
            <h3 className="text-xl font-semibold text-red-600">Payment Failed</h3>
            <p className="text-gray-600 mt-2">支付失败，请重试</p>
          </>
        );
      case 'cancelled':
        return (
          <>
            <h3 className="text-xl font-semibold text-gray-600">Payment Cancelled</h3>
            <p className="text-gray-600 mt-2">支付已取消</p>
          </>
        );
      default:
        return (
          <>
            <h3 className="text-xl font-semibold text-gray-900">Waiting for Payment</h3>
            <p className="text-gray-600 mt-2">等待支付中...</p>
          </>
        );
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <div className="flex flex-col items-center text-center">
        {/* Status icon */}
        {renderStatusIcon()}

        {/* Status message */}
        <div className="mt-6">
          {renderStatusMessage()}
        </div>

        {/* QR code or payment link (only when pending) */}
        {status === 'pending' && (
          <div className="mt-8 w-full max-w-sm">
            {qrCodeUrl ? (
              <div className="flex flex-col items-center">
                <div className="p-4 bg-white border-2 border-gray-200 rounded-xl">
                  <img
                    src={qrCodeUrl}
                    alt="Payment QR Code"
                    className="w-48 h-48"
                  />
                </div>
                <p className="mt-4 text-sm text-gray-600">
                  Scan QR code to pay 扫码支付
                </p>
              </div>
            ) : paymentUrl ? (
              <div className="flex flex-col items-center gap-4">
                <a
                  href={paymentUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors text-center"
                >
                  Open Payment Page 打开支付页面
                </a>
                <p className="text-sm text-gray-500">
                  Click the button to complete payment in a new tab
                </p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 text-gray-500">
                <QrCode className="w-12 h-12" />
                <p className="text-sm">Loading payment info...</p>
              </div>
            )}

            {/* Polling indicator */}
            <div className="mt-6 flex items-center justify-center gap-2 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              <span>Auto-checking payment status...</span>
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="mt-8 flex gap-4">
          {status === 'pending' && (
            <button
              onClick={onCancel}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
            >
              Cancel 取消
            </button>
          )}
          {status === 'failed' && (
            <>
              <button
                onClick={onCancel}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
              >
                Cancel 取消
              </button>
              <button
                onClick={() => setStatus('pending')}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Retry 重试
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
