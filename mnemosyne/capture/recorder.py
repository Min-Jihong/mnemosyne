"""Main recorder that orchestrates all capture components."""

import asyncio
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable
from threading import Lock
from queue import Queue

from mnemosyne.capture.mouse import MouseCapture
from mnemosyne.capture.keyboard import KeyboardCapture
from mnemosyne.capture.screen import ScreenCapture
from mnemosyne.capture.window import WindowCapture, WindowInfo
from mnemosyne.capture.events import (
    BaseEvent,
    Event,
    ScreenshotEvent,
    WindowChangeEvent,
    MouseClickEvent,
    ActionType,
)


@dataclass
class RecordingSession:
    """Represents a recording session."""
    id: str
    start_time: float
    end_time: float | None = None
    event_count: int = 0
    screenshot_count: int = 0
    
    @property
    def duration_seconds(self) -> float:
        """Get session duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time


@dataclass
class RecorderConfig:
    """Configuration for the recorder."""
    # Mouse settings
    mouse_move_throttle_ms: int = 50
    
    # Keyboard settings
    aggregate_typing: bool = True
    typing_timeout_ms: float = 500
    
    # Screenshot settings
    screenshot_quality: int = 80
    screenshot_format: str = "webp"
    screenshot_on_click: bool = True
    screenshot_on_window_change: bool = True
    screenshot_interval_ms: int = 0  # 0 = disabled, >0 = periodic
    
    # Window settings
    window_poll_interval_ms: int = 100
    
    # Output settings
    output_dir: Path = field(default_factory=lambda: Path("data"))


class Recorder:
    """
    Main recorder that orchestrates mouse, keyboard, screen, and window capture.
    
    This is the heart of Mnemosyne - it captures every micro-action
    the user performs on their computer.
    """
    
    def __init__(
        self,
        config: RecorderConfig | None = None,
        on_event: Callable[[Event], None] | None = None,
    ):
        """
        Initialize the recorder.
        
        Args:
            config: Recorder configuration
            on_event: Callback for each captured event
        """
        self.config = config or RecorderConfig()
        self.on_event = on_event
        
        # Ensure output directories exist
        self._screenshots_dir = self.config.output_dir / "screenshots"
        self._screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Event queue for processing
        self._event_queue: Queue[Event] = Queue()
        self._lock = Lock()
        
        # Session tracking
        self._session: RecordingSession | None = None
        self._running = False
        
        # Current window context (attached to events)
        self._current_window: WindowInfo | None = None
        
        # Initialize capture components
        self._mouse = MouseCapture(
            on_event=self._handle_event,
            move_throttle_ms=self.config.mouse_move_throttle_ms,
        )
        
        self._keyboard = KeyboardCapture(
            on_event=self._handle_event,
            aggregate_typing=self.config.aggregate_typing,
            typing_timeout_ms=self.config.typing_timeout_ms,
        )
        
        self._screen = ScreenCapture(
            output_dir=self._screenshots_dir,
            quality=self.config.screenshot_quality,
            format=self.config.screenshot_format,
        )
        
        self._window = WindowCapture(
            on_event=self._handle_window_event,
            poll_interval_ms=self.config.window_poll_interval_ms,
        )
        
        # Periodic screenshot task
        self._screenshot_task: asyncio.Task | None = None
    
    def start(self, session_id: str | None = None) -> RecordingSession:
        """
        Start recording.
        
        Args:
            session_id: Optional session ID (auto-generated if not provided)
            
        Returns:
            The recording session
        """
        if self._running:
            raise RuntimeError("Recorder is already running")
        
        import uuid
        
        # Create session
        self._session = RecordingSession(
            id=session_id or str(uuid.uuid4()),
            start_time=time.time(),
        )
        
        self._running = True
        
        # Start all capture components
        self._mouse.start()
        self._keyboard.start()
        self._window.start()
        
        # Get initial window
        self._current_window = self._window.get_active_window()
        
        # Take initial screenshot
        self._capture_screenshot()
        
        return self._session
    
    def stop(self) -> RecordingSession | None:
        """
        Stop recording.
        
        Returns:
            The completed recording session
        """
        if not self._running:
            return None
        
        self._running = False
        
        # Stop all capture components
        self._mouse.stop()
        self._keyboard.stop()
        self._window.stop()
        
        # Cancel periodic screenshot task
        if self._screenshot_task:
            self._screenshot_task.cancel()
            self._screenshot_task = None
        
        # Finalize session
        if self._session:
            self._session.end_time = time.time()
        
        return self._session
    
    def _handle_event(self, event: Event) -> None:
        """Handle an incoming event from any capture component."""
        if not self._running:
            return
        
        with self._lock:
            # Update session stats
            if self._session:
                self._session.event_count += 1
            
            # Check if we should capture a screenshot
            if self.config.screenshot_on_click:
                if isinstance(event, MouseClickEvent) and event.pressed:
                    self._capture_screenshot()
            
            # Add to queue and call callback
            self._event_queue.put(event)
            
            if self.on_event:
                self.on_event(event)
    
    def _handle_window_event(self, event: WindowChangeEvent) -> None:
        """Handle window change events."""
        if not self._running:
            return
        
        # Update current window context
        self._current_window = WindowInfo(
            app_name=event.app_name,
            window_title=event.window_title,
            bundle_id=event.bundle_id,
            bounds=event.bounds,
            pid=0,
        )
        
        # Capture screenshot on window change
        if self.config.screenshot_on_window_change:
            self._capture_screenshot()
        
        # Handle as regular event
        self._handle_event(event)
    
    def _capture_screenshot(self) -> ScreenshotEvent | None:
        """Capture a screenshot and create an event."""
        try:
            filepath, width, height, file_size = self._screen.capture_to_file()
            
            event = ScreenshotEvent(
                timestamp=time.time(),
                filepath=str(filepath),
                width=width,
                height=height,
                file_size=file_size,
            )
            
            with self._lock:
                if self._session:
                    self._session.screenshot_count += 1
            
            if self.on_event:
                self.on_event(event)
            
            return event
        except Exception as e:
            # Log error but don't crash
            print(f"Screenshot capture failed: {e}")
            return None
    
    async def start_async(self, session_id: str | None = None) -> RecordingSession:
        """
        Start recording asynchronously.
        
        Args:
            session_id: Optional session ID
            
        Returns:
            The recording session
        """
        session = self.start(session_id)
        
        # Start periodic screenshot task if configured
        if self.config.screenshot_interval_ms > 0:
            self._screenshot_task = asyncio.create_task(
                self._periodic_screenshot_loop()
            )
        
        return session
    
    async def _periodic_screenshot_loop(self) -> None:
        """Periodically capture screenshots."""
        interval = self.config.screenshot_interval_ms / 1000.0
        
        while self._running:
            await asyncio.sleep(interval)
            if self._running:
                self._capture_screenshot()
    
    def get_current_window(self) -> WindowInfo | None:
        """Get the current active window information."""
        return self._current_window
    
    def get_session(self) -> RecordingSession | None:
        """Get the current recording session."""
        return self._session
    
    def get_event_count(self) -> int:
        """Get the number of events captured."""
        return self._session.event_count if self._session else 0
    
    def get_screenshot_count(self) -> int:
        """Get the number of screenshots captured."""
        return self._session.screenshot_count if self._session else 0
