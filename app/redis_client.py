import json
from typing import Any, Optional
import redis
from config import get_redis_url, settings
import structlog

logger = structlog.get_logger(__name__)

class RedisClient:
    def __init__(self):
        self.client = redis.from_url(get_redis_url(), decode_responses=settings.redis.decode_responses)
        self.default_ttl = settings.redis.cache_ttl

    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("redis_get_error", key=key, error=str(e))
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error("redis_set_error", key=key, error=str(e))
            return False

    def delete(self, key: str) -> bool:
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error("redis_delete_error", key=key, error=str(e))
            return False

    def clear_pattern(self, pattern: str) -> int:
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error("redis_clear_pattern_error", pattern=pattern, error=str(e))
            return 0

    def ping(self) -> bool:
        try:
            return self.client.ping()
        except Exception:
            return False

redis_client = RedisClient()
