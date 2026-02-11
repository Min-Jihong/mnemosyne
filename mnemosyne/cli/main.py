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


@app.command()
def summary(
    period: str = typer.Argument("today", help="Period: today, yesterday, week"),
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text, json, html, markdown"),
    output: Path = typer.Option(None, "--output", "-o", help="Save report to file"),
):
    """Generate AI-powered activity summary."""
    from datetime import datetime, timedelta
    from mnemosyne.config import load_settings
    from mnemosyne.store.database import Database
    from mnemosyne.llm.factory import create_llm_provider
    from mnemosyne.analytics.summary import SummaryGenerator
    from mnemosyne.analytics.reports import ReportGenerator, ReportFormat
    
    settings = load_settings()
    db = Database(data_dir / "mnemosyne.db")
    llm = create_llm_provider(settings.llm)
    
    generator = SummaryGenerator(llm=llm, database=db)
    reporter = ReportGenerator(output_dir=data_dir / "reports")
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Generating summary...", total=None)
        
        if period == "week":
            result = asyncio.run(generator.generate_weekly_summary())
            report_name = f"weekly-{result.end_date.strftime('%Y-%m-%d')}"
        else:
            date = datetime.now()
            if period == "yesterday":
                date = date - timedelta(days=1)
            result = asyncio.run(generator.generate_daily_summary(date))
            report_name = f"daily-{result.date.strftime('%Y-%m-%d')}"
        
        progress.update(task, completed=True)
    
    fmt = ReportFormat(format) if format in ["json", "html", "markdown"] else None
    
    if fmt:
        if hasattr(result, 'daily_summaries'):
            content = reporter.generate_weekly_report(result, fmt)
        else:
            content = reporter.generate_daily_report(result, fmt)
        
        if output:
            with open(output, "w") as f:
                f.write(content)
            console.print(f"[green]Report saved to {output}[/green]")
        else:
            console.print(content)
    else:
        if hasattr(result, 'daily_summaries'):
            console.print(Panel(
                f"[bold]{result.headline}[/bold]\n\n"
                f"Period: {result.start_date.strftime('%b %d')} - {result.end_date.strftime('%b %d, %Y')}\n"
                f"Total Hours: {result.total_hours:.1f}h\n"
                f"Avg Productivity: {result.average_productivity:.0f}%\n\n"
                f"[cyan]Insights:[/cyan]\n" + "\n".join(f"  • {i}" for i in result.weekly_insights[:3]),
                title="📊 Weekly Summary",
            ))
        else:
            console.print(Panel(
                f"[bold]{result.headline}[/bold]\n\n"
                f"Date: {result.date.strftime('%A, %B %d, %Y')}\n"
                f"Active Time: {result.total_hours:.1f}h\n"
                f"Productivity: {result.productivity_score:.0f}%\n\n"
                f"[cyan]Top Apps:[/cyan] {', '.join(result.top_apps[:3])}\n\n"
                f"[cyan]Highlights:[/cyan]\n" + "\n".join(f"  • {h}" for h in result.highlights[:3]),
                title="📊 Daily Summary",
            ))


@app.command()
def stats(
    period: str = typer.Argument("today", help="Period: today, yesterday, week"),
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
):
    """Show work statistics and productivity metrics."""
    from datetime import datetime, timedelta
    from mnemosyne.store.database import Database
    from mnemosyne.analytics.statistics import StatisticsCalculator
    
    db = Database(data_dir / "mnemosyne.db")
    calculator = StatisticsCalculator(db)
    
    if period == "week":
        stats_list = calculator.calculate_weekly_stats()
        
        table = Table(title="📊 Weekly Statistics")
        table.add_column("Day", style="cyan")
        table.add_column("Hours")
        table.add_column("Productivity")
        table.add_column("Top App")
        table.add_column("Events")
        
        for s in stats_list:
            score_color = "green" if s.productivity.score >= 70 else "yellow" if s.productivity.score >= 40 else "red"
            table.add_row(
                s.date.strftime("%a %m/%d"),
                f"{s.total_active_hours:.1f}h",
                f"[{score_color}]{s.productivity.score:.0f}%[/{score_color}]",
                s.top_apps[0] if s.top_apps else "-",
                str(s.event_count),
            )
        
        console.print(table)
        
        total_hours = sum(s.total_active_hours for s in stats_list)
        avg_productivity = sum(s.productivity.score for s in stats_list) / len(stats_list) if stats_list else 0
        console.print(f"\n[bold]Total:[/bold] {total_hours:.1f}h | [bold]Avg Productivity:[/bold] {avg_productivity:.0f}%")
    else:
        date = datetime.now()
        if period == "yesterday":
            date = date - timedelta(days=1)
        
        s = calculator.calculate_daily_stats(date)
        
        console.print(Panel(
            f"[bold]Date:[/bold] {s.date.strftime('%A, %B %d, %Y')}\n"
            f"[bold]Active Time:[/bold] {s.total_active_hours:.1f} hours\n"
            f"[bold]Events:[/bold] {s.event_count} | [bold]Screenshots:[/bold] {s.screenshot_count}\n\n"
            f"[cyan]Productivity Score:[/cyan] {s.productivity.score:.0f}/100\n"
            f"  Productive: {s.productivity.productive_seconds/3600:.1f}h\n"
            f"  Neutral: {s.productivity.neutral_seconds/3600:.1f}h\n"
            f"  Distracting: {s.productivity.distracting_seconds/3600:.1f}h\n\n"
            f"[cyan]Peak Hours:[/cyan] {', '.join(f'{h}:00' for h in s.peak_hours) if s.peak_hours else 'N/A'}",
            title="📊 Daily Statistics",
        ))
        
        if s.app_usage:
            table = Table(title="App Usage")
            table.add_column("App", style="cyan")
            table.add_column("Time")
            table.add_column("Category")
            
            for app in sorted(s.app_usage, key=lambda x: x.total_seconds, reverse=True)[:10]:
                cat_color = "green" if app.category == "productive" else "red" if app.category == "distracting" else "white"
                table.add_row(
                    app.app_name[:30],
                    f"{app.total_minutes:.0f} min",
                    f"[{cat_color}]{app.category}[/{cat_color}]",
                )
            
            console.print(table)


@app.command()
def replay(
    session_id: str = typer.Argument(..., help="Session ID to replay"),
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
    speed: str = typer.Option("normal", "--speed", "-s", help="Speed: slow, normal, fast, instant"),
    no_confirm: bool = typer.Option(False, "--no-confirm", help="Skip action confirmations"),
    preview: bool = typer.Option(False, "--preview", "-p", help="Preview only, don't execute"),
):
    """Replay a recorded session."""
    from mnemosyne.store.database import Database
    from mnemosyne.replay import ActionReplayer, ReplayConfig, ReplaySpeed
    
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
    
    speed_map = {
        "slow": ReplaySpeed.SLOW,
        "normal": ReplaySpeed.NORMAL,
        "fast": ReplaySpeed.FAST,
        "instant": ReplaySpeed.INSTANT,
    }
    
    config = ReplayConfig(
        speed=speed_map.get(speed, ReplaySpeed.NORMAL),
        require_confirmation=not no_confirm,
    )
    
    replayer = ActionReplayer(
        database=db,
        config=config,
        on_action=lambda e, i, t: console.print(f"  [{i+1}/{t}] {e.action_type}"),
        on_complete=lambda s: console.print(f"\n[green]Replay completed![/green]"),
    )
    
    info = replayer.get_session_preview(session.id)
    
    console.print(Panel(
        f"[bold]Session:[/bold] {session.name or session.id[:8]}\n"
        f"[bold]Total Events:[/bold] {info['total_events']}\n"
        f"[bold]Replayable:[/bold] {info['replayable_events']}\n"
        f"[bold]Original Duration:[/bold] {info['original_duration_seconds']:.1f}s\n"
        f"[bold]Estimated Replay:[/bold] {info['estimated_replay_seconds']:.1f}s\n\n"
        f"[cyan]Actions:[/cyan]\n" + "\n".join(f"  • {k}: {v}" for k, v in info['action_breakdown'].items()),
        title="🎬 Replay Preview",
    ))
    
    if preview:
        return
    
    if not no_confirm:
        confirm = typer.confirm("Start replay?")
        if not confirm:
            return
    
    console.print("\n[yellow]Starting replay...[/yellow]\n")
    asyncio.run(replayer.replay_session(session.id))


@app.command()
def search(
    query: str = typer.Argument(..., help="Text to search for"),
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
    limit: int = typer.Option(10, "--limit", "-l", help="Max results"),
    index: bool = typer.Option(False, "--index", "-i", help="Re-index screenshots first"),
):
    """Search text in screenshots using OCR."""
    from mnemosyne.ocr import ScreenshotIndexer
    
    indexer = ScreenshotIndexer(data_dir=data_dir)
    
    if index:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Indexing screenshots...", total=None)
            count = indexer.index_all()
            progress.update(task, completed=True)
        console.print(f"[green]Indexed {count} screenshots[/green]\n")
    
    results = indexer.search(query, limit=limit)
    
    if not results:
        console.print(f"[yellow]No results found for '{query}'[/yellow]")
        console.print("[dim]Tip: Run with --index to index new screenshots[/dim]")
        return
    
    console.print(f"[green]Found {len(results)} results for '{query}':[/green]\n")
    
    for i, r in enumerate(results, 1):
        from datetime import datetime
        time_str = datetime.fromtimestamp(r.timestamp).strftime("%Y-%m-%d %H:%M") if r.timestamp else "Unknown"
        snippet = r.text[:100].replace("\n", " ")
        if query.lower() in snippet.lower():
            idx = snippet.lower().index(query.lower())
            snippet = snippet[:idx] + f"[bold yellow]{snippet[idx:idx+len(query)]}[/bold yellow]" + snippet[idx+len(query):]
        
        console.print(f"  {i}. [cyan]{time_str}[/cyan]")
        console.print(f"     {snippet}...")
        console.print(f"     [dim]{r.source_path}[/dim]\n")


@app.command()
def aggregate(
    session_id: str = typer.Argument(..., help="Session ID to aggregate"),
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
    mouse_window: float = typer.Option(500.0, "--mouse-window", help="Mouse aggregation window (ms)"),
    scroll_window: float = typer.Option(1000.0, "--scroll-window", help="Scroll aggregation window (ms)"),
    typing_window: float = typer.Option(2000.0, "--typing-window", help="Typing aggregation window (ms)"),
    idle_threshold: float = typer.Option(3.0, "--idle-threshold", help="Idle detection threshold (seconds)"),
    epsilon: float = typer.Option(5.0, "--epsilon", help="Douglas-Peucker epsilon for path simplification"),
    output: Path = typer.Option(None, "--output", "-o", help="Save result to JSON file"),
):
    """Aggregate events in a session to reduce noise."""
    from mnemosyne.store.database import Database
    from mnemosyne.aggregation import EventAggregator, AggregationConfig
    
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
    
    config = AggregationConfig(
        mouse_window_ms=mouse_window,
        scroll_window_ms=scroll_window,
        typing_window_ms=typing_window,
        idle_threshold_seconds=idle_threshold,
        douglas_peucker_epsilon=epsilon,
    )
    
    aggregator = EventAggregator(config=config)
    events = db.get_events(session.id)
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Aggregating events...", total=None)
        result = asyncio.run(aggregator.aggregate_session(events))
        progress.update(task, completed=True)
    
    console.print(Panel(
        f"[bold]Session:[/bold] {session.name or session.id[:8]}\n"
        f"[bold]Original Events:[/bold] {result.original_event_count}\n"
        f"[bold]Aggregated Events:[/bold] {result.aggregated_event_count}\n"
        f"[bold]Compression:[/bold] {result.compression_ratio:.1%}\n"
        f"[bold]Processing Time:[/bold] {result.processing_time_ms:.1f}ms\n\n"
        f"[cyan]Breakdown:[/cyan]\n"
        f"  Mouse trajectories: {len(result.mouse_trajectories)}\n"
        f"  Scroll sequences: {len(result.scroll_sequences)}\n"
        f"  Typing sequences: {len(result.typing_sequences)}\n"
        f"  Idle periods: {len(result.idle_periods)}",
        title="📊 Aggregation Result",
    ))
    
    if result.typing_sequences:
        console.print("\n[cyan]Typing Samples:[/cyan]")
        for i, ts in enumerate(result.typing_sequences[:3], 1):
            text_preview = ts.text[:50].replace("\n", "↵") + ("..." if len(ts.text) > 50 else "")
            console.print(f"  {i}. \"{text_preview}\" ({ts.wpm:.0f} WPM, {ts.char_count} chars)")
    
    if result.idle_periods:
        away_periods = [p for p in result.idle_periods if p.is_away]
        breaks = [p for p in result.idle_periods if p.is_break]
        pauses = [p for p in result.idle_periods if p.is_short_pause]
        console.print(f"\n[cyan]Idle Analysis:[/cyan] {len(pauses)} pauses, {len(breaks)} breaks, {len(away_periods)} away periods")
    
    if output:
        import json
        with open(output, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        console.print(f"\n[green]Result saved to {output}[/green]")


privacy_app = typer.Typer(help="Privacy scrubbing settings and controls")
app.add_typer(privacy_app, name="privacy")


@privacy_app.command("status")
def privacy_status(
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
):
    """Show current privacy scrubbing settings."""
    from mnemosyne.config import load_settings
    from mnemosyne.privacy import PrivacyScrubber, PrivacyConfig, ScrubLevel
    
    try:
        settings = load_settings()
        privacy_config = getattr(settings, "privacy", None)
        if privacy_config is None:
            privacy_config = PrivacyConfig()
    except Exception:
        privacy_config = PrivacyConfig()
    
    scrubber = PrivacyScrubber(config=privacy_config)
    stats = scrubber.get_statistics()
    
    status_color = "green" if stats["enabled"] else "red"
    status_text = "Enabled" if stats["enabled"] else "Disabled"
    
    console.print(Panel(
        f"[bold]Status:[/bold] [{status_color}]{status_text}[/{status_color}]\n"
        f"[bold]Level:[/bold] {stats['level']}\n"
        f"[bold]Pattern Count:[/bold] {stats['pattern_count']}\n\n"
        f"[cyan]Scrubbing Targets:[/cyan]\n"
        f"  Text: {'✓' if stats['scrub_text'] else '✗'}\n"
        f"  Images: {'✓' if stats['scrub_images'] else '✗'}\n"
        f"  Events: {'✓' if stats['scrub_events'] else '✗'}\n\n"
        f"[cyan]Allow List:[/cyan] {stats['allow_list_count']} entries\n"
        f"[cyan]Disabled Types:[/cyan] {', '.join(stats['disabled_types']) or 'None'}",
        title="🔒 Privacy Scrubbing Status",
    ))


@privacy_app.command("enable")
def privacy_enable(
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
):
    """Enable privacy scrubbing."""
    from mnemosyne.config import load_settings, save_settings
    from mnemosyne.privacy import PrivacyConfig
    
    config_path = data_dir / "config.toml"
    
    try:
        settings = load_settings(config_path)
    except Exception:
        from mnemosyne.config.settings import Settings
        settings = Settings()
    
    if not hasattr(settings, "privacy"):
        import toml
        
        if config_path.exists():
            with open(config_path) as f:
                data = toml.load(f)
        else:
            data = {}
        
        data["privacy"] = {"enabled": True}
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            toml.dump(data, f)
    else:
        settings.privacy.enabled = True
        save_settings(settings, config_path)
    
    console.print("[green]✓ Privacy scrubbing enabled[/green]")


@privacy_app.command("disable")
def privacy_disable(
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
):
    """Disable privacy scrubbing."""
    import toml
    
    config_path = data_dir / "config.toml"
    
    if config_path.exists():
        with open(config_path) as f:
            data = toml.load(f)
    else:
        data = {}
    
    if "privacy" not in data:
        data["privacy"] = {}
    
    data["privacy"]["enabled"] = False
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        toml.dump(data, f)
    
    console.print("[yellow]✗ Privacy scrubbing disabled[/yellow]")
    console.print("[dim]Warning: PII will not be masked in recordings[/dim]")


@privacy_app.command("level")
def privacy_level(
    level: str = typer.Argument(..., help="Scrubbing level: minimal, standard, aggressive"),
    data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data-dir", "-d"),
):
    """Set the privacy scrubbing level."""
    import toml
    from mnemosyne.privacy import ScrubLevel
    
    valid_levels = [l.value for l in ScrubLevel]
    if level not in valid_levels:
        console.print(f"[red]Invalid level: {level}[/red]")
        console.print(f"Valid levels: {', '.join(valid_levels)}")
        raise typer.Exit(1)
    
    config_path = data_dir / "config.toml"
    
    if config_path.exists():
        with open(config_path) as f:
            data = toml.load(f)
    else:
        data = {}
    
    if "privacy" not in data:
        data["privacy"] = {"enabled": True}
    
    data["privacy"]["level"] = level
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        toml.dump(data, f)
    
    level_descriptions = {
        "minimal": "Only high-risk PII (SSN, credit cards, API keys, passwords)",
        "standard": "Common PII types with high confidence",
        "aggressive": "All detectable PII including addresses and dates",
    }
    
    console.print(f"[green]✓ Privacy level set to: {level}[/green]")
    console.print(f"[dim]{level_descriptions[level]}[/dim]")


@privacy_app.command("test")
def privacy_test(
    text: str = typer.Argument(..., help="Text to test for PII detection"),
):
    """Test PII detection on sample text."""
    import asyncio
    from mnemosyne.privacy import PrivacyScrubber, PrivacyConfig, ScrubLevel
    
    scrubber = PrivacyScrubber(config=PrivacyConfig(level=ScrubLevel.AGGRESSIVE))
    
    scrubbed, result = asyncio.run(scrubber.scrub_text(text))
    
    console.print(Panel(
        f"[bold]Original:[/bold]\n{text}\n\n"
        f"[bold]Scrubbed:[/bold]\n{scrubbed}",
        title="🔍 PII Detection Test",
    ))
    
    if result.pii_found:
        console.print(f"\n[cyan]PII Found ({result.pii_count}):[/cyan]")
        for pii_type, value in result.pii_found:
            masked_value = value[:3] + "..." + value[-3:] if len(value) > 8 else "***"
            console.print(f"  • {pii_type.value}: {masked_value}")
    else:
        console.print("\n[green]No PII detected[/green]")


@privacy_app.command("scrub-file")
def privacy_scrub_file(
    file_path: Path = typer.Argument(..., help="File to scrub (text or image)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output path"),
    level: str = typer.Option("standard", "--level", "-l", help="Scrubbing level"),
):
    """Scrub PII from a file."""
    import asyncio
    from mnemosyne.privacy import PrivacyScrubber, PrivacyConfig, ScrubLevel
    
    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)
    
    try:
        scrub_level = ScrubLevel(level)
    except ValueError:
        console.print(f"[red]Invalid level: {level}[/red]")
        raise typer.Exit(1)
    
    scrubber = PrivacyScrubber(config=PrivacyConfig(level=scrub_level))
    
    image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
    
    if file_path.suffix.lower() in image_extensions:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Scrubbing image...", total=None)
            result = asyncio.run(scrubber.scrub_image(file_path))
            progress.update(task, completed=True)
        
        console.print(f"[green]✓ Image scrubbed[/green]")
        console.print(f"  Regions blurred: {result.regions_blurred}")
        console.print(f"  Output: {result.scrubbed_path}")
        
        if result.pii_types_found:
            console.print(f"  PII types: {', '.join(t.value for t in result.pii_types_found)}")
    else:
        with open(file_path) as f:
            text = f.read()
        
        scrubbed, result = asyncio.run(scrubber.scrub_text(text))
        
        output_path = output or file_path.with_suffix(f".scrubbed{file_path.suffix}")
        with open(output_path, "w") as f:
            f.write(scrubbed)
        
        console.print(f"[green]✓ Text file scrubbed[/green]")
        console.print(f"  PII instances found: {result.pii_count}")
        console.print(f"  Output: {output_path}")


@app.command()
def ground(
    image_path: Path = typer.Argument(..., help="Path to screenshot image"),
    output: Path = typer.Option(None, "--output", "-o", help="Output path for annotated image"),
    show_bounds: bool = typer.Option(False, "--bounds", "-b", help="Show bounding boxes"),
    prompt: bool = typer.Option(False, "--prompt", "-p", help="Generate Set-of-Mark prompt"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output elements as JSON"),
):
    """Detect and annotate UI elements in a screenshot (Set-of-Mark style)."""
    import asyncio
    import json
    from mnemosyne.grounding import VisualGrounder, AnnotationStyle
    
    if not image_path.exists():
        console.print(f"[red]Image not found: {image_path}[/red]")
        raise typer.Exit(1)
    
    style = AnnotationStyle(show_bounds=show_bounds)
    grounder = VisualGrounder(annotation_style=style)
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Detecting UI elements...", total=None)
        result = asyncio.run(grounder.ground_image(image_path, output))
        progress.update(task, completed=True)
    
    if json_output:
        elements_data = [
            {
                "id": e.id,
                "type": e.element_type.value,
                "x": e.bounds.x,
                "y": e.bounds.y,
                "width": e.bounds.width,
                "height": e.bounds.height,
                "center": e.center,
                "confidence": e.confidence,
                "interactive": e.is_interactive,
            }
            for e in result.elements
        ]
        console.print(json.dumps(elements_data, indent=2))
        return
    
    if prompt:
        som_prompt = asyncio.run(grounder.generate_som_prompt(image_path, result.elements))
        console.print(Panel(som_prompt, title="Set-of-Mark Prompt"))
        return
    
    interactive = [e for e in result.elements if e.is_interactive]
    non_interactive = [e for e in result.elements if not e.is_interactive]
    
    console.print(Panel(
        f"[bold]Source:[/bold] {result.source_path}\n"
        f"[bold]Size:[/bold] {result.image_width}x{result.image_height}\n"
        f"[bold]Elements:[/bold] {result.element_count} ({len(interactive)} interactive)\n"
        f"[bold]Processing:[/bold] {result.processing_time_ms:.1f}ms\n"
        f"[bold]Output:[/bold] {result.annotated_path}",
        title="🎯 Visual Grounding Result",
    ))
    
    if interactive:
        table = Table(title="Interactive Elements")
        table.add_column("ID", style="cyan")
        table.add_column("Type")
        table.add_column("Position")
        table.add_column("Size")
        table.add_column("Confidence")
        
        for e in interactive:
            cx, cy = e.center
            conf_color = "green" if e.confidence >= 0.7 else "yellow" if e.confidence >= 0.5 else "red"
            table.add_row(
                str(e.id),
                e.element_type.value,
                f"({cx}, {cy})",
                f"{e.bounds.width}x{e.bounds.height}",
                f"[{conf_color}]{e.confidence:.0%}[/{conf_color}]",
            )
        
        console.print(table)
    
    console.print(f"\n[dim]Annotated image saved to: {result.annotated_path}[/dim]")


if __name__ == "__main__":
    app()
