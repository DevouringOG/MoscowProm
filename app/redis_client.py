"""Redis client configuration and utilities."""
import json
from typing import Any, Optional
import redis
from config import get_redis_url, settings
import structlog

logger = structlog.get_logger(__name__)


class RedisClient:
    """Redis client wrapper for caching."""

    def __init__(self):
        """Initialize Redis client."""
        self.client = redis.from_url(
            get_redis_url(),
            decode_responses=settings.redis.decode_responses,
        )
        self.default_ttl = settings.redis.cache_ttl

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("redis_get_error", key=key, error=str(e))
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: from settings)

        Returns:
            True if successful, False otherwise
        """
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error("redis_set_error", key=key, error=str(e))
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error("redis_delete_error", key=key, error=str(e))
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., 'kpi:*')

        Returns:
            Number of keys deleted
        """
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error("redis_clear_pattern_error", pattern=pattern, error=str(e))
            return 0

    def ping(self) -> bool:
        """
        Check if Redis is available.

        Returns:
            True if Redis is available, False otherwise
        """
        try:
            return self.client.ping()
        except Exception:
            return False


# Global Redis client instance
redis_client = RedisClient()
