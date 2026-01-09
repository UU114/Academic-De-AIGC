import { Link } from 'react-router-dom';
import {
  FileText,
  Zap,
  Shield,
  ArrowRight,
  CheckCircle,
  Fingerprint,
  Activity,
  Calculator,
  Lock,
  Target,
  Brain,
  Layers,
  Layout,
  AlignJustify,
  Type,
  Hash,
  ChevronDown,
  ChevronRight,
  Play,
  Download,
  HelpCircle
} from 'lucide-react';
import Button from '../components/common/Button';
import ModeIndicator from '../components/auth/ModeIndicator';
import { useModeStore } from '../stores/modeStore';
import { useAuthStore } from '../stores/authStore';
import { useState } from 'react';

/**
 * Home page - Landing page with 5-layer architecture showcase
 * 首页 - 基于5层架构的产品介绍页
 */
export default function Home() {
  const { isDebug, pricing, features, isLoaded } = useModeStore();
  const { isLoggedIn, user } = useAuthStore();
  const [expandedLayer, setExpandedLayer] = useState<number | null>(null);

  return (
    <div className="max-w-6xl mx-auto">
      {/* ============================================ */}
      {/* Section 1: Hero Section                     */}
      {/* ============================================ */}
      <section className="text-center py-12 md:py-20 relative overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-purple-50 to-blue-50 opacity-50 -z-10" />

        <div className="flex justify-center mb-4">
          <ModeIndicator />
        </div>

        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-6">
          AcademicGuard
        </h1>

        <div className="mb-4">
          <h2 className="text-2xl md:text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-purple-600 mb-2">
            5层架构,从骨到皮的De-AIGC引擎
          </h2>
          <p className="text-lg md:text-xl text-gray-600">
            5-Layer Architecture: Bone-to-Skin De-AIGC Engine
          </p>
        </div>

        <p className="text-base md:text-lg text-gray-600 mb-2 max-w-3xl mx-auto">
          市面<span className="font-bold text-primary-600">唯一</span>支持
          <span className="font-bold"> 文档→章节→段落→句子→词汇 </span>
          全颗粒度分析的学术论文AIGC检测与人源化协作引擎
        </p>
        <p className="text-sm md:text-base text-gray-500 mb-8 max-w-3xl mx-auto">
          The <span className="font-bold">ONLY</span> Academic Paper AIGC Detection & Humanization Engine Supporting
          Full-Granularity Analysis: Document → Section → Paragraph → Sentence → Lexical
        </p>

        {/* Pricing badge for operational mode */}
        {isLoaded && features.showPricing && !isDebug && (
          <div className="flex justify-center mb-6">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-full shadow-sm">
              <Calculator className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-gray-700">
                定价：<span className="font-bold text-blue-600">¥{pricing.pricePerUnit}</span> / 100词
              </span>
              <span className="text-xs text-gray-500">
                (最低 ¥{pricing.minimumCharge})
              </span>
            </div>
          </div>
        )}

        {/* User status for operational mode */}
        {isLoaded && !isDebug && (
          <div className="flex justify-center mb-6">
            {isLoggedIn && user ? (
              <span className="text-sm text-gray-600">
                欢迎回来, <span className="font-medium">{user.nickname || user.phone || '用户'}</span>
              </span>
            ) : (
              <span className="text-sm text-gray-500">
                使用前需要登录 | Login required
              </span>
            )}
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/upload">
            <Button variant="primary" size="lg" className="shadow-lg hover:shadow-xl transition-shadow">
              <FileText className="w-5 h-5 mr-2" />
              开始使用
            </Button>
          </Link>
          <a href="#architecture">
            <Button variant="outline" size="lg">
              了解5层架构
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </a>
        </div>
      </section>

      {/* ============================================ */}
      {/* Section 2: 5-Layer Architecture             */}
      {/* ============================================ */}
      <section id="architecture" className="py-12 bg-white">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">
            5层架构可视化
          </h2>
          <p className="text-lg text-gray-600 mb-1">
            5-Layer Architecture Visualization
          </p>
          <p className="text-sm text-gray-500 max-w-2xl mx-auto">
            从粗到细的颗粒度分析,必须按 Layer 5 → 4 → 3 → 2 → 1 顺序处理
          </p>
        </div>

        <div className="max-w-4xl mx-auto space-y-3">
          {/* Layer 5 */}
          <LayerCard
            layerNum={5}
            title="文档层"
            titleEn="Document Level"
            icon={<FileText className="w-6 h-6" />}
            iconColor="text-blue-600"
            iconBg="bg-blue-100"
            description="全文结构、段落长度、连接词、内容实质性"
            subSteps={[
              { num: "1.0", name: "词汇锁定", nameEn: "Term Locking", required: true },
              { num: "1.1", name: "结构框架检测", nameEn: "Structure Framework" },
              { num: "1.2", name: "段落长度规律性", nameEn: "Paragraph Length" },
              { num: "1.3", name: "推进模式与闭合", nameEn: "Progression & Closure" },
              { num: "1.4", name: "连接词与衔接", nameEn: "Connectors & Transitions" },
              { num: "1.5", name: "内容实质性", nameEn: "Content Substantiveness" },
            ]}
            expanded={expandedLayer === 5}
            onToggle={() => setExpandedLayer(expandedLayer === 5 ? null : 5)}
          />

          {/* Layer 4 */}
          <LayerCard
            layerNum={4}
            title="章节层"
            titleEn="Section Level"
            icon={<Layout className="w-6 h-6" />}
            iconColor="text-purple-600"
            iconBg="bg-purple-100"
            description="章节顺序、长度分布、相似性、过渡、逻辑"
            subSteps={[
              { num: "2.0", name: "章节识别", nameEn: "Section Identification" },
              { num: "2.1", name: "章节顺序", nameEn: "Section Order" },
              { num: "2.2", name: "长度分布", nameEn: "Length Distribution" },
              { num: "2.3", name: "章节相似性", nameEn: "Section Similarity" },
              { num: "2.4", name: "章节过渡", nameEn: "Section Transition" },
              { num: "2.5", name: "章节逻辑", nameEn: "Section Logic" },
            ]}
            expanded={expandedLayer === 4}
            onToggle={() => setExpandedLayer(expandedLayer === 4 ? null : 4)}
          />

          {/* Layer 3 */}
          <LayerCard
            layerNum={3}
            title="段落层"
            titleEn="Paragraph Level"
            icon={<AlignJustify className="w-6 h-6" />}
            iconColor="text-green-600"
            iconBg="bg-green-100"
            description="段落角色、连贯性、锚点密度、句长分布、过渡"
            subSteps={[
              { num: "3.0", name: "段落识别", nameEn: "Paragraph Identification" },
              { num: "3.1", name: "段落角色", nameEn: "Paragraph Role" },
              { num: "3.2", name: "内部连贯性", nameEn: "Internal Coherence" },
              { num: "3.3", name: "锚点密度", nameEn: "Anchor Density" },
              { num: "3.4", name: "句长分布", nameEn: "Sentence Length" },
              { num: "3.5", name: "段落过渡", nameEn: "Paragraph Transition" },
            ]}
            expanded={expandedLayer === 3}
            onToggle={() => setExpandedLayer(expandedLayer === 3 ? null : 3)}
          />

          {/* Layer 2 */}
          <LayerCard
            layerNum={2}
            title="句子层"
            titleEn="Sentence Level"
            icon={<Type className="w-6 h-6" />}
            iconColor="text-amber-600"
            iconBg="bg-amber-100"
            description="句式分析、句长规划、合并拆分、连接词、多样化改写"
            subSteps={[
              { num: "4.0", name: "句子识别", nameEn: "Sentence Identification" },
              { num: "4.1", name: "句式结构分析", nameEn: "Pattern Analysis" },
              { num: "4.2", name: "句长分析", nameEn: "Length Analysis" },
              { num: "4.3", name: "句子合并", nameEn: "Sentence Merger" },
              { num: "4.4", name: "连接词优化", nameEn: "Connector Optimization" },
              { num: "4.5", name: "多样化改写", nameEn: "Diversification" },
            ]}
            expanded={expandedLayer === 2}
            onToggle={() => setExpandedLayer(expandedLayer === 2 ? null : 2)}
          />

          {/* Layer 1 */}
          <LayerCard
            layerNum={1}
            title="词汇层"
            titleEn="Lexical Level"
            icon={<Hash className="w-6 h-6" />}
            iconColor="text-red-600"
            iconBg="bg-red-100"
            description="AIGC指纹检测、人类特征分析、替换候选、LLM改写、验证"
            subSteps={[
              { num: "5.0", name: "词汇环境准备", nameEn: "Context Preparation" },
              { num: "5.1", name: "AIGC指纹检测", nameEn: "Fingerprint Detection" },
              { num: "5.2", name: "人类特征分析", nameEn: "Human Features" },
              { num: "5.3", name: "替换候选生成", nameEn: "Replacement Candidates" },
              { num: "5.4", name: "LLM段落改写", nameEn: "LLM Rewriting" },
              { num: "5.5", name: "改写结果验证", nameEn: "Validation" },
            ]}
            expanded={expandedLayer === 1}
            onToggle={() => setExpandedLayer(expandedLayer === 1 ? null : 1)}
          />
        </div>

        <div className="mt-8 text-center">
          <p className="text-sm text-gray-600 max-w-2xl mx-auto">
            <span className="font-bold text-primary-600">为什么需要5层架构?</span>
            如果先改句子再调结构,结构调整可能导致句子级修改失效。
            必须按从粗到细的顺序处理,就像装修房子要先看整体布局再调整细节。
          </p>
        </div>
      </section>

      {/* ============================================ */}
      {/* Section 3: 3 Core Technologies              */}
      {/* ============================================ */}
      <section className="py-12 bg-gray-50">
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-3">
          3大核心技术
        </h2>
        <p className="text-lg text-gray-600 text-center mb-10">
          3 Core Technologies
        </p>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Technology 1: CAASS v2.0 */}
          <TechnologyCard
            icon={<Target className="w-8 h-8" />}
            iconColor="text-blue-600"
            iconBg="bg-blue-100"
            title="CAASS v2.0 评分系统"
            titleEn="CAASS v2.0 Scoring System"
            subtitle="Context-Aware Adaptive Scoring"
            description="上下文感知的动态风险评分系统,综合困惑度、指纹词、突发性等多维度指标,生成0-100的综合风险分数"
            metrics={[
              "PPL 困惑度",
              "指纹词密度",
              "突发性分析",
              "结构可预测性"
            ]}
          />

          {/* Technology 2: 18-Point De-AIGC */}
          <TechnologyCard
            icon={<Brain className="w-8 h-8" />}
            iconColor="text-purple-600"
            iconBg="bg-purple-100"
            title="18点 De-AIGC 技术"
            titleEn="18-Point De-AIGC Techniques"
            subtitle="Advanced Rewriting Strategies"
            description="基于学术论文特性设计的18种改写策略,覆盖术语保护、句式多样性、长句保护、逻辑框架重排等"
            metrics={[
              "#13 句式多样性",
              "#14 长句保护",
              "#15 逻辑框架重排",
              "#16 嵌套从句生成"
            ]}
          />

          {/* Technology 3: Term Locking */}
          <TechnologyCard
            icon={<Lock className="w-8 h-8" />}
            iconColor="text-green-600"
            iconBg="bg-green-100"
            title="词汇锁定系统"
            titleEn="Intelligent Term Locking"
            subtitle="Step 1.0 - Must Execute First"
            description="LLM自动提取专业术语、专有名词、缩写词,用户确认后自动注入到所有后续LLM调用的Prompt中,确保专业性不受影响"
            metrics={[
              "专业术语锁定",
              "专有名词保护",
              "引用格式保留",
              "跨层全程传递"
            ]}
          />
        </div>
      </section>

      {/* ============================================ */}
      {/* Section 4: Why 5-Layer Architecture?        */}
      {/* ============================================ */}
      <section className="py-12">
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-3">
          为何与众不同?
        </h2>
        <p className="text-lg text-gray-600 text-center mb-10">
          Why AcademicGuard is Different
        </p>

        <div className="max-w-5xl mx-auto">
          <ComparisonTable />
        </div>

        <div className="mt-10 max-w-4xl mx-auto">
          <div className="bg-gradient-to-r from-primary-50 to-purple-50 rounded-2xl p-8 border border-primary-100">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <Shield className="w-6 h-6 text-primary-600 mr-2" />
              直击 Turnitin & GPTZero 核心算法
            </h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-bold text-gray-800 mb-2">检测器原理</h4>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start">
                    <span className="text-primary-600 mr-2">•</span>
                    <span><strong>Perplexity</strong>: AI文本过于平滑(PPL &lt; 20)</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-primary-600 mr-2">•</span>
                    <span><strong>Burstiness</strong>: AI句长过于均匀(CV &lt; 0.25)</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-primary-600 mr-2">•</span>
                    <span><strong>Structure</strong>: AI结构过于规整</span>
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="font-bold text-gray-800 mb-2">我们的应对</h4>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start">
                    <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Layer 2句子合并拆分 → 提升Burstiness</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Layer 1词汇多样化 → 提升PPL</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Layer 5结构重组 → 打破AI模式</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================ */}
      {/* Section 5: How It Works                     */}
      {/* ============================================ */}
      <section className="py-12 bg-gray-50">
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-3">
          工作流程
        </h2>
        <p className="text-lg text-gray-600 text-center mb-10">
          Complete Processing Flow
        </p>

        <div className="max-w-3xl mx-auto">
          <div className="space-y-4">
            <FlowStep num={1} title="上传文档" titleEn="Upload Document" />
            <FlowStep num={2} title="Step 1.0 词汇锁定" titleEn="Term Locking" highlight />
            <FlowStep num={3} title="Layer 5 文档层分析" titleEn="Document Analysis" />
            <FlowStep num={4} title="Layer 4 章节层分析" titleEn="Section Analysis" />
            <FlowStep num={5} title="Layer 3 段落层分析" titleEn="Paragraph Analysis" />
            <FlowStep num={6} title="Layer 2 句子层改写" titleEn="Sentence Rewriting" />
            <FlowStep num={7} title="Layer 1 词汇层精修" titleEn="Lexical Polishing" />
            <FlowStep num={8} title="导出优化文档" titleEn="Export Result" />
          </div>
        </div>
      </section>

      {/* ============================================ */}
      {/* Section 6: Dual Mode Comparison             */}
      {/* ============================================ */}
      <section className="py-12">
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-3">
          双模式处理
        </h2>
        <p className="text-lg text-gray-600 text-center mb-10">
          Intervention Mode vs YOLO Mode
        </p>

        <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto">
          <ModeCard
            icon={<Zap className="w-8 h-8" />}
            iconColor="text-amber-600"
            iconBg="bg-amber-100"
            title="干预模式"
            titleEn="Intervention Mode"
            features={[
              "逐层手动选择方案",
              "完全控制每一步",
              "适合重要论文",
              "学习AIGC特征"
            ]}
            recommended="首次使用推荐"
          />
          <ModeCard
            icon={<Zap className="w-8 h-8" />}
            iconColor="text-blue-600"
            iconBg="bg-blue-100"
            title="YOLO模式"
            titleEn="Auto Mode"
            features={[
              "全自动处理L5→L1",
              "最后统一审核",
              "适合快速处理",
              "提高处理效率"
            ]}
            recommended="截稿临近推荐"
          />
        </div>
      </section>

      {/* ============================================ */}
      {/* Section 7: Benefits                         */}
      {/* ============================================ */}
      <section className="py-12 bg-white">
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-10">
          核心优势
        </h2>

        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          <BenefitItem text="透明的检测逻辑,每个问题都有明确的依据和理由" />
          <BenefitItem text="智能术语锁定,确保学术专业性不受影响" />
          <BenefitItem text="语义相似度验证≥85%,保证内容意义不变" />
          <BenefitItem text="0-10级口语化控制,适应不同场景需求" />
          <BenefitItem text="中英双语支持,降低ESL用户理解门槛" />
          <BenefitItem text="完全用户控制,支持自定义修改" />
        </div>

        <div className="mt-8 max-w-3xl mx-auto">
          <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6 border border-green-100">
            <h3 className="font-bold text-gray-900 mb-3 flex items-center">
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
              质量承诺
            </h3>
            <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-700">
              <div>
                <p className="font-medium mb-1">我们承诺:</p>
                <ul className="space-y-1">
                  <li>• 语义相似度 ≥ 85%</li>
                  <li>• 术语完整性 100%</li>
                  <li>• 高风险转低风险率 ≥ 80%</li>
                </ul>
              </div>
              <div>
                <p className="font-medium mb-1">诚实告知:</p>
                <ul className="space-y-1">
                  <li>• 不保证100%通过所有检测器</li>
                  <li>• 建议最终人工审核</li>
                  <li>• 检测器算法会持续更新</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================ */}
      {/* Section 8: FAQ                              */}
      {/* ============================================ */}
      <section className="py-12 bg-gray-50">
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-10">
          常见问题
        </h2>

        <div className="max-w-4xl mx-auto space-y-4">
          <FAQItem
            question="为什么必须先做词汇锁定(Step 1.0)?"
            answer="锁定的专业术语会自动传递到所有后续LLM调用的Prompt中,确保改写时不会误改专业词汇。如果先改写再锁定,已经改过的内容可能包含错误替换。"
          />
          <FAQItem
            question="5层架构和传统工具有何区别?"
            answer="传统工具只在句子级做同义词替换,无法改变文章的结构特征。5层架构从文档→词汇逐层优化,能从根本上改变AI文本的特征模式。"
          />
          <FAQItem
            question="使用YOLO模式安全吗?"
            answer="YOLO模式会自动选择最优建议,但仍建议最后人工审核。重要论文建议使用干预模式,逐层确认修改。"
          />
          <FAQItem
            question="支持中文论文吗?"
            answer="目前仅支持英文学术论文。中文论文的AIGC检测逻辑不同,暂不支持。"
          />
        </div>

        <div className="mt-8 text-center">
          <a href="/doc/investor_presentation.md" className="inline-flex items-center text-primary-600 hover:text-primary-700">
            <Download className="w-4 h-4 mr-2" />
            下载技术白皮书
          </a>
        </div>
      </section>

      {/* ============================================ */}
      {/* Section 9: Final CTA                        */}
      {/* ============================================ */}
      <section className="py-12">
        <div className="card p-8 md:p-12 bg-gradient-to-br from-primary-50 via-purple-50 to-blue-50 border-2 border-primary-100">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              准备好体验5层架构的强大威力了吗?
            </h2>
            <p className="text-gray-600 mb-8">
              {isDebug ? (
                <>完全免费使用,无限制处理</>
              ) : (
                <>首次使用赠送100词免费额度 • 定价: ¥{pricing.pricePerUnit}/100词</>
              )}
            </p>
            <Link to="/upload">
              <Button variant="primary" size="lg" className="shadow-lg hover:shadow-xl">
                {isDebug ? '开始免费使用' : '立即注册开始'}
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <div className="mt-6 flex justify-center gap-6 text-sm text-gray-600">
              <a href="#architecture" className="hover:text-primary-600">
                <HelpCircle className="w-4 h-4 inline mr-1" />
                了解更多
              </a>
              <a href="https://github.com/yourorg/academicguard" className="hover:text-primary-600" target="_blank" rel="noopener noreferrer">
                <Play className="w-4 h-4 inline mr-1" />
                查看Demo
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

/**
 * LayerCard Component - Interactive 5-layer architecture card
 * 5层架构卡片组件 - 可展开显示子步骤
 */
function LayerCard({
  layerNum,
  title,
  titleEn,
  icon,
  iconColor,
  iconBg,
  description,
  subSteps,
  expanded,
  onToggle,
}: {
  layerNum: number;
  title: string;
  titleEn: string;
  icon: React.ReactNode;
  iconColor: string;
  iconBg: string;
  description: string;
  subSteps: Array<{ num: string; name: string; nameEn: string; required?: boolean }>;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="bg-white rounded-xl border-2 border-gray-200 hover:border-primary-300 transition-all overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full p-5 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-4 flex-1">
          <div className={`w-14 h-14 rounded-lg ${iconBg} ${iconColor} flex items-center justify-center flex-shrink-0`}>
            {icon}
          </div>
          <div className="text-left flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-bold text-gray-500">Layer {layerNum}</span>
              <h3 className="text-xl font-bold text-gray-900">{title}</h3>
              <span className="text-sm text-gray-500">{titleEn}</span>
            </div>
            <p className="text-sm text-gray-600">{description}</p>
          </div>
        </div>
        <div className="ml-4">
          {expanded ? (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronRight className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-5 bg-gray-50 border-t border-gray-200">
          <div className="grid md:grid-cols-2 gap-3 mt-4">
            {subSteps.map((step, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg ${step.required ? 'bg-amber-50 border-2 border-amber-200' : 'bg-white border border-gray-200'}`}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-bold ${step.required ? 'text-amber-600' : 'text-gray-500'}`}>
                    Step {step.num}
                  </span>
                  {step.required && (
                    <span className="text-xs font-bold text-amber-600">⭐ 必须首先完成</span>
                  )}
                </div>
                <p className="text-sm font-medium text-gray-900 mt-1">{step.name}</p>
                <p className="text-xs text-gray-500">{step.nameEn}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * TechnologyCard Component - Core technology showcase card
 * 核心技术展示卡片组件
 */
function TechnologyCard({
  icon,
  iconColor,
  iconBg,
  title,
  titleEn,
  subtitle,
  description,
  metrics,
}: {
  icon: React.ReactNode;
  iconColor: string;
  iconBg: string;
  title: string;
  titleEn: string;
  subtitle: string;
  description: string;
  metrics: string[];
}) {
  return (
    <div className="card p-6 hover:shadow-xl transition-shadow h-full">
      <div className={`w-16 h-16 rounded-xl ${iconBg} ${iconColor} flex items-center justify-center mb-4`}>
        {icon}
      </div>
      <h3 className="text-lg font-bold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 mb-1">{titleEn}</p>
      <p className="text-xs font-medium text-primary-600 mb-3">{subtitle}</p>
      <p className="text-sm text-gray-600 mb-4 leading-relaxed">{description}</p>
      <div className="space-y-2">
        {metrics.map((metric, idx) => (
          <div key={idx} className="flex items-center text-xs text-gray-700">
            <div className={`w-1.5 h-1.5 rounded-full ${iconBg} mr-2`} />
            {metric}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * ComparisonTable Component - Feature comparison table
 * 功能对比表组件
 */
function ComparisonTable() {
  const comparisons = [
    { dimension: '分析颗粒度', traditional: '仅句子级', ours: '5层 (文档→词汇)' },
    { dimension: '术语保护', traditional: '✗ 无', ours: '✓ 智能锁定' },
    { dimension: '检测原理', traditional: '简单规则', ours: 'CAASS v2.0' },
    { dimension: '改写策略', traditional: '同义词替换', ours: '18点技术' },
    { dimension: '用户控制', traditional: '黑盒自动', ours: '人机协作' },
    { dimension: '语义验证', traditional: '✗ 无', ours: '✓ BERT验证' },
  ];

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-100">
            <th className="p-4 text-left font-bold text-gray-700 border-b-2 border-gray-300">维度</th>
            <th className="p-4 text-left font-bold text-gray-700 border-b-2 border-gray-300">传统工具</th>
            <th className="p-4 text-left font-bold text-primary-600 border-b-2 border-primary-300 bg-primary-50">
              AcademicGuard
            </th>
          </tr>
        </thead>
        <tbody>
          {comparisons.map((row, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              <td className="p-4 border-b border-gray-200 font-medium text-gray-900">{row.dimension}</td>
              <td className="p-4 border-b border-gray-200 text-gray-600">{row.traditional}</td>
              <td className="p-4 border-b border-gray-200 font-medium text-primary-700 bg-primary-50/50">
                {row.ours}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * FlowStep Component - Processing flow step indicator
 * 流程步骤指示器组件
 */
function FlowStep({
  num,
  title,
  titleEn,
  highlight = false,
}: {
  num: number;
  title: string;
  titleEn: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-center gap-4">
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white flex-shrink-0 ${
          highlight ? 'bg-amber-600' : 'bg-primary-600'
        }`}
      >
        {num}
      </div>
      <div className={`flex-1 p-3 rounded-lg ${highlight ? 'bg-amber-50 border-2 border-amber-200' : 'bg-white border border-gray-200'}`}>
        <p className="font-medium text-gray-900">{title}</p>
        <p className="text-sm text-gray-500">{titleEn}</p>
      </div>
    </div>
  );
}

/**
 * ModeCard Component - Processing mode feature card
 * 处理模式特性卡片组件
 */
function ModeCard({
  icon,
  iconColor,
  iconBg,
  title,
  titleEn,
  features,
  recommended,
}: {
  icon: React.ReactNode;
  iconColor: string;
  iconBg: string;
  title: string;
  titleEn: string;
  features: string[];
  recommended: string;
}) {
  return (
    <div className="card p-6 hover:shadow-lg transition-shadow relative">
      <div className="absolute top-4 right-4">
        <span className="text-xs font-bold text-primary-600 bg-primary-50 px-2 py-1 rounded">
          {recommended}
        </span>
      </div>
      <div className={`w-14 h-14 rounded-xl ${iconBg} ${iconColor} flex items-center justify-center mb-4`}>
        {icon}
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 mb-4">{titleEn}</p>
      <ul className="space-y-2">
        {features.map((feature, idx) => (
          <li key={idx} className="flex items-start text-sm text-gray-700">
            <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
            {feature}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * BenefitItem Component - Benefit list item with checkmark
 * 优势列表项组件
 */
function BenefitItem({ text }: { text: string }) {
  return (
    <div className="flex items-start">
      <CheckCircle className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
      <span className="text-gray-700">{text}</span>
    </div>
  );
}

/**
 * FAQItem Component - Collapsible FAQ item
 * 可折叠FAQ项组件
 */
function FAQItem({ question, answer }: { question: string; answer: string }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <HelpCircle className="w-5 h-5 text-primary-600 flex-shrink-0" />
          <span className="font-medium text-gray-900">{question}</span>
        </div>
        {isOpen ? (
          <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
        )}
      </button>
      {isOpen && (
        <div className="px-4 pb-4 text-sm text-gray-600 leading-relaxed border-t border-gray-100 pt-3">
          {answer}
        </div>
      )}
    </div>
  );
}
