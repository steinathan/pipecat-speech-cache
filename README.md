# pipecat-speech-cache

A simple, async TTS response caching backend for use with Pipecat and compatible TTS systems. Uses Redis for efficient, scalable storage.

## Features
- Async Redis backend
- Extensible backend interface
- Typed models for cached audio and responses
- Designed for easy integration in TTS pipelines

## Installation

```bash
# Activate your environment (if not already)
source ./.venv/bin/activate

# Add dependencies
uv add redis loguru
```

## Usage Example

```python
from redis import RedisBackend

# Initialize the cache
cache = RedisBackend(redis_url="redis://localhost:6379/0")

# Store a response
await cache.store_response(cache_key, response_data)

# Retrieve a response
response = await cache.get_cached_response(cache_key)

# Get stats
stats = await cache.get_cache_stats()

# Clear cache
await cache.clear_cache()

# Close connection
await cache.close()
```

## Structure
- `base.py`: Abstract backend interface
- `redis.py`: Redis backend implementation
- `models.py`: Typed cache models

## License
MIT
