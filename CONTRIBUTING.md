# Contributing to Pipecat Speech Cache

First off, thank you for considering contributing! We welcome any help to make this library better.

This guide focuses on adding support for new TTS providers. If you're looking to fix a bug or add a different feature, feel free to open an issue to discuss it first.

## Adding a New TTS Provider

Adding a cached wrapper for a new TTS provider is straightforward. The goal is to intercept the TTS request, check the cache, and if it's a miss, call the original provider and store the result.

Here's a step-by-step guide, using the existing `CachedElevenlabsTTSService` as a reference.

### 1. Create the Provider File

Create a new Python file in `pipecat_speech_cache/providers/`. For example, if you are adding support for "MyTTS", you would create `pipecat_speech_cache/providers/mytts.py`.

### 2. Create the Cached Service Class

Your new class should inherit from the original, non-cached TTS service provided by the `pipecat-ai` library.

```python
# In pipecat_speech_cache/providers/mytts.py

from pipecat.services.mytts import MyTTSHttpTTSService # Fictional base service
from pipecat_speech_cache.tts import CachedTTSService

class CachedMyTTSService(MyTTSHttpTTSService, CachedTTSService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
```

### 3. Implement the `__init__` Method

The `__init__` method needs to accept cache-specific arguments and initialize the `SpeechCacheService`.

```python
class CachedMyTTSService(MyTTSHttpTTSService, CachedTTSService):
    def __init__(
        self,
        agent_cache_key: str = "default",
        enable_cache: bool = True,
        **kwargs,
    ):
        # Call the original provider's init
        super().__init__(**kwargs)
        # Initialize cache-specific attributes
        self.enable_cache = enable_cache
        self.cache_service = SpeechCacheService(agent_cache_key, backend_type="redis")
```

### 4. Override `run_tts`

This is the core of the integration. You'll override `run_tts` to add the caching logic.

```python
from collections.abc import AsyncGenerator
from pipecat.frames.frames import Frame, TTSAudioRawFrame
from pipecat_speech_cache.models import CachedAudioChunk

# ... inside CachedMyTTSService class

async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:
    # 1. Check if caching is enabled
    if self.enable_cache:
        # 2. Get settings needed for the cache key
        voice_settings = self._get_current_voice_settings()
        
        # 3. Check the cache
        cached_response = await self.cache_service.get_cached_response(
            text=text,
            voice_id=self.voice_id, # Or however the provider stores it
            model=self.model,       # Or however the provider stores it
            voice_settings=voice_settings,
            language=self.language # Or however the provider stores it
        )

        if cached_response:
            # 4. Cache hit: Stream from cache
            async for frame in self._run_cached_tts(cached_response):
                yield frame
            return

    # 5. Cache miss: Call original provider
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

    # 6. Store the new response in the cache
    await self._store_cache_if_ready(text, audio_chunks)
```

### 5. Implement Helper Methods

You will need to implement a few helper methods. You can often copy these from `elevenlabs.py` and adapt them.

-   `_get_current_voice_settings()`: **This is the most important provider-specific method.** You need to look at the base TTS service implementation to see how it stores voice settings (like speed, pitch, format) and retrieve them here to create a unique cache key.

    ```python
    def _get_current_voice_settings(self) -> dict[str, Any]:
        """Get current voice settings for cache key generation."""
        # Example: retrieve settings from a _settings dict
        return {
            "speed": getattr(self, "_settings", {}).get("speed"),
            "output_format": getattr(self, "_settings", {}).get("output_format", {}),
        }
    ```

-   `_run_cached_tts()`: This method takes a `CachedResponse` and yields the appropriate `pipecat` frames. It can usually be copied directly from `elevenlabs.py`.

-   `_store_cache_if_ready()`: This method stores the newly generated audio in the cache. You'll need to adapt it to retrieve the correct `voice_id`, `model`, and `language` from your service instance.

### 6. Add an Example and Tests

-   Update `example/bot.py` or add a new example to show your new provider in action.
-   Add a new test file in the `tests/` directory to verify that caching works for your new provider.

### Submission

Once you're done, open a pull request! We'll review it and help get it merged.
