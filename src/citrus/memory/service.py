from citrus.memory.base import MemoryCandidate, MemoryItem, MemoryStore
from citrus.runtime.events import SessionEvent


class MemoryService:
    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def retrieve_for_task(self, task: str) -> list[MemoryItem]:
        return self._store.search(task)

    def propose_updates(self, events: list[SessionEvent]) -> list[MemoryCandidate]:
        return []

