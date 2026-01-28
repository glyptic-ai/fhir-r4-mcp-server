"""Unit tests for the caching module."""

import pytest
import time

from fhir_r4_mcp.cache import (
    CacheConfig,
    CacheEntry,
    FHIRCache,
    MemoryCache,
)


class TestCacheConfig:
    """Tests for CacheConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CacheConfig()

        assert config.enabled is True
        assert config.backend == "memory"
        assert config.ttl_seconds == 300
        assert config.max_size == 1000
        assert config.capability_ttl == 3600
        assert config.valueset_ttl == 86400

    def test_custom_config(self):
        """Test custom configuration."""
        config = CacheConfig(
            enabled=False,
            backend="redis",
            ttl_seconds=600,
            max_size=500,
            redis_url="redis://localhost:6379",
        )

        assert config.enabled is False
        assert config.backend == "redis"
        assert config.ttl_seconds == 600
        assert config.redis_url == "redis://localhost:6379"


class TestCacheEntry:
    """Tests for CacheEntry class."""

    def test_entry_creation(self):
        """Test cache entry creation."""
        entry = CacheEntry(
            value={"resourceType": "Patient", "id": "123"},
            expires_at=time.time() + 300,
        )

        assert entry.value["id"] == "123"
        assert not entry.is_expired

    def test_entry_expiration(self):
        """Test cache entry expiration."""
        # Create already expired entry
        entry = CacheEntry(
            value={"test": True},
            expires_at=time.time() - 10,
        )

        assert entry.is_expired

    def test_ttl_remaining(self):
        """Test TTL remaining calculation."""
        expires_at = time.time() + 100
        entry = CacheEntry(
            value={"test": True},
            expires_at=expires_at,
        )

        assert entry.ttl_remaining > 0
        assert entry.ttl_remaining <= 100


class TestMemoryCache:
    """Tests for MemoryCache class."""

    @pytest.fixture
    def cache(self):
        """Create a test cache."""
        config = CacheConfig(
            enabled=True,
            max_size=10,
            ttl_seconds=60,
        )
        return MemoryCache(config)

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """Test basic set and get operations."""
        await cache.set("test:key", {"value": 123})

        result = await cache.get("test:key")

        assert result is not None
        assert result["value"] == 123

    @pytest.mark.asyncio
    async def test_get_missing_key(self, cache):
        """Test getting a missing key."""
        result = await cache.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Test deleting a key."""
        await cache.set("test:delete", {"value": "test"})

        deleted = await cache.delete("test:delete")

        assert deleted is True
        assert await cache.get("test:delete") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, cache):
        """Test deleting a nonexistent key."""
        deleted = await cache.delete("nonexistent")

        assert deleted is False

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, cache):
        """Test invalidating keys by pattern."""
        await cache.set("conn1:Patient:read:123", {"id": "123"})
        await cache.set("conn1:Patient:read:456", {"id": "456"})
        await cache.set("conn1:Observation:read:789", {"id": "789"})

        count = await cache.invalidate("conn1:Patient:*")

        assert count == 2
        assert await cache.get("conn1:Patient:read:123") is None
        assert await cache.get("conn1:Observation:read:789") is not None

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Test clearing all cache entries."""
        await cache.set("key1", {"value": 1})
        await cache.set("key2", {"value": 2})

        await cache.clear()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_stats(self, cache):
        """Test cache statistics."""
        await cache.set("test", {"value": 1})
        await cache.get("test")  # Hit
        await cache.get("nonexistent")  # Miss

        stats = await cache.stats()

        assert stats["enabled"] is True
        assert stats["backend"] == "memory"
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1

    @pytest.mark.asyncio
    async def test_max_size_eviction(self, cache):
        """Test LRU eviction when max size is reached."""
        # Fill cache beyond max_size (10)
        for i in range(15):
            await cache.set(f"key{i}", {"value": i})

        stats = await cache.stats()

        assert stats["size"] <= 10
        assert stats["evictions"] >= 5

    @pytest.mark.asyncio
    async def test_expired_entry_cleanup(self, cache):
        """Test that expired entries are not returned."""
        # Set with very short TTL
        await cache.set("short_ttl", {"value": "test"}, ttl=0)

        # Wait for expiration
        time.sleep(0.1)

        result = await cache.get("short_ttl")

        assert result is None

    @pytest.mark.asyncio
    async def test_disabled_cache(self):
        """Test that disabled cache doesn't store anything."""
        config = CacheConfig(enabled=False)
        cache = MemoryCache(config)

        await cache.set("test", {"value": 1})
        result = await cache.get("test")

        assert result is None

    @pytest.mark.asyncio
    async def test_generate_key(self, cache):
        """Test cache key generation."""
        key1 = cache.generate_key(
            connection_id="conn1",
            resource_type="Patient",
            operation="read",
            resource_id="123",
        )

        key2 = cache.generate_key(
            connection_id="conn1",
            resource_type="Patient",
            operation="search",
            params={"name": "Smith"},
        )

        assert key1 == "conn1:Patient:read:123"
        assert key2.startswith("conn1:Patient:search:")
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_ttl_by_resource_type(self, cache):
        """Test TTL determination by resource type."""
        # CapabilityStatement should get longer TTL
        await cache.set(
            "conn:CapabilityStatement",
            {"resourceType": "CapabilityStatement"},
        )

        # Check it was cached (actual TTL is internal)
        result = await cache.get("conn:CapabilityStatement")
        assert result is not None


class TestFHIRCacheInterface:
    """Tests for FHIRCache abstract interface."""

    def test_memory_cache_implements_interface(self):
        """Test that MemoryCache implements FHIRCache interface."""
        cache = MemoryCache()

        assert isinstance(cache, FHIRCache)
        assert hasattr(cache, "get")
        assert hasattr(cache, "set")
        assert hasattr(cache, "delete")
        assert hasattr(cache, "invalidate")
        assert hasattr(cache, "clear")
        assert hasattr(cache, "stats")
