"""
YAML schema validation using JSON Schema.
"""
from typing import Dict, Any, Optional
import jsonschema
from utils.logger import get_logger
from utils.exceptions import ValidationError

logger = get_logger(__name__)


class SchemaValidator:
    """
    Validates YAML configurations against JSON schemas.
    """
    
    # Agent configuration schema
    AGENT_SCHEMA = {
        "type": "object",
        "required": ["name", "llm"],
        "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "llm": {
                "type": "object",
                "required": ["provider", "orchestrator_model"],
                "properties": {
                    "provider": {"type": "string", "enum": ["ollama"]},
                    "orchestrator_model": {"type": "string"},
                    "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                    "max_tokens": {"type": "integer", "minimum": 1},
                }
            },
            "database": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "connection": {"type": "object"},
                    "allowed_tables": {"type": "array", "items": {"type": "string"}},
                }
            },
            "tools": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "type"],
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "config": {"type": "object"},
                    }
                }
            },
            "security": {
                "type": "object",
                "properties": {
                    "pii_masking": {"type": "boolean"},
                    "query_validation": {"type": "boolean"},
                    "allowed_operations": {"type": "array", "items": {"type": "string"}},
                }
            },
            "behavior": {
                "type": "object",
                "properties": {
                    "max_iterations": {"type": "integer", "minimum": 1},
                    "enable_self_correction": {"type": "boolean"},
                    "response_format": {"type": "string", "enum": ["json", "text"]},
                }
            },
        }
    }
    
    @staticmethod
    def validate_agent_config(config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate an agent configuration against the schema.
        
        Returns:
            (is_valid, error_message)
        """
        try:
            jsonschema.validate(instance=config, schema=SchemaValidator.AGENT_SCHEMA)
            return True, None
        except jsonschema.ValidationError as e:
            error_msg = f"Validation error at {'.'.join(str(p) for p in e.path)}: {e.message}"
            logger.warning("agent_config_validation_failed", error=error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Schema validation error: {e}"
            logger.error("schema_validation_error", error=str(e), exc_info=True)
            return False, error_msg
    
    @staticmethod
    def validate_and_raise(config: Dict[str, Any], schema_type: str = "agent"):
        """
        Validate configuration and raise exception if invalid.
        
        Args:
            config: Configuration dictionary
            schema_type: "agent" (only supported type)
            
        Raises:
            ValidationError: If validation fails
        """
        if schema_type == "agent":
            is_valid, error_msg = SchemaValidator.validate_agent_config(config)
        else:
            raise ValueError(f"Unknown schema type: {schema_type}")
        
        if not is_valid:
            raise ValidationError(error_msg or "Configuration validation failed")

