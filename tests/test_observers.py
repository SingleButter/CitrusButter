from pathlib import Path

from citrus.context.builder import ContextBuilder
from citrus.permissions.policy import GradedPermissionPolicy
from citrus.providers.base import ModelResponse
from citrus.providers.fake import FakeProvider
from citrus.runtime.agent import AgentRuntime, RunRequest
from citrus.runtime.events import EventType, SessionEvent
from citrus.runtime.messages import Message
from citrus.sessions.memory import InMemorySessionStore
from citrus.tools.registry import ToolRegistry


class RecordingObserver:
    def __init__(self) -> None:
        self.events: list[SessionEvent] = []

    def on_event(self, event: SessionEvent) -> None:
        self.events.append(event)


def test_runtime_observer_receives_session_events(tmp_path: Path) -> None:
    observer = RecordingObserver()
    runtime = AgentRuntime(
        provider=FakeProvider(
            [ModelResponse(messages=[Message.assistant_text("done")])]
        ),
        tools=ToolRegistry(),
        permissions=GradedPermissionPolicy(),
        context=ContextBuilder(),
        session_store=InMemorySessionStore(),
        observers=[observer],
    )

    runtime.run(RunRequest(task="finish", workspace=tmp_path))

    assert observer.events[0].type == EventType.TASK_STARTED
    assert observer.events[-1].type == EventType.TASK_COMPLETED
