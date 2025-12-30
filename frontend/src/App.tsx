import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/common/Layout'
import Home from './pages/Home'
import Upload from './pages/Upload'
import History from './pages/History'
import Intervention from './pages/Intervention'
import Yolo from './pages/Yolo'
import Review from './pages/Review'

/**
 * Main Application Component
 * 主应用组件
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="upload" element={<Upload />} />
          <Route path="history" element={<History />} />
          <Route path="intervention/:sessionId" element={<Intervention />} />
          <Route path="yolo/:sessionId" element={<Yolo />} />
          <Route path="review/:sessionId" element={<Review />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
