import base64
import json
from typing import Any

import redis.asyncio as redis
from loguru import logger

from .base import SpeechCacheBackend
from .models import CachedAudioChunk, CachedResponse


class RedisBackend(SpeechCacheBackend):
    def __init__(self, redis_url: str, prefix: str = "tts_cache"):
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.prefix = prefix
            logger.info(f"[Speech] Redis cache connected: {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def _get_redis_key(self, cache_key: str) -> str:
        return f"{self.prefix}:{cache_key}"

    async def get_cached_response(self, cache_key: str) -> CachedResponse | None:
        redis_key = self._get_redis_key(cache_key)
        try:
            data_str = await self.redis.get(redis_key)
            if data_str:
                data = json.loads(data_str)
                audio_chunks = [
                    CachedAudioChunk(
                        base64.b64decode(chunk["audio_base64"]),
                        chunk["sample_rate"],
                        chunk["num_channels"],
                    )
                    for chunk in data["audio_chunks"]
                ]
                return CachedResponse(
                    audio_chunks,
                    data["word_timestamps"],
                    data["total_duration"],
                    data.get("text", ""),
                )
        except Exception as e:
            logger.error(f"Error retrieving cache for key {redis_key}: {e}")
        return None

    async def store_response(
        self, cache_key: str, response_data: dict[str, Any]
    ) -> bool:
        redis_key = self._get_redis_key(cache_key)
        try:
            await self.redis.set(redis_key, json.dumps(response_data))
            logger.info(f"Wrote to Redis cache: {redis_key}")
            return True
        except Exception as e:
            logger.error(f"Error writing to Redis cache for key {redis_key}: {e}")
            return False

    async def close(self):
        await self.redis.close()

    async def get_cache_stats(self) -> dict[str, Any]:
        try:
            keys = await self.redis.keys(f"{self.prefix}:*")
            return {"keys": len(keys)}
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"keys": 0, "error": str(e)}

    async def clear_cache(self):
        try:
            keys = await self.redis.keys(f"{self.prefix}:*")
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache keys.")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
