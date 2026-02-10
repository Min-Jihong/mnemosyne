"""
Mnemosyne Hook System

A powerful lifecycle hook system for extending and customizing Mnemosyne's behavior.

Hooks allow plugins and user code to:
- Intercept and modify events at various lifecycle points
- React to system events (capture, inference, execution)
- Add custom processing without modifying core code

Available Hook Events:
- pre_capture / post_capture: Before/after event capture
- pre_inference / post_inference: Before/after LLM inference
- pre_execute / post_execute: Before/after action execution
- session_start / session_end: Session lifecycle
- memory_store / memory_retrieve: Memory operations
- error: Error handling

Example usage:
    from mnemosyne.hooks import HookManager, HookEvent

    hooks = HookManager()

    @hooks.on(HookEvent.POST_CAPTURE)
    async def log_events(payload: dict) -> dict:
        print(f"Captured {len(payload['events'])} events")
        return payload

    # Later in the pipeline
    result = await hooks.trigger(HookEvent.POST_CAPTURE, {"events": events})
"""

from mnemosyne.hooks.events import HookEvent, HookPriority
from mnemosyne.hooks.manager import HookManager, get_hook_manager
from mnemosyne.hooks.decorators import hook, on_event

__all__ = [
    "HookEvent",
    "HookPriority",
    "HookManager",
    "get_hook_manager",
    "hook",
    "on_event",
]
