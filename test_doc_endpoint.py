"""Test document.py analyze_paragraph_length directly"""
import asyncio
from src.api.routes.analysis.document import analyze_paragraph_length
from src.api.routes.analysis.schemas import ParagraphLengthAnalysisRequest

async def main():
    req = ParagraphLengthAnalysisRequest(text="Test paragraph.")
    result = await analyze_paragraph_length(req)
    print("Recommendations:", result.recommendations)
    print("Paragraphs:", result.paragraphs)
    print("Processing time:", result.processing_time_ms)

if __name__ == "__main__":
    asyncio.run(main())
