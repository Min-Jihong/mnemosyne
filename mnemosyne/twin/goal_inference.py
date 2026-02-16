"""Goal Inference Engine - Infers user's goals from context and behavior patterns.

This module is the core of the autonomous agent system. It observes:
1. Current screen state
2. Recent actions
3. Time of day / day of week patterns
4. Historical behavior patterns

And infers: "What does the user want to accomplish right now?"
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field


class GoalType(str, Enum):
    """Types of goals the system can infer."""

    CODING = "coding"
    WRITING = "writing"
    COMMUNICATION = "communication"
    RESEARCH = "research"
    FILE_MANAGEMENT = "file_management"
    SYSTEM_ADMIN = "system_admin"
    BROWSING = "browsing"
    MEETING = "meeting"
    CREATIVE = "creative"
    DATA_ANALYSIS = "data_analysis"
    UNKNOWN = "unknown"


class GoalUrgency(str, Enum):
    """Urgency level of the inferred goal."""

    IMMEDIATE = "immediate"  # User wants this done NOW
    SOON = "soon"  # Within the current work session
    EVENTUAL = "eventual"  # Can be done later
    BACKGROUND = "background"  # Low priority, can run in background


class InferredGoal(BaseModel):
    """A goal inferred from user behavior and context."""

    goal_id: str
    goal_type: GoalType
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    urgency: GoalUrgency = GoalUrgency.EVENTUAL

    # Evidence supporting this inference
    supporting_evidence: list[str] = Field(default_factory=list)

    # Context when this goal was inferred
    app_context: str = ""
    window_title: str = ""
    timestamp: float = Field(default_factory=time.time)

    # Related sub-goals
    sub_goals: list[str] = Field(default_factory=list)

    # Estimated completion time (seconds)
    estimated_duration: float | None = None

    # Whether user has implicitly confirmed this goal
    user_validated: bool = False


class GoalPattern(BaseModel):
    """A learned pattern for goal inference."""

    pattern_id: str
    trigger_conditions: dict[str, Any]  # app, time, sequence, etc.
    typical_goal: GoalType
    typical_description: str
    occurrence_count: int = 0
    success_rate: float = 0.0
    avg_duration: float = 0.0


class ContextSignal(BaseModel):
    """A signal from the environment that helps infer goals."""

    signal_type: str  # app_switch, file_open, search_query, etc.
    signal_data: dict[str, Any]
    timestamp: float
    relevance_score: float = 0.5


class GoalInferenceEngine:
    """Infers user goals from context, behavior, and patterns.

    This is the "brain" that figures out what the user wants to do.
    It combines multiple signals:
    - Current app and window
    - Recent action sequence
    - Time-based patterns (morning routine, etc.)
    - Historical goal patterns

    Usage:
        engine = GoalInferenceEngine(llm=llm, profile=profile)
        await engine.initialize()

        # Feed context signals
        engine.observe_signal(ContextSignal(signal_type="app_switch", ...))

        # Get inferred goals
        goals = await engine.infer_current_goals()
    """

    def __init__(
        self,
        llm: Any = None,
        profile: Any = None,
        memory: Any = None,
        data_dir: Path | None = None,
        confidence_threshold: float = 0.6,
        max_active_goals: int = 5,
    ):
        self.llm = llm
        self.profile = profile
        self.memory = memory
        self.data_dir = data_dir or Path.home() / ".mnemosyne" / "goal_inference"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.confidence_threshold = confidence_threshold
        self.max_active_goals = max_active_goals

        # Active goals being tracked
        self._active_goals: dict[str, InferredGoal] = {}

        # Recent context signals
        self._signal_buffer: list[ContextSignal] = []
        self._max_signals = 100

        # Learned patterns
        self._patterns: dict[str, GoalPattern] = {}

        # Goal history for learning
        self._goal_history: list[InferredGoal] = []
        self._max_history = 1000

        # Callbacks
        self._on_goal_inferred: Callable[[InferredGoal], None] | None = None
        self._on_goal_completed: Callable[[InferredGoal], None] | None = None

    async def initialize(self) -> None:
        """Load learned patterns and history."""
        await self._load_patterns()
        await self._load_history()

    async def _load_patterns(self) -> None:
        """Load learned goal patterns from disk."""
        patterns_file = self.data_dir / "goal_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file) as f:
                    data = json.load(f)
                    for p_data in data:
                        pattern = GoalPattern(**p_data)
                        self._patterns[pattern.pattern_id] = pattern
            except Exception:
                pass

    async def _load_history(self) -> None:
        """Load goal history from disk."""
        history_file = self.data_dir / "goal_history.json"
        if history_file.exists():
            try:
                with open(history_file) as f:
                    data = json.load(f)
                    self._goal_history = [InferredGoal(**g) for g in data[-self._max_history :]]
            except Exception:
                pass

    def observe_signal(self, signal: ContextSignal) -> None:
        """Observe a context signal from the environment."""
        self._signal_buffer.append(signal)
        if len(self._signal_buffer) > self._max_signals:
            self._signal_buffer = self._signal_buffer[-self._max_signals :]

    def observe_app_switch(self, from_app: str, to_app: str, window_title: str = "") -> None:
        """Observe an app switch event."""
        self.observe_signal(
            ContextSignal(
                signal_type="app_switch",
                signal_data={
                    "from_app": from_app,
                    "to_app": to_app,
                    "window_title": window_title,
                },
                timestamp=time.time(),
                relevance_score=0.8,
            )
        )

    def observe_file_open(self, file_path: str, app: str) -> None:
        """Observe a file open event."""
        self.observe_signal(
            ContextSignal(
                signal_type="file_open",
                signal_data={
                    "file_path": file_path,
                    "app": app,
                    "extension": Path(file_path).suffix if file_path else "",
                },
                timestamp=time.time(),
                relevance_score=0.9,
            )
        )

    def observe_search_query(self, query: str, source: str) -> None:
        """Observe a search query."""
        self.observe_signal(
            ContextSignal(
                signal_type="search_query",
                signal_data={
                    "query": query,
                    "source": source,  # browser, spotlight, app-specific
                },
                timestamp=time.time(),
                relevance_score=0.7,
            )
        )

    def observe_typing_burst(self, app: str, char_count: int, duration_ms: int) -> None:
        """Observe a burst of typing activity."""
        self.observe_signal(
            ContextSignal(
                signal_type="typing_burst",
                signal_data={
                    "app": app,
                    "char_count": char_count,
                    "duration_ms": duration_ms,
                    "wpm": (char_count / 5) / (duration_ms / 60000) if duration_ms > 0 else 0,
                },
                timestamp=time.time(),
                relevance_score=0.6,
            )
        )

    async def infer_current_goals(
        self,
        current_app: str = "",
        current_title: str = "",
        screen_content: str = "",
    ) -> list[InferredGoal]:
        """Infer what goals the user is currently trying to achieve.

        Returns a ranked list of possible goals, sorted by confidence.
        """
        goals: list[InferredGoal] = []

        # 1. Rule-based inference from current context
        rule_goals = self._infer_from_rules(current_app, current_title)
        goals.extend(rule_goals)

        # 2. Pattern-based inference from learned patterns
        pattern_goals = self._infer_from_patterns()
        goals.extend(pattern_goals)

        # 3. Time-based inference (what does user typically do at this time?)
        time_goals = self._infer_from_time_patterns()
        goals.extend(time_goals)

        # 4. LLM-based inference for complex scenarios
        if self.llm and screen_content:
            llm_goals = await self._infer_from_llm(
                current_app, current_title, screen_content, goals
            )
            goals.extend(llm_goals)

        # Deduplicate and rank
        goals = self._deduplicate_goals(goals)
        goals = sorted(goals, key=lambda g: g.confidence, reverse=True)

        # Filter by confidence threshold
        goals = [g for g in goals if g.confidence >= self.confidence_threshold]

        # Limit to max active goals
        goals = goals[: self.max_active_goals]

        # Update active goals
        for goal in goals:
            self._active_goals[goal.goal_id] = goal
            if self._on_goal_inferred:
                self._on_goal_inferred(goal)

        return goals

    def _infer_from_rules(self, app: str, title: str) -> list[InferredGoal]:
        """Rule-based goal inference from app and window context."""
        goals = []
        now = time.time()

        app_lower = app.lower()
        title_lower = title.lower()

        # Coding apps
        if any(x in app_lower for x in ["code", "vscode", "pycharm", "xcode", "intellij", "vim"]):
            goal_type = GoalType.CODING
            description = "Writing or editing code"

            # More specific based on title
            if ".py" in title_lower:
                description = "Working on Python code"
            elif ".ts" in title_lower or ".tsx" in title_lower:
                description = "Working on TypeScript code"
            elif ".js" in title_lower or ".jsx" in title_lower:
                description = "Working on JavaScript code"
            elif "test" in title_lower:
                description = "Writing or running tests"
            elif "debug" in title_lower:
                description = "Debugging code"

            goals.append(
                InferredGoal(
                    goal_id=f"goal_{int(now * 1000)}_coding",
                    goal_type=goal_type,
                    description=description,
                    confidence=0.85,
                    urgency=GoalUrgency.IMMEDIATE,
                    app_context=app,
                    window_title=title,
                    supporting_evidence=[f"Active in coding app: {app}"],
                )
            )

        # Writing/Documents
        elif any(
            x in app_lower
            for x in ["word", "pages", "notion", "obsidian", "bear", "typora", "markdown"]
        ):
            goals.append(
                InferredGoal(
                    goal_id=f"goal_{int(now * 1000)}_writing",
                    goal_type=GoalType.WRITING,
                    description="Writing or editing documents",
                    confidence=0.8,
                    urgency=GoalUrgency.SOON,
                    app_context=app,
                    window_title=title,
                    supporting_evidence=[f"Active in document app: {app}"],
                )
            )

        # Communication
        elif any(x in app_lower for x in ["slack", "teams", "discord", "mail", "messages", "zoom"]):
            goal_type = GoalType.COMMUNICATION
            urgency = GoalUrgency.IMMEDIATE

            if "zoom" in app_lower or "meet" in app_lower:
                description = "In a meeting or call"
                goal_type = GoalType.MEETING
            elif "mail" in app_lower:
                description = "Managing emails"
            else:
                description = "Communicating with team/contacts"

            goals.append(
                InferredGoal(
                    goal_id=f"goal_{int(now * 1000)}_comm",
                    goal_type=goal_type,
                    description=description,
                    confidence=0.75,
                    urgency=urgency,
                    app_context=app,
                    window_title=title,
                    supporting_evidence=[f"Active in communication app: {app}"],
                )
            )

        # Browser - more nuanced
        elif any(x in app_lower for x in ["chrome", "safari", "firefox", "arc", "edge", "brave"]):
            goal_type = GoalType.BROWSING
            description = "Browsing the web"
            confidence = 0.5  # Lower confidence, needs more context

            # Infer from title
            if any(x in title_lower for x in ["github", "gitlab", "stackoverflow", "docs"]):
                goal_type = GoalType.RESEARCH
                description = "Researching code/documentation"
                confidence = 0.75
            elif any(x in title_lower for x in ["google", "search", "bing"]):
                goal_type = GoalType.RESEARCH
                description = "Searching for information"
                confidence = 0.7
            elif any(x in title_lower for x in ["youtube", "netflix", "twitter", "reddit"]):
                description = "Entertainment/Social media"
                confidence = 0.6

            goals.append(
                InferredGoal(
                    goal_id=f"goal_{int(now * 1000)}_browse",
                    goal_type=goal_type,
                    description=description,
                    confidence=confidence,
                    urgency=GoalUrgency.EVENTUAL,
                    app_context=app,
                    window_title=title,
                    supporting_evidence=[f"Browser title: {title[:50]}"],
                )
            )

        # Terminal
        elif any(x in app_lower for x in ["terminal", "iterm", "warp", "hyper", "kitty"]):
            goals.append(
                InferredGoal(
                    goal_id=f"goal_{int(now * 1000)}_terminal",
                    goal_type=GoalType.SYSTEM_ADMIN,
                    description="Running commands or system administration",
                    confidence=0.7,
                    urgency=GoalUrgency.IMMEDIATE,
                    app_context=app,
                    window_title=title,
                    supporting_evidence=["Active in terminal"],
                )
            )

        # Finder/Explorer
        elif any(x in app_lower for x in ["finder", "explorer", "files"]):
            goals.append(
                InferredGoal(
                    goal_id=f"goal_{int(now * 1000)}_files",
                    goal_type=GoalType.FILE_MANAGEMENT,
                    description="Managing files",
                    confidence=0.65,
                    urgency=GoalUrgency.SOON,
                    app_context=app,
                    window_title=title,
                    supporting_evidence=["Active in file manager"],
                )
            )

        # Excel/Sheets
        elif any(x in app_lower for x in ["excel", "sheets", "numbers", "tableau"]):
            goals.append(
                InferredGoal(
                    goal_id=f"goal_{int(now * 1000)}_data",
                    goal_type=GoalType.DATA_ANALYSIS,
                    description="Working with data/spreadsheets",
                    confidence=0.8,
                    urgency=GoalUrgency.SOON,
                    app_context=app,
                    window_title=title,
                    supporting_evidence=[f"Active in data app: {app}"],
                )
            )

        return goals

    def _infer_from_patterns(self) -> list[InferredGoal]:
        """Infer goals from learned patterns."""
        goals = []
        now = time.time()

        # Get recent signals
        recent_signals = [s for s in self._signal_buffer if now - s.timestamp < 300]  # Last 5 min

        if not recent_signals:
            return goals

        # Look for matching patterns
        for pattern in self._patterns.values():
            if self._pattern_matches(pattern, recent_signals):
                goals.append(
                    InferredGoal(
                        goal_id=f"goal_{int(now * 1000)}_pattern_{pattern.pattern_id}",
                        goal_type=pattern.typical_goal,
                        description=pattern.typical_description,
                        confidence=min(0.9, 0.5 + pattern.success_rate * 0.4),
                        urgency=GoalUrgency.SOON,
                        supporting_evidence=[
                            f"Matches learned pattern (seen {pattern.occurrence_count} times)"
                        ],
                        estimated_duration=pattern.avg_duration,
                    )
                )

        return goals

    def _pattern_matches(self, pattern: GoalPattern, signals: list[ContextSignal]) -> bool:
        """Check if current signals match a learned pattern."""
        conditions = pattern.trigger_conditions

        # Check app condition
        if "app" in conditions:
            app_signals = [s for s in signals if s.signal_type == "app_switch"]
            if not any(conditions["app"] in s.signal_data.get("to_app", "") for s in app_signals):
                return False

        # Check time condition
        if "hour_range" in conditions:
            current_hour = datetime.now().hour
            start, end = conditions["hour_range"]
            if not (start <= current_hour <= end):
                return False

        # Check day condition
        if "days" in conditions:
            current_day = datetime.now().weekday()
            if current_day not in conditions["days"]:
                return False

        return True

    def _infer_from_time_patterns(self) -> list[InferredGoal]:
        """Infer goals based on time-of-day patterns."""
        goals = []
        now = datetime.now()
        current_hour = now.hour
        current_day = now.weekday()

        # Use profile if available
        if self.profile and hasattr(self.profile, "work_patterns"):
            # Check typical activities for this time
            for pattern in getattr(self.profile, "work_patterns", {}).values():
                if hasattr(pattern, "peak_hours") and current_hour in pattern.peak_hours:
                    goals.append(
                        InferredGoal(
                            goal_id=f"goal_{int(time.time() * 1000)}_time",
                            goal_type=GoalType.UNKNOWN,
                            description=f"Time-based: Usually active at {current_hour}:00",
                            confidence=0.4,  # Lower confidence for time-only inference
                            urgency=GoalUrgency.EVENTUAL,
                            supporting_evidence=[f"Typical activity time: {current_hour}:00"],
                        )
                    )

        # Generic time-based heuristics
        if 9 <= current_hour <= 12 and current_day < 5:  # Morning weekday
            goals.append(
                InferredGoal(
                    goal_id=f"goal_{int(time.time() * 1000)}_morning",
                    goal_type=GoalType.UNKNOWN,
                    description="Morning work session - peak productivity time",
                    confidence=0.3,
                    urgency=GoalUrgency.SOON,
                    supporting_evidence=["Morning work hours"],
                )
            )

        return goals

    async def _infer_from_llm(
        self,
        app: str,
        title: str,
        screen_content: str,
        existing_goals: list[InferredGoal],
    ) -> list[InferredGoal]:
        """Use LLM for complex goal inference."""
        if not self.llm:
            return []

        # Build context from recent signals
        recent_signals = self._signal_buffer[-20:]
        signal_context = "\n".join(
            f"- {s.signal_type}: {json.dumps(s.signal_data)}" for s in recent_signals
        )

        existing_goal_context = "\n".join(
            f"- {g.goal_type.value}: {g.description} (confidence: {g.confidence:.2f})"
            for g in existing_goals[:5]
        )

        prompt = f"""Based on the following context, infer what the user is trying to accomplish.

Current App: {app}
Window Title: {title}

Recent Activity:
{signal_context}

Screen Content (truncated):
{screen_content[:500]}

Already inferred goals:
{existing_goal_context}

What additional goals might the user have? Consider:
1. The immediate task they're working on
2. The broader objective they're trying to achieve
3. Any preparation or follow-up tasks

Return a JSON array of goals:
[{{"goal_type": "coding|writing|communication|research|...", "description": "...", "confidence": 0.0-1.0, "urgency": "immediate|soon|eventual"}}]

Only include goals with confidence > 0.5. Return at most 3 goals."""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.generate(messages)

            # Parse response
            response_text = response.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            goal_data = json.loads(response_text)
            goals = []

            for g in goal_data:
                try:
                    goal_type = GoalType(g.get("goal_type", "unknown"))
                except ValueError:
                    goal_type = GoalType.UNKNOWN

                try:
                    urgency = GoalUrgency(g.get("urgency", "eventual"))
                except ValueError:
                    urgency = GoalUrgency.EVENTUAL

                goals.append(
                    InferredGoal(
                        goal_id=f"goal_{int(time.time() * 1000)}_llm_{len(goals)}",
                        goal_type=goal_type,
                        description=g.get("description", ""),
                        confidence=float(g.get("confidence", 0.5)),
                        urgency=urgency,
                        supporting_evidence=["Inferred by LLM from screen context"],
                        app_context=app,
                        window_title=title,
                    )
                )

            return goals

        except Exception:
            return []

    def _deduplicate_goals(self, goals: list[InferredGoal]) -> list[InferredGoal]:
        """Remove duplicate goals, keeping the highest confidence one."""
        seen: dict[str, InferredGoal] = {}

        for goal in goals:
            # Create a key based on goal type and description similarity
            key = f"{goal.goal_type.value}:{goal.description[:30]}"

            if key not in seen or goal.confidence > seen[key].confidence:
                seen[key] = goal

        return list(seen.values())

    def validate_goal(self, goal_id: str) -> None:
        """Mark a goal as validated by user behavior."""
        if goal_id in self._active_goals:
            self._active_goals[goal_id].user_validated = True

    def complete_goal(self, goal_id: str, success: bool = True) -> None:
        """Mark a goal as completed."""
        if goal_id in self._active_goals:
            goal = self._active_goals.pop(goal_id)
            goal.timestamp = time.time()

            # Add to history
            self._goal_history.append(goal)
            if len(self._goal_history) > self._max_history:
                self._goal_history = self._goal_history[-self._max_history :]

            # Update pattern if this was pattern-based
            self._update_patterns(goal, success)

            if self._on_goal_completed:
                self._on_goal_completed(goal)

    def _update_patterns(self, goal: InferredGoal, success: bool) -> None:
        """Update learned patterns based on goal completion."""
        # Find matching pattern or create new one
        pattern_key = f"{goal.goal_type.value}_{goal.app_context}"

        if pattern_key not in self._patterns:
            self._patterns[pattern_key] = GoalPattern(
                pattern_id=pattern_key,
                trigger_conditions={"app": goal.app_context},
                typical_goal=goal.goal_type,
                typical_description=goal.description,
            )

        pattern = self._patterns[pattern_key]
        pattern.occurrence_count += 1

        # Update success rate with exponential moving average
        alpha = 0.1
        pattern.success_rate = (
            alpha * (1.0 if success else 0.0) + (1 - alpha) * pattern.success_rate
        )

        # Update duration if available
        if goal.estimated_duration:
            if pattern.avg_duration == 0:
                pattern.avg_duration = goal.estimated_duration
            else:
                pattern.avg_duration = (
                    alpha * goal.estimated_duration + (1 - alpha) * pattern.avg_duration
                )

    def get_active_goals(self) -> list[InferredGoal]:
        """Get currently active goals."""
        return list(self._active_goals.values())

    def get_primary_goal(self) -> InferredGoal | None:
        """Get the highest confidence active goal."""
        goals = self.get_active_goals()
        if not goals:
            return None
        return max(goals, key=lambda g: g.confidence)

    def set_goal_callback(self, on_goal_inferred: Callable[[InferredGoal], None]) -> None:
        """Set callback for when a new goal is inferred."""
        self._on_goal_inferred = on_goal_inferred

    def set_completion_callback(self, on_goal_completed: Callable[[InferredGoal], None]) -> None:
        """Set callback for when a goal is completed."""
        self._on_goal_completed = on_goal_completed

    async def save_state(self) -> None:
        """Save patterns and history to disk."""
        # Save patterns
        patterns_file = self.data_dir / "goal_patterns.json"
        with open(patterns_file, "w") as f:
            json.dump([p.model_dump() for p in self._patterns.values()], f, indent=2)

        # Save history
        history_file = self.data_dir / "goal_history.json"
        with open(history_file, "w") as f:
            json.dump([g.model_dump() for g in self._goal_history], f, indent=2)

    def get_stats(self) -> dict[str, Any]:
        """Get goal inference statistics."""
        return {
            "active_goals": len(self._active_goals),
            "learned_patterns": len(self._patterns),
            "goal_history_size": len(self._goal_history),
            "signal_buffer_size": len(self._signal_buffer),
            "confidence_threshold": self.confidence_threshold,
        }
