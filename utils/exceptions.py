"""
Custom exception hierarchy for the framework.
"""
from typing import Optional


class AgentFrameworkError(Exception):
    """Base exception for all framework errors."""
    pass


class AgentError(AgentFrameworkError):
    """Base exception for agent-related errors."""
    def __init__(self, message: str, agent_name: Optional[str] = None):
        super().__init__(message)
        self.agent_name = agent_name


class ToolExecutionError(AgentFrameworkError):
    """Exception raised when tool execution fails."""
    def __init__(self, message: str, tool_name: Optional[str] = None):
        super().__init__(message)
        self.tool_name = tool_name


class DatabaseError(AgentFrameworkError):
    """Exception raised when database operations fail."""
    def __init__(self, message: str, database_type: Optional[str] = None):
        super().__init__(message)
        self.database_type = database_type


class LLMError(AgentFrameworkError):
    """Exception raised when LLM API calls fail."""
    def __init__(self, message: str, model_name: Optional[str] = None):
        super().__init__(message)
        self.model_name = model_name


class ConfigurationError(AgentFrameworkError):
    """Exception raised when configuration is invalid."""
    def __init__(self, message: str, config_path: Optional[str] = None):
        super().__init__(message)
        self.config_path = config_path


class ValidationError(AgentFrameworkError):
    """Exception raised when validation fails."""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field
