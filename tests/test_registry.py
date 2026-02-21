"""
Tests for registry systems.
"""
import pytest
from unittest.mock import Mock
from core.registry import ToolRegistry
from core.tool import ITool, BaseTool


class TestToolRegistry:
    """Tests for tool registry."""
    
    def test_tool_registry_singleton(self):
        """Test that registry is a singleton."""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()
        
        assert registry1 is registry2
    
    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        
        class TestTool(BaseTool):
            def _execute_impl(self, args, trace_id=None):
                return "test"
        
        registry.register(TestTool, "test_tool")
        assert "test_tool" in registry.list_all()
    
    def test_get_tool(self):
        """Test getting a tool."""
        registry = ToolRegistry()
        
        class TestTool(BaseTool):
            def _execute_impl(self, args, trace_id=None):
                return "test"
        
        registry.register(TestTool, "test_tool")
        tool_class = registry.get("test_tool")
        
        assert tool_class == TestTool
    
    def test_get_nonexistent_tool(self):
        """Test getting non-existent tool."""
        registry = ToolRegistry()
        tool_class = registry.get("nonexistent")
        
        assert tool_class is None
    
    def test_create_tool_instance(self):
        """Test creating tool instance."""
        registry = ToolRegistry()
        
        class TestTool(BaseTool):
            def __init__(self, test_param):
                super().__init__("test", "test", {})
                self.test_param = test_param
            
            def _execute_impl(self, args, trace_id=None):
                return "test"
        
        registry.register(TestTool, "test_tool")
        instance = registry.create_instance("test_tool", {"test_param": "value"})
        
        assert instance is not None
        assert instance.test_param == "value"
    
    def test_create_nonexistent_tool_instance(self):
        """Test creating instance of non-existent tool."""
        registry = ToolRegistry()
        instance = registry.create_instance("nonexistent", {})
        
        assert instance is None

