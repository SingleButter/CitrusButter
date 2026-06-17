import os
from typing import Annotated

import typer

from citrus.config.settings import ProviderSettingsError, build_provider
from citrus.context.builder import ContextBuilder
from citrus.permissions.policy import GradedPermissionPolicy
from citrus.providers.base import ModelResponse
from citrus.providers.fake import FakeProvider
from citrus.runtime.agent import AgentRuntime, RunRequest
from citrus.runtime.messages import Message
from citrus.sessions.memory import InMemorySessionStore
from citrus.tools.registry import ToolRegistry

app = typer.Typer(
    help="CitrusButter: a modular coding agent harness.",
    no_args_is_help=True,
)


@app.command()
def run(
    task: Annotated[
        str,
        typer.Argument(help="Coding task for the CitrusButter runtime."),
    ],
    provider: Annotated[str, typer.Option(help="Provider to use.")] = "fake",
    model: Annotated[
        str | None,
        typer.Option(help="Model override for real providers."),
    ] = None,
    fake_response: Annotated[
        str,
        typer.Option(help="Scripted response for the fake provider."),
    ] = "CitrusButter fake provider completed the task.",
) -> None:
    """Run a coding-agent task."""
    try:
        selected_provider = (
            FakeProvider(
                responses=[
                    ModelResponse(messages=[Message.assistant_text(fake_response)]),
                ]
            )
            if provider == "fake"
            else build_provider(provider, model=model, env=os.environ)
        )
    except ProviderSettingsError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    runtime = AgentRuntime(
        provider=selected_provider,
        tools=ToolRegistry.with_default_local_tools(),
        permissions=GradedPermissionPolicy(auto_approve=False),
        context=ContextBuilder(),
        session_store=InMemorySessionStore(),
    )
    result = runtime.run(RunRequest(task=task))
    typer.echo(result.final_message)


@app.command()
def providers() -> None:
    """Show configured model providers."""
    typer.echo("anthropic")
    typer.echo("openai")
    typer.echo("deepseek")
    typer.echo("fake")


@app.command()
def config() -> None:
    """Show or update CitrusButter configuration."""
    typer.echo(f"CITRUS_PROVIDER={os.getenv('CITRUS_PROVIDER', 'fake')}")
    typer.echo(f"CITRUS_MODEL={os.getenv('CITRUS_MODEL', '')}")
    typer.echo(
        "Provider API keys are read from provider-specific environment variables."
    )
