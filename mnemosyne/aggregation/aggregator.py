"""Event aggregation engine for reducing noise and storage."""

import math
import time
from typing import TypeVar

from mnemosyne.aggregation.models import (
    AggregatedMouseEvent,
    AggregatedScrollEvent,
    AggregatedTypingEvent,
    AggregationConfig,
    AggregationResult,
    IdlePeriod,
    Point,
    ScrollDirection,
)
from mnemosyne.store.models import StoredEvent

T = TypeVar("T", bound=StoredEvent)


def _perpendicular_distance(
    point: tuple[int, int], line_start: tuple[int, int], line_end: tuple[int, int]
) -> float:
    """Calculate perpendicular distance from point to line segment (Douglas-Peucker helper)."""
    x, y = point
    x1, y1 = line_start
    x2, y2 = line_end

    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return math.sqrt((x - x1) ** 2 + (y - y1) ** 2)

    t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))

    proj_x = x1 + t * dx
    proj_y = y1 + t * dy

    return math.sqrt((x - proj_x) ** 2 + (y - proj_y) ** 2)


def _douglas_peucker(
    points: list[tuple[int, int, float]], epsilon: float
) -> list[tuple[int, int, float]]:
    """Simplify path using Douglas-Peucker algorithm. Points are (x, y, timestamp)."""
    if len(points) <= 2:
        return points

    max_dist = 0.0
    max_idx = 0

    start = (points[0][0], points[0][1])
    end = (points[-1][0], points[-1][1])

    for i in range(1, len(points) - 1):
        dist = _perpendicular_distance((points[i][0], points[i][1]), start, end)
        if dist > max_dist:
            max_dist = dist
            max_idx = i

    if max_dist > epsilon:
        left = _douglas_peucker(points[: max_idx + 1], epsilon)
        right = _douglas_peucker(points[max_idx:], epsilon)
        return left[:-1] + right
    else:
        return [points[0], points[-1]]


class EventAggregator:
    def __init__(self, config: AggregationConfig | None = None):
        self.config = config or AggregationConfig()

    async def aggregate_mouse_movements(
        self, events: list[StoredEvent]
    ) -> list[AggregatedMouseEvent]:
        mouse_events = [e for e in events if e.action_type == "mouse_move"]
        if len(mouse_events) < 2:
            return []

        result: list[AggregatedMouseEvent] = []
        current_group: list[StoredEvent] = []
        current_window = (mouse_events[0].window_app, mouse_events[0].window_title)

        for event in mouse_events:
            event_window = (event.window_app, event.window_title)

            should_split = False
            if current_group:
                time_gap = (event.timestamp - current_group[-1].timestamp) * 1000
                if time_gap > self.config.mouse_window_ms:
                    should_split = True
                if not self.config.aggregate_across_windows and event_window != current_window:
                    should_split = True

            if should_split and len(current_group) >= 2:
                aggregated = self._create_mouse_trajectory(current_group)
                if aggregated:
                    result.append(aggregated)
                current_group = []
                current_window = event_window

            current_group.append(event)
            if not self.config.aggregate_across_windows:
                current_window = event_window

        if len(current_group) >= 2:
            aggregated = self._create_mouse_trajectory(current_group)
            if aggregated:
                result.append(aggregated)

        return result

    def _create_mouse_trajectory(self, events: list[StoredEvent]) -> AggregatedMouseEvent | None:
        if len(events) < 2:
            return None

        points: list[tuple[int, int, float]] = []
        for e in events:
            x = e.data.get("x", 0)
            y = e.data.get("y", 0)
            points.append((x, y, e.timestamp))

        simplified = _douglas_peucker(points, self.config.douglas_peucker_epsilon)

        if len(simplified) > self.config.max_path_points:
            step = len(simplified) // self.config.max_path_points
            simplified = simplified[::step]
            if simplified[-1] != points[-1]:
                simplified.append(points[-1])

        total_distance = 0.0
        max_speed = 0.0
        speeds: list[float] = []

        for i in range(1, len(points)):
            dx = points[i][0] - points[i - 1][0]
            dy = points[i][1] - points[i - 1][1]
            dist = math.sqrt(dx * dx + dy * dy)
            total_distance += dist

            dt = points[i][2] - points[i - 1][2]
            if dt > 0:
                speed = dist / dt
                speeds.append(speed)
                max_speed = max(max_speed, speed)

        duration = points[-1][2] - points[0][2]
        avg_speed = total_distance / duration if duration > 0 else 0.0

        start_x, start_y = points[0][0], points[0][1]
        end_x, end_y = points[-1][0], points[-1][1]
        straight_dist = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        path_points = [Point(x=p[0], y=p[1], timestamp=p[2]) for p in simplified]

        return AggregatedMouseEvent(
            start_timestamp=events[0].timestamp,
            end_timestamp=events[-1].timestamp,
            event_count=len(events),
            window_app=events[0].window_app,
            window_title=events[0].window_title,
            start_point=Point(x=start_x, y=start_y, timestamp=points[0][2]),
            end_point=Point(x=end_x, y=end_y, timestamp=points[-1][2]),
            path=path_points,
            total_distance=total_distance,
            straight_line_distance=straight_dist,
            average_speed=avg_speed,
            max_speed=max_speed,
            min_x=min(xs),
            max_x=max(xs),
            min_y=min(ys),
            max_y=max(ys),
        )

    async def aggregate_scrolls(self, events: list[StoredEvent]) -> list[AggregatedScrollEvent]:
        scroll_events = [e for e in events if e.action_type == "mouse_scroll"]
        if not scroll_events:
            return []

        result: list[AggregatedScrollEvent] = []
        current_group: list[StoredEvent] = []
        current_window = (scroll_events[0].window_app, scroll_events[0].window_title)

        for event in scroll_events:
            event_window = (event.window_app, event.window_title)

            should_split = False
            if current_group:
                time_gap = (event.timestamp - current_group[-1].timestamp) * 1000
                if time_gap > self.config.scroll_window_ms:
                    should_split = True
                if not self.config.aggregate_across_windows and event_window != current_window:
                    should_split = True

            if should_split and current_group:
                aggregated = self._create_scroll_sequence(current_group)
                if aggregated:
                    result.append(aggregated)
                current_group = []
                current_window = event_window

            current_group.append(event)
            if not self.config.aggregate_across_windows:
                current_window = event_window

        if current_group:
            aggregated = self._create_scroll_sequence(current_group)
            if aggregated:
                result.append(aggregated)

        return result

    def _create_scroll_sequence(self, events: list[StoredEvent]) -> AggregatedScrollEvent | None:
        if not events:
            return None

        total_dx = 0
        total_dy = 0

        for e in events:
            total_dx += e.data.get("dx", 0)
            total_dy += e.data.get("dy", 0)

        if abs(total_dy) > abs(total_dx):
            direction = ScrollDirection.UP if total_dy > 0 else ScrollDirection.DOWN
        elif abs(total_dx) > abs(total_dy):
            direction = ScrollDirection.LEFT if total_dx < 0 else ScrollDirection.RIGHT
        else:
            direction = ScrollDirection.MIXED

        total_scroll = abs(total_dx) + abs(total_dy)
        avg_scroll = total_scroll / len(events) if events else 0.0

        return AggregatedScrollEvent(
            start_timestamp=events[0].timestamp,
            end_timestamp=events[-1].timestamp,
            event_count=len(events),
            window_app=events[0].window_app,
            window_title=events[0].window_title,
            x=events[0].data.get("x", 0),
            y=events[0].data.get("y", 0),
            total_dx=total_dx,
            total_dy=total_dy,
            primary_direction=direction,
            scroll_events=len(events),
            average_scroll_per_event=avg_scroll,
        )

    async def aggregate_keystrokes(self, events: list[StoredEvent]) -> list[AggregatedTypingEvent]:
        key_events = [e for e in events if e.action_type in ("key_press", "key_type")]
        if not key_events:
            return []

        result: list[AggregatedTypingEvent] = []
        current_group: list[StoredEvent] = []
        current_window = (key_events[0].window_app, key_events[0].window_title)

        for event in key_events:
            event_window = (event.window_app, event.window_title)

            should_split = False
            if current_group:
                time_gap = (event.timestamp - current_group[-1].timestamp) * 1000
                if time_gap > self.config.typing_window_ms:
                    should_split = True
                if not self.config.aggregate_across_windows and event_window != current_window:
                    should_split = True

            if should_split and current_group:
                aggregated = self._create_typing_sequence(current_group)
                if aggregated:
                    result.append(aggregated)
                current_group = []
                current_window = event_window

            current_group.append(event)
            if not self.config.aggregate_across_windows:
                current_window = event_window

        if current_group:
            aggregated = self._create_typing_sequence(current_group)
            if aggregated:
                result.append(aggregated)

        return result

    def _create_typing_sequence(self, events: list[StoredEvent]) -> AggregatedTypingEvent | None:
        if not events:
            return None

        text_parts: list[str] = []
        backspace_count = 0
        special_key_count = 0
        intervals: list[float] = []
        max_pause = 0.0

        for i, e in enumerate(events):
            key_char = e.data.get("key_char")
            key = e.data.get("key", "")

            if key_char and len(key_char) == 1:
                text_parts.append(key_char)
            elif key.lower() == "space":
                text_parts.append(" ")
            elif key.lower() in ("backspace", "delete"):
                backspace_count += 1
                if text_parts:
                    text_parts.pop()
            elif key.lower() in ("return", "enter"):
                text_parts.append("\n")
            elif key.lower() == "tab":
                text_parts.append("\t")
            else:
                special_key_count += 1

            if i > 0:
                interval = (e.timestamp - events[i - 1].timestamp) * 1000
                intervals.append(interval)
                max_pause = max(max_pause, interval)

        text = "".join(text_parts)
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0

        duration_seconds = events[-1].timestamp - events[0].timestamp
        duration_minutes = duration_seconds / 60 if duration_seconds > 0 else 0

        wpm = word_count / duration_minutes if duration_minutes > 0 else 0.0
        cpm = char_count / duration_minutes if duration_minutes > 0 else 0.0

        avg_interval = sum(intervals) / len(intervals) if intervals else 0.0

        return AggregatedTypingEvent(
            start_timestamp=events[0].timestamp,
            end_timestamp=events[-1].timestamp,
            event_count=len(events),
            window_app=events[0].window_app,
            window_title=events[0].window_title,
            text=text,
            char_count=char_count,
            word_count=word_count,
            wpm=wpm,
            cpm=cpm,
            backspace_count=backspace_count,
            special_key_count=special_key_count,
            average_key_interval_ms=avg_interval,
            max_pause_ms=max_pause,
        )

    async def detect_idle_periods(self, events: list[StoredEvent]) -> list[IdlePeriod]:
        if len(events) < 2:
            return []

        sorted_events = sorted(events, key=lambda e: e.timestamp)
        result: list[IdlePeriod] = []

        for i in range(1, len(sorted_events)):
            prev_event = sorted_events[i - 1]
            curr_event = sorted_events[i]

            gap_seconds = curr_event.timestamp - prev_event.timestamp

            if gap_seconds >= self.config.idle_threshold_seconds:
                is_short = gap_seconds < self.config.short_pause_max_seconds
                is_break = (
                    self.config.short_pause_max_seconds
                    <= gap_seconds
                    < self.config.break_max_seconds
                )
                is_away = gap_seconds >= self.config.break_max_seconds

                idle = IdlePeriod(
                    start_timestamp=prev_event.timestamp,
                    end_timestamp=curr_event.timestamp,
                    event_count=0,
                    window_app=prev_event.window_app,
                    window_title=prev_event.window_title,
                    duration_seconds=gap_seconds,
                    last_action_type=prev_event.action_type,
                    next_action_type=curr_event.action_type,
                    is_short_pause=is_short,
                    is_break=is_break,
                    is_away=is_away,
                )
                result.append(idle)

        return result

    async def aggregate_session(self, events: list[StoredEvent]) -> AggregationResult:
        start_time = time.time()

        mouse_trajectories = await self.aggregate_mouse_movements(events)
        scroll_sequences = await self.aggregate_scrolls(events)
        typing_sequences = await self.aggregate_keystrokes(events)
        idle_periods = await self.detect_idle_periods(events)

        aggregated_count = (
            len(mouse_trajectories)
            + len(scroll_sequences)
            + len(typing_sequences)
            + len(idle_periods)
        )

        compression = 1 - (aggregated_count / len(events)) if events else 0.0

        processing_time = (time.time() - start_time) * 1000

        session_id = events[0].session_id if events else ""

        return AggregationResult(
            session_id=session_id,
            mouse_trajectories=mouse_trajectories,
            scroll_sequences=scroll_sequences,
            typing_sequences=typing_sequences,
            idle_periods=idle_periods,
            original_event_count=len(events),
            aggregated_event_count=aggregated_count,
            compression_ratio=compression,
            processing_time_ms=processing_time,
        )
