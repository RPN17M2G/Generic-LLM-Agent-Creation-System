"""
Input validation and sanitization utilities.
"""
from typing import Any, Dict, Optional, List
from utils.logger import get_logger
from utils.exceptions import ValidationError

logger = get_logger(__name__)


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that required fields are present in a dictionary.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If any required field is missing
    """
    missing = [field for field in required_fields if field not in data or data[field] is None]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")


def validate_string_field(
    value: Any,
    field_name: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    allowed_values: Optional[List[str]] = None
) -> str:
    """
    Validate a string field.
    
    Args:
        value: Value to validate
        field_name: Name of the field (for error messages)
        min_length: Minimum length (optional)
        max_length: Maximum length (optional)
        allowed_values: List of allowed values (optional)
        
    Returns:
        Validated string value
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string, got {type(value).__name__}")
    
    if min_length is not None and len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")
    
    if max_length is not None and len(value) > max_length:
        raise ValidationError(f"{field_name} must be at most {max_length} characters")
    
    if allowed_values is not None and value not in allowed_values:
        raise ValidationError(f"{field_name} must be one of {allowed_values}, got '{value}'")
    
    return value


def sanitize_string(value: Any, max_length: Optional[int] = None) -> str:
    """
    Sanitize a string value.
    
    Args:
        value: Value to sanitize
        max_length: Maximum length to truncate to
        
    Returns:
        Sanitized string
    """
    if value is None:
        return ""
    
    sanitized = str(value).strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        logger.warning("string_truncated", original_length=len(str(value)), truncated_length=max_length)
    
    return sanitized


def validate_dict_structure(
    data: Dict[str, Any],
    schema: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate dictionary structure against a schema.
    
    Args:
        data: Dictionary to validate
        schema: Schema definition
            Format: {
                "field_name": {
                    "type": "str|int|float|bool|list|dict",
                    "required": bool,
                    "default": optional_value
                }
            }
        
    Returns:
        Validated dictionary with defaults applied
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    for field_name, field_spec in schema.items():
        is_required = field_spec.get("required", False)
        expected_type = field_spec.get("type", "str")
        default_value = field_spec.get("default")
        
        if field_name not in data or data[field_name] is None:
            if is_required:
                raise ValidationError(f"Required field '{field_name}' is missing")
            if default_value is not None:
                validated[field_name] = default_value
            continue
        
        value = data[field_name]
        
        # Type checking
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
        }
        
        expected_python_type = type_map.get(expected_type.lower())
        if expected_python_type and not isinstance(value, expected_python_type):
            raise ValidationError(
                f"Field '{field_name}' has wrong type. Expected {expected_type}, got {type(value).__name__}"
            )
        
        validated[field_name] = value
    
    return validated

