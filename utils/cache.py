"""
Caching utilities for performance optimization.
"""
from typing import Dict, Any, Optional, Callable
from functools import wraps
import hashlib
import json
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)


class SimpleCache:
    """
    Simple in-memory cache with TTL support.
    """
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        logger.info("cache_initialized", default_ttl=default_ttl)
    
    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        expires_at = entry.get("expires_at")
        
        if expires_at and datetime.utcnow() > expires_at:
            del self._cache[key]
            return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (defaults to default_ttl)
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at
        }
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("cache_cleared")
    
    def invalidate(self, key: str):
        """Invalidate a specific cache entry."""
        if key in self._cache:
            del self._cache[key]


def cached(ttl: int = 3600, key_func: Optional[Callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time-to-live in seconds
        key_func: Optional function to generate cache key
    """
    cache = SimpleCache(default_ttl=ttl)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache._make_key(*args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug("cache_hit", function=func.__name__, key=cache_key)
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug("cache_miss", function=func.__name__, key=cache_key)
            return result
        
        return wrapper
    return decorator
