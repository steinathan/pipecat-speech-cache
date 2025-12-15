import pytest
from pipecat_speech_cache.models import CachedAudioChunk, CachedResponse


def test_cached_audio_chunk():
    chunk = CachedAudioChunk(
        audio=b"test_audio",
        sample_rate=22050,
        num_channels=1,
    )
    assert chunk.audio == b"test_audio"
    assert chunk.sample_rate == 22050
    assert chunk.num_channels == 1


def test_cached_response():
    chunk = CachedAudioChunk(
        audio=b"test_audio",
        sample_rate=22050,
        num_channels=1,
    )
    response = CachedResponse(
        audio_chunks=[chunk],
        word_timestamps=[{"word": "hello", "start": 0.0, "end": 0.5}],
        total_duration=1.0,
        text="Hello world",
    )
    assert len(response.audio_chunks) == 1
    assert response.audio_chunks[0].audio == b"test_audio"
    assert response.word_timestamps == [{"word": "hello", "start": 0.0, "end": 0.5}]
    assert response.total_duration == 1.0
    assert response.text == "Hello world"
