import json
from pathlib import Path

from citrus.runtime.events import SessionEvent


class JsonlSessionStore:
    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def append(self, event: SessionEvent) -> None:
        path = self._path_for(event.session_id)
        with path.open("a", encoding="utf-8") as file:
            file.write(event.model_dump_json() + "\n")

    def load(self, session_id: str) -> list[SessionEvent]:
        path = self._path_for(session_id)
        if not path.exists():
            return []
        return [
            SessionEvent.model_validate(json.loads(line))
            for line in path.read_text(encoding="utf-8").splitlines()
            if line
        ]

    def _path_for(self, session_id: str) -> Path:
        return self._directory / f"{session_id}.jsonl"

