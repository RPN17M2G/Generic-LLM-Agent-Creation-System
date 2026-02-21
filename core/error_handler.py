"""
Error handler for consistent error handling across the framework.
"""
from typing import Dict, Any, Optional, Tuple
from utils.logger import get_logger
from utils.exceptions import AgentFrameworkError

logger = get_logger(__name__)


class ErrorHandler:
    """
    Centralized error handling.
    Follows Single Responsibility Principle: only handles errors.
    """
    
    @staticmethod
    def handle_parsing_error(
        response_text: str,
        parse_error: Optional[str] = None,
        response_json: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Handle JSON parsing errors.
        
        Args:
            response_text: Raw response text
            parse_error: Error message from parser
            response_json: Partially parsed JSON (if any)
            
        Returns:
            Error observation message
        """
        error_details = parse_error or "Unknown parsing error"
        observation = (
            f"❌ ERROR: Invalid JSON response format. "
            f"You must respond ONLY with valid JSON (no text labels, no markdown, no explanations). "
            f"⚠️ CRITICAL: Use this EXACT format: "
            f'{{\"thought\": \"your reasoning here\", \"tool_call\": {{\"name\": \"tool_name\", \"args\": {{\"param\": \"value\"}}}}}}. '
            f"The error was: {error_details}. "
            f"Your response was: {response_text[:300]}"
        )
        return observation
    
    @staticmethod
    def handle_missing_field(
        missing_field: str,
        response_json: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Handle missing required field errors.
        
        Args:
            missing_field: Name of missing field
            response_json: Parsed response (if any)
            
        Returns:
            Error observation message
        """
        provided_keys = list(response_json.keys()) if response_json else []
        observation = (
            f"❌ ERROR: Your response is missing required field: {missing_field}. "
            f"You provided: {provided_keys}. "
            f"⚠️ CRITICAL: You MUST include BOTH 'thought' AND 'tool_call' in EVERY response. "
            f"Use this EXACT format: "
            f'{{\"thought\": \"your reasoning here\", \"tool_call\": {{\"name\": \"tool_name\", \"args\": {{}}}}}}. '
            f"Never omit either field."
        )
        return observation
    
    @staticmethod
    def handle_tool_error(
        tool_name: str,
        error: Exception,
        available_tools: Optional[list] = None
    ) -> str:
        """
        Handle tool execution errors.
        
        Args:
            tool_name: Name of the tool
            error: Exception that occurred
            available_tools: List of available tools
            
        Returns:
            Error observation message
        """
        error_msg = str(error)
        if available_tools and tool_name not in available_tools:
            return f"Error: Unknown tool '{tool_name}'. Available tools: {available_tools}"
        return f"Tool Execution Failed: {error_msg}"
    
    @staticmethod
    def handle_validation_error(
        field_name: str,
        expected_type: str,
        actual_type: str
    ) -> str:
        """
        Handle validation errors.
        
        Args:
            field_name: Name of the field
            expected_type: Expected type
            actual_type: Actual type received
            
        Returns:
            Error observation message
        """
        return (
            f"Error: {field_name} must be {expected_type}, got {actual_type}. "
            f"Please provide a valid {field_name}."
        )

