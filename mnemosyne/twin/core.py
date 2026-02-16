from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field

from mnemosyne.llm.base import BaseLLMProvider
from mnemosyne.memory.persistent import PersistentMemory
from mnemosyne.memory.types import MemoryType
from mnemosyne.store.database import Database
from mnemosyne.twin.active_learner import ActiveLearner, LearningQuestion
from mnemosyne.twin.encoder import BehavioralEncoder
from mnemosyne.twin.predictor import IntentPredictor, PredictionResult
from mnemosyne.twin.profile import UserProfile, UserProfileStore, TimeOfDay


class TwinState(str, Enum):
    INITIALIZING = "initializing"
    OBSERVING = "observing"
    LEARNING = "learning"
    READY = "ready"
    EXECUTING = "executing"
    PAUSED = "paused"


class ReplicationMetrics(BaseModel):
    action_prediction_accuracy: float = 0.0
    intent_prediction_accuracy: float = 0.0
    pattern_recognition_rate: float = 0.0
    timing_accuracy: float = 0.0

    total_predictions: int = 0
    correct_predictions: int = 0

    learning_rate: float = 0.0
    profile_completeness: float = 0.0

    @property
    def overall_replication_score(self) -> float:
        weights = {
            "action": 0.35,
            "intent": 0.25,
            "pattern": 0.25,
            "timing": 0.15,
        }

        return (
            self.action_prediction_accuracy * weights["action"]
            + self.intent_prediction_accuracy * weights["intent"]
            + self.pattern_recognition_rate * weights["pattern"]
            + self.timing_accuracy * weights["timing"]
        )


@dataclass
class TwinConfig:
    data_dir: Path = field(default_factory=lambda: Path.home() / ".mnemosyne" / "twin")

    learning_enabled: bool = True
    active_questioning_enabled: bool = True

    max_questions_per_hour: int = 5
    min_question_interval_seconds: int = 300
    uncertainty_threshold: float = 0.6

    auto_learn_from_corrections: bool = True
    persist_patterns: bool = True

    context_window_size: int = 50
    embedding_dim: int = 128


class DigitalTwin:
    def __init__(
        self,
        database: Database,
        memory: PersistentMemory,
        llm: BaseLLMProvider | None = None,
        config: TwinConfig | None = None,
        on_question: Callable[[LearningQuestion], None] | None = None,
        on_prediction: Callable[[PredictionResult], None] | None = None,
    ):
        self.config = config or TwinConfig()
        self.config.data_dir.mkdir(parents=True, exist_ok=True)

        self.database = database
        self.memory = memory
        self.llm = llm

        self._on_question = on_question
        self._on_prediction = on_prediction

        self.encoder = BehavioralEncoder(
            embedding_dim=self.config.embedding_dim,
            max_sequence_length=self.config.context_window_size,
        )

        self.profile_store = UserProfileStore(self.config.data_dir)
        self.profile = self.profile_store.load_or_create()

        self.predictor = IntentPredictor(
            encoder=self.encoder,
            llm=llm,
        )

        self.active_learner = ActiveLearner(
            data_dir=self.config.data_dir,
            uncertainty_threshold=self.config.uncertainty_threshold,
            max_questions_per_hour=self.config.max_questions_per_hour,
            min_question_interval_seconds=self.config.min_question_interval_seconds,
        )

        if on_question:
            self.active_learner.set_question_callback(on_question)

        self.state = TwinState.INITIALIZING
        self.metrics = ReplicationMetrics()

        self._event_buffer: list[dict[str, Any]] = []
        self._last_prediction: PredictionResult | None = None
        self._session_start_time: float = time.time()

    async def initialize(self) -> None:
        self.state = TwinState.LEARNING

        vocab_path = self.config.data_dir / "vocabularies.json"
        if vocab_path.exists():
            self.encoder.load_vocabularies(str(vocab_path))

        await self._load_historical_patterns()

        self.profile_store.calculate_completeness()
        self.metrics.profile_completeness = self.profile.profile_completeness

        self.state = TwinState.READY

    async def _load_historical_patterns(self) -> None:
        sessions = self.database.list_sessions(limit=10)

        for session in sessions:
            events = list(self.database.iter_events(session.id))

            if len(events) < 10:
                continue

            event_dicts = [
                {
                    "id": e.id,
                    "action_type": e.action_type,
                    "window_app": e.window_app,
                    "window_title": e.window_title,
                    "timestamp": e.timestamp,
                    "data": e.data,
                    "inferred_intent": e.inferred_intent,
                }
                for e in events
            ]

            for i in range(5, len(event_dicts)):
                context = event_dicts[i - 5 : i]
                next_action = event_dicts[i]["action_type"]
                self.predictor.learn_pattern(context, next_action)

            self.profile_store.update_work_patterns(event_dicts)

    async def observe_event(self, event: dict[str, Any]) -> PredictionResult | None:
        self._event_buffer.append(event)

        if len(self._event_buffer) > self.config.context_window_size:
            self._event_buffer = self._event_buffer[-self.config.context_window_size :]

        if len(self._event_buffer) >= 5:
            context = {
                "app": event.get("window_app", ""),
                "title": event.get("window_title", ""),
                "timestamp": event.get("timestamp", time.time()),
            }

            prediction = self.predictor.predict_next_action(
                self._event_buffer[:-1],
                context,
                self.profile,
            )

            actual_action = event.get("action_type", "")
            self._record_prediction_accuracy(prediction, actual_action)

            if self._on_prediction:
                self._on_prediction(prediction)

            self._last_prediction = prediction
            return prediction

        return None

    def _record_prediction_accuracy(
        self,
        prediction: PredictionResult,
        actual_action: str,
    ) -> None:
        self.metrics.total_predictions += 1

        predicted = (
            prediction.predicted_action.split(":")[-1]
            if ":" in prediction.predicted_action
            else prediction.predicted_action
        )

        if predicted == actual_action:
            self.metrics.correct_predictions += 1
        elif self.config.auto_learn_from_corrections and prediction.confidence > 0.3:
            self.predictor.learn_from_correction(
                self._event_buffer[:-1],
                prediction.predicted_action,
                actual_action,
            )

        if self.metrics.total_predictions > 0:
            self.metrics.action_prediction_accuracy = (
                self.metrics.correct_predictions / self.metrics.total_predictions
            )

    async def process_session(
        self,
        session_id: str,
        generate_questions: bool = True,
    ) -> dict[str, Any]:
        events = list(self.database.iter_events(session_id))

        if not events:
            return {"error": "No events found", "session_id": session_id}

        event_dicts = [
            {
                "id": e.id,
                "action_type": e.action_type,
                "window_app": e.window_app,
                "window_title": e.window_title,
                "timestamp": e.timestamp,
                "data": e.data,
                "inferred_intent": e.inferred_intent,
            }
            for e in events
        ]

        for i in range(5, len(event_dicts)):
            context = event_dicts[i - 5 : i]
            next_action = event_dicts[i]["action_type"]
            self.predictor.learn_pattern(context, next_action)

        self.profile_store.update_work_patterns(event_dicts)

        self._update_profile_from_events(event_dicts)

        questions_generated = 0
        if generate_questions and self.config.active_questioning_enabled:
            uncertainties = self.active_learner.detect_uncertainty(event_dicts)
            questions = self.active_learner.generate_questions(uncertainties, event_dicts)
            self.active_learner.add_questions(questions)
            questions_generated = len(questions)

        self._store_session_insights(session_id, event_dicts)

        self.encoder.save_vocabularies(str(self.config.data_dir / "vocabularies.json"))

        return {
            "session_id": session_id,
            "events_processed": len(events),
            "patterns_learned": self.predictor.get_prediction_stats()["sequence_patterns"],
            "questions_generated": questions_generated,
            "profile_completeness": self.profile_store.calculate_completeness(),
        }

    def _update_profile_from_events(self, events: list[dict[str, Any]]) -> None:
        prev_app = None
        prev_time = None

        for event in events:
            app = event.get("window_app", "")
            timestamp = event.get("timestamp", 0)
            action = event.get("action_type", "")
            data = event.get("data", {})

            if prev_app and app != prev_app and prev_time:
                time_in_source = (timestamp - prev_time) * 1000
                self.profile_store.record_app_transition(prev_app, app, time_in_source)

            if action == "hotkey":
                keys = tuple(data.get("keys", []))
                if keys:
                    self.profile_store.record_hotkey(keys, app)

            if action == "key_type":
                char_count = len(data.get("text", ""))
                duration = data.get("duration_ms", 0)
                if char_count > 0 and duration > 0:
                    self.profile_store.record_typing_session(
                        app,
                        char_count,
                        duration,
                        corrections=data.get("corrections", 0),
                    )

            prev_app = app
            prev_time = timestamp

    def _store_session_insights(
        self,
        session_id: str,
        events: list[dict[str, Any]],
    ) -> None:
        if len(events) < 10:
            return

        app_counts: dict[str, int] = {}
        action_counts: dict[str, int] = {}

        for event in events:
            app = event.get("window_app", "unknown")
            action = event.get("action_type", "unknown")
            app_counts[app] = app_counts.get(app, 0) + 1
            action_counts[action] = action_counts.get(action, 0) + 1

        dominant_app = max(app_counts.items(), key=lambda x: x[1])[0]
        dominant_action = max(action_counts.items(), key=lambda x: x[1])[0]

        duration = events[-1].get("timestamp", 0) - events[0].get("timestamp", 0)

        insight = f"Session in {dominant_app}: {len(events)} events over {duration / 60:.1f} min, mostly {dominant_action}"

        self.memory.remember(
            content=insight,
            memory_type=MemoryType.OBSERVATION,
            context={
                "session_id": session_id,
                "dominant_app": dominant_app,
                "event_count": len(events),
                "duration_seconds": duration,
            },
            importance=0.6,
            tags=["session", "observation"],
        )

    async def answer_question(
        self,
        question_id: str,
        answer: str,
        confidence: float = 1.0,
    ) -> None:
        self.active_learner.submit_answer(question_id, answer, confidence)

        self.memory.remember(
            content=f"User answered: {answer}",
            memory_type=MemoryType.INSIGHT,
            context={"question_id": question_id, "confidence": confidence},
            importance=0.8,
            tags=["user_feedback", "learning"],
        )

    def get_next_question(self) -> LearningQuestion | None:
        return self.active_learner.get_next_question()

    async def predict_next(
        self,
        current_context: dict[str, Any] | None = None,
    ) -> PredictionResult:
        context = current_context or {}

        return self.predictor.predict_next_action(
            self._event_buffer,
            context,
            self.profile,
        )

    async def get_intent(
        self,
        events: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        target_events = events or self._event_buffer

        if not target_events:
            return {"intent": "unknown", "confidence": 0.0}

        intent_prediction = await self.predictor.predict_intent(target_events)

        return {
            "intent": intent_prediction.intent,
            "confidence": intent_prediction.confidence,
            "evidence": intent_prediction.supporting_evidence,
        }

    def get_replication_score(self) -> float:
        self.metrics.profile_completeness = self.profile.profile_completeness

        predictor_stats = self.predictor.get_prediction_stats()
        self.metrics.pattern_recognition_rate = min(predictor_stats["sequence_patterns"] / 100, 1.0)

        return self.metrics.overall_replication_score

    def get_status(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "replication_score": self.get_replication_score(),
            "metrics": self.metrics.model_dump(),
            "profile_completeness": self.profile.profile_completeness,
            "predictor_stats": self.predictor.get_prediction_stats(),
            "learning_stats": self.active_learner.get_learning_stats(),
            "encoder_stats": self.encoder.get_vocabulary_stats(),
            "event_buffer_size": len(self._event_buffer),
            "session_duration_hours": (time.time() - self._session_start_time) / 3600,
        }

    def get_improvement_suggestions(self) -> list[str]:
        suggestions = []

        if self.metrics.action_prediction_accuracy < 0.5:
            suggestions.append(
                "Action prediction accuracy is low. Answer more questions about your intent."
            )

        if self.profile.profile_completeness < 0.3:
            suggestions.append(
                "Profile is incomplete. Use the system more to help it learn your patterns."
            )

        learning_stats = self.active_learner.get_learning_stats()
        if learning_stats["pending_questions"] > 10:
            suggestions.append(
                f"You have {learning_stats['pending_questions']} unanswered questions. "
                "Answering them will improve accuracy."
            )

        predictor_stats = self.predictor.get_prediction_stats()
        if predictor_stats["sequence_patterns"] < 50:
            suggestions.append("More usage patterns needed. Continue using the system normally.")

        if not suggestions:
            suggestions.append("Keep using the system! The more you use it, the better it learns.")

        return suggestions

    async def export_twin_state(self) -> dict[str, Any]:
        return {
            "version": "1.0",
            "exported_at": time.time(),
            "profile": self.profile.model_dump(),
            "metrics": self.metrics.model_dump(),
            "predictor_stats": self.predictor.get_prediction_stats(),
            "learning_stats": self.active_learner.get_learning_stats(),
            "encoder_stats": self.encoder.get_vocabulary_stats(),
        }

    def pause(self) -> None:
        self.state = TwinState.PAUSED

    def resume(self) -> None:
        self.state = TwinState.READY
