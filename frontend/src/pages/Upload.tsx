import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, FileText, Type, AlertCircle, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import Button from '../components/common/Button';
import ColloquialismSlider from '../components/settings/ColloquialismSlider';
import { useRotatingLoadingMessage } from '../utils/loadingMessages';
import { documentApi, sessionApi } from '../services/api';
import { useConfigStore } from '../stores/configStore';
import type { RiskLevel } from '../types';

/**
 * Upload page - Document upload and session configuration
 * 上传页面 - 文档上传和会话配置
 */
export default function Upload() {
  const navigate = useNavigate();
  const { processLevels, setProcessLevels, colloquialismLevel } = useConfigStore();

  // Fun loading message for upload state
  // 趣味上传加载提示
  const uploadLoadingMessage = useRotatingLoadingMessage('upload', 3000);

  // Upload state
  // 上传状态
  const [uploadMode, setUploadMode] = useState<'file' | 'text'>('file');
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Session mode
  // 会话模式: 'intervention' (干预模式), 'yolo' (自动处理)
  // Both modes start from Level 1 (structure analysis)
  // 两种模式都从 Level 1（结构分析）开始
  const [sessionMode, setSessionMode] = useState<'intervention' | 'yolo'>('intervention');

  // Handle file drop
  // 处理文件拖放
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  }, []);

  // Validate and set file
  // 验证并设置文件
  const validateAndSetFile = (selectedFile: File) => {
    const allowedTypes = [
      'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(selectedFile.type)) {
      setError('仅支持 TXT 和 DOCX 格式');
      return;
    }

    if (selectedFile.size > maxSize) {
      setError('文件大小不能超过 10MB');
      return;
    }

    setFile(selectedFile);
    setError(null);
  };

  // Handle file input change
  // 处理文件输入变化
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  // Handle process level toggle
  // 处理处理等级切换
  const toggleProcessLevel = (level: RiskLevel) => {
    const newLevels = processLevels.includes(level)
      ? processLevels.filter((l) => l !== level)
      : [...processLevels, level];
    setProcessLevels(newLevels);
  };

  // Handle submit
  // 处理提交
  const handleSubmit = async () => {
    if (uploadMode === 'file' && !file) {
      setError('请选择一个文件');
      return;
    }

    if (uploadMode === 'text' && !text.trim()) {
      setError('请输入文本内容');
      return;
    }

    if (processLevels.length === 0) {
      setError('请至少选择一个处理风险等级');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      // Upload document
      // 上传文档
      let documentId: string;

      if (uploadMode === 'file' && file) {
        const result = await documentApi.upload(file);
        documentId = result.id;
      } else {
        const result = await documentApi.uploadText(text);
        documentId = result.id;
      }

      // Create session for this document
      // 为此文档创建会话
      const sessionResult = await sessionApi.start(documentId, {
        mode: sessionMode,
        colloquialismLevel,
        processLevels,
      });

      // Navigate to Step 1-1 (document structure analysis) with mode and session
      // Both intervention and yolo modes start from Step 1-1
      // 导航到 Step 1-1（文档结构分析），带上模式和会话ID
      // 干预模式和YOLO模式都从 Step 1-1 开始
      navigate(`/flow/step1-1/${documentId}?mode=${sessionMode}&session=${sessionResult.sessionId}`);
    } catch (err) {
      setError((err as Error).message || '上传失败，请重试');
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">上传文档</h1>
      <p className="text-gray-600 mb-8">Upload your document to start the humanization process</p>

      {/* Upload Mode Tabs */}
      <div className="flex space-x-2 mb-6">
        <button
          onClick={() => setUploadMode('file')}
          className={clsx(
            'flex items-center px-4 py-2 rounded-lg font-medium transition-colors',
            uploadMode === 'file'
              ? 'bg-primary-100 text-primary-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          )}
        >
          <UploadIcon className="w-4 h-4 mr-2" />
          上传文件
        </button>
        <button
          onClick={() => setUploadMode('text')}
          className={clsx(
            'flex items-center px-4 py-2 rounded-lg font-medium transition-colors',
            uploadMode === 'text'
              ? 'bg-primary-100 text-primary-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          )}
        >
          <Type className="w-4 h-4 mr-2" />
          粘贴文本
        </button>
      </div>

      {/* Upload Area */}
      <div className="card p-6 mb-6">
        {uploadMode === 'file' ? (
          <div
            onDrop={handleDrop}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            className={clsx(
              'border-2 border-dashed rounded-xl p-8 text-center transition-colors',
              isDragging
                ? 'border-primary-500 bg-primary-50'
                : file
                ? 'border-green-500 bg-green-50'
                : 'border-gray-300 hover:border-gray-400'
            )}
          >
            {file ? (
              <div className="flex items-center justify-center">
                <FileText className="w-8 h-8 text-green-600 mr-3" />
                <div className="text-left">
                  <p className="font-medium text-gray-800">{file.name}</p>
                  <p className="text-sm text-gray-500">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <button
                  onClick={() => setFile(null)}
                  className="ml-4 text-gray-400 hover:text-red-500"
                >
                  &times;
                </button>
              </div>
            ) : (
              <>
                <UploadIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-2">
                  拖放文件到此处，或
                </p>
                <label className="inline-block">
                  <input
                    type="file"
                    accept=".txt,.docx"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <span className="text-primary-600 hover:text-primary-700 cursor-pointer font-medium">
                    点击选择文件
                  </span>
                </label>
                <p className="text-sm text-gray-500 mt-2">
                  支持 TXT、DOCX 格式，最大 10MB
                </p>
              </>
            )}
          </div>
        ) : (
          <div>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="粘贴或输入您的英文文本..."
              className="textarea h-48"
            />
            <p className="text-sm text-gray-500 mt-2 text-right">
              {text.length} 字符
            </p>
          </div>
        )}
      </div>

      {/* Session Configuration */}
      <div className="card p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          处理设置 / Processing Settings
        </h2>

        {/* Session Mode */}
        <div className="mb-6">
          <label className="text-sm font-medium text-gray-700 mb-2 block">
            处理模式 / Processing Mode
          </label>
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => setSessionMode('intervention')}
              className={clsx(
                'p-4 rounded-lg border-2 text-left transition-colors',
                sessionMode === 'intervention'
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              )}
            >
              <p className="font-medium text-gray-800">干预模式</p>
              <p className="text-sm text-gray-500">Intervention Mode</p>
              <p className="text-xs text-gray-400 mt-2">
                三级流程：结构 → 衔接 → 句子
              </p>
              <p className="text-xs text-gray-400">
                每一步手动选择方案，完全掌控
              </p>
            </button>
            <button
              onClick={() => setSessionMode('yolo')}
              className={clsx(
                'p-4 rounded-lg border-2 text-left transition-colors',
                sessionMode === 'yolo'
                  ? 'border-amber-500 bg-amber-50'
                  : 'border-gray-200 hover:border-gray-300'
              )}
            >
              <p className="font-medium text-gray-800">YOLO模式</p>
              <p className="text-sm text-gray-500">Auto Mode</p>
              <p className="text-xs text-gray-400 mt-2">
                三级流程：结构 → 衔接 → 句子
              </p>
              <p className="text-xs text-gray-400">
                全自动处理，最后统一审核
              </p>
            </button>
          </div>
          <p className="text-xs text-amber-600 mt-2">
            💡 YOLO模式仅适用于灌水文章，想认真改的请用干预模式
          </p>
        </div>

        {/* Colloquialism Level */}
        <div className="mb-6">
          <ColloquialismSlider />
        </div>

        {/* Process Levels */}
        <div>
          <label className="text-sm font-medium text-gray-700 mb-2 block">
            处理风险等级
          </label>
          <div className="flex space-x-3">
            {(['high', 'medium', 'low'] as RiskLevel[]).map((level) => {
              const labels: Record<RiskLevel, { zh: string; en: string; color: string }> = {
                high: { zh: '高风险', en: 'High', color: 'bg-red-100 text-red-700 border-red-300' },
                medium: { zh: '中风险', en: 'Medium', color: 'bg-amber-100 text-amber-700 border-amber-300' },
                low: { zh: '低风险', en: 'Low', color: 'bg-green-100 text-green-700 border-green-300' },
                safe: { zh: '安全', en: 'Safe', color: 'bg-gray-100 text-gray-700 border-gray-300' },
              };
              const isSelected = processLevels.includes(level);

              return (
                <button
                  key={level}
                  onClick={() => toggleProcessLevel(level)}
                  className={clsx(
                    'px-4 py-2 rounded-lg border-2 font-medium transition-all',
                    isSelected
                      ? labels[level].color
                      : 'bg-gray-50 text-gray-400 border-gray-200'
                  )}
                >
                  {labels[level].zh}
                </button>
              );
            })}
          </div>
          <p className="text-xs text-gray-500 mt-2">
            选择需要处理的风险等级，低风险句子通常可以保持原样
          </p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center p-4 mb-6 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Submit Button */}
      <Button
        variant="primary"
        size="lg"
        onClick={handleSubmit}
        disabled={isUploading || (uploadMode === 'file' ? !file : !text.trim())}
        className="w-full"
      >
        {isUploading ? (
          <>
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            <span className="text-sm">{uploadLoadingMessage.zh}</span>
          </>
        ) : (
          <>
            开始处理
          </>
        )}
      </Button>
    </div>
  );
}
