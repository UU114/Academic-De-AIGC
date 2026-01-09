"""
Document Layer Orchestrator (Layer 5)
文档层编排器（第5层）

Handles document-level analysis:
- Step 1.1: Structure Analysis (integrates structure_predictability.py)
- Step 1.2: Global Risk Assessment

处理文档级分析：
- 步骤 1.1：结构分析（集成 structure_predictability.py）
- 步骤 1.2：全局风险评估
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple

from src.core.analyzer.layers.base import (
    BaseOrchestrator,
    LayerContext,
    LayerResult,
    LayerLevel,
    RiskLevel,
    DetectionIssue,
)
from src.core.analyzer.structure_predictability import (
    StructurePredictabilityAnalyzer,
    PredictabilityScore,
)

logger = logging.getLogger(__name__)


class DocumentOrchestrator(BaseOrchestrator):
    """
    Layer 5: Document-level orchestrator
    第5层：文档级编排器

    Responsibilities:
    - Detect overall document structure patterns
    - Identify section boundaries and roles
    - Calculate document-level AIGC risk score
    - Integrate structure_predictability.py scoring

    职责：
    - 检测整体文档结构模式
    - 识别章节边界和角色
    - 计算文档级AIGC风险评分
    - 集成 structure_predictability.py 评分
    """

    layer = LayerLevel.DOCUMENT

    def __init__(self):
        super().__init__()
        self.predictability_analyzer = StructurePredictabilityAnalyzer()

    async def analyze(self, context: LayerContext) -> LayerResult:
        """
        Run document-level analysis
        运行文档级分析

        Steps:
        1.1 - Structure Analysis
        1.2 - Global Risk Assessment
        """
        self.logger.info("Starting document layer analysis (Layer 5)")

        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        # Extract paragraphs if not already done
        if not context.paragraphs:
            context.paragraphs = self._extract_paragraphs(context.full_text)

        # Step 1.1: Structure Analysis
        structure_result = await self._analyze_structure(context)
        issues.extend(structure_result["issues"])
        details["structure_analysis"] = structure_result["details"]
        recommendations.extend(structure_result["recommendations"])
        recommendations_zh.extend(structure_result["recommendations_zh"])

        # Step 1.2: Global Risk Assessment
        risk_result = self._assess_global_risk(context, structure_result)
        issues.extend(risk_result["issues"])
        details["global_risk"] = risk_result["details"]
        recommendations.extend(risk_result["recommendations"])
        recommendations_zh.extend(risk_result["recommendations_zh"])

        # Calculate overall risk score for this layer
        risk_score = self._calculate_layer_risk(structure_result, risk_result)
        risk_level = self._calculate_risk_level(risk_score)

        # Update context with document-level information
        context.document_structure = details.get("structure_analysis", {})
        context.document_risk_score = risk_score
        context.document_issues = issues
        updated_context = self._update_context(context)

        self.logger.info(f"Document layer analysis complete. Risk score: {risk_score}")

        return LayerResult(
            layer=self.layer,
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            details=details,
            updated_context=updated_context,
        )

    def _extract_paragraphs(self, text: str) -> List[str]:
        """
        Extract paragraphs from text
        从文本中提取段落
        """
        # Split by double newlines or single newlines with indent
        paragraphs = re.split(r'\n\s*\n', text.strip())

        # Filter out empty paragraphs and very short ones (likely headers)
        paragraphs = [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 50]

        self.logger.debug(f"Extracted {len(paragraphs)} paragraphs")
        return paragraphs

    async def _analyze_structure(self, context: LayerContext) -> Dict[str, Any]:
        """
        Step 1.1: Structure Analysis
        步骤 1.1：结构分析

        Integrates structure_predictability.py for 5-dimension scoring:
        1. Progression Predictability
        2. Function Uniformity
        3. Closure Strength
        4. Length Regularity
        5. Connector Explicitness
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        try:
            # Run structure predictability analysis
            predictability_score = self.predictability_analyzer.analyze(context.paragraphs)

            details["predictability"] = predictability_score.to_dict()
            details["paragraph_count"] = len(context.paragraphs)
            details["total_word_count"] = sum(len(p.split()) for p in context.paragraphs)

            # Generate issues based on predictability dimensions
            issues.extend(self._generate_structure_issues(predictability_score))

            # Add recommendations
            recommendations.extend(predictability_score.recommendations)
            recommendations_zh.extend(predictability_score.recommendations_zh)

        except Exception as e:
            self.logger.error(f"Structure predictability analysis failed: {e}")
            # Fallback to basic analysis
            details["predictability"] = None
            details["error"] = str(e)

            # Basic paragraph length analysis
            para_lengths = [len(p.split()) for p in context.paragraphs]
            if para_lengths:
                details["avg_paragraph_length"] = sum(para_lengths) / len(para_lengths)
                details["paragraph_lengths"] = para_lengths

                # Check for uniform paragraph lengths (AI pattern)
                if len(para_lengths) > 2:
                    import statistics
                    cv = statistics.stdev(para_lengths) / statistics.mean(para_lengths) if statistics.mean(para_lengths) > 0 else 0
                    if cv < 0.2:
                        issues.append(self._create_issue(
                            issue_type="uniform_paragraph_length",
                            description="Paragraph lengths are very uniform, suggesting AI generation",
                            description_zh="段落长度非常均匀，表明可能是AI生成",
                            severity=RiskLevel.MEDIUM,
                            suggestion="Vary paragraph lengths for more natural flow",
                            suggestion_zh="变化段落长度以获得更自然的流程",
                        ))

        return {
            "issues": issues,
            "details": details,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _generate_structure_issues(self, score: PredictabilityScore) -> List[DetectionIssue]:
        """
        Generate issues from predictability score
        根据预测性分数生成问题
        """
        issues = []

        # High progression predictability
        if score.progression_predictability >= 70:
            issues.append(self._create_issue(
                issue_type="high_progression_predictability",
                description=f"Document has highly predictable progression pattern ({score.progression_type})",
                description_zh=f"文档具有高度可预测的推进模式（{score.progression_type}）",
                severity=RiskLevel.HIGH if score.progression_predictability >= 85 else RiskLevel.MEDIUM,
                suggestion="Add non-monotonic elements: digressions, callbacks, or anticipatory references",
                suggestion_zh="添加非单调元素：旁白、回调或预期引用",
                progression_score=score.progression_predictability,
            ))

        # High function uniformity
        if score.function_uniformity >= 70:
            issues.append(self._create_issue(
                issue_type="high_function_uniformity",
                description=f"Paragraph functions are too uniform ({score.function_distribution})",
                description_zh=f"段落功能过于均匀（{score.function_distribution}）",
                severity=RiskLevel.MEDIUM,
                suggestion="Create asymmetric paragraph roles: some longer analysis, some brief transitions",
                suggestion_zh="创建非对称段落角色：一些较长的分析，一些简短的过渡",
                uniformity_score=score.function_uniformity,
            ))

        # Strong closure (too perfect ending)
        if score.closure_strength >= 80:
            issues.append(self._create_issue(
                issue_type="strong_closure",
                description=f"Document ending is too strong/summarizing ({score.closure_type})",
                description_zh=f"文档结尾过于强烈/总结性（{score.closure_type}）",
                severity=RiskLevel.LOW,
                suggestion="Consider a more open or reflective ending instead of a perfect summary",
                suggestion_zh="考虑更开放或反思性的结尾，而不是完美的总结",
                closure_score=score.closure_strength,
            ))

        # High length regularity
        if score.length_regularity >= 70:
            issues.append(self._create_issue(
                issue_type="high_length_regularity",
                description="Paragraph lengths are too regular/uniform",
                description_zh="段落长度过于规则/均匀",
                severity=RiskLevel.MEDIUM,
                suggestion="Vary paragraph lengths: mix short (2-3 sentences) with longer (6-8 sentences)",
                suggestion_zh="变化段落长度：混合短段落（2-3句）和长段落（6-8句）",
                regularity_score=score.length_regularity,
            ))

        # High connector explicitness
        if score.connector_explicitness >= 70:
            issues.append(self._create_issue(
                issue_type="high_connector_explicitness",
                description="Too many explicit connectors (Furthermore, Moreover, Additionally...)",
                description_zh="显式连接词过多（Furthermore, Moreover, Additionally...）",
                severity=RiskLevel.HIGH if score.connector_explicitness >= 85 else RiskLevel.MEDIUM,
                suggestion="Replace explicit connectors with lexical echo and implicit logical flow",
                suggestion_zh="用词汇回声和隐式逻辑流替换显式连接词",
                connector_score=score.connector_explicitness,
                lexical_echo_score=score.lexical_echo_score,
            ))

        return issues

    def _assess_global_risk(
        self,
        context: LayerContext,
        structure_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 1.2: Global Risk Assessment
        步骤 1.2：全局风险评估

        Calculate document-level risk and determine which lower layers need attention.
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        # Aggregate risk indicators
        predictability = structure_result.get("details", {}).get("predictability", {})
        total_score = predictability.get("total_score", 50) if predictability else 50

        # Document-level statistics
        para_count = len(context.paragraphs)
        total_words = sum(len(p.split()) for p in context.paragraphs)

        details["total_paragraphs"] = para_count
        details["total_words"] = total_words
        details["avg_words_per_paragraph"] = total_words / para_count if para_count > 0 else 0
        details["structure_risk_score"] = total_score

        # Determine which layers need priority attention
        layers_needing_attention = []

        if total_score >= 60:
            layers_needing_attention.append({
                "layer": "section",
                "reason": "High structure predictability needs section-level fixes",
                "reason_zh": "高结构可预测性需要章节级修复",
            })

        if predictability and predictability.get("connector_explicitness", 0) >= 60:
            layers_needing_attention.append({
                "layer": "lexical",
                "reason": "Connector issues need lexical-level attention",
                "reason_zh": "连接词问题需要词汇级关注",
            })

        details["layers_needing_attention"] = layers_needing_attention

        # Add overall assessment issue if high risk
        if total_score >= 70:
            issues.append(self._create_issue(
                issue_type="high_document_risk",
                description=f"Document has high AIGC detection risk (score: {total_score})",
                description_zh=f"文档具有高AIGC检测风险（分数：{total_score}）",
                severity=RiskLevel.HIGH,
                suggestion="Consider restructuring the document with more human-like patterns",
                suggestion_zh="考虑用更像人类的模式重新构建文档",
                risk_score=total_score,
            ))
            recommendations.append("Prioritize section-level and paragraph-level restructuring")
            recommendations_zh.append("优先进行章节级和段落级重组")

        return {
            "issues": issues,
            "details": details,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _calculate_layer_risk(
        self,
        structure_result: Dict[str, Any],
        risk_result: Dict[str, Any]
    ) -> int:
        """
        Calculate overall risk score for document layer
        计算文档层的整体风险分数
        """
        predictability = structure_result.get("details", {}).get("predictability", {})
        total_score = predictability.get("total_score", 50) if predictability else 50

        # Weight structure issues
        structure_issues = len(structure_result.get("issues", []))
        issue_penalty = min(structure_issues * 5, 20)  # Max 20 points from issues

        final_score = min(100, total_score + issue_penalty)
        return final_score
