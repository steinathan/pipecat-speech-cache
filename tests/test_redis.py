import pytest
import asyncio
import redis
from pipecat_speech_cache.models import CachedAudioChunk, CachedResponse
from pipecat_speech_cache.redis import RedisBackend


@pytest.fixture
async def redis_backend():
    try:
        # Test Redis connection
        client = redis.Redis(host='localhost', port=6379, db=1)
        client.ping()
        client.close()
    except Exception as e:
        if "Redis" in str(type(e)) or "ConnectionError" in str(type(e)):
            pytest.skip("Redis is not running on localhost:6379")
        else:
            raise
    
    backend = RedisBackend("redis://localhost:6379/1", prefix="test_cache")
    yield backend
    await backend.clear_cache()
    await backend.close()


@pytest.mark.asyncio
async def test_store_and_get_cached_response(redis_backend):
    audio_chunk = CachedAudioChunk(
        audio=b"fake_audio_data",
        sample_rate=22050,
        num_channels=1,
    )
    response = CachedResponse(
        audio_chunks=[audio_chunk],
        word_timestamps=[],
        total_duration=1.0,
        text="Hello world",
    )
    cache_key = "test_key"
    stored = await redis_backend.store_response(cache_key, {
        "audio_chunks": [
            {
                "audio_base64": "ZmFrZV9hdWRpb19kYXRh",  # base64 of "fake_audio_data"
                "sample_rate": 22050,
                "num_channels": 1,
            }
        ],
        "word_timestamps": [],
        "total_duration": 1.0,
        "text": "Hello world",
    })
    assert stored is True

    cached = await redis_backend.get_cached_response(cache_key)
    assert cached is not None
    assert cached.text == "Hello world"
    assert len(cached.audio_chunks) == 1
    assert cached.audio_chunks[0].sample_rate == 22050


@pytest.mark.asyncio
async def test_cache_miss(redis_backend):
    cached = await redis_backend.get_cached_response("nonexistent_key")
    assert cached is None


@pytest.mark.asyncio
async def test_cache_stats(redis_backend):
    stats = await redis_backend.get_cache_stats()
    assert "keys" in stats
    assert isinstance(stats["keys"], int)


@pytest.mark.asyncio
async def test_clear_cache(redis_backend):
    await redis_backend.store_response("temp_key", {"text": "temp"})
    await redis_backend.clear_cache()
    stats = await redis_backend.get_cache_stats()
    assert stats["keys"] == 0
