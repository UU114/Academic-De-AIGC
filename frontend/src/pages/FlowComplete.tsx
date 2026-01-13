import { useEffect, useState } from 'react';
import { useParams, useSearchParams, Link, useNavigate } from 'react-router-dom';
import {
  Download,
  FileText,
  CheckCircle,
  AlertTriangle,
  ArrowLeft,
  Loader2,
  Copy,
  Check,
  Home,
  History,
  RefreshCw,
  BarChart2,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import LoadingMessage from '../components/common/LoadingMessage';
import { documentApi, sessionApi, exportApi } from '../services/api';

/**
 * FlowComplete - Analysis completion and export page
 * 分析完成和导出页面
 *
 * This page is shown after completing the 5-layer analysis flow.
 * Allows users to review results and export the document.
 * 此页面在完成5层分析流程后显示。允许用户查看结果并导出文档。
 */

interface DocumentInfo {
  id: string;
  filename: string;
  originalText: string;
  modifiedText?: string;
  createdAt: string;
}

interface AnalysisStats {
  totalWords: number;
  totalSentences: number;
  issuesFound: number;
  issuesResolved: number;
  riskReduction: number;
}

export default function FlowComplete() {
  const { documentId } = useParams<{ documentId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const sessionId = searchParams.get('session');
  const mode = searchParams.get('mode') || 'intervention';

  // State
  const [isLoading, setIsLoading] = useState(true);
  const [document, setDocument] = useState<DocumentInfo | null>(null);
  const [stats, setStats] = useState<AnalysisStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<'txt' | 'docx' | 'pdf'>('txt');
  const [copied, setCopied] = useState(false);

  // Load document and stats
  // 加载文档和统计信息
  useEffect(() => {
    if (!documentId) {
      setError('Document ID not found / 未找到文档ID');
      setIsLoading(false);
      return;
    }

    const loadData = async () => {
      setIsLoading(true);
      try {
        // Load document info
        // 加载文档信息
        const docInfo = await documentApi.get(documentId);
        setDocument({
          id: documentId,
          filename: docInfo.filename || 'document.txt',
          originalText: docInfo.originalText || '',
          modifiedText: docInfo.modifiedText,
          createdAt: docInfo.createdAt || new Date().toISOString(),
        });

        // Calculate basic stats
        // 计算基本统计
        const text = docInfo.modifiedText || docInfo.originalText || '';
        const words = text.split(/\s+/).filter(w => w.length > 0).length;
        const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0).length;

        setStats({
          totalWords: words,
          totalSentences: sentences,
          issuesFound: 0,
          issuesResolved: 0,
          riskReduction: 0,
        });

        // Try to load session stats if available
        // 如果可用，尝试加载会话统计
        if (sessionId) {
          try {
            const sessionStats = await sessionApi.getReviewStats(sessionId);
            if (sessionStats) {
              setStats(prev => ({
                ...prev!,
                totalSentences: sessionStats.total_sentences || prev!.totalSentences,
                issuesFound: sessionStats.modified_count || 0,
                issuesResolved: sessionStats.modified_count || 0,
                riskReduction: sessionStats.avg_risk_reduction || 0,
              }));
            }
          } catch {
            // Session stats not available, continue with basic stats
            // 会话统计不可用，继续使用基本统计
          }
        }
      } catch (err) {
        console.error('Failed to load document:', err);
        setError('Failed to load document / 加载文档失败');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [documentId, sessionId]);

  // Handle export
  // 处理导出
  const handleExport = async () => {
    if (!documentId || !sessionId) {
      setError('Cannot export: missing document or session ID / 无法导出：缺少文档或会话ID');
      return;
    }

    setIsExporting(true);
    try {
      const blob = await exportApi.exportDocument(sessionId, exportFormat);
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = `${document?.filename || 'document'}.${exportFormat}`;
      window.document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      window.document.body.removeChild(a);
    } catch (err) {
      console.error('Export failed:', err);
      setError('Export failed / 导出失败');
    } finally {
      setIsExporting(false);
    }
  };

  // Handle copy to clipboard
  // 处理复制到剪贴板
  const handleCopy = async () => {
    const text = document?.modifiedText || document?.originalText || '';
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Handle start new analysis
  // 处理开始新分析
  const handleNewAnalysis = () => {
    navigate('/upload');
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex items-center justify-center min-h-[50vh]">
          <LoadingMessage message="Loading results... / 加载结果中..." />
        </div>
      </div>
    );
  }

  if (error && !document) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-red-600" />
            <div>
              <h3 className="text-lg font-semibold text-red-700">Error</h3>
              <p className="text-red-600">{error}</p>
            </div>
          </div>
          <div className="mt-4 flex gap-3">
            <Link to="/">
              <Button variant="outline">
                <Home className="w-4 h-4 mr-2" />
                Go Home / 返回首页
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-6">
      {/* Header */}
      {/* 标题 */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-6">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-green-100 rounded-full">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-green-800">
              Analysis Complete / 分析完成
            </h1>
            <p className="text-green-600 mt-1">
              Your document has been processed through all analysis layers.
            </p>
            <p className="text-green-500 text-sm">
              您的文档已通过所有分析层处理完成。
            </p>
          </div>
        </div>
      </div>

      {/* Document Info */}
      {/* 文档信息 */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
          <FileText className="w-5 h-5 text-gray-600" />
          Document Information / 文档信息
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">Filename / 文件名</p>
            <p className="font-medium text-gray-900">{document?.filename}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Document ID</p>
            <p className="font-mono text-sm text-gray-600">{document?.id}</p>
          </div>
        </div>
      </div>

      {/* Statistics */}
      {/* 统计信息 */}
      {stats && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
            <BarChart2 className="w-5 h-5 text-gray-600" />
            Statistics / 统计信息
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-blue-600">Total Words / 总词数</p>
              <p className="text-2xl font-bold text-blue-700">{stats.totalWords}</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <p className="text-sm text-purple-600">Sentences / 句子数</p>
              <p className="text-2xl font-bold text-purple-700">{stats.totalSentences}</p>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <p className="text-sm text-orange-600">Issues Found / 发现问题</p>
              <p className="text-2xl font-bold text-orange-700">{stats.issuesFound}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm text-green-600">Resolved / 已解决</p>
              <p className="text-2xl font-bold text-green-700">{stats.issuesResolved}</p>
            </div>
          </div>
        </div>
      )}

      {/* Document Preview */}
      {/* 文档预览 */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Document Preview / 文档预览
          </h2>
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopy}
            className="flex items-center gap-2"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-green-600" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy / 复制
              </>
            )}
          </Button>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
          <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
            {document?.modifiedText || document?.originalText || 'No content available'}
          </pre>
        </div>
      </div>

      {/* Export Options */}
      {/* 导出选项 */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
          <Download className="w-5 h-5 text-gray-600" />
          Export Document / 导出文档
        </h2>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Format / 格式:</span>
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as 'txt' | 'docx' | 'pdf')}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
            >
              <option value="txt">Text (.txt)</option>
              <option value="docx">Word (.docx)</option>
              <option value="pdf">PDF (.pdf)</option>
            </select>
          </div>
          <Button
            onClick={handleExport}
            disabled={isExporting || !sessionId}
            className={clsx(!sessionId && 'opacity-50 cursor-not-allowed')}
          >
            {isExporting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                Export / 导出
              </>
            )}
          </Button>
          {!sessionId && (
            <span className="text-sm text-yellow-600">
              Session ID required for export / 导出需要会话ID
            </span>
          )}
        </div>
      </div>

      {/* Error Display */}
      {/* 错误显示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Navigation */}
      {/* 导航 */}
      <div className="flex items-center justify-between pt-4 border-t">
        <Button
          variant="outline"
          onClick={() => navigate(-1)}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back / 返回
        </Button>
        <div className="flex gap-3">
          <Link to="/history">
            <Button variant="outline" className="flex items-center gap-2">
              <History className="w-4 h-4" />
              View History / 查看历史
            </Button>
          </Link>
          <Button onClick={handleNewAnalysis} className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
            New Analysis / 新建分析
          </Button>
        </div>
      </div>
    </div>
  );
}
