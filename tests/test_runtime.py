from pathlib import Path

from citrus.context.builder import ContextBuilder
from citrus.permissions.policy import GradedPermissionPolicy
from citrus.providers.base import ModelResponse
from citrus.providers.fake import FakeProvider
from citrus.runtime.agent import AgentRuntime, RunRequest
from citrus.runtime.events import EventType
from citrus.runtime.messages import Message, ToolCall
from citrus.sessions.memory import InMemorySessionStore
from citrus.tools.registry import ToolRegistry


def test_runtime_executes_tool_call_and_records_events(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    provider = FakeProvider(
        responses=[
            ModelResponse(
                messages=[
                    Message.assistant_tool_call(
                        ToolCall(
                            id="call-1",
                            name="write_file",
                            arguments={"path": "note.txt", "content": "hello"},
                        )
                    )
                ]
            ),
            ModelResponse(messages=[Message.assistant_text("wrote note.txt")]),
        ]
    )
    sessions = InMemorySessionStore()
    runtime = AgentRuntime(
        provider=provider,
        tools=ToolRegistry.with_default_local_tools(),
        permissions=GradedPermissionPolicy(auto_approve=True),
        context=ContextBuilder(),
        session_store=sessions,
    )

    result = runtime.run(RunRequest(task="write a note", workspace=tmp_path))

    assert result.final_message == "wrote note.txt"
    assert provider.requests[0].tools[0].name == "read_file"
    assert provider.requests[0].tools[1].name == "write_file"
    assert target.read_text() == "hello"
    assert [event.type for event in sessions.load(result.session_id)] == [
        EventType.TASK_STARTED,
        EventType.CONTEXT_BUILT,
        EventType.MODEL_REQUESTED,
        EventType.MODEL_RESPONDED,
        EventType.TOOL_REQUESTED,
        EventType.PERMISSION_REQUESTED,
        EventType.PERMISSION_RESOLVED,
        EventType.TOOL_COMPLETED,
        EventType.MODEL_REQUESTED,
        EventType.MODEL_RESPONDED,
        EventType.TASK_COMPLETED,
    ]


def test_runtime_stops_when_permission_denies_tool(tmp_path: Path) -> None:
    provider = FakeProvider(
        responses=[
            ModelResponse(
                messages=[
                    Message.assistant_tool_call(
                        ToolCall(
                            id="call-1",
                            name="run_shell",
                            arguments={"command": "rm -rf /tmp/example"},
                        )
                    )
                ]
            )
        ]
    )
    sessions = InMemorySessionStore()
    runtime = AgentRuntime(
        provider=provider,
        tools=ToolRegistry.with_default_local_tools(),
        permissions=GradedPermissionPolicy(auto_approve=False),
        context=ContextBuilder(),
        session_store=sessions,
    )

    result = runtime.run(RunRequest(task="delete something", workspace=tmp_path))

    assert result.success is False
    assert "denied" in result.final_message.lower()
    assert sessions.load(result.session_id)[-1].type == EventType.TASK_FAILED
