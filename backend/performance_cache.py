"""
Performance Caching Layer
Provides in-memory caching for frequently accessed data to reduce database and API calls
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from functools import wraps

logger = logging.getLogger(__name__)

class CacheEntry:
    """Represents a cached entry with expiration"""
    def __init__(self, data: Any, ttl_seconds: int):
        self.data = data
        self.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

class PerformanceCache:
    """
    In-memory cache for performance optimization
    Thread-safe with async support
    """
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._lock = asyncio.Lock()
        logger.info("[PERF_CACHE] Initialized performance cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value if exists and not expired"""
        entry = self._cache.get(key)
        if entry and not entry.is_expired():
            logger.debug(f"[PERF_CACHE] Cache HIT: {key}")
            return entry.data
        
        # Clean up expired entry
        if entry and entry.is_expired():
            logger.debug(f"[PERF_CACHE] Expired entry removed: {key}")
            del self._cache[key]
        
        logger.debug(f"[PERF_CACHE] Cache MISS: {key}")
        return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 60):
        """Set cached value with TTL"""
        self._cache[key] = CacheEntry(value, ttl_seconds)
        logger.debug(f"[PERF_CACHE] Cache SET: {key} (TTL: {ttl_seconds}s)")
    
    async def delete(self, key: str):
        """Delete cached value"""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"[PERF_CACHE] Cache DELETE: {key}")
    
    async def clear(self):
        """Clear all cached values"""
        count = len(self._cache)
        self._cache.clear()
        self._locks.clear()
        logger.info(f"[PERF_CACHE] Cache CLEARED: {count} entries")
    
    async def get_lock(self, key: str) -> asyncio.Lock:
        """Get or create a lock for a specific key (for request deduplication)"""
        async with self._lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]
    
    async def fetch_with_cache_and_dedup(
        self,
        key: str,
        fetcher: Callable,
        ttl_seconds: int = 60
    ) -> Any:
        """
        Fetch data with caching and request deduplication
        If multiple requests come in simultaneously, only one will execute the fetcher
        """
        # Check cache first
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        # Get lock for this key to prevent duplicate requests
        lock = await self.get_lock(key)
        
        async with lock:
            # Double-check cache after acquiring lock
            cached = await self.get(key)
            if cached is not None:
                logger.debug(f"[PERF_CACHE] Dedup prevented: {key}")
                return cached
            
            # Execute fetcher
            logger.debug(f"[PERF_CACHE] Executing fetcher: {key}")
            result = await fetcher()
            
            # Cache result
            await self.set(key, result, ttl_seconds)
            
            return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        expired = sum(1 for entry in self._cache.values() if entry.is_expired())
        return {
            "total_entries": len(self._cache),
            "expired_entries": expired,
            "active_entries": len(self._cache) - expired,
            "active_locks": len(self._locks)
        }


# Global cache instance
perf_cache = PerformanceCache()


def cached(ttl_seconds: int = 60, key_prefix: str = ""):
    """
    Decorator for caching async function results
    
    Usage:
        @cached(ttl_seconds=120, key_prefix="user_data")
        async def get_user_data(user_id: str):
            return await fetch_from_db(user_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Use fetch_with_cache_and_dedup for automatic caching and deduplication
            async def fetcher():
                return await func(*args, **kwargs)
            
            return await perf_cache.fetch_with_cache_and_dedup(
                cache_key,
                fetcher,
                ttl_seconds
            )
        
        return wrapper
    return decorator


# Cleanup task to remove expired entries periodically
async def cache_cleanup_task():
    """Background task to clean up expired cache entries"""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        
        expired_keys = [
            key for key, entry in perf_cache._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            await perf_cache.delete(key)
        
        if expired_keys:
            logger.info(f"[PERF_CACHE] Cleaned up {len(expired_keys)} expired entries")
