class CachedAudioChunk:
    def __init__(self, audio: bytes, sample_rate: int, num_channels: int):
        self.audio = audio
        self.sample_rate = sample_rate
        self.num_channels = num_channels


class CachedResponse:
    def __init__(
        self,
        audio_chunks: list[CachedAudioChunk],
        word_timestamps: list,
        total_duration: float,
        text: str,
    ):
        self.audio_chunks = audio_chunks
        self.word_timestamps = word_timestamps
        self.total_duration = total_duration
        self.text = text
