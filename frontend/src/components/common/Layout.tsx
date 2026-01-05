import { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { FileText, Upload, Home, Clock, Wand2, User, LogOut, Settings, MessageSquare } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import LoginModal from '../auth/LoginModal';

/**
 * Main layout component with navigation
 * 带导航的主布局组件
 */
export default function Layout() {
  const location = useLocation();
  const { isLoggedIn, user, logout } = useAuthStore();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Check if on intervention page to show DE-AIGC tab
  // 检查是否在干预模式页面以显示DE-AIGC标签
  const isInterventionPage = location.pathname.startsWith('/intervention');
  const interventionSessionId = isInterventionPage
    ? location.pathname.split('/intervention/')[1]
    : null;

  const navItems = [
    { path: '/', icon: Home, label: '首页', labelEn: 'Home' },
    { path: '/upload', icon: Upload, label: '新建', labelEn: 'New' },
    { path: '/history', icon: Clock, label: '历史', labelEn: 'History' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2">
              <FileText className="w-8 h-8 text-primary-600" />
              <span className="text-xl font-bold text-gray-900">
                AcademicGuard
              </span>
            </Link>

            {/* Navigation */}
            <nav className="flex items-center space-x-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`
                    flex items-center px-3 py-2 rounded-lg text-sm font-medium
                    transition-colors duration-200
                    ${
                      isActive(item.path)
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }
                  `}
                >
                  <item.icon className="w-4 h-4 mr-1.5" />
                  <span>{item.label}</span>
                </Link>
              ))}
              {/* DE-AIGC tab - only show when on intervention page */}
              {/* DE-AIGC标签 - 仅在干预模式页面显示 */}
              {isInterventionPage && interventionSessionId && (
                <Link
                  to={`/intervention/${interventionSessionId}`}
                  className="flex items-center px-3 py-2 rounded-lg text-sm font-medium bg-primary-100 text-primary-700 border border-primary-300"
                >
                  <Wand2 className="w-4 h-4 mr-1.5" />
                  <span>DE-AIGC</span>
                </Link>
              )}
            </nav>

            {/* User button - login or user info */}
            {/* 用户按钮 - 登录或用户信息 */}
            {isLoggedIn ? (
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors"
                  title={user?.nickname || user?.phone || 'User'}
                >
                  <User className="w-5 h-5" />
                  <span className="text-sm font-medium max-w-[100px] truncate">
                    {user?.nickname || user?.phone?.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') || 'User'}
                  </span>
                </button>
                {/* User dropdown menu */}
                {showUserMenu && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setShowUserMenu(false)}
                    />
                    <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                      <div className="px-4 py-2 border-b border-gray-100">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {user?.nickname || 'User'}
                        </p>
                        <p className="text-xs text-gray-500 truncate">
                          {user?.phone?.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')}
                        </p>
                      </div>
                      <Link
                        to="/profile"
                        onClick={() => setShowUserMenu(false)}
                        className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                      >
                        <Settings className="w-4 h-4" />
                        <span>User Center 用户中心</span>
                      </Link>
                      <button
                        onClick={() => {
                          logout();
                          setShowUserMenu(false);
                        }}
                        className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>Logout 退出登录</span>
                      </button>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <button
                onClick={() => setShowLoginModal(true)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                <User className="w-4 h-4" />
                <span className="text-sm font-medium">Login 登录</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-center gap-4">
            <p className="text-sm text-gray-500">
              AcademicGuard - AIGC Detection & Human-AI Collaborative Humanization Engine
            </p>
            <Link
              to="/feedback"
              className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-primary-600 transition-colors"
            >
              <MessageSquare className="w-4 h-4" />
              <span>问题反馈</span>
            </Link>
          </div>
        </div>
      </footer>

      {/* Login Modal */}
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
      />
    </div>
  );
}
