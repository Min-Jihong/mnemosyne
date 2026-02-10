from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import json
import uuid


@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    started_at: float = 0.0
    ended_at: float | None = None
    event_count: int = 0
    screenshot_count: int = 0
    platform: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        if self.ended_at is None:
            return 0.0
        return self.ended_at - self.started_at
    
    @property
    def is_active(self) -> bool:
        return self.ended_at is None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "event_count": self.event_count,
            "screenshot_count": self.screenshot_count,
            "platform": self.platform,
            "metadata": json.dumps(self.metadata),
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "Session":
        return cls(
            id=row[0],
            name=row[1],
            started_at=row[2],
            ended_at=row[3],
            event_count=row[4],
            screenshot_count=row[5],
            platform=row[6],
            metadata=json.loads(row[7]) if row[7] else {},
        )


@dataclass
class StoredEvent:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    timestamp: float = 0.0
    action_type: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    screenshot_id: str | None = None
    window_app: str = ""
    window_title: str = ""
    inferred_intent: str | None = None
    reasoning: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "action_type": self.action_type,
            "data": json.dumps(self.data),
            "screenshot_id": self.screenshot_id,
            "window_app": self.window_app,
            "window_title": self.window_title,
            "inferred_intent": self.inferred_intent,
            "reasoning": self.reasoning,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "StoredEvent":
        return cls(
            id=row[0],
            session_id=row[1],
            timestamp=row[2],
            action_type=row[3],
            data=json.loads(row[4]) if row[4] else {},
            screenshot_id=row[5],
            window_app=row[6],
            window_title=row[7],
            inferred_intent=row[8],
            reasoning=row[9],
        )


@dataclass
class Screenshot:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    timestamp: float = 0.0
    filepath: str = ""
    width: int = 0
    height: int = 0
    file_size: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "filepath": self.filepath,
            "width": self.width,
            "height": self.height,
            "file_size": self.file_size,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "Screenshot":
        return cls(
            id=row[0],
            session_id=row[1],
            timestamp=row[2],
            filepath=row[3],
            width=row[4],
            height=row[5],
            file_size=row[6],
        )
