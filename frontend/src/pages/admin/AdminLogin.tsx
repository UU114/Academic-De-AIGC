/**
 * Admin Login Page - Admin authentication with secret key
 * 管理员登录页面 - 使用密钥进行管理员认证
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, AlertCircle, Loader2 } from 'lucide-react';
import Button from '../../components/common/Button';
import { useAdminStore } from '../../stores/adminStore';

export default function AdminLogin() {
  const navigate = useNavigate();
  const { adminLogin, isLoading, error, clearError, isAdminLoggedIn } = useAdminStore();
  const [secretKey, setSecretKey] = useState('');

  // Redirect if already logged in
  // 如果已登录则重定向
  if (isAdminLoggedIn) {
    navigate('/admin');
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!secretKey.trim()) {
      return;
    }

    const success = await adminLogin(secretKey);
    if (success) {
      navigate('/admin');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-primary-100">
            <Lock className="h-8 w-8 text-primary-600" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            管理员登录
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Admin Dashboard Login
          </p>
        </div>

        {/* Login Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {/* Error Alert */}
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Secret Key Input */}
          <div>
            <label htmlFor="secret-key" className="block text-sm font-medium text-gray-700">
              管理员密钥 | Admin Secret Key
            </label>
            <div className="mt-1">
              <input
                id="secret-key"
                name="secret-key"
                type="password"
                required
                className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="Enter admin secret key..."
                value={secretKey}
                onChange={(e) => setSecretKey(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <p className="mt-1 text-xs text-gray-500">
              请输入在环境变量 ADMIN_SECRET_KEY 中配置的密钥
            </p>
          </div>

          {/* Submit Button */}
          <div>
            <Button
              type="submit"
              variant="primary"
              className="w-full"
              disabled={isLoading || !secretKey.trim()}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  登录中...
                </>
              ) : (
                '登录 | Login'
              )}
            </Button>
          </div>

          {/* Back Link */}
          <div className="text-center">
            <a
              href="/"
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              ← 返回首页 | Back to Home
            </a>
          </div>
        </form>
      </div>
    </div>
  );
}
