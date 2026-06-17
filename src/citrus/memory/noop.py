class NoopMemoryStore:
    """Memory store implementation that intentionally persists nothing."""

    def search(self, query: str) -> list[object]:
        return []

    def put(self, scope: str, content: str) -> None:
        return None

