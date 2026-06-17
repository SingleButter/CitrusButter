from citrus.memory.base import MemoryItem


class NoopMemoryStore:
    """Memory store implementation that intentionally persists nothing."""

    def search(self, query: str) -> list[MemoryItem]:
        return []

    def put(self, item: MemoryItem | str, content: str | None = None) -> None:
        return None
