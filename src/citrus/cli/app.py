import json
import os
from typing import Annotated

import typer

from citrus.config.settings import ProviderSettingsError, build_provider, load_config
from citrus.context.builder import ContextBuilder
from citrus.permissions.base import PermissionDecision, PermissionRequest
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


def _approve_permission(request: PermissionRequest) -> PermissionDecision:
    typer.echo(f"Tool {request.tool_name} requires approval.")
    typer.echo(f"Reason: {request.reason}")
    if request.command:
        typer.echo(f"Command: {request.command}")
    else:
        arguments = json.dumps(
            request.arguments,
            ensure_ascii=False,
            sort_keys=True,
        )
        typer.echo(f"Arguments: {arguments}")

    approved = typer.confirm(f"Allow tool {request.tool_name}?", default=False)
    if approved:
        return PermissionDecision(outcome="allow", reason="Approved by user.")
    return PermissionDecision(outcome="deny", reason="Denied by user.")


@app.command()
def run(
    task: Annotated[
        str,
        typer.Argument(help="Coding task for the CitrusButter runtime."),
    ],
    provider: Annotated[
        str | None,
        typer.Option(help="Provider to use. Defaults to config file."),
    ] = None,
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
        config = load_config(os.environ)
        selected_provider_name = provider or config.provider
        selected_provider = (
            FakeProvider(
                responses=[
                    ModelResponse(messages=[Message.assistant_text(fake_response)]),
                ]
            )
            if selected_provider_name == "fake"
            else build_provider(
                selected_provider_name,
                model=model,
                env=os.environ,
                config=config,
            )
        )
    except ProviderSettingsError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    runtime = AgentRuntime(
        provider=selected_provider,
        tools=ToolRegistry.with_default_local_tools(),
        permissions=GradedPermissionPolicy(auto_approve=False),
        permission_approver=_approve_permission,
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
    loaded = load_config(os.environ)
    typer.echo(f"config={loaded.path}")
    typer.echo(f"provider={os.getenv('CITRUS_PROVIDER', loaded.provider)}")
    typer.echo(f"model={os.getenv('CITRUS_MODEL', loaded.model or '')}")
    for name, provider_config in sorted(loaded.providers.items()):
        key_state = "configured" if provider_config.api_key else "missing"
        model_state = provider_config.model or ""
        typer.echo(f"{name} api_key={key_state} model={model_state}")
    typer.echo("Environment variables override config file values.")
