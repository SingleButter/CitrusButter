from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel

PermissionOutcome = Literal["allow", "deny", "ask"]


class PermissionDecision(BaseModel):
    outcome: PermissionOutcome
    reason: str


class PermissionRequest(BaseModel):
    tool_name: str
    tool_call_id: str
    arguments: dict[str, object]
    reason: str
    command: str | None = None


PermissionApprover = Callable[[PermissionRequest], PermissionDecision]
