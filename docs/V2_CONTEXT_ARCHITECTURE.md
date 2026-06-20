# CitrusButter V2 Context Architecture

V2 starts by making multi-turn chat context bounded and extensible. The goal is
not full long-term memory yet. The goal is to define a clean context boundary so
future repo summaries, memory notes, auto compact, and summary pipelines can be
added without rewriting `AgentRuntime`.

## Implemented Capabilities

- `ContextBuilder` assembles prior active messages plus the current user task.
- `ContextBuilder.prepare_for_model()` delegates provider-call preparation to a
  compactor.
- `DeterministicContextCompactor` runs before each provider call.
- Old large tool results can be shortened while preserving `tool_call_id`.
- Middle history can be snipped with one placeholder message.
- Assistant tool calls and matching tool results are treated as pair-safe
  segments so provider message sequences stay valid.

## Runtime Flow

```python
messages = context.build(
    task=request.task,
    messages=request.messages,
    workspace=workspace,
)

for _turn in range(request.max_turns):
    messages = context.prepare_for_model(messages)
    response = provider.complete(ModelRequest(messages=messages, tools=tool_specs))
    messages.extend(response.messages)

    tool_calls = collect_tool_calls(response.messages)
    if not tool_calls:
        return RunResult(messages=messages)

    for tool_call in tool_calls:
        tool_result = execute_tool(tool_call)
        messages.append(Message.tool_text(tool_call.id, tool_result.content))
```

The compactor is a pre-provider processor. Tool results are not compacted when
they are appended; they are compacted before the next model call.

## Public Interfaces

```python
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
```

`RunResult.messages` is the active context for the next turn. Full transcript
history remains the responsibility of `SessionStore`.

## Future Extension Path

- OpenCode-style auto compact: replace or wrap the deterministic compactor with
  threshold-based summary compaction.
- NanoBot-style long-term context/memory: add `ContextSource` implementations
  that retrieve selected memory notes into builder output.
- learn-claude-code-style layered compaction: add budget, snip, micro-compact,
  summary, and reactive prompt-too-long recovery layers behind the same
  `compact(messages) -> messages` boundary.

V2 keeps the key V1 rule intact: `AgentRuntime` owns the loop, while context
assembly and compaction remain replaceable dependencies.
