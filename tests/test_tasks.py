"""Tests for the background task system."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from mnemosyne.tasks import TaskManager, TaskStatus, TaskPriority, Task


class TestTask:
    """Tests for Task dataclass."""

    def test_create_task(self) -> None:
        """Test creating a task."""
        task = Task(name="test")
        assert task.name == "test"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL
        assert task.id is not None

    def test_task_priority_ordering(self) -> None:
        """Test that higher priority tasks sort first."""
        high = Task(name="high", priority=TaskPriority.HIGH)
        low = Task(name="low", priority=TaskPriority.LOW)
        normal = Task(name="normal", priority=TaskPriority.NORMAL)

        tasks = sorted([low, high, normal])
        assert tasks[0].name == "high"
        assert tasks[1].name == "normal"
        assert tasks[2].name == "low"

    def test_update_progress(self) -> None:
        """Test progress updates."""
        task = Task(name="test")
        task.update_progress(0.5, "Halfway done")

        assert task.progress == 0.5
        assert task.progress_message == "Halfway done"

    def test_progress_clamping(self) -> None:
        """Test progress is clamped to 0-1."""
        task = Task(name="test")

        task.update_progress(-1.0)
        assert task.progress == 0.0

        task.update_progress(2.0)
        assert task.progress == 1.0


class TestTaskManager:
    """Tests for TaskManager."""

    @pytest.fixture
    def manager(self) -> TaskManager:
        """Create a fresh task manager."""
        return TaskManager(max_workers=2)

    @pytest.mark.asyncio
    async def test_register_task(self, manager: TaskManager) -> None:
        """Test registering a task handler."""

        async def my_task(x: int) -> int:
            return x * 2

        manager.register("double", my_task)

        # Should be able to submit
        task_id = await manager.submit("double", 5)
        assert task_id is not None

    @pytest.mark.asyncio
    async def test_task_decorator(self, manager: TaskManager) -> None:
        """Test registering with decorator."""

        @manager.task(priority=TaskPriority.HIGH)
        async def decorated_task(x: int) -> int:
            return x + 1

        task_id = await manager.submit("decorated_task", 10)
        task = manager.get_task(task_id)

        assert task is not None
        assert task.priority == TaskPriority.HIGH

    @pytest.mark.asyncio
    async def test_submit_and_execute(self, manager: TaskManager) -> None:
        """Test submitting and executing a task."""
        result_value = None

        async def simple_task() -> str:
            return "done"

        manager.register("simple", simple_task)

        await manager.start()
        try:
            task_id = await manager.submit("simple")

            result = await manager.get_result(task_id, timeout=5.0)

            assert result.status == TaskStatus.COMPLETED
            assert result.result == "done"
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_task_with_args(self, manager: TaskManager) -> None:
        """Test task with arguments."""

        async def add_task(a: int, b: int) -> int:
            return a + b

        manager.register("add", add_task)

        await manager.start()
        try:
            task_id = await manager.submit("add", 3, 4)
            result = await manager.get_result(task_id, timeout=5.0)

            assert result.result == 7
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_task_cancellation(self, manager: TaskManager) -> None:
        """Test cancelling a task."""

        async def slow_task() -> None:
            await asyncio.sleep(10)

        manager.register("slow", slow_task)

        await manager.start()
        try:
            task_id = await manager.submit("slow")

            # Cancel immediately
            cancelled = await manager.cancel(task_id)
            assert cancelled is True

            task = manager.get_task(task_id)
            assert task.status in (TaskStatus.CANCELLED, TaskStatus.QUEUED)
        finally:
            await manager.stop(wait=False)

    @pytest.mark.asyncio
    async def test_task_failure(self, manager: TaskManager) -> None:
        """Test task that fails."""

        async def failing_task() -> None:
            raise ValueError("Test error")

        manager.register("failing", failing_task, max_retries=0)

        await manager.start()
        try:
            task_id = await manager.submit("failing")
            result = await manager.get_result(task_id, timeout=5.0)

            assert result.status == TaskStatus.FAILED
            assert "Test error" in result.error
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_task_retry(self, manager: TaskManager) -> None:
        """Test task retry on failure."""
        attempt_count = 0

        async def flaky_task() -> str:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ValueError("Temporary error")
            return "success"

        manager.register("flaky", flaky_task, max_retries=3)

        await manager.start()
        try:
            task_id = await manager.submit("flaky")
            result = await manager.get_result(task_id, timeout=5.0)

            assert result.status == TaskStatus.COMPLETED
            assert result.result == "success"
            assert attempt_count == 2
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_priority_ordering(self, manager: TaskManager) -> None:
        """Test that high priority tasks run first."""
        execution_order = []

        async def track_task(name: str) -> None:
            execution_order.append(name)
            await asyncio.sleep(0.01)

        manager.register("track", track_task)

        # Don't start workers yet so we can queue tasks
        low_id = await manager.submit("track", "low", priority=TaskPriority.LOW)
        normal_id = await manager.submit("track", "normal", priority=TaskPriority.NORMAL)
        high_id = await manager.submit("track", "high", priority=TaskPriority.HIGH)

        # Now start with single worker to ensure ordering
        manager._max_workers = 1
        await manager.start()
        try:
            await manager.get_result(high_id, timeout=5.0)
            await manager.get_result(normal_id, timeout=5.0)
            await manager.get_result(low_id, timeout=5.0)

            # High priority should have run first
            assert execution_order[0] == "high"
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_submit_raw(self, manager: TaskManager) -> None:
        """Test submitting a raw task without registration."""

        async def inline_task() -> int:
            return 42

        await manager.start()
        try:
            task_id = await manager.submit_raw(inline_task, name="inline")
            result = await manager.get_result(task_id, timeout=5.0)

            assert result.result == 42
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_list_tasks(self, manager: TaskManager) -> None:
        """Test listing tasks."""

        async def dummy() -> None:
            pass

        manager.register("dummy", dummy)

        task_id1 = await manager.submit("dummy")
        task_id2 = await manager.submit("dummy")

        tasks = manager.list_tasks()
        assert len(tasks) == 2

        queued = manager.list_tasks(status=TaskStatus.QUEUED)
        assert len(queued) == 2

    @pytest.mark.asyncio
    async def test_stats(self, manager: TaskManager) -> None:
        """Test getting manager stats."""

        async def dummy() -> None:
            await asyncio.sleep(0.1)

        manager.register("dummy", dummy)

        await manager.submit("dummy")
        await manager.submit("dummy")

        stats = manager.stats()
        assert stats["total_tasks"] == 2
        assert stats["queued"] == 2
        assert stats["workers"] == 2

    @pytest.mark.asyncio
    async def test_unknown_task_error(self, manager: TaskManager) -> None:
        """Test error when submitting unknown task."""
        with pytest.raises(ValueError, match="Unknown task"):
            await manager.submit("nonexistent")

    @pytest.mark.asyncio
    async def test_result_timeout(self, manager: TaskManager) -> None:
        """Test timeout waiting for result."""

        async def slow() -> None:
            await asyncio.sleep(10)

        manager.register("slow", slow)

        task_id = await manager.submit("slow")

        with pytest.raises(TimeoutError):
            await manager.get_result(task_id, timeout=0.1)
