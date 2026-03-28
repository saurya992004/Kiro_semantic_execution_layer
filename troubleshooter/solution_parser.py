import json
import re

def parse_solution(raw_response: str) -> dict:
    if not raw_response:
        return None
        
    try:
        # Step 1: Strip markdown code fences
        clean = raw_response.strip()
        
        # Step 2: Try to find JSON within ```json ... ``` blocks first
        json_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', clean, re.DOTALL)
        if json_blocks:
            # Try each block until one parses
            for block in json_blocks:
                try:
                    result = json.loads(block.strip())
                    if isinstance(result, dict) and "commands" in result:
                        return result
                except json.JSONDecodeError:
                    continue
        
        # Step 3: Find the first { ... } that contains "commands" using brace matching
        start = clean.find('{')
        while start != -1:
            depth = 0
            for i in range(start, len(clean)):
                if clean[i] == '{':
                    depth += 1
                elif clean[i] == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = clean[start:i+1]
                        try:
                            result = json.loads(candidate)
                            if isinstance(result, dict) and "commands" in result:
                                return result
                        except json.JSONDecodeError:
                            pass
                        break
            start = clean.find('{', start + 1)
        
        # Step 4: Last resort — try the whole thing
        return json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"Failed to parse the Vision model output as JSON: {e}")
        print(f"Raw output: {raw_response[:200]}")
        return None
