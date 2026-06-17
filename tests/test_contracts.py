import pytest

from citrus.context.builder import ContextBuilder
from citrus.memory.noop import NoopMemoryStore
from citrus.permissions.policy import GradedPermissionPolicy
from citrus.providers.base import ModelRequest, ModelResponse
from citrus.providers.fake import FakeProvider
from citrus.runtime.messages import Message, TextBlock, ToolResult
from citrus.tools.base import Tool, ToolContext
from citrus.tools.registry import ToolRegistry


def test_fake_provider_returns_scripted_response() -> None:
    provider = FakeProvider(
        responses=[
            ModelResponse(messages=[Message.assistant_text("hello from fake")]),
        ]
    )

    response = provider.complete(ModelRequest(messages=[Message.user_text("hi")]))

    assert response.messages[0].content[0] == TextBlock(text="hello from fake")


def test_tool_registry_registers_and_returns_tools() -> None:
    class EchoTool:
        name = "echo"
        description = "Echo input"
        input_schema = {"type": "object"}

        def run(self, input: dict[str, object], context: ToolContext) -> ToolResult:
            return ToolResult(tool_call_id="echo-1", content=str(input["text"]))

    tool: Tool = EchoTool()
    registry = ToolRegistry()

    registry.register(tool)

    assert registry.get("echo") is tool
    assert registry.list() == [tool]


def test_tool_registry_raises_for_unknown_tool() -> None:
    registry = ToolRegistry()

    with pytest.raises(KeyError, match="Unknown tool"):
        registry.get("missing")


def test_permission_policy_allows_reads_and_gates_mutations() -> None:
    policy = GradedPermissionPolicy()

    read = policy.evaluate_tool("read_file")
    write = policy.evaluate_tool("write_file")
    shell = policy.evaluate_tool("run_shell", command="pytest")
    dangerous = policy.evaluate_tool("run_shell", command="rm -rf /tmp/example")

    assert read.outcome == "allow"
    assert write.outcome == "ask"
    assert shell.outcome == "ask"
    assert dangerous.outcome == "deny"


def test_context_builder_includes_user_task() -> None:
    messages = ContextBuilder().build(task="inspect this repository")

    assert messages == [Message.user_text("inspect this repository")]


def test_noop_memory_store_is_empty_and_accepts_writes() -> None:
    store = NoopMemoryStore()

    assert store.search("coding style") == []
    store.put("project", "Use pytest for tests")
    assert store.search("pytest") == []

