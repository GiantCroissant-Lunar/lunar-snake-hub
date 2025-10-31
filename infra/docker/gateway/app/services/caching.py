"""
Caching Service - Multi-layer caching with Redis and in-memory caching
"""

import json
import hashlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import aioredis
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class CacheConfig(BaseModel):
    """Cache configuration"""

    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 3600  # 1 hour
    max_memory_items: int = 1000
    enable_redis: bool = True
    enable_memory: bool = True


class CacheEntry(BaseModel):
    """Cache entry with metadata"""

    key: str
    value: Any
    ttl: Optional[int] = None
    created_at: datetime
    access_count: int = 0
    last_accessed: datetime


class CachingService:
    """Multi-layer caching service with Redis and in-memory caching"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client: Optional[aioredis.Redis] = None
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_stats = {"hits": 0, "misses": 0, "sets": 0, "evictions": 0}

    async def initialize(self):
        """Initialize Redis connection"""
        if self.config.enable_redis:
            try:
                self.redis_client = aioredis.from_url(self.config.redis_url)
                await self.redis_client.ping()
                logger.info("✅ Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None

    def _generate_key(self, prefix: str, identifier: str, *args) -> str:
        """Generate cache key"""
        key_data = f"{prefix}:{identifier}:{':'.join(map(str, args))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired"""
        if entry.ttl is None:
            return False
        return datetime.now() > entry.created_at + timedelta(seconds=entry.ttl)

    def _evict_memory_if_needed(self):
        """Evict old entries if memory cache is full"""
        if len(self.memory_cache) <= self.config.max_memory_items:
            return

        # Sort by last accessed time and remove oldest
        sorted_items = sorted(
            self.memory_cache.items(), key=lambda x: x[1].last_accessed
        )

        items_to_remove = len(self.memory_cache) - self.config.max_memory_items + 100
        for key, _ in sorted_items[:items_to_remove]:
            del self.memory_cache[key]
            self.cache_stats["evictions"] += 1

    async def get(self, prefix: str, identifier: str, *args) -> Optional[Any]:
        """Get value from cache (tries memory first, then Redis)"""
        key = self._generate_key(prefix, identifier, *args)

        # Try memory cache first
        if self.config.enable_memory and key in self.memory_cache:
            entry = self.memory_cache[key]

            if not self._is_expired(entry):
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self.cache_stats["hits"] += 1
                return entry.value
            else:
                # Remove expired entry
                del self.memory_cache[key]

        # Try Redis cache
        if self.config.enable_redis and self.redis_client:
            try:
                cached_data = await self.redis_client.get(key)
                if cached_data:
                    data = json.loads(cached_data)
                    entry = CacheEntry(**data)

                    if not self._is_expired(entry):
                        # Cache in memory for faster access
                        if self.config.enable_memory:
                            self._evict_memory_if_needed()
                            self.memory_cache[key] = entry

                        self.cache_stats["hits"] += 1
                        return entry.value
                    else:
                        # Remove expired entry from Redis
                        await self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")

        self.cache_stats["misses"] += 1
        return None

    async def set(
        self, prefix: str, identifier: str, value: Any, ttl: Optional[int] = None, *args
    ) -> bool:
        """Set value in cache (both memory and Redis)"""
        key = self._generate_key(prefix, identifier, *args)
        ttl = ttl or self.config.default_ttl

        entry = CacheEntry(
            key=key,
            value=value,
            ttl=ttl,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
        )

        success = True

        # Set in memory cache
        if self.config.enable_memory:
            self._evict_memory_if_needed()
            self.memory_cache[key] = entry

        # Set in Redis cache
        if self.config.enable_redis and self.redis_client:
            try:
                await self.redis_client.setex(
                    key, ttl, json.dumps(entry.dict(), default=str)
                )
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
                success = False

        self.cache_stats["sets"] += 1
        return success

    async def delete(self, prefix: str, identifier: str, *args) -> bool:
        """Delete value from cache"""
        key = self._generate_key(prefix, identifier, *args)

        success = True

        # Delete from memory cache
        if self.config.enable_memory and key in self.memory_cache:
            del self.memory_cache[key]

        # Delete from Redis cache
        if self.config.enable_redis and self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
                success = False

        return success

    async def clear_prefix(self, prefix: str) -> int:
        """Clear all cache entries with given prefix"""
        count = 0

        # Clear from memory cache
        if self.config.enable_memory:
            keys_to_remove = [
                key
                for key in self.memory_cache.keys()
                if key.startswith(hashlib.md5(prefix.encode()).hexdigest()[:8])
            ]
            for key in keys_to_remove:
                del self.memory_cache[key]
                count += 1

        # Clear from Redis cache
        if self.config.enable_redis and self.redis_client:
            try:
                pattern = f"*{hashlib.md5(prefix.encode()).hexdigest()[:8]}*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    count += await self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis clear error: {e}")

        return count

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (
            (self.cache_stats["hits"] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        stats = {
            **self.cache_stats,
            "hit_rate_percent": round(hit_rate, 2),
            "memory_cache_size": len(self.memory_cache),
            "max_memory_items": self.config.max_memory_items,
        }

        # Add Redis stats if available
        if self.config.enable_redis and self.redis_client:
            try:
                info = await self.redis_client.info()
                stats["redis_memory_used"] = info.get("used_memory_human", "N/A")
                stats["redis_connected_clients"] = info.get("connected_clients", "N/A")
            except Exception as e:
                logger.warning(f"Redis stats error: {e}")

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Health check for cache services"""
        health = {
            "memory_cache": self.config.enable_memory,
            "redis_cache": False,
            "overall_status": "healthy",
        }

        if self.config.enable_redis and self.redis_client:
            try:
                await self.redis_client.ping()
                health["redis_cache"] = True
            except Exception as e:
                health["redis_cache"] = False
                health["overall_status"] = "degraded"
                logger.warning(f"Redis health check failed: {e}")

        return health

    async def warm_cache(self, data: List[Dict[str, Any]], prefix: str = "warmup"):
        """Warm up cache with initial data"""
        warmed = 0
        for item in data:
            try:
                identifier = item.get("id", str(warmed))
                await self.set(prefix, identifier, item.get("data", item))
                warmed += 1
            except Exception as e:
                logger.warning(f"Cache warmup error: {e}")

        logger.info(f"Cache warmed with {warmed} entries")
        return warmed


# Specialized cache decorators
def cache_result(prefix: str, ttl: int = 3600):
    """Decorator to cache function results"""

    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            # Generate cache key
            cache_key = (
                f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            )

            # Try to get from cache
            if hasattr(self, "cache_service"):
                cached_result = await self.cache_service.get(prefix, cache_key)
                if cached_result is not None:
                    return cached_result

            # Execute function and cache result
            result = await func(self, *args, **kwargs)

            if hasattr(self, "cache_service"):
                await self.cache_service.set(prefix, cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def cache_embedding(prefix: str = "embedding"):
    """Specialized decorator for embedding caching"""
    return cache_result(prefix, ttl=86400)  # 24 hours


def cache_search(prefix: str = "search", ttl: int = 1800):
    """Specialized decorator for search results caching"""
    return cache_result(prefix, ttl)  # 30 minutes
