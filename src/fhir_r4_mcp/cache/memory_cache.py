"""In-memory cache implementation for FHIR resources.

This module provides a simple in-memory cache with TTL support
for caching FHIR responses to improve performance.
"""

import asyncio
import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from fhir_r4_mcp.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheConfig:
    """Configuration for the FHIR cache."""

    enabled: bool = True
    backend: str = "memory"  # memory | redis
    ttl_seconds: int = 300  # 5 minutes default
    max_size: int = 1000  # Maximum entries
    capability_ttl: int = 3600  # 1 hour for CapabilityStatement
    valueset_ttl: int = 86400  # 24 hours for ValueSet expansions
    metadata_ttl: int = 3600  # 1 hour for metadata
    search_ttl: int = 300  # 5 minutes for search results

    # Redis-specific settings
    redis_url: str | None = None
    redis_prefix: str = "fhir:"


@dataclass
class CacheEntry:
    """A single cache entry with expiration."""

    value: dict[str, Any]
    expires_at: float
    created_at: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        return time.time() >= self.expires_at

    @property
    def ttl_remaining(self) -> float:
        """Get remaining TTL in seconds."""
        return max(0, self.expires_at - time.time())


class FHIRCache(ABC):
    """Abstract base class for FHIR cache implementations."""

    @abstractmethod
    async def get(self, key: str) -> dict[str, Any] | None:
        """Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        pass

    @abstractmethod
    async def invalidate(self, pattern: str) -> int:
        """Invalidate keys matching a pattern.

        Args:
            pattern: Pattern to match (supports * wildcard)

        Returns:
            Number of keys invalidated
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @abstractmethod
    async def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        pass

    def generate_key(
        self,
        connection_id: str,
        resource_type: str,
        operation: str = "read",
        resource_id: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Generate a cache key for a FHIR operation.

        Args:
            connection_id: FHIR connection ID
            resource_type: Resource type
            operation: Operation type (read, search, etc.)
            resource_id: Optional resource ID
            params: Optional search parameters

        Returns:
            Unique cache key
        """
        parts = [connection_id, resource_type, operation]

        if resource_id:
            parts.append(resource_id)

        if params:
            # Sort and hash params for consistent keys
            sorted_params = json.dumps(params, sort_keys=True)
            param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
            parts.append(param_hash)

        return ":".join(parts)


class MemoryCache(FHIRCache):
    """In-memory cache implementation with TTL support.

    This cache stores entries in a dictionary with automatic
    expiration and LRU-like eviction when max size is reached.
    """

    def __init__(self, config: CacheConfig | None = None) -> None:
        """Initialize the memory cache.

        Args:
            config: Cache configuration
        """
        self._config = config or CacheConfig()
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []  # For LRU eviction
        self._lock = asyncio.Lock()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    async def get(self, key: str) -> dict[str, Any] | None:
        """Get a value from cache."""
        if not self._config.enabled:
            return None

        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired:
                # Remove expired entry
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._misses += 1
                return None

            # Update access order for LRU
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            self._hits += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Set a value in cache."""
        if not self._config.enabled:
            return

        # Determine TTL based on resource type or operation
        if ttl is None:
            ttl = self._determine_ttl(key, value)

        async with self._lock:
            # Check if we need to evict entries
            while len(self._cache) >= self._config.max_size:
                await self._evict_oldest()

            # Create entry
            entry = CacheEntry(
                value=value,
                expires_at=time.time() + ttl,
            )

            self._cache[key] = entry

            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            logger.debug(f"Cached {key} with TTL {ttl}s")

    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                return True
            return False

    async def invalidate(self, pattern: str) -> int:
        """Invalidate keys matching a pattern."""
        import fnmatch

        async with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)
            ]

            for key in keys_to_delete:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)

            count = len(keys_to_delete)
            if count > 0:
                logger.debug(f"Invalidated {count} cache entries matching '{pattern}'")

            return count

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            logger.info("Cache cleared")

    async def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0

            return {
                "enabled": self._config.enabled,
                "backend": "memory",
                "size": len(self._cache),
                "max_size": self._config.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 3),
                "evictions": self._evictions,
            }

    async def _evict_oldest(self) -> None:
        """Evict the least recently used entry."""
        if self._access_order:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                self._evictions += 1
                logger.debug(f"Evicted cache entry: {oldest_key}")

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

    async def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed
        """
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired
            ]

            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)

            return len(expired_keys)


# Global cache instance
fhir_cache: FHIRCache = MemoryCache()


async def invalidate_on_write(
    connection_id: str,
    resource_type: str,
    resource_id: str | None = None,
) -> None:
    """Invalidate cache entries after a write operation.

    This should be called after create, update, or delete operations
    to ensure cache consistency.

    Args:
        connection_id: FHIR connection ID
        resource_type: Resource type that was modified
        resource_id: Optional specific resource ID
    """
    # Invalidate specific resource
    if resource_id:
        pattern = f"{connection_id}:{resource_type}:read:{resource_id}"
        await fhir_cache.invalidate(pattern)

    # Invalidate search results for this resource type
    pattern = f"{connection_id}:{resource_type}:search:*"
    await fhir_cache.invalidate(pattern)

    logger.debug(f"Invalidated cache for {connection_id}:{resource_type}")
