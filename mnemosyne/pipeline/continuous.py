from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from mnemosyne.capture.events import Event
from mnemosyne.capture.recorder import Recorder, RecorderConfig
from mnemosyne.llm.base import BaseLLMProvider
from mnemosyne.memory.persistent import PersistentMemory
from mnemosyne.store.database import Database
from mnemosyne.store.session_manager import SessionManager
from mnemosyne.pipeline.orchestrator import LearningPipeline, PipelineConfig


@dataclass
class ContinuousLearnerConfig:
    data_dir: Path = field(default_factory=lambda: Path.home() / ".mnemosyne")
    db_path: Path | None = None

    real_time_learning: bool = True
    prediction_on_every_event: bool = True

    event_buffer_size: int = 100
    learning_batch_size: int = 50

    pipeline_config: PipelineConfig = field(default_factory=PipelineConfig)
    recorder_config: RecorderConfig = field(default_factory=RecorderConfig)


class ContinuousLearner:
    def __init__(
        self,
        llm: BaseLLMProvider | None = None,
        config: ContinuousLearnerConfig | None = None,
        on_prediction: Callable[[dict], None] | None = None,
        on_question: Callable[[dict], None] | None = None,
        on_insight: Callable[[str], None] | None = None,
        on_status: Callable[[str], None] | None = None,
    ):
        self.config = config or ContinuousLearnerConfig()
        self.config.data_dir.mkdir(parents=True, exist_ok=True)

        self.llm = llm

        self._on_prediction = on_prediction
        self._on_question = on_question
        self._on_insight = on_insight
        self._on_status = on_status

        db_path = self.config.db_path or self.config.data_dir / "mnemosyne.db"
        self.database = Database(db_path)

        self.memory = PersistentMemory(
            data_dir=self.config.data_dir / "memory",
            llm=llm,
        )

        self.pipeline = LearningPipeline(
            database=self.database,
            memory=self.memory,
            llm=llm,
            config=self.config.pipeline_config,
            on_insight=on_insight,
            on_question=on_question,
            on_status=on_status,
        )

        self.session_manager: SessionManager | None = None
        self.recorder: Recorder | None = None

        self._running = False
        self._event_buffer: list[dict[str, Any]] = []
        self._start_time: float = 0

    def _emit_status(self, message: str) -> None:
        if self._on_status:
            self._on_status(message)

    async def start(self, session_name: str = "continuous_learning") -> None:
        self._running = True
        self._start_time = time.time()

        self._emit_status("Starting continuous learning system...")

        await self.pipeline.start()

        self.recorder = Recorder(
            config=self.config.recorder_config,
            on_event=self._handle_event,
        )

        self.session_manager = SessionManager(
            database=self.database,
            recorder=self.recorder,
        )

        session = self.session_manager.start_session(name=session_name)

        self._emit_status(f"Recording started: {session.id}")

    async def stop(self) -> dict[str, Any]:
        self._running = False

        session = None
        if self.session_manager:
            session = self.session_manager.stop_session()

        await self.pipeline.stop()

        stats = self.get_stats()

        self._emit_status("Continuous learning stopped")

        return {
            "session_id": session.id if session else None,
            "duration_minutes": (time.time() - self._start_time) / 60,
            "stats": stats,
        }

    def _handle_event(self, event: Event) -> None:
        if not self._running:
            return

        event_dict = {
            "id": getattr(event, "id", str(hash(str(event.timestamp)))),
            "action_type": event.action_type.value
            if hasattr(event, "action_type")
            else str(type(event).__name__),
            "timestamp": event.timestamp,
            "data": event.to_dict() if hasattr(event, "to_dict") else {},
        }

        if hasattr(event, "app_name"):
            event_dict["window_app"] = event.app_name
        if hasattr(event, "window_title"):
            event_dict["window_title"] = event.window_title

        self._event_buffer.append(event_dict)

        if len(self._event_buffer) > self.config.event_buffer_size:
            self._event_buffer = self._event_buffer[-self.config.event_buffer_size :]

        if self.config.real_time_learning and self.config.prediction_on_every_event:
            asyncio.create_task(self._process_event(event_dict))

    async def _process_event(self, event: dict[str, Any]) -> None:
        try:
            result = await self.pipeline.process_event(event)

            if result.get("prediction") and self._on_prediction:
                self._on_prediction(result["prediction"])

        except Exception as e:
            self._emit_status(f"Event processing error: {e}")

    def answer_question(self, question_id: str, answer: str) -> None:
        self.pipeline.answer_question(question_id, answer)

    def get_next_question(self) -> dict[str, Any] | None:
        question = self.pipeline.digital_twin.get_next_question()

        if question:
            return {
                "id": question.id,
                "text": question.question_text,
                "type": question.question_type.value,
                "priority": question.priority.value,
                "options": question.options,
            }

        return None

    def get_replication_score(self) -> float:
        return self.pipeline.get_replication_score()

    def get_stats(self) -> dict[str, Any]:
        pipeline_status = self.pipeline.get_status()

        return {
            "running": self._running,
            "uptime_minutes": (time.time() - self._start_time) / 60 if self._start_time else 0,
            "events_in_buffer": len(self._event_buffer),
            "replication_score": self.get_replication_score(),
            "pipeline": pipeline_status,
        }

    def get_improvement_suggestions(self) -> list[str]:
        return self.pipeline.get_improvement_suggestions()

    async def force_analysis(self) -> dict[str, Any]:
        return await self.pipeline.analyze_recent_events()

    async def force_consolidation(self) -> dict[str, Any]:
        return await self.pipeline.consolidate_memory()

    def pause(self) -> None:
        self.pipeline.pause()
        self._emit_status("Continuous learning paused")

    def resume(self) -> None:
        self.pipeline.resume()
        self._emit_status("Continuous learning resumed")
