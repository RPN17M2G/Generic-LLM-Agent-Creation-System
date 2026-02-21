"""
Tool executor for agent tool calls.
Extracted from ReActAgent to follow Single Responsibility Principle.
"""
from typing import Dict, Any, Optional
from utils.logger import get_logger
from core.tool import ITool

logger = get_logger(__name__)


class ToolExecutor:
    """
    Executes tool calls for agents.
    Single Responsibility: Execute tools and return observations.
    """
    
    def __init__(self, tools: Dict[str, ITool]):
        """
        Initialize tool executor.
        
        Args:
            tools: Dictionary of available tools (name -> ITool)
        """
        self.tools = tools
    
    def execute(self, tool_call: Dict[str, Any], trace_id: str) -> str:
        """
        Execute a tool call.
        
        Args:
            tool_call: Tool call dictionary with 'name' and 'args'
            trace_id: Trace ID for logging
            
        Returns:
            Observation string
        """
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        
        log = logger.bind(trace_id=trace_id, tool_name=tool_name, tool_args=tool_args)
        log.info("tool_execution_start")
        
        if tool_name not in self.tools:
            error_msg = f"Unknown tool '{tool_name}'. Available tools: {list(self.tools.keys())}"
            log.error("tool_not_found", available_tools=list(self.tools.keys()))
            return f"Error: {error_msg}"
        
        try:
            tool = self.tools[tool_name]
            result = tool.execute(tool_args, trace_id=trace_id)
            log.info("tool_execution_success", result_preview=str(result)[:200])
            return result
        except Exception as e:
            log.error("tool_execution_error", error=str(e), exc_info=True)
            return f"Tool Execution Failed: {e}"

