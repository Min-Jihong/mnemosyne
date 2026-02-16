"""Task Executor - Execute real work tasks using generated content and learned patterns."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    WRITE_CODE = "write_code"
    SEND_EMAIL = "send_email"
    WRITE_DOCUMENT = "write_document"
    REPLY_MESSAGE = "reply_message"
    FILE_OPERATION = "file_operation"
    GIT_OPERATION = "git_operation"
    TERMINAL_COMMAND = "terminal_command"
    BROWSER_ACTION = "browser_action"
    CUSTOM = "custom"


class ExecutionMode(str, Enum):
    AUTONOMOUS = "autonomous"
    SUPERVISED = "supervised"
    CONFIRMATION_REQUIRED = "confirmation_required"
    PREVIEW_ONLY = "preview_only"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStep(BaseModel):
    step_number: int
    action_type: str
    parameters: dict[str, Any]
    status: str = "pending"
    result: str = ""
    started_at: float | None = None
    completed_at: float | None = None


class TaskExecution(BaseModel):
    task_id: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING

    description: str = ""
    goal: str = ""

    execution_plan: list[ExecutionStep] = Field(default_factory=list)
    current_step: int = 0

    generated_content: str = ""

    started_at: float | None = None
    completed_at: float | None = None

    result: dict[str, Any] = Field(default_factory=dict)
    error: str = ""

    user_approved: bool = False
    approval_timestamp: float | None = None


class TaskExecutor:
    def __init__(
        self,
        content_generator: Any = None,
        screen_understanding: Any = None,
        decision_reasoner: Any = None,
        controller: Any = None,
        llm: Any = None,
        mode: ExecutionMode = ExecutionMode.CONFIRMATION_REQUIRED,
        data_dir: Path | None = None,
        on_confirmation_needed: Callable[[TaskExecution], None] | None = None,
        on_task_complete: Callable[[TaskExecution], None] | None = None,
    ):
        self.content_generator = content_generator
        self.screen_understanding = screen_understanding
        self.decision_reasoner = decision_reasoner
        self.controller = controller
        self.llm = llm
        self.mode = mode
        self.data_dir = data_dir or Path.home() / ".mnemosyne" / "task_executor"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._on_confirmation_needed = on_confirmation_needed
        self._on_task_complete = on_task_complete

        self._active_tasks: dict[str, TaskExecution] = {}
        self._completed_tasks: list[TaskExecution] = []
        self._max_completed = 500

    async def execute_task(
        self,
        task_type: TaskType,
        description: str,
        context: dict[str, Any] | None = None,
        content_params: dict[str, Any] | None = None,
    ) -> TaskExecution:
        task = TaskExecution(
            task_id=f"task_{int(time.time() * 1000)}",
            task_type=task_type,
            description=description,
            goal=description,
            started_at=time.time(),
        )

        self._active_tasks[task.task_id] = task

        task.status = TaskStatus.PLANNING
        task.execution_plan = await self._plan_execution(task, context, content_params)

        if task_type in (TaskType.WRITE_CODE, TaskType.SEND_EMAIL, TaskType.WRITE_DOCUMENT):
            task.generated_content = await self._generate_content(task, content_params)

        if self.mode == ExecutionMode.PREVIEW_ONLY:
            task.status = TaskStatus.COMPLETED
            task.result = {"preview": True, "content": task.generated_content}
            self._finalize_task(task)
            return task

        if self.mode == ExecutionMode.CONFIRMATION_REQUIRED:
            task.status = TaskStatus.AWAITING_CONFIRMATION
            if self._on_confirmation_needed:
                self._on_confirmation_needed(task)
            return task

        await self._execute_plan(task)

        return task

    async def _plan_execution(
        self,
        task: TaskExecution,
        context: dict[str, Any] | None,
        content_params: dict[str, Any] | None,
    ) -> list[ExecutionStep]:
        steps = []

        if task.task_type == TaskType.WRITE_CODE:
            steps = [
                ExecutionStep(
                    step_number=1, action_type="generate_code", parameters=content_params or {}
                ),
                ExecutionStep(step_number=2, action_type="navigate_to_editor", parameters={}),
                ExecutionStep(step_number=3, action_type="type_content", parameters={}),
                ExecutionStep(step_number=4, action_type="save_file", parameters={}),
            ]

        elif task.task_type == TaskType.SEND_EMAIL:
            steps = [
                ExecutionStep(
                    step_number=1, action_type="generate_email", parameters=content_params or {}
                ),
                ExecutionStep(step_number=2, action_type="open_email_composer", parameters={}),
                ExecutionStep(step_number=3, action_type="fill_recipient", parameters={}),
                ExecutionStep(step_number=4, action_type="fill_subject", parameters={}),
                ExecutionStep(step_number=5, action_type="type_body", parameters={}),
                ExecutionStep(step_number=6, action_type="review_and_send", parameters={}),
            ]

        elif task.task_type == TaskType.WRITE_DOCUMENT:
            steps = [
                ExecutionStep(
                    step_number=1, action_type="generate_document", parameters=content_params or {}
                ),
                ExecutionStep(step_number=2, action_type="open_document_app", parameters={}),
                ExecutionStep(step_number=3, action_type="type_content", parameters={}),
                ExecutionStep(step_number=4, action_type="save_document", parameters={}),
            ]

        elif task.task_type == TaskType.TERMINAL_COMMAND:
            command = (content_params or {}).get("command", "")
            steps = [
                ExecutionStep(step_number=1, action_type="open_terminal", parameters={}),
                ExecutionStep(
                    step_number=2, action_type="type_command", parameters={"command": command}
                ),
                ExecutionStep(step_number=3, action_type="execute_command", parameters={}),
            ]

        elif task.task_type == TaskType.GIT_OPERATION:
            operation = (content_params or {}).get("operation", "")
            steps = [
                ExecutionStep(step_number=1, action_type="open_terminal", parameters={}),
                ExecutionStep(
                    step_number=2, action_type="git_operation", parameters={"operation": operation}
                ),
            ]

        else:
            if self.llm:
                steps = await self._plan_with_llm(task, context, content_params)
            else:
                steps = [
                    ExecutionStep(step_number=1, action_type="unknown", parameters={}),
                ]

        return steps

    async def _plan_with_llm(
        self,
        task: TaskExecution,
        context: dict[str, Any] | None,
        content_params: dict[str, Any] | None,
    ) -> list[ExecutionStep]:
        if not self.llm:
            return []

        prompt = f"""Create an execution plan for this task:
Task: {task.description}
Type: {task.task_type.value}
Context: {json.dumps(context) if context else "None"}
Parameters: {json.dumps(content_params) if content_params else "None"}

Return a JSON array of steps, each with:
- step_number: int
- action_type: string (click, type, hotkey, navigate, etc.)
- parameters: object with any needed parameters

Keep it simple and actionable."""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.generate(messages)

            response_text = response.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            steps_data = json.loads(response_text)
            return [ExecutionStep(**step) for step in steps_data]
        except Exception:
            return [ExecutionStep(step_number=1, action_type="manual", parameters={})]

    async def _generate_content(
        self,
        task: TaskExecution,
        content_params: dict[str, Any] | None,
    ) -> str:
        params = content_params or {}

        if task.task_type == TaskType.WRITE_CODE and self.content_generator:
            result = await self.content_generator.generate_code(
                task_description=task.description,
                language=params.get("language", "python"),
                context=params.get("context"),
                existing_code=params.get("existing_code", ""),
            )
            return result.content

        elif task.task_type == TaskType.SEND_EMAIL and self.content_generator:
            result = await self.content_generator.generate_email(
                purpose=task.description,
                recipient=params.get("recipient", ""),
                context=params.get("context"),
                reply_to=params.get("reply_to", ""),
            )
            return result.content

        elif task.task_type == TaskType.WRITE_DOCUMENT and self.content_generator:
            result = await self.content_generator.generate_document(
                topic=task.description,
                document_type=params.get("document_type", "general"),
                context=params.get("context"),
                outline=params.get("outline"),
            )
            return result.content

        return ""

    async def approve_task(self, task_id: str, approved: bool = True) -> TaskExecution | None:
        task = self._active_tasks.get(task_id)
        if not task:
            return None

        if not approved:
            task.status = TaskStatus.CANCELLED
            self._finalize_task(task)
            return task

        task.user_approved = True
        task.approval_timestamp = time.time()

        await self._execute_plan(task)

        return task

    async def _execute_plan(self, task: TaskExecution) -> None:
        task.status = TaskStatus.EXECUTING

        for step in task.execution_plan:
            task.current_step = step.step_number
            step.status = "executing"
            step.started_at = time.time()

            try:
                result = await self._execute_step(task, step)
                step.result = result
                step.status = "completed"
            except Exception as e:
                step.status = "failed"
                step.result = str(e)
                task.status = TaskStatus.FAILED
                task.error = str(e)
                self._finalize_task(task)
                return

            step.completed_at = time.time()

        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        task.result = {"success": True, "content": task.generated_content}

        self._finalize_task(task)

    async def _execute_step(self, task: TaskExecution, step: ExecutionStep) -> str:
        action = step.action_type
        params = step.parameters

        if action in ("generate_code", "generate_email", "generate_document"):
            return "Content already generated"

        if not self.controller:
            return f"Would execute: {action}"

        if action == "type_content":
            content = task.generated_content
            if content:
                success = self.controller.type_text(content, interval=0.01)
                return "typed" if success else "failed to type"

        elif action == "type_command":
            command = params.get("command", "")
            if command:
                success = self.controller.type_text(command)
                if success:
                    self.controller.press_key("return")
                return "executed" if success else "failed"

        elif action == "save_file":
            success = self.controller.hotkey("cmd", "s")
            return "saved" if success else "failed"

        elif action == "navigate_to_editor":
            return "navigation would be implemented"

        elif action == "open_email_composer":
            success = self.controller.hotkey("cmd", "n")
            return "opened" if success else "failed"

        elif action == "execute_command":
            self.controller.press_key("return")
            return "executed"

        return f"Step {action} executed"

    def _finalize_task(self, task: TaskExecution) -> None:
        if task.task_id in self._active_tasks:
            del self._active_tasks[task.task_id]

        self._completed_tasks.append(task)
        if len(self._completed_tasks) > self._max_completed:
            self._completed_tasks = self._completed_tasks[-self._max_completed :]

        self._save_task(task)

        if self._on_task_complete:
            self._on_task_complete(task)

    def _save_task(self, task: TaskExecution) -> None:
        date_str = time.strftime("%Y-%m-%d")
        file_path = self.data_dir / f"tasks_{date_str}.jsonl"

        with open(file_path, "a") as f:
            f.write(task.model_dump_json() + "\n")

    def get_task(self, task_id: str) -> TaskExecution | None:
        if task_id in self._active_tasks:
            return self._active_tasks[task_id]

        return next((t for t in self._completed_tasks if t.task_id == task_id), None)

    def get_pending_approvals(self) -> list[TaskExecution]:
        return [
            t for t in self._active_tasks.values() if t.status == TaskStatus.AWAITING_CONFIRMATION
        ]

    def get_active_tasks(self) -> list[TaskExecution]:
        return list(self._active_tasks.values())

    def get_execution_stats(self) -> dict[str, Any]:
        completed = [t for t in self._completed_tasks if t.status == TaskStatus.COMPLETED]
        failed = [t for t in self._completed_tasks if t.status == TaskStatus.FAILED]

        type_counts = {}
        for t in self._completed_tasks:
            tt = t.task_type.value
            type_counts[tt] = type_counts.get(tt, 0) + 1

        return {
            "total_completed": len(completed),
            "total_failed": len(failed),
            "active_tasks": len(self._active_tasks),
            "pending_approvals": len(self.get_pending_approvals()),
            "success_rate": len(completed) / (len(completed) + len(failed))
            if completed or failed
            else 0,
            "tasks_by_type": type_counts,
        }

    async def cancel_task(self, task_id: str) -> bool:
        task = self._active_tasks.get(task_id)
        if not task:
            return False

        task.status = TaskStatus.CANCELLED
        self._finalize_task(task)
        return True
