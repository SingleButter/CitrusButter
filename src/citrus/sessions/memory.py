from collections import defaultdict

from citrus.runtime.events import SessionEvent


class InMemorySessionStore:
    def __init__(self) -> None:
        self._events: dict[str, list[SessionEvent]] = defaultdict(list)

    def append(self, event: SessionEvent) -> None:
        self._events[event.session_id].append(event)

    def load(self, session_id: str) -> list[SessionEvent]:
        return list(self._events[session_id])

