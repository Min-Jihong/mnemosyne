"""Screen Understanding - Vision AI for semantic screen comprehension."""

from __future__ import annotations

import asyncio
import base64
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class WorkContext(str, Enum):
    CODING = "coding"
    WRITING = "writing"
    EMAIL = "email"
    BROWSING = "browsing"
    COMMUNICATION = "communication"
    DESIGN = "design"
    SPREADSHEET = "spreadsheet"
    TERMINAL = "terminal"
    FILE_MANAGEMENT = "file_management"
    MEETING = "meeting"
    UNKNOWN = "unknown"


class UIElementType(str, Enum):
    BUTTON = "button"
    INPUT = "input"
    TEXT = "text"
    LINK = "link"
    IMAGE = "image"
    MENU = "menu"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    TAB = "tab"
    CODE_EDITOR = "code_editor"
    TERMINAL = "terminal"
    CHAT_INPUT = "chat_input"
    FILE_LIST = "file_list"
    TOOLBAR = "toolbar"
    UNKNOWN = "unknown"


Bounds = tuple[int, int, int, int]  # (x, y, width, height)


@dataclass
class UIElement:
    element_type: UIElementType
    text: str
    bounds: Bounds
    confidence: float
    is_interactive: bool
    semantic_role: str = ""


@dataclass
class ScreenRegion:
    name: str
    bounds: tuple[int, int, int, int]
    purpose: str
    elements: list[UIElement] = field(default_factory=list)


class ScreenContext(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    app_name: str = ""
    window_title: str = ""
    work_context: WorkContext = WorkContext.UNKNOWN

    visible_text: list[str] = Field(default_factory=list)
    code_content: str | None = None
    document_content: str | None = None

    ui_elements: list[dict[str, Any]] = Field(default_factory=list)
    regions: list[dict[str, Any]] = Field(default_factory=list)

    focused_element: dict[str, Any] | None = None
    cursor_context: dict[str, Any] | None = None

    semantic_summary: str = ""
    inferred_task: str = ""
    task_confidence: float = 0.0


class ScreenUnderstanding:
    APP_CONTEXT_MAP = {
        "Visual Studio Code": WorkContext.CODING,
        "Code": WorkContext.CODING,
        "PyCharm": WorkContext.CODING,
        "IntelliJ": WorkContext.CODING,
        "Xcode": WorkContext.CODING,
        "Sublime Text": WorkContext.CODING,
        "Cursor": WorkContext.CODING,
        "Terminal": WorkContext.TERMINAL,
        "iTerm": WorkContext.TERMINAL,
        "Warp": WorkContext.TERMINAL,
        "Mail": WorkContext.EMAIL,
        "Outlook": WorkContext.EMAIL,
        "Gmail": WorkContext.EMAIL,
        "Slack": WorkContext.COMMUNICATION,
        "Discord": WorkContext.COMMUNICATION,
        "Microsoft Teams": WorkContext.COMMUNICATION,
        "Zoom": WorkContext.MEETING,
        "Google Meet": WorkContext.MEETING,
        "Safari": WorkContext.BROWSING,
        "Chrome": WorkContext.BROWSING,
        "Firefox": WorkContext.BROWSING,
        "Arc": WorkContext.BROWSING,
        "Pages": WorkContext.WRITING,
        "Word": WorkContext.WRITING,
        "Google Docs": WorkContext.WRITING,
        "Notion": WorkContext.WRITING,
        "Obsidian": WorkContext.WRITING,
        "Figma": WorkContext.DESIGN,
        "Sketch": WorkContext.DESIGN,
        "Numbers": WorkContext.SPREADSHEET,
        "Excel": WorkContext.SPREADSHEET,
        "Finder": WorkContext.FILE_MANAGEMENT,
    }

    def __init__(
        self,
        vision_llm: Any = None,
        ocr_engine: Any = None,
        cache_dir: Path | None = None,
    ):
        self.vision_llm = vision_llm
        self.ocr_engine = ocr_engine
        self.cache_dir = cache_dir or Path.home() / ".mnemosyne" / "screen_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._context_history: list[ScreenContext] = []
        self._max_history = 100

    async def understand_screen(
        self,
        screenshot_path: str | Path | None = None,
        screenshot_data: bytes | None = None,
        app_name: str = "",
        window_title: str = "",
        mouse_position: tuple[int, int] | None = None,
    ) -> ScreenContext:
        context = ScreenContext(app_name=app_name, window_title=window_title)
        context.work_context = self._infer_work_context(app_name, window_title)

        if screenshot_path or screenshot_data:
            if self.ocr_engine:
                ocr_result = await self._run_ocr(screenshot_path, screenshot_data)
                context.visible_text = ocr_result.get("text_lines", [])
                context.ui_elements = ocr_result.get("elements", [])

            if self.vision_llm:
                vision_result = await self._analyze_with_vision(
                    screenshot_path, screenshot_data, context.work_context, app_name, window_title
                )
                context.semantic_summary = vision_result.get("summary", "")
                context.inferred_task = vision_result.get("task", "")
                context.task_confidence = vision_result.get("confidence", 0.0)
                context.code_content = vision_result.get("code_content")
                context.document_content = vision_result.get("document_content")

                if vision_result.get("regions"):
                    context.regions = vision_result["regions"]

        if mouse_position and context.ui_elements:
            context.cursor_context = self._get_cursor_context(mouse_position, context.ui_elements)

        self._context_history.append(context)
        if len(self._context_history) > self._max_history:
            self._context_history = self._context_history[-self._max_history :]

        return context

    def _infer_work_context(self, app_name: str, window_title: str) -> WorkContext:
        for app_pattern, context in self.APP_CONTEXT_MAP.items():
            if app_pattern.lower() in app_name.lower():
                return context

        title_lower = window_title.lower()
        if any(ext in title_lower for ext in [".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp"]):
            return WorkContext.CODING
        if any(word in title_lower for word in ["inbox", "compose", "mail", "email"]):
            return WorkContext.EMAIL
        if any(word in title_lower for word in ["doc", "document", "draft", "writing"]):
            return WorkContext.WRITING

        return WorkContext.UNKNOWN

    async def _run_ocr(
        self,
        screenshot_path: str | Path | None,
        screenshot_data: bytes | None,
    ) -> dict[str, Any]:
        if not self.ocr_engine:
            return {"text_lines": [], "elements": []}

        try:
            if screenshot_path:
                result = await self.ocr_engine.process_file(str(screenshot_path))
            elif screenshot_data:
                result = await self.ocr_engine.process_bytes(screenshot_data)
            else:
                return {"text_lines": [], "elements": []}

            return result
        except Exception:
            return {"text_lines": [], "elements": []}

    async def _analyze_with_vision(
        self,
        screenshot_path: str | Path | None,
        screenshot_data: bytes | None,
        work_context: WorkContext,
        app_name: str,
        window_title: str,
    ) -> dict[str, Any]:
        if not self.vision_llm:
            return {}

        if screenshot_path:
            image_data = Path(screenshot_path).read_bytes()
        elif screenshot_data:
            image_data = screenshot_data
        else:
            return {}

        base64_image = base64.b64encode(image_data).decode("utf-8")

        system_prompt = f"""You are analyzing a screenshot to understand what the user is doing.
Current context: {work_context.value} in {app_name}

Analyze the screen and return JSON with:
- summary: Brief description of what's visible (1-2 sentences)
- task: What the user appears to be working on
- confidence: How confident you are (0.0-1.0)
- code_content: If coding, describe the code being written (null if not applicable)
- document_content: If writing, summarize the document content (null if not applicable)
- regions: List of semantic regions like [{{name: "editor", purpose: "main code editing", bounds: [x,y,w,h]}}]
- key_elements: Important UI elements visible

Focus on understanding WHAT work is being done, not just what's on screen."""

        user_prompt = f"Window: {window_title}\nApp: {app_name}\n\nAnalyze this screenshot:"

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image,
                            },
                        },
                    ],
                },
            ]

            response = await self.vision_llm.generate(messages)

            response_text = response.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            return json.loads(response_text)
        except Exception:
            return {"summary": "Unable to analyze screen", "task": "unknown", "confidence": 0.0}

    def _get_cursor_context(
        self,
        mouse_position: tuple[int, int],
        ui_elements: list[dict[str, Any]],
    ) -> dict[str, Any]:
        mx, my = mouse_position

        for element in ui_elements:
            bounds = element.get("bounds", [0, 0, 0, 0])
            x, y, w, h = bounds

            if x <= mx <= x + w and y <= my <= y + h:
                return {
                    "element": element,
                    "position_in_element": (mx - x, my - y),
                    "element_type": element.get("type", "unknown"),
                }

        return {"element": None, "position": mouse_position}

    async def understand_click(
        self,
        screenshot_path: str | Path | None,
        screenshot_data: bytes | None,
        click_position: tuple[int, int],
        app_name: str = "",
        window_title: str = "",
    ) -> dict[str, Any]:
        context = await self.understand_screen(
            screenshot_path=screenshot_path,
            screenshot_data=screenshot_data,
            app_name=app_name,
            window_title=window_title,
            mouse_position=click_position,
        )

        cursor_context = context.cursor_context or {}
        clicked_element = cursor_context.get("element")

        click_analysis = {
            "position": click_position,
            "app": app_name,
            "window": window_title,
            "work_context": context.work_context.value,
            "clicked_element": clicked_element,
            "task_context": context.inferred_task,
            "semantic_meaning": "",
        }

        if self.vision_llm and clicked_element:
            click_analysis["semantic_meaning"] = await self._analyze_click_meaning(
                clicked_element, context.inferred_task, context.work_context
            )

        return click_analysis

    async def _analyze_click_meaning(
        self,
        clicked_element: dict[str, Any],
        task_context: str,
        work_context: WorkContext,
    ) -> str:
        if not self.vision_llm:
            return ""

        element_text = clicked_element.get("text", "")
        element_type = clicked_element.get("type", "unknown")

        prompt = f"""User clicked on a {element_type} element with text "{element_text}".
Current task: {task_context}
Work context: {work_context.value}

In one sentence, explain WHY the user likely clicked this (what they're trying to accomplish):"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.vision_llm.generate(messages)
            return response.strip()
        except Exception:
            return ""

    async def understand_typing(
        self,
        screenshot_path: str | Path | None,
        screenshot_data: bytes | None,
        typed_text: str,
        app_name: str = "",
        window_title: str = "",
    ) -> dict[str, Any]:
        context = await self.understand_screen(
            screenshot_path=screenshot_path,
            screenshot_data=screenshot_data,
            app_name=app_name,
            window_title=window_title,
        )

        typing_analysis = {
            "typed_text": typed_text,
            "work_context": context.work_context.value,
            "content_type": self._classify_typed_content(typed_text, context.work_context),
            "task_context": context.inferred_task,
            "semantic_meaning": "",
        }

        if self.vision_llm:
            typing_analysis["semantic_meaning"] = await self._analyze_typing_meaning(
                typed_text, context.work_context, context.inferred_task
            )

        return typing_analysis

    def _classify_typed_content(self, text: str, work_context: WorkContext) -> str:
        if work_context == WorkContext.CODING:
            if any(
                kw in text
                for kw in ["def ", "function ", "class ", "const ", "let ", "var ", "import "]
            ):
                return "code_structure"
            if any(
                kw in text for kw in ["if ", "else ", "for ", "while ", "try ", "except ", "catch "]
            ):
                return "control_flow"
            if "=" in text:
                return "assignment"
            return "code"

        if work_context == WorkContext.EMAIL:
            if any(greeting in text.lower() for greeting in ["hi ", "hello ", "dear ", "hey "]):
                return "greeting"
            if any(
                closing in text.lower() for closing in ["regards", "sincerely", "thanks", "best"]
            ):
                return "closing"
            return "email_body"

        if work_context == WorkContext.TERMINAL:
            if text.startswith("cd "):
                return "navigation"
            if text.startswith("git "):
                return "version_control"
            return "command"

        return "text"

    async def _analyze_typing_meaning(
        self,
        typed_text: str,
        work_context: WorkContext,
        task_context: str,
    ) -> str:
        if not self.vision_llm:
            return ""

        prompt = f"""User typed: "{typed_text}"
Work context: {work_context.value}
Current task: {task_context}

In one sentence, explain what this typing accomplishes and why:"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.vision_llm.generate(messages)
            return response.strip()
        except Exception:
            return ""

    async def track_work_progress(
        self,
        time_window_seconds: float = 300,
    ) -> dict[str, Any]:
        if not self._context_history:
            return {"progress": "unknown", "summary": "No context history"}

        cutoff_time = time.time() - time_window_seconds
        recent_contexts = [c for c in self._context_history if c.timestamp > cutoff_time]

        if not recent_contexts:
            return {"progress": "idle", "summary": "No recent activity"}

        work_contexts = [c.work_context.value for c in recent_contexts]
        tasks = [c.inferred_task for c in recent_contexts if c.inferred_task]

        from collections import Counter

        context_counts = Counter(work_contexts)
        primary_context = context_counts.most_common(1)[0][0] if context_counts else "unknown"

        return {
            "primary_context": primary_context,
            "context_distribution": dict(context_counts),
            "recent_tasks": list(set(tasks))[-5:],
            "activity_count": len(recent_contexts),
            "time_window_seconds": time_window_seconds,
        }

    def get_current_context(self) -> ScreenContext | None:
        return self._context_history[-1] if self._context_history else None

    def get_context_summary(self) -> dict[str, Any]:
        if not self._context_history:
            return {"status": "no_history"}

        recent = self._context_history[-10:]

        return {
            "total_contexts": len(self._context_history),
            "recent_work_contexts": [c.work_context.value for c in recent],
            "recent_tasks": [c.inferred_task for c in recent if c.inferred_task],
            "current": {
                "app": recent[-1].app_name,
                "work_context": recent[-1].work_context.value,
                "task": recent[-1].inferred_task,
            },
        }
