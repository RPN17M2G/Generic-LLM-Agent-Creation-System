"""
Robust request parser for handling various input formats.
Follows SOLID principles with clear separation of concerns.
"""
import json
from typing import Dict, Any, Optional, Union
from flask import Request
from utils.logger import get_logger

logger = get_logger(__name__)


class RequestParser:
    """
    Handles parsing of HTTP requests in various formats.
    Single Responsibility: Parse requests into a standardized format.
    """
    
    @staticmethod
    def parse(request: Request) -> Dict[str, Any]:
        """
        Parse request data from various formats into a standardized dictionary.
        
        Supports:
        - JSON body (application/json)
        - Form data (application/x-www-form-urlencoded)
        - Plain text body
        - Query parameters
        - Mixed formats (query params + body)
        
        Args:
            request: Flask request object
            
        Returns:
            Dictionary with parsed data, always contains 'query' key if valid
        """
        result = {}
        
        # 1. Try to get query from URL parameters first
        query_param = request.args.get('query') or request.args.get('q')
        if query_param:
            result['query'] = query_param
        
        # 2. Try to parse JSON body
        json_data = RequestParser._parse_json(request)
        if json_data:
            result.update(json_data)
        
        # 3. Try to parse form data
        form_data = RequestParser._parse_form(request)
        if form_data:
            result.update(form_data)
        
        # 4. Try to parse raw body as text/JSON
        raw_data = RequestParser._parse_raw_body(request)
        if raw_data and 'query' not in result:
            result['query'] = raw_data
        
        # 5. Normalize the result
        return RequestParser._normalize(result)
    
    @staticmethod
    def _parse_json(request: Request) -> Optional[Dict[str, Any]]:
        """Parse JSON from request body."""
        try:
            # Try standard JSON parsing
            if request.is_json:
                data = request.get_json(silent=True)
                if data:
                    return RequestParser._ensure_dict(data)
            
            # Try forcing JSON parsing
            if request.content_type and 'application/json' in request.content_type:
                data = request.get_json(force=True, silent=True)
                if data:
                    return RequestParser._ensure_dict(data)
            
            # Try parsing raw data as JSON
            raw_data = request.get_data(as_text=True)
            if raw_data:
                try:
                    data = json.loads(raw_data)
                    return RequestParser._ensure_dict(data)
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
                    
        except Exception as e:
            logger.debug("json_parse_failed", error=str(e))
        
        return None
    
    @staticmethod
    def _parse_form(request: Request) -> Optional[Dict[str, Any]]:
        """Parse form data from request."""
        try:
            if request.form:
                form_dict = dict(request.form)
                # Unwrap single-item lists (Flask form behavior)
                for key, value in form_dict.items():
                    if isinstance(value, list) and len(value) == 1:
                        form_dict[key] = value[0]
                return form_dict
        except Exception as e:
            logger.debug("form_parse_failed", error=str(e))
        
        return None
    
    @staticmethod
    def _parse_raw_body(request: Request) -> Optional[str]:
        """Parse raw body as text."""
        try:
            raw_data = request.get_data(as_text=True)
            if raw_data and raw_data.strip():
                # If it looks like a plain string (not JSON), return it
                stripped = raw_data.strip()
                if not (stripped.startswith('{') or stripped.startswith('[')):
                    return stripped
        except Exception as e:
            logger.debug("raw_body_parse_failed", error=str(e))
        
        return None
    
    @staticmethod
    def _ensure_dict(data: Any) -> Dict[str, Any]:
        """Ensure data is a dictionary, converting if necessary."""
        if isinstance(data, dict):
            return data
        elif isinstance(data, str):
            # Try to parse string as JSON
            try:
                parsed = json.loads(data)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
            # If it's a plain string, treat as query
            return {"query": data}
        elif isinstance(data, (list, tuple)) and len(data) > 0:
            # If it's a list, try to extract query from first element
            first = data[0]
            if isinstance(first, dict):
                return first
            elif isinstance(first, str):
                return {"query": first}
        elif data is None:
            return {}
        
        # Fallback: wrap in dict
        return {"data": data}
    
    @staticmethod
    def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize parsed data to ensure consistent structure.
        
        Ensures:
        - 'query' key exists if any query-like data was found
        - 'context' key exists as a dict
        - Removes None values
        """
        normalized = {}
        
        # Extract query from various possible keys
        query_keys = ['query', 'q', 'question', 'text', 'input', 'message', 'prompt']
        query_value = None
        
        for key in query_keys:
            if key in data and data[key]:
                query_value = data[key]
                break
        
        # If no query found, check if the whole data dict should be treated as query
        if not query_value and len(data) == 1:
            single_value = list(data.values())[0]
            if isinstance(single_value, str):
                query_value = single_value
        
        # If still no query, use the first string value found
        if not query_value:
            for value in data.values():
                if isinstance(value, str) and value.strip():
                    query_value = value
                    break
        
        if query_value:
            normalized['query'] = str(query_value).strip()
        
        # Extract context
        context = data.get('context', {})
        if not isinstance(context, dict):
            context = {}
        normalized['context'] = context
        
        # Copy other valid keys (excluding query keys we've already processed)
        excluded_keys = set(query_keys) | {'context'}
        for key, value in data.items():
            if key not in excluded_keys and value is not None:
                normalized[key] = value
        
        return normalized


def parse_request(request: Request) -> Dict[str, Any]:
    """
    Convenience function to parse a request.
    
    Args:
        request: Flask request object
        
    Returns:
        Normalized dictionary with 'query' and 'context' keys
    """
    return RequestParser.parse(request)

