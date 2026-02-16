"""User profile model for personalized behavior learning."""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class TimeOfDay(str, Enum):
    EARLY_MORNING = "early_morning"
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


class AppCategory(str, Enum):
    DEVELOPMENT = "development"
    COMMUNICATION = "communication"
    BROWSER = "browser"
    PRODUCTIVITY = "productivity"
    ENTERTAINMENT = "entertainment"
    SYSTEM = "system"
    OTHER = "other"


APP_CATEGORIES: dict[str, AppCategory] = {
    "code": AppCategory.DEVELOPMENT,
    "vscode": AppCategory.DEVELOPMENT,
    "visual studio code": AppCategory.DEVELOPMENT,
    "xcode": AppCategory.DEVELOPMENT,
    "pycharm": AppCategory.DEVELOPMENT,
    "intellij": AppCategory.DEVELOPMENT,
    "terminal": AppCategory.DEVELOPMENT,
    "iterm": AppCategory.DEVELOPMENT,
    "slack": AppCategory.COMMUNICATION,
    "discord": AppCategory.COMMUNICATION,
    "messages": AppCategory.COMMUNICATION,
    "mail": AppCategory.COMMUNICATION,
    "zoom": AppCategory.COMMUNICATION,
    "teams": AppCategory.COMMUNICATION,
    "chrome": AppCategory.BROWSER,
    "safari": AppCategory.BROWSER,
    "firefox": AppCategory.BROWSER,
    "arc": AppCategory.BROWSER,
    "notion": AppCategory.PRODUCTIVITY,
    "obsidian": AppCategory.PRODUCTIVITY,
    "notes": AppCategory.PRODUCTIVITY,
    "calendar": AppCategory.PRODUCTIVITY,
    "finder": AppCategory.SYSTEM,
    "activity monitor": AppCategory.SYSTEM,
    "system preferences": AppCategory.SYSTEM,
    "spotify": AppCategory.ENTERTAINMENT,
    "youtube": AppCategory.ENTERTAINMENT,
    "netflix": AppCategory.ENTERTAINMENT,
}


class HotkeyPreference(BaseModel):
    keys: tuple[str, ...] = Field(default_factory=tuple)
    frequency: int = 0
    last_used: float = Field(default_factory=time.time)
    associated_app: str | None = None
    inferred_purpose: str | None = None


class AppTransition(BaseModel):
    from_app: str
    to_app: str
    count: int = 0
    avg_time_before_switch_ms: float = 0.0
    common_triggers: list[str] = Field(default_factory=list)


class WorkPattern(BaseModel):
    time_of_day: TimeOfDay
    dominant_apps: list[str] = Field(default_factory=list)
    avg_session_duration_min: float = 0.0
    typing_speed_wpm: float = 0.0
    click_frequency_per_min: float = 0.0
    focus_score: float = 0.5
    common_workflows: list[str] = Field(default_factory=list)


class UserPreferences(BaseModel):
    preferred_apps_by_task: dict[str, list[str]] = Field(default_factory=dict)
    hotkey_preferences: list[HotkeyPreference] = Field(default_factory=list)
    app_transitions: list[AppTransition] = Field(default_factory=list)
    work_patterns: dict[TimeOfDay, WorkPattern] = Field(default_factory=dict)

    typing_style: str = "unknown"
    mouse_style: str = "unknown"

    preferred_window_arrangement: str = "unknown"
    common_file_locations: list[str] = Field(default_factory=list)

    language: str = "en"
    timezone: str = "UTC"


class BehaviorStatistics(BaseModel):
    total_events: int = 0
    total_sessions: int = 0
    total_hours: float = 0.0

    events_by_type: dict[str, int] = Field(default_factory=dict)
    events_by_app: dict[str, int] = Field(default_factory=dict)
    events_by_hour: dict[int, int] = Field(default_factory=dict)

    avg_events_per_hour: float = 0.0
    avg_session_duration_min: float = 0.0

    most_productive_hours: list[int] = Field(default_factory=list)
    least_productive_hours: list[int] = Field(default_factory=list)


class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    preferences: UserPreferences = Field(default_factory=UserPreferences)
    statistics: BehaviorStatistics = Field(default_factory=BehaviorStatistics)

    learned_intents: dict[str, float] = Field(default_factory=dict)
    action_patterns: dict[str, list[str]] = Field(default_factory=dict)

    personality_traits: dict[str, float] = Field(default_factory=dict)

    profile_completeness: float = 0.0
    prediction_accuracy: float = 0.0


class UserProfileStore:
    def __init__(self, data_dir: Path | str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._db_path = self.data_dir / "user_profile.db"
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._init_schema()

        self._profile: UserProfile | None = None

    def _init_schema(self) -> None:
        cursor = self._conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at REAL,
                updated_at REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotkey_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keys TEXT NOT NULL,
                app TEXT,
                timestamp REAL,
                purpose TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_app TEXT,
                to_app TEXT,
                timestamp REAL,
                time_in_source_ms REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS typing_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app TEXT,
                char_count INTEGER,
                duration_ms REAL,
                timestamp REAL,
                corrections INTEGER DEFAULT 0
            )
        """)

        self._conn.commit()

    def load_or_create(self) -> UserProfile:
        cursor = self._conn.cursor()
        cursor.execute("SELECT data FROM profiles ORDER BY updated_at DESC LIMIT 1")
        row = cursor.fetchone()

        if row:
            self._profile = UserProfile.model_validate_json(row[0])
        else:
            self._profile = UserProfile()
            self._save_profile()

        return self._profile

    def get_profile(self) -> UserProfile:
        if self._profile is None:
            return self.load_or_create()
        return self._profile

    def _save_profile(self) -> None:
        if self._profile is None:
            return

        self._profile.updated_at = time.time()

        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO profiles (id, data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                self._profile.id,
                self._profile.model_dump_json(),
                self._profile.created_at,
                self._profile.updated_at,
            ),
        )
        self._conn.commit()

    def record_hotkey(
        self,
        keys: tuple[str, ...],
        app: str | None = None,
        purpose: str | None = None,
    ) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO hotkey_usage (keys, app, timestamp, purpose)
            VALUES (?, ?, ?, ?)
        """,
            (json.dumps(keys), app, time.time(), purpose),
        )
        self._conn.commit()

        self._update_hotkey_preferences()

    def record_app_transition(
        self,
        from_app: str,
        to_app: str,
        time_in_source_ms: float,
    ) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO app_transitions (from_app, to_app, timestamp, time_in_source_ms)
            VALUES (?, ?, ?, ?)
        """,
            (from_app, to_app, time.time(), time_in_source_ms),
        )
        self._conn.commit()

        self._update_app_transitions()

    def record_typing_session(
        self,
        app: str,
        char_count: int,
        duration_ms: float,
        corrections: int = 0,
    ) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO typing_sessions (app, char_count, duration_ms, timestamp, corrections)
            VALUES (?, ?, ?, ?, ?)
        """,
            (app, char_count, duration_ms, time.time(), corrections),
        )
        self._conn.commit()

        self._update_typing_style()

    def _update_hotkey_preferences(self) -> None:
        if self._profile is None:
            return

        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT keys, app, COUNT(*) as freq, MAX(timestamp) as last_used
            FROM hotkey_usage
            GROUP BY keys
            ORDER BY freq DESC
            LIMIT 50
        """)

        preferences = []
        for row in cursor.fetchall():
            keys = tuple(json.loads(row[0]))
            preferences.append(
                HotkeyPreference(
                    keys=keys,
                    frequency=row[2],
                    last_used=row[3],
                    associated_app=row[1],
                )
            )

        self._profile.preferences.hotkey_preferences = preferences
        self._save_profile()

    def _update_app_transitions(self) -> None:
        if self._profile is None:
            return

        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT from_app, to_app, COUNT(*) as cnt, AVG(time_in_source_ms) as avg_time
            FROM app_transitions
            GROUP BY from_app, to_app
            ORDER BY cnt DESC
            LIMIT 100
        """)

        transitions = []
        for row in cursor.fetchall():
            transitions.append(
                AppTransition(
                    from_app=row[0],
                    to_app=row[1],
                    count=row[2],
                    avg_time_before_switch_ms=row[3],
                )
            )

        self._profile.preferences.app_transitions = transitions
        self._save_profile()

    def _update_typing_style(self) -> None:
        if self._profile is None:
            return

        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT AVG(char_count * 60000.0 / duration_ms / 5) as avg_wpm,
                   AVG(corrections * 1.0 / char_count) as correction_rate
            FROM typing_sessions
            WHERE duration_ms > 1000 AND char_count > 10
        """)

        row = cursor.fetchone()
        if row and row[0]:
            avg_wpm = row[0]
            correction_rate = row[1] or 0

            if avg_wpm > 80 and correction_rate < 0.05:
                style = "fast_accurate"
            elif avg_wpm > 60:
                style = "burst"
            elif correction_rate > 0.1:
                style = "slow_careful"
            else:
                style = "continuous"

            self._profile.preferences.typing_style = style
            self._save_profile()

    def update_work_patterns(self, events: list[dict[str, Any]]) -> None:
        if self._profile is None or not events:
            return

        patterns_by_time: dict[TimeOfDay, dict[str, Any]] = {}

        for event in events:
            ts = event.get("timestamp", 0)
            hour = time.localtime(ts).tm_hour

            if 5 <= hour < 8:
                tod = TimeOfDay.EARLY_MORNING
            elif 8 <= hour < 12:
                tod = TimeOfDay.MORNING
            elif 12 <= hour < 17:
                tod = TimeOfDay.AFTERNOON
            elif 17 <= hour < 21:
                tod = TimeOfDay.EVENING
            else:
                tod = TimeOfDay.NIGHT

            if tod not in patterns_by_time:
                patterns_by_time[tod] = {
                    "apps": {},
                    "events": 0,
                    "duration_ms": 0,
                }

            app = event.get("window_app", "unknown")
            patterns_by_time[tod]["apps"][app] = patterns_by_time[tod]["apps"].get(app, 0) + 1
            patterns_by_time[tod]["events"] += 1

        for tod, data in patterns_by_time.items():
            sorted_apps = sorted(data["apps"].items(), key=lambda x: x[1], reverse=True)
            dominant_apps = [app for app, _ in sorted_apps[:5]]

            self._profile.preferences.work_patterns[tod] = WorkPattern(
                time_of_day=tod,
                dominant_apps=dominant_apps,
            )

        self._save_profile()

    def calculate_completeness(self) -> float:
        if self._profile is None:
            return 0.0

        score = 0.0
        total = 0.0

        prefs = self._profile.preferences

        total += 1
        if prefs.hotkey_preferences:
            score += min(len(prefs.hotkey_preferences) / 10, 1.0)

        total += 1
        if prefs.app_transitions:
            score += min(len(prefs.app_transitions) / 20, 1.0)

        total += 1
        if prefs.work_patterns:
            score += min(len(prefs.work_patterns) / 5, 1.0)

        total += 1
        if prefs.typing_style != "unknown":
            score += 1.0

        total += 1
        if prefs.mouse_style != "unknown":
            score += 1.0

        stats = self._profile.statistics

        total += 1
        if stats.total_events > 1000:
            score += 1.0
        elif stats.total_events > 100:
            score += 0.5

        total += 1
        if stats.total_hours > 10:
            score += 1.0
        elif stats.total_hours > 1:
            score += 0.5

        completeness = score / total if total > 0 else 0.0
        self._profile.profile_completeness = completeness
        self._save_profile()

        return completeness

    def get_prediction_for_context(
        self,
        current_app: str,
        time_of_day: TimeOfDay,
        recent_actions: list[str],
    ) -> dict[str, float]:
        if self._profile is None:
            return {}

        predictions: dict[str, float] = {}

        for transition in self._profile.preferences.app_transitions:
            if transition.from_app.lower() == current_app.lower():
                confidence = min(transition.count / 100, 0.9)
                predictions[f"switch_to:{transition.to_app}"] = confidence

        work_pattern = self._profile.preferences.work_patterns.get(time_of_day)
        if work_pattern:
            for i, app in enumerate(work_pattern.dominant_apps[:3]):
                if app.lower() != current_app.lower():
                    predictions[f"use:{app}"] = 0.3 - (i * 0.05)

        for hotkey in self._profile.preferences.hotkey_preferences[:10]:
            if hotkey.associated_app and hotkey.associated_app.lower() == current_app.lower():
                confidence = min(hotkey.frequency / 50, 0.7)
                key_str = "+".join(hotkey.keys)
                predictions[f"hotkey:{key_str}"] = confidence

        return predictions
