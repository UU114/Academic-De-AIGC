import httpx
import time
import os
import json
import asyncio

BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_FILE = "test_documents/test_high_risk.txt"

# Map layers to their first step endpoint
# Layer 5 -> Step 1.1
# Layer 4 -> Step 2.1
# Layer 3 -> Step 3.1
# Layer 2 -> Step 4.1
# Layer 1 -> Step 5.1
STEPS = [
    {"layer": "layer5", "step": "step1-1", "name": "Structure Analysis"},
    {"layer": "layer4", "step": "step2-1", "name": "Section Analysis"},
    {"layer": "layer3", "step": "step3-1", "name": "Paragraph Analysis"},
    {"layer": "layer2", "step": "step4-1", "name": "Sentence Analysis"},
    {"layer": "layer1", "step": "step5-1", "name": "Lexical Analysis"},
]

async def run_test():
    print(f"=== Starting Full Flow Test ===")
    print(f"Target: {BASE_URL}")
    print(f"File: {TEST_FILE}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. Upload
        print("\n[1] Uploading document...")
        if not os.path.exists(TEST_FILE):
            print(f"Error: File {TEST_FILE} not found.")
            return

        with open(TEST_FILE, 'rb') as f:
            files = {'file': (os.path.basename(TEST_FILE), f, 'text/plain')}
            resp = await client.post(f"{BASE_URL}/documents/upload", files=files)
            if resp.status_code != 200:
                print(f"Upload failed: {resp.text}")
                return
            doc_data = resp.json()
            doc_id = doc_data['id']
            print(f"    Upload success. Doc ID: {doc_id}")

        # 2. Start Session
        print("\n[2] Starting session...")
        payload = {
            "document_id": doc_id,
            "mode": "intervention",
            "process_levels": ["high", "medium", "low"],
            "colloquialism_level": 5,
            "target_lang": "zh"
        }
        resp = await client.post(f"{BASE_URL}/session/start", json=payload)
        if resp.status_code != 200:
            print(f"Start session failed: {resp.text}")
            return
        session_data = resp.json()
        session_id = session_data['session_id']
        print(f"    Session started. Session ID: {session_id}")
        
        # Initial text
        # We need to fetch the text or use what we uploaded. 
        # The upload response might not have text, let's assume we read the file locally for the first step
        # OR we can rely on the session to load it if we don't pass 'text'.
        # But the requirement is to pass previous output.
        with open(TEST_FILE, 'r', encoding='utf-8') as f:
            current_text = f.read()

        # 3. Iterate Steps
        for step_info in STEPS:
            layer = step_info['layer']
            step = step_info['step']
            name = step_info['name']
            
            print(f"\n[{layer}/{step}] {name}...")
            
            # 3.1 Analyze
            analyze_url = f"{BASE_URL}/{layer}/{step}/analyze"
            analyze_payload = {
                "text": current_text,
                "session_id": session_id,
                "locked_terms": []
            }
            
            try:
                resp = await client.post(analyze_url, json=analyze_payload)
                if resp.status_code != 200:
                    print(f"    Analysis failed: {resp.status_code} - {resp.text}")
                    continue
                
                analysis_result = resp.json()
                issues = analysis_result.get('issues', [])
                risk_score = analysis_result.get('risk_score', 0)
                print(f"    Analysis complete. Risk Score: {risk_score}")
                print(f"    Issues found: {len(issues)}")
                
                if len(issues) > 0:
                    # 3.2 Apply Fixes (if issues exist)
                    print(f"    Applying fixes for {len(issues)} issues...")
                    
                    apply_url = f"{BASE_URL}/{layer}/{step}/merge-modify/apply"
                    apply_payload = {
                        "document_id": doc_id,
                        "session_id": session_id,
                        "selected_issues": issues, # Assuming structure matches
                        "user_notes": "Fix everything automatically for testing."
                    }
                    
                    resp = await client.post(apply_url, json=apply_payload)
                    if resp.status_code != 200:
                        print(f"    Apply failed: {resp.status_code} - {resp.text}")
                        # Keep current text if apply failed
                    else:
                        apply_result = resp.json()
                        modified_text = apply_result.get('modified_text')
                        if modified_text:
                            print(f"    Fix applied. Text length: {len(current_text)} -> {len(modified_text)}")
                            current_text = modified_text
                        else:
                            print("    Fix applied but no text returned?")
                else:
                    print("    No issues to fix. proceeding with same text.")

            except Exception as e:
                import traceback
                print(f"    Error executing step {step}: {e}")
                traceback.print_exc()
                
        # 4. Final Verification
        print("\n[4] Test Complete.")
        print(f"Final text length: {len(current_text)}")
        
        # Save output
        with open("test_result_final.txt", "w", encoding="utf-8") as f:
            f.write(current_text)
        print("Final text saved to test_result_final.txt")

if __name__ == "__main__":
    asyncio.run(run_test())
