"""
Ollama client wrapper with connection pooling and retry logic.
"""
import time
from typing import Dict, Any, Optional, List
from ollama import Client
from utils.logger import get_logger
from utils.exceptions import LLMError
from llm.base import ILLMProvider

logger = get_logger(__name__)


class OllamaClient(ILLMProvider):
    """
    Wrapper around Ollama client with retry logic and error handling.
    """
    
    def __init__(
        self,
        host: str = "http://localhost:11434",
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize Ollama client.
        
        Args:
            host: Ollama server host URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.host = host
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client = Client(host=host)
        
        # Test connection
        try:
            self._client.list()
            logger.info("ollama_client_initialized", host=host)
        except Exception as e:
            logger.warning("ollama_connection_test_failed", error=str(e))
    
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat request to Ollama with retry logic.
        
        Args:
            model: Model name
            messages: List of message dictionaries
            options: Optional model options
            **kwargs: Additional arguments
            
        Returns:
            Response dictionary
            
        Raises:
            LLMError: If request fails after retries
        """
        options = options or {}
        
        for attempt in range(self.max_retries):
            try:
                log = logger.bind(model=model, attempt=attempt+1)
                log.debug("ollama_chat_request", 
                         message_count=len(messages),
                         options=options,
                         last_message_preview=str(messages[-1].get("content", ""))[:200] if messages else None)
                
                response = self._client.chat(
                    model=model,
                    messages=messages,
                    options=options,
                    **kwargs
                )
                
                # Log response details
                if isinstance(response, dict) and "message" in response:
                    content = response["message"].get("content", "")
                    log.info("ollama_chat_response_received",
                            response_length=len(content),
                            content_preview=content[:300],
                            has_content=bool(content))
                else:
                    log.warning("ollama_chat_response_unexpected_format",
                               response_type=type(response).__name__,
                               response_keys=list(response.keys()) if isinstance(response, dict) else None)
                
                return response
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        "ollama_request_retry",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        delay=delay,
                        error=str(e)
                    )
                    time.sleep(delay)
                else:
                    logger.error("ollama_request_failed", error=str(e), exc_info=True)
                    raise LLMError(f"Ollama request failed after {self.max_retries} attempts: {e}", model)
    
    def list_models(self) -> List[str]:
        """
        List available models.
        
        Returns:
            List of model names
        """
        try:
            models = self._client.list()
            return [model['name'] for model in models.get('models', [])]
        except Exception as e:
            logger.error("ollama_list_models_failed", error=str(e))
            return []
    
    def pull_model(self, model: str) -> bool:
        """
        Pull a model if not available.
        
        Args:
            model: Model name
            
        Returns:
            True if successful
        """
        try:
            self._client.pull(model)
            logger.info("ollama_model_pulled", model=model)
            return True
        except Exception as e:
            logger.error("ollama_pull_model_failed", model=model, error=str(e))
            return False
    
    def health_check(self) -> bool:
        """
        Check if Ollama is healthy.
        
        Returns:
            True if healthy
        """
        try:
            self._client.list()
            return True
        except Exception:
            return False


class OllamaClientPool:
    """
    Pool of Ollama clients for concurrent requests.
    """
    
    def __init__(
        self,
        host: str = "http://localhost:11434",
        pool_size: int = 5,
        timeout: int = 60
    ):
        """
        Initialize client pool.
        
        Args:
            host: Ollama server host URL
            pool_size: Number of clients in the pool
            timeout: Request timeout
        """
        self.host = host
        self.pool_size = pool_size
        self.timeout = timeout
        self._pool: List[OllamaClient] = []
        self._lock = None  # Would use threading.Lock in production
        
        # Initialize pool
        for _ in range(pool_size):
            self._pool.append(OllamaClient(host=host, timeout=timeout))
        
        logger.info("ollama_client_pool_initialized", pool_size=pool_size)
    
    def get_client(self) -> OllamaClient:
        """
        Get a client from the pool (round-robin).
        
        Returns:
            OllamaClient instance
        """
        # Simple round-robin (in production, use proper locking)
        import random
        return self._pool[random.randint(0, len(self._pool) - 1)]
    
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat request using a client from the pool.
        """
        client = self.get_client()
        return client.chat(model=model, messages=messages, options=options, **kwargs)

