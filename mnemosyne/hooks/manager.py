"""Hook manager for registering and triggering hooks."""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine

from mnemosyne.hooks.events import HookEvent, HookPriority

logger = logging.getLogger(__name__)

# Type for hook handler functions
HookHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any] | None]]


@dataclass
class HookRegistration:
    """Represents a registered hook handler."""

    event: HookEvent
    handler: HookHandler
    priority: HookPriority
    name: str
    source: str  # Plugin name or "user"
    enabled: bool = True
    registered_at: datetime = field(default_factory=datetime.now)
    call_count: int = 0
    total_time_ms: float = 0.0


@dataclass
class HookResult:
    """Result of triggering a hook event."""

    event: HookEvent
    payload: dict[str, Any]
    handlers_called: int
    cancelled: bool = False
    errors: list[tuple[str, Exception]] = field(default_factory=list)
    total_time_ms: float = 0.0


class HookManager:
    """
    Manages hook registration and event dispatch.

    Features:
    - Priority-based handler ordering
    - Async handler support
    - Handler enable/disable
    - Error isolation (one handler failure doesn't stop others)
    - Performance tracking
    - Event cancellation for pre-* events
    """

    def __init__(self) -> None:
        self._hooks: dict[HookEvent, list[HookRegistration]] = defaultdict(list)
        self._handlers_by_name: dict[str, HookRegistration] = {}

    def register(
        self,
        event: HookEvent,
        handler: HookHandler,
        *,
        priority: HookPriority = HookPriority.NORMAL,
        name: str | None = None,
        source: str = "user",
    ) -> str:
        """
        Register a hook handler.

        Args:
            event: The event to listen for
            handler: Async function that receives and optionally modifies payload
            priority: Handler priority (higher runs first)
            name: Unique name for the handler (auto-generated if not provided)
            source: Source identifier (plugin name or "user")

        Returns:
            The handler name (for later reference)
        """
        if name is None:
            name = f"{source}:{event.value}:{len(self._hooks[event])}"

        if name in self._handlers_by_name:
            raise ValueError(f"Handler with name '{name}' already registered")

        registration = HookRegistration(
            event=event,
            handler=handler,
            priority=priority,
            name=name,
            source=source,
        )

        self._hooks[event].append(registration)
        self._handlers_by_name[name] = registration

        # Sort by priority (highest first)
        self._hooks[event].sort(key=lambda r: r.priority.value, reverse=True)

        logger.debug(f"Registered hook handler '{name}' for {event.value}")
        return name

    def unregister(self, name: str) -> bool:
        """
        Unregister a hook handler by name.

        Args:
            name: The handler name

        Returns:
            True if handler was found and removed
        """
        registration = self._handlers_by_name.pop(name, None)
        if registration is None:
            return False

        self._hooks[registration.event] = [
            r for r in self._hooks[registration.event] if r.name != name
        ]
        logger.debug(f"Unregistered hook handler '{name}'")
        return True

    def unregister_by_source(self, source: str) -> int:
        """
        Unregister all handlers from a specific source.

        Args:
            source: Source identifier (e.g., plugin name)

        Returns:
            Number of handlers removed
        """
        to_remove = [
            name for name, reg in self._handlers_by_name.items()
            if reg.source == source
        ]
        for name in to_remove:
            self.unregister(name)
        return len(to_remove)

    def enable(self, name: str) -> bool:
        """Enable a handler by name."""
        if name in self._handlers_by_name:
            self._handlers_by_name[name].enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a handler by name."""
        if name in self._handlers_by_name:
            self._handlers_by_name[name].enabled = False
            return True
        return False

    async def trigger(
        self,
        event: HookEvent,
        payload: dict[str, Any],
        *,
        allow_cancel: bool = True,
    ) -> HookResult:
        """
        Trigger a hook event and run all registered handlers.

        Args:
            event: The event to trigger
            payload: Event data (may be modified by handlers)
            allow_cancel: Whether handlers can cancel the event

        Returns:
            HookResult with final payload and metadata
        """
        import time

        start_time = time.perf_counter()
        result = HookResult(event=event, payload=payload, handlers_called=0)

        handlers = self._hooks.get(event, [])
        if not handlers:
            return result

        current_payload = payload.copy()

        for registration in handlers:
            if not registration.enabled:
                continue

            handler_start = time.perf_counter()

            try:
                # Call the handler
                handler_result = await registration.handler(current_payload)

                # Update payload if handler returned modified version
                if handler_result is not None:
                    # Check for cancellation
                    if allow_cancel and handler_result.get("_cancel"):
                        result.cancelled = True
                        result.payload = current_payload
                        logger.info(
                            f"Event {event.value} cancelled by handler '{registration.name}'"
                        )
                        break

                    current_payload = handler_result

                result.handlers_called += 1

            except Exception as e:
                logger.error(
                    f"Hook handler '{registration.name}' failed for {event.value}: {e}"
                )
                result.errors.append((registration.name, e))

            finally:
                # Track performance
                handler_time = (time.perf_counter() - handler_start) * 1000
                registration.call_count += 1
                registration.total_time_ms += handler_time

        result.payload = current_payload
        result.total_time_ms = (time.perf_counter() - start_time) * 1000

        return result

    async def trigger_parallel(
        self,
        event: HookEvent,
        payload: dict[str, Any],
    ) -> HookResult:
        """
        Trigger a hook event and run all handlers in parallel.

        Use for events where handler order doesn't matter and
        payload modification is not expected.

        Args:
            event: The event to trigger
            payload: Event data (not modified)

        Returns:
            HookResult with original payload and metadata
        """
        import time

        start_time = time.perf_counter()
        result = HookResult(event=event, payload=payload, handlers_called=0)

        handlers = self._hooks.get(event, [])
        if not handlers:
            return result

        async def run_handler(registration: HookRegistration) -> tuple[str, Exception | None]:
            if not registration.enabled:
                return registration.name, None

            try:
                await registration.handler(payload.copy())
                registration.call_count += 1
                return registration.name, None
            except Exception as e:
                return registration.name, e

        # Run all handlers in parallel
        tasks = [run_handler(reg) for reg in handlers]
        results = await asyncio.gather(*tasks)

        for name, error in results:
            if error is None:
                result.handlers_called += 1
            else:
                result.errors.append((name, error))
                logger.error(f"Hook handler '{name}' failed for {event.value}: {error}")

        result.total_time_ms = (time.perf_counter() - start_time) * 1000
        return result

    def on(
        self,
        event: HookEvent,
        *,
        priority: HookPriority = HookPriority.NORMAL,
        name: str | None = None,
        source: str = "user",
    ) -> Callable[[HookHandler], HookHandler]:
        """
        Decorator to register a hook handler.

        Example:
            @hooks.on(HookEvent.POST_CAPTURE)
            async def my_handler(payload: dict) -> dict:
                # Process payload
                return payload
        """

        def decorator(handler: HookHandler) -> HookHandler:
            handler_name = name or handler.__name__
            self.register(
                event, handler, priority=priority, name=handler_name, source=source
            )
            return handler

        return decorator

    def get_handlers(self, event: HookEvent | None = None) -> list[HookRegistration]:
        """Get all handlers, optionally filtered by event."""
        if event is None:
            return list(self._handlers_by_name.values())
        return self._hooks.get(event, []).copy()

    def get_stats(self) -> dict[str, Any]:
        """Get performance statistics for all handlers."""
        return {
            name: {
                "event": reg.event.value,
                "priority": reg.priority.name,
                "enabled": reg.enabled,
                "call_count": reg.call_count,
                "total_time_ms": reg.total_time_ms,
                "avg_time_ms": (
                    reg.total_time_ms / reg.call_count if reg.call_count > 0 else 0
                ),
            }
            for name, reg in self._handlers_by_name.items()
        }

    def clear(self) -> None:
        """Remove all registered handlers."""
        self._hooks.clear()
        self._handlers_by_name.clear()


# Global hook manager instance
_manager: HookManager | None = None


def get_hook_manager() -> HookManager:
    """Get or create the global hook manager."""
    global _manager
    if _manager is None:
        _manager = HookManager()
    return _manager
