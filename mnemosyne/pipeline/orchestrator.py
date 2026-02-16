from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from mnemosyne.capture.recorder import Recorder, RecorderConfig
from mnemosyne.llm.base import BaseLLMProvider
from mnemosyne.memory.persistent import PersistentMemory
from mnemosyne.memory.types import MemoryType
from mnemosyne.reason.curious import CuriousLLM
from mnemosyne.reason.intent import IntentInferrer
from mnemosyne.store.database import Database
from mnemosyne.store.session_manager import SessionManager
from mnemosyne.twin.core import DigitalTwin, TwinConfig


class PipelineState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PROCESSING = "processing"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class PipelineConfig:
    data_dir: Path = field(default_factory=lambda: Path.home() / ".mnemosyne")

    auto_analyze_interval_seconds: int = 300
    auto_consolidate_interval_seconds: int = 3600

    batch_size: int = 100
    max_events_per_analysis: int = 500

    enable_curious_questions: bool = True
    enable_intent_inference: bool = True
    enable_pattern_learning: bool = True
    enable_memory_consolidation: bool = True

    twin_config: TwinConfig = field(default_factory=TwinConfig)


class LearningPipeline:
    def __init__(
        self,
        database: Database,
        memory: PersistentMemory,
        llm: BaseLLMProvider | None = None,
        config: PipelineConfig | None = None,
        on_insight: Callable[[str], None] | None = None,
        on_question: Callable[[dict], None] | None = None,
        on_status: Callable[[str], None] | None = None,
    ):
        self.config = config or PipelineConfig()
        self.config.data_dir.mkdir(parents=True, exist_ok=True)

        self.database = database
        self.memory = memory
        self.llm = llm

        self._on_insight = on_insight
        self._on_question = on_question
        self._on_status = on_status

        self.digital_twin = DigitalTwin(
            database=database,
            memory=memory,
            llm=llm,
            config=self.config.twin_config,
            on_question=lambda q: self._handle_question(q) if on_question else None,
        )

        self.intent_inferrer: IntentInferrer | None = None
        self.curious_llm: CuriousLLM | None = None

        if llm:
            from mnemosyne.reason.context import ContextBuilder

            self.intent_inferrer = IntentInferrer(
                llm=llm,
                database=database,
                context_builder=ContextBuilder(),
            )
            self.curious_llm = CuriousLLM(
                llm=llm,
                database=database,
            )

        self.state = PipelineState.STOPPED
        self._last_analysis_time: float = 0
        self._last_consolidation_time: float = 0
        self._processed_event_ids: set[str] = set()

        self._analysis_task: asyncio.Task | None = None
        self._consolidation_task: asyncio.Task | None = None

    def _handle_question(self, question: Any) -> None:
        if self._on_question:
            self._on_question(
                {
                    "id": question.id,
                    "text": question.question_text,
                    "type": question.question_type.value,
                    "options": question.options,
                }
            )

    def _emit_status(self, message: str) -> None:
        if self._on_status:
            self._on_status(message)

    def _emit_insight(self, insight: str) -> None:
        if self._on_insight:
            self._on_insight(insight)

    async def start(self) -> None:
        self.state = PipelineState.STARTING
        self._emit_status("Initializing learning pipeline...")

        await self.digital_twin.initialize()

        self._analysis_task = asyncio.create_task(self._analysis_loop())

        if self.config.enable_memory_consolidation:
            self._consolidation_task = asyncio.create_task(self._consolidation_loop())

        self.state = PipelineState.RUNNING
        self._emit_status("Learning pipeline started")

    async def stop(self) -> None:
        self.state = PipelineState.STOPPED

        if self._analysis_task:
            self._analysis_task.cancel()
            try:
                await self._analysis_task
            except asyncio.CancelledError:
                pass

        if self._consolidation_task:
            self._consolidation_task.cancel()
            try:
                await self._consolidation_task
            except asyncio.CancelledError:
                pass

        self._emit_status("Learning pipeline stopped")

    async def _analysis_loop(self) -> None:
        while self.state in (PipelineState.RUNNING, PipelineState.PROCESSING):
            try:
                await asyncio.sleep(self.config.auto_analyze_interval_seconds)

                if self.state == PipelineState.PAUSED:
                    continue

                await self.analyze_recent_events()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._emit_status(f"Analysis error: {e}")

    async def _consolidation_loop(self) -> None:
        while self.state in (PipelineState.RUNNING, PipelineState.PROCESSING):
            try:
                await asyncio.sleep(self.config.auto_consolidate_interval_seconds)

                if self.state == PipelineState.PAUSED:
                    continue

                await self.consolidate_memory()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._emit_status(f"Consolidation error: {e}")

    async def analyze_recent_events(self) -> dict[str, Any]:
        self.state = PipelineState.PROCESSING

        sessions = self.database.list_sessions(limit=5)

        total_processed = 0
        total_intents = 0
        total_patterns = 0

        for session in sessions:
            events = list(self.database.iter_events(session.id))

            new_events = [e for e in events if e.id not in self._processed_event_ids]

            if not new_events:
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
                for e in new_events[: self.config.max_events_per_analysis]
            ]

            result = await self.digital_twin.process_session(session.id)
            total_patterns += result.get("patterns_learned", 0)

            if self.config.enable_intent_inference and self.intent_inferrer:
                events_without_intent = [e for e in new_events if not e.inferred_intent][
                    : self.config.batch_size
                ]

                for event in events_without_intent:
                    try:
                        await self.intent_inferrer.infer_intent(event)
                        total_intents += 1
                    except Exception:
                        pass

            if self.config.enable_curious_questions and self.curious_llm:
                stored_events = [e for e in events if e.id in [ed["id"] for ed in event_dicts]]

                if len(stored_events) >= 10:
                    try:
                        curiosities = await self.curious_llm.observe_and_wonder(stored_events[:50])

                        for curiosity in curiosities:
                            self.memory.remember(
                                content=curiosity.question,
                                memory_type=MemoryType.INSIGHT,
                                context={
                                    "category": curiosity.category,
                                    "importance": curiosity.importance,
                                },
                                importance=curiosity.importance,
                                tags=["curiosity", curiosity.category],
                            )
                            self._emit_insight(curiosity.question)
                    except Exception:
                        pass

            for e in new_events[: self.config.max_events_per_analysis]:
                self._processed_event_ids.add(e.id)

            total_processed += len(new_events)

        self._last_analysis_time = time.time()
        self.state = PipelineState.RUNNING

        return {
            "events_processed": total_processed,
            "intents_inferred": total_intents,
            "patterns_learned": total_patterns,
            "timestamp": self._last_analysis_time,
        }

    async def consolidate_memory(self) -> dict[str, Any]:
        if not self.llm:
            return {"error": "No LLM configured for consolidation"}

        self._emit_status("Consolidating memories...")

        insights = await self.memory.consolidate()

        for insight in insights:
            self._emit_insight(f"Consolidated insight: {insight.content}")

        self._last_consolidation_time = time.time()

        return {
            "insights_generated": len(insights),
            "timestamp": self._last_consolidation_time,
        }

    async def process_event(self, event: dict[str, Any]) -> dict[str, Any]:
        prediction = await self.digital_twin.observe_event(event)

        return {
            "prediction": prediction.model_dump() if prediction else None,
            "replication_score": self.digital_twin.get_replication_score(),
        }

    def answer_question(self, question_id: str, answer: str) -> None:
        asyncio.create_task(self.digital_twin.answer_question(question_id, answer))

    def get_status(self) -> dict[str, Any]:
        return {
            "pipeline_state": self.state.value,
            "twin_status": self.digital_twin.get_status(),
            "last_analysis": self._last_analysis_time,
            "last_consolidation": self._last_consolidation_time,
            "processed_events": len(self._processed_event_ids),
        }

    def get_replication_score(self) -> float:
        return self.digital_twin.get_replication_score()

    def get_improvement_suggestions(self) -> list[str]:
        return self.digital_twin.get_improvement_suggestions()

    def pause(self) -> None:
        self.state = PipelineState.PAUSED
        self.digital_twin.pause()
        self._emit_status("Learning pipeline paused")

    def resume(self) -> None:
        self.state = PipelineState.RUNNING
        self.digital_twin.resume()
        self._emit_status("Learning pipeline resumed")
