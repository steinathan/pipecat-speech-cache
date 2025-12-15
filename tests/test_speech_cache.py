import pytest
import asyncio
import redis
from pipecat_speech_cache.speech_cache import SpeechCacheService
from pipecat_speech_cache.models import CachedAudioChunk


@pytest.fixture
async def speech_cache():
    try:
        # Test Redis connection
        client = redis.Redis(host='localhost', port=6379, db=2)
        client.ping()
        client.close()
    except Exception as e:
        if "Redis" in str(type(e)) or "ConnectionError" in str(type(e)):
            pytest.skip("Redis is not running on localhost:6379")
        else:
            raise
    
    cache = SpeechCacheService("test_agent", redis_url="redis://localhost:6379/2")
    yield cache
    await cache.clear_cache()
    await cache.close()


@pytest.mark.asyncio
async def test_speech_cache_store_and_get(speech_cache):
    audio_chunk = CachedAudioChunk(
        audio=b"test_audio",
        sample_rate=22050,
        num_channels=1,
    )
    stored = await speech_cache.store_response(
        text="Hello world",
        voice_id="voice_123",
        model="eleven_monolingual_v1",
        voice_settings={"speed": 1.0},
        audio_chunks=[audio_chunk],
        word_timestamps=[],
        language="en",
    )
    assert stored is True

    cached = await speech_cache.get_cached_response(
        text="Hello world",
        voice_id="voice_123",
        model="eleven_monolingual_v1",
        voice_settings={"speed": 1.0},
        language="en",
    )
    assert cached is not None
    assert cached.text == "Hello world"


@pytest.mark.asyncio
async def test_speech_cache_miss(speech_cache):
    cached = await speech_cache.get_cached_response(
        text="Nonexistent text",
        voice_id="voice_123",
        model="eleven_monolingual_v1",
        voice_settings={"speed": 1.0},
        language="en",
    )
    assert cached is None


@pytest.mark.asyncio
async def test_speech_cache_stats(speech_cache):
    stats = await speech_cache.get_cache_stats()
    assert "keys" in stats
    assert isinstance(stats["keys"], int)
