import { Link } from 'react-router-dom';
import { FileText, Zap, Shield, Users, ArrowRight, CheckCircle, Fingerprint, Activity, Link2, Calculator } from 'lucide-react';
import Button from '../components/common/Button';
import ModeIndicator from '../components/auth/ModeIndicator';
import { useModeStore } from '../stores/modeStore';
import { useAuthStore } from '../stores/authStore';

/**
 * Home page - Landing page with product introduction
 * 首页 - 产品介绍和快速入口
 */
export default function Home() {
  const { isDebug, pricing, features, isLoaded } = useModeStore();
  const { isLoggedIn, user } = useAuthStore();

  return (
    <div className="max-w-6xl mx-auto">
      {/* Hero Section */}
      <section className="text-center py-12 md:py-20">
        <div className="flex justify-center mb-4">
          <ModeIndicator />
        </div>
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
          AcademicGuard
        </h1>
        <p className="text-xl md:text-2xl text-gray-600 mb-4">
          English Paper AIGC Detection & Humanization Engine
        </p>
        <p className="text-lg text-gray-500 mb-8 max-w-2xl mx-auto">
          智能协作，掌控自如 — 人机协作式AIGC文本优化
        </p>

        {/* Pricing badge for operational mode */}
        {/* 运营模式下显示价格徽章 */}
        {isLoaded && features.showPricing && !isDebug && (
          <div className="flex justify-center mb-6">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-full">
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
        {/* 运营模式下显示用户状态 */}
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
            <Button variant="primary" size="lg">
              <FileText className="w-5 h-5 mr-2" />
              开始使用
            </Button>
          </Link>
          <a href="#features">
            <Button variant="outline" size="lg">
              了解更多
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </a>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-12">
        <h2 className="text-2xl font-bold text-gray-800 text-center mb-8">
          核心特性 / Core Features
        </h2>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Feature 1: Dual Mode */}
          <FeatureCard
            icon={<Zap className="w-8 h-8" />}
            iconColor="text-amber-600"
            iconBg="bg-amber-100"
            title="双模式处理"
            titleEn="Dual Mode Processing"
            description="YOLO模式快速自动处理，干预模式逐句精细控制"
          />

          {/* Feature 2: Dual Track */}
          <FeatureCard
            icon={<Users className="w-8 h-8" />}
            iconColor="text-purple-600"
            iconBg="bg-purple-100"
            title="双轨建议"
            titleEn="Dual Track Suggestions"
            description="LLM智能改写 + 规则建议，用户自主选择或自定义"
          />

          {/* Feature 3: Multi-detector */}
          <FeatureCard
            icon={<Shield className="w-8 h-8" />}
            iconColor="text-blue-600"
            iconBg="bg-blue-100"
            title="多检测器视角"
            titleEn="Multi-Detector Views"
            description="模拟Turnitin和GPTZero的检测逻辑，精准定位问题"
          />
        </div>
      </section>

      {/* Unique Logic Section - Why we are different */}
      <section className="py-12">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-800 text-center mb-8">
            为何我们与众不同？
            <br />
            <span className="text-lg font-normal text-gray-500">The Unique Logic Behind AcademicGuard</span>
          </h2>
          
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-8 md:p-10">
              <div className="flex flex-col md:flex-row gap-8">
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                    <Shield className="w-6 h-6 text-primary-600 mr-2" />
                    直击 Turnitin & GPTZero 核心算法
                  </h3>
                  <div className="space-y-4 text-gray-600">
                    <p>
                      目前的顶级检测器（如 <strong>Turnitin</strong> 和 <strong>GPTZero</strong>）并不仅靠"查重"，而是通过计算文本的 
                      <span className="text-indigo-600 font-medium"> 困惑度 (Perplexity) </span> 和 
                      <span className="text-indigo-600 font-medium"> 节奏变化度 (Burstiness) </span> 来判定是否为 AI 生成。
                    </p>
                    <p>
                      AI 生成的文本通常逻辑平顺、结构单一（低困惑度、低节奏变化度）。市面上的大多数工具仅仅是进行同义词替换，无法改变文章底层的逻辑结构特征，因此往往无法通过严格的检测。
                    </p>
                  </div>
                </div>
                
                <div className="flex-1 bg-gray-50 rounded-xl p-6 border border-gray-100">
                  <h3 className="text-lg font-bold text-gray-900 mb-4">
                    AcademicGuard 的独家方案
                  </h3>
                  <p className="text-gray-600 mb-4 text-sm">
                    我们是市面上<span className="text-red-600 font-bold">唯一</span>引入"结构化节奏变化度"分析的工具：
                  </p>
                  <ul className="space-y-3">
                    <li className="flex items-start text-sm text-gray-700">
                      <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5" />
                      <span><strong>精准降噪：</strong> 识别并打破 AI 固有的指纹句式</span>
                    </li>
                    <li className="flex items-start text-sm text-gray-700">
                      <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5" />
                      <span><strong>逻辑重构：</strong> 增强段落间的逻辑跳跃感（提升节奏变化度）</span>
                    </li>
                    <li className="flex items-start text-sm text-gray-700">
                      <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5" />
                      <span><strong>深度人机协作：</strong> 在保持学术严谨性的同时注入"人类特征"</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Analysis Dimensions Section */}
      <section className="py-12 bg-white">
        <div className="max-w-6xl mx-auto">
           <h2 className="text-2xl font-bold text-gray-800 text-center mb-8">
            全维度检测矩阵
            <br />
            <span className="text-lg font-normal text-gray-500">The 4-Dimensional Analysis Matrix</span>
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <DimensionCard 
              icon={<Activity className="w-6 h-6" />}
              title="语义复杂度"
              subTitle="Semantic Complexity"
              description="衡量文本的随机性。AI生成内容往往过于平滑、可预测，缺乏人类写作的复杂变化。"
              color="text-blue-600"
              bg="bg-blue-50"
            />
            <DimensionCard
              icon={<Zap className="w-6 h-6" />}
              title="节奏变化度"
              subTitle="Logical Burstiness"
              description="评估句式结构与长度的跳跃感。人类写作充满节奏变化，而AI倾向于单调重复。"
              color="text-amber-600"
              bg="bg-amber-50"
            />
            <DimensionCard 
              icon={<Fingerprint className="w-6 h-6" />}
              title="AI指纹特征"
              subTitle="AI Fingerprints"
              description="识别大模型（LLM）惯用的高频词组与句式模板，精准定位“合成感”来源。"
              color="text-purple-600"
              bg="bg-purple-50"
            />
            <DimensionCard 
              icon={<Link2 className="w-6 h-6" />}
              title="逻辑衔接力"
              subTitle="Cohesion Indicators"
              description="深度分析段落间的逻辑链条。区分简单的词汇堆砌与真实且深度的思维递进。"
              color="text-green-600"
              bg="bg-green-50"
            />
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-12 bg-gray-50 -mx-4 px-4 rounded-xl">
        <h2 className="text-2xl font-bold text-gray-800 text-center mb-8">
          工作流程 / How It Works
        </h2>

        <div className="grid md:grid-cols-4 gap-6 max-w-4xl mx-auto">
          <StepCard
            step={1}
            title="上传文档"
            titleEn="Upload"
            description="支持TXT、DOCX格式"
          />
          <StepCard
            step={2}
            title="AI分析"
            titleEn="Analysis"
            description="逐句检测AIGC特征"
          />
          <StepCard
            step={3}
            title="协作修改"
            titleEn="Collaborate"
            description="选择或自定义修改"
          />
          <StepCard
            step={4}
            title="导出结果"
            titleEn="Export"
            description="下载优化后的文档"
          />
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-12">
        <h2 className="text-2xl font-bold text-gray-800 text-center mb-8">
          为什么选择我们 / Why Choose Us
        </h2>

        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          <BenefitItem text="透明的检测逻辑，让你理解为什么需要修改" />
          <BenefitItem text="保留学术术语，确保专业性不受影响" />
          <BenefitItem text="语义相似度验证，保证内容意义不变" />
          <BenefitItem text="可调节口语化程度，适应不同场景需求" />
          <BenefitItem text="中英双语支持，降低理解门槛" />
          <BenefitItem text="支持自定义修改，最终决定权在你" />
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-12 text-center">
        <div className="card p-8 bg-gradient-to-r from-primary-50 to-purple-50">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            准备好开始了吗？
          </h2>
          <p className="text-gray-600 mb-6">
            上传你的文档，体验人机协作的AIGC优化之旅
          </p>
          <Link to="/upload">
            <Button variant="primary" size="lg">
              立即开始
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}

// Feature card sub-component
// 特性卡片子组件
function FeatureCard({
  icon,
  iconColor,
  iconBg,
  title,
  titleEn,
  description,
}: {
  icon: React.ReactNode;
  iconColor: string;
  iconBg: string;
  title: string;
  titleEn: string;
  description: string;
}) {
  return (
    <div className="card p-6 hover:shadow-lg transition-shadow">
      <div className={`w-16 h-16 rounded-xl ${iconBg} ${iconColor} flex items-center justify-center mb-4`}>
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-gray-800 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 mb-2">{titleEn}</p>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

// Step card sub-component
// 步骤卡片子组件
function StepCard({
  step,
  title,
  titleEn,
  description,
}: {
  step: number;
  title: string;
  titleEn: string;
  description: string;
}) {
  return (
    <div className="text-center">
      <div className="w-12 h-12 rounded-full bg-primary-600 text-white flex items-center justify-center text-xl font-bold mx-auto mb-3">
        {step}
      </div>
      <h3 className="font-semibold text-gray-800">{title}</h3>
      <p className="text-xs text-gray-500 mb-1">{titleEn}</p>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  );
}

// Benefit item sub-component
// 优势项子组件
function BenefitItem({ text }: { text: string }) {
  return (
    <div className="flex items-start">
      <CheckCircle className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
      <span className="text-gray-700">{text}</span>
    </div>
  );
}

// Dimension card sub-component
// 分析维度卡片子组件
function DimensionCard({
  icon,
  title,
  subTitle,
  description,
  color,
  bg,
}: {
  icon: React.ReactNode;
  title: string;
  subTitle: string;
  description: string;
  color: string;
  bg: string;
}) {
  return (
    <div className="bg-gray-50 rounded-xl p-6 border border-gray-100 hover:shadow-md transition-shadow">
      <div className={`w-12 h-12 rounded-lg ${bg} ${color} flex items-center justify-center mb-4`}>
        {icon}
      </div>
      <h3 className="text-lg font-bold text-gray-900 mb-1">{title}</h3>
      <p className="text-xs font-medium text-gray-500 mb-3 uppercase tracking-wider">{subTitle}</p>
      <p className="text-sm text-gray-600 leading-relaxed">{description}</p>
    </div>
  );
}
