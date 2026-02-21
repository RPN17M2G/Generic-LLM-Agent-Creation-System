"""
Model registry for tracking available LLM models and their capabilities.
"""
from typing import Dict, Any, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelRegistry:
    """
    Registry for tracking LLM models and their metadata.
    """
    _instance: Optional['ModelRegistry'] = None
    _models: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelRegistry, cls).__new__(cls)
            cls._instance._models = {}
        return cls._instance
    
    def register(
        self,
        model_name: str,
        provider: str = "ollama",
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register a model with its capabilities.
        
        Args:
            model_name: Name of the model
            provider: LLM provider (default: ollama)
            capabilities: List of capabilities (e.g., ["sql_generation", "reasoning"])
            metadata: Additional metadata about the model
        """
        self._models[model_name] = {
            "name": model_name,
            "provider": provider,
            "capabilities": capabilities or [],
            "metadata": metadata or {}
        }
        logger.info("model_registered", model_name=model_name, provider=provider)
    
    def get(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get model information."""
        return self._models.get(model_name)
    
    def list_models(self, capability: Optional[str] = None) -> List[str]:
        """
        List all registered models, optionally filtered by capability.
        
        Args:
            capability: Optional capability to filter by
            
        Returns:
            List of model names
        """
        if capability is None:
            return list(self._models.keys())
        
        return [
            name for name, info in self._models.items()
            if capability in info.get("capabilities", [])
        ]
    
    def has_capability(self, model_name: str, capability: str) -> bool:
        """Check if a model has a specific capability."""
        model_info = self.get(model_name)
        if not model_info:
            return False
        return capability in model_info.get("capabilities", [])

