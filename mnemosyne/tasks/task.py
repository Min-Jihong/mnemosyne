"""Task definition and status types."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Coroutine


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """Task priority levels (higher = more urgent)."""

    LOW = 10
    NORMAL = 50
    HIGH = 75
    CRITICAL = 100


@dataclass
class TaskResult:
    """Result of a completed task."""

    task_id: str
    status: TaskStatus
    result: Any | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None


@dataclass
class Task:
    """Represents a background task."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    handler: Callable[..., Coroutine[Any, Any, Any]] | None = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING

    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    result: Any | None = None
    error: str | None = None
    progress: float = 0.0
    progress_message: str = ""

    retries: int = 0
    max_retries: int = 3
    timeout_seconds: float | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other: "Task") -> bool:
        return self.priority.value > other.priority.value

    def to_result(self) -> TaskResult:
        return TaskResult(
            task_id=self.id,
            status=self.status,
            result=self.result,
            error=self.error,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )

    def update_progress(self, progress: float, message: str = "") -> None:
        self.progress = min(max(progress, 0.0), 1.0)
        if message:
            self.progress_message = message
