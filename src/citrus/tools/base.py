from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from citrus.runtime.messages import ToolResult


class ToolContext(BaseModel):
    workspace: Path = Field(default_factory=Path.cwd)


class Tool(Protocol):
    name: str
    description: str
    input_schema: dict[str, object]

    def run(self, input: dict[str, object], context: ToolContext) -> ToolResult:
        ...

