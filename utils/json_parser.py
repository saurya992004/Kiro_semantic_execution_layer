import json
import re
import logging

logger = logging.getLogger(__name__)


def extract_json(text: str):
    """
    Extracts JSON object or array from LLM response.
    Handles both JSON objects {} and JSON arrays [].
    Returns parsed JSON or empty dict/list on failure.
    """
    
    if not text or not isinstance(text, str):
        return {}
    
    # Try to find and parse JSON array first [...]
    try:
        array_match = re.search(r"\[.*\]", text, re.DOTALL)
        if array_match:
            json_str = array_match.group()
            # Try to parse as-is first
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # If fails, try to find the valid JSON boundary
                for end_pos in range(len(json_str), 0, -1):
                    try:
                        return json.loads(json_str[:end_pos])
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        logger.debug(f"Array parsing failed: {e}")
    
    # Try to find and parse JSON object {...}
    try:
        object_match = re.search(r"\{.*\}", text, re.DOTALL)
        if object_match:
            json_str = object_match.group()
            # Try to parse as-is first
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # If fails, try to find the valid JSON boundary
                for end_pos in range(len(json_str), 0, -1):
                    try:
                        return json.loads(json_str[:end_pos])
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        logger.debug(f"Object parsing failed: {e}")
    
    logger.warning(f"Could not extract JSON from: {text[:100]}...")
    return {}

