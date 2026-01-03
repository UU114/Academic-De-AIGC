#!/usr/bin/env python3
"""
Download and convert distilgpt2 to ONNX format for PPL calculation
下载并转换distilgpt2到ONNX格式用于PPL计算

This script downloads the distilgpt2 model from HuggingFace and exports it
to ONNX format for efficient inference without PyTorch dependency at runtime.

本脚本从HuggingFace下载distilgpt2模型并导出为ONNX格式，
以便在运行时无需PyTorch依赖进行高效推理。

Usage:
    python scripts/download_onnx_model.py

Requirements (install before running):
    pip install torch transformers onnx

Output:
    models/distilgpt2.onnx - ONNX model file (~200MB)
    models/tokenizer.json - Tokenizer file

Author: AcademicGuard Team
Date: 2026-01-02
"""

import sys
import logging
from pathlib import Path

# Configure logging
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """
    Check if required dependencies are installed
    检查是否安装了所需的依赖项
    """
    missing = []

    try:
        import torch
        logger.info(f"PyTorch version: {torch.__version__}")
    except ImportError:
        missing.append("torch")

    try:
        import transformers
        logger.info(f"Transformers version: {transformers.__version__}")
    except ImportError:
        missing.append("transformers")

    try:
        import onnx
        logger.info(f"ONNX version: {onnx.__version__}")
    except ImportError:
        missing.append("onnx")

    if missing:
        logger.error(
            f"Missing dependencies: {', '.join(missing)}. "
            f"Install with: pip install {' '.join(missing)}"
        )
        return False

    return True


def download_and_convert():
    """
    Download distilgpt2 model and convert to ONNX format
    下载distilgpt2模型并转换为ONNX格式
    """
    import torch
    from transformers import GPT2LMHeadModel, GPT2TokenizerFast

    # Setup model directory
    # 设置模型目录
    project_root = Path(__file__).parent.parent
    model_dir = project_root / "models"
    model_dir.mkdir(exist_ok=True)

    onnx_path = model_dir / "distilgpt2.onnx"
    tokenizer_path = model_dir / "tokenizer.json"

    # Check if already exists
    # 检查是否已存在
    if onnx_path.exists() and tokenizer_path.exists():
        logger.info(f"Model already exists at {onnx_path}")
        response = input("Overwrite existing model? (y/N): ")
        if response.lower() != 'y':
            logger.info("Skipping download.")
            return

    logger.info("Downloading distilgpt2 model from HuggingFace...")

    # Download model and tokenizer
    # 下载模型和分词器
    model = GPT2LMHeadModel.from_pretrained("distilgpt2")
    tokenizer = GPT2TokenizerFast.from_pretrained("distilgpt2")

    logger.info("Model downloaded successfully.")

    # Set model to evaluation mode
    # 设置模型为评估模式
    model.eval()

    # Create dummy input for ONNX export
    # 创建ONNX导出的虚拟输入
    # Shape: [batch_size, sequence_length]
    dummy_input = torch.randint(0, 50257, (1, 128))

    logger.info("Exporting model to ONNX format...")

    # Export to ONNX with dynamic axes for variable batch and sequence length
    # 导出为ONNX，使用动态轴以支持可变的批次和序列长度
    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        input_names=["input_ids"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "logits": {0: "batch_size", 1: "sequence_length"}
        },
        opset_version=14,
        do_constant_folding=True,
        verbose=False
    )

    logger.info(f"ONNX model exported to {onnx_path}")
    logger.info(f"Model size: {onnx_path.stat().st_size / 1024 / 1024:.1f} MB")

    # Save tokenizer in fast tokenizer format
    # 以快速分词器格式保存分词器
    tokenizer.save_pretrained(str(model_dir))

    # Also save the tokenizer.json specifically
    # 同时专门保存tokenizer.json
    if (model_dir / "tokenizer.json").exists():
        logger.info(f"Tokenizer saved to {tokenizer_path}")
    else:
        # Fallback: save vocab and merges files
        # 回退：保存词汇表和合并文件
        logger.warning("tokenizer.json not found, saving vocab files instead")

    logger.info("Download and conversion complete!")
    logger.info("")
    logger.info("To use the model, ensure onnxruntime is installed:")
    logger.info("  pip install onnxruntime tokenizers")


def verify_model():
    """
    Verify the exported ONNX model
    验证导出的ONNX模型
    """
    import onnx

    project_root = Path(__file__).parent.parent
    model_path = project_root / "models" / "distilgpt2.onnx"

    if not model_path.exists():
        logger.error(f"Model not found at {model_path}")
        return False

    logger.info("Verifying ONNX model...")

    try:
        # Load and check model
        # 加载并检查模型
        model = onnx.load(str(model_path))
        onnx.checker.check_model(model)

        logger.info("Model verification passed!")

        # Print model info
        # 打印模型信息
        logger.info(f"Model inputs: {[i.name for i in model.graph.input]}")
        logger.info(f"Model outputs: {[o.name for o in model.graph.output]}")

        return True

    except Exception as e:
        logger.error(f"Model verification failed: {e}")
        return False


def test_inference():
    """
    Test inference with the ONNX model
    使用ONNX模型测试推理
    """
    try:
        import onnxruntime as ort
        from tokenizers import Tokenizer
        import numpy as np
        import math
    except ImportError as e:
        logger.warning(f"Cannot test inference, missing dependencies: {e}")
        return

    project_root = Path(__file__).parent.parent
    model_path = project_root / "models" / "distilgpt2.onnx"
    tokenizer_path = project_root / "models" / "tokenizer.json"

    if not model_path.exists() or not tokenizer_path.exists():
        logger.warning("Model or tokenizer not found, skipping inference test")
        return

    logger.info("Testing inference...")

    # Load model and tokenizer
    # 加载模型和分词器
    session = ort.InferenceSession(str(model_path))
    tokenizer = Tokenizer.from_file(str(tokenizer_path))

    # Test text samples
    # 测试文本样本
    test_texts = [
        # AI-like text (should have lower PPL)
        "The implementation of this methodology demonstrates significant improvements in overall performance metrics. Furthermore, the results indicate that this approach is particularly effective in addressing the identified challenges.",
        # Human-like text (should have higher PPL)
        "So I tried this new method—surprisingly, it worked. Not perfectly, mind you, but good enough. The weird part? Nobody expected it to help with those tricky edge cases.",
    ]

    for i, text in enumerate(test_texts):
        encoding = tokenizer.encode(text)
        input_ids = np.array([encoding.ids], dtype=np.int64)

        outputs = session.run(None, {"input_ids": input_ids})
        logits = outputs[0]

        # Calculate PPL
        # 计算PPL
        shift_logits = logits[:, :-1, :]
        shift_labels = input_ids[:, 1:]

        max_logits = np.max(shift_logits, axis=-1, keepdims=True)
        exp_logits = np.exp(shift_logits - max_logits)
        sum_exp = np.sum(exp_logits, axis=-1, keepdims=True)
        log_probs = shift_logits - max_logits - np.log(sum_exp)

        token_log_probs = [log_probs[0, j, shift_labels[0, j]] for j in range(len(shift_labels[0]))]
        ppl = math.exp(-np.mean(token_log_probs))

        style = "AI-like" if i == 0 else "Human-like"
        logger.info(f"Sample {i+1} ({style}): PPL = {ppl:.2f}")

    logger.info("Inference test complete!")


def main():
    """
    Main entry point
    主入口点
    """
    logger.info("=" * 60)
    logger.info("AcademicGuard ONNX Model Downloader")
    logger.info("=" * 60)

    # Check dependencies
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # Download and convert
    # 下载并转换
    download_and_convert()

    # Verify model
    # 验证模型
    verify_model()

    # Test inference
    # 测试推理
    test_inference()

    logger.info("")
    logger.info("Setup complete! You can now use ONNX-based PPL calculation.")


if __name__ == "__main__":
    main()
