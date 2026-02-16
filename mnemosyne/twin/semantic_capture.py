"""Semantic Work Capture - Understanding WHAT work is being done, not just actions."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class WorkType(str, Enum):
    CODE_WRITING = "code_writing"
    CODE_DEBUGGING = "code_debugging"
    CODE_REVIEW = "code_review"
    CODE_REFACTORING = "code_refactoring"

    DOCUMENT_DRAFTING = "document_drafting"
    DOCUMENT_EDITING = "document_editing"
    DOCUMENT_REVIEW = "document_review"

    EMAIL_COMPOSING = "email_composing"
    EMAIL_REPLYING = "email_replying"
    EMAIL_READING = "email_reading"

    RESEARCH = "research"
    PLANNING = "planning"
    COMMUNICATION = "communication"
    MEETING = "meeting"

    FILE_ORGANIZATION = "file_organization"
    SYSTEM_ADMIN = "system_admin"

    UNKNOWN = "unknown"


class ProjectContext(BaseModel):
    project_name: str = ""
    project_path: str = ""
    project_type: str = ""

    current_file: str = ""
    current_function: str = ""
    current_class: str = ""

    related_files: list[str] = Field(default_factory=list)

    git_branch: str = ""
    git_status: str = ""

    dependencies: list[str] = Field(default_factory=list)

    last_modified_files: list[str] = Field(default_factory=list)


class WorkUnit(BaseModel):
    id: str
    work_type: WorkType
    started_at: float
    ended_at: float | None = None

    description: str = ""
    goal: str = ""

    project_context: ProjectContext | None = None

    content_created: str = ""
    content_modified: str = ""

    input_events: list[str] = Field(default_factory=list)

    completion_percentage: float = 0.0
    outcome: str = ""

    reasoning: str = ""


class SemanticWorkCapture:
    def __init__(
        self,
        llm: Any = None,
        data_dir: Path | None = None,
    ):
        self.llm = llm
        self.data_dir = data_dir or Path.home() / ".mnemosyne" / "work_capture"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._current_work: WorkUnit | None = None
        self._work_history: list[WorkUnit] = []
        self._max_history = 1000

        self._content_buffer: list[str] = []
        self._last_work_detection_time: float = 0
        self._work_detection_interval: float = 30.0

    async def process_event(
        self,
        event: dict[str, Any],
        screen_context: dict[str, Any] | None = None,
    ) -> WorkUnit | None:
        should_detect = (
            time.time() - self._last_work_detection_time > self._work_detection_interval
            or self._is_significant_event(event)
        )

        if should_detect:
            await self._detect_work_type(event, screen_context)
            self._last_work_detection_time = time.time()

        if self._current_work:
            self._update_current_work(event, screen_context)

        return self._current_work

    def _is_significant_event(self, event: dict[str, Any]) -> bool:
        action = event.get("action_type", "")

        significant_actions = [
            "window_change",
            "hotkey",
        ]

        if action in significant_actions:
            return True

        if action == "key_type":
            text = event.get("data", {}).get("text", "")
            if len(text) > 50:
                return True

        return False

    async def _detect_work_type(
        self,
        event: dict[str, Any],
        screen_context: dict[str, Any] | None,
    ) -> None:
        app_name = event.get("window_app", "")
        window_title = event.get("window_title", "")
        action = event.get("action_type", "")

        detected_work_type = self._infer_work_type_from_context(
            app_name, window_title, action, screen_context
        )

        if self._current_work is None:
            self._start_new_work(detected_work_type, event, screen_context)
        elif self._current_work.work_type != detected_work_type:
            if self._is_work_transition(self._current_work.work_type, detected_work_type):
                await self._complete_current_work()
                self._start_new_work(detected_work_type, event, screen_context)

    def _infer_work_type_from_context(
        self,
        app_name: str,
        window_title: str,
        action: str,
        screen_context: dict[str, Any] | None,
    ) -> WorkType:
        app_lower = app_name.lower()
        title_lower = window_title.lower()

        code_apps = ["code", "pycharm", "intellij", "xcode", "sublime", "cursor", "vim", "nvim"]
        if any(app in app_lower for app in code_apps):
            if screen_context:
                task = screen_context.get("inferred_task", "").lower()
                if "debug" in task or "fix" in task or "error" in task:
                    return WorkType.CODE_DEBUGGING
                if "review" in task or "pr" in task:
                    return WorkType.CODE_REVIEW
                if "refactor" in task or "clean" in task:
                    return WorkType.CODE_REFACTORING
            return WorkType.CODE_WRITING

        if any(app in app_lower for app in ["mail", "outlook", "gmail"]):
            if "compose" in title_lower or "new" in title_lower:
                return WorkType.EMAIL_COMPOSING
            if "re:" in title_lower or "reply" in title_lower:
                return WorkType.EMAIL_REPLYING
            return WorkType.EMAIL_READING

        if any(app in app_lower for app in ["pages", "word", "docs", "notion", "obsidian"]):
            if screen_context:
                task = screen_context.get("inferred_task", "").lower()
                if "review" in task or "edit" in task:
                    return WorkType.DOCUMENT_EDITING
                if "draft" in task or "write" in task or "new" in task:
                    return WorkType.DOCUMENT_DRAFTING
            return WorkType.DOCUMENT_DRAFTING

        if any(app in app_lower for app in ["slack", "discord", "teams", "messages"]):
            return WorkType.COMMUNICATION

        if any(app in app_lower for app in ["zoom", "meet", "facetime"]):
            return WorkType.MEETING

        if any(app in app_lower for app in ["safari", "chrome", "firefox", "arc"]):
            return WorkType.RESEARCH

        if any(app in app_lower for app in ["finder", "explorer"]):
            return WorkType.FILE_ORGANIZATION

        if any(app in app_lower for app in ["terminal", "iterm", "warp"]):
            return WorkType.SYSTEM_ADMIN

        return WorkType.UNKNOWN

    def _start_new_work(
        self,
        work_type: WorkType,
        event: dict[str, Any],
        screen_context: dict[str, Any] | None,
    ) -> None:
        work_id = f"work_{int(time.time() * 1000)}"

        project_context = self._extract_project_context(event, screen_context)

        self._current_work = WorkUnit(
            id=work_id,
            work_type=work_type,
            started_at=time.time(),
            description=self._generate_work_description(work_type, event, screen_context),
            project_context=project_context,
        )

        if screen_context:
            self._current_work.goal = screen_context.get("inferred_task", "")

        self._content_buffer = []

    def _extract_project_context(
        self,
        event: dict[str, Any],
        screen_context: dict[str, Any] | None,
    ) -> ProjectContext:
        context = ProjectContext()

        window_title = event.get("window_title", "")

        file_indicators = [".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c", ".rb"]
        for indicator in file_indicators:
            if indicator in window_title:
                parts = window_title.split()
                for part in parts:
                    if indicator in part:
                        context.current_file = part.strip(" -—")
                        break
                break

        if " - " in window_title:
            parts = window_title.split(" - ")
            if len(parts) >= 2:
                context.project_name = parts[-1].strip()

        return context

    def _generate_work_description(
        self,
        work_type: WorkType,
        event: dict[str, Any],
        screen_context: dict[str, Any] | None,
    ) -> str:
        app_name = event.get("window_app", "unknown")

        descriptions = {
            WorkType.CODE_WRITING: f"Writing code in {app_name}",
            WorkType.CODE_DEBUGGING: f"Debugging in {app_name}",
            WorkType.CODE_REVIEW: f"Reviewing code in {app_name}",
            WorkType.CODE_REFACTORING: f"Refactoring code in {app_name}",
            WorkType.DOCUMENT_DRAFTING: f"Drafting document in {app_name}",
            WorkType.DOCUMENT_EDITING: f"Editing document in {app_name}",
            WorkType.EMAIL_COMPOSING: f"Composing email in {app_name}",
            WorkType.EMAIL_REPLYING: f"Replying to email in {app_name}",
            WorkType.EMAIL_READING: f"Reading email in {app_name}",
            WorkType.RESEARCH: f"Researching in {app_name}",
            WorkType.COMMUNICATION: f"Communicating via {app_name}",
            WorkType.MEETING: f"In meeting via {app_name}",
        }

        return descriptions.get(work_type, f"Working in {app_name}")

    def _is_work_transition(self, old_type: WorkType, new_type: WorkType) -> bool:
        same_category_groups = [
            {
                WorkType.CODE_WRITING,
                WorkType.CODE_DEBUGGING,
                WorkType.CODE_REVIEW,
                WorkType.CODE_REFACTORING,
            },
            {WorkType.DOCUMENT_DRAFTING, WorkType.DOCUMENT_EDITING, WorkType.DOCUMENT_REVIEW},
            {WorkType.EMAIL_COMPOSING, WorkType.EMAIL_REPLYING, WorkType.EMAIL_READING},
        ]

        for group in same_category_groups:
            if old_type in group and new_type in group:
                return False

        return True

    def _update_current_work(
        self,
        event: dict[str, Any],
        screen_context: dict[str, Any] | None,
    ) -> None:
        if not self._current_work:
            return

        self._current_work.input_events.append(event.get("id", ""))

        action = event.get("action_type", "")
        if action == "key_type":
            text = event.get("data", {}).get("text", "")
            self._content_buffer.append(text)
            self._current_work.content_created = "".join(self._content_buffer[-100:])

        if screen_context:
            if screen_context.get("inferred_task") and not self._current_work.goal:
                self._current_work.goal = screen_context["inferred_task"]

    async def _complete_current_work(self) -> None:
        if not self._current_work:
            return

        self._current_work.ended_at = time.time()

        if self.llm:
            self._current_work.outcome = await self._analyze_work_outcome()

        self._work_history.append(self._current_work)

        if len(self._work_history) > self._max_history:
            self._work_history = self._work_history[-self._max_history :]

        self._save_work_unit(self._current_work)
        self._current_work = None

    async def _analyze_work_outcome(self) -> str:
        if not self.llm or not self._current_work:
            return ""

        work = self._current_work
        duration_mins = (time.time() - work.started_at) / 60

        prompt = f"""Analyze this work session:
Type: {work.work_type.value}
Duration: {duration_mins:.1f} minutes
Goal: {work.goal}
Content created: {work.content_created[:500] if work.content_created else "N/A"}
Events: {len(work.input_events)} actions

In one sentence, summarize what was accomplished:"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.generate(messages)
            return response.strip()
        except Exception:
            return ""

    def _save_work_unit(self, work: WorkUnit) -> None:
        date_str = time.strftime("%Y-%m-%d")
        file_path = self.data_dir / f"work_{date_str}.jsonl"

        with open(file_path, "a") as f:
            f.write(work.model_dump_json() + "\n")

    async def capture_content(
        self,
        content: str,
        content_type: str,
        source: str = "",
    ) -> dict[str, Any]:
        if not self._current_work:
            return {"status": "no_active_work"}

        self._current_work.content_created = content[:5000]

        if self.llm:
            semantic_analysis = await self._analyze_content_semantics(content, content_type)
        else:
            semantic_analysis = {"type": content_type}

        return {
            "work_id": self._current_work.id,
            "content_length": len(content),
            "content_type": content_type,
            "semantics": semantic_analysis,
        }

    async def _analyze_content_semantics(
        self,
        content: str,
        content_type: str,
    ) -> dict[str, Any]:
        if not self.llm:
            return {}

        prompt = f"""Analyze this {content_type}:

{content[:2000]}

Return JSON with:
- purpose: What this content is for
- key_concepts: Main ideas/concepts (list)
- style: Writing/coding style characteristics
- completeness: How complete this seems (0-1)"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.generate(messages)
            return json.loads(response.strip())
        except Exception:
            return {"error": "analysis_failed"}

    def get_current_work(self) -> WorkUnit | None:
        return self._current_work

    def get_work_history(self, limit: int = 50) -> list[WorkUnit]:
        return self._work_history[-limit:]

    def get_work_summary(self, hours: float = 24) -> dict[str, Any]:
        cutoff = time.time() - (hours * 3600)
        recent_work = [w for w in self._work_history if w.started_at > cutoff]

        if not recent_work:
            return {"period_hours": hours, "work_units": 0}

        work_type_duration: dict[str, float] = {}
        for work in recent_work:
            duration = (work.ended_at or time.time()) - work.started_at
            work_type = work.work_type.value
            work_type_duration[work_type] = work_type_duration.get(work_type, 0) + duration

        total_duration = sum(work_type_duration.values())

        return {
            "period_hours": hours,
            "work_units": len(recent_work),
            "total_duration_hours": total_duration / 3600,
            "work_breakdown": {k: v / 3600 for k, v in work_type_duration.items()},
            "primary_work": max(work_type_duration.items(), key=lambda x: x[1])[0]
            if work_type_duration
            else None,
        }

    async def end_session(self) -> dict[str, Any]:
        if self._current_work:
            await self._complete_current_work()

        summary = self.get_work_summary(hours=8)
        return {"session_ended": True, "summary": summary}
