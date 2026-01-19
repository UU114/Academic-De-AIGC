import asyncio
import os
import sys

# Add app to path
sys.path.append('/var/www/academicguard/api')
os.chdir('/var/www/academicguard/api')

from src.core.suggester.llm_track import LLMTrack
from src.config import get_settings

async def test():
    print("--- Environment Debug ---")
    print(f"CWD: {os.getcwd()}")
    print(f".env exists in CWD: {os.path.exists('.env')}")
    if os.path.exists('.env'):
        print(f".env size: {os.path.getsize('.env')}")
        with open('.env', 'r') as f:
            for line in f:
                if 'LLM_PROVIDER' in line or 'DASHSCOPE' in line:
                    print(f"Found in .env: {line.strip()}")

    print("\n--- Settings Debug ---")
    # Force reload settings
    from src import config
    config.get_settings.cache_clear()
    settings = get_settings()
    print(f"Loaded LLM_PROVIDER: {settings.llm_provider}")
    print(f"Loaded DASHSCOPE_API_KEY set: {bool(settings.dashscope_api_key)}")
    
    print("\n--- LLMTrack Test ---")
    track = LLMTrack(colloquialism_level=4)
    sentence = "The results are very important for the study."
    print(f"Testing with sentence: {sentence}")
    try:
        # Signature: sentence, issues, locked_terms
        res = await track.generate_suggestion(sentence, [], [])
        if res:
            print(f"SUCCESS! Rewritten: {res.rewritten}")
            print(f"Explanation: {res.explanation_zh}")
        else:
            print("FAILED: Received None from generate_suggestion")
    except Exception as e:
        print(f"FAILED with error: {str(e)}")

if __name__ == '__main__':
    asyncio.run(test())