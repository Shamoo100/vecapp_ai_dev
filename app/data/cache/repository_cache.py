from typing import Dict, Any, Optional, List, TypeVar, Generic, Callable, Awaitable
from uuid import UUID
import json
import hashlib
import asyncio
from datetime import timedelta
from functools import wraps
from app.config.settings import get_settings

settings = get_settings()
T = TypeVar('T')

class RepositoryCache(Generic[T]):
    """Caching layer for repository data
    
    This class provides caching functionality for repository methods to improve
    performance for frequently accessed data.
    """
    
    def __init__(self, cache_client=None):
        """Initialize the cache
        
        Args:
            cache_client: Optional Redis client or other cache implementation
        """
        self.cache_client = cache_client
        # If no client provided, use in-memory cache for development
        if self.cache_client is None:
            self._memory_cache: Dict[str, Any] = {}
            self._expiry_times: Dict[str, float] = {}
    
    async def get(self, key: str) -> Optional[T]:
        """Get a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if self.cache_client:
            value = await self.cache_client.get(key)
            if value:
                return json.loads(value)
            return None
        else:
            # Check expiry for in-memory cache
            now = asyncio.get_event_loop().time()
            if key in self._memory_cache and self._expiry_times.get(key, 0) > now:
                return self._memory_cache[key]
            elif key in self._memory_cache:
                # Expired
                del self._memory_cache[key]
                del self._expiry_times[key]
            return None
    
    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set a value in the cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        if ttl is None:
            ttl = settings.DEFAULT_CACHE_TTL
            
        if self.cache_client:
            await self.cache_client.set(
                key, 
                json.dumps(value), 
                expire=ttl
            )
        else:
            self._memory_cache[key] = value
            self._expiry_times[key] = asyncio.get_event_loop().time() + ttl
    
    async def delete(self, key: str) -> None:
        """Delete a value from the cache
        
        Args:
            key: Cache key
        """
        if self.cache_client:
            await self.cache_client.delete(key)
        else:
            if key in self._memory_cache:
                del self._memory_cache[key]
                del self._expiry_times[key]
    
    async def clear_pattern(self, pattern: str) -> None:
        """Clear all keys matching a pattern
        
        Args:
            pattern: Pattern to match keys against
        """
        if self.cache_client:
            keys = await self.cache_client.keys(pattern)
            if keys:
                await self.cache_client.delete(*keys)
        else:
            # Simple pattern matching for in-memory cache
            keys_to_delete = [k for k in self._memory_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._memory_cache[key]
                del self._expiry_times[key]

def cached(ttl: Optional[int] = None, key_builder: Optional[Callable] = None):
    """Decorator for caching repository method results
    
    Args:
        ttl: Time to live in seconds
        key_builder: Optional function to build cache key from method arguments
        
    Returns:
        Decorated method
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get cache instance from repository
            cache = getattr(self, '_cache', None)
            if cache is None:
                # No cache available, just call the method
                return await func(self, *args, **kwargs)
            
            # Build cache key
            if key_builder:
                cache_key = key_builder(self, *args, **kwargs)
            else:
                # Default key builder: method name + args hash
                args_str = json.dumps(args, default=str) + json.dumps(kwargs, default=str)
                args_hash = hashlib.md5(args_str.encode()).hexdigest()
                cache_key = f"{self.__class__.__name__}:{func.__name__}:{args_hash}"
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call the method and cache the result
            result = await func(self, *args, **kwargs)
            if result is not None:  # Don't cache None results
                await cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator