"""
Base tool interface and implementation.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class ITool(ABC):
    """
    Interface for all tools in the framework.
    Tools are executable units that agents can use to perform actions.
    """
    
    @abstractmethod
    def execute(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """
        Execute the tool with given arguments.
        
        Args:
            args: Dictionary of tool arguments
            trace_id: Optional trace ID for logging
            
        Returns:
            Result of tool execution as a string
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the tool's name."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return the tool's description."""
        pass
    
    @abstractmethod
    def get_parameter_schema(self) -> Dict[str, Any]:
        """
        Return the parameter schema for this tool.
        
        Returns:
            Dictionary describing parameter names, types, and requirements
        """
        pass


class BaseTool(ITool):
    """
    Base implementation of ITool with common functionality.
    Provides validation, logging, and error handling.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        parameter_schema: Dict[str, Any]
    ):
        """
        Initialize the base tool.
        
        Args:
            name: Tool name (must be unique)
            description: Human-readable description
            parameter_schema: Schema defining expected parameters
                Format: {
                    "param_name": {
                        "type": "str|int|float|bool|list|dict",
                        "required": bool,
                        "description": str,
                        "default": optional_value
                    }
                }
        """
        self._name = name
        self._description = description
        self._parameter_schema = parameter_schema
    
    def get_name(self) -> str:
        return self._name
    
    def get_description(self) -> str:
        return self._description
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return self._parameter_schema.copy()
    
    def _validate_args(self, args: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate arguments against the parameter schema.
        
        Returns:
            (is_valid, error_message)
        """
        for param_name, param_spec in self._parameter_schema.items():
            is_required = param_spec.get("required", False)
            param_type = param_spec.get("type", "str")
            
            if param_name not in args:
                if is_required:
                    return False, f"Required parameter '{param_name}' is missing."
                # Use default if available
                if "default" in param_spec:
                    args[param_name] = param_spec["default"]
                continue
            
            # Type validation
            value = args[param_name]
            if not self._check_type(value, param_type):
                return False, f"Parameter '{param_name}' has wrong type. Expected {param_type}, got {type(value).__name__}."
        
        return True, None
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
        }
        
        expected_python_type = type_map.get(expected_type.lower())
        if expected_python_type is None:
            return True  # Unknown type, skip validation
        
        return isinstance(value, expected_python_type)
    
    def execute(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """
        Execute the tool with validation.
        Subclasses should implement _execute_impl.
        """
        log = logger.bind(trace_id=trace_id, tool_name=self._name)
        
        # Validate arguments
        is_valid, error_msg = self._validate_args(args)
        if not is_valid:
            log.warning("tool_validation_failed", error=error_msg)
            return f"Error: {error_msg}"
        
        try:
            log.info("tool_execution_start", args=args)
            result = self._execute_impl(args, trace_id)
            log.info("tool_execution_success", result_preview=str(result)[:200])
            return result
        except Exception as e:
            log.error("tool_execution_error", error=str(e), exc_info=True)
            return f"Tool execution failed: {e}"
    
    @abstractmethod
    def _execute_impl(self, args: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """
        Implementation of tool execution.
        Subclasses must implement this method.
        """
        pass

