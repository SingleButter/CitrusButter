# Context Builder 与 Compactor 设计思考

这篇文档记录 CitrusButter V2 context 架构的设计思路。它不是实现说明，而是帮助理解为什么要把 context 拆成 `ContextBuilder` 和 `ContextCompactor`，以及这个接口如何承接后续 OpenCode 式 auto compact、NanoBot 式长期 context/memory、以及 `learn-claude-code` 的多层压缩管线。

## 为什么 context 需要独立设计

CitrusButter 现在已经有基础 agent loop：

```text
messages -> model -> assistant response -> optional tool calls -> tool results -> loop
```

这个 loop 可以工作，但多轮 chat 和工具调用会让 `messages` 不断变长。当前 `ContextBuilder` 只做一件事：把当前任务变成一条 user message。这符合 V1 的轻量目标，但还没有给以下能力留下清晰位置：

- 在 provider 调用前压缩长对话历史
- 注入仓库结构、项目规则、源码片段等 repo context
- 从长期 memory 中取出和当前任务相关的事实

所以 context 层应该分成两个组件：

```text
ContextBuilder
  负责组装一次 run 开始时的 active context

ContextCompactor
  负责每次 provider 调用前整理和压缩 active messages
```

这个拆分的核心价值是：`AgentRuntime` 仍然拥有 loop，但不需要知道具体如何压缩历史、如何注入 memory、如何处理 repo context。

## 组件职责

### ContextBuilder

`ContextBuilder` 回答的问题是：

```text
本轮 AgentRuntime.run() 开始时，模型应该看到什么？
```

它每次 `run()` 只执行一次。输入包括上一轮成功留下的 active messages、当前用户任务、workspace 信息。第一版可以只返回：

```text
previous active messages + Message.user_text(current task)
```

后续它可以调用 `ContextSource`，把 repo summary、项目规则、memory notes、system/context notes 插入到合适的位置。Builder 的职责是组装和排序，不是压缩。

### ContextCompactor

`ContextCompactor` 回答的问题是：

```text
这些 active messages 现在是否足够小、足够安全，可以发给 provider？
```

它在 agent loop 内部、每次 `provider.complete(...)` 前执行。它不应该知道 provider、tools、CLI、permission，也不应该写 session。它只做：

```text
list[Message] -> list[Message]
```

第一版 compactor 应该是 deterministic 的：

- 用字符数估算 active context 大小
- 压缩旧的大 tool result
- 超预算时裁剪中间历史
- 保证 assistant tool call 和对应 tool result 不被拆开
- 重复运行时不不断追加新的 placeholder

暂时不做 LLM summary、tokenizer、memory retrieval 或大结果落盘。

## Runtime 交互流程

推荐流程如下：

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
        return RunResult(success=True, messages=messages)

    for tool_call in tool_calls:
        tool_result = execute_tool(tool_call)
        messages.append(Message.tool_text(tool_call.id, tool_result.content))
```

关键规则是：**只在 provider 调用前压缩**。工具结果 append 后不立刻压缩，而是在下一次 loop 开始、下一次模型调用前统一压缩。这样触发点只有一个，不会重复压缩。

## 推荐接口

```python
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from citrus.runtime.messages import Message


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


class DeterministicContextCompactor:
    def __init__(self, config: ContextCompactorConfig | None = None) -> None:
        ...

    def compact(self, messages: list[Message]) -> list[Message]:
        ...


class ContextBuilder:
    def __init__(self, compactor: ContextCompactor | None = None) -> None:
        ...

    def build(
        self,
        task: str,
        messages: list[Message],
        workspace: Path,
    ) -> list[Message]:
        ...

    def prepare_for_model(self, messages: list[Message]) -> list[Message]:
        ...
```

`ContextBuilder.prepare_for_model()` 可以委托给 compactor。这样 `AgentRuntime` 只依赖 context 层，不直接依赖具体压缩算法。

## Pair-Safe Segment：为什么不能按单条消息裁剪

OpenAI-compatible provider 对 tool call 序列很敏感。不能留下这种历史：

```text
assistant tool_call(call-1)
```

却没有对应：

```text
tool result(call-1)
```

也不能只留下孤立的 tool result。否则 DeepSeek/OpenAI 这类 provider 很容易拒绝请求。

所以 compactor 应该先把 messages 转成 segment：

```text
TextSegment
  普通 user / assistant / system message

ToolExchangeSegment
  assistant tool_call message
  matching tool result messages
```

裁剪时按 segment 裁，而不是按单条 message 裁。旧的 tool exchange 可以整体删除并用 placeholder 替代；近期 tool exchange 可以保留结构，只缩短 tool result 的文本。

## 第一版压缩策略

第一版采用 budget-first deterministic 策略：

1. 复制 messages，避免意外修改调用方传入的列表。
2. 压缩旧的长 tool result，但保留 `tool_call_id`。
3. 用 `message.text()` 长度和 tool call metadata 估算 active context。
4. 如果低于预算，直接返回。
5. 如果超过 `max_context_chars` 或 `max_messages`，转成 pair-safe segments。
6. 保留 head segments 和 tail segments，中间替换成一条 user placeholder。
7. 重新估算，最多做有限次数的二次收缩，避免无限循环。

这套策略应该接近幂等：同一批 messages 连续 compact 两次，不应该不断产生新的 placeholder，也不应该反复缩短已经缩短过的 tool result。

## 如何承接 OpenCode 式 Auto Compact

OpenCode 的重要思想是：当 session 接近模型 context window 时自动 compact，而不是等 provider 报错才处理。CitrusButter 可以通过同一个接口承接这个能力：

```python
messages = context.prepare_for_model(messages)
```

未来只需要替换 compactor 实现：

```text
DeterministicContextCompactor
  -> AutoSummaryCompactor
       if estimated usage > threshold:
           save active transcript reference
           summarize old history
           return summary + recent segments
```

runtime 不需要知道 compactor 是简单裁剪、provider-specific token 估算，还是调用 LLM 做摘要。新增配置即可：

```text
auto_compact_threshold
summary_model
max_summary_retries
manual_compact_enabled
```

这就是好接口的价值：能力升级发生在实现替换里，而不是横向修改 `AgentRuntime`。

## 如何承接 NanoBot 式长期 Context / Memory

NanoBot 这类系统覆盖面更广：workspace、tools、memory、workflow、channel、MCP、context controls 都会组合起来。CitrusButter 现在不应该复制这种范围，但应该吸收它的边界思想：

```text
SessionStore
  记录发生过什么

MemoryService
  保存值得跨任务复用的事实

ContextSource
  为当前任务检索相关事实

ContextBuilder
  决定检索结果放进 active messages 的位置

ContextCompactor
  保证 active messages 在 provider 调用前可发送
```

未来 `MemoryContextSource` 可以返回类似内容：

```text
Project memory:
- Use pytest, ruff, and mypy before completion.
- Keep AgentRuntime as the loop owner.
- Do not persist API keys under version control.
```

Builder 把这些 notes 放到当前用户任务附近。Compactor 把它们当作 active context 的一部分处理。如果 memory notes 太长，应该由 source 重新筛选或摘要，而不是让 runtime 直接理解 memory。

## 如何承接 learn-claude-code 多层压缩管线

`learn-claude-code/s08_context_compact` 展示的是多层 pipeline：

```text
tool result budget
-> snip middle history
-> micro compact old tool results
-> LLM summary if still too large
-> reactive compact on prompt_too_long
```

CitrusButter 第一版只实现 deterministic 子集，但接口可以自然扩展：

```python
class LayeredContextCompactor:
    def compact(self, messages: list[Message]) -> list[Message]:
        messages = self._tool_result_budget(messages)
        messages = self._snip_middle(messages)
        messages = self._micro_compact_tool_results(messages)
        if self._over_threshold(messages):
            messages = self._summarize_history(messages)
        return messages
```

`prompt_too_long` 的 reactive compact 可以作为 provider error recovery 进入：

```python
try:
    response = provider.complete(...)
except PromptTooLongError:
    messages = context.recover_from_prompt_too_long(messages)
    response = provider.complete(...)
```

这个 recovery 必须有 retry 上限，防止 agent 在压缩和重试之间无限循环。

## Active Context 不是 Session History

最重要的架构区分是：

```text
RunResult.messages = 下一轮模型调用需要的 active context
SessionStore = 完整、真实、append-only 的审计日志
MemoryService = 被筛选过、值得跨任务复用的事实
```

Active context 可以被裁剪、压缩、摘要。Session history 不能被压缩成“看起来差不多”的东西，因为它承担审计、debug、replay、eval 的职责。Memory 也不是完整历史，它是提炼后的项目事实和用户偏好。

这也是为什么 `citrus chat` 应该继续传递 `RunResult.messages`，而 JSONL session persistence 应该独立记录完整事件流。

## 设计上的学习点

这个设计真正重要的不是“加一个 compactor”，而是把责任放在正确边界：

- Builder 是组装。
- Compactor 是 provider 前处理。
- Runtime 是 loop orchestration。
- Session 是审计。
- Memory 是持久事实。
- Source 是检索适配器。

有了这些边界，CitrusButter 可以先实现简单 deterministic compactor，之后再演进到 auto compact、长期 memory、repo context、多层压缩管线，而不用重写 `AgentRuntime`。

## References

- `learn-claude-code/s08_context_compact`: https://github.com/shareAI-lab/learn-claude-code/tree/main/s08_context_compact
- OpenCode: https://github.com/opencode-ai/opencode
- NanoBot: https://github.com/HKUDS/NanoBot
- Pi Agent Harness: https://github.com/earendil-works/pi
