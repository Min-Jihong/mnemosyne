"""
Mnemosyne Background Task System

A system for running tasks asynchronously in the background with:
- Priority-based scheduling
- Progress tracking
- Cancellation support
- Result caching
- Error handling

Usage:
    from mnemosyne.tasks import TaskManager, Task

    manager = TaskManager()

    # Define a task
    @manager.task(priority=TaskPriority.HIGH)
    async def analyze_session(session_id: str):
        ...

    # Run in background
    task_id = await manager.submit("analyze_session", session_id="abc123")

    # Check status
    status = manager.get_status(task_id)

    # Get result when done
    result = await manager.get_result(task_id)
"""

from mnemosyne.tasks.manager import TaskManager, get_task_manager
from mnemosyne.tasks.task import Task, TaskStatus, TaskPriority, TaskResult

__all__ = [
    "TaskManager",
    "get_task_manager",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskResult",
]
