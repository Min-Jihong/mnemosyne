"""Pattern matching and learning for action sequences."""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from mnemosyne.execute.planner import Action, ActionType
from mnemosyne.execute.screen import ScreenContext
from mnemosyne.memory.persistent import PersistentMemory
from mnemosyne.memory.types import MemoryType


class ActionPattern(BaseModel):
    """A learned pattern of actions for achieving a goal."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal_template: str = Field(description="Template/description of the goal this pattern achieves")
    actions: list[Action] = Field(default_factory=list, description="Sequence of actions")

    success_count: int = Field(default=0, description="Number of successful executions")
    failure_count: int = Field(default=0, description="Number of failed executions")
    total_duration_ms: float = Field(
        default=0.0, description="Total execution time across all runs"
    )

    context_hints: dict[str, Any] = Field(
        default_factory=dict, description="Context clues that indicate this pattern applies"
    )

    created_at: float = Field(default_factory=time.time)
    last_used_at: float = Field(default_factory=time.time)
    last_success_at: float | None = Field(default=None)

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

    @property
    def average_duration_ms(self) -> float:
        total = self.success_count + self.failure_count
        return self.total_duration_ms / total if total > 0 else 0.0

    @property
    def is_reliable(self) -> bool:
        """Pattern is reliable if success rate > 70% with at least 3 executions."""
        total = self.success_count + self.failure_count
        return total >= 3 and self.success_rate > 0.7

    def record_execution(self, success: bool, duration_ms: float) -> None:
        """Record an execution attempt."""
        if success:
            self.success_count += 1
            self.last_success_at = time.time()
        else:
            self.failure_count += 1
        self.total_duration_ms += duration_ms
        self.last_used_at = time.time()


class PatternMatcher:
    """Matches goals to learned action patterns and learns new patterns."""

    def __init__(
        self,
        data_dir: Path | str,
        memory: PersistentMemory | None = None,
        similarity_threshold: float = 0.7,
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._db_path = self.data_dir / "patterns.db"
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._init_schema()

        self._memory = memory
        self._similarity_threshold = similarity_threshold

    def _init_schema(self) -> None:
        cursor = self._conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                goal_template TEXT NOT NULL,
                actions TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                total_duration_ms REAL DEFAULT 0.0,
                context_hints TEXT,
                created_at REAL,
                last_used_at REAL,
                last_success_at REAL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_goal ON patterns(goal_template)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_success ON patterns(success_count)
        """)

        self._conn.commit()

    async def find_matching_pattern(
        self,
        goal: str,
        screen_context: ScreenContext | None = None,
    ) -> ActionPattern | None:
        """
        Find a pattern that matches the given goal.

        Uses both exact matching and semantic similarity via memory.

        Args:
            goal: The goal to find a pattern for
            screen_context: Current screen state for context matching

        Returns:
            Best matching ActionPattern, or None if no good match
        """
        exact_match = self._find_exact_match(goal)
        if exact_match and exact_match.is_reliable:
            return exact_match

        similar_patterns = self._find_similar_patterns(goal)

        if self._memory:
            semantic_matches = await self._find_semantic_matches(goal)
            similar_patterns.extend(semantic_matches)

        if screen_context:
            similar_patterns = self._filter_by_context(similar_patterns, screen_context)

        if not similar_patterns:
            return exact_match

        similar_patterns.sort(
            key=lambda p: (p.success_rate, p.success_count),
            reverse=True,
        )

        best = similar_patterns[0]
        if best.is_reliable:
            return best

        return exact_match if exact_match else (best if best.success_count > 0 else None)

    def _find_exact_match(self, goal: str) -> ActionPattern | None:
        """Find pattern with exact goal match."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM patterns WHERE goal_template = ? ORDER BY success_count DESC LIMIT 1",
            (goal,),
        )
        row = cursor.fetchone()
        return self._row_to_pattern(row) if row else None

    def _find_similar_patterns(self, goal: str) -> list[ActionPattern]:
        """Find patterns with similar goal text."""
        cursor = self._conn.cursor()

        words = goal.lower().split()
        if not words:
            return []

        conditions = " OR ".join(["LOWER(goal_template) LIKE ?" for _ in words])
        params = [f"%{word}%" for word in words]

        cursor.execute(
            f"SELECT * FROM patterns WHERE {conditions} ORDER BY success_count DESC LIMIT 10",
            params,
        )

        return [self._row_to_pattern(row) for row in cursor.fetchall()]

    async def _find_semantic_matches(self, goal: str) -> list[ActionPattern]:
        """Find patterns using semantic similarity via memory."""
        if not self._memory:
            return []

        memories = self._memory.recall(
            query=goal,
            n_results=5,
            memory_types=[MemoryType.PATTERN],
        )

        patterns = []
        for memory in memories:
            pattern_id = memory.context.get("pattern_id")
            if pattern_id:
                pattern = self._get_pattern_by_id(pattern_id)
                if pattern:
                    patterns.append(pattern)

        return patterns

    def _filter_by_context(
        self,
        patterns: list[ActionPattern],
        screen_context: ScreenContext,
    ) -> list[ActionPattern]:
        """Filter patterns by context compatibility."""
        filtered = []

        for pattern in patterns:
            hints = pattern.context_hints

            if not hints:
                filtered.append(pattern)
                continue

            required_text = hints.get("required_text", [])
            if required_text:
                screen_text = screen_context.text_content.lower()
                if not all(t.lower() in screen_text for t in required_text):
                    continue

            required_elements = hints.get("required_element_types", [])
            if required_elements:
                element_types = {e.element_type.value for e in screen_context.elements}
                if not all(t in element_types for t in required_elements):
                    continue

            filtered.append(pattern)

        return filtered

    def _get_pattern_by_id(self, pattern_id: str) -> ActionPattern | None:
        """Get pattern by ID."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM patterns WHERE id = ?", (pattern_id,))
        row = cursor.fetchone()
        return self._row_to_pattern(row) if row else None

    def _row_to_pattern(self, row: tuple) -> ActionPattern:
        """Convert database row to ActionPattern."""
        actions_data = json.loads(row[2])
        actions = [Action(**a) for a in actions_data]

        return ActionPattern(
            id=row[0],
            goal_template=row[1],
            actions=actions,
            success_count=row[3],
            failure_count=row[4],
            total_duration_ms=row[5],
            context_hints=json.loads(row[6]) if row[6] else {},
            created_at=row[7],
            last_used_at=row[8],
            last_success_at=row[9],
        )

    async def learn_pattern(
        self,
        goal: str,
        actions: list[Action],
        success: bool,
        duration_ms: float,
        screen_context: ScreenContext | None = None,
    ) -> ActionPattern:
        """
        Learn a new pattern or update an existing one.

        Args:
            goal: The goal that was achieved
            actions: The actions that were executed
            success: Whether the execution was successful
            duration_ms: How long the execution took
            screen_context: Screen context at start of execution

        Returns:
            The created or updated ActionPattern
        """
        existing = self._find_exact_match(goal)

        if existing:
            existing.record_execution(success, duration_ms)

            if success and existing.success_rate < 0.5:
                existing.actions = actions

            self._save_pattern(existing)
            return existing

        context_hints = self._extract_context_hints(screen_context) if screen_context else {}

        pattern = ActionPattern(
            goal_template=goal,
            actions=actions,
            success_count=1 if success else 0,
            failure_count=0 if success else 1,
            total_duration_ms=duration_ms,
            context_hints=context_hints,
        )

        self._save_pattern(pattern)

        if self._memory:
            self._memory.remember(
                content=f"Pattern for: {goal}",
                memory_type=MemoryType.PATTERN,
                context={"pattern_id": pattern.id},
                importance=0.7 if success else 0.4,
                tags=["pattern", "execution"],
            )

        return pattern

    def _extract_context_hints(self, screen_context: ScreenContext) -> dict[str, Any]:
        """Extract context hints from screen state."""
        hints: dict[str, Any] = {}

        if screen_context.text_content:
            words = screen_context.text_content.lower().split()
            common_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been"}
            significant_words = [w for w in words[:50] if w not in common_words and len(w) > 3]
            if significant_words:
                hints["text_keywords"] = significant_words[:10]

        if screen_context.elements:
            element_types = list({e.element_type.value for e in screen_context.elements})
            hints["element_types_present"] = element_types

        return hints

    def _save_pattern(self, pattern: ActionPattern) -> None:
        """Save pattern to database."""
        cursor = self._conn.cursor()

        actions_json = json.dumps([a.model_dump() for a in pattern.actions])
        context_json = json.dumps(pattern.context_hints)

        cursor.execute(
            """
            INSERT OR REPLACE INTO patterns 
            (id, goal_template, actions, success_count, failure_count, 
             total_duration_ms, context_hints, created_at, last_used_at, last_success_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                pattern.id,
                pattern.goal_template,
                actions_json,
                pattern.success_count,
                pattern.failure_count,
                pattern.total_duration_ms,
                context_json,
                pattern.created_at,
                pattern.last_used_at,
                pattern.last_success_at,
            ),
        )

        self._conn.commit()

    def adapt_pattern(
        self,
        pattern: ActionPattern,
        current_context: ScreenContext,
    ) -> list[Action]:
        """
        Adapt a pattern's actions to the current screen context.

        Adjusts coordinates based on detected UI elements.

        Args:
            pattern: The pattern to adapt
            current_context: Current screen state

        Returns:
            List of adapted actions
        """
        adapted_actions = []

        for action in pattern.actions:
            adapted = self._adapt_action(action, current_context)
            adapted_actions.append(adapted)

        return adapted_actions

    def _adapt_action(self, action: Action, context: ScreenContext) -> Action:
        """Adapt a single action to current context."""
        if action.element_id is not None:
            element = context.get_element_by_id(action.element_id)
            if element:
                cx, cy = element.center
                return action.model_copy(update={"x": cx, "y": cy})

        if action.type == ActionType.CLICK and action.x is not None and action.y is not None:
            element = context.get_element_at_point(action.x, action.y)
            if element:
                cx, cy = element.center
                return action.model_copy(update={"x": cx, "y": cy})

        return action

    def get_all_patterns(self, limit: int = 100) -> list[ActionPattern]:
        """Get all stored patterns."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM patterns ORDER BY success_count DESC LIMIT ?", (limit,))
        return [self._row_to_pattern(row) for row in cursor.fetchall()]

    def get_reliable_patterns(self, min_success_rate: float = 0.7) -> list[ActionPattern]:
        """Get patterns with high success rates."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT * FROM patterns 
            WHERE (success_count + failure_count) >= 3
            AND CAST(success_count AS REAL) / (success_count + failure_count) >= ?
            ORDER BY success_count DESC
        """,
            (min_success_rate,),
        )
        return [self._row_to_pattern(row) for row in cursor.fetchall()]

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern by ID."""
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM patterns WHERE id = ?", (pattern_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def clear_unreliable_patterns(self, max_failure_rate: float = 0.7) -> int:
        """Remove patterns with high failure rates."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            DELETE FROM patterns 
            WHERE (success_count + failure_count) >= 3
            AND CAST(failure_count AS REAL) / (success_count + failure_count) >= ?
        """,
            (max_failure_rate,),
        )
        self._conn.commit()
        return cursor.rowcount

    def pattern_count(self) -> int:
        """Get total number of stored patterns."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patterns")
        return cursor.fetchone()[0]
