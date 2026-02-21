"""
Base interface for LLM providers.
Follows Dependency Inversion Principle.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class ILLMProvider(ABC):
    """
    Interface for LLM providers.
    Allows different LLM backends (Ollama, OpenAI, etc.)
    """
    
    @abstractmethod
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send chat request to LLM.
        
        Args:
            model: Model name
            messages: List of message dictionaries
            options: Optional model options (temperature, etc.)
            
        Returns:
            Response dictionary with 'message' key containing 'content'
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if LLM provider is healthy."""
        pass

