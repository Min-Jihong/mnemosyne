"""Tests for the hook system."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from mnemosyne.hooks.events import HookEvent, HookPriority
from mnemosyne.hooks.manager import HookManager


class TestHookManager:
    """Tests for HookManager."""

    @pytest.fixture
    def manager(self) -> HookManager:
        """Create a fresh hook manager."""
        return HookManager()

    @pytest.mark.asyncio
    async def test_register_handler(self, manager: HookManager) -> None:
        """Test registering a handler."""
        async def handler(payload: dict) -> dict:
            return payload

        name = manager.register(HookEvent.POST_CAPTURE, handler)
        assert name is not None
        handlers = manager.get_handlers(HookEvent.POST_CAPTURE)
        assert len(handlers) == 1
        assert handlers[0].name == name

    @pytest.mark.asyncio
    async def test_unregister_handler(self, manager: HookManager) -> None:
        """Test unregistering a handler."""
        async def handler(payload: dict) -> dict:
            return payload

        name = manager.register(HookEvent.POST_CAPTURE, handler, name="test_handler")
        assert manager.unregister("test_handler")
        handlers = manager.get_handlers(HookEvent.POST_CAPTURE)
        assert len(handlers) == 0

    @pytest.mark.asyncio
    async def test_trigger_single_handler(self, manager: HookManager) -> None:
        """Test triggering event with single handler."""
        called_with = None

        async def handler(payload: dict) -> dict:
            nonlocal called_with
            called_with = payload.copy()
            payload["modified"] = True
            return payload

        manager.register(HookEvent.POST_CAPTURE, handler)
        result = await manager.trigger(HookEvent.POST_CAPTURE, {"data": "test"})

        assert called_with == {"data": "test"}
        assert result.payload["modified"] is True
        assert result.handlers_called == 1

    @pytest.mark.asyncio
    async def test_trigger_multiple_handlers(self, manager: HookManager) -> None:
        """Test triggering event with multiple handlers."""
        call_order = []

        async def handler1(payload: dict) -> dict:
            call_order.append("handler1")
            payload["handler1"] = True
            return payload

        async def handler2(payload: dict) -> dict:
            call_order.append("handler2")
            payload["handler2"] = True
            return payload

        manager.register(HookEvent.POST_CAPTURE, handler1)
        manager.register(HookEvent.POST_CAPTURE, handler2)

        result = await manager.trigger(HookEvent.POST_CAPTURE, {})

        assert result.handlers_called == 2
        assert result.payload["handler1"] is True
        assert result.payload["handler2"] is True

    @pytest.mark.asyncio
    async def test_priority_ordering(self, manager: HookManager) -> None:
        """Test handlers are called in priority order."""
        call_order = []

        async def low_priority(payload: dict) -> dict:
            call_order.append("low")
            return payload

        async def high_priority(payload: dict) -> dict:
            call_order.append("high")
            return payload

        async def normal_priority(payload: dict) -> dict:
            call_order.append("normal")
            return payload

        manager.register(HookEvent.POST_CAPTURE, low_priority, priority=HookPriority.LOW)
        manager.register(HookEvent.POST_CAPTURE, high_priority, priority=HookPriority.HIGH)
        manager.register(HookEvent.POST_CAPTURE, normal_priority, priority=HookPriority.NORMAL)

        await manager.trigger(HookEvent.POST_CAPTURE, {})

        assert call_order == ["high", "normal", "low"]

    @pytest.mark.asyncio
    async def test_cancel_event(self, manager: HookManager) -> None:
        """Test cancelling an event."""
        async def cancelling_handler(payload: dict) -> dict:
            payload["_cancel"] = True
            return payload

        async def never_called(payload: dict) -> dict:
            payload["reached"] = True
            return payload

        manager.register(
            HookEvent.PRE_CAPTURE,
            cancelling_handler,
            priority=HookPriority.HIGH
        )
        manager.register(
            HookEvent.PRE_CAPTURE,
            never_called,
            priority=HookPriority.LOW
        )

        result = await manager.trigger(HookEvent.PRE_CAPTURE, {})

        assert result.cancelled is True
        assert "reached" not in result.payload

    @pytest.mark.asyncio
    async def test_disable_handler(self, manager: HookManager) -> None:
        """Test disabling a handler."""
        async def handler(payload: dict) -> dict:
            payload["called"] = True
            return payload

        name = manager.register(HookEvent.POST_CAPTURE, handler, name="test")
        manager.disable("test")

        result = await manager.trigger(HookEvent.POST_CAPTURE, {})

        assert result.handlers_called == 0
        assert "called" not in result.payload

    @pytest.mark.asyncio
    async def test_enable_handler(self, manager: HookManager) -> None:
        """Test enabling a disabled handler."""
        async def handler(payload: dict) -> dict:
            payload["called"] = True
            return payload

        manager.register(HookEvent.POST_CAPTURE, handler, name="test")
        manager.disable("test")
        manager.enable("test")

        result = await manager.trigger(HookEvent.POST_CAPTURE, {})

        assert result.handlers_called == 1
        assert result.payload["called"] is True

    @pytest.mark.asyncio
    async def test_handler_error_isolation(self, manager: HookManager) -> None:
        """Test that one handler error doesn't affect others."""
        async def failing_handler(payload: dict) -> dict:
            raise ValueError("Test error")

        async def working_handler(payload: dict) -> dict:
            payload["working"] = True
            return payload

        manager.register(
            HookEvent.POST_CAPTURE,
            failing_handler,
            priority=HookPriority.HIGH
        )
        manager.register(
            HookEvent.POST_CAPTURE,
            working_handler,
            priority=HookPriority.LOW
        )

        result = await manager.trigger(HookEvent.POST_CAPTURE, {})

        # Working handler should still be called
        assert result.payload["working"] is True
        assert len(result.errors) == 1
        assert "Test error" in str(result.errors[0][1])

    @pytest.mark.asyncio
    async def test_trigger_parallel(self, manager: HookManager) -> None:
        """Test parallel event triggering."""
        results = []

        async def slow_handler(payload: dict) -> dict:
            await asyncio.sleep(0.01)
            results.append("slow")
            return payload

        async def fast_handler(payload: dict) -> dict:
            results.append("fast")
            return payload

        manager.register(HookEvent.POST_CAPTURE, slow_handler)
        manager.register(HookEvent.POST_CAPTURE, fast_handler)

        result = await manager.trigger_parallel(HookEvent.POST_CAPTURE, {})

        assert result.handlers_called == 2
        # With parallel execution, fast should finish first
        assert "fast" in results
        assert "slow" in results

    @pytest.mark.asyncio
    async def test_unregister_by_source(self, manager: HookManager) -> None:
        """Test unregistering all handlers from a source."""
        async def handler1(payload: dict) -> dict:
            return payload

        async def handler2(payload: dict) -> dict:
            return payload

        manager.register(HookEvent.POST_CAPTURE, handler1, source="plugin-a")
        manager.register(HookEvent.POST_CAPTURE, handler2, source="plugin-a")
        manager.register(HookEvent.PRE_CAPTURE, handler1, source="plugin-b")

        removed = manager.unregister_by_source("plugin-a")

        assert removed == 2
        assert len(manager.get_handlers(HookEvent.POST_CAPTURE)) == 0
        assert len(manager.get_handlers(HookEvent.PRE_CAPTURE)) == 1

    @pytest.mark.asyncio
    async def test_decorator_registration(self, manager: HookManager) -> None:
        """Test using decorator for registration."""

        @manager.on(HookEvent.POST_CAPTURE)
        async def decorated_handler(payload: dict) -> dict:
            payload["decorated"] = True
            return payload

        result = await manager.trigger(HookEvent.POST_CAPTURE, {})

        assert result.payload["decorated"] is True

    @pytest.mark.asyncio
    async def test_stats_tracking(self, manager: HookManager) -> None:
        """Test performance stats tracking."""
        async def handler(payload: dict) -> dict:
            return payload

        manager.register(HookEvent.POST_CAPTURE, handler, name="test_handler")

        await manager.trigger(HookEvent.POST_CAPTURE, {})
        await manager.trigger(HookEvent.POST_CAPTURE, {})

        stats = manager.get_stats()
        assert "test_handler" in stats
        assert stats["test_handler"]["call_count"] == 2
        assert stats["test_handler"]["total_time_ms"] > 0

    def test_clear_handlers(self, manager: HookManager) -> None:
        """Test clearing all handlers."""
        async def handler(payload: dict) -> dict:
            return payload

        manager.register(HookEvent.POST_CAPTURE, handler)
        manager.register(HookEvent.PRE_CAPTURE, handler)

        manager.clear()

        assert len(manager.get_handlers()) == 0

    def test_duplicate_name_error(self, manager: HookManager) -> None:
        """Test that duplicate handler names raise error."""
        async def handler(payload: dict) -> dict:
            return payload

        manager.register(HookEvent.POST_CAPTURE, handler, name="unique_name")

        with pytest.raises(ValueError, match="already registered"):
            manager.register(HookEvent.POST_CAPTURE, handler, name="unique_name")


class TestHookEvents:
    """Tests for hook event definitions."""

    def test_all_events_have_string_value(self) -> None:
        """Test all hook events have valid string values."""
        for event in HookEvent:
            assert isinstance(event.value, str)
            assert len(event.value) > 0

    def test_priority_ordering(self) -> None:
        """Test priority values are correctly ordered."""
        assert HookPriority.LOWEST.value < HookPriority.LOW.value
        assert HookPriority.LOW.value < HookPriority.NORMAL.value
        assert HookPriority.NORMAL.value < HookPriority.HIGH.value
        assert HookPriority.HIGH.value < HookPriority.HIGHEST.value
        assert HookPriority.HIGHEST.value < HookPriority.SYSTEM.value
