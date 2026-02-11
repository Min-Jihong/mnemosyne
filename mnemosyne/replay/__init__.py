"""Action replay - replay recorded sessions."""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from mnemosyne.store.database import Database
from mnemosyne.store.models import StoredEvent
from mnemosyne.execute.controller import Controller
from mnemosyne.execute.safety import SafetyGuard, SafetyConfig


class ReplaySpeed(Enum):
    SLOW = 0.5
    NORMAL = 1.0
    FAST = 2.0
    INSTANT = 10.0


@dataclass
class ReplayConfig:
    speed: ReplaySpeed = ReplaySpeed.NORMAL
    skip_typing: bool = False
    skip_scrolling: bool = False
    require_confirmation: bool = True
    pause_between_actions_ms: int = 100
    safety_config: SafetyConfig | None = None


@dataclass
class ReplayState:
    session_id: str
    total_events: int
    current_index: int
    is_playing: bool
    is_paused: bool
    speed: ReplaySpeed
    
    @property
    def progress_percentage(self) -> float:
        return (self.current_index / self.total_events * 100) if self.total_events > 0 else 0


class ActionReplayer:
    
    def __init__(
        self,
        database: Database,
        config: ReplayConfig | None = None,
        on_action: Callable[[StoredEvent, int, int], None] | None = None,
        on_complete: Callable[[str], None] | None = None,
        on_error: Callable[[str, Exception], None] | None = None,
    ):
        self.database = database
        self.config = config or ReplayConfig()
        self.on_action = on_action
        self.on_complete = on_complete
        self.on_error = on_error
        
        self.controller = Controller(
            safety_guard=SafetyGuard(config=self.config.safety_config)
        )
        
        self._state: ReplayState | None = None
        self._stop_requested = False

    async def replay_session(
        self,
        session_id: str,
        start_index: int = 0,
    ) -> bool:
        events = self.database.get_events(session_id=session_id, limit=10000)
        
        if not events:
            return False
        
        replayable = self._filter_replayable_events(events)
        
        if not replayable:
            return False
        
        self._state = ReplayState(
            session_id=session_id,
            total_events=len(replayable),
            current_index=start_index,
            is_playing=True,
            is_paused=False,
            speed=self.config.speed,
        )
        
        self._stop_requested = False
        
        try:
            for i, event in enumerate(replayable[start_index:], start=start_index):
                if self._stop_requested:
                    break
                
                while self._state.is_paused:
                    await asyncio.sleep(0.1)
                    if self._stop_requested:
                        break
                
                self._state.current_index = i
                
                if self.on_action:
                    self.on_action(event, i, len(replayable))
                
                if self.config.require_confirmation:
                    confirmed = await self._confirm_action(event)
                    if not confirmed:
                        continue
                
                await self._execute_event(event)
                
                delay = self.config.pause_between_actions_ms / 1000.0
                delay /= self.config.speed.value
                await asyncio.sleep(delay)
            
            self._state.is_playing = False
            
            if self.on_complete:
                self.on_complete(session_id)
            
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(session_id, e)
            return False

    def pause(self) -> None:
        if self._state:
            self._state.is_paused = True

    def resume(self) -> None:
        if self._state:
            self._state.is_paused = False

    def stop(self) -> None:
        self._stop_requested = True
        if self._state:
            self._state.is_playing = False

    def set_speed(self, speed: ReplaySpeed) -> None:
        self.config.speed = speed
        if self._state:
            self._state.speed = speed

    def get_state(self) -> ReplayState | None:
        return self._state

    def _filter_replayable_events(self, events: list[StoredEvent]) -> list[StoredEvent]:
        replayable_types = {
            "mouse_click", "mouse_double_click", "mouse_right_click",
            "key_press", "key_type", "hotkey",
            "scroll",
        }
        
        filtered = []
        for event in events:
            if event.action_type not in replayable_types:
                continue
            
            if self.config.skip_typing and event.action_type == "key_type":
                continue
            
            if self.config.skip_scrolling and event.action_type == "scroll":
                continue
            
            filtered.append(event)
        
        return filtered

    async def _execute_event(self, event: StoredEvent) -> bool:
        try:
            action_type = event.action_type
            data = event.data or {}
            
            if action_type == "mouse_click":
                return self.controller.click(
                    x=data.get("x"),
                    y=data.get("y"),
                    button=data.get("button", "left"),
                )
            
            elif action_type == "mouse_double_click":
                return self.controller.double_click(
                    x=data.get("x"),
                    y=data.get("y"),
                )
            
            elif action_type == "mouse_right_click":
                return self.controller.right_click(
                    x=data.get("x"),
                    y=data.get("y"),
                )
            
            elif action_type == "key_press":
                return self.controller.press_key(
                    key=data.get("key", ""),
                )
            
            elif action_type == "key_type":
                text = data.get("text", "")
                if text:
                    return self.controller.type_text(
                        text=text,
                        interval=0.02 / self.config.speed.value,
                    )
            
            elif action_type == "hotkey":
                keys = data.get("keys", [])
                if keys:
                    return self.controller.hotkey(*keys)
            
            elif action_type == "scroll":
                return self.controller.scroll(
                    clicks=data.get("clicks", 0),
                    x=data.get("x"),
                    y=data.get("y"),
                )
            
            return False
            
        except Exception:
            return False

    async def _confirm_action(self, event: StoredEvent) -> bool:
        return True

    def get_session_preview(self, session_id: str) -> dict:
        events = self.database.get_events(session_id=session_id, limit=10000)
        replayable = self._filter_replayable_events(events)
        
        action_counts: dict[str, int] = {}
        for event in replayable:
            action_counts[event.action_type] = action_counts.get(event.action_type, 0) + 1
        
        duration = 0.0
        if events:
            duration = events[-1].timestamp - events[0].timestamp
        
        estimated_replay_time = len(replayable) * (self.config.pause_between_actions_ms / 1000.0)
        estimated_replay_time /= self.config.speed.value
        
        return {
            "session_id": session_id,
            "total_events": len(events),
            "replayable_events": len(replayable),
            "action_breakdown": action_counts,
            "original_duration_seconds": duration,
            "estimated_replay_seconds": estimated_replay_time,
        }
