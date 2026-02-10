from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import time
import uuid


class MemoryType(str, Enum):
    COMMAND = "command"
    CONVERSATION = "conversation"
    OBSERVATION = "observation"
    INSIGHT = "insight"
    PATTERN = "pattern"
    PREFERENCE = "preference"
    CORRECTION = "correction"


@dataclass
class Memory:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MemoryType = MemoryType.OBSERVATION
    content: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    embedding: list[float] | None = None
    tags: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "context": self.context,
            "importance": self.importance,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "tags": self.tags,
        }
    
    def access(self) -> None:
        self.last_accessed = time.time()
        self.access_count += 1
