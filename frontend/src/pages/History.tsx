import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Clock, Play, CheckCircle, Pause, Trash2, AlertCircle } from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import RiskBadge from '../components/common/RiskBadge';
import ProgressBar from '../components/common/ProgressBar';
import { sessionApi, documentApi } from '../services/api';
import type { SessionInfo, DocumentInfo } from '../types';

/**
 * History page - View and resume past sessions
 * 历史页面 - 查看和恢复过去的会话
 */
export default function History() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'sessions' | 'documents'>('sessions');

  // Load data on mount
  // 组件挂载时加载数据
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [sessionsData, documentsData] = await Promise.all([
        sessionApi.list(),
        documentApi.list(),
      ]);
      setSessions(sessionsData);
      setDocuments(documentsData);
    } catch (err) {
      setError((err as Error).message || '加载失败');
    } finally {
      setIsLoading(false);
    }
  };

  // Resume a session
  // 恢复会话
  const handleResumeSession = (session: SessionInfo) => {
    if (session.mode === 'intervention') {
      navigate(`/intervention/${session.sessionId}`);
    } else {
      navigate(`/yolo/${session.sessionId}`);
    }
  };

  // Delete a document
  // 删除文档
  const handleDeleteDocument = async (docId: string) => {
    if (!confirm('确定要删除此文档及其所有会话吗？')) return;

    try {
      await documentApi.delete(docId);
      loadData();
    } catch (err) {
      setError((err as Error).message || '删除失败');
    }
  };

  // Get status icon
  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'active':
        return <Play className="w-4 h-4 text-blue-500" />;
      case 'paused':
        return <Pause className="w-4 h-4 text-amber-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  // Format date
  // 格式化日期
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">历史任务</h1>
          <p className="text-gray-600">History - View and resume past sessions</p>
        </div>
        <Button variant="primary" onClick={() => navigate('/upload')}>
          新建任务
        </Button>
      </div>

      {/* Error message */}
      {error && (
        <div className="flex items-center p-4 mb-6 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex space-x-2 mb-6">
        <button
          onClick={() => setActiveTab('sessions')}
          className={clsx(
            'px-4 py-2 rounded-lg font-medium transition-colors',
            activeTab === 'sessions'
              ? 'bg-primary-100 text-primary-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          )}
        >
          会话列表 ({sessions.length})
        </button>
        <button
          onClick={() => setActiveTab('documents')}
          className={clsx(
            'px-4 py-2 rounded-lg font-medium transition-colors',
            activeTab === 'documents'
              ? 'bg-primary-100 text-primary-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          )}
        >
          文档列表 ({documents.length})
        </button>
      </div>

      {/* Sessions Tab */}
      {activeTab === 'sessions' && (
        <div className="space-y-4">
          {sessions.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Clock className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>暂无历史会话</p>
              <p className="text-sm">上传文档开始第一个任务</p>
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.sessionId}
                className="card p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => handleResumeSession(session)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <FileText className="w-8 h-8 text-gray-400" />
                    <div>
                      <h3 className="font-medium text-gray-800">
                        {session.documentName}
                      </h3>
                      <div className="flex items-center space-x-3 text-sm text-gray-500">
                        <span className="flex items-center">
                          {getStatusIcon(session.status)}
                          <span className="ml-1">
                            {session.status === 'completed' ? '已完成' :
                             session.status === 'active' ? '进行中' : '已暂停'}
                          </span>
                        </span>
                        <span>•</span>
                        <span>{session.mode === 'intervention' ? '干预模式' : 'YOLO模式'}</span>
                        <span>•</span>
                        <span>{formatDate(session.createdAt)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className="text-sm text-gray-500">
                        {session.processed} / {session.totalSentences} 句
                      </div>
                      <ProgressBar
                        value={session.progressPercent}
                        size="sm"
                        className="w-24"
                      />
                    </div>
                    <Button
                      variant={session.status === 'completed' ? 'secondary' : 'primary'}
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleResumeSession(session);
                      }}
                    >
                      {session.status === 'completed' ? '查看' : '继续'}
                    </Button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Documents Tab */}
      {activeTab === 'documents' && (
        <div className="space-y-4">
          {documents.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>暂无上传的文档</p>
            </div>
          ) : (
            documents.map((doc) => (
              <div key={doc.id} className="card p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <FileText className="w-8 h-8 text-gray-400" />
                    <div>
                      <h3 className="font-medium text-gray-800">{doc.filename}</h3>
                      <div className="flex items-center space-x-3 text-sm text-gray-500">
                        <span>{doc.totalSentences} 句</span>
                        <span>•</span>
                        <span>{formatDate(doc.createdAt)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      {doc.highRiskCount > 0 && (
                        <RiskBadge level="high" score={doc.highRiskCount} size="sm" />
                      )}
                      {doc.mediumRiskCount > 0 && (
                        <RiskBadge level="medium" score={doc.mediumRiskCount} size="sm" />
                      )}
                      {doc.lowRiskCount > 0 && (
                        <RiskBadge level="low" score={doc.lowRiskCount} size="sm" />
                      )}
                    </div>
                    <button
                      onClick={() => handleDeleteDocument(doc.id)}
                      className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                      title="删除文档"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
