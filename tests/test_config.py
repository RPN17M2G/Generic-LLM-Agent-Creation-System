"""
Tests for configuration management.
"""
import pytest
import yaml
import tempfile
import os
from pathlib import Path
from config.yaml_loader import YAMLLoader, load_agent_config
from config.schema_validator import SchemaValidator
from config.config_manager import ConfigManager
from utils.exceptions import ConfigurationError, ValidationError


class TestYAMLLoader:
    """Tests for YAML loader."""
    
    def test_load_yaml_file(self):
        """Test loading YAML from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"test": "value"}, f)
            temp_path = f.name
        
        try:
            result = YAMLLoader.load_yaml(temp_path)
            assert result["test"] == "value"
        finally:
            os.unlink(temp_path)
    
    def test_load_yaml_missing_file(self):
        """Test loading non-existent file."""
        with pytest.raises(ConfigurationError):
            YAMLLoader.load_yaml("nonexistent.yaml")
    
    def test_load_yaml_with_env_substitution(self):
        """Test environment variable substitution."""
        os.environ["TEST_VAR"] = "substituted_value"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("test: ${TEST_VAR}")
            temp_path = f.name
        
        try:
            result = YAMLLoader.load_yaml(temp_path)
            assert result["test"] == "substituted_value"
        finally:
            os.unlink(temp_path)
            if "TEST_VAR" in os.environ:
                del os.environ["TEST_VAR"]
    
    def test_load_yaml_with_default(self):
        """Test environment variable with default value."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("test: ${NONEXISTENT_VAR:default_value}")
            temp_path = f.name
        
        try:
            result = YAMLLoader.load_yaml(temp_path)
            assert result["test"] == "default_value"
        finally:
            os.unlink(temp_path)
    
    def test_load_agent_config(self):
        """Test loading agent configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"agent": {"name": "test_agent"}}, f)
            temp_path = f.name
        
        try:
            result = load_agent_config(temp_path)
            assert result["name"] == "test_agent"
        finally:
            os.unlink(temp_path)
    
    def test_load_agent_config_missing_key(self):
        """Test loading agent config without 'agent' key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"not_agent": {}}, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError):
                load_agent_config(temp_path)
        finally:
            os.unlink(temp_path)


class TestSchemaValidator:
    """Tests for schema validator."""
    
    def test_validate_agent_config_valid(self):
        """Test validation of valid agent config."""
        config = {
            "name": "test_agent",
            "llm": {
                "provider": "ollama",
                "orchestrator_model": "test-model"
            }
        }
        
        is_valid, error = SchemaValidator.validate_agent_config(config)
        assert is_valid is True
        assert error is None
    
    def test_validate_agent_config_missing_required(self):
        """Test validation with missing required fields."""
        config = {
            "name": "test_agent"
            # Missing llm
        }
        
        is_valid, error = SchemaValidator.validate_agent_config(config)
        assert is_valid is False
        assert error is not None


class TestConfigManager:
    """Tests for configuration manager."""
    
    def test_config_manager_init(self):
        """Test configuration manager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(config_dir=temp_dir)
            assert manager.config_dir == Path(temp_dir)
    
    def test_list_agents(self):
        """Test listing agents."""
        with tempfile.TemporaryDirectory() as temp_dir:
            agents_dir = Path(temp_dir) / "agents"
            agents_dir.mkdir()
            
            # Create test agent file
            agent_file = agents_dir / "test_agent.yaml"
            with open(agent_file, 'w') as f:
                yaml.dump({"agent": {"name": "test_agent"}}, f)
            
            manager = ConfigManager(config_dir=temp_dir)
            agents = manager.list_agents()
            
            assert "test_agent" in agents
    
    def test_load_agent(self):
        """Test loading agent configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            agents_dir = Path(temp_dir) / "agents"
            agents_dir.mkdir()
            
            agent_file = agents_dir / "test_agent.yaml"
            with open(agent_file, 'w') as f:
                yaml.dump({
                    "agent": {
                        "name": "test_agent",
                        "llm": {
                            "provider": "ollama",
                            "orchestrator_model": "test-model"
                        }
                    }
                }, f)
            
            manager = ConfigManager(config_dir=temp_dir)
            config = manager.load_agent("test_agent", validate=False)
            
            assert config["name"] == "test_agent"
    
    def test_load_agent_not_found(self):
        """Test loading non-existent agent."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(config_dir=temp_dir)
            
            with pytest.raises(ConfigurationError):
                manager.load_agent("nonexistent_agent")

