/**
 * Feedback Page
 * 问题反馈页面
 *
 * Allows users to submit feedback and issue reports.
 * 允许用户提交反馈和问题报告。
 */

import { useState } from 'react';
import { MessageSquare, Send, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

// ==========================================
// Types
// 类型定义
// ==========================================

interface FeedbackResponse {
  success: boolean;
  message: string;
  message_zh: string;
  feedback_id?: string;
}

// ==========================================
// API Configuration
// API配置
// ==========================================

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ==========================================
// Main Component
// 主组件
// ==========================================

export default function Feedback() {
  // Form state
  // 表单状态
  const [contact, setContact] = useState('');
  const [content, setContent] = useState('');

  // UI state
  // UI状态
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  /**
   * Handle form submission
   * 处理表单提交
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate content
    // 验证内容
    const trimmedContent = content.trim();
    if (trimmedContent.length < 5) {
      setSubmitResult({
        success: false,
        message: '反馈内容至少需要5个字符'
      });
      return;
    }

    if (trimmedContent.length > 2000) {
      setSubmitResult({
        success: false,
        message: '反馈内容不能超过2000个字符'
      });
      return;
    }

    setIsSubmitting(true);
    setSubmitResult(null);

    try {
      const response = await fetch(`${API_BASE}/api/v1/feedback/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contact: contact.trim() || null,
          content: trimmedContent
        })
      });

      const data: FeedbackResponse = await response.json();

      if (response.ok && data.success) {
        setSubmitResult({
          success: true,
          message: data.message_zh || '反馈提交成功，感谢您的反馈！'
        });
        // Clear form on success
        // 成功后清空表单
        setContact('');
        setContent('');
      } else {
        setSubmitResult({
          success: false,
          message: data.message_zh || '提交失败，请稍后重试'
        });
      }
    } catch (error) {
      console.error('Feedback submission error:', error);
      setSubmitResult({
        success: false,
        message: '网络错误，请检查网络连接后重试'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
          <MessageSquare className="w-8 h-8 text-primary-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          问题反馈
        </h1>
        <p className="text-gray-600">
          如果您在使用过程中遇到问题或有任何建议，请告诉我们
        </p>
      </div>

      {/* Feedback Form */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Contact Field */}
          <div>
            <label
              htmlFor="contact"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              联系方式
              <span className="text-gray-400 font-normal ml-2">(选填)</span>
            </label>
            <input
              type="text"
              id="contact"
              value={contact}
              onChange={(e) => setContact(e.target.value)}
              placeholder="邮箱、手机号或微信号"
              maxLength={200}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
              disabled={isSubmitting}
            />
            <p className="mt-1.5 text-xs text-gray-500">
              留下联系方式方便我们回复您的问题
            </p>
          </div>

          {/* Content Field */}
          <div>
            <label
              htmlFor="content"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              反馈内容
              <span className="text-red-500 ml-1">*</span>
            </label>
            <textarea
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="请详细描述您遇到的问题或建议..."
              rows={6}
              maxLength={2000}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors resize-none"
              disabled={isSubmitting}
              required
            />
            <div className="mt-1.5 flex justify-between text-xs text-gray-500">
              <span>最少5个字符</span>
              <span>{content.length}/2000</span>
            </div>
          </div>

          {/* Submit Result */}
          {submitResult && (
            <div
              className={`flex items-start gap-3 p-4 rounded-lg ${
                submitResult.success
                  ? 'bg-green-50 text-green-800'
                  : 'bg-red-50 text-red-800'
              }`}
            >
              {submitResult.success ? (
                <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              )}
              <p className="text-sm">{submitResult.message}</p>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting || content.trim().length < 5}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 focus:ring-4 focus:ring-primary-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                提交中...
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                提交反馈
              </>
            )}
          </button>
        </form>
      </div>

      {/* Tips */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="text-sm font-medium text-gray-700 mb-2">提示</h3>
        <ul className="text-xs text-gray-500 space-y-1">
          <li>• 请尽量详细描述问题，包括操作步骤和错误信息</li>
          <li>• 如果方便，可以留下联系方式以便我们进一步沟通</li>
          <li>• 您的反馈将帮助我们不断改进产品</li>
        </ul>
      </div>
    </div>
  );
}
