from citrus.tools.registry import ToolRegistry
from citrus.tools.sources import StaticToolSource


def test_registry_can_load_tools_from_tool_source() -> None:
    registry = ToolRegistry.from_sources([StaticToolSource([])])

    assert registry.list() == []

