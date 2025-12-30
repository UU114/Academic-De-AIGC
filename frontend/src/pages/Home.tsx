import { Link } from 'react-router-dom';
import { FileText, Zap, Shield, Users, ArrowRight, CheckCircle } from 'lucide-react';
import Button from '../components/common/Button';

/**
 * Home page - Landing page with product introduction
 * 首页 - 产品介绍和快速入口
 */
export default function Home() {
  return (
    <div className="max-w-6xl mx-auto">
      {/* Hero Section */}
      <section className="text-center py-12 md:py-20">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
          AcademicGuard
        </h1>
        <p className="text-xl md:text-2xl text-gray-600 mb-4">
          English Paper AIGC Detection & Humanization Engine
        </p>
        <p className="text-lg text-gray-500 mb-8 max-w-2xl mx-auto">
          AI教你改，而非AI替你改 - 人机协作式AIGC文本优化
        </p>

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
