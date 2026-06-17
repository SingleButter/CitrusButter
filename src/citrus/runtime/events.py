from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EventType(StrEnum):
    TASK_STARTED = "task_started"
    CONTEXT_BUILT = "context_built"
    MODEL_REQUESTED = "model_requested"
    MODEL_RESPONDED = "model_responded"
    TOOL_REQUESTED = "tool_requested"
    PERMISSION_REQUESTED = "permission_requested"
    PERMISSION_RESOLVED = "permission_resolved"
    TOOL_COMPLETED = "tool_completed"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"


class SessionEvent(BaseModel):
    session_id: str
    type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RuntimeObserver:
    def on_event(self, event: SessionEvent) -> None:
        return None

