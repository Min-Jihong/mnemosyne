"""Keyboard input capture using pynput."""

import time
from typing import Callable
from threading import Lock

from pynput import keyboard
from pynput.keyboard import Key, KeyCode

from mnemosyne.capture.events import (
    KeyPressEvent,
    KeyReleaseEvent,
    KeyTypeEvent,
    HotkeyEvent,
    ActionType,
)


# Modifier keys that we track
MODIFIER_KEYS = {
    Key.shift, Key.shift_l, Key.shift_r,
    Key.ctrl, Key.ctrl_l, Key.ctrl_r,
    Key.alt, Key.alt_l, Key.alt_r,
    Key.cmd, Key.cmd_l, Key.cmd_r,
}

# Map pynput keys to readable names
KEY_NAMES = {
    Key.space: "space",
    Key.enter: "enter",
    Key.tab: "tab",
    Key.backspace: "backspace",
    Key.delete: "delete",
    Key.esc: "esc",
    Key.up: "up",
    Key.down: "down",
    Key.left: "left",
    Key.right: "right",
    Key.home: "home",
    Key.end: "end",
    Key.page_up: "page_up",
    Key.page_down: "page_down",
    Key.caps_lock: "caps_lock",
    Key.f1: "f1", Key.f2: "f2", Key.f3: "f3", Key.f4: "f4",
    Key.f5: "f5", Key.f6: "f6", Key.f7: "f7", Key.f8: "f8",
    Key.f9: "f9", Key.f10: "f10", Key.f11: "f11", Key.f12: "f12",
    Key.shift: "shift", Key.shift_l: "shift", Key.shift_r: "shift",
    Key.ctrl: "ctrl", Key.ctrl_l: "ctrl", Key.ctrl_r: "ctrl",
    Key.alt: "alt", Key.alt_l: "alt", Key.alt_r: "alt",
    Key.cmd: "cmd", Key.cmd_l: "cmd", Key.cmd_r: "cmd",
}


class KeyboardCapture:
    """Captures keyboard events."""
    
    def __init__(
        self,
        on_event: Callable,
        aggregate_typing: bool = True,
        typing_timeout_ms: float = 500,
    ):
        """
        Initialize keyboard capture.
        
        Args:
            on_event: Callback function for keyboard events
            aggregate_typing: Whether to aggregate sequential key presses into typing events
            typing_timeout_ms: Timeout for aggregating typing
        """
        self.on_event = on_event
        self.aggregate_typing = aggregate_typing
        self.typing_timeout_ms = typing_timeout_ms
        
        self._listener: keyboard.Listener | None = None
        self._running = False
        
        # Track active modifiers
        self._active_modifiers: set[str] = set()
        self._modifier_lock = Lock()
        
        # Typing aggregation
        self._typing_buffer = ""
        self._typing_start_time = 0.0
        self._last_key_time = 0.0
        self._typing_lock = Lock()
    
    def start(self) -> None:
        """Start capturing keyboard events."""
        if self._running:
            return
        
        self._running = True
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()
    
    def stop(self) -> None:
        """Stop capturing keyboard events."""
        self._running = False
        
        # Flush any pending typing
        self._flush_typing_buffer()
        
        if self._listener:
            self._listener.stop()
            self._listener = None
    
    def _on_press(self, key: Key | KeyCode | None) -> None:
        """Handle key press events."""
        if not self._running or key is None:
            return
        
        current_time = time.time()
        key_name, key_char, key_code = self._parse_key(key)
        
        # Update modifier state
        if key in MODIFIER_KEYS:
            with self._modifier_lock:
                self._active_modifiers.add(key_name)
        
        # Get current modifiers
        with self._modifier_lock:
            modifiers = list(self._active_modifiers)
        
        # Check for hotkey (modifier + key)
        if modifiers and key not in MODIFIER_KEYS:
            hotkey_event = HotkeyEvent(
                timestamp=current_time,
                keys=modifiers + [key_name],
            )
            self.on_event(hotkey_event)
        
        # Create press event
        event = KeyPressEvent(
            timestamp=current_time,
            key=key_name,
            key_char=key_char,
            key_code=key_code,
            modifiers=modifiers,
        )
        self.on_event(event)
        
        # Handle typing aggregation
        if self.aggregate_typing and key_char and not modifiers:
            self._add_to_typing_buffer(key_char, current_time)
    
    def _on_release(self, key: Key | KeyCode | None) -> None:
        """Handle key release events."""
        if not self._running or key is None:
            return
        
        current_time = time.time()
        key_name, key_char, key_code = self._parse_key(key)
        
        # Update modifier state
        if key in MODIFIER_KEYS:
            with self._modifier_lock:
                self._active_modifiers.discard(key_name)
        
        event = KeyReleaseEvent(
            timestamp=current_time,
            key=key_name,
            key_char=key_char,
            key_code=key_code,
        )
        self.on_event(event)
    
    def _parse_key(self, key: Key | KeyCode) -> tuple[str, str | None, int | None]:
        """
        Parse a pynput key into name, char, and code.
        
        Returns:
            Tuple of (key_name, key_char, key_code)
        """
        if isinstance(key, Key):
            key_name = KEY_NAMES.get(key, str(key).replace("Key.", ""))
            return key_name, None, None
        elif isinstance(key, KeyCode):
            key_char = key.char
            key_code = key.vk if hasattr(key, 'vk') else None
            key_name = key_char if key_char else f"vk_{key_code}"
            return key_name, key_char, key_code
        
        return "unknown", None, None
    
    def _add_to_typing_buffer(self, char: str, current_time: float) -> None:
        """Add character to typing buffer, flushing if timeout exceeded."""
        with self._typing_lock:
            elapsed_ms = (current_time - self._last_key_time) * 1000
            
            # Flush buffer if timeout exceeded
            if self._typing_buffer and elapsed_ms > self.typing_timeout_ms:
                self._flush_typing_buffer_locked()
            
            # Start new buffer if empty
            if not self._typing_buffer:
                self._typing_start_time = current_time
            
            self._typing_buffer += char
            self._last_key_time = current_time
    
    def _flush_typing_buffer(self) -> None:
        """Flush the typing buffer (thread-safe)."""
        with self._typing_lock:
            self._flush_typing_buffer_locked()
    
    def _flush_typing_buffer_locked(self) -> None:
        """Flush the typing buffer (must hold lock)."""
        if not self._typing_buffer:
            return
        
        duration_ms = (self._last_key_time - self._typing_start_time) * 1000
        
        event = KeyTypeEvent(
            timestamp=self._typing_start_time,
            text=self._typing_buffer,
            duration_ms=duration_ms,
        )
        self.on_event(event)
        
        self._typing_buffer = ""
        self._typing_start_time = 0.0
