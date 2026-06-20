from pathlib import Path

from citrus.context.compactor import ContextCompactor, DeterministicContextCompactor
from citrus.runtime.messages import Message


class ContextBuilder:
    """Build model messages for a runtime turn."""

    def __init__(self, compactor: ContextCompactor | None = None) -> None:
        self._compactor = compactor or DeterministicContextCompactor()

    def build(
        self,
        task: str,
        messages: list[Message] | None = None,
        workspace: Path | None = None,
    ) -> list[Message]:
        _ = workspace
        return [*(messages or []), Message.user_text(task)]

    def prepare_for_model(self, messages: list[Message]) -> list[Message]:
        return self._compactor.compact(messages)
