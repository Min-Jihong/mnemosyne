import sys
import signal
import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from mnemosyne import __version__

app = typer.Typer(
    name="mnemosyne",
    help="Learn to Think Like You - A digital twin that learns your computer behavior",
    no_args_is_help=True,
)
console = Console()

DEFAULT_DATA_DIR = Path.home() / ".mnemosyne"


@app.command()
def setup():
    """Interactive setup wizard for Mnemosyne."""
    from mnemosyne.cli.setup import run_setup
    run_setup()


@app.command()
def record(
    name: str = typer.Option("", "--name", "-n", help="Session name"),
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d", help="Data directory"),
):
    """Start recording your computer activity."""
    from mnemosyne.store.session_manager import SessionManager
    from mnemosyne.capture.recorder import RecorderConfig
    
    config = RecorderConfig(output_dir=data_dir / "screenshots")
    manager = SessionManager(data_dir=data_dir, recorder_config=config)
    
    session = manager.start_session(name=name)
    
    console.print(Panel(
        f"[bold green]Recording started![/bold green]\n\n"
        f"Session ID: [cyan]{session.id}[/cyan]\n"
        f"Name: {session.name}\n\n"
        "Press [bold]Ctrl+C[/bold] to stop recording.",
        title="Mnemosyne Recorder",
    ))
    
    def signal_handler(sig, frame):
        console.print("\n[yellow]Stopping recording...[/yellow]")
        final_session = manager.stop_session()
        if final_session:
            console.print(Panel(
                f"[bold]Session completed![/bold]\n\n"
                f"Duration: {final_session.duration_seconds:.1f}s\n"
                f"Events: {final_session.event_count}\n"
                f"Screenshots: {final_session.screenshot_count}",
                title="Recording Summary",
            ))
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        while True:
            signal.pause()
    except AttributeError:
        import time
        while True:
            time.sleep(1)


@app.command()
def sessions(
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of sessions to show"),
):
    """List recorded sessions."""
    from mnemosyne.store.database import Database
    
    db = Database(data_dir / "mnemosyne.db")
    session_list = db.list_sessions(limit=limit)
    
    if not session_list:
        console.print("[yellow]No sessions found.[/yellow]")
        return
    
    table = Table(title="Recording Sessions")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Duration")
    table.add_column("Events")
    table.add_column("Screenshots")
    
    for s in session_list:
        duration = f"{s.duration_seconds:.1f}s" if s.ended_at else "Running"
        table.add_row(
            s.id[:8],
            s.name[:30] if s.name else "-",
            duration,
            str(s.event_count),
            str(s.screenshot_count),
        )
    
    console.print(table)


@app.command()
def analyze(
    session_id: str = typer.Argument(..., help="Session ID to analyze"),
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
    batch_size: int = typer.Option(10, "--batch", "-b", help="Batch size for analysis"),
):
    """Analyze a session with LLM to infer intents."""
    from mnemosyne.config import load_settings
    from mnemosyne.store.database import Database
    from mnemosyne.llm.factory import create_llm_provider
    from mnemosyne.reason.intent import IntentInferrer
    
    settings = load_settings()
    db = Database(data_dir / "mnemosyne.db")
    
    session = db.get_session(session_id)
    if not session:
        for s in db.list_sessions():
            if s.id.startswith(session_id):
                session = s
                break
    
    if not session:
        console.print(f"[red]Session not found: {session_id}[/red]")
        raise typer.Exit(1)
    
    llm = create_llm_provider(settings.llm)
    inferrer = IntentInferrer(llm=llm, database=db)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing events...", total=None)
        
        async def run_analysis():
            return await inferrer.batch_infer(
                session_id=session.id,
                batch_size=batch_size,
            )
        
        count = asyncio.run(run_analysis())
        progress.update(task, completed=True)
    
    console.print(f"[green]Analyzed {count} events.[/green]")


@app.command()
def curious(
    session_id: str = typer.Argument(..., help="Session ID to explore"),
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
):
    """Let the curious LLM explore and ask questions about a session."""
    from mnemosyne.config import load_settings
    from mnemosyne.store.database import Database
    from mnemosyne.llm.factory import create_llm_provider
    from mnemosyne.reason.curious import CuriousLLM
    from mnemosyne.store.models import StoredEvent
    
    settings = load_settings()
    db = Database(data_dir / "mnemosyne.db")
    
    session = db.get_session(session_id)
    if not session:
        for s in db.list_sessions():
            if s.id.startswith(session_id):
                session = s
                break
    
    if not session:
        console.print(f"[red]Session not found: {session_id}[/red]")
        raise typer.Exit(1)
    
    llm = create_llm_provider(settings.llm)
    curious_llm = CuriousLLM(llm=llm, database=db)
    
    events = db.get_events(session.id, limit=100)
    
    console.print(Panel(
        f"[bold]Exploring session:[/bold] {session.name or session.id}\n"
        f"Events: {len(events)}",
        title="Curious LLM",
    ))
    
    async def run_curiosity():
        return await curious_llm.observe_and_wonder(events)
    
    curiosities = asyncio.run(run_curiosity())
    
    if curiosities:
        console.print("\n[bold cyan]Questions generated:[/bold cyan]\n")
        for i, c in enumerate(curiosities, 1):
            importance_color = "green" if c.importance > 0.7 else "yellow" if c.importance > 0.4 else "white"
            console.print(f"  {i}. [{importance_color}]{c.question}[/{importance_color}]")
            console.print(f"     Category: {c.category} | Importance: {c.importance:.2f}")
            console.print()
    else:
        console.print("[yellow]No curiosities generated. Need more events.[/yellow]")


@app.command()
def memory(
    query: str = typer.Argument(None, help="Search query for memories"),
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
    recent: bool = typer.Option(False, "--recent", "-r", help="Show recent memories"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
):
    """Search or browse persistent memory."""
    from mnemosyne.memory.persistent import PersistentMemory
    
    mem = PersistentMemory(data_dir=data_dir / "memory")
    
    if recent or not query:
        memories = mem.get_recent(n=limit)
        title = "Recent Memories"
    else:
        memories = mem.recall(query=query, n_results=limit)
        title = f"Memories matching '{query}'"
    
    if not memories:
        console.print("[yellow]No memories found.[/yellow]")
        return
    
    table = Table(title=title)
    table.add_column("Type", style="cyan")
    table.add_column("Content")
    table.add_column("Importance")
    table.add_column("Accessed")
    
    for m in memories:
        content = m.content[:50] + "..." if len(m.content) > 50 else m.content
        table.add_row(
            m.type.value,
            content,
            f"{m.importance:.2f}",
            str(m.access_count),
        )
    
    console.print(table)
    console.print(f"\n[dim]Total memories: {mem.count()}[/dim]")


@app.command()
def export(
    session_id: str = typer.Argument(..., help="Session ID to export"),
    output: Path = typer.Option(Path("export"), "--output", "-o", help="Output directory"),
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
):
    """Export session data for training."""
    from mnemosyne.store.database import Database
    from mnemosyne.learn.dataset import BehaviorDataset
    
    db = Database(data_dir / "mnemosyne.db")
    dataset = BehaviorDataset(database=db)
    
    output.mkdir(parents=True, exist_ok=True)
    output_file = output / f"{session_id}.jsonl"
    
    count = dataset.export_to_jsonl(session_id, output_file)
    stats = dataset.get_statistics(session_id)
    
    console.print(Panel(
        f"[bold green]Export complete![/bold green]\n\n"
        f"File: {output_file}\n"
        f"Events: {count}\n"
        f"Intent coverage: {stats['intent_coverage']:.1%}",
        title="Export Summary",
    ))


@app.command()
def execute(
    goal: str = typer.Argument(..., help="Goal to execute"),
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
    confirm: bool = typer.Option(True, "--confirm/--no-confirm", help="Require confirmation"),
    max_steps: int = typer.Option(20, "--max-steps", "-m", help="Maximum steps"),
):
    """Execute a goal using the learned behavior model."""
    from mnemosyne.config import load_settings
    from mnemosyne.llm.factory import create_llm_provider
    from mnemosyne.memory.persistent import PersistentMemory
    from mnemosyne.execute.agent import ExecutionAgent
    from mnemosyne.execute.safety import SafetyConfig
    
    settings = load_settings()
    llm = create_llm_provider(settings.llm)
    mem = PersistentMemory(data_dir=data_dir / "memory")
    
    safety_config = SafetyConfig(
        enabled=True,
        require_confirmation=confirm,
    )
    
    agent = ExecutionAgent(
        llm=llm,
        memory=mem,
        safety_config=safety_config,
        on_action=lambda t, d: console.print(f"  [cyan]Action:[/cyan] {t}"),
        on_error=lambda e: console.print(f"  [red]Error:[/red] {e}"),
    )
    
    console.print(Panel(
        f"[bold]Goal:[/bold] {goal}\n"
        f"[bold]Max steps:[/bold] {max_steps}\n"
        f"[bold]Confirmation:[/bold] {'Required' if confirm else 'Not required'}",
        title="Execution Agent",
    ))
    
    console.print("\n[yellow]Starting execution...[/yellow]\n")
    
    result = asyncio.run(
        agent.execute_goal(
            goal=goal,
            max_steps=max_steps,
            require_confirmation=confirm,
        )
    )
    
    status = "[green]Success[/green]" if result["completed"] else "[red]Failed[/red]"
    console.print(Panel(
        f"[bold]Status:[/bold] {status}\n"
        f"[bold]Actions taken:[/bold] {result['actions_taken']}\n"
        f"[bold]Errors:[/bold] {len(result['errors'])}",
        title="Execution Result",
    ))


@app.command()
def tui(
    port: int = typer.Option(8000, "--port", "-p", help="Web server port"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Don't open browser automatically"),
):
    """Launch the interactive TUI with web interface."""
    import threading
    import webbrowser
    import time
    
    try:
        import textual
    except ImportError:
        console.print("[red]Textual not installed.[/red]")
        console.print("Install with: [cyan]pip install textual[/cyan]")
        console.print("Or install all TUI deps: [cyan]pip install 'mnemosyne[tui]'[/cyan]")
        raise typer.Exit(1)
    
    try:
        from mnemosyne.tui.app import run_tui
    except ImportError as e:
        console.print(f"[red]Failed to load TUI: {e}[/red]")
        raise typer.Exit(1)
    
    try:
        import uvicorn
    except ImportError:
        console.print("[yellow]Web dependencies not installed. Running TUI only.[/yellow]")
        console.print("Install with: [cyan]pip install 'mnemosyne[web]'[/cyan]")
        run_tui()
        return
    
    def run_web_server():
        config = uvicorn.Config(
            "mnemosyne.web.app:app",
            host="127.0.0.1",
            port=port,
            log_level="warning",
        )
        server = uvicorn.Server(config)
        server.run()
    
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    time.sleep(1.5)
    
    if not no_browser:
        webbrowser.open(f"http://localhost:{port}")
    
    console.print(Panel(
        f"[bold green]Mnemosyne Started[/bold green]\n\n"
        f"Web UI: [cyan]http://localhost:{port}[/cyan]\n"
        f"TUI: Running in terminal\n\n"
        "Press [bold]q[/bold] in TUI or [bold]Ctrl+C[/bold] to exit.",
        title="🧠 Mnemosyne",
    ))
    
    run_tui()


@app.command()
def web(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
):
    """Start the web interface for Mnemosyne."""
    try:
        from mnemosyne.web.app import run_server
    except ImportError:
        console.print("[red]Web dependencies not installed.[/red]")
        console.print("Install with: pip install 'mnemosyne[web]'")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"[bold green]Starting Mnemosyne Web UI[/bold green]\n\n"
        f"Open [cyan]http://localhost:{port}[/cyan] in your browser\n\n"
        f"Features:\n"
        f"  • Chat with your digital twin\n"
        f"  • Configure LLM API keys\n"
        f"  • Control recording sessions\n"
        f"  • Search memories\n\n"
        "Press [bold]Ctrl+C[/bold] to stop.",
        title="🧠 Mnemosyne",
    ))
    
    run_server(host=host, port=port, reload=reload)


@app.command()
def status():
    """Show current status and configuration."""
    from mnemosyne.config import load_settings
    
    try:
        settings = load_settings()
        console.print(Panel(
            f"[bold]LLM Provider:[/bold] {settings.llm.provider.value}\n"
            f"[bold]Model:[/bold] {settings.llm.model}\n"
            f"[bold]Curiosity Mode:[/bold] {settings.curiosity.mode.value}",
            title="Mnemosyne Status",
        ))
    except Exception:
        console.print("[yellow]Configuration not found. Run 'mnemosyne setup' first.[/yellow]")


@app.command()
def doctor():
    """Diagnose installation and environment issues."""
    import platform
    import shutil
    
    checks: list[tuple[str, bool, str]] = []
    
    checks.append(("Mnemosyne version", True, __version__))
    checks.append(("Python version", True, f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"))
    checks.append(("Platform", True, f"{platform.system()} {platform.machine()}"))
    
    config_path = DEFAULT_DATA_DIR / "config.toml"
    checks.append(("Config file", config_path.exists(), str(config_path)))
    
    data_dir = DEFAULT_DATA_DIR
    checks.append(("Data directory", data_dir.exists(), str(data_dir)))
    
    try:
        from mnemosyne.config import load_settings
        settings = load_settings()
        checks.append(("Configuration", True, f"Provider: {settings.llm.provider.value}"))
    except Exception as e:
        checks.append(("Configuration", False, str(e)[:50]))
    
    try:
        import chromadb
        checks.append(("ChromaDB", True, chromadb.__version__))
    except (ImportError, Exception) as e:
        error_msg = str(e)[:30] if str(e) else "Import failed"
        checks.append(("ChromaDB", False, error_msg))
    
    try:
        import anthropic
        checks.append(("Anthropic SDK", True, anthropic.__version__))
    except ImportError:
        checks.append(("Anthropic SDK", False, "Not installed"))
    
    try:
        import openai
        checks.append(("OpenAI SDK", True, openai.__version__))
    except ImportError:
        checks.append(("OpenAI SDK", False, "Not installed"))
    
    try:
        import fastapi
        checks.append(("FastAPI (web)", True, fastapi.__version__))
    except ImportError:
        checks.append(("FastAPI (web)", False, "Not installed (optional)"))
    
    try:
        import textual
        checks.append(("Textual (TUI)", True, textual.__version__))
    except ImportError:
        checks.append(("Textual (TUI)", False, "Not installed (optional)"))
    
    try:
        import pynput
        checks.append(("pynput (capture)", True, "Available"))
    except ImportError:
        checks.append(("pynput (capture)", False, "Not installed"))
    
    if platform.system() == "Darwin":
        try:
            import Quartz
            checks.append(("macOS Quartz", True, "Available"))
        except ImportError:
            checks.append(("macOS Quartz", False, "Not installed (optional)"))
    
    console.print(Panel("[bold]Mnemosyne Doctor[/bold]\nDiagnostic information for troubleshooting", title="🩺 Doctor"))
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Details")
    
    all_passed = True
    for name, passed, details in checks:
        status_icon = "[green]✓[/green]" if passed else "[red]✗[/red]"
        if not passed and "optional" not in details.lower():
            all_passed = False
        table.add_row(name, status_icon, details)
    
    console.print(table)
    
    if all_passed:
        console.print("\n[green]All checks passed![/green]")
    else:
        console.print("\n[yellow]Some checks failed. Run 'mnemosyne setup' to configure.[/yellow]")
    
    console.print("\n[dim]Copy this output when reporting issues.[/dim]")


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold]Mnemosyne[/bold] v{__version__}")


if __name__ == "__main__":
    app()
