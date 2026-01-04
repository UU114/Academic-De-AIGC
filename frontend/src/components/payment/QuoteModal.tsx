/**
 * Quote Modal Component
 * 报价确认弹窗组件
 *
 * Shows pricing quote and allows user to proceed to payment.
 * 显示报价并允许用户继续支付。
 */

import React, { useState, useEffect } from 'react';
import { X, FileText, Calculator, AlertCircle, Loader2, Check } from 'lucide-react';
import { useModeStore } from '../../stores/modeStore';
import { useAuthStore } from '../../stores/authStore';

interface QuoteData {
  taskId: string;
  wordCountRaw: number;
  wordCountBillable: number;
  billableUnits: number;
  calculatedPrice: number;
  finalPrice: number;
  isMinimumCharge: boolean;
  minimumCharge: number;
  isDebugMode: boolean;
  paymentRequired: boolean;
}

interface QuoteModalProps {
  isOpen: boolean;
  onClose: () => void;
  taskId: string;
  documentName?: string;
  onConfirm: (taskId: string) => void;
}

export default function QuoteModal({
  isOpen,
  onClose,
  taskId,
  documentName,
  onConfirm,
}: QuoteModalProps) {
  const { pricing, isDebug } = useModeStore();
  const { token } = useAuthStore();

  const [quote, setQuote] = useState<QuoteData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch quote data
  // 获取报价数据
  useEffect(() => {
    if (!isOpen || !taskId) return;

    const fetchQuote = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        };
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`/api/v1/payment/quote/${taskId}`, {
          headers,
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail?.message_zh || data.detail?.message || 'Failed to get quote');
        }

        const data = await response.json();
        setQuote({
          taskId: data.task_id,
          wordCountRaw: data.word_count_raw,
          wordCountBillable: data.word_count_billable,
          billableUnits: data.billable_units,
          calculatedPrice: data.calculated_price,
          finalPrice: data.final_price,
          isMinimumCharge: data.is_minimum_charge,
          minimumCharge: data.minimum_charge,
          isDebugMode: data.is_debug_mode,
          paymentRequired: data.payment_required,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    };

    fetchQuote();
  }, [isOpen, taskId, token]);

  // Handle confirm
  // 处理确认
  const handleConfirm = () => {
    if (quote) {
      onConfirm(quote.taskId);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Order Confirmation
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              确认订单
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
              <p className="mt-4 text-gray-600">Calculating price...</p>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center gap-2 text-red-700">
                <AlertCircle className="w-5 h-5" />
                <span>{error}</span>
              </div>
            </div>
          ) : quote ? (
            <div className="space-y-6">
              {/* File info */}
              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <FileText className="w-8 h-8 text-blue-600" />
                <div>
                  <p className="font-medium text-gray-900">
                    {documentName || 'Document'}
                  </p>
                  <p className="text-sm text-gray-500">
                    {quote.wordCountRaw.toLocaleString()} words detected
                  </p>
                </div>
              </div>

              {/* Pricing breakdown */}
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-gray-600">Detected Words 检测字数</span>
                  <span className="font-medium">{quote.wordCountBillable.toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b text-sm text-gray-500">
                  <span>(References excluded 已排除参考文献)</span>
                  <span></span>
                </div>
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-gray-600">Billing Units 计费单元</span>
                  <span className="font-medium">{quote.billableUnits} units</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-gray-600">Rate 单价</span>
                  <span className="font-medium">¥{pricing.pricePerUnit} / 100 words</span>
                </div>

                {/* Total */}
                <div className="flex justify-between items-center py-4 bg-blue-50 rounded-lg px-4 mt-4">
                  <span className="text-lg font-medium text-gray-900">Total 应付金额</span>
                  <div className="text-right">
                    {quote.isDebugMode ? (
                      <div className="flex items-center gap-2">
                        <span className="text-lg line-through text-gray-400">
                          ¥{quote.calculatedPrice.toFixed(2)}
                        </span>
                        <span className="px-2 py-1 bg-amber-100 text-amber-700 text-sm font-medium rounded">
                          FREE (Debug)
                        </span>
                      </div>
                    ) : (
                      <span className="text-2xl font-bold text-blue-600">
                        ¥{quote.finalPrice.toFixed(2)}
                      </span>
                    )}
                  </div>
                </div>

                {/* Minimum charge notice */}
                {quote.isMinimumCharge && !quote.isDebugMode && (
                  <div className="flex items-start gap-2 text-sm text-amber-700">
                    <AlertCircle className="w-4 h-4 mt-0.5" />
                    <span>
                      Minimum charge of ¥{quote.minimumCharge} applied.
                      已触发最低消费 ¥{quote.minimumCharge}
                    </span>
                  </div>
                )}
              </div>

              {/* Debug mode notice */}
              {quote.isDebugMode && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-amber-500 mt-0.5" />
                    <div className="text-sm">
                      <p className="font-medium text-amber-800">Debug Mode</p>
                      <p className="text-amber-700 mt-1">
                        Payment is skipped in debug mode. Click confirm to proceed directly.
                        调试模式下跳过支付，点击确认直接处理。
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="p-6 bg-gray-50 border-t flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-100 transition-colors"
          >
            Cancel 取消
          </button>
          <button
            onClick={handleConfirm}
            disabled={isLoading || !!error}
            className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {quote?.isDebugMode ? (
              <>
                <Check className="w-5 h-5" />
                Confirm 确认
              </>
            ) : (
              <>
                Proceed to Pay 去支付
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
