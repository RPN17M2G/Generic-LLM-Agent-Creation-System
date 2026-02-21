"""
Robust JSON parsing utilities for LLM responses.
"""
import json
import re
from typing import Dict, Any, Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_json_from_text(text: str) -> Tuple[Optional[str], bool]:
    """
    Extract JSON object from text that may contain extra content.
    
    Args:
        text: Text that may contain JSON
        
    Returns:
        Tuple of (extracted_json_string, success_flag)
    """
    if not text or not isinstance(text, str):
        return None, False
    
    text_clean = text.strip()
    
    # Handle common text prefixes that LLMs sometimes add
    # Remove "Thought:" or "Tool call:" prefixes
    text_clean = re.sub(r'^(?:Thought|Tool call|Response):\s*', '', text_clean, flags=re.IGNORECASE | re.MULTILINE)
    text_clean = text_clean.strip()
    
    # Remove markdown code blocks if present
    if text_clean.startswith("```"):
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', text_clean, re.DOTALL)
        if match:
            text_clean = match.group(1).strip()
    
    # Try direct parsing first (most reliable)
    try:
        test_parse = json.loads(text_clean)
        if isinstance(test_parse, dict):
            logger.debug("json_parsed_directly", keys=list(test_parse.keys()))
            return text_clean, True
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from text that has "Thought:" and "Tool call:" as separate lines
    # Pattern: Thought: ... Tool call: {...}
    thought_tool_match = re.search(
        r'Thought:\s*(.*?)\s*Tool\s+call:\s*(\{.*\})',
        text_clean,
        re.DOTALL | re.IGNORECASE
    )
    if thought_tool_match:
        thought_text = thought_tool_match.group(1).strip()
        tool_call_text = thought_tool_match.group(2).strip()
        try:
            tool_call_json = json.loads(tool_call_text)
            # Construct proper JSON structure
            constructed_json = {
                "thought": thought_text,
                "tool_call": tool_call_json
            }
            json_str = json.dumps(constructed_json)
            logger.debug("json_constructed_from_thought_toolcall")
            return json_str, True
        except json.JSONDecodeError:
            pass
    
    # Try to find the outermost JSON object using balanced braces
    brace_count = 0
    start_idx = -1
    for i, char in enumerate(text_clean):
        if char == '{':
            if start_idx == -1:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                # Found complete outermost JSON object
                extracted = text_clean[start_idx:i+1]
                try:
                    test = json.loads(extracted)
                    if isinstance(test, dict):
                        logger.debug("json_extracted_with_braces", keys=list(test.keys()))
                        return extracted, True
                except json.JSONDecodeError:
                    pass
    
    # Fallback: try regex to find any JSON object
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text_clean, re.DOTALL)
    if json_match:
        potential_json = json_match.group(0)
        try:
            test = json.loads(potential_json)
            if isinstance(test, dict):
                logger.debug("json_extracted_with_regex", keys=list(test.keys()))
                return potential_json, True
        except json.JSONDecodeError:
            pass
    
    return None, False


def parse_llm_response(
    response_text: str,
    expected_keys: Optional[list[str]] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse LLM response text into a JSON dictionary.
    
    Args:
        response_text: Raw response text from LLM
        expected_keys: Optional list of expected top-level keys
        
    Returns:
        Tuple of (parsed_dict, error_message)
        If parsing fails, returns (None, error_message)
    """
    if not response_text:
        return None, "Empty response text"
    
    # Extract JSON from text
    json_str, success = extract_json_from_text(response_text)
    if not success or not json_str:
        return None, f"Failed to extract valid JSON from response: {response_text[:200]}"
    
    # Parse JSON
    try:
        parsed = json.loads(json_str)
        if not isinstance(parsed, dict):
            return None, f"Parsed JSON is not a dictionary, got {type(parsed).__name__}"
        
        # Note: We don't fail on missing keys here - let the caller handle defaults
        # This allows graceful degradation when LLM omits fields
        if expected_keys:
            missing_keys = [key for key in expected_keys if key not in parsed]
            if missing_keys:
                # Return the parsed dict anyway, with a warning about missing keys
                # The caller can add defaults
                logger.debug("json_missing_expected_keys", 
                           missing_keys=missing_keys,
                           present_keys=list(parsed.keys()))
                # Don't return error - return the partial dict with a note
                return parsed, None  # Changed: return partial dict instead of error
        
        return parsed, None
        
    except json.JSONDecodeError as e:
        error_msg = f"JSON decode error: {e} at position {getattr(e, 'pos', 'unknown')}"
        logger.error("json_parse_error", error=str(e), json_str=json_str[:500])
        return None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error parsing JSON: {e}"
        logger.error("json_parse_unexpected_error", error=str(e), exc_info=True)
        return None, error_msg

