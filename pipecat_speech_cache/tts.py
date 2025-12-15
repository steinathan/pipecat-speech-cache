from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger
from pipecat.frames.frames import (
    Frame,
    TTSAudioRawFrame,
    TTSTextFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
)
from pipecat.services.elevenlabs.tts import ElevenLabsHttpTTSService
from pipecat.utils.text.base_text_aggregator import AggregationType

from pipecat_speech_cache.models import CachedAudioChunk
from pipecat_speech_cache.speech_cache import SpeechCacheService


class CachedTTSService(ElevenLabsHttpTTSService):
    """
    Elevenlabs TTS Service with integrated file-system caching.
    """

    def __init__(
        self,
        agent_cache_key: str = "default",
        enable_cache: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.enable_cache = enable_cache
        self.cache_service = SpeechCacheService(agent_cache_key, backend_type="redis")
        self._current_text = None
        self._current_cache_data: dict | None = None

    def _get_current_voice_settings(self) -> dict[str, Any]:
        """Get current voice settings for cache key generation."""
        return {
            "speed": getattr(self, "_settings", {}).get("speed"),
            "emotion": getattr(self, "_settings", {}).get("emotion", []),
            "output_format": getattr(self, "_settings", {}).get("output_format", {}),
        }

    async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:
        logger.debug(f"CachedElevenlabsTTS: Processing text [{text}]")
        if self.enable_cache and self.cache_service:
            voice_settings = self._get_current_voice_settings()
            language = getattr(self, "_settings", {}).get("language")
            cached_response = await self.cache_service.get_cached_response(
                text=text,
                voice_id=getattr(self, "_voice_id", "default"),
                model=getattr(self, "model_name", "default"),
                voice_settings=voice_settings,
                language=language,
            )
            if cached_response:
                logger.debug(
                    f"🎯 Speech Cache Hit: Using cached response for text: '{text[:50]}'"
                )
                async for frame in self._run_cached_tts(cached_response):
                    yield frame
                return

        logger.warning(
            f"❌ Speech Cache Miss: Generating new TTS for text: '{text[:50]}'"
        )

        audio_chunks = []
        async for frame in super().run_tts(text):
            if isinstance(frame, TTSAudioRawFrame):
                audio_chunks.append(
                    CachedAudioChunk(
                        audio=frame.audio,
                        sample_rate=frame.sample_rate,
                        num_channels=frame.num_channels,
                    )
                )
            yield frame

        await self._store_cache_if_ready(text, audio_chunks)
        audio_chunks = []

    async def _run_cached_tts(self, cached_response) -> AsyncGenerator[Frame, None]:
        # Only emit TTSTextFrame if we have text (for backward compatibility with old cache)
        if cached_response.text:
            yield TTSTextFrame(
                text=cached_response.text, aggregated_by=AggregationType.SENTENCE
            )
        yield TTSStartedFrame()
        for chunk in cached_response.audio_chunks:
            yield TTSAudioRawFrame(
                audio=chunk.audio,
                sample_rate=chunk.sample_rate,
                num_channels=chunk.num_channels,
            )
        yield TTSStoppedFrame()

    async def _store_cache_if_ready(self, text, audio_chunks):
        await self.cache_service.store_response(
            text=text,
            voice_id=getattr(self, "_voice_id", "default"),
            model=getattr(self, "model_name", "default"),
            voice_settings=self._get_current_voice_settings(),
            audio_chunks=list(audio_chunks),
            word_timestamps=list([]),
            language=self._settings["language"],
        )
