import json

def parse_solution(raw_response: str) -> dict:
    if not raw_response:
        return None
        
    try:
        # Clean up potential markdown blocks
        clean_resp = raw_response.strip()
        if clean_resp.startswith("```json"):
            clean_resp = clean_resp[7:]
        elif clean_resp.startswith("```"):
            clean_resp = clean_resp[3:]
            
        if clean_resp.endswith("```"):
            clean_resp = clean_resp[:-3]
            
        return json.loads(clean_resp.strip())
    except json.JSONDecodeError as e:
        print(f"Failed to parse the Vision model output as JSON: {e}")
        print(f"Raw output: {raw_response}")
        return None
