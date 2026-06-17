import subprocess

from citrus.runtime.messages import ToolResult
from citrus.tools.base import ToolContext


class RunShellTool:
    name = "run_shell"
    description = "Run a shell command in the workspace."
    input_schema: dict[str, object] = {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
    }

    def run(self, input: dict[str, object], context: ToolContext) -> ToolResult:
        command = str(input["command"])
        completed = subprocess.run(
            command,
            cwd=context.workspace,
            shell=True,
            check=False,
            text=True,
            capture_output=True,
            timeout=30,
        )
        content = completed.stdout if completed.stdout else completed.stderr
        return ToolResult(
            tool_call_id=context.tool_call_id,
            content=content,
            is_error=completed.returncode != 0,
        )
