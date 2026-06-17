from typing import Literal

from pydantic import BaseModel

PermissionOutcome = Literal["allow", "deny", "ask"]


class PermissionDecision(BaseModel):
    outcome: PermissionOutcome
    reason: str

