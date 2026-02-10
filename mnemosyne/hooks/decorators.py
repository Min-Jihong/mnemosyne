"""Decorators for easy hook registration."""

from functools import wraps
from typing import Any, Callable, Coroutine

from mnemosyne.hooks.events import HookEvent, HookPriority
from mnemosyne.hooks.manager import HookHandler, get_hook_manager


def hook(
    event: HookEvent,
    *,
    priority: HookPriority = HookPriority.NORMAL,
    name: str | None = None,
    source: str = "user",
) -> Callable[[HookHandler], HookHandler]:
    """
    Decorator to register a function as a hook handler.

    The decorated function will be automatically registered with the
    global hook manager when the module is loaded.

    Args:
        event: The hook event to listen for
        priority: Handler priority (higher runs first)
        name: Unique handler name (defaults to function name)
        source: Source identifier for grouping handlers

    Example:
        @hook(HookEvent.POST_CAPTURE)
        async def log_capture(payload: dict) -> dict:
            print(f"Captured: {payload}")
            return payload

        @hook(HookEvent.PRE_EXECUTE, priority=HookPriority.HIGH)
        async def validate_action(payload: dict) -> dict:
            if not is_safe(payload["action"]):
                payload["_cancel"] = True
            return payload
    """

    def decorator(handler: HookHandler) -> HookHandler:
        handler_name = name or handler.__name__

        # Register with global manager
        manager = get_hook_manager()
        manager.register(
            event,
            handler,
            priority=priority,
            name=handler_name,
            source=source,
        )

        return handler

    return decorator


def on_event(
    *events: HookEvent,
    priority: HookPriority = HookPriority.NORMAL,
    source: str = "user",
) -> Callable[[HookHandler], HookHandler]:
    """
    Decorator to register a function for multiple hook events.

    Args:
        *events: One or more hook events to listen for
        priority: Handler priority
        source: Source identifier

    Example:
        @on_event(HookEvent.SESSION_START, HookEvent.SESSION_END)
        async def track_session(payload: dict) -> dict:
            print(f"Session event: {payload}")
            return payload
    """

    def decorator(handler: HookHandler) -> HookHandler:
        manager = get_hook_manager()

        for event in events:
            handler_name = f"{handler.__name__}:{event.value}"
            manager.register(
                event,
                handler,
                priority=priority,
                name=handler_name,
                source=source,
            )

        return handler

    return decorator


class HookMixin:
    """
    Mixin class for adding hook support to any class.

    Classes that inherit from this mixin gain easy access to
    hook registration and triggering.

    Example:
        class MyService(HookMixin):
            async def process(self, data):
                # Trigger pre-hook
                result = await self.trigger_hook(
                    HookEvent.PRE_INFERENCE,
                    {"data": data}
                )

                if result.cancelled:
                    return None

                # Do processing...

                # Trigger post-hook
                await self.trigger_hook(
                    HookEvent.POST_INFERENCE,
                    {"data": data, "result": processed}
                )
    """

    @property
    def hooks(self):
        """Get the global hook manager."""
        return get_hook_manager()

    def register_hook(
        self,
        event: HookEvent,
        handler: HookHandler,
        *,
        priority: HookPriority = HookPriority.NORMAL,
        name: str | None = None,
    ) -> str:
        """Register a hook handler."""
        source = self.__class__.__name__
        return self.hooks.register(
            event, handler, priority=priority, name=name, source=source
        )

    async def trigger_hook(
        self,
        event: HookEvent,
        payload: dict[str, Any],
        *,
        allow_cancel: bool = True,
    ):
        """Trigger a hook event."""
        return await self.hooks.trigger(event, payload, allow_cancel=allow_cancel)

    def unregister_hooks(self) -> int:
        """Unregister all hooks registered by this instance."""
        return self.hooks.unregister_by_source(self.__class__.__name__)
