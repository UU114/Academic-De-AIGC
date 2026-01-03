"""
Three-Level De-AIGC Flow Coordinator
三层级 De-AIGC 流程协调器

Phase 5: Orchestrates L1 → L2 → L3 processing flow
第5阶段：协调 L1 → L2 → L3 处理流程
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ProcessingLevel(str, Enum):
    """Processing level identifiers 处理层级标识"""
    LEVEL_1 = "level_1"  # 骨架重组 Macro Structure
    LEVEL_2 = "level_2"  # 关节润滑 Paragraph Transition
    LEVEL_3 = "level_3"  # 皮肤精修 Sentence Polish


class ProcessingMode(str, Enum):
    """Processing mode types 处理模式类型"""
    QUICK = "quick"  # Skip L1, focus on L3 (for small documents)
    DEEP = "deep"    # Full L1 → L2 → L3 flow


class StepStatus(str, Enum):
    """Processing step status 处理步骤状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class LevelResult:
    """
    Result from a processing level
    处理层级的结果
    """
    level: ProcessingLevel
    status: StepStatus
    score_before: int
    score_after: int
    issues_found: int
    issues_fixed: int
    changes: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""
    message_zh: str = ""


@dataclass
class FlowContext:
    """
    Context passed between processing levels
    在处理层级之间传递的上下文
    """
    # Document info
    # 文档信息
    document_id: str
    session_id: str
    original_text: str

    # Current state
    # 当前状态
    current_text: str
    current_level: ProcessingLevel
    mode: ProcessingMode

    # Extracted info from L1
    # 从L1提取的信息
    core_thesis: Optional[str] = None
    key_arguments: List[str] = field(default_factory=list)
    structure_issues: List[Dict] = field(default_factory=list)
    new_paragraph_order: Optional[List[int]] = None

    # Transition info from L2
    # 从L2提取的信息
    paragraph_pairs: List[Dict] = field(default_factory=list)
    transition_repairs: List[Dict] = field(default_factory=list)

    # Level results
    # 层级结果
    level_results: List[LevelResult] = field(default_factory=list)

    # Whitelist and config
    # 白名单和配置
    whitelist: List[str] = field(default_factory=list)
    colloquialism_level: int = 4

    def get_current_paragraphs(self) -> List[str]:
        """
        Get current paragraphs from text
        从文本获取当前段落
        """
        return [p.strip() for p in self.current_text.split('\n\n') if p.strip()]

    def update_text(self, new_text: str):
        """
        Update current text after processing
        处理后更新当前文本
        """
        self.current_text = new_text


class FlowCoordinator:
    """
    Coordinates the three-level De-AIGC processing flow
    协调三层级 De-AIGC 处理流程

    Flow: L1 (Structure) → L2 (Transition) → L3 (Sentence)
    流程：L1 (结构) → L2 (衔接) → L3 (句子)

    Key principle: Each level must complete before next level starts,
    because higher-level changes may invalidate lower-level edits.

    关键原则：每个层级必须在下一层级开始前完成，
    因为高层级的更改可能使低层级的编辑失效。
    """

    LEVEL_ORDER = [
        ProcessingLevel.LEVEL_1,
        ProcessingLevel.LEVEL_2,
        ProcessingLevel.LEVEL_3,
    ]

    LEVEL_NAMES = {
        ProcessingLevel.LEVEL_1: {"en": "Macro Structure", "zh": "骨架重组"},
        ProcessingLevel.LEVEL_2: {"en": "Paragraph Transition", "zh": "关节润滑"},
        ProcessingLevel.LEVEL_3: {"en": "Sentence Polish", "zh": "皮肤精修"},
    }

    def __init__(self):
        """Initialize the flow coordinator 初始化流程协调器"""
        pass

    def create_context(
        self,
        document_id: str,
        session_id: str,
        text: str,
        mode: ProcessingMode = ProcessingMode.DEEP,
        whitelist: Optional[List[str]] = None,
        colloquialism_level: int = 4
    ) -> FlowContext:
        """
        Create a new flow context for processing
        创建新的处理流程上下文

        Args:
            document_id: Document identifier 文档标识
            session_id: Session identifier 会话标识
            text: Document text 文档文本
            mode: Processing mode (quick/deep) 处理模式
            whitelist: Terms to whitelist 白名单术语
            colloquialism_level: Target tone level 目标语气等级

        Returns:
            FlowContext for tracking processing state 用于跟踪处理状态的FlowContext
        """
        return FlowContext(
            document_id=document_id,
            session_id=session_id,
            original_text=text,
            current_text=text,
            current_level=ProcessingLevel.LEVEL_1,
            mode=mode,
            whitelist=whitelist or [],
            colloquialism_level=colloquialism_level
        )

    def get_current_level(self, context: FlowContext) -> ProcessingLevel:
        """
        Get the current processing level
        获取当前处理层级
        """
        return context.current_level

    def get_level_status(self, context: FlowContext, level: ProcessingLevel) -> StepStatus:
        """
        Get status of a specific level
        获取特定层级的状态

        Args:
            context: Flow context 流程上下文
            level: Level to check 要检查的层级

        Returns:
            StepStatus for the level 层级的状态
        """
        # Check if level has a result
        # 检查层级是否有结果
        for result in context.level_results:
            if result.level == level:
                return result.status

        # Determine pending/skipped status
        # 确定待处理/跳过状态
        level_idx = self.LEVEL_ORDER.index(level)
        current_idx = self.LEVEL_ORDER.index(context.current_level)

        if level_idx < current_idx:
            # Previous level should be completed or skipped
            # 之前的层级应该已完成或跳过
            return StepStatus.SKIPPED
        elif level_idx == current_idx:
            return StepStatus.IN_PROGRESS
        else:
            return StepStatus.PENDING

    def should_skip_level(self, context: FlowContext, level: ProcessingLevel) -> bool:
        """
        Determine if a level should be skipped
        确定是否应该跳过某个层级

        Args:
            context: Flow context 流程上下文
            level: Level to check 要检查的层级

        Returns:
            True if level should be skipped 如果应该跳过则返回True
        """
        # Quick mode skips L1 and L2
        # 快速模式跳过L1和L2
        if context.mode == ProcessingMode.QUICK:
            return level in [ProcessingLevel.LEVEL_1, ProcessingLevel.LEVEL_2]

        # Small documents (< 3 paragraphs) skip L1
        # 小文档（< 3段落）跳过L1
        paragraphs = context.get_current_paragraphs()
        if len(paragraphs) < 3 and level == ProcessingLevel.LEVEL_1:
            return True

        # Documents with < 2 paragraphs skip L2
        # 少于2段落的文档跳过L2
        if len(paragraphs) < 2 and level == ProcessingLevel.LEVEL_2:
            return True

        return False

    def advance_level(self, context: FlowContext, result: LevelResult) -> Optional[ProcessingLevel]:
        """
        Complete current level and advance to next
        完成当前层级并进入下一层级

        Args:
            context: Flow context 流程上下文
            result: Result from completed level 已完成层级的结果

        Returns:
            Next level to process, or None if complete 下一个要处理的层级，如果完成则返回None
        """
        # Store result
        # 存储结果
        context.level_results.append(result)

        # Find next level
        # 查找下一层级
        current_idx = self.LEVEL_ORDER.index(context.current_level)
        if current_idx >= len(self.LEVEL_ORDER) - 1:
            return None  # All levels complete

        next_level = self.LEVEL_ORDER[current_idx + 1]

        # Skip if needed
        # 如果需要则跳过
        while self.should_skip_level(context, next_level):
            skip_result = LevelResult(
                level=next_level,
                status=StepStatus.SKIPPED,
                score_before=0,
                score_after=0,
                issues_found=0,
                issues_fixed=0,
                message=f"Level skipped based on document size or mode",
                message_zh=f"根据文档大小或模式跳过层级"
            )
            context.level_results.append(skip_result)

            current_idx = self.LEVEL_ORDER.index(next_level)
            if current_idx >= len(self.LEVEL_ORDER) - 1:
                return None

            next_level = self.LEVEL_ORDER[current_idx + 1]

        context.current_level = next_level
        return next_level

    def get_flow_progress(self, context: FlowContext) -> Dict:
        """
        Get current flow progress summary
        获取当前流程进度摘要

        Args:
            context: Flow context 流程上下文

        Returns:
            Progress summary dict 进度摘要字典
        """
        levels_status = []
        total_issues_found = 0
        total_issues_fixed = 0
        total_score_reduction = 0

        for level in self.LEVEL_ORDER:
            status = self.get_level_status(context, level)
            level_info = {
                "level": level.value,
                "name_en": self.LEVEL_NAMES[level]["en"],
                "name_zh": self.LEVEL_NAMES[level]["zh"],
                "status": status.value,
            }

            # Add result info if available
            # 如果可用则添加结果信息
            for result in context.level_results:
                if result.level == level:
                    level_info["score_before"] = result.score_before
                    level_info["score_after"] = result.score_after
                    level_info["issues_found"] = result.issues_found
                    level_info["issues_fixed"] = result.issues_fixed
                    total_issues_found += result.issues_found
                    total_issues_fixed += result.issues_fixed
                    total_score_reduction += (result.score_before - result.score_after)
                    break

            levels_status.append(level_info)

        # Determine overall status
        # 确定整体状态
        completed_count = sum(1 for r in context.level_results if r.status == StepStatus.COMPLETED)
        skipped_count = sum(1 for r in context.level_results if r.status == StepStatus.SKIPPED)
        total_levels = len(self.LEVEL_ORDER)

        if completed_count + skipped_count >= total_levels:
            overall_status = "completed"
        else:
            overall_status = "in_progress"

        return {
            "mode": context.mode.value,
            "current_level": context.current_level.value,
            "overall_status": overall_status,
            "levels": levels_status,
            "summary": {
                "total_issues_found": total_issues_found,
                "total_issues_fixed": total_issues_fixed,
                "total_score_reduction": total_score_reduction,
                "completed_levels": completed_count,
                "skipped_levels": skipped_count,
            }
        }

    def validate_level_transition(
        self,
        context: FlowContext,
        from_level: ProcessingLevel,
        to_level: ProcessingLevel
    ) -> bool:
        """
        Validate that a level transition is allowed
        验证层级转换是否允许

        Args:
            context: Flow context 流程上下文
            from_level: Source level 源层级
            to_level: Target level 目标层级

        Returns:
            True if transition is valid 如果转换有效则返回True
        """
        from_idx = self.LEVEL_ORDER.index(from_level)
        to_idx = self.LEVEL_ORDER.index(to_level)

        # Can only go forward
        # 只能前进
        if to_idx <= from_idx:
            logger.warning(f"Invalid level transition: {from_level} → {to_level}")
            return False

        # Current level must be completed
        # 当前层级必须已完成
        status = self.get_level_status(context, from_level)
        if status not in [StepStatus.COMPLETED, StepStatus.SKIPPED]:
            logger.warning(f"Cannot transition: {from_level} is {status}")
            return False

        return True

    def get_level_context_for_l2(self, context: FlowContext) -> Dict:
        """
        Get context from L1 for L2 processing
        获取用于L2处理的L1上下文

        Args:
            context: Flow context 流程上下文

        Returns:
            Context dict for L2 L2的上下文字典
        """
        return {
            "core_thesis": context.core_thesis,
            "key_arguments": context.key_arguments,
            "structure_issues": context.structure_issues,
            "new_paragraph_order": context.new_paragraph_order,
        }

    def get_level_context_for_l3(self, context: FlowContext) -> Dict:
        """
        Get context from L1+L2 for L3 processing
        获取用于L3处理的L1+L2上下文

        Args:
            context: Flow context 流程上下文

        Returns:
            Context dict for L3 L3的上下文字典
        """
        l2_context = self.get_level_context_for_l2(context)
        l2_context.update({
            "paragraph_pairs": context.paragraph_pairs,
            "transition_repairs": context.transition_repairs,
            "whitelist": context.whitelist,
            "colloquialism_level": context.colloquialism_level,
        })
        return l2_context


# Singleton instance
# 单例实例
flow_coordinator = FlowCoordinator()
