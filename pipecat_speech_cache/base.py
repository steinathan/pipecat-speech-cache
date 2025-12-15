from abc import ABC, abstractmethod
from typing import Any

from .models import CachedResponse


class SpeechCacheBackend(ABC):
    @abstractmethod
    async def get_cached_response(self, cache_key: str) -> CachedResponse | None:
        pass

    @abstractmethod
    async def store_response(
        self, cache_key: str, response_data: dict[str, Any]
    ) -> bool:
        pass

    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    async def get_cache_stats(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def clear_cache(self):
        pass
