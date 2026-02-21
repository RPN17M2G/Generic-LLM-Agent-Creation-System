"""
YAML configuration loader with environment variable substitution.
"""
import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logger import get_logger
from utils.exceptions import ConfigurationError

logger = get_logger(__name__)


class YAMLLoader:
    """
    Loads and processes YAML configuration files with environment variable substitution.
    """
    
    # Pattern to match ${VAR_NAME} or ${VAR_NAME:default_value}
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}:]+)(?::([^}]*))?\}')
    
    @staticmethod
    def _substitute_env_vars(value: Any) -> Any:
        """
        Recursively substitute environment variables in configuration values.
        Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax.
        """
        if isinstance(value, str):
            def replace_match(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.lastindex >= 2 else None
                env_value = os.getenv(var_name, default_value)
                if env_value is None:
                    logger.warning("env_var_not_found", var_name=var_name)
                    return match.group(0)  # Return original if not found and no default
                return env_value
            
            return YAMLLoader.ENV_VAR_PATTERN.sub(replace_match, value)
        elif isinstance(value, dict):
            return {k: YAMLLoader._substitute_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [YAMLLoader._substitute_env_vars(item) for item in value]
        else:
            return value
    
    @staticmethod
    def load_yaml(file_path: str, substitute_env: bool = True) -> Dict[str, Any]:
        """
        Load a YAML file and optionally substitute environment variables.
        
        Args:
            file_path: Path to YAML file
            substitute_env: Whether to substitute environment variables
            
        Returns:
            Parsed YAML as dictionary
            
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        path = Path(file_path)
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}", file_path)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
            
            if content is None:
                raise ConfigurationError(f"Configuration file is empty: {file_path}", file_path)
            
            if substitute_env:
                content = YAMLLoader._substitute_env_vars(content)
            
            logger.info("yaml_loaded", file_path=file_path)
            return content
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML file {file_path}: {e}", file_path) from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration file {file_path}: {e}", file_path) from e
    
    @staticmethod
    def load_from_string(content: str, substitute_env: bool = True) -> Dict[str, Any]:
        """
        Load YAML from a string.
        
        Args:
            content: YAML content as string
            substitute_env: Whether to substitute environment variables
            
        Returns:
            Parsed YAML as dictionary
        """
        try:
            data = yaml.safe_load(content)
            if substitute_env:
                data = YAMLLoader._substitute_env_vars(data)
            return data
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML content: {e}") from e


def load_agent_config(file_path: str) -> Dict[str, Any]:
    """
    Load an agent configuration file.
    
    Args:
        file_path: Path to agent YAML file
        
    Returns:
        Agent configuration dictionary
    """
    config = YAMLLoader.load_yaml(file_path)
    
    if "agent" not in config:
        raise ConfigurationError(
            f"Invalid agent configuration: missing 'agent' key in {file_path}",
            file_path
        )
    
    return config["agent"]

