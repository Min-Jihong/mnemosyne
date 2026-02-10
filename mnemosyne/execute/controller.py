import time
from typing import Callable

from mnemosyne.execute.safety import SafetyGuard


class Controller:
    
    def __init__(
        self,
        safety_guard: SafetyGuard | None = None,
        action_delay_ms: int = 50,
    ):
        self.safety_guard = safety_guard or SafetyGuard()
        self.action_delay_ms = action_delay_ms
        self._pyautogui = None
    
    def _ensure_pyautogui(self) -> None:
        if self._pyautogui is None:
            try:
                import pyautogui
                pyautogui.FAILSAFE = True
                pyautogui.PAUSE = self.action_delay_ms / 1000.0
                self._pyautogui = pyautogui
            except ImportError:
                raise ImportError(
                    "pyautogui is required for computer control. "
                    "Install with: pip install pyautogui"
                )
    
    def move_mouse(self, x: int, y: int, duration: float = 0.25) -> bool:
        allowed, reason = self.safety_guard.check_action(
            action_type="mouse_move",
            position=(x, y),
        )
        if not allowed:
            return False
        
        self._ensure_pyautogui()
        self._pyautogui.moveTo(x, y, duration=duration)
        return True
    
    def click(
        self,
        x: int | None = None,
        y: int | None = None,
        button: str = "left",
        clicks: int = 1,
    ) -> bool:
        position = (x, y) if x is not None and y is not None else None
        
        allowed, reason = self.safety_guard.check_action(
            action_type="mouse_click",
            position=position,
        )
        if not allowed:
            return False
        
        self._ensure_pyautogui()
        self._pyautogui.click(x=x, y=y, button=button, clicks=clicks)
        return True
    
    def double_click(self, x: int | None = None, y: int | None = None) -> bool:
        return self.click(x=x, y=y, clicks=2)
    
    def right_click(self, x: int | None = None, y: int | None = None) -> bool:
        return self.click(x=x, y=y, button="right")
    
    def scroll(self, clicks: int, x: int | None = None, y: int | None = None) -> bool:
        position = (x, y) if x is not None and y is not None else None
        
        allowed, reason = self.safety_guard.check_action(
            action_type="mouse_scroll",
            position=position,
        )
        if not allowed:
            return False
        
        self._ensure_pyautogui()
        self._pyautogui.scroll(clicks, x=x, y=y)
        return True
    
    def type_text(self, text: str, interval: float = 0.02) -> bool:
        allowed, reason = self.safety_guard.check_action(
            action_type="key_type",
        )
        if not allowed:
            return False
        
        self._ensure_pyautogui()
        self._pyautogui.typewrite(text, interval=interval)
        return True
    
    def press_key(self, key: str) -> bool:
        allowed, reason = self.safety_guard.check_action(
            action_type="key_press",
            keys=[key],
        )
        if not allowed:
            return False
        
        self._ensure_pyautogui()
        self._pyautogui.press(key)
        return True
    
    def hotkey(self, *keys: str) -> bool:
        allowed, reason = self.safety_guard.check_action(
            action_type="hotkey",
            keys=list(keys),
        )
        if not allowed:
            return False
        
        self._ensure_pyautogui()
        self._pyautogui.hotkey(*keys)
        return True
    
    def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 0.5,
        button: str = "left",
    ) -> bool:
        allowed, reason = self.safety_guard.check_action(
            action_type="mouse_drag",
            position=(start_x, start_y),
        )
        if not allowed:
            return False
        
        self._ensure_pyautogui()
        self._pyautogui.moveTo(start_x, start_y)
        self._pyautogui.drag(
            end_x - start_x,
            end_y - start_y,
            duration=duration,
            button=button,
        )
        return True
    
    def get_screen_size(self) -> tuple[int, int]:
        self._ensure_pyautogui()
        return self._pyautogui.size()
    
    def get_mouse_position(self) -> tuple[int, int]:
        self._ensure_pyautogui()
        pos = self._pyautogui.position()
        return (pos.x, pos.y)
