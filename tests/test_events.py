import pytest
from mnemosyne.capture.events import (
    ActionType,
    MouseMoveEvent,
    MouseClickEvent,
    MouseScrollEvent,
    KeyPressEvent,
    KeyReleaseEvent,
    KeyTypeEvent,
    HotkeyEvent,
    WindowChangeEvent,
)


class TestEvents:
    
    def test_mouse_move_event(self):
        event = MouseMoveEvent(x=100, y=200)
        
        assert event.action_type == ActionType.MOUSE_MOVE
        assert event.x == 100
        assert event.y == 200
        assert event.id is not None
        assert event.timestamp > 0
    
    def test_mouse_click_event(self):
        event = MouseClickEvent(
            x=50,
            y=75,
            button="right",
            pressed=True,
            click_count=2,
        )
        
        assert event.action_type == ActionType.MOUSE_CLICK
        assert event.button == "right"
        assert event.click_count == 2
    
    def test_key_press_event(self):
        event = KeyPressEvent(
            key="cmd",
            modifiers=["shift"],
        )
        
        assert event.action_type == ActionType.KEY_PRESS
        assert event.key == "cmd"
        assert "shift" in event.modifiers
    
    def test_hotkey_event(self):
        event = HotkeyEvent(keys=["cmd", "c"])
        
        assert event.action_type == ActionType.HOTKEY
        assert event.keys == ["cmd", "c"]
    
    def test_window_change_event(self):
        event = WindowChangeEvent(
            app_name="Finder",
            window_title="Documents",
            bundle_id="com.apple.finder",
            bounds=(0, 0, 800, 600),
        )
        
        assert event.action_type == ActionType.WINDOW_CHANGE
        assert event.app_name == "Finder"
        assert event.bounds == (0, 0, 800, 600)
    
    def test_event_to_dict(self):
        event = MouseClickEvent(x=10, y=20, button="left")
        d = event.to_dict()
        
        assert "id" in d
        assert "timestamp" in d
        assert "action_type" in d
        assert d["x"] == 10
        assert d["y"] == 20
        assert d["button"] == "left"
