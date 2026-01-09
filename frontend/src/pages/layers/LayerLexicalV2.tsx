import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Type,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Fingerprint,
  User,
  Replace,
  Wand2,
  ShieldCheck,
  Play,
  Loader2,
  Cpu,
  Brain,
  Activity,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../../components/common/Button';
import LoadingMessage from '../../components/common/LoadingMessage';
import { documentApi, sessionApi } from '../../services/api';

// API base URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Layer Lexical V2 (Layer 1) - Enhanced Lexical Analysis & Rewriting
 * 词汇层V2（第1层）- 增强的词汇分析与改写
 *
 * Steps:
 * - Step 5.0: Context Preparation (上下文准备)
 * - Step 5.1: AIGC Fingerprint Detection (AIGC指纹检测)
 * - Step 5.2: Human Feature Analysis (人类特征分析)
 * - Step 5.3: Replacement Candidate Generation (替换候选生成)
 * - Step 5.4: LLM Paragraph Rewriting (LLM段落改写)
 * - Step 5.5: Result Validation (结果验证)
 */

interface StepResult {
  name: string;
  name_zh: string;
  summary: Record<string, unknown>;
}

interface PipelineResult {
  success: boolean;
  pipeline: string;
  steps: Record<string, StepResult>;
  final_document: string;
  final_paragraphs: Array<{
    index: number;
    original: string;
    rewritten: string;
    changes: Array<{
      original: string;
      replacement: string;
      reason: string;
    }>;
  }>;
  overall_metrics: {
    original_fingerprints: number;
    original_risk: number;
    original_human_score: number;
    paragraphs_rewritten: number;
    total_changes: number;
    aigc_removed: number;
    human_features_added: number;
  };
}

// PPL Paragraph Analysis for per-paragraph PPL display
// PPL段落分析用于显示每段的PPL
interface PPLParagraphInfo {
  index: number;
  ppl: number;
  risk_level: string;
  word_count: number;
  preview: string;
}

// PPL Analysis Result from backend
// 后端返回的PPL分析结果
interface PPLAnalysis {
  ppl_score: number | null;
  ppl_risk_level: string | null;
  used_onnx: boolean;
  paragraphs: PPLParagraphInfo[];
  high_risk_paragraphs: number[];
  available: boolean;
  model_info?: Record<string, unknown>;
  reason?: string;
}

interface AnalysisResult {
  success: boolean;
  fingerprints: {
    total_fingerprints: number;
    type_a_count: number;
    type_b_count: number;
    phrase_count: number;
    overall_density: number;
    risk_level: string;
    type_a_words: string[];
    type_b_words: string[];
    recommendations: string[];
    recommendations_zh: string[];
    // PPL Analysis fields (integrated from core/analyzer/ppl_calculator.py)
    // PPL分析字段（从 core/analyzer/ppl_calculator.py 集成）
    ppl_score?: number | null;
    ppl_risk_level?: string | null;
    ppl_used_onnx?: boolean;
    ppl_analysis?: PPLAnalysis;
  };
  human_features: {
    overall_human_score: number;
    verb_coverage: { rate: number; target: number; is_sufficient: boolean };
    adjective_coverage: { rate: number; target: number; is_sufficient: boolean };
    hedging_coverage: { rate: number; target: number; is_sufficient: boolean };
    recommendations: string[];
    recommendations_zh: string[];
  };
  candidates: {
    total_replaceable: number;
    type_a_candidates: number;
    candidates: Array<{
      original: string;
      type: string;
      recommended: string;
      is_human_feature: boolean;
    }>;
  };
  overall: {
    aigc_risk_score: number;
    aigc_risk_level: string;
    human_score: number;
  };
}

interface LayerLexicalV2Props {
  documentIdProp?: string;
  onComplete?: (result: PipelineResult) => void;
  showNavigation?: boolean;
}

type CurrentStep = '5.0' | '5.1' | '5.2' | '5.3' | '5.4' | '5.5' | 'full';

export default function LayerLexicalV2({
  documentIdProp,
  onComplete,
  showNavigation = true,
}: LayerLexicalV2Props) {
  const { documentId: documentIdParam } = useParams<{ documentId: string }>();
  const documentId = documentIdProp || documentIdParam;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get('mode') || 'intervention';
  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (sessionId) {
      sessionApi.updateStep(sessionId, 'layer-lexical-v2').catch(console.error);
    }
  }, [sessionId]);

  // State
  const [documentText, setDocumentText] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<CurrentStep>('5.1');

  // Analysis results
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null);

  // UI state
  const [expandedParagraph, setExpandedParagraph] = useState<number | null>(null);
  const [isRunningPipeline, setIsRunningPipeline] = useState(false);

  const isAnalyzingRef = useRef(false);

  // Load document
  useEffect(() => {
    if (documentId) {
      loadDocumentText(documentId);
    }
  }, [documentId]);

  const loadDocumentText = async (docId: string) => {
    try {
      const doc = await documentApi.get(docId);
      if (doc.originalText) {
        setDocumentText(doc.originalText);
      } else {
        setError('Document text not found');
      }
    } catch (err) {
      console.error('Failed to load document:', err);
      setError('Failed to load document');
    }
  };

  // Run analysis on document load
  useEffect(() => {
    if (documentText && !isAnalyzingRef.current) {
      runAnalysis();
    }
  }, [documentText]);

  const runAnalysis = async () => {
    if (isAnalyzingRef.current || !documentText) return;
    isAnalyzingRef.current = true;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/v1/analysis/lexical-v2/analyze-only`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_text: documentText,
          session_id: sessionId,
          colloquialism_level: 4,
        }),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.status}`);
      }

      const result = await response.json();
      setAnalysisResult(result);
    } catch (err) {
      console.error('Analysis failed:', err);
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsLoading(false);
      isAnalyzingRef.current = false;
    }
  };

  const runFullPipeline = async () => {
    if (!documentText) return;

    setIsRunningPipeline(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/v1/analysis/lexical-v2/full-pipeline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_text: documentText,
          session_id: sessionId,
          colloquialism_level: 4,
          skip_validation: false,
        }),
      });

      if (!response.ok) {
        throw new Error(`Pipeline failed: ${response.status}`);
      }

      const result = await response.json();
      setPipelineResult(result);
      setCurrentStep('full');

      if (onComplete) {
        onComplete(result);
      }
    } catch (err) {
      console.error('Pipeline failed:', err);
      setError(err instanceof Error ? err.message : 'Pipeline failed');
    } finally {
      setIsRunningPipeline(false);
    }
  };

  const handleBack = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/layer-sentence/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

  const handleFinish = useCallback(() => {
    const sessionParam = sessionId ? `&session=${sessionId}` : '';
    navigate(`/flow/summary/${documentId}?mode=${mode}${sessionParam}`);
  }, [documentId, mode, sessionId, navigate]);

  const renderRiskBadge = (level: string) => (
    <span className={clsx(
      'px-2 py-1 rounded text-xs font-medium',
      level === 'critical' && 'bg-red-200 text-red-800',
      level === 'high' && 'bg-red-100 text-red-700',
      level === 'medium' && 'bg-yellow-100 text-yellow-700',
      level === 'low' && 'bg-green-100 text-green-700'
    )}>
      {level === 'critical' ? 'Critical' : level === 'high' ? 'High' : level === 'medium' ? 'Medium' : 'Low'}
    </span>
  );

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex items-center justify-center min-h-[50vh]">
          <LoadingMessage category="structure" size="lg" showEnglish={true} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex flex-col items-center justify-center min-h-[50vh]">
          <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
          <p className="text-red-600 text-lg mb-4">{error}</p>
          {showNavigation && (
            <Button variant="outline" onClick={handleBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="p-2 rounded-lg bg-pink-100 text-pink-600 mr-3">
              <Type className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Layer 1: 词汇层分析 V2
              </h1>
              <p className="text-gray-600 mt-1">
                Enhanced Lexical Analysis & Rewriting
              </p>
            </div>
          </div>
          {showNavigation && (
            <Button variant="outline" onClick={handleBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          )}
        </div>

        {/* Step tabs */}
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            onClick={() => setCurrentStep('5.1')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '5.1' ? 'bg-pink-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <Fingerprint className="w-4 h-4 mr-1" />
            5.1 Fingerprints
          </button>
          <button
            onClick={() => setCurrentStep('5.2')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '5.2' ? 'bg-pink-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <User className="w-4 h-4 mr-1" />
            5.2 Human Features
          </button>
          <button
            onClick={() => setCurrentStep('5.3')}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
              currentStep === '5.3' ? 'bg-pink-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <Replace className="w-4 h-4 mr-1" />
            5.3 Candidates
          </button>
          {pipelineResult && (
            <>
              <button
                onClick={() => setCurrentStep('5.4')}
                className={clsx(
                  'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
                  currentStep === '5.4' ? 'bg-pink-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >
                <Wand2 className="w-4 h-4 mr-1" />
                5.4 Rewrite
              </button>
              <button
                onClick={() => setCurrentStep('5.5')}
                className={clsx(
                  'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center',
                  currentStep === '5.5' ? 'bg-pink-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >
                <ShieldCheck className="w-4 h-4 mr-1" />
                5.5 Validate
              </button>
            </>
          )}
        </div>
      </div>

      {/* Analysis Results */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Overall Score Card */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-1">
                  Analysis Overview
                </h3>
                <p className="text-sm text-gray-500">
                  AIGC Risk + Human Feature Analysis
                </p>
              </div>
              <div className="text-right">
                <p className={clsx(
                  'text-4xl font-bold',
                  analysisResult.overall.aigc_risk_score <= 30 && 'text-green-600',
                  analysisResult.overall.aigc_risk_score > 30 && analysisResult.overall.aigc_risk_score <= 60 && 'text-yellow-600',
                  analysisResult.overall.aigc_risk_score > 60 && 'text-red-600'
                )}>
                  {analysisResult.overall.aigc_risk_score}
                </p>
                {renderRiskBadge(analysisResult.overall.aigc_risk_level)}
              </div>
            </div>

            <div className="mt-4 grid grid-cols-4 gap-4">
              <div className="p-3 bg-red-50 rounded-lg">
                <p className="text-2xl font-bold text-red-600">
                  {analysisResult.fingerprints.type_a_count}
                </p>
                <p className="text-sm text-gray-600">Type A</p>
              </div>
              <div className="p-3 bg-yellow-50 rounded-lg">
                <p className="text-2xl font-bold text-yellow-600">
                  {analysisResult.fingerprints.type_b_count}
                </p>
                <p className="text-sm text-gray-600">Type B</p>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">
                  {analysisResult.fingerprints.phrase_count}
                </p>
                <p className="text-sm text-gray-600">Phrases</p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">
                  {analysisResult.human_features.overall_human_score}
                </p>
                <p className="text-sm text-gray-600">Human Score</p>
              </div>
            </div>

            {/* Run Pipeline Button */}
            {!pipelineResult && (
              <div className="mt-6">
                <Button
                  onClick={runFullPipeline}
                  disabled={isRunningPipeline}
                  className="w-full"
                >
                  {isRunningPipeline ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Running De-AIGC Pipeline...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Run Full De-AIGC Pipeline
                    </>
                  )}
                </Button>
              </div>
            )}
          </div>

          {/* Step 5.1: Fingerprints */}
          {currentStep === '5.1' && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Fingerprint className="w-5 h-5 mr-2 text-pink-600" />
                AIGC Fingerprint Detection
              </h3>

              {analysisResult.fingerprints.type_a_words.length > 0 && (
                <div className="mb-4">
                  <h4 className="font-medium text-red-700 mb-2">
                    Type A: Dead Giveaways (Must Remove)
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {analysisResult.fingerprints.type_a_words.map((word, idx) => (
                      <span key={idx} className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">
                        {word}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {analysisResult.fingerprints.type_b_words.length > 0 && (
                <div className="mb-4">
                  <h4 className="font-medium text-yellow-700 mb-2">
                    Type B: Academic Cliches (Reduce Density)
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {analysisResult.fingerprints.type_b_words.map((word, idx) => (
                      <span key={idx} className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm">
                        {word}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {analysisResult.fingerprints.recommendations_zh.length > 0 && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-700 mb-2">Recommendations</h4>
                  {analysisResult.fingerprints.recommendations_zh.map((rec, idx) => (
                    <p key={idx} className="text-sm text-gray-600 mb-1">{rec}</p>
                  ))}
                </div>
              )}

              {/* PPL (Perplexity) Analysis Section - NEW */}
              {/* PPL（困惑度）分析部分 - 新增 */}
              {analysisResult.fingerprints.ppl_score !== undefined && analysisResult.fingerprints.ppl_score !== null && (
                <div className="mt-6 border-t pt-6">
                  <h4 className="font-semibold text-gray-800 mb-4 flex items-center">
                    <Brain className="w-5 h-5 mr-2 text-blue-600" />
                    Perplexity Analysis (PPL)
                    <span className="ml-2 text-xs text-gray-500">
                      / 困惑度分析
                    </span>
                    {analysisResult.fingerprints.ppl_used_onnx && (
                      <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs flex items-center">
                        <Cpu className="w-3 h-3 mr-1" />
                        ONNX
                      </span>
                    )}
                  </h4>

                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className={clsx(
                      'rounded-lg p-4',
                      analysisResult.fingerprints.ppl_risk_level === 'high' ? 'bg-red-50' :
                      analysisResult.fingerprints.ppl_risk_level === 'medium' ? 'bg-yellow-50' :
                      'bg-green-50'
                    )}>
                      <div className={clsx(
                        'text-3xl font-bold',
                        analysisResult.fingerprints.ppl_risk_level === 'high' ? 'text-red-700' :
                        analysisResult.fingerprints.ppl_risk_level === 'medium' ? 'text-yellow-700' :
                        'text-green-700'
                      )}>
                        {analysisResult.fingerprints.ppl_score?.toFixed(1) || 'N/A'}
                      </div>
                      <div className="text-sm text-gray-600">PPL Score</div>
                    </div>
                    <div className={clsx(
                      'rounded-lg p-4',
                      analysisResult.fingerprints.ppl_risk_level === 'high' ? 'bg-red-50' :
                      analysisResult.fingerprints.ppl_risk_level === 'medium' ? 'bg-yellow-50' :
                      'bg-green-50'
                    )}>
                      <div className={clsx(
                        'text-xl font-bold uppercase',
                        analysisResult.fingerprints.ppl_risk_level === 'high' ? 'text-red-700' :
                        analysisResult.fingerprints.ppl_risk_level === 'medium' ? 'text-yellow-700' :
                        'text-green-700'
                      )}>
                        {analysisResult.fingerprints.ppl_risk_level || 'N/A'}
                      </div>
                      <div className="text-sm text-gray-600">Risk Level / 风险级别</div>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4">
                      <div className="text-xl font-bold text-blue-700">
                        {analysisResult.fingerprints.ppl_analysis?.high_risk_paragraphs?.length || 0}
                      </div>
                      <div className="text-sm text-blue-600">High Risk Paragraphs / 高风险段落</div>
                    </div>
                  </div>

                  {/* PPL Interpretation */}
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg mb-4">
                    <div className="flex items-start gap-2">
                      <Activity className="w-5 h-5 text-blue-600 mt-0.5" />
                      <div className="text-sm">
                        <p className="text-blue-800">
                          <strong>What is PPL?</strong> Perplexity measures how "predictable" text is.
                          Lower PPL (&lt;20) = highly predictable = AI-like.
                          Higher PPL (&gt;40) = less predictable = human-like.
                        </p>
                        <p className="text-blue-700 mt-1">
                          <strong>什么是PPL？</strong> 困惑度衡量文本的"可预测性"。
                          低PPL（&lt;20）= 高度可预测 = 像AI。
                          高PPL（&gt;40）= 不可预测 = 像人类。
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Per-Paragraph PPL Details */}
                  {analysisResult.fingerprints.ppl_analysis?.paragraphs && analysisResult.fingerprints.ppl_analysis.paragraphs.length > 0 && (
                    <div className="space-y-2">
                      <h5 className="text-sm font-medium text-gray-700">Per-Paragraph PPL / 各段落PPL:</h5>
                      <div className="max-h-48 overflow-y-auto space-y-2">
                        {analysisResult.fingerprints.ppl_analysis.paragraphs.map((para) => (
                          <div
                            key={para.index}
                            className={clsx(
                              'p-2 rounded flex items-center justify-between text-sm',
                              para.risk_level === 'high' ? 'bg-red-50' :
                              para.risk_level === 'medium' ? 'bg-yellow-50' :
                              'bg-green-50'
                            )}
                          >
                            <div className="flex items-center gap-2">
                              <span className={clsx(
                                'w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold',
                                para.risk_level === 'high' ? 'bg-red-200 text-red-800' :
                                para.risk_level === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                                'bg-green-200 text-green-800'
                              )}>
                                {para.index + 1}
                              </span>
                              <span className="text-gray-600 truncate max-w-[200px]" title={para.preview}>
                                {para.preview}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500 text-xs">{para.word_count} words</span>
                              <span className={clsx(
                                'font-bold',
                                para.risk_level === 'high' ? 'text-red-700' :
                                para.risk_level === 'medium' ? 'text-yellow-700' :
                                'text-green-700'
                              )}>
                                {para.ppl.toFixed(1)}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Step 5.2: Human Features */}
          {currentStep === '5.2' && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <User className="w-5 h-5 mr-2 text-pink-600" />
                Human Feature Analysis
              </h3>

              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-700">Academic Verbs</span>
                    <span className={clsx(
                      'font-bold',
                      analysisResult.human_features.verb_coverage.is_sufficient ? 'text-green-600' : 'text-red-600'
                    )}>
                      {analysisResult.human_features.verb_coverage.rate}% / {analysisResult.human_features.verb_coverage.target}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={clsx(
                        'h-2 rounded-full',
                        analysisResult.human_features.verb_coverage.is_sufficient ? 'bg-green-500' : 'bg-red-500'
                      )}
                      style={{ width: `${Math.min(100, analysisResult.human_features.verb_coverage.rate / analysisResult.human_features.verb_coverage.target * 100)}%` }}
                    />
                  </div>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-700">Academic Adjectives</span>
                    <span className={clsx(
                      'font-bold',
                      analysisResult.human_features.adjective_coverage.is_sufficient ? 'text-green-600' : 'text-red-600'
                    )}>
                      {analysisResult.human_features.adjective_coverage.rate}% / {analysisResult.human_features.adjective_coverage.target}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={clsx(
                        'h-2 rounded-full',
                        analysisResult.human_features.adjective_coverage.is_sufficient ? 'bg-green-500' : 'bg-red-500'
                      )}
                      style={{ width: `${Math.min(100, analysisResult.human_features.adjective_coverage.rate / analysisResult.human_features.adjective_coverage.target * 100)}%` }}
                    />
                  </div>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-700">Hedging Language</span>
                    <span className={clsx(
                      'font-bold',
                      analysisResult.human_features.hedging_coverage.is_sufficient ? 'text-green-600' : 'text-red-600'
                    )}>
                      {analysisResult.human_features.hedging_coverage.rate}% / {analysisResult.human_features.hedging_coverage.target}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={clsx(
                        'h-2 rounded-full',
                        analysisResult.human_features.hedging_coverage.is_sufficient ? 'bg-green-500' : 'bg-red-500'
                      )}
                      style={{ width: `${Math.min(100, analysisResult.human_features.hedging_coverage.rate / analysisResult.human_features.hedging_coverage.target * 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              {analysisResult.human_features.recommendations_zh.length > 0 && (
                <div className="mt-4 p-4 bg-green-50 rounded-lg">
                  <h4 className="font-medium text-green-700 mb-2">Recommendations</h4>
                  {analysisResult.human_features.recommendations_zh.map((rec, idx) => (
                    <p key={idx} className="text-sm text-green-800 mb-1">{rec}</p>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Step 5.3: Candidates */}
          {currentStep === '5.3' && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Replace className="w-5 h-5 mr-2 text-pink-600" />
                Replacement Candidates ({analysisResult.candidates.total_replaceable})
              </h3>

              <div className="space-y-3">
                {analysisResult.candidates.candidates.slice(0, 20).map((candidate, idx) => (
                  <div key={idx} className="p-3 bg-gray-50 rounded-lg flex items-center justify-between">
                    <div>
                      <span className={clsx(
                        'font-medium line-through',
                        candidate.type === 'type_a' && 'text-red-700',
                        candidate.type === 'type_b' && 'text-yellow-700',
                        candidate.type === 'phrase' && 'text-purple-700'
                      )}>
                        {candidate.original}
                      </span>
                      <span className="mx-2 text-gray-400">→</span>
                      <span className={clsx(
                        'font-medium',
                        candidate.is_human_feature ? 'text-green-700' : 'text-blue-700'
                      )}>
                        {candidate.recommended}
                        {candidate.is_human_feature && (
                          <span className="ml-1 text-xs text-green-500">[Human]</span>
                        )}
                      </span>
                    </div>
                    <span className={clsx(
                      'text-xs px-2 py-1 rounded',
                      candidate.type === 'type_a' && 'bg-red-100 text-red-700',
                      candidate.type === 'type_b' && 'bg-yellow-100 text-yellow-700',
                      candidate.type === 'phrase' && 'bg-purple-100 text-purple-700'
                    )}>
                      {candidate.type}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Pipeline Results */}
          {pipelineResult && (currentStep === '5.4' || currentStep === '5.5' || currentStep === 'full') && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                Rewriting Results
              </h3>

              {/* Metrics */}
              <div className="grid grid-cols-4 gap-4 mb-6">
                <div className="p-3 bg-green-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {pipelineResult.overall_metrics.paragraphs_rewritten}
                  </p>
                  <p className="text-xs text-gray-600">Paragraphs Rewritten</p>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {pipelineResult.overall_metrics.total_changes}
                  </p>
                  <p className="text-xs text-gray-600">Total Changes</p>
                </div>
                <div className="p-3 bg-red-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-red-600">
                    -{pipelineResult.overall_metrics.aigc_removed}
                  </p>
                  <p className="text-xs text-gray-600">AIGC Removed</p>
                </div>
                <div className="p-3 bg-green-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-green-600">
                    +{pipelineResult.overall_metrics.human_features_added}
                  </p>
                  <p className="text-xs text-gray-600">Human Added</p>
                </div>
              </div>

              {/* Paragraph Changes */}
              <div className="space-y-4">
                {pipelineResult.final_paragraphs.filter(p => p.changes.length > 0).map((para, idx) => (
                  <div key={idx} className="border rounded-lg overflow-hidden">
                    <div
                      className="p-4 bg-gray-50 cursor-pointer flex items-center justify-between"
                      onClick={() => setExpandedParagraph(expandedParagraph === para.index ? null : para.index)}
                    >
                      <span className="font-medium">
                        Paragraph {para.index + 1} ({para.changes.length} changes)
                      </span>
                      {expandedParagraph === para.index ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                    {expandedParagraph === para.index && (
                      <div className="p-4 border-t">
                        <div className="mb-4">
                          <h5 className="text-sm font-medium text-gray-500 mb-2">Original:</h5>
                          <p className="text-sm text-gray-600 bg-red-50 p-3 rounded">
                            {para.original}
                          </p>
                        </div>
                        <div className="mb-4">
                          <h5 className="text-sm font-medium text-gray-500 mb-2">Rewritten:</h5>
                          <p className="text-sm text-gray-800 bg-green-50 p-3 rounded">
                            {para.rewritten}
                          </p>
                        </div>
                        <div>
                          <h5 className="text-sm font-medium text-gray-500 mb-2">Changes:</h5>
                          <div className="space-y-1">
                            {para.changes.map((change, cIdx) => (
                              <div key={cIdx} className="text-sm">
                                <span className="text-red-600 line-through">{change.original}</span>
                                <span className="mx-2">→</span>
                                <span className="text-green-600">{change.replacement}</span>
                                <span className="text-gray-400 ml-2">({change.reason})</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Navigation */}
          {showNavigation && (
            <div className="flex justify-between pt-4">
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Sentence Layer
              </Button>
              <Button onClick={handleFinish}>
                Finish Analysis
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
