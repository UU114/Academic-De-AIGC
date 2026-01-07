import httpx
import time
import os

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_simulation():
    # 1. Upload
    print("[1] Uploading document...")
    with open('test_simulation.txt', 'rb') as f:
        files = {'file': ('test_simulation.txt', f, 'text/plain')}
        try:
            response = httpx.post(f"{BASE_URL}/documents/upload", files=files, timeout=30.0)
            response.raise_for_status()
            doc_data = response.json()
            doc_id = doc_data['id']
            print(f"    Upload success. Doc ID: {doc_id}")
            print(f"    Status: {doc_data['status']}")
        except Exception as e:
            print(f"    Upload failed: {e}")
            return

    # 2. Start Session
    print("\n[2] Starting session...")
    payload = {
        "document_id": doc_id,
        "mode": "intervention",
        "process_levels": ["high", "medium", "low"],
        "colloquialism_level": 4,
        "target_lang": "zh"
    }
    try:
        response = httpx.post(f"{BASE_URL}/session/start", json=payload, timeout=30.0)
        response.raise_for_status()
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"    Session started. Session ID: {session_id}")
        print(f"    Total sentences to process: {session_data['total_sentences']}")
    except Exception as e:
        print(f"    Start session failed: {e}")
        return

    # 3. Process Sentences
    print("\n[3] Processing sentences...")
    count = 0
    while True:
        # Get current
        try:
            resp = httpx.get(f"{BASE_URL}/session/{session_id}/current", timeout=30.0)
            state = resp.json()
            print(f"    DEBUG: Status={state.get('status')}, Index={state.get('current_index')}")
        except Exception as e:
            print(f"    Get current failed: {e}")
            break
        
        if state.get('status') == 'completed' or state.get('current_sentence') is None:
            print("    Session completed.")
            break
            
        sentence = state['current_sentence']
        sent_id = sentence['id']
        text = sentence['text']
        risk = sentence['risk_level']
        print(f"    Processing sentence {state['current_index'] + 1}: [{risk}] {text[:50]}...")

        # Get suggestions
        sugg_payload = {
            "sentence": text,
            "issues": sentence.get('issues', []),
            "colloquialism_level": 4,
            "target_lang": "zh",
            "whitelist": [],
            "context_baseline": 0
        }
        try:
            sugg_resp = httpx.post(f"{BASE_URL}/suggest/", json=sugg_payload, timeout=30.0)
            if sugg_resp.status_code == 200:
                suggestions = sugg_resp.json()
                rule_sugg = suggestions.get('rule_suggestion')
                if rule_sugg:
                    # Apply rule suggestion
                    new_text = rule_sugg['rewritten']
                    print(f"    Applying suggestion: {new_text[:50]}...")
                    params = {
                        "session_id": session_id,
                        "sentence_id": sent_id,
                        "source": "rule",
                        "modified_text": new_text
                    }
                    apply_resp = httpx.post(f"{BASE_URL}/suggest/apply", params=params, timeout=30.0)
                    if apply_resp.status_code == 200:
                        print("    Applied successfully.")
                    else:
                        print(f"    Apply failed: {apply_resp.text}")
        except Exception as e:
            print(f"    Suggestion/Apply failed: {e}")
        
        # Next
        httpx.post(f"{BASE_URL}/session/{session_id}/next", timeout=30.0)
        count += 1
        if count >= 10: # Limit loop
            break
        time.sleep(0.2)

    # 4. Export
    print("\n[4] Exporting document...")
    try:
        export_resp = httpx.post(f"{BASE_URL}/export/document", params={"session_id": session_id, "format": "txt"}, timeout=30.0)
        if export_resp.status_code == 200:
            export_data = export_resp.json()
            print(f"    Export success: {export_data['filename']}")
            print(f"    Download URL: {export_data['download_url']}")
        else:
            print(f"    Export failed: {export_resp.text}")
    except Exception as e:
        print(f"    Export failed: {e}")

if __name__ == "__main__":
    run_simulation()
