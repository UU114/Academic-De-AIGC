"""
Base classes and data structures for 5-Layer Detection Architecture
5层检测架构的基类和数据结构

Design Principles:
1. Coarse to Fine: Document → Section → Paragraph → Sentence → Lexical
2. Context Passing: Each layer receives context from upper layers
3. Flexible Steps: Steps within layers are dynamically determined
4. Sentence-in-Paragraph: Sentence analysis must be in paragraph context

设计原则：
1. 从粗到细：文档 → 章节 → 段落 → 句子 → 词汇
2. 上下文传递：每层接收上层传递的上下文
3. 灵活步骤：层内步骤根据检测问题动态调整
4. 句子段落化：句子分析必须在段落上下文中进行
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LayerLevel(Enum):
    """Layer levels in the detection hierarchy"""
    DOCUMENT = 5   # Layer 5: Document level (文章层)
    SECTION = 4    # Layer 4: Section level (章节层)
    PARAGRAPH = 3  # Layer 3: Paragraph level (段落层)
    SENTENCE = 2   # Layer 2: Sentence level (句子层)
    LEXICAL = 1    # Layer 1: Lexical level (词汇层)


class RiskLevel(Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class DetectionIssue:
    """
    Represents a detected issue at any layer
    表示在任何层检测到的问题
    """
    type: str                      # Issue type identifier
    description: str               # English description
    description_zh: str            # Chinese description
    severity: RiskLevel            # low, medium, high
    layer: LayerLevel              # Which layer detected this
    position: Optional[str] = None # Position reference (e.g., "3.2(1)" or sentence index)
    suggestion: str = ""           # Suggestion for fix
    suggestion_zh: str = ""        # Chinese suggestion
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": self.type,
            "description": self.description,
            "description_zh": self.description_zh,
            "severity": self.severity.value,
            "layer": self.layer.value,
            "position": self.position,
            "suggestion": self.suggestion,
            "suggestion_zh": self.suggestion_zh,
            "details": self.details,
        }


@dataclass
class LayerContext:
    """
    Context passed between layers in the detection pipeline
    在检测流水线中各层之间传递的上下文

    Upper layers add information that lower layers can use:
    - Document layer adds: sections, overall structure
    - Section layer adds: section boundaries, roles, transitions
    - Paragraph layer adds: paragraph roles, coherence info
    - Sentence layer adds: sentence roles, context for lexical
    """
    # Raw input
    full_text: str = ""                               # Full document text (optional for lower layers)
    paragraphs: List[str] = field(default_factory=list)  # Extracted paragraphs

    # Document layer (Layer 5) context
    document_structure: Optional[Dict[str, Any]] = None    # Section hierarchy
    document_risk_score: int = 0                           # 0-100
    document_issues: List[DetectionIssue] = field(default_factory=list)

    # Section layer (Layer 4) context
    sections: List[Dict[str, Any]] = field(default_factory=list)  # Section info
    section_boundaries: List[int] = field(default_factory=list)    # Paragraph indices
    section_transitions: List[Dict[str, Any]] = field(default_factory=list)

    # Paragraph layer (Layer 3) context
    paragraph_roles: List[str] = field(default_factory=list)       # Role per paragraph
    paragraph_coherence: List[float] = field(default_factory=list) # Coherence scores
    paragraph_anchor_density: List[float] = field(default_factory=list)
    paragraph_sentence_lengths: List[List[int]] = field(default_factory=list)  # Per paragraph

    # Sentence layer (Layer 2) context - MUST include paragraph context
    sentences: List[str] = field(default_factory=list)             # All sentences
    sentence_to_paragraph: List[int] = field(default_factory=list) # Map sentence to para
    sentence_roles: List[str] = field(default_factory=list)        # Role per sentence

    # Processing metadata
    current_layer: LayerLevel = LayerLevel.DOCUMENT
    processed_layers: List[LayerLevel] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "full_text_length": len(self.full_text),
            "paragraph_count": len(self.paragraphs),
            "document_risk_score": self.document_risk_score,
            "document_issues_count": len(self.document_issues),
            "section_count": len(self.sections),
            "current_layer": self.current_layer.value,
            "processed_layers": [l.value for l in self.processed_layers],
        }


@dataclass
class LayerResult:
    """
    Result from a layer's analysis
    层分析的结果
    """
    layer: LayerLevel                               # Which layer produced this
    risk_score: int = 0                             # Layer-specific risk score (0-100)
    risk_level: RiskLevel = RiskLevel.LOW           # Overall risk level
    issues: List[DetectionIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    recommendations_zh: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    # Updated context to pass to next layer
    updated_context: Optional[LayerContext] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "layer": self.layer.value,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "issues": [i.to_dict() for i in self.issues],
            "recommendations": self.recommendations,
            "recommendations_zh": self.recommendations_zh,
            "details": self.details,
        }


class BaseOrchestrator(ABC):
    """
    Base class for all layer orchestrators
    所有层编排器的基类

    Each orchestrator:
    1. Receives context from upper layer
    2. Runs detection steps for its layer
    3. Returns result with updated context for lower layer
    """

    layer: LayerLevel = LayerLevel.DOCUMENT

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def analyze(self, context: LayerContext) -> LayerResult:
        """
        Run analysis for this layer
        运行本层分析

        Args:
            context: Context from upper layer

        Returns:
            LayerResult with issues found and updated context
        """
        pass

    def _create_issue(
        self,
        issue_type: str,
        description: str,
        description_zh: str,
        severity: RiskLevel,
        position: Optional[str] = None,
        suggestion: str = "",
        suggestion_zh: str = "",
        **details
    ) -> DetectionIssue:
        """Helper to create a DetectionIssue with this layer's level"""
        return DetectionIssue(
            type=issue_type,
            description=description,
            description_zh=description_zh,
            severity=severity,
            layer=self.layer,
            position=position,
            suggestion=suggestion,
            suggestion_zh=suggestion_zh,
            details=details,
        )

    def _calculate_risk_level(self, score: int) -> RiskLevel:
        """Calculate risk level from score"""
        if score >= 60:
            return RiskLevel.HIGH
        elif score >= 30:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _update_context(self, context: LayerContext) -> LayerContext:
        """Mark this layer as processed in context"""
        context.processed_layers.append(self.layer)
        return context
