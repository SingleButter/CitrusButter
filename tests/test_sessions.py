from pathlib import Path

from citrus.runtime.events import EventType, SessionEvent
from citrus.sessions.jsonl import JsonlSessionStore


def test_jsonl_session_store_round_trips_events(tmp_path: Path) -> None:
    store = JsonlSessionStore(tmp_path / "sessions")
    event = SessionEvent(
        session_id="session-1",
        type=EventType.TASK_STARTED,
        payload={"task": "hello"},
    )

    store.append(event)

    assert store.load("session-1") == [event]

