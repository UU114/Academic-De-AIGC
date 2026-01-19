"""
Batch fix script for substep files
批量修复子步骤文件脚本

This script updates all substep files to use the new document_service
for getting working text (previous step's modified text).
"""

import os
import re

# Define all substep files and their step names
SUBSTEP_FILES = {
    # Layer 5 - Document Level
    "src/api/routes/substeps/layer5/step1_1.py": "layer5-step1-1",  # Already fixed
    "src/api/routes/substeps/layer5/step1_2.py": "layer5-step1-2",
    "src/api/routes/substeps/layer5/step1_3.py": "layer5-step1-3",
    "src/api/routes/substeps/layer5/step1_4.py": "layer5-step1-4",
    "src/api/routes/substeps/layer5/step1_5.py": "layer5-step1-5",
    # Layer 4 - Section Level
    "src/api/routes/substeps/layer4/step2_0.py": "layer4-step2-0",
    "src/api/routes/substeps/layer4/step2_1.py": "layer4-step2-1",
    "src/api/routes/substeps/layer4/step2_2.py": "layer4-step2-2",
    "src/api/routes/substeps/layer4/step2_3.py": "layer4-step2-3",
    "src/api/routes/substeps/layer4/step2_4.py": "layer4-step2-4",
    "src/api/routes/substeps/layer4/step2_5.py": "layer4-step2-5",
    # Layer 3 - Paragraph Level
    "src/api/routes/substeps/layer3/step3_0.py": "layer3-step3-0",
    "src/api/routes/substeps/layer3/step3_1.py": "layer3-step3-1",
    "src/api/routes/substeps/layer3/step3_2.py": "layer3-step3-2",
    "src/api/routes/substeps/layer3/step3_3.py": "layer3-step3-3",
    "src/api/routes/substeps/layer3/step3_4.py": "layer3-step3-4",
    "src/api/routes/substeps/layer3/step3_5.py": "layer3-step3-5",
    # Layer 2 - Sentence Level
    "src/api/routes/substeps/layer2/step4_0.py": "layer2-step4-0",
    "src/api/routes/substeps/layer2/step4_1.py": "layer2-step4-1",
    "src/api/routes/substeps/layer2/step4_2.py": "layer2-step4-2",
    "src/api/routes/substeps/layer2/step4_3.py": "layer2-step4-3",
    "src/api/routes/substeps/layer2/step4_4.py": "layer2-step4-4",
    "src/api/routes/substeps/layer2/step4_5.py": "layer2-step4-5",
    # Layer 1 - Lexical Level
    "src/api/routes/substeps/layer1/step5_0.py": "layer1-step5-0",
    "src/api/routes/substeps/layer1/step5_1.py": "layer1-step5-1",
    "src/api/routes/substeps/layer1/step5_2.py": "layer1-step5-2",
    "src/api/routes/substeps/layer1/step5_3.py": "layer1-step5-3",
    "src/api/routes/substeps/layer1/step5_4.py": "layer1-step5-4",
    "src/api/routes/substeps/layer1/step5_5.py": "layer1-step5-5",
}

# Files already correctly implemented (using database query)
ALREADY_CORRECT = {
    "src/api/routes/substeps/layer5/step1_1.py",  # Just fixed
    "src/api/routes/substeps/layer4/step2_1.py",  # Reference implementation
}


def fix_imports(content: str) -> str:
    """Add necessary imports if not present"""
    # Check and add FastAPI Depends import
    if "from fastapi import" in content and "Depends" not in content:
        content = content.replace(
            "from fastapi import APIRouter, HTTPException",
            "from fastapi import APIRouter, HTTPException, Depends"
        )

    # Add AsyncSession import if not present
    if "AsyncSession" not in content:
        # Find the fastapi import line and add after it
        content = re.sub(
            r'(from fastapi import[^\n]+\n)',
            r'\1from sqlalchemy.ext.asyncio import AsyncSession\n',
            content
        )

    # Add database imports if not present
    if "from src.db.database import get_db" not in content:
        # Find a good place to add it (after other imports)
        if "from src.api.routes.substeps.schemas import" in content:
            content = re.sub(
                r'(from src\.api\.routes\.substeps\.schemas import)',
                r'from src.db.database import get_db\nfrom src.services.document_service import get_working_text, save_modified_text\n\n\1',
                content
            )

    # Remove SessionService import if present
    content = re.sub(
        r'\s*from src\.services\.session_service import SessionService\n',
        '',
        content
    )
    content = re.sub(
        r'\s*session_service = SessionService\(\)\n',
        '',
        content
    )

    return content


def fix_apply_endpoint(content: str, step_name: str) -> str:
    """Fix the apply_modification endpoint"""
    # Pattern 1: SessionService pattern (most files)
    session_service_pattern = r'''async def apply_modification\(request: MergeModifyRequest\):
    """Apply AI modification for .+ issues"""
    try:
        from src\.services\.session_service import SessionService
        session_service = SessionService\(\)
        session_data = await session_service\.get_session\(request\.session_id\) if request\.session_id else None
        document_text = session_data\.get\("document_text", ""\) if session_data else ""

        if not document_text:
            raise HTTPException\(status_code=400, detail="Document text not found in session"\)

        result = await handler\.apply_rewrite\(
            document_text=document_text,
            issues=request\.selected_issues,
            user_notes=request\.user_notes,
            locked_terms=session_data\.get\("locked_terms", \[\]\) if session_data else \[\]
        \)
        return MergeModifyApplyResponse\(
            modified_text=result\.get\("modified_text", ""\),
            changes_summary_zh=result\.get\("changes_summary_zh", ""\),
            changes_count=result\.get\("changes_count", 0\),
            issues_addressed=\[i\.type for i in request\.selected_issues\],
            remaining_attempts=3
        \)'''

    replacement = f'''async def apply_modification(
    request: MergeModifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Apply AI modification"""
    try:
        # Get working text (uses previous step's modified text if available)
        document_text, locked_terms = await get_working_text(
            db=db,
            session_id=request.session_id,
            current_step="{step_name}",
            document_id=request.document_id
        )

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found")

        result = await handler.apply_rewrite(
            document_text=document_text,
            issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )

        # Save modified text for next step
        if request.session_id and result.get("modified_text"):
            await save_modified_text(
                db=db,
                session_id=request.session_id,
                step_name="{step_name}",
                modified_text=result["modified_text"]
            )

        return MergeModifyApplyResponse(
            modified_text=result.get("modified_text", ""),
            changes_summary_zh=result.get("changes_summary_zh", ""),
            changes_count=result.get("changes_count", 0),
            issues_addressed=[i.type for i in request.selected_issues],
            remaining_attempts=3
        )'''

    # Try to match and replace the SessionService pattern
    if "from src.services.session_service import SessionService" in content:
        # This file uses SessionService, replace the whole block
        new_content = re.sub(
            session_service_pattern,
            replacement,
            content,
            flags=re.DOTALL
        )
        if new_content != content:
            return new_content

    return content


def process_file(filepath: str, step_name: str, base_dir: str) -> bool:
    """Process a single file"""
    full_path = os.path.join(base_dir, filepath)

    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        return False

    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Skip if already correct
    if "from src.services.document_service import" in content:
        print(f"Already fixed: {filepath}")
        return True

    # Fix imports
    content = fix_imports(content)

    # Fix apply endpoint
    content = fix_apply_endpoint(content, step_name)

    if content != original_content:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    else:
        print(f"No changes needed or pattern not matched: {filepath}")
        return False


def main():
    """Main function"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    fixed_count = 0
    failed_count = 0

    for filepath, step_name in SUBSTEP_FILES.items():
        if filepath in ALREADY_CORRECT:
            print(f"Skipping (already correct): {filepath}")
            continue

        if process_file(filepath, step_name, base_dir):
            fixed_count += 1
        else:
            failed_count += 1

    print(f"\nSummary: Fixed {fixed_count} files, {failed_count} failed/skipped")


if __name__ == "__main__":
    main()
