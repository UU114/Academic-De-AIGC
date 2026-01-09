"""
Term Locking API Routes (Layer 5 - Step 1.0)
词汇锁定API路由（第5层 - 步骤1.0）

Endpoints:
- POST /extract-terms - Extract candidate terms for locking
- POST /confirm-lock - Confirm and lock selected terms
- GET /locked-terms - Get current locked terms for session
- DELETE /locked-terms - Clear locked terms
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import logging
import time

from src.core.analyzer.term_extractor import (
    TermExtractor,
    TermExtractionResult,
    ExtractedTerm,
    TermType
)

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# In-memory session storage for locked terms (replace with Redis in production)
# 内存中的会话存储（生产环境应使用Redis）
# =============================================================================
_locked_terms_store: Dict[str, Dict[str, Any]] = {}


# =============================================================================
# Schemas
# =============================================================================

class TermTypeEnum(str, Enum):
    """Term type enumeration for API"""
    TECHNICAL_TERM = "technical_term"
    PROPER_NOUN = "proper_noun"
    ACRONYM = "acronym"
    KEY_PHRASE = "key_phrase"
    CORE_WORD = "core_word"


class ExtractedTermResponse(BaseModel):
    """Single extracted term in response"""
    term: str = Field(..., description="The extracted term")
    term_type: TermTypeEnum = Field(..., description="Type of term")
    frequency: int = Field(..., description="Frequency in document")
    reason: str = Field(..., description="Why this should be locked (English)")
    reason_zh: str = Field(..., description="Why this should be locked (Chinese)")
    recommended: bool = Field(True, description="Whether recommended for locking")


class ExtractTermsRequest(BaseModel):
    """Request to extract terms from document"""
    document_text: str = Field(..., min_length=10, description="Document text to analyze")
    session_id: str = Field(..., description="Session ID for term storage")


class ExtractTermsResponse(BaseModel):
    """Response with extracted terms"""
    extracted_terms: List[ExtractedTermResponse] = Field(default_factory=list)
    total_count: int = Field(0, description="Total number of terms extracted")
    by_type: Dict[str, int] = Field(default_factory=dict, description="Count by term type")
    processing_time_ms: int = Field(0, description="Processing time in milliseconds")


class ConfirmLockRequest(BaseModel):
    """Request to confirm and lock selected terms"""
    session_id: str = Field(..., description="Session ID")
    locked_terms: List[str] = Field(default_factory=list, description="Terms selected for locking")
    custom_terms: List[str] = Field(default_factory=list, description="Custom terms added by user")


class ConfirmLockResponse(BaseModel):
    """Response after confirming locked terms"""
    locked_count: int = Field(0, description="Number of terms locked")
    locked_terms: List[str] = Field(default_factory=list, description="All locked terms")
    message: str = Field("", description="Status message")
    message_zh: str = Field("", description="Status message in Chinese")


class LockedTermsResponse(BaseModel):
    """Response with current locked terms for session"""
    session_id: str = Field(..., description="Session ID")
    locked_terms: List[str] = Field(default_factory=list, description="Locked terms")
    locked_count: int = Field(0, description="Number of locked terms")
    created_at: Optional[str] = Field(None, description="When terms were locked")


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/extract-terms", response_model=ExtractTermsResponse)
async def extract_terms(request: ExtractTermsRequest):
    """
    Extract candidate terms for locking from document
    从文档中提取待锁定的候选术语

    Step 1.0.1: LLM analyzes document and extracts:
    - Technical terms (domain-specific vocabulary)
    - Proper nouns (names, places, methods)
    - Acronyms (technical abbreviations)
    - Key phrases (fixed expressions)
    - High-frequency core words
    """
    start_time = time.time()

    try:
        # Initialize extractor
        extractor = TermExtractor()

        # Extract terms
        result = await extractor.extract_terms(request.document_text)

        # Convert to response format
        extracted_terms = [
            ExtractedTermResponse(
                term=t.term,
                term_type=TermTypeEnum(t.term_type.value),
                frequency=t.frequency,
                reason=t.reason,
                reason_zh=t.reason_zh,
                recommended=t.recommended
            )
            for t in result.extracted_terms
        ]

        # Sort by frequency (highest first), then by type priority
        type_priority = {
            TermTypeEnum.TECHNICAL_TERM: 1,
            TermTypeEnum.PROPER_NOUN: 2,
            TermTypeEnum.ACRONYM: 3,
            TermTypeEnum.KEY_PHRASE: 4,
            TermTypeEnum.CORE_WORD: 5,
        }
        extracted_terms.sort(
            key=lambda t: (type_priority.get(t.term_type, 5), -t.frequency)
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ExtractTermsResponse(
            extracted_terms=extracted_terms,
            total_count=result.total_count,
            by_type=result.by_type,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Term extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm-lock", response_model=ConfirmLockResponse)
async def confirm_lock_terms(request: ConfirmLockRequest):
    """
    Confirm and lock selected terms for the session
    确认并锁定选中的术语

    Step 1.0.2: User confirms which terms to lock
    - Terms will be protected in all subsequent LLM steps
    - Supports both selected terms and custom user-added terms
    """
    try:
        # Combine selected and custom terms
        all_terms = list(set(request.locked_terms + request.custom_terms))

        # Store in session
        _locked_terms_store[request.session_id] = {
            "locked_terms": all_terms,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "from_extraction": len(request.locked_terms),
            "custom_added": len(request.custom_terms)
        }

        logger.info(f"Session {request.session_id}: Locked {len(all_terms)} terms")

        return ConfirmLockResponse(
            locked_count=len(all_terms),
            locked_terms=all_terms,
            message=f"Successfully locked {len(all_terms)} terms. These will be protected in all subsequent rewriting steps.",
            message_zh=f"成功锁定 {len(all_terms)} 个词汇。这些词汇将在后续所有改写步骤中保持不变。"
        )

    except Exception as e:
        logger.error(f"Term locking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/locked-terms", response_model=LockedTermsResponse)
async def get_locked_terms(session_id: str = Query(..., description="Session ID")):
    """
    Get current locked terms for session
    获取当前会话的锁定术语

    Returns the list of terms that will be protected
    in all subsequent LLM processing steps.
    """
    try:
        session_data = _locked_terms_store.get(session_id, {})

        return LockedTermsResponse(
            session_id=session_id,
            locked_terms=session_data.get("locked_terms", []),
            locked_count=len(session_data.get("locked_terms", [])),
            created_at=session_data.get("created_at")
        )

    except Exception as e:
        logger.error(f"Failed to get locked terms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/locked-terms")
async def clear_locked_terms(session_id: str = Query(..., description="Session ID")):
    """
    Clear locked terms for session
    清除会话的锁定术语

    Use this to reset term locking and start fresh.
    """
    try:
        if session_id in _locked_terms_store:
            del _locked_terms_store[session_id]
            return {
                "success": True,
                "message": "Locked terms cleared successfully",
                "message_zh": "锁定术语已清除"
            }
        else:
            return {
                "success": True,
                "message": "No locked terms found for session",
                "message_zh": "该会话没有锁定的术语"
            }

    except Exception as e:
        logger.error(f"Failed to clear locked terms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Helper functions for other modules to access locked terms
# 供其他模块访问锁定术语的辅助函数
# =============================================================================

def get_session_locked_terms(session_id: str) -> List[str]:
    """
    Get locked terms for a session (for use by other modules)
    获取会话的锁定术语（供其他模块使用）

    Args:
        session_id: Session identifier

    Returns:
        List of locked terms
    """
    session_data = _locked_terms_store.get(session_id, {})
    return session_data.get("locked_terms", [])


def build_locked_terms_prompt(session_id: str) -> str:
    """
    Build the locked terms instruction to inject into LLM prompts
    构建要注入LLM提示词的锁定术语指令

    Args:
        session_id: Session identifier

    Returns:
        Formatted instruction string, or empty string if no locked terms
    """
    locked_terms = get_session_locked_terms(session_id)

    if not locked_terms:
        return ""

    terms_list = "\n".join([f"- {term}" for term in locked_terms])

    return f"""
## PROTECTED TERMS (DO NOT MODIFY) / 锁定词汇（禁止修改）

The following terms must remain EXACTLY as written. Do not:
- Change the wording or spelling
- Replace with synonyms or paraphrases
- Translate to another language
- Modify capitalization or formatting
- Split or merge these terms

以下术语必须保持原样，禁止：
- 更改措辞或拼写
- 用同义词或释义替换
- 翻译成其他语言
- 修改大小写或格式
- 拆分或合并这些术语

Protected terms / 锁定术语:
{terms_list}

When rewriting, preserve these terms verbatim in their original positions.
改写时，请将这些术语保持原样放在原来的位置。
"""
