"""AI-powered daily and weekly summaries."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from mnemosyne.llm.base import LLMProvider, Message
from mnemosyne.analytics.statistics import StatisticsCalculator, WorkStatistics
from mnemosyne.store.database import Database


@dataclass
class DailySummary:
    date: datetime
    headline: str
    highlights: list[str]
    insights: list[str]
    productivity_score: float
    total_hours: float
    top_apps: list[str]
    recommendations: list[str]
    raw_stats: WorkStatistics | None = None


@dataclass
class WeeklySummary:
    start_date: datetime
    end_date: datetime
    headline: str
    daily_summaries: list[DailySummary]
    weekly_insights: list[str]
    trends: dict[str, Any]
    average_productivity: float
    total_hours: float
    most_used_apps: list[str]
    recommendations: list[str]


class SummaryGenerator:

    DAILY_PROMPT = """You are analyzing a user's computer activity for one day.

Date: {date}
Total Active Time: {total_hours:.1f} hours
Productivity Score: {productivity_score:.0f}/100
Event Count: {event_count}
Screenshot Count: {screenshot_count}

Top Apps Used (by time):
{top_apps}

App Usage Breakdown:
{app_breakdown}

Peak Activity Hours: {peak_hours}

Productive Time: {productive_hours:.1f}h
Neutral Time: {neutral_hours:.1f}h
Distracting Time: {distracting_hours:.1f}h

Generate a JSON response with:
{{
    "headline": "One catchy sentence summarizing the day (e.g., 'A focused coding day with minimal distractions')",
    "highlights": ["3-5 notable observations about the day"],
    "insights": ["2-3 deeper insights about work patterns"],
    "recommendations": ["2-3 actionable suggestions for improvement"]
}}"""

    WEEKLY_PROMPT = """You are analyzing a user's weekly computer activity.

Week: {start_date} to {end_date}
Total Active Time: {total_hours:.1f} hours
Average Daily Productivity: {avg_productivity:.0f}/100

Daily Breakdown:
{daily_breakdown}

Most Used Apps This Week:
{most_used_apps}

Productivity Trend: {productivity_trend}

Generate a JSON response with:
{{
    "headline": "One catchy sentence summarizing the week",
    "weekly_insights": ["3-5 insights about the week's work patterns"],
    "trends": {{"productivity": "improving/stable/declining", "focus": "high/medium/low", "work_life_balance": "good/needs_attention"}},
    "recommendations": ["3-5 actionable suggestions for next week"]
}}"""

    def __init__(self, llm: LLMProvider, database: Database):
        self.llm = llm
        self.database = database
        self.stats_calculator = StatisticsCalculator(database)

    async def generate_daily_summary(
        self,
        date: datetime | None = None,
        session_id: str | None = None,
    ) -> DailySummary:
        if date is None:
            date = datetime.now()

        stats = self.stats_calculator.calculate_daily_stats(date, session_id)

        if stats.event_count == 0:
            return self._empty_daily_summary(date)

        prompt = self._build_daily_prompt(stats)
        response = await self._generate_with_llm(prompt)
        parsed = self._parse_json_response(response)

        return DailySummary(
            date=date,
            headline=parsed.get("headline", "No activity recorded"),
            highlights=parsed.get("highlights", []),
            insights=parsed.get("insights", []),
            productivity_score=stats.productivity.score,
            total_hours=stats.total_active_hours,
            top_apps=stats.top_apps,
            recommendations=parsed.get("recommendations", []),
            raw_stats=stats,
        )

    async def generate_weekly_summary(
        self,
        end_date: datetime | None = None,
    ) -> WeeklySummary:
        if end_date is None:
            end_date = datetime.now()

        start_date = end_date - timedelta(days=6)
        weekly_stats = self.stats_calculator.calculate_weekly_stats(end_date)

        daily_summaries = []
        for stats in weekly_stats:
            summary = await self.generate_daily_summary(stats.date)
            daily_summaries.append(summary)

        total_hours = sum(s.total_hours for s in daily_summaries)
        avg_productivity = (
            sum(s.productivity_score for s in daily_summaries) / len(daily_summaries)
            if daily_summaries else 0
        )

        all_apps: dict[str, float] = {}
        for stats in weekly_stats:
            for app in stats.app_usage:
                all_apps[app.app_name] = all_apps.get(app.app_name, 0) + app.total_seconds

        most_used = sorted(all_apps.items(), key=lambda x: x[1], reverse=True)[:10]
        most_used_apps = [app for app, _ in most_used]

        prompt = self._build_weekly_prompt(
            start_date, end_date, daily_summaries, most_used_apps, avg_productivity
        )
        response = await self._generate_with_llm(prompt)
        parsed = self._parse_json_response(response)

        return WeeklySummary(
            start_date=start_date,
            end_date=end_date,
            headline=parsed.get("headline", "Week summary"),
            daily_summaries=daily_summaries,
            weekly_insights=parsed.get("weekly_insights", []),
            trends=parsed.get("trends", {}),
            average_productivity=avg_productivity,
            total_hours=total_hours,
            most_used_apps=most_used_apps,
            recommendations=parsed.get("recommendations", []),
        )

    def _build_daily_prompt(self, stats: WorkStatistics) -> str:
        top_apps_str = "\n".join(
            f"- {app.app_name}: {app.total_minutes:.0f} min ({app.category})"
            for app in sorted(stats.app_usage, key=lambda x: x.total_seconds, reverse=True)[:10]
        )

        app_breakdown = "\n".join(
            f"- {app.app_name}: {app.total_minutes:.0f} min"
            for app in stats.app_usage[:15]
        )

        peak_hours_str = ", ".join(f"{h}:00" for h in stats.peak_hours) if stats.peak_hours else "N/A"

        return self.DAILY_PROMPT.format(
            date=stats.date.strftime("%Y-%m-%d"),
            total_hours=stats.total_active_hours,
            productivity_score=stats.productivity.score,
            event_count=stats.event_count,
            screenshot_count=stats.screenshot_count,
            top_apps=top_apps_str,
            app_breakdown=app_breakdown,
            peak_hours=peak_hours_str,
            productive_hours=stats.productivity.productive_seconds / 3600,
            neutral_hours=stats.productivity.neutral_seconds / 3600,
            distracting_hours=stats.productivity.distracting_seconds / 3600,
        )

    def _build_weekly_prompt(
        self,
        start_date: datetime,
        end_date: datetime,
        daily_summaries: list[DailySummary],
        most_used_apps: list[str],
        avg_productivity: float,
    ) -> str:
        daily_breakdown = "\n".join(
            f"- {s.date.strftime('%a %m/%d')}: {s.total_hours:.1f}h, {s.productivity_score:.0f}% productivity"
            for s in daily_summaries
        )

        most_used_str = "\n".join(f"- {app}" for app in most_used_apps[:10])

        scores = [s.productivity_score for s in daily_summaries if s.total_hours > 0]
        if len(scores) >= 2:
            first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
            second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
            if second_half > first_half + 5:
                trend = "improving"
            elif second_half < first_half - 5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient data"

        return self.WEEKLY_PROMPT.format(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            total_hours=sum(s.total_hours for s in daily_summaries),
            avg_productivity=avg_productivity,
            daily_breakdown=daily_breakdown,
            most_used_apps=most_used_str,
            productivity_trend=trend,
        )

    async def _generate_with_llm(self, prompt: str) -> str:
        messages = [
            Message(
                role="system",
                content="You are an AI assistant that analyzes work patterns and generates insightful summaries. Always respond with valid JSON.",
            ),
            Message(role="user", content=prompt),
        ]
        response = await self.llm.complete(messages)
        return response.content

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        import json

        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1])

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "headline": "Summary generated",
                "highlights": [],
                "insights": [],
                "recommendations": [],
            }

    def _empty_daily_summary(self, date: datetime) -> DailySummary:
        return DailySummary(
            date=date,
            headline="No activity recorded",
            highlights=[],
            insights=[],
            productivity_score=0,
            total_hours=0,
            top_apps=[],
            recommendations=["Start recording your activity to get insights!"],
            raw_stats=None,
        )
