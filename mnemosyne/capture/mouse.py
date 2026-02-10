"""Mouse input capture using pynput."""

import time
from typing import Callable
from threading import Thread

from pynput import mouse
from pynput.mouse import Button

from mnemosyne.capture.events import (
    MouseMoveEvent,
    MouseClickEvent,
    MouseScrollEvent,
)


class MouseCapture:
    """Captures mouse events."""
    
    def __init__(
        self,
        on_event: Callable,
        move_throttle_ms: int = 50,
    ):
        """
        Initialize mouse capture.
        
        Args:
            on_event: Callback function for mouse events
            move_throttle_ms: Minimum milliseconds between move events
        """
        self.on_event = on_event
        self.move_throttle_ms = move_throttle_ms
        self._last_move_time = 0.0
        self._listener: mouse.Listener | None = None
        self._running = False
        
        # Track for double-click detection
        self._last_click_time = 0.0
        self._last_click_button: str | None = None
        self._last_click_pos: tuple[int, int] = (0, 0)
        self._double_click_threshold_ms = 500
    
    def start(self) -> None:
        """Start capturing mouse events."""
        if self._running:
            return
        
        self._running = True
        self._listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._listener.start()
    
    def stop(self) -> None:
        """Stop capturing mouse events."""
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
    
    def _on_move(self, x: int, y: int) -> None:
        """Handle mouse move events with throttling."""
        if not self._running:
            return
        
        current_time = time.time()
        elapsed_ms = (current_time - self._last_move_time) * 1000
        
        if elapsed_ms < self.move_throttle_ms:
            return
        
        self._last_move_time = current_time
        
        event = MouseMoveEvent(
            timestamp=current_time,
            x=int(x),
            y=int(y),
        )
        self.on_event(event)
    
    def _on_click(self, x: int, y: int, button: Button, pressed: bool) -> None:
        """Handle mouse click events."""
        if not self._running:
            return
        
        current_time = time.time()
        button_name = self._button_to_str(button)
        
        # Detect double-click
        click_count = 1
        if pressed:
            elapsed_ms = (current_time - self._last_click_time) * 1000
            same_button = button_name == self._last_click_button
            near_position = (
                abs(x - self._last_click_pos[0]) < 5 and
                abs(y - self._last_click_pos[1]) < 5
            )
            
            if (
                elapsed_ms < self._double_click_threshold_ms
                and same_button
                and near_position
            ):
                click_count = 2
            
            self._last_click_time = current_time
            self._last_click_button = button_name
            self._last_click_pos = (x, y)
        
        event = MouseClickEvent(
            timestamp=current_time,
            x=int(x),
            y=int(y),
            button=button_name,
            pressed=pressed,
            click_count=click_count,
        )
        self.on_event(event)
    
    def _on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """Handle mouse scroll events."""
        if not self._running:
            return
        
        event = MouseScrollEvent(
            timestamp=time.time(),
            x=int(x),
            y=int(y),
            dx=int(dx),
            dy=int(dy),
        )
        self.on_event(event)
    
    @staticmethod
    def _button_to_str(button: Button) -> str:
        """Convert pynput Button to string."""
        if button == Button.left:
            return "left"
        elif button == Button.right:
            return "right"
        elif button == Button.middle:
            return "middle"
        return "unknown"
