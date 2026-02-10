"""Window information capture for macOS."""

import time
from dataclasses import dataclass
from typing import Callable

from mnemosyne.capture.events import WindowChangeEvent


@dataclass
class WindowInfo:
    """Information about the active window."""
    app_name: str
    window_title: str
    bundle_id: str
    bounds: tuple[int, int, int, int]  # x, y, width, height
    pid: int


class WindowCapture:
    """Captures active window information on macOS."""
    
    def __init__(
        self,
        on_event: Callable | None = None,
        poll_interval_ms: int = 100,
    ):
        """
        Initialize window capture.
        
        Args:
            on_event: Callback function for window change events
            poll_interval_ms: Interval between window polls
        """
        self.on_event = on_event
        self.poll_interval_ms = poll_interval_ms
        self._last_window: WindowInfo | None = None
        self._running = False
        self._poll_thread = None
    
    def get_active_window(self) -> WindowInfo | None:
        """
        Get information about the currently active window.
        
        Returns:
            WindowInfo or None if not available
        """
        try:
            return self._get_window_macos()
        except ImportError:
            return self._get_window_fallback()
    
    def _get_window_macos(self) -> WindowInfo | None:
        """Get active window using macOS APIs."""
        from AppKit import NSWorkspace
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGWindowListOptionOnScreenOnly,
            kCGWindowListExcludeDesktopElements,
            kCGNullWindowID,
        )
        
        # Get active application
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()
        
        if active_app is None:
            return None
        
        app_name = active_app.localizedName() or "Unknown"
        bundle_id = active_app.bundleIdentifier() or ""
        pid = active_app.processIdentifier()
        
        # Get window list to find the active window's bounds and title
        window_list = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
            kCGNullWindowID
        )
        
        window_title = ""
        bounds = (0, 0, 0, 0)
        
        if window_list:
            for window in window_list:
                owner_pid = window.get("kCGWindowOwnerPID", 0)
                if owner_pid == pid:
                    window_title = window.get("kCGWindowName", "") or ""
                    window_bounds = window.get("kCGWindowBounds", {})
                    if window_bounds:
                        bounds = (
                            int(window_bounds.get("X", 0)),
                            int(window_bounds.get("Y", 0)),
                            int(window_bounds.get("Width", 0)),
                            int(window_bounds.get("Height", 0)),
                        )
                    break
        
        return WindowInfo(
            app_name=app_name,
            window_title=window_title,
            bundle_id=bundle_id,
            bounds=bounds,
            pid=pid,
        )
    
    def _get_window_fallback(self) -> WindowInfo | None:
        """Fallback for non-macOS systems."""
        # Basic fallback - returns minimal info
        return WindowInfo(
            app_name="Unknown",
            window_title="Unknown",
            bundle_id="",
            bounds=(0, 0, 0, 0),
            pid=0,
        )
    
    def start(self) -> None:
        """Start polling for window changes."""
        if self._running:
            return
        
        import threading
        
        self._running = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
    
    def stop(self) -> None:
        """Stop polling for window changes."""
        self._running = False
        if self._poll_thread:
            self._poll_thread.join(timeout=1.0)
            self._poll_thread = None
    
    def _poll_loop(self) -> None:
        """Poll for window changes."""
        while self._running:
            try:
                current_window = self.get_active_window()
                
                if current_window and self._has_window_changed(current_window):
                    self._last_window = current_window
                    
                    if self.on_event:
                        event = WindowChangeEvent(
                            timestamp=time.time(),
                            app_name=current_window.app_name,
                            window_title=current_window.window_title,
                            bundle_id=current_window.bundle_id,
                            bounds=current_window.bounds,
                        )
                        self.on_event(event)
            except Exception:
                pass  # Ignore errors in polling
            
            time.sleep(self.poll_interval_ms / 1000.0)
    
    def _has_window_changed(self, current: WindowInfo) -> bool:
        """Check if the window has changed."""
        if self._last_window is None:
            return True
        
        return (
            current.app_name != self._last_window.app_name
            or current.window_title != self._last_window.window_title
            or current.pid != self._last_window.pid
        )
