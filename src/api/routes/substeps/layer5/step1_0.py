"""
Step 1.0: Term Locking (词汇锁定)
Layer 5 Document Level - First substep

Extracts and locks domain-specific terms that should not be modified
提取并锁定不应被修改的领域特定术语
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
import logging
import time

from src.api.routes.substeps.schemas import (
    TermLockRequest,
    ExtractedTerm,
    ExtractTermsResponse,
    ConfirmLockRequest,
    ConfirmLockResponse,
)
from src.core.analyzer.term_extractor import TermExtractor

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session storage (use Redis in production)
# 内存会话存储（生产环境使用Redis）
_locked_terms_store: Dict[str, Dict[str, Any]] = {}


@router.post("/extract-terms", response_model=ExtractTermsResponse)
async def extract_terms(request: TermLockRequest):
    """
    Step 1.0.1: Extract candidate terms for locking
    步骤 1.0.1：提取待锁定的候选术语

    LLM analyzes document and extracts:
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
            ExtractedTerm(
                term=t.term,
                term_type=t.term_type.value,
                frequency=t.frequency,
                reason=t.reason,
                reason_zh=t.reason_zh,
                recommended=t.recommended
            )
            for t in result.extracted_terms
        ]

        # Sort by frequency and type priority
        type_priority = {
            "technical_term": 1,
            "proper_noun": 2,
            "acronym": 3,
            "key_phrase": 4,
            "core_word": 5,
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
    Step 1.0.2: Confirm and lock selected terms
    步骤 1.0.2：确认并锁定选中的术语

    User confirms which terms to lock.
    Terms will be protected in all subsequent LLM steps.
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


@router.get("/locked-terms")
async def get_locked_terms(session_id: str = Query(..., description="Session ID")):
    """
    Get current locked terms for session
    获取当前会话的锁定术语
    """
    try:
        session_data = _locked_terms_store.get(session_id, {})

        return {
            "session_id": session_id,
            "locked_terms": session_data.get("locked_terms", []),
            "locked_count": len(session_data.get("locked_terms", [])),
            "created_at": session_data.get("created_at")
        }

    except Exception as e:
        logger.error(f"Failed to get locked terms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/locked-terms")
async def clear_locked_terms(session_id: str = Query(..., description="Session ID")):
    """
    Clear locked terms for session
    清除会话的锁定术语
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


# Helper functions for other modules
# 供其他模块使用的辅助函数
def get_session_locked_terms(session_id: str) -> List[str]:
    """Get locked terms for a session"""
    session_data = _locked_terms_store.get(session_id, {})
    return session_data.get("locked_terms", [])


def build_locked_terms_prompt(session_id: str) -> str:
    """Build the locked terms instruction for LLM prompts"""
    locked_terms = get_session_locked_terms(session_id)

    if not locked_terms:
        return ""

    terms_list = "\n".join([f"- {term}" for term in locked_terms])

    return f"""
## PROTECTED TERMS (DO NOT MODIFY)

The following terms must remain EXACTLY as written. Do not:
- Change the wording or spelling
- Replace with synonyms or paraphrases
- Translate to another language
- Modify capitalization or formatting

Protected terms:
{terms_list}

When rewriting, preserve these terms verbatim.
"""
