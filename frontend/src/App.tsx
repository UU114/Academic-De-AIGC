import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/common/Layout'
import Home from './pages/Home'
import Upload from './pages/Upload'
import History from './pages/History'
import Profile from './pages/Profile'
import Feedback from './pages/Feedback'
import Intervention from './pages/Intervention'
import Yolo from './pages/Yolo'
import YoloFullAuto from './pages/YoloFullAuto'
import Review from './pages/Review'
import ThreeLevelFlow from './pages/ThreeLevelFlow'
import Step1_1 from './pages/Step1_1'
import Step1_2 from './pages/Step1_2'
import Step2 from './pages/Step2'
// 5-Layer Analysis Components (New Architecture)
// 5层分析组件（新架构）
import {
  LayerTermLock,
  LayerStep1_1,
  LayerStep1_2,
  LayerStep1_3,
  LayerStep1_4,
  LayerStep1_5,
  LayerStep2_0,
  LayerStep2_1,
  LayerStep2_2,
  LayerStep2_3,
  LayerStep2_4,
  LayerStep2_5,
  LayerStep3_0,
  LayerStep3_1,
  LayerStep3_2,
  LayerStep3_3,
  LayerStep3_4,
  LayerStep3_5,
  LayerStep4_0,
  LayerStep4_1,
  LayerStep4_Console,
  LayerLexicalV2,
  LayerDocument,
  LayerSection,
  LayerParagraph,
  LayerSentence,
  LayerLexical,
} from './pages/layers'
import AdminLogin from './pages/admin/AdminLogin'
import AdminDashboard from './pages/admin/AdminDashboard'
import AnomalyDetection from './pages/admin/AnomalyDetection'
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
        {/* Admin routes (outside main layout) */}
        {/* 管理员路由（在主布局之外） */}
        <Route path="admin/login" element={<AdminLogin />} />
        <Route path="admin" element={<AdminDashboard />} />
        <Route path="admin/anomaly" element={<AnomalyDetection />} />

        {/* Main application routes */}
        {/* 主应用路由 */}
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="upload" element={<Upload />} />
          <Route path="history" element={<History />} />
          <Route path="profile" element={<Profile />} />
          <Route path="feedback" element={<Feedback />} />
          {/* ============================================ */}
          {/* DEPRECATED: Legacy 4-step flow routes       */}
          {/* 已废弃：旧版4步流程路由                        */}
          {/* These routes use old APIs (/api/v1/structure, /api/v1/transition) */}
          {/* Users should use the new 5-layer routes below instead */}
          {/* 这些路由使用旧API，用户应使用下方的新版5层路由 */}
          {/* DO NOT DELETE - kept for backward compatibility */}
          {/* 请勿删除 - 保留用于向后兼容                    */}
          {/* ============================================ */}
          <Route path="flow/step1-1/:documentId" element={<Step1_1 />} />
          <Route path="flow/step1-2/:documentId" element={<Step1_2 />} />
          <Route path="flow/step2/:documentId" element={<Step2 />} />

          {/* 5-Layer Analysis Routes (New Architecture) */}
          {/* 5层分析路由（新架构） */}
          {/* Step 1.0: Term Locking (must run before all layers) */}
          <Route path="flow/term-lock/:documentId" element={<LayerTermLock />} />
          {/* Layer 5 Sub-steps: Document Level Analysis */}
          {/* Layer 5 子步骤：全文层面分析 */}
          <Route path="flow/layer5-step1-1/:documentId" element={<LayerStep1_1 />} />
          <Route path="flow/layer5-step1-2/:documentId" element={<LayerStep1_2 />} />
          <Route path="flow/layer5-step1-3/:documentId" element={<LayerStep1_3 />} />
          <Route path="flow/layer5-step1-4/:documentId" element={<LayerStep1_4 />} />
          <Route path="flow/layer5-step1-5/:documentId" element={<LayerStep1_5 />} />
          {/* Layer 4 Sub-steps: Section Level Analysis */}
          {/* Layer 4 子步骤：章节层面分析 */}
          <Route path="flow/layer4-step2-0/:documentId" element={<LayerStep2_0 />} />
          <Route path="flow/layer4-step2-1/:documentId" element={<LayerStep2_1 />} />
          <Route path="flow/layer4-step2-2/:documentId" element={<LayerStep2_2 />} />
          <Route path="flow/layer4-step2-3/:documentId" element={<LayerStep2_3 />} />
          <Route path="flow/layer4-step2-4/:documentId" element={<LayerStep2_4 />} />
          <Route path="flow/layer4-step2-5/:documentId" element={<LayerStep2_5 />} />
          {/* Layer 3 Sub-steps: Paragraph Level Analysis */}
          {/* Layer 3 子步骤：段落层面分析 */}
          <Route path="flow/layer3-step3-0/:documentId" element={<LayerStep3_0 />} />
          <Route path="flow/layer3-step3-1/:documentId" element={<LayerStep3_1 />} />
          <Route path="flow/layer3-step3-2/:documentId" element={<LayerStep3_2 />} />
          <Route path="flow/layer3-step3-3/:documentId" element={<LayerStep3_3 />} />
          <Route path="flow/layer3-step3-4/:documentId" element={<LayerStep3_4 />} />
          <Route path="flow/layer3-step3-5/:documentId" element={<LayerStep3_5 />} />
          {/* Layer 2 Sub-steps: Sentence Level Analysis */}
          {/* Layer 2 子步骤：句子层面分析 */}
          <Route path="flow/layer2-step4-0/:documentId" element={<LayerStep4_0 />} />
          <Route path="flow/layer2-step4-1/:documentId" element={<LayerStep4_1 />} />
          <Route path="flow/layer2-step4-console/:documentId" element={<LayerStep4_Console />} />
          {/* Layer 1 Sub-steps: Lexical Level Analysis (Enhanced) */}
          {/* Layer 1 子步骤：词汇层面分析（增强版） */}
          <Route path="flow/layer1-lexical-v2/:documentId" element={<LayerLexicalV2 />} />
          {/* ============================================ */}
          {/* DEPRECATED: Legacy combined layer routes    */}
          {/* 已废弃：旧版组合层级路由                       */}
          {/* These are superseded by the granular LayerStep routes above */}
          {/* 已被上方细粒度的LayerStep路由取代              */}
          {/* DO NOT DELETE - kept for backward compatibility */}
          {/* 请勿删除 - 保留用于向后兼容                    */}
          {/* ============================================ */}
          <Route path="flow/layer-document/:documentId" element={<LayerDocument />} />
          <Route path="flow/layer-section/:documentId" element={<LayerSection />} />
          <Route path="flow/layer-paragraph/:documentId" element={<LayerParagraph />} />
          <Route path="flow/layer-sentence/:documentId" element={<LayerSentence />} />
          <Route path="flow/layer-lexical/:documentId" element={<LayerLexical />} />
          {/* DEPRECATED: Legacy ThreeLevelFlow - uses old API structure */}
          {/* 已废弃：旧版三级流程 - 使用旧API结构 */}
          <Route path="flow/:documentId" element={<ThreeLevelFlow />} />
          <Route path="intervention/:sessionId" element={<Intervention />} />
          <Route path="yolo/:sessionId" element={<Yolo />} />
          <Route path="yolo-full-auto/:sessionId" element={<YoloFullAuto />} />
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
