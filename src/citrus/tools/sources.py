from typing import Protocol

from citrus.tools.base import Tool


class ToolSource(Protocol):
    def list_tools(self) -> list[Tool]:
        ...


class StaticToolSource:
    def __init__(self, tools: list[Tool]) -> None:
        self._tools = tools

    def list_tools(self) -> list[Tool]:
        return list(self._tools)

