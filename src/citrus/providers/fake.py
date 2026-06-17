from collections.abc import Sequence

from citrus.providers.base import ModelRequest, ModelResponse


class FakeProvider:
    """Deterministic provider for tests and offline demos."""

    name = "fake"

    def __init__(self, responses: Sequence[ModelResponse]) -> None:
        self._responses = list(responses)
        self._index = 0

    def complete(self, request: ModelRequest) -> ModelResponse:
        if self._index >= len(self._responses):
            raise RuntimeError("FakeProvider has no scripted responses left.")

        response = self._responses[self._index]
        self._index += 1
        return response

