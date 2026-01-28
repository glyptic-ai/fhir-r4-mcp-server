"""Redis cache implementation for FHIR resources.

This module provides a Redis-backed cache for distributed deployments.
Requires the 'redis' optional dependency.
"""

import json
from typing import Any

from fhir_r4_mcp.cache.memory_cache import CacheConfig, FHIRCache
from fhir_r4_mcp.utils.logging import get_logger

logger = get_logger(__name__)

try:
    import redis.asyncio as redis  # type: ignore

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore


class RedisCache(FHIRCache):
    """Redis-backed cache implementation.

    This cache stores entries in Redis for distributed deployments
    where multiple server instances need to share cache state.

    Requires: pip install fhir-r4-mcp-server[cache]
    """

    def __init__(self, config: CacheConfig | None = None) -> None:
        """Initialize the Redis cache.

        Args:
            config: Cache configuration with Redis URL

        Raises:
            ImportError: If redis package is not installed
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis cache requires the 'redis' package. "
                "Install with: pip install fhir-r4-mcp-server[cache]"
            )

        self._config = config or CacheConfig()
        self._prefix = self._config.redis_prefix
        self._client: redis.Redis | None = None  # type: ignore

        # Statistics (local counters, not shared across instances)
        self._hits = 0
        self._misses = 0

    async def connect(self) -> None:
        """Connect to Redis server."""
        if self._client is not None:
            return

        url = self._config.redis_url or "redis://localhost:6379"
        self._client = redis.from_url(url, decode_responses=True)  # type: ignore

        # Test connection
        await self._client.ping()
        logger.info(f"Connected to Redis at {url}")

    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self._client:
            await self._client.close()  # type: ignore
            self._client = None
            logger.info("Disconnected from Redis")

    def _key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> dict[str, Any] | None:
        """Get a value from Redis cache."""
        if not self._config.enabled or not self._client:
            return None

        try:
            data = await self._client.get(self._key(key))  # type: ignore

            if data is None:
                self._misses += 1
                return None

            self._hits += 1
            return json.loads(data)

        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self._misses += 1
            return None

    async def set(
        self,
        key: str,
        value: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Set a value in Redis cache."""
        if not self._config.enabled or not self._client:
            return

        if ttl is None:
            ttl = self._determine_ttl(key, value)

        try:
            data = json.dumps(value)
            await self._client.setex(self._key(key), ttl, data)  # type: ignore
            logger.debug(f"Cached {key} with TTL {ttl}s in Redis")

        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis cache."""
        if not self._client:
            return False

        try:
            result = await self._client.delete(self._key(key))  # type: ignore
            return result > 0

        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def invalidate(self, pattern: str) -> int:
        """Invalidate keys matching a pattern."""
        if not self._client:
            return 0

        try:
            # Convert glob pattern to Redis pattern
            redis_pattern = self._key(pattern)
            keys = []

            # Use SCAN to find matching keys
            async for key in self._client.scan_iter(match=redis_pattern):  # type: ignore
                keys.append(key)

            if keys:
                await self._client.delete(*keys)  # type: ignore
                logger.debug(f"Invalidated {len(keys)} Redis keys matching '{pattern}'")

            return len(keys)

        except Exception as e:
            logger.error(f"Redis invalidate error: {e}")
            return 0

    async def clear(self) -> None:
        """Clear all cache entries with our prefix."""
        if not self._client:
            return

        try:
            pattern = f"{self._prefix}*"
            keys = []

            async for key in self._client.scan_iter(match=pattern):  # type: ignore
                keys.append(key)

            if keys:
                await self._client.delete(*keys)  # type: ignore

            logger.info(f"Cleared {len(keys)} Redis cache entries")

        except Exception as e:
            logger.error(f"Redis clear error: {e}")

    async def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        stats: dict[str, Any] = {
            "enabled": self._config.enabled,
            "backend": "redis",
            "hits": self._hits,
            "misses": self._misses,
        }

        if self._client:
            try:
                # Get Redis info
                info = await self._client.info("memory")  # type: ignore
                stats["redis_memory_used"] = info.get("used_memory_human")

                # Count our keys
                pattern = f"{self._prefix}*"
                key_count = 0
                async for _ in self._client.scan_iter(match=pattern):  # type: ignore
                    key_count += 1
                stats["size"] = key_count

            except Exception as e:
                logger.error(f"Redis stats error: {e}")
                stats["error"] = str(e)

        total_requests = self._hits + self._misses
        stats["hit_rate"] = round(self._hits / total_requests, 3) if total_requests > 0 else 0

        return stats

    def _determine_ttl(self, key: str, value: dict[str, Any]) -> int:
        """Determine TTL based on content type."""
        # Check for CapabilityStatement
        if "CapabilityStatement" in key or value.get("resourceType") == "CapabilityStatement":
            return self._config.capability_ttl

        # Check for ValueSet
        if "ValueSet" in key or value.get("resourceType") == "ValueSet":
            return self._config.valueset_ttl

        # Check for metadata
        if "metadata" in key:
            return self._config.metadata_ttl

        # Check for search results (Bundles)
        if value.get("resourceType") == "Bundle":
            return self._config.search_ttl

        # Default TTL
        return self._config.ttl_seconds


async def create_redis_cache(config: CacheConfig | None = None) -> RedisCache:
    """Create and connect a Redis cache instance.

    Args:
        config: Optional cache configuration

    Returns:
        Connected RedisCache instance
    """
    cache = RedisCache(config)
    await cache.connect()
    return cache
