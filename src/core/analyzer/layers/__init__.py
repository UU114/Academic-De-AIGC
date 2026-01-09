"""
5-Layer Detection Architecture Orchestrators
5层检测架构编排器

Layer 5: Document (文章层) - document_orchestrator
Layer 4: Section (章节层) - section_analyzer
Layer 3: Paragraph (段落层) - paragraph_orchestrator
Layer 2: Sentence (句子层) - sentence_orchestrator
Layer 1: Lexical (词汇层) - lexical_orchestrator

Each layer receives context from upper layers and passes enriched context to lower layers.
每层从上层接收上下文，并将增强的上下文传递给下层。
"""

from src.core.analyzer.layers.base import (
    LayerContext,
    LayerResult,
    BaseOrchestrator,
    LayerLevel,
    RiskLevel,
    DetectionIssue,
)
from src.core.analyzer.layers.document_orchestrator import DocumentOrchestrator
from src.core.analyzer.layers.section_analyzer import SectionAnalyzer
from src.core.analyzer.layers.paragraph_orchestrator import ParagraphOrchestrator
from src.core.analyzer.layers.sentence_orchestrator import SentenceOrchestrator
from src.core.analyzer.layers.lexical_orchestrator import LexicalOrchestrator

__all__ = [
    # Base classes and data structures
    "LayerContext",
    "LayerResult",
    "BaseOrchestrator",
    "LayerLevel",
    "RiskLevel",
    "DetectionIssue",
    # Layer orchestrators
    "DocumentOrchestrator",
    "SectionAnalyzer",
    "ParagraphOrchestrator",
    "SentenceOrchestrator",
    "LexicalOrchestrator",
]
