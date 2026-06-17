from citrus.permissions.base import PermissionDecision


class GradedPermissionPolicy:
    """Small default policy for local coding tools."""

    def evaluate_tool(
        self,
        tool_name: str,
        command: str | None = None,
    ) -> PermissionDecision:
        if tool_name == "read_file":
            return PermissionDecision(
                outcome="allow",
                reason="File reads are safe by default.",
            )

        if tool_name == "write_file":
            return PermissionDecision(
                outcome="ask",
                reason="File writes modify the workspace.",
            )

        if tool_name == "run_shell":
            if command and self._is_dangerous_shell_command(command):
                return PermissionDecision(
                    outcome="deny",
                    reason="Dangerous shell command denied by default.",
                )
            return PermissionDecision(
                outcome="ask",
                reason="Shell commands require approval.",
            )

        return PermissionDecision(
            outcome="ask",
            reason="Unknown tools require approval.",
        )

    def _is_dangerous_shell_command(self, command: str) -> bool:
        normalized = command.strip().lower()
        return "rm -rf" in normalized or normalized.startswith("sudo ")
