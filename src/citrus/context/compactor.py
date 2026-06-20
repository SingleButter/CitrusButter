from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel

from citrus.runtime.messages import Message

COMPACTED_HISTORY_MARKER = "[Earlier conversation compacted:"
COMPACTED_TOOL_RESULT_MARKER = "[Earlier tool result compacted."


class ContextCompactor(Protocol):
    def compact(self, messages: list[Message]) -> list[Message]:
        ...


class ContextCompactorConfig(BaseModel):
    max_context_chars: int = 80_000
    target_context_chars: int = 60_000
    max_messages: int = 60
    keep_head_segments: int = 2
    keep_tail_segments: int = 24
    keep_recent_tool_results: int = 3
    max_tool_result_chars: int = 4_000
    tool_result_preview_chars: int = 800


@dataclass(frozen=True)
class _Segment:
    messages: list[Message]


class DeterministicContextCompactor:
    def __init__(self, config: ContextCompactorConfig | None = None) -> None:
        self._config = config or ContextCompactorConfig()

    def compact(self, messages: list[Message]) -> list[Message]:
        compacted = self._compact_old_tool_results(list(messages))
        if not self._over_budget(compacted):
            return compacted

        return self._snip_middle_segments(compacted)

    def _compact_old_tool_results(self, messages: list[Message]) -> list[Message]:
        tool_indexes = [
            index for index, message in enumerate(messages) if message.role == "tool"
        ]
        recent_tool_indexes: set[int] = set()
        if self._config.keep_recent_tool_results > 0:
            recent_tool_indexes = set(
                tool_indexes[-self._config.keep_recent_tool_results :]
            )
        compacted: list[Message] = []
        for index, message in enumerate(messages):
            if (
                message.role == "tool"
                and index not in recent_tool_indexes
                and len(message.text()) > self._config.max_tool_result_chars
                and COMPACTED_TOOL_RESULT_MARKER not in message.text()
            ):
                compacted.append(self._compact_tool_result(message))
            else:
                compacted.append(message)
        return compacted

    def _compact_tool_result(self, message: Message) -> Message:
        preview = message.text()[: self._config.tool_result_preview_chars]
        text = (
            f"{COMPACTED_TOOL_RESULT_MARKER} Preview:\n"
            f"{preview}\n"
            "Re-run the tool if full output is needed.]"
        )
        return Message.tool_text(message.tool_call_id or "", text)

    def _over_budget(self, messages: list[Message]) -> bool:
        return (
            len(messages) > self._config.max_messages
            or self._estimate_chars(messages) > self._config.max_context_chars
        )

    def _estimate_chars(self, messages: list[Message]) -> int:
        total = 0
        for message in messages:
            total += len(message.text())
            for tool_call in message.tool_calls():
                total += len(tool_call.model_dump_json())
        return total

    def _snip_middle_segments(self, messages: list[Message]) -> list[Message]:
        segments = self._segments(messages)
        if self._has_history_placeholder(segments):
            return messages

        keep_head = self._config.keep_head_segments
        keep_tail = self._config.keep_tail_segments
        if len(segments) <= keep_head + keep_tail:
            return messages

        head = segments[:keep_head]
        tail = segments[-keep_tail:]
        removed = segments[keep_head:-keep_tail]
        removed_messages = sum(len(segment.messages) for segment in removed)
        placeholder = _Segment(
            messages=[
                Message.user_text(
                    f"{COMPACTED_HISTORY_MARKER} "
                    f"{removed_messages} messages removed. "
                    "Full details remain in the session log.]"
                )
            ]
        )
        return [
            message
            for segment in [*head, placeholder, *tail]
            for message in segment.messages
        ]

    def _segments(self, messages: list[Message]) -> list[_Segment]:
        segments: list[_Segment] = []
        index = 0
        while index < len(messages):
            message = messages[index]
            tool_call_ids = {tool_call.id for tool_call in message.tool_calls()}
            if tool_call_ids:
                segment_messages = [message]
                index += 1
                while index < len(messages):
                    next_message = messages[index]
                    if (
                        next_message.role == "tool"
                        and next_message.tool_call_id in tool_call_ids
                    ):
                        segment_messages.append(next_message)
                        index += 1
                        continue
                    break
                segments.append(_Segment(messages=segment_messages))
                continue

            segments.append(_Segment(messages=[message]))
            index += 1
        return segments

    def _has_history_placeholder(self, segments: list[_Segment]) -> bool:
        return any(
            COMPACTED_HISTORY_MARKER in message.text()
            for segment in segments
            for message in segment.messages
        )
