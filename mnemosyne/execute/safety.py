import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class SafetyConfig:
    enabled: bool = True
    require_confirmation: bool = True
    max_actions_per_minute: int = 60
    blocked_apps: list[str] = field(default_factory=lambda: [
        "Terminal",
        "iTerm",
        "System Preferences",
        "System Settings",
        "Keychain Access",
        "1Password",
        "Bitwarden",
    ])
    blocked_hotkeys: list[list[str]] = field(default_factory=lambda: [
        ["cmd", "q"],
        ["cmd", "shift", "q"],
        ["cmd", "alt", "esc"],
    ])
    safe_zone: tuple[int, int, int, int] | None = None


class SafetyGuard:
    
    def __init__(
        self,
        config: SafetyConfig | None = None,
        on_violation: Callable[[str], None] | None = None,
    ):
        self.config = config or SafetyConfig()
        self.on_violation = on_violation
        self._action_timestamps: list[float] = []
        self._paused = False
    
    def check_action(
        self,
        action_type: str,
        target_app: str | None = None,
        position: tuple[int, int] | None = None,
        keys: list[str] | None = None,
    ) -> tuple[bool, str]:
        if not self.config.enabled:
            return True, ""
        
        if self._paused:
            return False, "Safety guard is paused"
        
        if target_app and target_app in self.config.blocked_apps:
            msg = f"Action blocked: {target_app} is a protected application"
            self._handle_violation(msg)
            return False, msg
        
        if keys:
            normalized_keys = sorted([k.lower() for k in keys])
            for blocked in self.config.blocked_hotkeys:
                blocked_normalized = sorted([k.lower() for k in blocked])
                if normalized_keys == blocked_normalized:
                    msg = f"Action blocked: {'+'.join(keys)} is a protected hotkey"
                    self._handle_violation(msg)
                    return False, msg
        
        if position and self.config.safe_zone:
            x, y = position
            sx, sy, sw, sh = self.config.safe_zone
            if not (sx <= x <= sx + sw and sy <= y <= sy + sh):
                msg = f"Action blocked: position ({x}, {y}) outside safe zone"
                self._handle_violation(msg)
                return False, msg
        
        if not self._check_rate_limit():
            msg = "Action blocked: rate limit exceeded"
            self._handle_violation(msg)
            return False, msg
        
        return True, ""
    
    def _check_rate_limit(self) -> bool:
        current_time = time.time()
        self._action_timestamps = [
            t for t in self._action_timestamps
            if current_time - t < 60
        ]
        
        if len(self._action_timestamps) >= self.config.max_actions_per_minute:
            return False
        
        self._action_timestamps.append(current_time)
        return True
    
    def _handle_violation(self, message: str) -> None:
        if self.on_violation:
            self.on_violation(message)
    
    def pause(self) -> None:
        self._paused = True
    
    def resume(self) -> None:
        self._paused = False
    
    def emergency_stop(self) -> None:
        self._paused = True
        self._action_timestamps.clear()
    
    def add_blocked_app(self, app_name: str) -> None:
        if app_name not in self.config.blocked_apps:
            self.config.blocked_apps.append(app_name)
    
    def remove_blocked_app(self, app_name: str) -> None:
        if app_name in self.config.blocked_apps:
            self.config.blocked_apps.remove(app_name)
    
    def set_safe_zone(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        self.config.safe_zone = (x, y, width, height)
    
    def clear_safe_zone(self) -> None:
        self.config.safe_zone = None
