"""Main TUI application."""

from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import (
        Button,
        DataTable,
        Footer,
        Header,
        Input,
        Label,
        ListItem,
        ListView,
        ProgressBar,
        RichLog,
        Static,
        Tab,
        TabbedContent,
        TabPane,
    )
    from textual.reactive import reactive
    from textual import work

    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


if TEXTUAL_AVAILABLE:

    class StatusBar(Static):
        """Status bar showing current state."""

        recording = reactive(False)
        session_name = reactive("")
        event_count = reactive(0)

        def compose(self) -> ComposeResult:
            yield Static("", id="status-text")

        def watch_recording(self, recording: bool) -> None:
            self._update_status()

        def watch_session_name(self, name: str) -> None:
            self._update_status()

        def watch_event_count(self, count: int) -> None:
            self._update_status()

        def _update_status(self) -> None:
            status = self.query_one("#status-text", Static)
            if self.recording:
                text = f"[bold red]● RECORDING[/] | Session: {self.session_name} | Events: {self.event_count}"
            else:
                text = "[dim]○ Idle[/] | Press [bold]r[/] to start recording"
            status.update(text)

    class EventLog(RichLog):
        """Real-time event log display."""

        def add_event(self, event: dict[str, Any]) -> None:
            """Add an event to the log."""
            timestamp = datetime.now().strftime("%H:%M:%S")
            event_type = event.get("type", "unknown")
            
            # Color-code by event type
            if "mouse" in event_type.lower():
                color = "blue"
            elif "key" in event_type.lower():
                color = "green"
            elif "window" in event_type.lower():
                color = "yellow"
            else:
                color = "white"

            self.write(f"[dim]{timestamp}[/] [{color}]{event_type}[/]")

    class SessionsList(DataTable):
        """Sessions list with details."""

        def on_mount(self) -> None:
            self.add_columns("ID", "Name", "Date", "Events", "Duration")
            self.cursor_type = "row"

        def load_sessions(self, sessions: list[dict[str, Any]]) -> None:
            """Load sessions into the table."""
            self.clear()
            for session in sessions:
                self.add_row(
                    session.get("id", "")[:8],
                    session.get("name", "Unnamed"),
                    session.get("created_at", "")[:10],
                    str(session.get("event_count", 0)),
                    session.get("duration", "0:00"),
                )

    class MemorySearch(Container):
        """Memory search interface."""

        def compose(self) -> ComposeResult:
            yield Input(placeholder="Search memories...", id="memory-search")
            yield ScrollableContainer(
                RichLog(id="memory-results", highlight=True, markup=True),
            )

    class ChatInterface(Container):
        """Chat interface with the digital twin."""

        def compose(self) -> ComposeResult:
            yield ScrollableContainer(
                RichLog(id="chat-log", highlight=True, markup=True),
                id="chat-container",
            )
            yield Horizontal(
                Input(placeholder="Ask your digital twin...", id="chat-input"),
                Button("Send", id="send-btn", variant="primary"),
                id="chat-controls",
            )

    class MnemosyneApp(App):
        """
        Mnemosyne Terminal User Interface.

        A professional TUI for managing your digital twin.
        """

        TITLE = "Mnemosyne"
        SUB_TITLE = "Your Digital Twin"
        CSS = """
        Screen {
            background: $surface;
        }

        #main-container {
            height: 100%;
        }

        StatusBar {
            height: 3;
            background: $panel;
            padding: 1;
            border-bottom: solid $primary;
        }

        #status-text {
            text-align: center;
        }

        TabbedContent {
            height: 1fr;
        }

        TabPane {
            padding: 1;
        }

        EventLog {
            height: 100%;
            border: solid $primary;
            background: $surface-darken-1;
        }

        SessionsList {
            height: 100%;
        }

        MemorySearch {
            height: 100%;
        }

        #memory-search {
            margin-bottom: 1;
        }

        #memory-results {
            height: 1fr;
            border: solid $primary;
        }

        ChatInterface {
            height: 100%;
        }

        #chat-container {
            height: 1fr;
            border: solid $primary;
            margin-bottom: 1;
        }

        #chat-log {
            height: 100%;
        }

        #chat-controls {
            height: 3;
        }

        #chat-input {
            width: 1fr;
            margin-right: 1;
        }

        .recording {
            background: $error 20%;
        }
        """

        BINDINGS = [
            Binding("q", "quit", "Quit"),
            Binding("r", "toggle_recording", "Record"),
            Binding("m", "show_memory", "Memory"),
            Binding("s", "show_sessions", "Sessions"),
            Binding("c", "show_chat", "Chat"),
            Binding("e", "show_events", "Events"),
            Binding("?", "show_help", "Help"),
            Binding("escape", "cancel", "Cancel"),
        ]

        # Reactive state
        recording = reactive(False)
        current_session: str | None = None

        def compose(self) -> ComposeResult:
            yield Header()
            yield Container(
                StatusBar(id="status-bar"),
                TabbedContent(
                    TabPane("Events", EventLog(id="event-log"), id="events-tab"),
                    TabPane("Sessions", SessionsList(id="sessions-list"), id="sessions-tab"),
                    TabPane("Memory", MemorySearch(id="memory-search"), id="memory-tab"),
                    TabPane("Chat", ChatInterface(id="chat-interface"), id="chat-tab"),
                    id="tabs",
                ),
                id="main-container",
            )
            yield Footer()

        def on_mount(self) -> None:
            """Initialize the app."""
            self.title = "Mnemosyne"
            self.sub_title = "Your Digital Twin"
            self._load_sessions()

        async def action_toggle_recording(self) -> None:
            """Toggle recording state."""
            self.recording = not self.recording
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.recording = self.recording

            if self.recording:
                status_bar.session_name = f"Session_{datetime.now().strftime('%H%M%S')}"
                self.notify("Recording started", severity="information")
                self._add_event_log("[bold green]Recording started[/]")
            else:
                self.notify("Recording stopped", severity="information")
                self._add_event_log("[bold red]Recording stopped[/]")

        def action_show_events(self) -> None:
            """Switch to events tab."""
            tabs = self.query_one("#tabs", TabbedContent)
            tabs.active = "events-tab"

        def action_show_sessions(self) -> None:
            """Switch to sessions tab."""
            tabs = self.query_one("#tabs", TabbedContent)
            tabs.active = "sessions-tab"

        def action_show_memory(self) -> None:
            """Switch to memory tab."""
            tabs = self.query_one("#tabs", TabbedContent)
            tabs.active = "memory-tab"

        def action_show_chat(self) -> None:
            """Switch to chat tab."""
            tabs = self.query_one("#tabs", TabbedContent)
            tabs.active = "chat-tab"

        def action_show_help(self) -> None:
            """Show help dialog."""
            help_text = """
[bold]Mnemosyne TUI Help[/]

[bold]Keyboard Shortcuts:[/]
  [dim]r[/]  Toggle recording
  [dim]e[/]  Events tab
  [dim]s[/]  Sessions tab
  [dim]m[/]  Memory tab
  [dim]c[/]  Chat tab
  [dim]q[/]  Quit

[bold]Recording:[/]
  Press 'r' to start/stop recording your
  computer activity. Events are captured
  in real-time.

[bold]Memory:[/]
  Search your memories semantically.
  Find patterns and insights from past
  sessions.

[bold]Chat:[/]
  Ask your digital twin questions about
  your behavior and preferences.
"""
            self.notify(help_text, title="Help", severity="information", timeout=10)

        def action_cancel(self) -> None:
            """Cancel current action."""
            # Focus on main content
            pass

        def _add_event_log(self, message: str) -> None:
            """Add a message to the event log."""
            try:
                event_log = self.query_one("#event-log", EventLog)
                event_log.write(message)
            except Exception:
                pass

        def _load_sessions(self) -> None:
            """Load sessions into the sessions list."""
            # Mock data for now
            sessions = [
                {
                    "id": "abc12345",
                    "name": "Work Session",
                    "created_at": "2024-01-15",
                    "event_count": 1234,
                    "duration": "2:30:15",
                },
                {
                    "id": "def67890",
                    "name": "Coding",
                    "created_at": "2024-01-14",
                    "event_count": 567,
                    "duration": "1:15:30",
                },
            ]
            try:
                sessions_list = self.query_one("#sessions-list", SessionsList)
                sessions_list.load_sessions(sessions)
            except Exception:
                pass

        async def on_input_submitted(self, event: Input.Submitted) -> None:
            """Handle input submission."""
            if event.input.id == "chat-input":
                await self._send_chat(event.value)
                event.input.clear()
            elif event.input.id == "memory-search":
                await self._search_memory(event.value)

        async def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button presses."""
            if event.button.id == "send-btn":
                chat_input = self.query_one("#chat-input", Input)
                await self._send_chat(chat_input.value)
                chat_input.clear()

        async def _send_chat(self, message: str) -> None:
            """Send a chat message."""
            if not message.strip():
                return

            chat_log = self.query_one("#chat-log", RichLog)
            chat_log.write(f"[bold blue]You:[/] {message}")

            # Simulate AI response (in real implementation, call LLM)
            chat_log.write("[dim]Thinking...[/]")

            # Placeholder response
            response = "I'm your digital twin. I'm learning to think like you!"
            chat_log.write(f"[bold green]Mnemosyne:[/] {response}")

        async def _search_memory(self, query: str) -> None:
            """Search memories."""
            if not query.strip():
                return

            results_log = self.query_one("#memory-results", RichLog)
            results_log.clear()
            results_log.write(f"[bold]Searching for:[/] {query}")
            results_log.write("")

            # Placeholder results
            results_log.write("[bold]Results:[/]")
            results_log.write("  [dim]No memories found yet. Start recording![/]")


    def run_tui() -> None:
        """Run the TUI application."""
        if not TEXTUAL_AVAILABLE:
            print("Error: Textual is not installed.")
            print("Install with: pip install textual")
            return

        app = MnemosyneApp()
        app.run()

else:
    # Stub class when Textual is not available
    class MnemosyneApp:
        """Stub class when Textual is not available."""

        def __init__(self) -> None:
            raise ImportError(
                "Textual is not installed. Install with: pip install textual"
            )

        def run(self) -> None:
            pass

    def run_tui() -> None:
        """Run the TUI application."""
        print("Error: Textual is not installed.")
        print("Install with: pip install textual")
