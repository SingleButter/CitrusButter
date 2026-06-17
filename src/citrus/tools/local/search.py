from pathlib import Path

from citrus.runtime.messages import ToolResult
from citrus.tools.base import ToolContext
from citrus.tools.local.paths import resolve_workspace_path


class SearchFilesTool:
    name = "search_files"
    description = "Search workspace text files for a literal query."
    input_schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "path": {"type": "string"},
        },
        "required": ["query"],
    }

    def run(self, input: dict[str, object], context: ToolContext) -> ToolResult:
        try:
            query = str(input["query"])
            root = resolve_workspace_path(
                context.workspace,
                str(input.get("path", ".")),
            )
            matches = self._search(root, context.workspace.resolve(), query)
            return ToolResult(
                tool_call_id=context.tool_call_id,
                content="\n".join(matches),
            )
        except Exception as exc:
            return ToolResult(
                tool_call_id=context.tool_call_id,
                content=str(exc),
                is_error=True,
            )

    def _search(self, root: Path, workspace: Path, query: str) -> list[str]:
        files = [root] if root.is_file() else sorted(path for path in root.rglob("*"))
        matches: list[str] = []
        for path in files:
            if not path.is_file() or any(part.startswith(".") for part in path.parts):
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(lines, start=1):
                if query in line:
                    relative = path.relative_to(workspace)
                    matches.append(f"{relative}:{line_number}:{line}")
        return matches
