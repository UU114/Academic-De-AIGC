"""
Dynamic Prompt Builder - Assembles LLM prompts based on diagnosis results
动态提示词构建器 - 根据诊断结果组装LLM提示词

Part of DEAI Engine 2.0 - Dynamic Prompt Generation
DEAI引擎2.0的一部分 - 动态提示词生成

This module generates targeted prompts based on specific issues detected in the text,
rather than using one-size-fits-all prompts.
此模块根据文本中检测到的具体问题生成针对性提示词，而不是使用一刀切的提示词。
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class IssueType(Enum):
    """Types of issues that require specific prompt strategies"""
    P0_FINGERPRINT = "p0_fingerprint"  # Dead giveaway words (delve, tapestry)
    P1_FINGERPRINT = "p1_fingerprint"  # AI clichés (crucial, pivotal)
    SYNTACTIC_VOID = "syntactic_void"  # Empty but flowery language
    LINEAR_LOGIC = "linear_logic"  # Too linear progression
    LOW_ANCHOR_DENSITY = "low_anchor_density"  # Lacks specific evidence
    EXPLICIT_CONNECTOR = "explicit_connector"  # Furthermore, Moreover
    UNIFORM_LENGTH = "uniform_length"  # All sentences same length
    FORMULAIC_OPENING = "formulaic_opening"  # "It is important to note..."
    PREDICTABLE_STRUCTURE = "predictable_structure"  # Too symmetric


@dataclass
class DiagnosedIssue:
    """
    Represents a diagnosed issue in the text
    表示文本中诊断出的问题
    """
    issue_type: IssueType
    severity: str  # high, medium, low
    matched_text: str
    position: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptComponents:
    """
    Components for building a prompt
    构建提示词的组件
    """
    task_instruction: str
    detected_issues: List[str]
    specific_guidelines: List[str]
    avoid_list: List[str]
    output_requirements: List[str]


class PromptBuilder:
    """
    Dynamic prompt builder that generates targeted prompts based on diagnosis
    根据诊断生成针对性提示词的动态提示词构建器
    """

    # Issue-specific prompt strategies
    # 针对特定问题的提示词策略
    ISSUE_STRATEGIES = {
        IssueType.P0_FINGERPRINT: {
            "instruction": "Replace the AI fingerprint word with a concrete, human-like alternative",
            "instruction_zh": "用具体的、人类化的替代词替换AI指纹词",
            "guidelines": [
                "Replace '{word}' with a specific action verb describing the actual methodology",
                "Avoid flowery or abstract language - be direct",
                "Use common academic vocabulary that humans naturally use"
            ],
            "avoid": [
                "delve", "tapestry", "realm", "plethora", "myriad", "elucidate",
                "henceforth", "aforementioned", "multifaceted", "inextricably"
            ],
            "priority": 1
        },
        IssueType.P1_FINGERPRINT: {
            "instruction": "Replace overused AI cliché with simpler, more natural phrasing",
            "instruction_zh": "用更简单、更自然的措辞替换过度使用的AI套话",
            "guidelines": [
                "Replace '{word}' with a more natural, everyday academic term",
                "Prefer simple words over complex ones",
                "Match the formality level of the surrounding text"
            ],
            "avoid": [
                "crucial", "pivotal", "paramount", "holistic", "comprehensive",
                "underscore", "foster", "noteworthy", "groundbreaking"
            ],
            "priority": 2
        },
        IssueType.SYNTACTIC_VOID: {
            "instruction": "Rewrite to state specific findings instead of vague generalizations",
            "instruction_zh": "改写为具体发现而非模糊概括",
            "guidelines": [
                "The sentence '{text}' is syntactically complex but semantically empty",
                "Replace abstract phrases with concrete statements",
                "Include specific data, numbers, or examples where possible",
                "If no specific content is available, use placeholders like [DATA] or [SPECIFIC FINDING]"
            ],
            "avoid": [
                "underscores the significance of", "plays a pivotal role in",
                "serves as a testament to", "in the comprehensive landscape of"
            ],
            "priority": 1
        },
        IssueType.LINEAR_LOGIC: {
            "instruction": "Reorganize using contrastive or causal structure instead of linear list",
            "instruction_zh": "使用对比或因果结构重组，而非线性列举",
            "guidelines": [
                "Break the 'First... Second... Third...' pattern",
                "Use 'however', 'despite', 'although' to create contrast",
                "Show cause-and-effect relationships instead of simple listing",
                "Consider combining points that have logical relationships"
            ],
            "avoid": [
                "Firstly", "Secondly", "Thirdly", "Finally",
                "First,", "Second,", "Third,"
            ],
            "priority": 2
        },
        IssueType.LOW_ANCHOR_DENSITY: {
            "instruction": "Add specific evidence placeholders where concrete data should appear",
            "instruction_zh": "在应该出现具体数据的位置添加证据占位符",
            "guidelines": [
                "This paragraph lacks specific evidence - it reads like AI filler",
                "Insert placeholders like [X%], [N participants], [specific value]",
                "Add references to specific studies: [Author, Year]",
                "Include concrete examples: [specific case/example]",
                "The goal is to mark where human evidence needs to be added"
            ],
            "avoid": [],
            "priority": 3
        },
        IssueType.EXPLICIT_CONNECTOR: {
            "instruction": "Remove explicit connector and create natural flow using semantic echo",
            "instruction_zh": "移除显性连接词，使用语义回声创建自然流转",
            "guidelines": [
                "Remove the connector '{word}' at sentence start",
                "Start with a key concept from the previous sentence to create natural flow",
                "Use 'This [concept]...' or 'Such [finding]...' patterns",
                "Let the logical connection be implicit rather than explicit"
            ],
            "avoid": [
                "Furthermore", "Moreover", "Additionally", "However",
                "Nevertheless", "Consequently", "Therefore"
            ],
            "priority": 2
        },
        IssueType.UNIFORM_LENGTH: {
            "instruction": "Vary sentence length to create natural rhythm",
            "instruction_zh": "变化句子长度以创建自然节奏",
            "guidelines": [
                "Break one long sentence into shorter ones, or combine short ones",
                "Aim for a mix: short (5-10 words), medium (15-20), long (25+)",
                "Use short sentences for emphasis on key points",
                "Use longer sentences for complex explanations"
            ],
            "avoid": [],
            "priority": 3
        },
        IssueType.FORMULAIC_OPENING: {
            "instruction": "Delete the filler phrase and start directly with the main point",
            "instruction_zh": "删除填充短语，直接从要点开始",
            "guidelines": [
                "Remove '{text}' entirely",
                "Start the sentence with the actual subject or finding",
                "Capitalize the first letter of what remains",
                "The meaning should be preserved but more direct"
            ],
            "avoid": [
                "It is important to note that", "It should be noted that",
                "It is worth mentioning that", "It is crucial to understand that"
            ],
            "priority": 1
        },
        IssueType.PREDICTABLE_STRUCTURE: {
            "instruction": "Break the symmetric structure by varying paragraph depth and focus",
            "instruction_zh": "通过变化段落深度和重点打破对称结构",
            "guidelines": [
                "Vary the length of paragraphs - some can be much shorter or longer",
                "Not every section needs equal treatment",
                "Some points deserve deep analysis, others can be brief",
                "Consider merging related short sections or splitting complex ones"
            ],
            "avoid": [],
            "priority": 3
        }
    }

    # Base prompt template
    # 基础提示词模板
    BASE_TEMPLATE = """You are an academic writing advisor helping to make text appear more naturally human-written while maintaining academic quality.

## DETECTED ISSUES
{detected_issues}

## YOUR TASK
{task_instruction}

## SPECIFIC GUIDELINES
{guidelines}

## WORDS/PHRASES TO AVOID
{avoid_list}

## ORIGINAL TEXT
{original_text}

## OUTPUT REQUIREMENTS
{output_requirements}

## RESPONSE FORMAT (JSON)
{{
  "rewritten": "your rewritten text",
  "changes": [
    {{"original": "old text", "replacement": "new text", "reason": "why this change"}}
  ],
  "explanation": "what techniques were applied",
  "explanation_zh": "应用了什么技巧"
}}

IMPORTANT: Do not use any words from the AVOID list in your rewritten text."""

    def __init__(self, p0_blocklist: Optional[List[str]] = None):
        """
        Initialize prompt builder

        Args:
            p0_blocklist: Additional P0 words to always avoid
        """
        self.p0_blocklist = set(p0_blocklist or [])

    def build_prompt(
        self,
        original_text: str,
        diagnosed_issues: List[DiagnosedIssue],
        locked_terms: Optional[List[str]] = None,
        tone_level: int = 4,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Build a dynamic prompt based on diagnosed issues
        根据诊断问题构建动态提示词

        Args:
            original_text: The text to rewrite
            diagnosed_issues: List of diagnosed issues
            locked_terms: Terms that must be preserved
            tone_level: Target formality level (0-5)
            additional_context: Extra context to include

        Returns:
            Formatted prompt string
        """
        if not diagnosed_issues:
            # No specific issues - use generic improvement prompt
            # 没有具体问题 - 使用通用改进提示词
            return self._build_generic_prompt(original_text, locked_terms, tone_level)

        # Sort issues by priority
        # 按优先级排序问题
        sorted_issues = sorted(
            diagnosed_issues,
            key=lambda x: self.ISSUE_STRATEGIES.get(x.issue_type, {}).get("priority", 99)
        )

        # Build components
        # 构建组件
        components = self._extract_components(sorted_issues, original_text)

        # Add locked terms protection
        # 添加锁定术语保护
        if locked_terms:
            components.specific_guidelines.append(
                f"PROTECTED TERMS (do not modify): {', '.join(locked_terms)}"
            )

        # Add tone guidance
        # 添加语气指导
        components.specific_guidelines.append(
            self._get_tone_guidance(tone_level)
        )

        # Format the prompt
        # 格式化提示词
        prompt = self.BASE_TEMPLATE.format(
            detected_issues=self._format_issues(sorted_issues),
            task_instruction=components.task_instruction,
            guidelines="\n".join(f"- {g}" for g in components.specific_guidelines),
            avoid_list=", ".join(set(components.avoid_list) | self.p0_blocklist),
            original_text=original_text,
            output_requirements="\n".join(f"- {r}" for r in components.output_requirements)
        )

        if additional_context:
            prompt = f"## CONTEXT\n{additional_context}\n\n{prompt}"

        return prompt

    def _extract_components(
        self,
        issues: List[DiagnosedIssue],
        original_text: str
    ) -> PromptComponents:
        """
        Extract prompt components from issues
        从问题中提取提示词组件
        """
        # Use primary issue for main instruction
        # 使用主要问题作为主要指令
        primary = issues[0]
        strategy = self.ISSUE_STRATEGIES.get(primary.issue_type, {})

        task_instruction = strategy.get("instruction", "Improve the text to sound more human-written")

        # Replace placeholders in instruction
        # 替换指令中的占位符
        if "{word}" in task_instruction:
            task_instruction = task_instruction.replace("{word}", primary.matched_text)
        if "{text}" in task_instruction:
            task_instruction = task_instruction.replace("{text}", primary.matched_text[:50])

        # Collect guidelines from all issues
        # 从所有问题中收集指导方针
        guidelines = []
        avoid_list = []

        for issue in issues:
            issue_strategy = self.ISSUE_STRATEGIES.get(issue.issue_type, {})

            # Add guidelines with placeholder replacement
            # 添加带占位符替换的指导方针
            for g in issue_strategy.get("guidelines", []):
                formatted = g.replace("{word}", issue.matched_text)
                formatted = formatted.replace("{text}", issue.matched_text[:50])
                guidelines.append(formatted)

            avoid_list.extend(issue_strategy.get("avoid", []))

        # Standard output requirements
        # 标准输出要求
        output_requirements = [
            "Preserve exact academic meaning",
            "Maintain formal academic tone",
            "Keep all citations and references unchanged",
            "Output must be grammatically correct",
            "Do not change technical terminology"
        ]

        return PromptComponents(
            task_instruction=task_instruction,
            detected_issues=[issue.issue_type.value for issue in issues],
            specific_guidelines=guidelines,
            avoid_list=avoid_list,
            output_requirements=output_requirements
        )

    def _format_issues(self, issues: List[DiagnosedIssue]) -> str:
        """Format issues for prompt display"""
        lines = []
        for issue in issues:
            severity_marker = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue.severity, "⚪")
            lines.append(f"{severity_marker} [{issue.issue_type.value}] '{issue.matched_text[:40]}...'")
        return "\n".join(lines)

    def _get_tone_guidance(self, tone_level: int) -> str:
        """Get tone guidance based on level"""
        if tone_level <= 1:
            return "Target tone: Highly academic (journal paper level) - complex vocabulary acceptable"
        elif tone_level <= 3:
            return "Target tone: Standard academic (thesis level) - balanced formality"
        elif tone_level <= 4:
            return "Target tone: Semi-formal academic - clear and accessible"
        else:
            return "Target tone: Accessible (blog/report level) - simple and direct"

    def _build_generic_prompt(
        self,
        original_text: str,
        locked_terms: Optional[List[str]],
        tone_level: int
    ) -> str:
        """Build a generic improvement prompt when no specific issues detected"""
        return f"""You are an academic writing advisor helping to improve text clarity.

## ORIGINAL TEXT
{original_text}

## TASK
Improve this text to sound more naturally human-written while maintaining academic quality.

## GUIDELINES
- Use simpler, more direct language where possible
- Avoid overly formal or flowery vocabulary
- {self._get_tone_guidance(tone_level)}
{f"- PROTECTED TERMS (do not modify): {', '.join(locked_terms)}" if locked_terms else ""}

## RESPONSE FORMAT (JSON)
{{
  "rewritten": "your improved text",
  "changes": [
    {{"original": "old", "replacement": "new", "reason": "why"}}
  ],
  "explanation": "what improvements were made"
}}"""

    def build_from_analysis_result(
        self,
        original_text: str,
        fingerprint_matches: List[Any],
        void_matches: List[Any] = None,
        anchor_analysis: Any = None,
        locked_terms: Optional[List[str]] = None,
        tone_level: int = 4
    ) -> str:
        """
        Build prompt from analysis module results
        从分析模块结果构建提示词

        Convenience method that converts analysis results to DiagnosedIssue objects.
        """
        diagnosed_issues = []

        # Convert fingerprint matches
        # 转换指纹匹配
        if fingerprint_matches:
            for fp in fingerprint_matches:
                # Determine issue type based on risk weight
                # 根据风险权重确定问题类型
                if hasattr(fp, 'risk_weight') and fp.risk_weight >= 0.8:
                    issue_type = IssueType.P0_FINGERPRINT
                    severity = "high"
                else:
                    issue_type = IssueType.P1_FINGERPRINT
                    severity = "medium"

                diagnosed_issues.append(DiagnosedIssue(
                    issue_type=issue_type,
                    severity=severity,
                    matched_text=fp.word if hasattr(fp, 'word') else str(fp),
                    position=fp.position if hasattr(fp, 'position') else None
                ))

        # Convert void matches
        # 转换空洞匹配
        if void_matches:
            for vm in void_matches:
                diagnosed_issues.append(DiagnosedIssue(
                    issue_type=IssueType.SYNTACTIC_VOID,
                    severity=vm.severity if hasattr(vm, 'severity') else "medium",
                    matched_text=vm.matched_text if hasattr(vm, 'matched_text') else str(vm),
                    position=vm.position if hasattr(vm, 'position') else None
                ))

        # Convert anchor analysis
        # 转换锚点分析
        if anchor_analysis and hasattr(anchor_analysis, 'has_hallucination_risk'):
            if anchor_analysis.has_hallucination_risk:
                diagnosed_issues.append(DiagnosedIssue(
                    issue_type=IssueType.LOW_ANCHOR_DENSITY,
                    severity="medium",
                    matched_text=f"Low anchor density: {anchor_analysis.anchor_density:.1f}%",
                    details={"density": anchor_analysis.anchor_density}
                ))

        return self.build_prompt(
            original_text=original_text,
            diagnosed_issues=diagnosed_issues,
            locked_terms=locked_terms,
            tone_level=tone_level
        )


# Convenience function
# 便捷函数
def build_dynamic_prompt(
    original_text: str,
    issues: List[Dict[str, Any]],
    locked_terms: Optional[List[str]] = None,
    tone_level: int = 4
) -> str:
    """
    Convenience function to build dynamic prompt
    构建动态提示词的便捷函数

    Args:
        original_text: Text to rewrite
        issues: List of issue dicts with keys: type, severity, text
        locked_terms: Terms to protect
        tone_level: Formality level (0-5)

    Returns:
        Formatted prompt string
    """
    diagnosed = []
    for issue in issues:
        try:
            issue_type = IssueType(issue.get("type", "p1_fingerprint"))
        except ValueError:
            issue_type = IssueType.P1_FINGERPRINT

        diagnosed.append(DiagnosedIssue(
            issue_type=issue_type,
            severity=issue.get("severity", "medium"),
            matched_text=issue.get("text", "")
        ))

    builder = PromptBuilder()
    return builder.build_prompt(original_text, diagnosed, locked_terms, tone_level)
