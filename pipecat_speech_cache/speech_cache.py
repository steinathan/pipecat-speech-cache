import base64
import hashlib
import json
import os
from typing import Any, Literal

from loguru import logger

from .models import CachedAudioChunk, CachedResponse
from .redis import RedisBackend


class SpeechCacheService:
    def __init__(
        self,
        agent_cache_key: str,
        backend_type: Literal["redis"] = "redis",
        redis_url: str | None = None,
    ):
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        self.agent_cache_key = agent_cache_key
        self.backend = RedisBackend(redis_url=redis_url, prefix=agent_cache_key)

    def _get_cache_key(
        self,
        text: str,
        voice_id: str,
        model: str,
        voice_settings: dict[str, Any],
        language: str | None,
    ) -> str:
        key_data = {
            "text": text,
            "voice_id": voice_id,
            "model": model,
            "voice_settings": voice_settings,
            "language": language,
        }
        key_json = json.dumps(key_data, sort_keys=True, separators=((",", ":")))
        return hashlib.sha256(key_json.encode("utf-8")).hexdigest()

    async def get_cached_response(
        self,
        text: str,
        voice_id: str,
        model: str,
        voice_settings: dict[str, Any],
        language: str | None,
    ) -> CachedResponse | None:
        cache_key = self._get_cache_key(text, voice_id, model, voice_settings, language)
        logger.debug(f"Getting cached response for: {text}, cache_key: {cache_key}")
        return await self.backend.get_cached_response(cache_key)

    async def store_response(
        self,
        text: str,
        voice_id: str,
        model: str,
        voice_settings: dict[str, Any],
        audio_chunks: list[CachedAudioChunk],
        word_timestamps: list,
        language: str | None,
    ) -> bool:
        cache_key = self._get_cache_key(text, voice_id, model, voice_settings, language)
        valid_audio_chunks = [chunk for chunk in audio_chunks if chunk.audio]
        if not valid_audio_chunks:
            logger.error(
                f"Skipping cache write for '{text[:50]}...' due to empty audio data"
            )
            return False

        audio_chunks_json = [
            {
                "audio_base64": base64.b64encode(chunk.audio).decode("utf-8"),
                "sample_rate": chunk.sample_rate,
                "num_channels": chunk.num_channels,
            }
            for chunk in valid_audio_chunks
        ]

        sample_rate = valid_audio_chunks[0].sample_rate
        num_channels = valid_audio_chunks[0].num_channels
        total_duration = sum(
            len(chunk.audio) / (chunk.sample_rate * 2) for chunk in valid_audio_chunks
        )

        data = {
            "text": text,
            "audio_chunks": audio_chunks_json,
            "word_timestamps": word_timestamps,
            "total_duration": total_duration,
            "sample_rate": sample_rate,
            "num_channels": num_channels,
        }

        result = await self.backend.store_response(cache_key, data)
        if result:
            logger.info(f"Cached audio for text: '{text[:50]}' with key {cache_key}")
        return result

    async def close(self):
        await self.backend.close()

    async def get_cache_stats(self) -> dict[str, Any]:
        return await self.backend.get_cache_stats()

    async def clear_cache(self):
        await self.backend.clear_cache()
