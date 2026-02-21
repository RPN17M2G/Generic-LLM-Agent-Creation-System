"""
Response parser for LLM responses.
Extracted from ReActAgent to follow Single Responsibility Principle.
"""
from typing import Dict, Any, Optional, Tuple
from utils.logger import get_logger
from utils.json_parser import parse_llm_response

logger = get_logger(__name__)


class ResponseParser:
    """
    Parses and validates LLM responses.
    Single Responsibility: Parse responses into structured format.
    """
    
    def __init__(self, response_format: str = "json"):
        """
        Initialize response parser.
        
        Args:
            response_format: Expected format ("json" or "text")
        """
        self.response_format = response_format
    
    def parse(
        self,
        response_text: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        """
        Parse LLM response.
        
        Args:
            response_text: Raw response text from LLM
            
        Returns:
            Tuple of (response_json, thought, tool_call, error_message)
            If parsing fails, returns (None, None, None, error_message)
        """
        if self.response_format == "json":
            return self._parse_json(response_text)
        else:
            return self._parse_text(response_text)
    
    def _parse_json(self, response_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[Dict[str, Any]], Optional[str]]:
        """Parse JSON response."""
        response_json, parse_error = parse_llm_response(
            response_text,
            expected_keys=None  # Don't fail on missing keys, add defaults instead
        )
        
        if parse_error or not response_json:
            return None, None, None, parse_error or "Failed to parse JSON"
        
        # Handle missing fields gracefully - add defaults
        if "thought" not in response_json:
            logger.warning("response_missing_thought", response_keys=list(response_json.keys()))
            # Generate default thought based on tool_call if available
            if "tool_call" in response_json and isinstance(response_json.get("tool_call"), dict):
                tool_name = response_json["tool_call"].get("name", "unknown_tool")
                response_json["thought"] = f"Proceeding with {tool_name} tool call."
            else:
                response_json["thought"] = "Continuing with the task."
        
        if "tool_call" not in response_json:
            logger.warning("response_missing_tool_call", response_keys=list(response_json.keys()))
            return None, None, None, "Missing required 'tool_call' field"
        
        thought = response_json.get("thought", "Continuing with the task.")
        tool_call = response_json.get("tool_call")
        
        # Handle case where LLM returns tool_call directly
        if not tool_call and "name" in response_json and "args" in response_json:
            logger.warning("response_tool_call_direct_format", response_json=response_json)
            tool_call = response_json
            thought = "[Tool call provided directly]"
            response_json = {"thought": thought, "tool_call": tool_call}
        
        return response_json, thought, tool_call, None
    
    def _parse_text(self, response_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[Dict[str, Any]], Optional[str]]:
        """Parse text response (fallback)."""
        # For text format, try to extract tool call
        thought = response_text
        tool_call = self._extract_tool_call_from_text(response_text)
        return None, thought, tool_call, None
    
    def _extract_tool_call_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract tool call from text (simple implementation)."""
        # This is a fallback - JSON format is preferred
        # Could be enhanced with regex or NLP
        return None

