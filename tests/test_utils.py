"""
Tests for utility functions.
"""
import pytest
import time
from unittest.mock import Mock, patch
from utils.exceptions import (
    AgentFrameworkError,
    AgentError,
    ToolExecutionError,
    DatabaseError,
    LLMError,
    ConfigurationError,
    ValidationError
)
from utils.retry import retry_with_backoff, RetryHandler
from utils.cache import SimpleCache, cached


class TestExceptions:
    """Tests for custom exceptions."""
    
    def test_agent_framework_error(self):
        """Test base exception."""
        error = AgentFrameworkError("test error")
        assert str(error) == "test error"
    
    def test_agent_error(self):
        """Test agent error."""
        error = AgentError("test error", agent_name="test_agent")
        assert error.agent_name == "test_agent"
    
    def test_tool_execution_error(self):
        """Test tool execution error."""
        error = ToolExecutionError("test error", tool_name="test_tool")
        assert error.tool_name == "test_tool"
    
    def test_database_error(self):
        """Test database error."""
        error = DatabaseError("test error", database_type="clickhouse")
        assert error.database_type == "clickhouse"
    
    def test_llm_error(self):
        """Test LLM error."""
        error = LLMError("test error", model_name="test-model")
        assert error.model_name == "test-model"
    
    def test_configuration_error(self):
        """Test configuration error."""
        error = ConfigurationError("test error", config_path="/path/to/config")
        assert error.config_path == "/path/to/config"
    
    def test_validation_error(self):
        """Test validation error."""
        error = ValidationError("test error", field="test_field")
        assert error.field == "test_field"


class TestRetryHandler:
    """Tests for retry handler."""
    
    def test_retry_handler_success(self):
        """Test retry handler with successful execution."""
        handler = RetryHandler(max_retries=3)
        
        def success_func():
            return "success"
        
        result = handler.execute(success_func)
        assert result == "success"
    
    def test_retry_handler_retry(self):
        """Test retry handler with retries."""
        handler = RetryHandler(max_retries=3, initial_delay=0.1)
        call_count = [0]
        
        def failing_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("test error")
            return "success"
        
        result = handler.execute(failing_func, exceptions=(ValueError,))
        assert result == "success"
        assert call_count[0] == 2
    
    def test_retry_handler_exhausted(self):
        """Test retry handler with exhausted retries."""
        handler = RetryHandler(max_retries=2, initial_delay=0.1)
        
        def always_failing_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            handler.execute(always_failing_func, exceptions=(ValueError,))
    
    @patch('utils.retry.time.sleep')
    def test_retry_handler_exponential_backoff(self, mock_sleep):
        """Test exponential backoff."""
        handler = RetryHandler(max_retries=3, initial_delay=1.0, exponential_base=2.0)
        call_count = [0]
        
        def failing_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("test error")
            return "success"
        
        handler.execute(failing_func, exceptions=(ValueError,))
        
        # Check that sleep was called with increasing delays
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 1.0  # First delay
        assert mock_sleep.call_args_list[1][0][0] == 2.0  # Second delay (exponential)


class TestSimpleCache:
    """Tests for simple cache."""
    
    def test_cache_set_get(self):
        """Test setting and getting from cache."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        
        result = cache.get("key1")
        assert result == "value1"
    
    def test_cache_miss(self):
        """Test cache miss."""
        cache = SimpleCache()
        result = cache.get("nonexistent")
        assert result is None
    
    def test_cache_clear(self):
        """Test clearing cache."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        cache.clear()
        
        result = cache.get("key1")
        assert result is None
    
    def test_cache_invalidate(self):
        """Test invalidating specific key."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.invalidate("key1")
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
    
    def test_cache_ttl_expiry(self):
        """Test TTL expiry."""
        cache = SimpleCache(default_ttl=1)
        cache.set("key1", "value1", ttl=0.1)  # Very short TTL
        
        # Should still be there immediately
        assert cache.get("key1") == "value1"
        
        # Wait for expiry
        time.sleep(0.2)
        assert cache.get("key1") is None


class TestCachedDecorator:
    """Tests for cached decorator."""
    
    def test_cached_decorator(self):
        """Test cached decorator."""
        call_count = [0]
        
        @cached(ttl=3600)
        def test_func(x):
            call_count[0] += 1
            return x * 2
        
        # First call - should execute
        result1 = test_func(5)
        assert result1 == 10
        assert call_count[0] == 1
        
        # Second call with same args - should use cache
        result2 = test_func(5)
        assert result2 == 10
        assert call_count[0] == 1  # Should not increment
        
        # Different args - should execute
        result3 = test_func(10)
        assert result3 == 20
        assert call_count[0] == 2

