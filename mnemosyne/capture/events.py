"""Event types for capturing user interactions."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal
import time
import uuid


class ActionType(str, Enum):
    """Types of user actions."""
    # Mouse events
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_DOUBLE_CLICK = "mouse_double_click"
    MOUSE_RIGHT_CLICK = "mouse_right_click"
    MOUSE_DRAG = "mouse_drag"
    MOUSE_SCROLL = "mouse_scroll"
    
    # Keyboard events
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    KEY_TYPE = "key_type"  # Aggregated typing (multiple chars)
    HOTKEY = "hotkey"  # Keyboard shortcut
    
    # Screen events
    SCREENSHOT = "screenshot"
    
    # Window events
    WINDOW_CHANGE = "window_change"
    WINDOW_RESIZE = "window_resize"


@dataclass
class BaseEvent:
    """Base class for all events."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    action_type: ActionType = ActionType.MOUSE_MOVE
    
    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "action_type": self.action_type.value,
        }


@dataclass
class MouseMoveEvent(BaseEvent):
    """Mouse movement event."""
    action_type: ActionType = field(default=ActionType.MOUSE_MOVE)
    x: int = 0
    y: int = 0
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"x": self.x, "y": self.y})
        return d


@dataclass
class MouseClickEvent(BaseEvent):
    """Mouse click event."""
    action_type: ActionType = field(default=ActionType.MOUSE_CLICK)
    x: int = 0
    y: int = 0
    button: str = "left"
    pressed: bool = True
    click_count: int = 1  # 1 for single, 2 for double
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "x": self.x,
            "y": self.y,
            "button": self.button,
            "pressed": self.pressed,
            "click_count": self.click_count,
        })
        return d


@dataclass
class MouseScrollEvent(BaseEvent):
    """Mouse scroll event."""
    action_type: ActionType = field(default=ActionType.MOUSE_SCROLL)
    x: int = 0
    y: int = 0
    dx: int = 0  # Horizontal scroll
    dy: int = 0  # Vertical scroll
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "x": self.x,
            "y": self.y,
            "dx": self.dx,
            "dy": self.dy,
        })
        return d


@dataclass
class KeyPressEvent(BaseEvent):
    """Key press event."""
    action_type: ActionType = field(default=ActionType.KEY_PRESS)
    key: str = ""  # Key name (e.g., "a", "shift", "cmd")
    key_char: str | None = None  # Character if printable
    key_code: int | None = None  # Virtual key code
    modifiers: list[str] = field(default_factory=list)  # Active modifiers
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "key": self.key,
            "key_char": self.key_char,
            "key_code": self.key_code,
            "modifiers": self.modifiers,
        })
        return d


@dataclass
class KeyReleaseEvent(BaseEvent):
    """Key release event."""
    action_type: ActionType = field(default=ActionType.KEY_RELEASE)
    key: str = ""
    key_char: str | None = None
    key_code: int | None = None
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "key": self.key,
            "key_char": self.key_char,
            "key_code": self.key_code,
        })
        return d


@dataclass
class KeyTypeEvent(BaseEvent):
    """Aggregated typing event (multiple characters)."""
    action_type: ActionType = field(default=ActionType.KEY_TYPE)
    text: str = ""
    duration_ms: float = 0.0  # Time taken to type
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "text": self.text,
            "duration_ms": self.duration_ms,
        })
        return d


@dataclass
class HotkeyEvent(BaseEvent):
    """Keyboard shortcut event."""
    action_type: ActionType = field(default=ActionType.HOTKEY)
    keys: list[str] = field(default_factory=list)  # e.g., ["cmd", "c"]
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"keys": self.keys})
        return d


@dataclass
class ScreenshotEvent(BaseEvent):
    """Screenshot capture event."""
    action_type: ActionType = field(default=ActionType.SCREENSHOT)
    filepath: str = ""
    width: int = 0
    height: int = 0
    file_size: int = 0
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "filepath": self.filepath,
            "width": self.width,
            "height": self.height,
            "file_size": self.file_size,
        })
        return d


@dataclass
class WindowChangeEvent(BaseEvent):
    """Window focus/change event."""
    action_type: ActionType = field(default=ActionType.WINDOW_CHANGE)
    app_name: str = ""
    window_title: str = ""
    bundle_id: str = ""  # macOS bundle identifier
    bounds: tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, width, height
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "app_name": self.app_name,
            "window_title": self.window_title,
            "bundle_id": self.bundle_id,
            "bounds": self.bounds,
        })
        return d


# Type alias for all event types
Event = (
    MouseMoveEvent
    | MouseClickEvent
    | MouseScrollEvent
    | KeyPressEvent
    | KeyReleaseEvent
    | KeyTypeEvent
    | HotkeyEvent
    | ScreenshotEvent
    | WindowChangeEvent
)
