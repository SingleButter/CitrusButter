from collections.abc import Sequence

from citrus.providers.base import ModelRequest, ModelResponse


class FakeProvider:
    """Deterministic provider for tests and offline demos."""

    name = "fake"

    def __init__(
        self,
        responses: Sequence[ModelResponse],
        repeat_last: bool = False,
    ) -> None:
        self._responses = list(responses)
        self._repeat_last = repeat_last
        self._index = 0
        self.requests: list[ModelRequest] = []

    def complete(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        if self._index >= len(self._responses):
            if self._repeat_last and self._responses:
                return self._responses[-1]
            raise RuntimeError("FakeProvider has no scripted responses left.")

        response = self._responses[self._index]
        self._index += 1
        return response
