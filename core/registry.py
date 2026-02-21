"""
Registry system for dynamic registration and discovery of tools.
"""
from typing import Dict, Optional, Type
from utils.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """
    Central registry for tool registration and discovery.
    Implements singleton pattern to ensure single registry instance.
    """
    _instance: Optional['ToolRegistry'] = None
    _tools: Dict[str, Type['ITool']] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._tools = {}
        return cls._instance
    
    def register(self, tool_class: Type['ITool'], name: Optional[str] = None):
        """
        Register a tool class.
        
        Args:
            tool_class: Tool class (must be instantiable)
            name: Optional name override (defaults to class name)
        """
        tool_name = name or tool_class.__name__
        if tool_name in self._tools:
            logger.warning("tool_already_registered", tool_name=tool_name)
        
        self._tools[tool_name] = tool_class
        logger.info("tool_registered", tool_name=tool_name)
    
    def get(self, name: str) -> Optional[Type['ITool']]:
        """Get a tool class by name."""
        return self._tools.get(name)
    
    def list_all(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def create_instance(self, name: str, config: Dict) -> Optional['ITool']:
        """
        Create an instance of a tool.
        
        Args:
            name: Tool name
            config: Configuration dictionary for tool initialization
            
        Returns:
            Tool instance or None if not found
        """
        tool_class = self.get(name)
        if tool_class is None:
            logger.error("tool_not_found", tool_name=name)
            return None
        
        try:
            return tool_class(**config)
        except Exception as e:
            logger.error("tool_instantiation_failed", tool_name=name, error=str(e))
            return None

