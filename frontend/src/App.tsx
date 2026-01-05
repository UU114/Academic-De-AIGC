import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/common/Layout'
import Home from './pages/Home'
import Upload from './pages/Upload'
import History from './pages/History'
import Profile from './pages/Profile'
import Intervention from './pages/Intervention'
import Yolo from './pages/Yolo'
import Review from './pages/Review'
import ThreeLevelFlow from './pages/ThreeLevelFlow'
import Step1_1 from './pages/Step1_1'
import Step1_2 from './pages/Step1_2'
import Step2 from './pages/Step2'
import { useModeStore } from './stores/modeStore'
import { useAuthStore } from './stores/authStore'
import { FloatingModeBadge } from './components/auth/ModeIndicator'

/**
 * Main Application Component
 * 主应用组件
 *
 * Routes:
 * - /flow/step1-1/:documentId - Step 1-1: Document structure analysis
 * - /flow/step1-2/:documentId - Step 1-2: Paragraph relationship analysis
 * - /flow/step2/:documentId - Step 2: Transition analysis
 * - /intervention/:sessionId - Step 3: Sentence polish (intervention mode)
 */
function App() {
  const { loadMode } = useModeStore();
  const { checkAuth } = useAuthStore();

  // Initialize mode and auth state on app load
  // 应用加载时初始化模式和认证状态
  useEffect(() => {
    const init = async () => {
      await loadMode();
      await checkAuth();
    };
    init();
  }, [loadMode, checkAuth]);

  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="upload" element={<Upload />} />
          <Route path="history" element={<History />} />
          <Route path="profile" element={<Profile />} />
          {/* New 4-step flow routes */}
          {/* 新的4步流程路由 */}
          <Route path="flow/step1-1/:documentId" element={<Step1_1 />} />
          <Route path="flow/step1-2/:documentId" element={<Step1_2 />} />
          <Route path="flow/step2/:documentId" element={<Step2 />} />
          {/* Legacy combined flow (kept for backward compatibility) */}
          {/* 遗留组合流程（保持向后兼容） */}
          <Route path="flow/:documentId" element={<ThreeLevelFlow />} />
          <Route path="intervention/:sessionId" element={<Intervention />} />
          <Route path="yolo/:sessionId" element={<Yolo />} />
          <Route path="review/:sessionId" element={<Review />} />
        </Route>
      </Routes>
      {/* Floating debug mode badge */}
      {/* 浮动调试模式徽章 */}
      <FloatingModeBadge />
    </BrowserRouter>
  )
}

export default App
