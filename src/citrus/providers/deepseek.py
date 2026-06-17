from citrus.providers.openai import OpenAIProvider


class DeepSeekProvider(OpenAIProvider):
    name = "deepseek"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        client: object | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.deepseek.com",
            client=client,
        )
