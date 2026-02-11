"""Work statistics and productivity metrics."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Any

from mnemosyne.store.database import Database
from mnemosyne.store.models import StoredEvent


@dataclass
class AppUsage:
    app_name: str
    total_seconds: float
    session_count: int
    first_used: datetime
    last_used: datetime
    category: str = "uncategorized"

    @property
    def total_minutes(self) -> float:
        return self.total_seconds / 60

    @property
    def total_hours(self) -> float:
        return self.total_seconds / 3600


@dataclass
class ProductivityScore:
    score: float
    productive_seconds: float
    neutral_seconds: float
    distracting_seconds: float
    breakdown: dict[str, float] = field(default_factory=dict)

    @property
    def productive_percentage(self) -> float:
        total = self.productive_seconds + self.neutral_seconds + self.distracting_seconds
        return (self.productive_seconds / total * 100) if total > 0 else 0


@dataclass
class WorkStatistics:
    date: datetime
    total_active_seconds: float
    app_usage: list[AppUsage]
    productivity: ProductivityScore
    top_apps: list[str]
    peak_hours: list[int]
    event_count: int
    screenshot_count: int

    @property
    def total_active_hours(self) -> float:
        return self.total_active_seconds / 3600


APP_CATEGORIES = {
    "productive": [
        "Code", "Visual Studio Code", "VS Code", "PyCharm", "IntelliJ",
        "Xcode", "Android Studio", "Sublime Text", "Vim", "Neovim",
        "Terminal", "iTerm", "Hyper", "Warp",
        "Notion", "Obsidian", "Bear", "Notes",
        "Figma", "Sketch", "Adobe",
        "Microsoft Word", "Google Docs", "Pages",
        "Microsoft Excel", "Google Sheets", "Numbers",
    ],
    "neutral": [
        "Finder", "File Explorer", "Preview",
        "Safari", "Chrome", "Firefox", "Arc", "Brave", "Edge",
        "Slack", "Discord", "Microsoft Teams", "Zoom",
        "Mail", "Outlook", "Gmail",
        "Calendar", "Reminders",
    ],
    "distracting": [
        "YouTube", "Netflix", "Spotify", "Music",
        "Twitter", "X", "Facebook", "Instagram", "TikTok",
        "Reddit", "Hacker News",
        "Games", "Steam",
    ],
}


def categorize_app(app_name: str) -> str:
    app_lower = app_name.lower()
    for category, apps in APP_CATEGORIES.items():
        for app in apps:
            if app.lower() in app_lower:
                return category
    return "neutral"


class StatisticsCalculator:

    def __init__(self, database: Database):
        self.database = database

    def calculate_daily_stats(
        self,
        date: datetime | None = None,
        session_id: str | None = None,
    ) -> WorkStatistics:
        if date is None:
            date = datetime.now()

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        events = self._get_events_in_range(start_of_day, end_of_day, session_id)

        if not events:
            return self._empty_stats(date)

        app_usage = self._calculate_app_usage(events)
        productivity = self._calculate_productivity(app_usage)
        peak_hours = self._calculate_peak_hours(events)

        top_apps = sorted(
            app_usage,
            key=lambda x: x.total_seconds,
            reverse=True,
        )[:5]

        screenshot_count = sum(1 for e in events if e.action_type == "screenshot")

        return WorkStatistics(
            date=date,
            total_active_seconds=sum(a.total_seconds for a in app_usage),
            app_usage=app_usage,
            productivity=productivity,
            top_apps=[a.app_name for a in top_apps],
            peak_hours=peak_hours,
            event_count=len(events),
            screenshot_count=screenshot_count,
        )

    def calculate_weekly_stats(
        self,
        end_date: datetime | None = None,
    ) -> list[WorkStatistics]:
        if end_date is None:
            end_date = datetime.now()

        stats = []
        for i in range(7):
            date = end_date - timedelta(days=i)
            daily = self.calculate_daily_stats(date)
            stats.append(daily)

        return list(reversed(stats))

    def _get_events_in_range(
        self,
        start: datetime,
        end: datetime,
        session_id: str | None = None,
    ) -> list[StoredEvent]:
        all_events = self.database.get_events(session_id=session_id, limit=10000)
        return [
            e for e in all_events
            if start.timestamp() <= e.timestamp <= end.timestamp()
        ]

    def _calculate_app_usage(self, events: list[StoredEvent]) -> list[AppUsage]:
        app_times: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "total_seconds": 0,
            "session_count": 0,
            "first_used": None,
            "last_used": None,
        })

        prev_event = None
        for event in events:
            app_name = event.window_app or "Unknown"

            if prev_event:
                time_diff = event.timestamp - prev_event.timestamp
                if time_diff < 300:
                    app_times[app_name]["total_seconds"] += time_diff

            if app_times[app_name]["first_used"] is None:
                app_times[app_name]["first_used"] = event.timestamp
                app_times[app_name]["session_count"] = 1
            elif prev_event and prev_event.window_app != app_name:
                app_times[app_name]["session_count"] += 1

            app_times[app_name]["last_used"] = event.timestamp
            prev_event = event

        result = []
        for app_name, data in app_times.items():
            if data["first_used"] is not None:
                result.append(AppUsage(
                    app_name=app_name,
                    total_seconds=data["total_seconds"],
                    session_count=data["session_count"],
                    first_used=datetime.fromtimestamp(data["first_used"]),
                    last_used=datetime.fromtimestamp(data["last_used"]),
                    category=categorize_app(app_name),
                ))

        return result

    def _calculate_productivity(self, app_usage: list[AppUsage]) -> ProductivityScore:
        productive = 0.0
        neutral = 0.0
        distracting = 0.0
        breakdown: dict[str, float] = {}

        for app in app_usage:
            breakdown[app.app_name] = app.total_seconds
            if app.category == "productive":
                productive += app.total_seconds
            elif app.category == "distracting":
                distracting += app.total_seconds
            else:
                neutral += app.total_seconds

        total = productive + neutral + distracting
        if total > 0:
            score = (productive - distracting * 0.5) / total * 100
            score = max(0, min(100, score))
        else:
            score = 50.0

        return ProductivityScore(
            score=score,
            productive_seconds=productive,
            neutral_seconds=neutral,
            distracting_seconds=distracting,
            breakdown=breakdown,
        )

    def _calculate_peak_hours(self, events: list[StoredEvent]) -> list[int]:
        hour_counts: dict[int, int] = defaultdict(int)

        for event in events:
            hour = datetime.fromtimestamp(event.timestamp).hour
            hour_counts[hour] += 1

        sorted_hours = sorted(
            hour_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return [h for h, _ in sorted_hours[:3]]

    def _empty_stats(self, date: datetime) -> WorkStatistics:
        return WorkStatistics(
            date=date,
            total_active_seconds=0,
            app_usage=[],
            productivity=ProductivityScore(
                score=0,
                productive_seconds=0,
                neutral_seconds=0,
                distracting_seconds=0,
            ),
            top_apps=[],
            peak_hours=[],
            event_count=0,
            screenshot_count=0,
        )
