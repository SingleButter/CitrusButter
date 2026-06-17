from citrus.runtime.messages import Message


class ContextBuilder:
    """Build model messages for a runtime turn."""

    def build(self, task: str) -> list[Message]:
        return [Message.user_text(task)]

