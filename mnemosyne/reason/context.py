import base64
from pathlib import Path
from typing import Any

from mnemosyne.store.models import StoredEvent, Screenshot


class ContextBuilder:
    
    def __init__(self, max_events: int = 10, include_screenshots: bool = True):
        self.max_events = max_events
        self.include_screenshots = include_screenshots
    
    def build_event_context(
        self,
        event: StoredEvent,
        surrounding_events: list[StoredEvent],
        screenshot: Screenshot | None = None,
    ) -> dict[str, Any]:
        context = {
            "current_event": self._format_event(event),
            "window": {
                "app": event.window_app,
                "title": event.window_title,
            },
            "surrounding_events": [
                self._format_event(e) for e in surrounding_events[-self.max_events:]
            ],
        }
        
        if screenshot and self.include_screenshots:
            context["screenshot"] = {
                "path": screenshot.filepath,
                "dimensions": f"{screenshot.width}x{screenshot.height}",
            }
        
        return context
    
    def _format_event(self, event: StoredEvent) -> dict[str, Any]:
        return {
            "type": event.action_type,
            "timestamp": event.timestamp,
            "data": event.data,
        }
    
    def build_prompt(
        self,
        event: StoredEvent,
        surrounding_events: list[StoredEvent],
        screenshot_path: str | None = None,
    ) -> str:
        lines = [
            "Analyze this user action and infer the intent behind it.",
            "",
            f"Current Action: {event.action_type}",
            f"Window: {event.window_app} - {event.window_title}",
            f"Action Data: {event.data}",
            "",
            "Recent Actions:",
        ]
        
        for e in surrounding_events[-5:]:
            lines.append(f"  - {e.action_type}: {e.data}")
        
        lines.extend([
            "",
            "Questions to answer:",
            "1. What is the user trying to accomplish?",
            "2. Why did they perform this specific action?",
            "3. What might they do next?",
            "",
            "Provide your analysis in JSON format with keys:",
            "- intent: The inferred intent (1-2 sentences)",
            "- reasoning: Why you think this (1-2 sentences)",
            "- confidence: low/medium/high",
            "- predicted_next: What they might do next",
        ])
        
        return "\n".join(lines)
    
    def encode_screenshot(self, filepath: str | Path) -> str | None:
        path = Path(filepath)
        if not path.exists():
            return None
        
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
