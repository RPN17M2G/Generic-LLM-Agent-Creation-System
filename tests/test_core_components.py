"""
Tests for core components (ResponseParser, ToolExecutor, ErrorHandler).
"""
import pytest
from unittest.mock import Mock, MagicMock
from core.response_parser import ResponseParser
from core.tool_executor import ToolExecutor
from core.error_handler import ErrorHandler
from core.tool import ITool


class MockTool(ITool):
    """Mock tool for testing."""
    
    def __init__(self, name: str, result: str = "success"):
        self._name = name
        self._result = result
    
    def execute(self, args: dict, trace_id: str = None) -> str:
        return self._result
    
    def get_name(self) -> str:
        return self._name
    
    def get_description(self) -> str:
        return f"Mock tool {self._name}"
    
    def get_parameter_schema(self) -> dict:
        return {}


class TestResponseParser:
    """Tests for ResponseParser."""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""
        parser = ResponseParser(response_format="json")
        response = '{"thought": "I need to query", "tool_call": {"name": "generate_sql", "args": {"query": "test"}}}'
        
        response_json, thought, tool_call, error = parser.parse(response)
        
        assert error is None
        assert thought == "I need to query"
        assert tool_call is not None
        assert tool_call["name"] == "generate_sql"
    
    def test_parse_missing_thought(self):
        """Test parsing response with missing thought."""
        parser = ResponseParser(response_format="json")
        response = '{"tool_call": {"name": "generate_sql", "args": {}}}'
        
        response_json, thought, tool_call, error = parser.parse(response)
        
        # Should add default thought
        assert error is None
        assert thought is not None
        assert tool_call is not None
    
    def test_parse_missing_tool_call(self):
        """Test parsing response with missing tool_call."""
        parser = ResponseParser(response_format="json")
        response = '{"thought": "I need to query"}'
        
        response_json, thought, tool_call, error = parser.parse(response)
        
        assert error is not None
        assert "tool_call" in error.lower()
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        parser = ResponseParser(response_format="json")
        response = "This is not JSON"
        
        response_json, thought, tool_call, error = parser.parse(response)
        
        assert error is not None
        assert response_json is None
    
    def test_parse_with_markdown(self):
        """Test parsing JSON wrapped in markdown."""
        parser = ResponseParser(response_format="json")
        response = '```json\n{"thought": "test", "tool_call": {"name": "test", "args": {}}}\n```'
        
        response_json, thought, tool_call, error = parser.parse(response)
        
        assert error is None
        assert tool_call is not None


class TestToolExecutor:
    """Tests for ToolExecutor."""
    
    def test_execute_success(self):
        """Test successful tool execution."""
        tool1 = MockTool("tool1", "result1")
        tool2 = MockTool("tool2", "result2")
        tools = {"tool1": tool1, "tool2": tool2}
        
        executor = ToolExecutor(tools=tools)
        result = executor.execute({"name": "tool1", "args": {}}, "trace-123")
        
        assert result == "result1"
    
    def test_execute_unknown_tool(self):
        """Test execution with unknown tool."""
        tools = {"tool1": MockTool("tool1")}
        executor = ToolExecutor(tools=tools)
        
        result = executor.execute({"name": "unknown_tool", "args": {}}, "trace-123")
        
        assert "Error" in result
        assert "unknown_tool" in result
    
    def test_execute_tool_exception(self):
        """Test tool execution with exception."""
        class FailingTool(ITool):
            def execute(self, args: dict, trace_id: str = None) -> str:
                raise Exception("Tool failed")
            
            def get_name(self) -> str:
                return "failing_tool"
            
            def get_description(self) -> str:
                return "Failing tool"
            
            def get_parameter_schema(self) -> dict:
                return {}
        
        tools = {"failing_tool": FailingTool()}
        executor = ToolExecutor(tools=tools)
        
        result = executor.execute({"name": "failing_tool", "args": {}}, "trace-123")
        
        assert "Failed" in result
        assert "Tool failed" in result


class TestErrorHandler:
    """Tests for ErrorHandler."""
    
    def test_handle_parsing_error(self):
        """Test parsing error handling."""
        error_msg = ErrorHandler.handle_parsing_error(
            "invalid response",
            "JSON parse error",
            None
        )
        
        assert "ERROR" in error_msg
        assert "JSON" in error_msg
    
    def test_handle_missing_field(self):
        """Test missing field error handling."""
        error_msg = ErrorHandler.handle_missing_field("tool_call", {"thought": "test"})
        
        assert "ERROR" in error_msg
        assert "tool_call" in error_msg
    
    def test_handle_tool_error(self):
        """Test tool error handling."""
        error_msg = ErrorHandler.handle_tool_error(
            "test_tool",
            Exception("Tool failed"),
            ["tool1", "tool2"]
        )
        
        assert "Error" in error_msg or "Failed" in error_msg
    
    def test_handle_validation_error(self):
        """Test validation error handling."""
        error_msg = ErrorHandler.handle_validation_error(
            "field_name",
            "string",
            "int"
        )
        
        assert "field_name" in error_msg
        assert "string" in error_msg
        assert "int" in error_msg

