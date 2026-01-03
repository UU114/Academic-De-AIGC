"""
Perplexity Calculator using ONNX Runtime
使用 ONNX Runtime 的困惑度计算器

This module provides true token-level perplexity calculation using a pre-trained
language model (distilgpt2) exported to ONNX format. This replaces the zlib
compression ratio proxy with a real statistical language model.

本模块使用预训练语言模型(distilgpt2)的ONNX格式提供真实的token级困惑度计算。
这替代了zlib压缩比代理，使用真正的统计语言模型。

Key insight from improvement report:
- zlib can only detect "repetitiveness" and "low information entropy"
- It fails on high-quality AI text with rich vocabulary but predictable token sequences
- True PPL measures the statistical likelihood of token sequences
- AI text has lower PPL (more predictable), human text has higher PPL (more surprising)

来自改进报告的关键洞察：
- zlib只能检测"重复性"和"低信息熵"
- 它无法检测词汇丰富但token序列可预测的高质量AI文本
- 真实PPL测量token序列的统计可能性
- AI文本PPL较低(更可预测)，人类文本PPL较高(更出人意料)

Author: AcademicGuard Team
Date: 2026-01-02
"""

import math
import logging
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Model loading state (singleton pattern for lazy loading)
# 模型加载状态（单例模式用于懒加载）
_onnx_session = None
_tokenizer = None
_model_available: Optional[bool] = None


def _get_model_paths() -> Tuple[Path, Path]:
    """
    Get paths for ONNX model and tokenizer files
    获取ONNX模型和分词器文件的路径

    Returns:
        Tuple of (model_path, tokenizer_path)
    """
    # Model directory is at project_root/models/
    # 模型目录在 project_root/models/
    project_root = Path(__file__).parent.parent.parent.parent
    model_dir = project_root / "models"

    model_path = model_dir / "distilgpt2.onnx"
    tokenizer_path = model_dir / "tokenizer.json"

    return model_path, tokenizer_path


def _lazy_load_model() -> bool:
    """
    Lazy load ONNX model and tokenizer (one-time initialization)
    懒加载ONNX模型和分词器（一次性初始化）

    Uses singleton pattern to ensure model is loaded only once.
    使用单例模式确保模型只加载一次。

    Returns:
        True if model is available, False otherwise
    """
    global _onnx_session, _tokenizer, _model_available

    # Return cached result if already attempted
    # 如果已经尝试过，返回缓存结果
    if _model_available is not None:
        return _model_available

    try:
        # Import optional dependencies
        # 导入可选依赖
        import onnxruntime as ort

        model_path, tokenizer_path = _get_model_paths()

        # Check if model files exist
        # 检查模型文件是否存在
        if not model_path.exists():
            logger.warning(
                f"ONNX model not found at {model_path}. "
                f"Run 'python scripts/download_onnx_model.py' to download. "
                f"Falling back to zlib compression ratio."
            )
            _model_available = False
            return False

        # Try to load tokenizer from tokenizers library first, fallback to transformers
        # 首先尝试从 tokenizers 库加载分词器，回退到 transformers
        try:
            from tokenizers import Tokenizer
            if tokenizer_path.exists():
                _tokenizer = Tokenizer.from_file(str(tokenizer_path))
                logger.debug("Using fast tokenizer from tokenizers library")
            else:
                raise FileNotFoundError("tokenizer.json not found")
        except (ImportError, FileNotFoundError):
            # Fallback to transformers tokenizer (already installed in project)
            # 回退到 transformers 分词器（项目已安装）
            try:
                from transformers import GPT2TokenizerFast
                _tokenizer = GPT2TokenizerFast.from_pretrained("distilgpt2")
                logger.debug("Using tokenizer from transformers library")
            except Exception as e:
                logger.warning(
                    f"Cannot load tokenizer: {e}. "
                    f"Falling back to zlib compression ratio."
                )
                _model_available = False
                return False

        # Configure ONNX Runtime session with optimizations
        # 配置带优化的ONNX Runtime会话
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = 2  # Limit threads for responsiveness
        sess_options.inter_op_num_threads = 1

        # Try to use GPU if available, fallback to CPU
        # 如果可用则尝试使用GPU，否则回退到CPU
        providers = ['CPUExecutionProvider']
        try:
            if 'CUDAExecutionProvider' in ort.get_available_providers():
                providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        except Exception:
            pass

        _onnx_session = ort.InferenceSession(
            str(model_path),
            sess_options,
            providers=providers
        )
        _model_available = True

        logger.info(
            f"ONNX PPL model loaded successfully from {model_path}. "
            f"Using providers: {_onnx_session.get_providers()}"
        )
        return True

    except ImportError as e:
        logger.warning(
            f"ONNX dependencies not installed: {e}. "
            f"Install with: pip install onnxruntime. "
            f"Using zlib fallback."
        )
        _model_available = False
        return False

    except Exception as e:
        logger.error(f"Failed to load ONNX model: {e}")
        _model_available = False
        return False


def calculate_onnx_ppl(text: str, max_length: int = 512) -> Tuple[Optional[float], bool]:
    """
    Calculate true perplexity using ONNX model
    使用ONNX模型计算真实困惑度

    Perplexity measures how "surprised" the language model is by the text.
    Lower PPL = more predictable = more AI-like
    Higher PPL = more surprising = more human-like

    困惑度衡量语言模型对文本的"惊讶程度"。
    较低PPL = 更可预测 = 更像AI
    较高PPL = 更出人意料 = 更像人类

    Args:
        text: Input text to analyze
        max_length: Maximum token length (default 512 for efficiency)

    Returns:
        Tuple of (ppl_score, used_onnx)
        - ppl_score: Perplexity value (None if failed)
        - used_onnx: Whether ONNX model was used (True) or fallback needed (False)
    """
    # Try to load model if not already loaded
    # 如果尚未加载，尝试加载模型
    if not _lazy_load_model():
        return None, False

    # Validate input
    # 验证输入
    if not text or len(text.strip()) < 10:
        logger.debug("Text too short for PPL calculation")
        return None, False

    try:
        import numpy as np

        # Tokenize the text - handle both tokenizers library and transformers
        # 对文本进行分词 - 处理 tokenizers 库和 transformers 两种情况
        try:
            # Try tokenizers library format first
            # 首先尝试 tokenizers 库格式
            encoding = _tokenizer.encode(text)
            if hasattr(encoding, 'ids'):
                # tokenizers library
                input_ids = encoding.ids
            else:
                # transformers library returns list directly
                input_ids = encoding
        except Exception:
            # transformers tokenizer
            input_ids = _tokenizer.encode(text)

        # Need at least 2 tokens for PPL calculation (predict next from current)
        # 需要至少2个token进行PPL计算（从当前预测下一个）
        if len(input_ids) < 2:
            logger.debug("Not enough tokens for PPL calculation")
            return None, False

        # Truncate to max_length if necessary
        # 如果需要，截断到最大长度
        if len(input_ids) > max_length:
            input_ids = input_ids[:max_length]

        # Convert to numpy array with batch dimension
        # 转换为带批次维度的numpy数组
        seq_len = len(input_ids)
        input_array = np.array([input_ids], dtype=np.int64)

        # Prepare additional inputs for Transformers.js-style ONNX model
        # 为 Transformers.js 风格的 ONNX 模型准备额外输入
        # attention_mask: all 1s for the full sequence
        # 注意力掩码：整个序列都是1
        attention_mask = np.ones((1, seq_len), dtype=np.int64)

        # position_ids: 0, 1, 2, ... for each position
        # 位置ID：每个位置0, 1, 2, ...
        position_ids = np.arange(seq_len, dtype=np.int64).reshape(1, -1)

        # past_key_values: empty tensors (no past context)
        # 过去的键值：空张量（没有过去的上下文）
        # distilgpt2 has 6 layers, each with 12 heads, head_dim=64
        # distilgpt2有6层，每层12个头，head_dim=64
        num_layers = 6
        num_heads = 12
        head_dim = 64
        past_seq_len = 0  # No past context for PPL calculation / PPL计算没有过去上下文

        # Build input feed with all required tensors
        # 构建包含所有必需张量的输入
        input_feed = {
            "input_ids": input_array,
            "attention_mask": attention_mask,
            "position_ids": position_ids,
        }

        # Add empty past_key_values for each layer
        # 为每一层添加空的past_key_values
        for i in range(num_layers):
            input_feed[f"past_key_values.{i}.key"] = np.zeros(
                (1, num_heads, past_seq_len, head_dim), dtype=np.float32
            )
            input_feed[f"past_key_values.{i}.value"] = np.zeros(
                (1, num_heads, past_seq_len, head_dim), dtype=np.float32
            )

        # Run inference with all required inputs
        # 使用所有必需的输入运行推理
        outputs = _onnx_session.run(None, input_feed)
        logits = outputs[0]  # Shape: [batch, seq_len, vocab_size]

        # Calculate cross-entropy loss for perplexity
        # 计算交叉熵损失用于困惑度
        # Shift: predict next token from current position
        # 移位：从当前位置预测下一个token
        shift_logits = logits[:, :-1, :]  # [batch, seq_len-1, vocab_size]
        shift_labels = input_array[:, 1:]  # [batch, seq_len-1]

        # Compute log softmax for numerical stability
        # 为数值稳定性计算log softmax
        # log_softmax(x) = x - log(sum(exp(x)))
        max_logits = np.max(shift_logits, axis=-1, keepdims=True)
        exp_logits = np.exp(shift_logits - max_logits)
        sum_exp_logits = np.sum(exp_logits, axis=-1, keepdims=True)
        log_probs = shift_logits - max_logits - np.log(sum_exp_logits)

        # Get log probability of actual tokens
        # 获取实际token的对数概率
        token_log_probs = []
        for i, token_id in enumerate(shift_labels[0]):
            token_log_probs.append(log_probs[0, i, token_id])

        # Perplexity = exp(-mean(log_probs))
        # 困惑度 = exp(-mean(log_probs))
        avg_neg_log_prob = -np.mean(token_log_probs)
        ppl = math.exp(avg_neg_log_prob)

        # Sanity check: PPL should be reasonable (typically 5-500 for real text)
        # 健全性检查：PPL应该在合理范围内（真实文本通常为5-500）
        if ppl < 1.0 or ppl > 10000:
            logger.warning(f"Unusual PPL value: {ppl}. May indicate model issue.")

        logger.debug(f"ONNX PPL calculated: {ppl:.2f} for {len(input_ids)} tokens")
        return ppl, True

    except Exception as e:
        logger.warning(f"ONNX PPL calculation failed: {e}")
        return None, False


def is_onnx_available() -> bool:
    """
    Check if ONNX model is available for PPL calculation
    检查ONNX模型是否可用于PPL计算

    Returns:
        True if ONNX model can be used, False otherwise
    """
    return _lazy_load_model()


def get_model_info() -> dict:
    """
    Get information about the loaded model
    获取已加载模型的信息

    Returns:
        Dictionary with model information
    """
    if not _lazy_load_model():
        return {
            "available": False,
            "reason": "Model not loaded or dependencies missing"
        }

    model_path, tokenizer_path = _get_model_paths()

    return {
        "available": True,
        "model_path": str(model_path),
        "tokenizer_path": str(tokenizer_path),
        "providers": _onnx_session.get_providers() if _onnx_session else [],
        "model_type": "distilgpt2"
    }
