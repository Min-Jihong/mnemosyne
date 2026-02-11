"""Pydantic models for aggregated events."""

import uuid
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AggregationType(StrEnum):
    MOUSE_TRAJECTORY = "mouse_trajectory"
    SCROLL_SEQUENCE = "scroll_sequence"
    TYPING_SEQUENCE = "typing_sequence"
    IDLE_PERIOD = "idle_period"


class Point(BaseModel):
    x: int
    y: int
    timestamp: float


class AggregatedEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    aggregation_type: AggregationType
    start_timestamp: float
    end_timestamp: float
    event_count: int = Field(description="Number of raw events aggregated")
    window_app: str = ""
    window_title: str = ""

    @property
    def duration_ms(self) -> float:
        return (self.end_timestamp - self.start_timestamp) * 1000

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "aggregation_type": self.aggregation_type.value,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "event_count": self.event_count,
            "window_app": self.window_app,
            "window_title": self.window_title,
            "duration_ms": self.duration_ms,
        }


class AggregatedMouseEvent(AggregatedEvent):
    """Uses Douglas-Peucker algorithm for path simplification."""

    aggregation_type: AggregationType = AggregationType.MOUSE_TRAJECTORY

    start_point: Point
    end_point: Point
    path: list[Point] = Field(default_factory=list)

    total_distance: float = Field(description="Total distance traveled in pixels")
    straight_line_distance: float = Field(description="Direct distance start to end")
    average_speed: float = Field(description="Average speed in pixels/second")
    max_speed: float = Field(description="Maximum speed in pixels/second")

    min_x: int = 0
    max_x: int = 0
    min_y: int = 0
    max_y: int = 0

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update(
            {
                "start_point": self.start_point.model_dump(),
                "end_point": self.end_point.model_dump(),
                "path": [p.model_dump() for p in self.path],
                "total_distance": self.total_distance,
                "straight_line_distance": self.straight_line_distance,
                "average_speed": self.average_speed,
                "max_speed": self.max_speed,
                "bounding_box": {
                    "min_x": self.min_x,
                    "max_x": self.max_x,
                    "min_y": self.min_y,
                    "max_y": self.max_y,
                },
            }
        )
        return d


class ScrollDirection(StrEnum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    MIXED = "mixed"


class AggregatedScrollEvent(AggregatedEvent):
    aggregation_type: AggregationType = AggregationType.SCROLL_SEQUENCE

    x: int = 0
    y: int = 0

    total_dx: int = Field(default=0, description="Total horizontal scroll")
    total_dy: int = Field(default=0, description="Total vertical scroll")

    primary_direction: ScrollDirection = ScrollDirection.DOWN

    scroll_events: int = Field(default=0, description="Number of scroll events")
    average_scroll_per_event: float = Field(default=0.0)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update(
            {
                "x": self.x,
                "y": self.y,
                "total_dx": self.total_dx,
                "total_dy": self.total_dy,
                "primary_direction": self.primary_direction.value,
                "scroll_events": self.scroll_events,
                "average_scroll_per_event": self.average_scroll_per_event,
            }
        )
        return d


class AggregatedTypingEvent(AggregatedEvent):
    aggregation_type: AggregationType = AggregationType.TYPING_SEQUENCE

    text: str = ""

    char_count: int = 0
    word_count: int = 0

    wpm: float = Field(default=0.0, description="Words per minute")
    cpm: float = Field(default=0.0, description="Characters per minute")

    backspace_count: int = Field(default=0, description="Number of backspaces")
    special_key_count: int = Field(default=0, description="Non-printable keys")

    average_key_interval_ms: float = Field(default=0.0)
    max_pause_ms: float = Field(default=0.0, description="Longest pause between keys")

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update(
            {
                "text": self.text,
                "char_count": self.char_count,
                "word_count": self.word_count,
                "wpm": self.wpm,
                "cpm": self.cpm,
                "backspace_count": self.backspace_count,
                "special_key_count": self.special_key_count,
                "average_key_interval_ms": self.average_key_interval_ms,
                "max_pause_ms": self.max_pause_ms,
            }
        )
        return d


class IdlePeriod(AggregatedEvent):
    aggregation_type: AggregationType = AggregationType.IDLE_PERIOD

    duration_seconds: float = 0.0

    last_action_type: str = ""
    next_action_type: str = ""

    is_short_pause: bool = Field(default=False, description="< 5 seconds")
    is_break: bool = Field(default=False, description="5-60 seconds")
    is_away: bool = Field(default=False, description="> 60 seconds")

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update(
            {
                "duration_seconds": self.duration_seconds,
                "last_action_type": self.last_action_type,
                "next_action_type": self.next_action_type,
                "is_short_pause": self.is_short_pause,
                "is_break": self.is_break,
                "is_away": self.is_away,
            }
        )
        return d


class AggregationConfig(BaseModel):
    mouse_window_ms: float = Field(default=500.0, description="Window for mouse aggregation")
    scroll_window_ms: float = Field(default=1000.0, description="Window for scroll aggregation")
    typing_window_ms: float = Field(default=2000.0, description="Window for typing aggregation")

    idle_threshold_seconds: float = Field(default=3.0, description="Min gap to consider idle")
    short_pause_max_seconds: float = Field(default=5.0)
    break_max_seconds: float = Field(default=60.0)

    douglas_peucker_epsilon: float = Field(
        default=5.0, description="Tolerance for Douglas-Peucker algorithm (pixels)"
    )
    min_path_points: int = Field(default=2, description="Minimum points to keep in path")
    max_path_points: int = Field(default=100, description="Maximum points to keep")

    aggregate_across_windows: bool = Field(
        default=False, description="Whether to aggregate events across different windows"
    )
    preserve_raw_events: bool = Field(
        default=True, description="Keep reference to original event IDs"
    )


class AggregationResult(BaseModel):
    session_id: str

    mouse_trajectories: list[AggregatedMouseEvent] = Field(default_factory=list)
    scroll_sequences: list[AggregatedScrollEvent] = Field(default_factory=list)
    typing_sequences: list[AggregatedTypingEvent] = Field(default_factory=list)
    idle_periods: list[IdlePeriod] = Field(default_factory=list)

    original_event_count: int = 0
    aggregated_event_count: int = 0
    compression_ratio: float = Field(default=0.0, description="Reduction in event count")

    processing_time_ms: float = 0.0

    @property
    def all_events(self) -> list[AggregatedEvent]:
        events: list[AggregatedEvent] = []
        events.extend(self.mouse_trajectories)
        events.extend(self.scroll_sequences)
        events.extend(self.typing_sequences)
        events.extend(self.idle_periods)
        return sorted(events, key=lambda e: e.start_timestamp)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "mouse_trajectories": [e.to_dict() for e in self.mouse_trajectories],
            "scroll_sequences": [e.to_dict() for e in self.scroll_sequences],
            "typing_sequences": [e.to_dict() for e in self.typing_sequences],
            "idle_periods": [e.to_dict() for e in self.idle_periods],
            "original_event_count": self.original_event_count,
            "aggregated_event_count": self.aggregated_event_count,
            "compression_ratio": self.compression_ratio,
            "processing_time_ms": self.processing_time_ms,
        }
