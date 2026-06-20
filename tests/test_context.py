from pathlib import Path

from citrus.context.builder import ContextBuilder
from citrus.context.compactor import (
    ContextCompactorConfig,
    DeterministicContextCompactor,
)
from citrus.runtime.messages import Message, ToolCall


def test_context_builder_appends_current_task_to_history(tmp_path: Path) -> None:
    history = [
        Message.user_text("first task"),
        Message.assistant_text("first answer"),
    ]

    messages = ContextBuilder().build(
        task="second task",
        messages=history,
        workspace=tmp_path,
    )

    assert messages == [
        Message.user_text("first task"),
        Message.assistant_text("first answer"),
        Message.user_text("second task"),
    ]
    assert messages is not history


def test_context_builder_prepare_for_model_delegates_to_compactor() -> None:
    class RecordingCompactor:
        def __init__(self) -> None:
            self.calls: list[list[Message]] = []

        def compact(self, messages: list[Message]) -> list[Message]:
            self.calls.append(messages)
            return [Message.user_text("compacted")]

    compactor = RecordingCompactor()
    original = [Message.user_text("hello")]

    result = ContextBuilder(compactor=compactor).prepare_for_model(original)

    assert result == [Message.user_text("compacted")]
    assert compactor.calls == [original]


def test_compactor_compacts_old_large_tool_results_without_losing_call_id() -> None:
    compactor = DeterministicContextCompactor(
        ContextCompactorConfig(
            max_context_chars=200,
            target_context_chars=160,
            keep_recent_tool_results=1,
            max_tool_result_chars=20,
            tool_result_preview_chars=8,
        )
    )
    old_tool = Message.tool_text("old-call", "x" * 80)
    recent_tool = Message.tool_text("recent-call", "y" * 80)

    result = compactor.compact(
        [
            Message.assistant_tool_call(
                ToolCall(id="old-call", name="read_file", arguments={})
            ),
            old_tool,
            Message.assistant_tool_call(
                ToolCall(id="recent-call", name="read_file", arguments={})
            ),
            recent_tool,
        ]
    )

    assert result[1].role == "tool"
    assert result[1].tool_call_id == "old-call"
    assert "compacted" in result[1].text()
    assert result[3] == recent_tool


def test_compactor_can_compact_all_tool_results_when_recent_keep_is_zero() -> None:
    compactor = DeterministicContextCompactor(
        ContextCompactorConfig(
            keep_recent_tool_results=0,
            max_tool_result_chars=20,
            tool_result_preview_chars=8,
        )
    )

    result = compactor.compact([Message.tool_text("call-1", "x" * 80)])

    assert result[0].tool_call_id == "call-1"
    assert "compacted" in result[0].text()


def test_compactor_snips_middle_history_without_splitting_tool_exchange() -> None:
    compactor = DeterministicContextCompactor(
        ContextCompactorConfig(
            max_context_chars=120,
            target_context_chars=80,
            max_messages=6,
            keep_head_segments=1,
            keep_tail_segments=2,
            keep_recent_tool_results=3,
            max_tool_result_chars=200,
        )
    )
    messages = [
        Message.user_text("head"),
        Message.user_text("old user"),
        Message.assistant_tool_call(
            ToolCall(id="call-1", name="read_file", arguments={"path": "a.py"})
        ),
        Message.tool_text("call-1", "tool result"),
        Message.assistant_text("old answer"),
        Message.user_text("current task"),
        Message.assistant_text("current answer"),
    ]

    result = compactor.compact(messages)

    assert result[0] == Message.user_text("head")
    assert any("Earlier conversation compacted" in message.text() for message in result)
    assert Message.user_text("current task") in result
    assert Message.assistant_text("current answer") in result
    assert all(message.tool_call_id != "call-1" for message in result)
    assert all(not message.tool_calls() for message in result)


def test_compactor_is_idempotent_for_placeholders() -> None:
    compactor = DeterministicContextCompactor(
        ContextCompactorConfig(
            max_context_chars=80,
            target_context_chars=60,
            max_messages=4,
            keep_head_segments=1,
            keep_tail_segments=1,
        )
    )
    messages = [Message.user_text(f"message {index}") for index in range(8)]

    once = compactor.compact(messages)
    twice = compactor.compact(once)

    assert once == twice
    placeholders = sum(
        "Earlier conversation compacted" in message.text() for message in twice
    )
    assert placeholders == 1
