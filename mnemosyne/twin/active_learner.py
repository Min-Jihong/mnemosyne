from __future__ import annotations

import json
import random
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    INTENT = "intent"
    PREFERENCE = "preference"
    PATTERN = "pattern"
    CONFIRMATION = "confirmation"
    CORRECTION = "correction"


class QuestionPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LearningQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_type: QuestionType
    priority: QuestionPriority

    question_text: str
    context: dict[str, Any] = Field(default_factory=dict)

    options: list[str] | None = None
    allows_free_text: bool = True

    related_event_ids: list[str] = Field(default_factory=list)
    related_pattern: str | None = None

    created_at: float = Field(default_factory=time.time)
    answered_at: float | None = None
    answer: str | None = None
    answer_confidence: float = 0.0

    learning_value: float = 0.5
    times_asked: int = 0

    @property
    def is_answered(self) -> bool:
        return self.answer is not None

    @property
    def age_hours(self) -> float:
        return (time.time() - self.created_at) / 3600


class UncertaintySource(BaseModel):
    source_type: str
    description: str
    confidence: float
    event_ids: list[str] = Field(default_factory=list)


class ActiveLearner:
    QUESTION_TEMPLATES = {
        "intent_why": "Why did you {action} in {app}?",
        "intent_goal": "What were you trying to accomplish when you {action}?",
        "pattern_confirm": "I noticed you often {pattern}. Is this intentional?",
        "pattern_why": "Why do you prefer to {pattern}?",
        "preference_choice": "When {context}, do you prefer {option_a} or {option_b}?",
        "correction": "I predicted {predicted}, but you did {actual}. Why?",
        "sequence_intent": "What's the goal of this sequence: {sequence}?",
        "time_based": "Why do you usually {action} around {time}?",
        "app_switch": "What triggers you to switch from {from_app} to {to_app}?",
    }

    def __init__(
        self,
        data_dir: Path | str,
        uncertainty_threshold: float = 0.6,
        max_questions_per_hour: int = 5,
        min_question_interval_seconds: int = 300,
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.uncertainty_threshold = uncertainty_threshold
        self.max_questions_per_hour = max_questions_per_hour
        self.min_question_interval = min_question_interval_seconds

        self._db_path = self.data_dir / "active_learning.db"
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._init_schema()

        self._pending_questions: list[LearningQuestion] = []
        self._last_question_time: float = 0
        self._questions_this_hour: int = 0
        self._hour_start: float = time.time()

        self._on_question: Callable[[LearningQuestion], None] | None = None

    def _init_schema(self) -> None:
        cursor = self._conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                question_type TEXT,
                priority TEXT,
                question_text TEXT,
                context TEXT,
                options TEXT,
                related_event_ids TEXT,
                related_pattern TEXT,
                created_at REAL,
                answered_at REAL,
                answer TEXT,
                answer_confidence REAL,
                learning_value REAL,
                times_asked INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_intents (
                id TEXT PRIMARY KEY,
                action_pattern TEXT,
                context_pattern TEXT,
                intent TEXT,
                confidence REAL,
                source_question_id TEXT,
                created_at REAL,
                usage_count INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(question_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_questions_answered ON questions(answered_at)
        """)

        self._conn.commit()

    def set_question_callback(self, callback: Callable[[LearningQuestion], None]) -> None:
        self._on_question = callback

    def detect_uncertainty(
        self,
        events: list[dict[str, Any]],
        predictions: list[dict[str, Any]] | None = None,
    ) -> list[UncertaintySource]:
        uncertainties: list[UncertaintySource] = []

        if not events:
            return uncertainties

        events_without_intent = [e for e in events if not e.get("inferred_intent")]
        if len(events_without_intent) > len(events) * 0.3:
            uncertainties.append(
                UncertaintySource(
                    source_type="missing_intent",
                    description=f"{len(events_without_intent)} events without inferred intent",
                    confidence=0.3,
                    event_ids=[e.get("id", "") for e in events_without_intent[:10]],
                )
            )

        action_sequences: dict[tuple, list[int]] = {}
        for i in range(len(events) - 2):
            seq = tuple(e.get("action_type", "") for e in events[i : i + 3])
            if seq not in action_sequences:
                action_sequences[seq] = []
            action_sequences[seq].append(i)

        for seq, indices in action_sequences.items():
            if len(indices) >= 3:
                uncertainties.append(
                    UncertaintySource(
                        source_type="repeated_pattern",
                        description=f"Pattern '{' → '.join(seq)}' repeated {len(indices)} times",
                        confidence=0.4,
                        event_ids=[events[i].get("id", "") for i in indices[:5]],
                    )
                )

        for i in range(1, len(events)):
            prev_time = events[i - 1].get("timestamp", 0)
            curr_time = events[i].get("timestamp", 0)
            gap = curr_time - prev_time

            if gap > 5.0:
                uncertainties.append(
                    UncertaintySource(
                        source_type="long_pause",
                        description=f"{gap:.1f}s pause before {events[i].get('action_type', 'action')}",
                        confidence=0.5,
                        event_ids=[events[i].get("id", "")],
                    )
                )

        if predictions:
            for i, (event, pred) in enumerate(zip(events, predictions)):
                pred_confidence = pred.get("confidence", 1.0)
                if pred_confidence < self.uncertainty_threshold:
                    uncertainties.append(
                        UncertaintySource(
                            source_type="low_confidence_prediction",
                            description=f"Low confidence ({pred_confidence:.2f}) for {event.get('action_type', 'action')}",
                            confidence=pred_confidence,
                            event_ids=[event.get("id", "")],
                        )
                    )

                if pred.get("predicted_action") != event.get("action_type"):
                    uncertainties.append(
                        UncertaintySource(
                            source_type="prediction_mismatch",
                            description=f"Predicted {pred.get('predicted_action')}, actual {event.get('action_type')}",
                            confidence=0.3,
                            event_ids=[event.get("id", "")],
                        )
                    )

        return uncertainties

    def generate_questions(
        self,
        uncertainties: list[UncertaintySource],
        events: list[dict[str, Any]],
    ) -> list[LearningQuestion]:
        questions: list[LearningQuestion] = []

        for uncertainty in uncertainties:
            if uncertainty.source_type == "missing_intent":
                sample_events = [e for e in events if e.get("id") in uncertainty.event_ids][:3]

                for event in sample_events:
                    q = self._create_intent_question(event)
                    if q:
                        questions.append(q)

            elif uncertainty.source_type == "repeated_pattern":
                q = LearningQuestion(
                    question_type=QuestionType.PATTERN,
                    priority=QuestionPriority.MEDIUM,
                    question_text=self.QUESTION_TEMPLATES["pattern_why"].format(
                        pattern=uncertainty.description.split("'")[1]
                    ),
                    context={"pattern": uncertainty.description},
                    related_event_ids=uncertainty.event_ids,
                    related_pattern=uncertainty.description,
                    learning_value=0.7,
                )
                questions.append(q)

            elif uncertainty.source_type == "long_pause":
                event = next((e for e in events if e.get("id") in uncertainty.event_ids), None)
                if event:
                    q = LearningQuestion(
                        question_type=QuestionType.INTENT,
                        priority=QuestionPriority.HIGH,
                        question_text=f"You paused for a moment before {event.get('action_type', 'this action')}. What were you considering?",
                        context={
                            "pause_duration": uncertainty.description,
                            "action": event.get("action_type"),
                            "app": event.get("window_app"),
                        },
                        related_event_ids=uncertainty.event_ids,
                        options=[
                            "Thinking about what to do next",
                            "Reading/reviewing content",
                            "Waiting for something to load",
                            "Distracted/interrupted",
                        ],
                        learning_value=0.8,
                    )
                    questions.append(q)

            elif uncertainty.source_type == "prediction_mismatch":
                q = LearningQuestion(
                    question_type=QuestionType.CORRECTION,
                    priority=QuestionPriority.CRITICAL,
                    question_text=uncertainty.description.replace(
                        "Predicted", "I expected you to"
                    ).replace(", actual", ", but you did"),
                    context={"mismatch": uncertainty.description},
                    related_event_ids=uncertainty.event_ids,
                    learning_value=0.9,
                )
                questions.append(q)

        questions.sort(
            key=lambda q: (
                q.priority == QuestionPriority.CRITICAL,
                q.priority == QuestionPriority.HIGH,
                q.learning_value,
            ),
            reverse=True,
        )

        return questions

    def _create_intent_question(self, event: dict[str, Any]) -> LearningQuestion | None:
        action = event.get("action_type", "")
        app = event.get("window_app", "unknown app")
        data = event.get("data", {})

        if action in ("click", "double_click"):
            question_text = f"What were you trying to do when you clicked in {app}?"
        elif action in ("key_type", "key_press"):
            text_preview = data.get("text", "")[:30]
            question_text = f"What was the purpose of typing '{text_preview}...' in {app}?"
        elif action == "hotkey":
            keys = data.get("keys", [])
            question_text = f"Why did you use {'+'.join(keys)} in {app}?"
        elif action == "window_change":
            question_text = f"Why did you switch to {app}?"
        else:
            question_text = self.QUESTION_TEMPLATES["intent_why"].format(
                action=action,
                app=app,
            )

        return LearningQuestion(
            question_type=QuestionType.INTENT,
            priority=QuestionPriority.MEDIUM,
            question_text=question_text,
            context={
                "action_type": action,
                "app": app,
                "data": data,
            },
            related_event_ids=[event.get("id", "")],
            learning_value=0.6,
        )

    def should_ask_question(self) -> bool:
        now = time.time()

        if now - self._hour_start > 3600:
            self._hour_start = now
            self._questions_this_hour = 0

        if self._questions_this_hour >= self.max_questions_per_hour:
            return False

        if now - self._last_question_time < self.min_question_interval:
            return False

        return len(self._pending_questions) > 0

    def get_next_question(self) -> LearningQuestion | None:
        if not self.should_ask_question():
            return None

        if not self._pending_questions:
            return None

        question = self._pending_questions.pop(0)
        question.times_asked += 1

        self._last_question_time = time.time()
        self._questions_this_hour += 1

        self._save_question(question)

        if self._on_question:
            self._on_question(question)

        return question

    def submit_answer(
        self,
        question_id: str,
        answer: str,
        confidence: float = 1.0,
    ) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            UPDATE questions
            SET answered_at = ?, answer = ?, answer_confidence = ?
            WHERE id = ?
        """,
            (time.time(), answer, confidence, question_id),
        )
        self._conn.commit()

        cursor.execute(
            """
            SELECT question_type, context, related_event_ids, related_pattern
            FROM questions WHERE id = ?
        """,
            (question_id,),
        )
        row = cursor.fetchone()

        if row:
            q_type, context_json, event_ids_json, pattern = row
            context = json.loads(context_json) if context_json else {}

            if q_type == QuestionType.INTENT.value:
                self._store_learned_intent(
                    action_pattern=context.get("action_type", ""),
                    context_pattern=context.get("app", ""),
                    intent=answer,
                    confidence=confidence,
                    source_question_id=question_id,
                )

    def _store_learned_intent(
        self,
        action_pattern: str,
        context_pattern: str,
        intent: str,
        confidence: float,
        source_question_id: str,
    ) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO learned_intents 
            (id, action_pattern, context_pattern, intent, confidence, source_question_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                str(uuid.uuid4()),
                action_pattern,
                context_pattern,
                intent,
                confidence,
                source_question_id,
                time.time(),
            ),
        )
        self._conn.commit()

    def get_learned_intent(
        self,
        action_type: str,
        app: str,
    ) -> tuple[str, float] | None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT intent, confidence FROM learned_intents
            WHERE action_pattern = ? AND context_pattern = ?
            ORDER BY confidence DESC, created_at DESC
            LIMIT 1
        """,
            (action_type, app.lower()),
        )

        row = cursor.fetchone()
        if row:
            cursor.execute(
                """
                UPDATE learned_intents SET usage_count = usage_count + 1
                WHERE action_pattern = ? AND context_pattern = ?
            """,
                (action_type, app.lower()),
            )
            self._conn.commit()
            return (row[0], row[1])

        return None

    def add_questions(self, questions: list[LearningQuestion]) -> None:
        for q in questions:
            if not self._is_duplicate_question(q):
                self._pending_questions.append(q)

        self._pending_questions.sort(
            key=lambda q: (
                q.priority == QuestionPriority.CRITICAL,
                q.priority == QuestionPriority.HIGH,
                q.learning_value,
            ),
            reverse=True,
        )

    def _is_duplicate_question(self, question: LearningQuestion) -> bool:
        for pending in self._pending_questions:
            if (
                pending.question_type == question.question_type
                and pending.related_event_ids == question.related_event_ids
            ):
                return True

        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM questions
            WHERE question_type = ? AND related_event_ids = ? AND answered_at IS NOT NULL
        """,
            (question.question_type.value, json.dumps(question.related_event_ids)),
        )

        return cursor.fetchone()[0] > 0

    def _save_question(self, question: LearningQuestion) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO questions
            (id, question_type, priority, question_text, context, options,
             related_event_ids, related_pattern, created_at, answered_at,
             answer, answer_confidence, learning_value, times_asked)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                question.id,
                question.question_type.value,
                question.priority.value,
                question.question_text,
                json.dumps(question.context),
                json.dumps(question.options) if question.options else None,
                json.dumps(question.related_event_ids),
                question.related_pattern,
                question.created_at,
                question.answered_at,
                question.answer,
                question.answer_confidence,
                question.learning_value,
                question.times_asked,
            ),
        )
        self._conn.commit()

    def get_unanswered_questions(self, limit: int = 10) -> list[LearningQuestion]:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT id, question_type, priority, question_text, context, options,
                   related_event_ids, related_pattern, created_at, learning_value, times_asked
            FROM questions
            WHERE answered_at IS NULL
            ORDER BY 
                CASE priority 
                    WHEN 'critical' THEN 0 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    ELSE 3 
                END,
                learning_value DESC
            LIMIT ?
        """,
            (limit,),
        )

        questions = []
        for row in cursor.fetchall():
            questions.append(
                LearningQuestion(
                    id=row[0],
                    question_type=QuestionType(row[1]),
                    priority=QuestionPriority(row[2]),
                    question_text=row[3],
                    context=json.loads(row[4]) if row[4] else {},
                    options=json.loads(row[5]) if row[5] else None,
                    related_event_ids=json.loads(row[6]) if row[6] else [],
                    related_pattern=row[7],
                    created_at=row[8],
                    learning_value=row[9],
                    times_asked=row[10],
                )
            )

        return questions

    def get_learning_stats(self) -> dict[str, Any]:
        cursor = self._conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM questions")
        total_questions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM questions WHERE answered_at IS NOT NULL")
        answered_questions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM learned_intents")
        learned_intents = cursor.fetchone()[0]

        cursor.execute("""
            SELECT question_type, COUNT(*) 
            FROM questions 
            GROUP BY question_type
        """)
        questions_by_type = dict(cursor.fetchall())

        cursor.execute("""
            SELECT AVG(answer_confidence) 
            FROM questions 
            WHERE answered_at IS NOT NULL
        """)
        avg_confidence = cursor.fetchone()[0] or 0.0

        return {
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "answer_rate": answered_questions / total_questions if total_questions > 0 else 0,
            "learned_intents": learned_intents,
            "questions_by_type": questions_by_type,
            "average_confidence": avg_confidence,
            "pending_questions": len(self._pending_questions),
        }
