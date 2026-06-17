from typing import Protocol

from citrus.runtime.events import SessionEvent


class SessionStore(Protocol):
    def append(self, event: SessionEvent) -> None:
        ...

    def load(self, session_id: str) -> list[SessionEvent]:
        ...

