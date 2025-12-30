"""
Semantic similarity validation module
语义相似度验证模块
"""

import logging
from dataclasses import dataclass
from typing import Optional, List

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class SemanticValidationResult:
    """
    Result of semantic validation
    语义验证结果
    """
    similarity: float
    passed: bool
    message: str
    message_zh: str


class SemanticValidator:
    """
    Semantic similarity validation engine
    语义相似度验证引擎

    Ensures modified text preserves the meaning of original text.
    Uses Sentence-BERT for production, falls back to simple methods for MVP.
    """

    def __init__(self, threshold: float = None):
        """
        Initialize semantic validator

        Args:
            threshold: Minimum similarity score to pass (default from settings)
        """
        self.threshold = threshold or settings.semantic_similarity_threshold
        self._model = None
        self._model_loaded = False

    def _load_model(self):
        """
        Lazy load the sentence transformer model
        延迟加载句子转换模型
        """
        if self._model_loaded:
            return

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            self._model_loaded = True
            logger.info("Loaded Sentence-BERT model")
        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback similarity")
            self._model_loaded = True  # Mark as loaded to avoid repeated attempts
        except Exception as e:
            logger.error(f"Failed to load Sentence-BERT model: {e}")
            self._model_loaded = True

    def validate(
        self,
        original: str,
        modified: str
    ) -> SemanticValidationResult:
        """
        Validate that modified text preserves semantic meaning
        验证修改后的文本保留了语义含义

        Args:
            original: Original sentence
            modified: Modified sentence

        Returns:
            SemanticValidationResult with similarity score and pass/fail
        """
        if not original or not modified:
            return SemanticValidationResult(
                similarity=0.0,
                passed=False,
                message="Empty text provided",
                message_zh="提供了空文本"
            )

        # Calculate similarity
        # 计算相似度
        similarity = self._calculate_similarity(original, modified)

        # Determine pass/fail
        # 判断是否通过
        passed = similarity >= self.threshold

        # Generate message
        # 生成消息
        if passed:
            if similarity >= 0.95:
                message = "Excellent semantic preservation"
                message_zh = "语义保持极佳"
            elif similarity >= 0.90:
                message = "Good semantic preservation"
                message_zh = "语义保持良好"
            else:
                message = "Acceptable semantic preservation"
                message_zh = "语义保持可接受"
        else:
            if similarity >= 0.70:
                message = f"Semantic similarity ({similarity:.2f}) slightly below threshold ({self.threshold})"
                message_zh = f"语义相似度 ({similarity:.2f}) 略低于阈值 ({self.threshold})"
            elif similarity >= 0.50:
                message = f"Significant semantic drift detected ({similarity:.2f})"
                message_zh = f"检测到明显语义漂移 ({similarity:.2f})"
            else:
                message = f"Major semantic change detected ({similarity:.2f})"
                message_zh = f"检测到重大语义变化 ({similarity:.2f})"

        return SemanticValidationResult(
            similarity=similarity,
            passed=passed,
            message=message,
            message_zh=message_zh
        )

    def _calculate_similarity(self, original: str, modified: str) -> float:
        """
        Calculate semantic similarity between texts
        计算文本间的语义相似度
        """
        # Try Sentence-BERT first
        # 首先尝试Sentence-BERT
        self._load_model()

        if self._model is not None:
            return self._calculate_sbert_similarity(original, modified)
        else:
            return self._calculate_fallback_similarity(original, modified)

    def _calculate_sbert_similarity(self, original: str, modified: str) -> float:
        """
        Calculate similarity using Sentence-BERT
        使用Sentence-BERT计算相似度
        """
        try:
            from sklearn.metrics.pairwise import cosine_similarity

            embeddings = self._model.encode([original, modified])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

            return float(similarity)
        except Exception as e:
            logger.error(f"SBERT similarity calculation failed: {e}")
            return self._calculate_fallback_similarity(original, modified)

    def _calculate_fallback_similarity(self, original: str, modified: str) -> float:
        """
        Calculate similarity using fallback method (word overlap + length)
        使用备用方法计算相似度（词重叠 + 长度）
        """
        # Tokenize
        # 分词
        orig_words = set(original.lower().split())
        mod_words = set(modified.lower().split())

        if not orig_words or not mod_words:
            return 0.0

        # Jaccard similarity
        # Jaccard相似度
        intersection = len(orig_words & mod_words)
        union = len(orig_words | mod_words)
        jaccard = intersection / union if union > 0 else 0

        # Length similarity
        # 长度相似度
        len_orig = len(original)
        len_mod = len(modified)
        len_sim = min(len_orig, len_mod) / max(len_orig, len_mod) if max(len_orig, len_mod) > 0 else 1

        # Word order similarity (simplified)
        # 词序相似度（简化版）
        orig_list = original.lower().split()
        mod_list = modified.lower().split()
        common_words = list(orig_words & mod_words)

        if len(common_words) >= 2:
            # Check if common words appear in similar order
            # 检查共同词是否以相似顺序出现
            orig_positions = {w: i for i, w in enumerate(orig_list) if w in common_words}
            mod_positions = {w: i for i, w in enumerate(mod_list) if w in common_words}

            order_preserved = 0
            for w in common_words:
                if w in orig_positions and w in mod_positions:
                    # Normalize positions
                    # 规范化位置
                    orig_norm = orig_positions[w] / len(orig_list) if orig_list else 0
                    mod_norm = mod_positions[w] / len(mod_list) if mod_list else 0
                    if abs(orig_norm - mod_norm) < 0.3:
                        order_preserved += 1

            order_sim = order_preserved / len(common_words) if common_words else 1
        else:
            order_sim = 1

        # Weighted combination
        # 加权组合
        similarity = (jaccard * 0.5) + (len_sim * 0.2) + (order_sim * 0.3)

        # Boost for high word overlap
        # 高词重叠的加成
        if jaccard > 0.7:
            similarity = min(1.0, similarity + 0.1)

        return similarity

    def validate_batch(
        self,
        pairs: List[tuple]
    ) -> List[SemanticValidationResult]:
        """
        Validate multiple original-modified pairs
        验证多个原始-修改文本对

        Args:
            pairs: List of (original, modified) tuples

        Returns:
            List of validation results
        """
        return [self.validate(orig, mod) for orig, mod in pairs]

    def get_similarity_score(self, original: str, modified: str) -> float:
        """
        Get just the similarity score without full validation
        仅获取相似度分数，不进行完整验证
        """
        return self._calculate_similarity(original, modified)
