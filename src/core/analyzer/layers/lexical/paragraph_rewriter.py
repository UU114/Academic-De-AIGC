"""
Step 5.4: LLM Paragraph-Level Rewriting
步骤5.4：LLM段落级改写

Core rewriting functionality:
- Batch rewrite by paragraph unit
- Pass AIGC issue analysis to LLM
- Pass human feature targets
- Protect locked terms
- Apply academic writing norms
- Generate Track A (LLM) suggestions

核心改写功能：
- 按段落为单位批量改写
- 向LLM传入AIGC问题分析
- 传入人类特征目标
- 保护锁定词汇
- 应用学术写作规范
- 生成轨道A（LLM）建议
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from src.config import get_settings
from src.core.analyzer.layers.lexical.context_preparation import (
    LexicalContext,
    ParagraphLexicalInfo,
)
from src.core.analyzer.layers.lexical.fingerprint_detector import (
    FingerprintDetectionResult,
    ParagraphFingerprintStats,
)
from src.core.analyzer.layers.lexical.human_feature_analyzer import (
    HumanFeatureAnalysisResult,
    InjectionPoint,
)
from src.core.analyzer.layers.lexical.candidate_generator import (
    ReplacementCandidateResult,
    ReplacementCandidate,
)

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class RewriteChange:
    """A single change made during rewriting"""
    original: str
    replacement: str
    reason: str
    reason_zh: str
    change_type: str  # aigc_removal, human_injection, style_adjustment


@dataclass
class ParagraphRewriteResult:
    """Result for a single paragraph rewrite"""
    paragraph_index: int
    original_text: str
    rewritten_text: str
    changes: List[RewriteChange]
    aigc_removed: List[str]
    human_features_added: List[str]
    locked_terms_preserved: bool
    semantic_similarity_estimate: float
    risk_before: int
    risk_after_estimate: int


@dataclass
class LLMRewriteResult:
    """Complete LLM rewrite result"""
    paragraphs: List[ParagraphRewriteResult]
    total_paragraphs: int
    paragraphs_rewritten: int
    total_changes: int
    aigc_removed_count: int
    human_features_added_count: int
    all_locked_terms_preserved: bool
    recommendations: List[str]
    recommendations_zh: List[str]


class LLMParagraphRewriter:
    """
    Step 5.4: LLM Paragraph-Level Rewriter
    步骤5.4：LLM段落级改写器
    """

    # Style guides for different colloquialism levels
    STYLE_GUIDES = {
        "academic": """
Style: Academic (Formal)
- Use formal academic register
- Prefer precise, technical vocabulary
- Use passive voice where appropriate
- FORBIDDEN: First-person pronouns (I, we, my, our)
- USE INSTEAD: "this study", "the analysis", "the findings"
- Hedging language appropriate: "suggests", "indicates", "may"
""",
        "moderate": """
Style: Academic Moderate
- Use formal vocabulary with some flexibility
- Balance passive and active voice
- FORBIDDEN: First-person pronouns (I, we, my, our) unless explicitly required
- USE INSTEAD: "this research", "the current study"
- Clear but sophisticated sentence structures
""",
        "casual": """
Style: Semi-formal
- Mix of academic and common vocabulary
- Prefer active voice for clarity
- Contractions acceptable occasionally
- Direct statements preferred
""",
    }

    def __init__(self):
        """Initialize the paragraph rewriter"""
        pass

    async def rewrite(
        self,
        context: LexicalContext,
        fingerprint_result: FingerprintDetectionResult,
        human_feature_result: Optional[HumanFeatureAnalysisResult] = None,
        candidate_result: Optional[ReplacementCandidateResult] = None,
    ) -> LLMRewriteResult:
        """
        Rewrite paragraphs to reduce AIGC fingerprints and enhance human features
        改写段落以减少AIGC指纹并增强人类特征

        Args:
            context: Lexical context from Step 5.0
            fingerprint_result: Fingerprint detection from Step 5.1
            human_feature_result: Human feature analysis from Step 5.2 (optional)
            candidate_result: Replacement candidates from Step 5.3 (optional)

        Returns:
            LLMRewriteResult with all rewritten paragraphs
        """
        logger.info("Step 5.4: Starting paragraph-level rewriting")

        paragraph_results: List[ParagraphRewriteResult] = []
        style_level = self._get_style_level(context.colloquialism_level)

        # Group data by paragraph
        para_fingerprints = fingerprint_result.paragraph_stats
        para_candidates = self._group_candidates_by_paragraph(candidate_result)
        para_injections = self._group_injections_by_paragraph(human_feature_result)

        # Process each paragraph
        for para in context.paragraphs:
            para_stats = para_fingerprints.get(para.index)

            # Determine if paragraph needs rewriting
            needs_rewrite = self._needs_rewriting(para_stats)

            if needs_rewrite:
                # Rewrite with LLM
                result = await self._rewrite_paragraph_llm(
                    para,
                    para_stats,
                    para_candidates.get(para.index, []),
                    para_injections.get(para.index, []),
                    context,
                    style_level,
                )
            else:
                # Apply rule-based replacements only
                result = self._rewrite_paragraph_rules(
                    para,
                    para_candidates.get(para.index, []),
                    context,
                )

            paragraph_results.append(result)

        # Calculate overall statistics
        total_changes = sum(len(r.changes) for r in paragraph_results)
        aigc_removed = sum(len(r.aigc_removed) for r in paragraph_results)
        human_added = sum(len(r.human_features_added) for r in paragraph_results)
        all_preserved = all(r.locked_terms_preserved for r in paragraph_results)
        paragraphs_rewritten = sum(1 for r in paragraph_results if r.changes)

        recommendations, recommendations_zh = self._generate_recommendations(
            paragraph_results, fingerprint_result
        )

        result = LLMRewriteResult(
            paragraphs=paragraph_results,
            total_paragraphs=len(paragraph_results),
            paragraphs_rewritten=paragraphs_rewritten,
            total_changes=total_changes,
            aigc_removed_count=aigc_removed,
            human_features_added_count=human_added,
            all_locked_terms_preserved=all_preserved,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
        )

        logger.info(
            f"Step 5.4 complete: {paragraphs_rewritten}/{len(paragraph_results)} "
            f"paragraphs rewritten, {total_changes} changes made"
        )

        return result

    def _get_style_level(self, colloquialism_level: int) -> str:
        """Map colloquialism level to style category"""
        if colloquialism_level <= 2:
            return "academic"
        elif colloquialism_level <= 6:
            return "moderate"
        else:
            return "casual"

    def _needs_rewriting(self, para_stats: Optional[ParagraphFingerprintStats]) -> bool:
        """Determine if a paragraph needs LLM rewriting"""
        if not para_stats:
            return False
        # Rewrite if high risk or has Type A fingerprints
        return (
            para_stats.risk_level in ("critical", "high") or
            para_stats.type_a_count > 0 or
            para_stats.density > 3.0
        )

    def _group_candidates_by_paragraph(
        self,
        candidate_result: Optional[ReplacementCandidateResult]
    ) -> Dict[int, List[ReplacementCandidate]]:
        """Group replacement candidates by paragraph"""
        if not candidate_result:
            return {}

        grouped = {}
        for candidate in candidate_result.candidates:
            para_idx = candidate.paragraph_index
            if para_idx not in grouped:
                grouped[para_idx] = []
            grouped[para_idx].append(candidate)
        return grouped

    def _group_injections_by_paragraph(
        self,
        human_feature_result: Optional[HumanFeatureAnalysisResult]
    ) -> Dict[int, List[InjectionPoint]]:
        """Group injection points by paragraph"""
        if not human_feature_result:
            return {}

        grouped = {}
        for point in human_feature_result.injection_points:
            para_idx = point.paragraph_index
            if para_idx not in grouped:
                grouped[para_idx] = []
            grouped[para_idx].append(point)
        return grouped

    async def _rewrite_paragraph_llm(
        self,
        para: ParagraphLexicalInfo,
        para_stats: Optional[ParagraphFingerprintStats],
        candidates: List[ReplacementCandidate],
        injections: List[InjectionPoint],
        context: LexicalContext,
        style_level: str,
    ) -> ParagraphRewriteResult:
        """Rewrite a paragraph using LLM"""
        # Build prompt
        prompt = self._build_rewrite_prompt(
            para, para_stats, candidates, injections, context, style_level
        )

        try:
            # Call LLM
            response = await self._call_llm(prompt)

            # Parse response
            result = self._parse_llm_response(response, para, para_stats)

            # Verify locked terms preserved
            result.locked_terms_preserved = self._verify_locked_terms(
                result.rewritten_text, context.locked_terms
            )

            return result

        except Exception as e:
            logger.error(f"LLM rewrite failed for paragraph {para.index}: {e}")
            # Fallback to rule-based
            return self._rewrite_paragraph_rules(para, candidates, context)

    def _rewrite_paragraph_rules(
        self,
        para: ParagraphLexicalInfo,
        candidates: List[ReplacementCandidate],
        context: LexicalContext,
    ) -> ParagraphRewriteResult:
        """Apply rule-based replacements only (Track B fallback)"""
        text = para.text
        changes: List[RewriteChange] = []
        aigc_removed: List[str] = []

        # Apply each candidate replacement
        for candidate in candidates:
            if candidate.recommended:
                # Case-insensitive replacement
                pattern = re.compile(
                    r'\b' + re.escape(candidate.original) + r'\b',
                    re.IGNORECASE
                )

                def replace_match(m):
                    # Preserve original case
                    orig = m.group(0)
                    rep = candidate.recommended.replacement
                    if orig[0].isupper():
                        return rep.capitalize()
                    return rep

                new_text = pattern.sub(replace_match, text)

                if new_text != text:
                    changes.append(RewriteChange(
                        original=candidate.original,
                        replacement=candidate.recommended.replacement,
                        reason=candidate.recommended.reason,
                        reason_zh=candidate.recommended.reason_zh,
                        change_type="aigc_removal",
                    ))
                    aigc_removed.append(candidate.original)
                    text = new_text

        # Verify locked terms
        locked_preserved = self._verify_locked_terms(text, context.locked_terms)

        return ParagraphRewriteResult(
            paragraph_index=para.index,
            original_text=para.text,
            rewritten_text=text,
            changes=changes,
            aigc_removed=aigc_removed,
            human_features_added=[],
            locked_terms_preserved=locked_preserved,
            semantic_similarity_estimate=0.98 if changes else 1.0,
            risk_before=0,
            risk_after_estimate=0,
        )

    def _build_rewrite_prompt(
        self,
        para: ParagraphLexicalInfo,
        para_stats: Optional[ParagraphFingerprintStats],
        candidates: List[ReplacementCandidate],
        injections: List[InjectionPoint],
        context: LexicalContext,
        style_level: str,
    ) -> str:
        """Build the LLM rewrite prompt"""
        # Format AIGC issues
        aigc_issues = []
        if para_stats:
            for match in para_stats.matches:
                aigc_issues.append(f"- {match.fingerprint_type.value}: '{match.word}'")

        # Format candidates
        type_a_list = [c.original for c in candidates if c.original_type == "type_a"]
        type_b_list = [c.original for c in candidates if c.original_type == "type_b"]
        phrase_list = [c.original for c in candidates if c.original_type == "phrase"]

        # Format human feature targets
        human_targets = []
        for inj in injections:
            human_targets.append(
                f"- {inj.feature_type}: Consider adding {', '.join(inj.suggested_features)}"
            )

        prompt = f"""## TASK: Rewrite paragraph to reduce AI detection while maintaining academic rigor

## Original Paragraph
{para.text}

## AIGC Issues Detected (MUST FIX):
{chr(10).join(aigc_issues) if aigc_issues else "No specific issues"}

## Type A Words (MUST REPLACE - Dead Giveaways):
{', '.join(type_a_list) if type_a_list else "None"}

## Type B Words (REDUCE - Academic Clichés):
{', '.join(type_b_list) if type_b_list else "None"}

## Phrases to Rewrite:
{', '.join(phrase_list) if phrase_list else "None"}

## Human Feature Enhancement Targets:
{chr(10).join(human_targets) if human_targets else "No specific targets"}

## PROTECTED TERMS (DO NOT MODIFY):
{', '.join(context.locked_terms) if context.locked_terms else "None"}

## Style Level: {style_level}
{self.STYLE_GUIDES.get(style_level, self.STYLE_GUIDES["moderate"])}

## CRITICAL RULES:
1. Replace ALL Type A words with appropriate alternatives
2. Reduce Type B word density by varying vocabulary
3. Rewrite AI-typical phrases more naturally
4. Add human writing features where appropriate (hedging, academic verbs)
5. NEVER modify protected/locked terms
6. Maintain the EXACT same meaning
7. Keep citation formats intact

## Response (JSON only, no markdown):
{{
  "rewritten_paragraph": "the rewritten paragraph text",
  "changes": [
    {{"original": "word", "replacement": "new word", "reason": "why", "reason_zh": "原因", "type": "aigc_removal|human_injection|style_adjustment"}}
  ],
  "aigc_removed": ["list", "of", "removed", "words"],
  "human_features_added": ["list", "of", "added", "features"],
  "locked_terms_preserved": true,
  "semantic_similarity_estimate": 0.92
}}"""

        return prompt

    async def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM provider"""
        try:
            if settings.llm_provider == "volcengine" and settings.volcengine_api_key:
                return await self._call_volcengine(prompt)
            elif settings.llm_provider == "gemini" and settings.gemini_api_key:
                return await self._call_gemini(prompt)
            elif settings.llm_provider == "deepseek" and settings.deepseek_api_key:
                return await self._call_deepseek(prompt)
            elif settings.volcengine_api_key:
                return await self._call_volcengine(prompt)
            elif settings.gemini_api_key:
                return await self._call_gemini(prompt)
            elif settings.deepseek_api_key:
                return await self._call_deepseek(prompt)
            else:
                raise ValueError("No LLM API configured")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    async def _call_volcengine(self, prompt: str) -> str:
        """Call Volcengine API"""
        import httpx

        async with httpx.AsyncClient(
            base_url=settings.volcengine_base_url,
            headers={
                "Authorization": f"Bearer {settings.volcengine_api_key}",
                "Content-Type": "application/json"
            },
            timeout=120.0,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": settings.volcengine_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": settings.llm_max_tokens,
                "temperature": settings.llm_temperature
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
            config={
                "max_output_tokens": settings.llm_max_tokens,
                "temperature": settings.llm_temperature
            }
        )
        return response.text

    async def _call_deepseek(self, prompt: str) -> str:
        """Call DeepSeek API"""
        import httpx

        async with httpx.AsyncClient(
            base_url=settings.deepseek_base_url,
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json"
            },
            timeout=120.0,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": settings.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": settings.llm_max_tokens,
                "temperature": settings.llm_temperature
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def _parse_llm_response(
        self,
        response: str,
        para: ParagraphLexicalInfo,
        para_stats: Optional[ParagraphFingerprintStats],
    ) -> ParagraphRewriteResult:
        """Parse LLM response JSON"""
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()

            data = json.loads(response)

            changes = [
                RewriteChange(
                    original=c.get("original", ""),
                    replacement=c.get("replacement", ""),
                    reason=c.get("reason", ""),
                    reason_zh=c.get("reason_zh", ""),
                    change_type=c.get("type", "aigc_removal"),
                )
                for c in data.get("changes", [])
            ]

            return ParagraphRewriteResult(
                paragraph_index=para.index,
                original_text=para.text,
                rewritten_text=data.get("rewritten_paragraph", para.text),
                changes=changes,
                aigc_removed=data.get("aigc_removed", []),
                human_features_added=data.get("human_features_added", []),
                locked_terms_preserved=data.get("locked_terms_preserved", True),
                semantic_similarity_estimate=data.get("semantic_similarity_estimate", 0.9),
                risk_before=para_stats.total_risk_score if para_stats else 0,
                risk_after_estimate=int(para_stats.total_risk_score * 0.3) if para_stats else 0,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            # Return original text
            return ParagraphRewriteResult(
                paragraph_index=para.index,
                original_text=para.text,
                rewritten_text=para.text,
                changes=[],
                aigc_removed=[],
                human_features_added=[],
                locked_terms_preserved=True,
                semantic_similarity_estimate=1.0,
                risk_before=para_stats.total_risk_score if para_stats else 0,
                risk_after_estimate=para_stats.total_risk_score if para_stats else 0,
            )

    def _verify_locked_terms(self, text: str, locked_terms: List[str]) -> bool:
        """Verify all locked terms are preserved in text"""
        text_lower = text.lower()
        for term in locked_terms:
            if term.lower() not in text_lower:
                logger.warning(f"Locked term '{term}' not found in rewritten text")
                return False
        return True

    def _generate_recommendations(
        self,
        results: List[ParagraphRewriteResult],
        fingerprint_result: FingerprintDetectionResult,
    ) -> Tuple[List[str], List[str]]:
        """Generate recommendations after rewriting"""
        recs = []
        recs_zh = []

        # Check for remaining issues
        not_preserved = [r for r in results if not r.locked_terms_preserved]
        if not_preserved:
            recs.append(
                f"WARNING: {len(not_preserved)} paragraph(s) may have modified locked terms - review required"
            )
            recs_zh.append(
                f"警告：{len(not_preserved)} 个段落可能修改了锁定词汇 - 需要审查"
            )

        # Success metrics
        total_aigc_removed = sum(len(r.aigc_removed) for r in results)
        total_human_added = sum(len(r.human_features_added) for r in results)

        if total_aigc_removed > 0:
            recs.append(
                f"Successfully removed {total_aigc_removed} AIGC fingerprint(s)"
            )
            recs_zh.append(
                f"成功移除 {total_aigc_removed} 个AIGC指纹"
            )

        if total_human_added > 0:
            recs.append(
                f"Added {total_human_added} human writing feature(s)"
            )
            recs_zh.append(
                f"添加了 {total_human_added} 个人类写作特征"
            )

        return recs, recs_zh

    def get_rewrite_summary(self, result: LLMRewriteResult) -> Dict[str, Any]:
        """Get summary for API response"""
        return {
            "total_paragraphs": result.total_paragraphs,
            "paragraphs_rewritten": result.paragraphs_rewritten,
            "total_changes": result.total_changes,
            "aigc_removed_count": result.aigc_removed_count,
            "human_features_added_count": result.human_features_added_count,
            "all_locked_terms_preserved": result.all_locked_terms_preserved,
            "paragraphs": [
                {
                    "index": p.paragraph_index,
                    "original": p.original_text[:200] + "..." if len(p.original_text) > 200 else p.original_text,
                    "rewritten": p.rewritten_text[:200] + "..." if len(p.rewritten_text) > 200 else p.rewritten_text,
                    "changes_count": len(p.changes),
                    "aigc_removed": p.aigc_removed,
                    "human_features_added": p.human_features_added,
                    "semantic_similarity": p.semantic_similarity_estimate,
                    "locked_preserved": p.locked_terms_preserved,
                }
                for p in result.paragraphs
            ],
            "recommendations": result.recommendations,
            "recommendations_zh": result.recommendations_zh,
        }
