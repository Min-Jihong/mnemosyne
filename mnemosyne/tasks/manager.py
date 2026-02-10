"""Task manager for background execution."""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from heapq import heappush, heappop
from typing import Any, Callable, Coroutine

from mnemosyne.tasks.task import Task, TaskPriority, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class TaskDefinition:
    """Definition of a registered task type."""

    name: str
    handler: Callable[..., Coroutine[Any, Any, Any]]
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: float | None = None
    max_retries: int = 3


class TaskManager:
    """
    Manages background task execution.

    Features:
    - Priority queue scheduling
    - Concurrent execution with configurable workers
    - Progress tracking
    - Cancellation support
    - Automatic retries
    - Result caching
    """

    def __init__(
        self,
        max_workers: int = 5,
        result_ttl_seconds: float = 3600,
    ) -> None:
        self._max_workers = max_workers
        self._result_ttl = result_ttl_seconds

        self._definitions: dict[str, TaskDefinition] = {}
        self._tasks: dict[str, Task] = {}
        self._queue: list[Task] = []  # Priority queue (min-heap, but Task.__lt__ inverts)
        self._running: set[str] = set()
        self._results: dict[str, TaskResult] = {}

        self._workers: list[asyncio.Task] = []
        self._running_flag = False
        self._queue_event = asyncio.Event()

    def register(
        self,
        name: str,
        handler: Callable[..., Coroutine[Any, Any, Any]],
        *,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float | None = None,
        max_retries: int = 3,
    ) -> None:
        """Register a task handler."""
        self._definitions[name] = TaskDefinition(
            name=name,
            handler=handler,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
        )
        logger.debug(f"Registered task: {name}")

    def task(
        self,
        name: str | None = None,
        *,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float | None = None,
        max_retries: int = 3,
    ) -> Callable:
        """Decorator to register a task handler."""

        def decorator(
            handler: Callable[..., Coroutine[Any, Any, Any]]
        ) -> Callable[..., Coroutine[Any, Any, Any]]:
            task_name = name or handler.__name__
            self.register(
                task_name,
                handler,
                priority=priority,
                timeout=timeout,
                max_retries=max_retries,
            )
            return handler

        return decorator

    async def submit(
        self,
        task_name: str,
        *args: Any,
        priority: TaskPriority | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Submit a task for background execution.

        Args:
            task_name: Name of the registered task
            *args: Positional arguments for the handler
            priority: Override default priority
            **kwargs: Keyword arguments for the handler

        Returns:
            Task ID
        """
        definition = self._definitions.get(task_name)
        if definition is None:
            raise ValueError(f"Unknown task: {task_name}")

        task = Task(
            name=task_name,
            handler=definition.handler,
            args=args,
            kwargs=kwargs,
            priority=priority or definition.priority,
            timeout_seconds=definition.timeout,
            max_retries=definition.max_retries,
            status=TaskStatus.QUEUED,
        )

        self._tasks[task.id] = task
        heappush(self._queue, task)
        self._queue_event.set()

        logger.info(f"Task submitted: {task.id} ({task_name})")
        return task.id

    async def submit_raw(
        self,
        handler: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        name: str = "anonymous",
        priority: TaskPriority = TaskPriority.NORMAL,
        **kwargs: Any,
    ) -> str:
        """Submit a one-off task without registering."""
        task = Task(
            name=name,
            handler=handler,
            args=args,
            kwargs=kwargs,
            priority=priority,
            status=TaskStatus.QUEUED,
        )

        self._tasks[task.id] = task
        heappush(self._queue, task)
        self._queue_event.set()

        return task.id

    def get_status(self, task_id: str) -> TaskStatus | None:
        """Get task status."""
        task = self._tasks.get(task_id)
        return task.status if task else None

    def get_progress(self, task_id: str) -> tuple[float, str]:
        """Get task progress (0.0-1.0) and message."""
        task = self._tasks.get(task_id)
        if task:
            return task.progress, task.progress_message
        return 0.0, ""

    async def get_result(
        self,
        task_id: str,
        timeout: float | None = None,
    ) -> TaskResult:
        """
        Wait for and get task result.

        Args:
            task_id: Task ID to wait for
            timeout: Maximum time to wait (seconds)

        Returns:
            TaskResult

        Raises:
            TimeoutError: If timeout exceeded
        """
        if task_id in self._results:
            return self._results[task_id]

        task = self._tasks.get(task_id)
        if task is None:
            raise ValueError(f"Unknown task: {task_id}")

        start = datetime.now()
        while task.status not in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ):
            if timeout:
                elapsed = (datetime.now() - start).total_seconds()
                if elapsed >= timeout:
                    raise TimeoutError(f"Task {task_id} did not complete in {timeout}s")

            await asyncio.sleep(0.1)

        return task.to_result()

    async def cancel(self, task_id: str) -> bool:
        """
        Cancel a task.

        Returns True if task was cancelled, False if already completed.
        """
        task = self._tasks.get(task_id)
        if task is None:
            return False

        if task.status in (TaskStatus.PENDING, TaskStatus.QUEUED):
            task.status = TaskStatus.CANCELLED
            logger.info(f"Task cancelled: {task_id}")
            return True

        if task.status == TaskStatus.RUNNING:
            task.status = TaskStatus.CANCELLED
            logger.info(f"Task marked for cancellation: {task_id}")
            return True

        return False

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(
        self,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        """List tasks, optionally filtered by status."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    async def start(self) -> None:
        """Start the task manager workers."""
        if self._running_flag:
            return

        self._running_flag = True

        for i in range(self._max_workers):
            worker = asyncio.create_task(self._worker_loop(i))
            self._workers.append(worker)

        logger.info(f"Task manager started with {self._max_workers} workers")

    async def stop(self, wait: bool = True) -> None:
        """
        Stop the task manager.

        Args:
            wait: If True, wait for running tasks to complete
        """
        self._running_flag = False
        self._queue_event.set()

        if wait:
            for task_id in list(self._running):
                task = self._tasks.get(task_id)
                if task:
                    while task.status == TaskStatus.RUNNING:
                        await asyncio.sleep(0.1)

        for worker in self._workers:
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass

        self._workers.clear()
        logger.info("Task manager stopped")

    async def _worker_loop(self, worker_id: int) -> None:
        """Worker coroutine that processes tasks."""
        while self._running_flag:
            await self._queue_event.wait()

            if not self._queue:
                self._queue_event.clear()
                continue

            if len(self._running) >= self._max_workers:
                await asyncio.sleep(0.1)
                continue

            try:
                task = heappop(self._queue)
            except IndexError:
                self._queue_event.clear()
                continue

            if task.status == TaskStatus.CANCELLED:
                continue

            await self._execute_task(task, worker_id)

    async def _execute_task(self, task: Task, worker_id: int) -> None:
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self._running.add(task.id)

        logger.debug(f"Worker {worker_id} executing task: {task.id} ({task.name})")

        try:
            if task.handler is None:
                raise ValueError("Task has no handler")

            if task.timeout_seconds:
                result = await asyncio.wait_for(
                    task.handler(*task.args, **task.kwargs),
                    timeout=task.timeout_seconds,
                )
            else:
                result = await task.handler(*task.args, **task.kwargs)

            task.result = result
            task.status = TaskStatus.COMPLETED

        except asyncio.TimeoutError:
            task.error = f"Task timed out after {task.timeout_seconds}s"
            task.status = TaskStatus.FAILED
            logger.error(f"Task {task.id} timed out")

        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            logger.info(f"Task {task.id} was cancelled")

        except Exception as e:
            task.error = str(e)

            if task.retries < task.max_retries:
                task.retries += 1
                task.status = TaskStatus.QUEUED
                heappush(self._queue, task)
                self._queue_event.set()
                logger.warning(
                    f"Task {task.id} failed, retrying ({task.retries}/{task.max_retries})"
                )
            else:
                task.status = TaskStatus.FAILED
                logger.error(f"Task {task.id} failed: {e}")

        finally:
            task.completed_at = datetime.now()
            self._running.discard(task.id)
            self._results[task.id] = task.to_result()

    def stats(self) -> dict[str, Any]:
        """Get task manager statistics."""
        status_counts = defaultdict(int)
        for task in self._tasks.values():
            status_counts[task.status.value] += 1

        return {
            "total_tasks": len(self._tasks),
            "queued": len(self._queue),
            "running": len(self._running),
            "workers": self._max_workers,
            "by_status": dict(status_counts),
        }


_manager: TaskManager | None = None


def get_task_manager() -> TaskManager:
    """Get or create the global task manager."""
    global _manager
    if _manager is None:
        _manager = TaskManager()
    return _manager
