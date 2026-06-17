from typing import Annotated

import typer

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
) -> None:
    """Run a coding-agent task."""
    typer.echo(f"CitrusButter runtime is not implemented yet. Task: {task}")


@app.command()
def providers() -> None:
    """Show configured model providers."""
    typer.echo("No providers configured yet.")


@app.command()
def config() -> None:
    """Show or update CitrusButter configuration."""
    typer.echo("Configuration support is not implemented yet.")

