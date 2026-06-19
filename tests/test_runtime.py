from pathlib import Path

from citrus.context.builder import ContextBuilder
from citrus.permissions.base import PermissionDecision
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
    assert provider.requests[1].messages[-1].tool_call_id == "call-1"
    assert provider.requests[1].messages[-1].text() == "Wrote note.txt"
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


def test_runtime_asks_permission_approver_and_executes_allowed_tool(
    tmp_path: Path,
) -> None:
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
            ModelResponse(messages=[Message.assistant_text("done")]),
        ]
    )
    approval_requests = []
    sessions = InMemorySessionStore()
    runtime = AgentRuntime(
        provider=provider,
        tools=ToolRegistry.with_default_local_tools(),
        permissions=GradedPermissionPolicy(auto_approve=False),
        permission_approver=lambda request: approval_requests.append(request)
        or PermissionDecision(outcome="allow", reason="Approved by test."),
        context=ContextBuilder(),
        session_store=sessions,
    )

    result = runtime.run(RunRequest(task="write a note", workspace=tmp_path))

    assert result.success is True
    assert target.read_text() == "hello"
    assert len(approval_requests) == 1
    assert approval_requests[0].tool_name == "write_file"
    assert approval_requests[0].tool_call_id == "call-1"
    assert approval_requests[0].arguments == {"path": "note.txt", "content": "hello"}
    assert approval_requests[0].reason == "File writes modify the workspace."
    assert approval_requests[0].command is None
    resolved = [
        event
        for event in sessions.load(result.session_id)
        if event.type == EventType.PERMISSION_RESOLVED
    ][0]
    assert resolved.payload["outcome"] == "allow"


def test_runtime_stops_when_permission_approver_denies_tool(tmp_path: Path) -> None:
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
            )
        ]
    )
    sessions = InMemorySessionStore()
    runtime = AgentRuntime(
        provider=provider,
        tools=ToolRegistry.with_default_local_tools(),
        permissions=GradedPermissionPolicy(auto_approve=False),
        permission_approver=lambda request: PermissionDecision(
            outcome="deny",
            reason=f"Rejected {request.tool_name}.",
        ),
        context=ContextBuilder(),
        session_store=sessions,
    )

    result = runtime.run(RunRequest(task="write a note", workspace=tmp_path))

    assert result.success is False
    assert "Rejected write_file." in result.final_message
    assert not target.exists()
    resolved = [
        event
        for event in sessions.load(result.session_id)
        if event.type == EventType.PERMISSION_RESOLVED
    ][0]
    assert resolved.payload["outcome"] == "deny"


def test_runtime_denies_ask_permission_without_approver(tmp_path: Path) -> None:
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
            )
        ]
    )
    runtime = AgentRuntime(
        provider=provider,
        tools=ToolRegistry.with_default_local_tools(),
        permissions=GradedPermissionPolicy(auto_approve=False),
        context=ContextBuilder(),
        session_store=InMemorySessionStore(),
    )

    result = runtime.run(RunRequest(task="write a note", workspace=tmp_path))

    assert result.success is False
    assert "approval required" in result.final_message.lower()


def test_runtime_treats_unresolved_approver_ask_as_denied(tmp_path: Path) -> None:
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
            )
        ]
    )
    runtime = AgentRuntime(
        provider=provider,
        tools=ToolRegistry.with_default_local_tools(),
        permissions=GradedPermissionPolicy(auto_approve=False),
        permission_approver=lambda request: PermissionDecision(
            outcome="ask",
            reason=f"Still waiting on {request.tool_name}.",
        ),
        context=ContextBuilder(),
        session_store=InMemorySessionStore(),
    )

    result = runtime.run(RunRequest(task="write a note", workspace=tmp_path))

    assert result.success is False
    assert "approval unresolved" in result.final_message.lower()
    assert not target.exists()


def test_runtime_does_not_ask_for_policy_denied_tool(tmp_path: Path) -> None:
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

    def fail_if_called(_request):
        raise AssertionError("approver should not be called for denied tools")

    runtime = AgentRuntime(
        provider=provider,
        tools=ToolRegistry.with_default_local_tools(),
        permissions=GradedPermissionPolicy(auto_approve=False),
        permission_approver=fail_if_called,
        context=ContextBuilder(),
        session_store=InMemorySessionStore(),
    )

    result = runtime.run(RunRequest(task="delete something", workspace=tmp_path))

    assert result.success is False
    assert "dangerous shell command" in result.final_message.lower()


def test_runtime_auto_approve_skips_permission_approver(tmp_path: Path) -> None:
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
            ModelResponse(messages=[Message.assistant_text("done")]),
        ]
    )

    def fail_if_called(_request):
        raise AssertionError("approver should not be called with auto_approve=True")

    runtime = AgentRuntime(
        provider=provider,
        tools=ToolRegistry.with_default_local_tools(),
        permissions=GradedPermissionPolicy(auto_approve=True),
        permission_approver=fail_if_called,
        context=ContextBuilder(),
        session_store=InMemorySessionStore(),
    )

    result = runtime.run(RunRequest(task="write a note", workspace=tmp_path))

    assert result.success is True
