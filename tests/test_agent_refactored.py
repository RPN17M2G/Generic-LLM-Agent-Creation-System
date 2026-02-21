"""
Tests for refactored ReActAgent with new components.
"""
import pytest
from unittest.mock import Mock, MagicMock
from core.agent import ReActAgent, IAgent
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


class TestReActAgent:
    """Tests for ReActAgent."""
    
    def test_agent_init(self):
        """Test agent initialization."""
        mock_llm = Mock()
        
        tools = [MockTool("tool1")]
        agent = ReActAgent(
            name="test_agent",
            description="Test agent",
            orchestrator_llm=mock_llm,
            orchestrator_model_name="test-model",
            tools=tools,
            system_prompt_template="Test prompt",
            max_iterations=5
        )
        
        assert agent.get_name() == "test_agent"
        assert agent.get_description() == "Test agent"
        assert isinstance(agent.response_parser, ResponseParser)
        assert isinstance(agent.tool_executor, ToolExecutor)
        assert isinstance(agent.error_handler, ErrorHandler)
    
    def test_agent_finish_tool(self):
        """Test agent with finish tool call."""
        mock_llm = Mock()
        
        # Mock LLM response with finish tool
        mock_llm.chat.return_value = {
            'message': {
                'content': '{"thought": "Done", "tool_call": {"name": "finish", "args": {"answer": "Final answer"}}}'
            }
        }
        
        tools = []
        agent = ReActAgent(
            name="test_agent",
            description="Test",
            orchestrator_llm=mock_llm,
            orchestrator_model_name="test-model",
            tools=tools,
            system_prompt_template="Test",
            max_iterations=5
        )
        
        result = agent.run("test query")
        
        assert result == "Final answer"
    
    def test_agent_tool_execution(self):
        """Test agent tool execution."""
        mock_llm = Mock()
        
        # First call: use tool, second call: finish
        mock_llm.chat.side_effect = [
            {
                'message': {
                    'content': '{"thought": "Use tool", "tool_call": {"name": "tool1", "args": {}}}'
                }
            },
            {
                'message': {
                    'content': '{"thought": "Done", "tool_call": {"name": "finish", "args": {"answer": "Result"}}}'
                }
            }
        ]
        
        tools = [MockTool("tool1", "tool result")]
        agent = ReActAgent(
            name="test_agent",
            description="Test",
            orchestrator_llm=mock_llm,
            orchestrator_model_name="test-model",
            tools=tools,
            system_prompt_template="Test",
            max_iterations=5
        )
        
        result = agent.run("test query")
        
        assert result == "Result"
        assert mock_llm.chat.call_count == 2
    
    def test_agent_max_iterations(self):
        """Test agent max iterations."""
        mock_llm = Mock()
        
        # Always return invalid response (missing tool_call)
        mock_llm.chat.return_value = {
            'message': {
                'content': '{"thought": "Test"}'
            }
        }
        
        tools = []
        agent = ReActAgent(
            name="test_agent",
            description="Test",
            orchestrator_llm=mock_llm,
            orchestrator_model_name="test-model",
            tools=tools,
            system_prompt_template="Test",
            max_iterations=3
        )
        
        result = agent.run("test query")
        
        assert "unable to answer" in result.lower()
        assert mock_llm.chat.call_count >= 3

