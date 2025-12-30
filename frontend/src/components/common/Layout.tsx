import { Outlet, Link, useLocation } from 'react-router-dom';
import { FileText, Upload, Settings, Home, Clock, Wand2 } from 'lucide-react';

/**
 * Main layout component with navigation
 * 带导航的主布局组件
 */
export default function Layout() {
  const location = useLocation();

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

            {/* Settings button */}
            <button
              className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
              title="Settings"
            >
              <Settings className="w-5 h-5" />
            </button>
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
          <p className="text-center text-sm text-gray-500">
            AcademicGuard - AIGC Detection & Human-AI Collaborative Humanization Engine
          </p>
        </div>
      </footer>
    </div>
  );
}
