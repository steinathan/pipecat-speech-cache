# pipecat-speech-cache

A Redis-based TTS response caching layer for Pipecat to reduce costs and latency.

## Features
- Async Redis backend
- Extensible backend interface
- Typed models for cached audio and responses
- Designed for easy integration in TTS pipelines

## Installation

```bash
uv add pipecat-speech-cache
```

## Usage

See `example/bot.py` for a complete Pipecat bot using the cached ElevenLabs TTS service.

```python
from pipecat_speech_cache.providers.elevenlabs import CachedElevenlabsTTSService

tts = CachedElevenlabsTTSService(
    api_key=os.environ["ELEVEN_API_KEY"],
    sample_rate=8000,
    voice_id="UgBBYS2sOqTuMpoF3BR0",
)
```

## License
MIT
