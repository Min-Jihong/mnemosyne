from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Any
import json

from mnemosyne.store.database import Database
from mnemosyne.store.models import StoredEvent, Screenshot


@dataclass
class DataPoint:
    event_id: str
    action_type: str
    action_data: dict[str, Any]
    window_app: str
    window_title: str
    screenshot_path: str | None
    intent: str | None
    context_events: list[dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "action_type": self.action_type,
            "action_data": self.action_data,
            "window_app": self.window_app,
            "window_title": self.window_title,
            "screenshot_path": self.screenshot_path,
            "intent": self.intent,
            "context_events": self.context_events,
        }


class BehaviorDataset:
    
    def __init__(
        self,
        database: Database,
        context_window: int = 5,
        include_screenshots: bool = True,
    ):
        self.database = database
        self.context_window = context_window
        self.include_screenshots = include_screenshots
    
    def iter_session(self, session_id: str) -> Iterator[DataPoint]:
        events = list(self.database.iter_events(session_id))
        screenshots = {
            s.id: s
            for s in self.database.get_screenshots_for_session(session_id)
        }
        
        for i, event in enumerate(events):
            context_start = max(0, i - self.context_window)
            context_events = [
                {
                    "action_type": e.action_type,
                    "data": e.data,
                    "window_app": e.window_app,
                }
                for e in events[context_start:i]
            ]
            
            screenshot_path = None
            if self.include_screenshots and event.screenshot_id:
                screenshot = screenshots.get(event.screenshot_id)
                if screenshot:
                    screenshot_path = screenshot.filepath
            
            yield DataPoint(
                event_id=event.id,
                action_type=event.action_type,
                action_data=event.data,
                window_app=event.window_app,
                window_title=event.window_title,
                screenshot_path=screenshot_path,
                intent=event.inferred_intent,
                context_events=context_events,
            )
    
    def export_to_jsonl(
        self,
        session_id: str,
        output_path: Path | str,
    ) -> int:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        with open(output_path, "w") as f:
            for datapoint in self.iter_session(session_id):
                f.write(json.dumps(datapoint.to_dict()) + "\n")
                count += 1
        
        return count
    
    def export_all_sessions(
        self,
        output_dir: Path | str,
    ) -> dict[str, int]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        for session in self.database.list_sessions(limit=1000):
            output_path = output_dir / f"{session.id}.jsonl"
            count = self.export_to_jsonl(session.id, output_path)
            results[session.id] = count
        
        return results
    
    def get_statistics(self, session_id: str) -> dict[str, Any]:
        events = list(self.database.iter_events(session_id))
        
        action_counts: dict[str, int] = {}
        app_counts: dict[str, int] = {}
        with_intent = 0
        
        for event in events:
            action_counts[event.action_type] = action_counts.get(event.action_type, 0) + 1
            app_counts[event.window_app] = app_counts.get(event.window_app, 0) + 1
            if event.inferred_intent:
                with_intent += 1
        
        return {
            "total_events": len(events),
            "action_distribution": action_counts,
            "app_distribution": app_counts,
            "events_with_intent": with_intent,
            "intent_coverage": with_intent / len(events) if events else 0,
        }
