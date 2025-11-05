"""
Redis caching configuration for production performance.
"""

import json
import pickle
from typing import Any, Optional, Union, Dict, List
import logging
from datetime import timedelta
import redis.asyncio as redis
from redis.asyncio import ConnectionPool
import hashlib

from .settings import settings

logger = logging.getLogger("fairmind.cache")


class CacheManager:
    """Redis cache manager with connection pooling."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool: Optional[ConnectionPool] = None
        self.default_ttl = settings.redis_ttl
        self.key_prefix = "fairmind:"
    
    async def initialize(self):
        """Initialize Redis connection pool."""
        try:
            if not settings.redis_url:
                logger.warning("Redis URL not configured, caching disabled")
                return
            
            # Create connection pool
            self.connection_pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
            )
            
            # Create Redis client
            self.redis_client = redis.Redis(
                connection_pool=self.connection_pool,
                decode_responses=False,  # We'll handle encoding ourselves
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Close Redis connections."""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            if self.connection_pool:
                await self.connection_pool.disconnect()
            
            logger.info("Redis connections closed")
            
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")
    
    def _make_key(self, key: str) -> str:
        """Create a prefixed cache key."""
        return f"{self.key_prefix}{key}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value).encode('utf-8')
        else:
            return pickle.dumps(value)
    
    def _deserialize_value(self, value: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first (for simple types)
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle for complex objects
            return pickle.loads(value)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._make_key(key)
            value = await self.redis_client.get(cache_key)
            
            if value is None:
                return None
            
            return self._deserialize_value(value)
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Set value in cache."""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(key)
            serialized_value = self._serialize_value(value)
            ttl = ttl or self.default_ttl
            
            result = await self.redis_client.set(
                cache_key,
                serialized_value,
                ex=ttl,
                nx=nx,
                xx=xx
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(key)
            result = await self.redis_client.delete(cache_key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(key)
            result = await self.redis_client.exists(cache_key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._make_key(key)
            result = await self.redis_client.incrby(cache_key, amount)
            return result
            
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for a key."""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(key)
            result = await self.redis_client.expire(cache_key, ttl)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        if not self.redis_client or not keys:
            return {}
        
        try:
            cache_keys = [self._make_key(key) for key in keys]
            values = await self.redis_client.mget(cache_keys)
            
            result = {}
            for i, value in enumerate(values):
                if value is not None:
                    result[keys[i]] = self._deserialize_value(value)
            
            return result
            
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        if not self.redis_client or not mapping:
            return False
        
        try:
            pipe = self.redis_client.pipeline()
            ttl = ttl or self.default_ttl
            
            for key, value in mapping.items():
                cache_key = self._make_key(key)
                serialized_value = self._serialize_value(value)
                pipe.set(cache_key, serialized_value, ex=ttl)
            
            results = await pipe.execute()
            return all(results)
            
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching a pattern."""
        if not self.redis_client:
            return 0
        
        try:
            cache_pattern = self._make_key(pattern)
            keys = await self.redis_client.keys(cache_pattern)
            
            if keys:
                result = await self.redis_client.delete(*keys)
                return result
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache delete_pattern error for pattern {pattern}: {e}")
            return 0
    
    async def health_check(self) -> bool:
        """Check Redis health."""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.ping()
            return True
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def get_info(self) -> Dict[str, Any]:
        """Get Redis server info."""
        if not self.redis_client:
            return {"status": "disabled"}
        
        try:
            info = await self.redis_client.info()
            return {
                "status": "connected",
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
            }
            
        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            return {"status": "error", "error": str(e)}


# Global cache manager instance
cache_manager = CacheManager()


# Utility functions for common caching patterns
def cache_key_for_model(model_id: str, operation: str = "data") -> str:
    """Generate cache key for model data."""
    return f"model:{model_id}:{operation}"


def cache_key_for_dataset(dataset_id: str, operation: str = "data") -> str:
    """Generate cache key for dataset data."""
    return f"dataset:{dataset_id}:{operation}"


def cache_key_for_user(user_id: str, operation: str = "profile") -> str:
    """Generate cache key for user data."""
    return f"user:{user_id}:{operation}"


def cache_key_for_metrics(model_id: str, time_range: str = "1h") -> str:
    """Generate cache key for metrics data."""
    return f"metrics:{model_id}:{time_range}"


def cache_key_for_query(query: str, params: Dict[str, Any] = None) -> str:
    """Generate cache key for database query results."""
    # Create a hash of the query and parameters
    content = f"{query}:{json.dumps(params or {}, sort_keys=True)}"
    hash_key = hashlib.md5(content.encode()).hexdigest()
    return f"query:{hash_key}"


# Decorator for caching function results
def cached(ttl: int = None, key_func: callable = None):
    """Decorator to cache function results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                func_name = func.__name__
                args_str = str(args) + str(sorted(kwargs.items()))
                cache_key = f"func:{func_name}:{hashlib.md5(args_str.encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


# Initialize cache on import
async def init_cache():
    """Initialize cache connections."""
    await cache_manager.initialize()


async def close_cache():
    """Close cache connections."""
    await cache_manager.disconnect()