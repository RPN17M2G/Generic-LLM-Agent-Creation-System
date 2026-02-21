"""
Core framework components for the multi-agent LLM system.
"""

from .agent import IAgent, ReActAgent
from .tool import ITool, BaseTool
from .registry import ToolRegistry

__all__ = [
    'IAgent',
    'ReActAgent',
    'ITool',
    'BaseTool',
    'ToolRegistry',
]

