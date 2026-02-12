import json
import re


def extract_json(text: str) -> dict:
    """
    Extracts JSON object from LLM response.
    """

    try:
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print("JSON parse error:", e)

    return {}
