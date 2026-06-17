from __future__ import annotations

from collections.abc import Sequence

from citrus.tools.base import Tool
from citrus.tools.sources import ToolSource


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def list(self) -> list[Tool]:
        return list(self._tools.values())

    @classmethod
    def from_sources(cls, sources: Sequence[ToolSource]) -> ToolRegistry:
        registry = cls()
        for source in sources:
            for tool in source.list_tools():
                registry.register(tool)
        return registry

    @classmethod
    def with_default_local_tools(cls) -> ToolRegistry:
        from citrus.tools.local import (
            ReadFileTool,
            RunShellTool,
            SearchFilesTool,
            WriteFileTool,
        )

        registry = cls()
        tools: list[Tool] = [
            ReadFileTool(),
            WriteFileTool(),
            SearchFilesTool(),
            RunShellTool(),
        ]
        for tool in tools:
            registry.register(tool)
        return registry
