from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from citrus.context.builder import ContextBuilder
from citrus.memory.service import MemoryService
from citrus.permissions.policy import GradedPermissionPolicy
from citrus.providers.base import ModelProvider, ModelRequest, ToolSpec
from citrus.runtime.events import EventType, RuntimeObserver, SessionEvent
from citrus.runtime.messages import Message, ToolCall, ToolResult
from citrus.sessions.base import SessionStore
from citrus.tools.base import ToolContext
from citrus.tools.registry import ToolRegistry


class RunRequest(BaseModel):
    task: str
    workspace: Path = Field(default_factory=Path.cwd)
    session_id: str | None = None
    max_turns: int = 8


class RunResult(BaseModel):
    session_id: str
    success: bool
    final_message: str


class AgentRuntime:
    def __init__(
        self,
        provider: ModelProvider,
        tools: ToolRegistry,
        permissions: GradedPermissionPolicy,
        context: ContextBuilder,
        session_store: SessionStore,
        memory: MemoryService | None = None,
        observers: list[RuntimeObserver] | None = None,
    ) -> None:
        self._provider = provider
        self._tools = tools
        self._permissions = permissions
        self._context = context
        self._session_store = session_store
        self._memory = memory
        self._observers = observers or []

    def run(self, request: RunRequest) -> RunResult:
        session_id = request.session_id or str(uuid4())
        workspace = request.workspace.resolve()

        self._emit(session_id, EventType.TASK_STARTED, {"task": request.task})
        messages = self._context.build(task=request.task)
        self._emit(session_id, EventType.CONTEXT_BUILT, {"messages": len(messages)})

        for _turn in range(request.max_turns):
            self._emit(session_id, EventType.MODEL_REQUESTED, {})
            response = self._provider.complete(
                ModelRequest(messages=messages, tools=self._tool_specs())
            )
            self._emit(
                session_id,
                EventType.MODEL_RESPONDED,
                {"messages": len(response.messages)},
            )
            messages.extend(response.messages)

            tool_calls = self._collect_tool_calls(response.messages)
            if not tool_calls:
                final_message = self._final_text(response.messages)
                self._emit(
                    session_id,
                    EventType.TASK_COMPLETED,
                    {"final_message": final_message},
                )
                return RunResult(
                    session_id=session_id,
                    success=True,
                    final_message=final_message,
                )

            for tool_call in tool_calls:
                tool_result = self._execute_tool_call(session_id, tool_call, workspace)
                if tool_result.is_error:
                    final_message = tool_result.content
                    self._emit(
                        session_id,
                        EventType.TASK_FAILED,
                        {"reason": final_message},
                    )
                    return RunResult(
                        session_id=session_id,
                        success=False,
                        final_message=final_message,
                    )
                messages.append(Message.tool_text(tool_call.id, tool_result.content))

        final_message = "Agent reached the maximum turn limit."
        self._emit(session_id, EventType.TASK_FAILED, {"reason": final_message})
        return RunResult(
            session_id=session_id,
            success=False,
            final_message=final_message,
        )

    def _execute_tool_call(
        self,
        session_id: str,
        tool_call: ToolCall,
        workspace: Path,
    ) -> ToolResult:
        self._emit(
            session_id,
            EventType.TOOL_REQUESTED,
            {"tool": tool_call.name, "arguments": tool_call.arguments},
        )
        command = tool_call.arguments.get("command")
        self._emit(session_id, EventType.PERMISSION_REQUESTED, {"tool": tool_call.name})
        decision = self._permissions.evaluate_tool(
            tool_call.name,
            command=command if isinstance(command, str) else None,
        )
        if decision.outcome == "ask" and self._permissions.auto_approve:
            decision = decision.model_copy(update={"outcome": "allow"})
        self._emit(
            session_id,
            EventType.PERMISSION_RESOLVED,
            {"outcome": decision.outcome, "reason": decision.reason},
        )
        if decision.outcome != "allow":
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"Tool {tool_call.name} denied: {decision.reason}",
                is_error=True,
            )

        tool = self._tools.get(tool_call.name)
        tool_result = tool.run(
            tool_call.arguments,
            ToolContext(workspace=workspace, tool_call_id=tool_call.id),
        )
        self._emit(
            session_id,
            EventType.TOOL_COMPLETED,
            {
                "tool": tool_call.name,
                "is_error": tool_result.is_error,
                "content": tool_result.content,
            },
        )
        return tool_result

    def _emit(
        self,
        session_id: str,
        event_type: EventType,
        payload: dict[str, object],
    ) -> None:
        event = SessionEvent(session_id=session_id, type=event_type, payload=payload)
        self._session_store.append(event)
        for observer in self._observers:
            observer.on_event(event)

    def _collect_tool_calls(self, messages: list[Message]) -> list[ToolCall]:
        calls: list[ToolCall] = []
        for message in messages:
            calls.extend(message.tool_calls())
        return calls

    def _final_text(self, messages: list[Message]) -> str:
        for message in reversed(messages):
            text = message.text()
            if text:
                return text
        return ""

    def _tool_specs(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name=tool.name,
                description=tool.description,
                input_schema=tool.input_schema,
            )
            for tool in self._tools.list()
        ]
