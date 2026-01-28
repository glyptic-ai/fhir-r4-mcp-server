"""FHIR R4 Caching Layer for performance improvement."""

from fhir_r4_mcp.cache.memory_cache import (
    CacheConfig,
    CacheEntry,
    FHIRCache,
    MemoryCache,
    fhir_cache,
)

__all__ = [
    "CacheConfig",
    "CacheEntry",
    "FHIRCache",
    "MemoryCache",
    "fhir_cache",
]

# Try to import Redis cache if available
try:
    from fhir_r4_mcp.cache.redis_cache import RedisCache

    __all__.append("RedisCache")
except ImportError:
    pass
