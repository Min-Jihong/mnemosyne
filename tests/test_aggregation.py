"""Tests for aggregation module - event aggregation and path simplification."""

import pytest

from mnemosyne.aggregation.aggregator import (
    EventAggregator,
    _perpendicular_distance,
    _douglas_peucker,
)
from mnemosyne.aggregation.models import (
    AggregationConfig,
    AggregatedMouseEvent,
    AggregatedScrollEvent,
    AggregatedTypingEvent,
    IdlePeriod,
    Point,
    ScrollDirection,
    AggregationType,
)
from mnemosyne.store.models import StoredEvent


def make_mouse_event(
    x: int, y: int, timestamp: float, session_id: str = "test", window_app: str = "TestApp"
) -> StoredEvent:
    return StoredEvent(
        session_id=session_id,
        timestamp=timestamp,
        action_type="mouse_move",
        data={"x": x, "y": y},
        window_app=window_app,
        window_title="Test Window",
    )


def make_scroll_event(
    dx: int, dy: int, timestamp: float, x: int = 100, y: int = 100
) -> StoredEvent:
    return StoredEvent(
        session_id="test",
        timestamp=timestamp,
        action_type="mouse_scroll",
        data={"dx": dx, "dy": dy, "x": x, "y": y},
        window_app="TestApp",
        window_title="Test Window",
    )


def make_key_event(
    key: str, timestamp: float, key_char: str | None = None
) -> StoredEvent:
    return StoredEvent(
        session_id="test",
        timestamp=timestamp,
        action_type="key_press",
        data={"key": key, "key_char": key_char},
        window_app="TestApp",
        window_title="Test Window",
    )


class TestPerpendicularDistance:

    def test_point_on_line(self):
        dist = _perpendicular_distance((5, 5), (0, 0), (10, 10))
        assert dist == pytest.approx(0.0, abs=0.01)

    def test_point_above_line(self):
        dist = _perpendicular_distance((5, 10), (0, 0), (10, 0))
        assert dist == pytest.approx(10.0, abs=0.01)

    def test_point_below_line(self):
        dist = _perpendicular_distance((5, -5), (0, 0), (10, 0))
        assert dist == pytest.approx(5.0, abs=0.01)

    def test_same_start_end(self):
        dist = _perpendicular_distance((5, 5), (0, 0), (0, 0))
        assert dist == pytest.approx(7.07, abs=0.1)

    def test_horizontal_line(self):
        dist = _perpendicular_distance((50, 20), (0, 0), (100, 0))
        assert dist == pytest.approx(20.0, abs=0.01)


class TestDouglasPeucker:

    def test_two_points_unchanged(self):
        points = [(0, 0, 0.0), (10, 10, 1.0)]
        result = _douglas_peucker(points, epsilon=5.0)
        assert len(result) == 2

    def test_straight_line_simplified(self):
        points = [(0, 0, 0.0), (5, 5, 0.5), (10, 10, 1.0)]
        result = _douglas_peucker(points, epsilon=1.0)
        assert len(result) == 2

    def test_zigzag_preserved(self):
        points = [(0, 0, 0.0), (5, 10, 0.5), (10, 0, 1.0)]
        result = _douglas_peucker(points, epsilon=1.0)
        assert len(result) == 3

    def test_complex_path(self):
        points = [
            (0, 0, 0.0),
            (10, 0, 0.1),
            (20, 0, 0.2),
            (30, 0, 0.3),
            (40, 0, 0.4),
            (50, 50, 0.5),
            (60, 50, 0.6),
        ]
        result = _douglas_peucker(points, epsilon=5.0)
        assert len(result) < len(points)
        assert result[0] == points[0]
        assert result[-1] == points[-1]

    def test_high_epsilon_simplifies_more(self):
        points = [(0, 0, 0.0), (5, 10, 0.5), (10, 0, 1.0), (15, 10, 1.5), (20, 0, 2.0)]
        result_low = _douglas_peucker(points, epsilon=1.0)
        result_high = _douglas_peucker(points, epsilon=20.0)
        assert len(result_high) <= len(result_low)


class TestMouseAggregation:

    @pytest.mark.asyncio
    async def test_aggregate_simple_trajectory(self):
        aggregator = EventAggregator()
        events = [
            make_mouse_event(0, 0, 1.0),
            make_mouse_event(10, 10, 1.05),
            make_mouse_event(20, 20, 1.1),
            make_mouse_event(30, 30, 1.15),
        ]
        
        result = await aggregator.aggregate_mouse_movements(events)
        
        assert len(result) == 1
        trajectory = result[0]
        assert trajectory.event_count == 4
        assert trajectory.start_point.x == 0
        assert trajectory.end_point.x == 30

    @pytest.mark.asyncio
    async def test_aggregate_splits_on_time_gap(self):
        config = AggregationConfig(mouse_window_ms=100)
        aggregator = EventAggregator(config)
        events = [
            make_mouse_event(0, 0, 1.0),
            make_mouse_event(10, 10, 1.05),
            make_mouse_event(100, 100, 2.0),
            make_mouse_event(110, 110, 2.05),
        ]
        
        result = await aggregator.aggregate_mouse_movements(events)
        
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_aggregate_splits_on_window_change(self):
        config = AggregationConfig(aggregate_across_windows=False)
        aggregator = EventAggregator(config)
        events = [
            make_mouse_event(0, 0, 1.0, window_app="App1"),
            make_mouse_event(10, 10, 1.05, window_app="App1"),
            make_mouse_event(20, 20, 1.1, window_app="App2"),
            make_mouse_event(30, 30, 1.15, window_app="App2"),
        ]
        
        result = await aggregator.aggregate_mouse_movements(events)
        
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_aggregate_calculates_distance(self):
        aggregator = EventAggregator()
        events = [
            make_mouse_event(0, 0, 1.0),
            make_mouse_event(100, 0, 1.1),
        ]
        
        result = await aggregator.aggregate_mouse_movements(events)
        
        assert len(result) == 1
        assert result[0].total_distance == pytest.approx(100.0, abs=0.1)
        assert result[0].straight_line_distance == pytest.approx(100.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_aggregate_calculates_speed(self):
        aggregator = EventAggregator()
        events = [
            make_mouse_event(0, 0, 1.0),
            make_mouse_event(100, 0, 2.0),
        ]
        
        result = await aggregator.aggregate_mouse_movements(events)
        
        assert len(result) == 1
        assert result[0].average_speed == pytest.approx(100.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_empty_events(self):
        aggregator = EventAggregator()
        result = await aggregator.aggregate_mouse_movements([])
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_single_event(self):
        aggregator = EventAggregator()
        events = [make_mouse_event(0, 0, 1.0)]
        result = await aggregator.aggregate_mouse_movements(events)
        assert len(result) == 0


class TestScrollAggregation:

    @pytest.mark.asyncio
    async def test_aggregate_vertical_scroll(self):
        aggregator = EventAggregator()
        events = [
            make_scroll_event(0, 10, 1.0),
            make_scroll_event(0, 10, 1.1),
            make_scroll_event(0, 10, 1.2),
        ]
        
        result = await aggregator.aggregate_scrolls(events)
        
        assert len(result) == 1
        assert result[0].total_dy == 30
        assert result[0].primary_direction == ScrollDirection.UP

    @pytest.mark.asyncio
    async def test_aggregate_horizontal_scroll(self):
        aggregator = EventAggregator()
        events = [
            make_scroll_event(10, 0, 1.0),
            make_scroll_event(10, 0, 1.1),
        ]
        
        result = await aggregator.aggregate_scrolls(events)
        
        assert len(result) == 1
        assert result[0].total_dx == 20
        assert result[0].primary_direction == ScrollDirection.RIGHT

    @pytest.mark.asyncio
    async def test_scroll_direction_down(self):
        aggregator = EventAggregator()
        events = [
            make_scroll_event(0, -10, 1.0),
            make_scroll_event(0, -10, 1.1),
        ]
        
        result = await aggregator.aggregate_scrolls(events)
        
        assert result[0].primary_direction == ScrollDirection.DOWN

    @pytest.mark.asyncio
    async def test_scroll_direction_left(self):
        aggregator = EventAggregator()
        events = [
            make_scroll_event(-10, 0, 1.0),
            make_scroll_event(-10, 0, 1.1),
        ]
        
        result = await aggregator.aggregate_scrolls(events)
        
        assert result[0].primary_direction == ScrollDirection.LEFT

    @pytest.mark.asyncio
    async def test_scroll_direction_mixed(self):
        aggregator = EventAggregator()
        events = [
            make_scroll_event(10, 10, 1.0),
        ]
        
        result = await aggregator.aggregate_scrolls(events)
        
        assert result[0].primary_direction == ScrollDirection.MIXED

    @pytest.mark.asyncio
    async def test_empty_scroll_events(self):
        aggregator = EventAggregator()
        result = await aggregator.aggregate_scrolls([])
        assert len(result) == 0


class TestKeystrokeAggregation:

    @pytest.mark.asyncio
    async def test_aggregate_simple_typing(self):
        aggregator = EventAggregator()
        events = [
            make_key_event("h", 1.0, "h"),
            make_key_event("e", 1.1, "e"),
            make_key_event("l", 1.2, "l"),
            make_key_event("l", 1.3, "l"),
            make_key_event("o", 1.4, "o"),
        ]
        
        result = await aggregator.aggregate_keystrokes(events)
        
        assert len(result) == 1
        assert result[0].text == "hello"
        assert result[0].char_count == 5

    @pytest.mark.asyncio
    async def test_aggregate_with_space(self):
        aggregator = EventAggregator()
        events = [
            make_key_event("h", 1.0, "h"),
            make_key_event("i", 1.1, "i"),
            make_key_event("space", 1.2, None),
            make_key_event("y", 1.3, "y"),
            make_key_event("o", 1.4, "o"),
        ]
        
        result = await aggregator.aggregate_keystrokes(events)
        
        assert result[0].text == "hi yo"
        assert result[0].word_count == 2

    @pytest.mark.asyncio
    async def test_aggregate_with_backspace(self):
        aggregator = EventAggregator()
        events = [
            make_key_event("h", 1.0, "h"),
            make_key_event("e", 1.1, "e"),
            make_key_event("backspace", 1.2, None),
            make_key_event("i", 1.3, "i"),
        ]
        
        result = await aggregator.aggregate_keystrokes(events)
        
        assert result[0].text == "hi"
        assert result[0].backspace_count == 1

    @pytest.mark.asyncio
    async def test_aggregate_with_enter(self):
        aggregator = EventAggregator()
        events = [
            make_key_event("a", 1.0, "a"),
            make_key_event("return", 1.1, None),
            make_key_event("b", 1.2, "b"),
        ]
        
        result = await aggregator.aggregate_keystrokes(events)
        
        assert result[0].text == "a\nb"

    @pytest.mark.asyncio
    async def test_aggregate_calculates_wpm(self):
        aggregator = EventAggregator()
        events = [
            make_key_event("h", 1.0, "h"),
            make_key_event("i", 1.1, "i"),
            make_key_event("space", 1.2, None),
            make_key_event("y", 1.3, "y"),
            make_key_event("o", 61.0, "o"),
        ]
        
        result = await aggregator.aggregate_keystrokes(events)
        
        assert result[0].wpm > 0
        assert result[0].cpm > 0

    @pytest.mark.asyncio
    async def test_aggregate_special_keys(self):
        aggregator = EventAggregator()
        events = [
            make_key_event("ctrl", 1.0, None),
            make_key_event("c", 1.1, None),
        ]
        
        result = await aggregator.aggregate_keystrokes(events)
        
        assert result[0].special_key_count >= 1

    @pytest.mark.asyncio
    async def test_empty_keystroke_events(self):
        aggregator = EventAggregator()
        result = await aggregator.aggregate_keystrokes([])
        assert len(result) == 0


class TestIdlePeriodDetection:

    @pytest.mark.asyncio
    async def test_detect_idle_period(self):
        config = AggregationConfig(idle_threshold_seconds=1.0)
        aggregator = EventAggregator(config)
        events = [
            make_mouse_event(0, 0, 1.0),
            make_mouse_event(10, 10, 5.0),
        ]
        
        result = await aggregator.detect_idle_periods(events)
        
        assert len(result) == 1
        assert result[0].duration_seconds == pytest.approx(4.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_no_idle_period(self):
        config = AggregationConfig(idle_threshold_seconds=5.0)
        aggregator = EventAggregator(config)
        events = [
            make_mouse_event(0, 0, 1.0),
            make_mouse_event(10, 10, 2.0),
        ]
        
        result = await aggregator.detect_idle_periods(events)
        
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_idle_period_classification_short(self):
        config = AggregationConfig(
            idle_threshold_seconds=1.0,
            short_pause_max_seconds=5.0,
            break_max_seconds=60.0,
        )
        aggregator = EventAggregator(config)
        events = [
            make_mouse_event(0, 0, 1.0),
            make_mouse_event(10, 10, 4.0),
        ]
        
        result = await aggregator.detect_idle_periods(events)
        
        assert result[0].is_short_pause is True
        assert result[0].is_break is False
        assert result[0].is_away is False

    @pytest.mark.asyncio
    async def test_idle_period_classification_break(self):
        config = AggregationConfig(
            idle_threshold_seconds=1.0,
            short_pause_max_seconds=5.0,
            break_max_seconds=60.0,
        )
        aggregator = EventAggregator(config)
        events = [
            make_mouse_event(0, 0, 1.0),
            make_mouse_event(10, 10, 31.0),
        ]
        
        result = await aggregator.detect_idle_periods(events)
        
        assert result[0].is_short_pause is False
        assert result[0].is_break is True
        assert result[0].is_away is False

    @pytest.mark.asyncio
    async def test_idle_period_classification_away(self):
        config = AggregationConfig(
            idle_threshold_seconds=1.0,
            short_pause_max_seconds=5.0,
            break_max_seconds=60.0,
        )
        aggregator = EventAggregator(config)
        events = [
            make_mouse_event(0, 0, 1.0),
            make_mouse_event(10, 10, 120.0),
        ]
        
        result = await aggregator.detect_idle_periods(events)
        
        assert result[0].is_short_pause is False
        assert result[0].is_break is False
        assert result[0].is_away is True


class TestAggregationConfig:

    def test_default_config(self):
        config = AggregationConfig()
        assert config.mouse_window_ms == 500.0
        assert config.scroll_window_ms == 1000.0
        assert config.typing_window_ms == 2000.0
        assert config.douglas_peucker_epsilon == 5.0

    def test_custom_config(self):
        config = AggregationConfig(
            mouse_window_ms=100.0,
            douglas_peucker_epsilon=10.0,
        )
        assert config.mouse_window_ms == 100.0
        assert config.douglas_peucker_epsilon == 10.0


class TestAggregationResult:

    @pytest.mark.asyncio
    async def test_aggregate_session(self):
        aggregator = EventAggregator()
        events = [
            make_mouse_event(0, 0, 1.0),
            make_mouse_event(10, 10, 1.05),
            make_scroll_event(0, 10, 1.1),
            make_key_event("a", 1.2, "a"),
        ]
        
        result = await aggregator.aggregate_session(events)
        
        assert result.original_event_count == 4
        assert result.aggregated_event_count > 0
        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_compression_ratio(self):
        aggregator = EventAggregator()
        events = [make_mouse_event(i, i, 1.0 + i * 0.01) for i in range(100)]
        
        result = await aggregator.aggregate_session(events)
        
        assert result.compression_ratio > 0
        assert result.aggregated_event_count < result.original_event_count


class TestAggregatedEventModels:

    def test_point_model(self):
        point = Point(x=10, y=20, timestamp=1.0)
        assert point.x == 10
        assert point.y == 20
        assert point.timestamp == 1.0

    def test_aggregated_event_duration(self):
        event = AggregatedMouseEvent(
            start_timestamp=1.0,
            end_timestamp=2.0,
            event_count=10,
            start_point=Point(x=0, y=0, timestamp=1.0),
            end_point=Point(x=100, y=100, timestamp=2.0),
            total_distance=141.4,
            straight_line_distance=141.4,
            average_speed=141.4,
            max_speed=141.4,
        )
        assert event.duration_ms == pytest.approx(1000.0, abs=0.1)

    def test_scroll_direction_enum(self):
        assert ScrollDirection.UP == "up"
        assert ScrollDirection.DOWN == "down"
        assert ScrollDirection.LEFT == "left"
        assert ScrollDirection.RIGHT == "right"
        assert ScrollDirection.MIXED == "mixed"

    def test_aggregation_type_enum(self):
        assert AggregationType.MOUSE_TRAJECTORY == "mouse_trajectory"
        assert AggregationType.SCROLL_SEQUENCE == "scroll_sequence"
        assert AggregationType.TYPING_SEQUENCE == "typing_sequence"
        assert AggregationType.IDLE_PERIOD == "idle_period"

    def test_to_dict(self):
        event = AggregatedScrollEvent(
            start_timestamp=1.0,
            end_timestamp=2.0,
            event_count=5,
            total_dx=0,
            total_dy=50,
            primary_direction=ScrollDirection.UP,
            scroll_events=5,
            average_scroll_per_event=10.0,
        )
        d = event.to_dict()
        assert d["total_dy"] == 50
        assert d["primary_direction"] == "up"
