from typing import Protocol

from pydantic import BaseModel, Field

from citrus.runtime.events import SessionEvent


class MemoryItem(BaseModel):
    scope: str
    content: str
    tags: list[str] = Field(default_factory=list)


class MemoryCandidate(BaseModel):
    scope: str
    content: str
    source_event: str | None = None


class MemoryStore(Protocol):
    def search(self, query: str) -> list[MemoryItem]:
        ...

    def put(self, item: MemoryItem) -> None:
        ...


class MemoryPolicy(Protocol):
    def propose_updates(self, events: list[SessionEvent]) -> list[MemoryCandidate]:
        ...

