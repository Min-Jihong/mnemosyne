"""Main CLI entry point for Mnemosyne."""

import typer
from rich.console import Console
from rich.panel import Panel

from mnemosyne import __version__

app = typer.Typer(
    name="mnemosyne",
    help="Learn to Think Like You - A digital twin that learns your computer behavior",
    no_args_is_help=True,
)
console = Console()


@app.command()
def setup():
    """Interactive setup wizard for Mnemosyne."""
    from mnemosyne.cli.setup import run_setup
    run_setup()


@app.command()
def record(
    description: str = typer.Option(None, "--description", "-d", help="Session description"),
):
    """Start recording your computer activity."""
    console.print(Panel(
        "[bold green]Recording started![/bold green]\n"
        "Press Ctrl+C to stop recording.",
        title="Mnemosyne Recorder",
    ))
    # TODO: Implement recording


@app.command()
def stop():
    """Stop the current recording session."""
    console.print("[yellow]Stopping recording...[/yellow]")
    # TODO: Implement stop


@app.command()
def status():
    """Show current status and configuration."""
    from mnemosyne.config import load_settings
    
    settings = load_settings()
    
    console.print(Panel(
        f"[bold]LLM Provider:[/bold] {settings.llm.provider.value}\n"
        f"[bold]Model:[/bold] {settings.llm.model}\n"
        f"[bold]Embedding:[/bold] {settings.embedding.provider.value} ({settings.embedding.model})\n"
        f"[bold]Curiosity Mode:[/bold] {settings.curiosity.mode.value}",
        title="Mnemosyne Status",
    ))


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold]Mnemosyne[/bold] v{__version__}")


if __name__ == "__main__":
    app()
