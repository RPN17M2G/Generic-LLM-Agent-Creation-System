"""
Configuration manager for loading and managing agent configurations.
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from utils.logger import get_logger
from .yaml_loader import load_agent_config
from .schema_validator import SchemaValidator
from utils.exceptions import ConfigurationError

logger = get_logger(__name__)


class ConfigManager:
    """
    Manages loading and validation of agent configurations.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Base directory for configuration files (default: ./config)
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.agents_dir = self.config_dir / "agents"
        
        # Ensure directories exist
        self.agents_dir.mkdir(parents=True, exist_ok=True)
    
    def load_agent(self, agent_name: str, validate: bool = True) -> Dict[str, Any]:
        """
        Load an agent configuration by name.
        
        Args:
            agent_name: Name of the agent (file name without .yaml extension)
            validate: Whether to validate against schema
            
        Returns:
            Agent configuration dictionary
            
        Raises:
            ConfigurationError: If agent not found or invalid
        """
        agent_file = self.agents_dir / f"{agent_name}.yaml"
        
        if not agent_file.exists():
            raise ConfigurationError(
                f"Agent configuration not found: {agent_name}",
                str(agent_file)
            )
        
        config = load_agent_config(str(agent_file))
        
        if validate:
            is_valid, error_msg = SchemaValidator.validate_agent_config(config)
            if not is_valid:
                raise ConfigurationError(
                    f"Invalid agent configuration for {agent_name}: {error_msg}",
                    str(agent_file)
                )
        
        logger.info("agent_config_loaded", agent_name=agent_name)
        return config
    
    def list_agents(self) -> List[str]:
        """
        List all available agent configurations.
        
        Returns:
            List of agent names
        """
        agents = []
        for file in self.agents_dir.glob("*.yaml"):
            agents.append(file.stem)
        return sorted(agents)

