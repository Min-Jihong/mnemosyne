"""Decision Reasoning - Capture and replicate WHY the user makes decisions."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    NAVIGATION = "navigation"
    TOOL_SELECTION = "tool_selection"
    ACTION_CHOICE = "action_choice"
    CONTENT_DECISION = "content_decision"
    TIMING = "timing"
    PRIORITY = "priority"
    APPROACH = "approach"


class DecisionContext(BaseModel):
    app: str = ""
    window_title: str = ""
    work_context: str = ""

    visible_options: list[str] = Field(default_factory=list)
    recent_actions: list[str] = Field(default_factory=list)

    time_of_day: str = ""
    day_of_week: str = ""

    project_state: dict[str, Any] = Field(default_factory=dict)


class Decision(BaseModel):
    id: str
    decision_type: DecisionType
    timestamp: float

    chosen_option: str
    rejected_options: list[str] = Field(default_factory=list)

    context: DecisionContext

    explicit_reasoning: str = ""
    inferred_reasoning: str = ""

    confidence_in_inference: float = 0.0

    validated: bool = False
    user_correction: str = ""

    patterns_matched: list[str] = Field(default_factory=list)


class DecisionPattern(BaseModel):
    id: str
    pattern_type: DecisionType

    condition: dict[str, Any]
    typical_decision: str
    reasoning: str

    occurrence_count: int = 0
    last_occurrence: float = 0.0
    confidence: float = 0.0


class DecisionReasoner:
    def __init__(
        self,
        llm: Any = None,
        data_dir: Path | None = None,
    ):
        self.llm = llm
        self.data_dir = data_dir or Path.home() / ".mnemosyne" / "decisions"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._decisions: list[Decision] = []
        self._patterns: dict[str, DecisionPattern] = {}

        self._load_patterns()

    def _load_patterns(self) -> None:
        patterns_path = self.data_dir / "patterns.json"
        if patterns_path.exists():
            try:
                data = json.loads(patterns_path.read_text())
                for pattern_data in data:
                    pattern = DecisionPattern(**pattern_data)
                    self._patterns[pattern.id] = pattern
            except Exception:
                pass

    def _save_patterns(self) -> None:
        patterns_path = self.data_dir / "patterns.json"
        data = [p.model_dump() for p in self._patterns.values()]
        patterns_path.write_text(json.dumps(data, indent=2))

    async def record_decision(
        self,
        decision_type: DecisionType,
        chosen_option: str,
        context: DecisionContext,
        rejected_options: list[str] | None = None,
    ) -> Decision:
        decision = Decision(
            id=f"dec_{int(time.time() * 1000)}",
            decision_type=decision_type,
            timestamp=time.time(),
            chosen_option=chosen_option,
            rejected_options=rejected_options or [],
            context=context,
        )

        matching_patterns = self._find_matching_patterns(decision)
        decision.patterns_matched = [p.id for p in matching_patterns]

        if matching_patterns:
            decision.inferred_reasoning = self._infer_reasoning_from_patterns(
                decision, matching_patterns
            )
            decision.confidence_in_inference = max(p.confidence for p in matching_patterns)
        elif self.llm:
            decision.inferred_reasoning = await self._infer_reasoning_with_llm(decision)
            decision.confidence_in_inference = 0.5

        self._update_patterns(decision)
        self._decisions.append(decision)
        self._save_decision(decision)

        return decision

    def _find_matching_patterns(self, decision: Decision) -> list[DecisionPattern]:
        matching = []

        for pattern in self._patterns.values():
            if pattern.pattern_type != decision.decision_type:
                continue

            if self._pattern_matches_context(pattern.condition, decision.context):
                matching.append(pattern)

        return sorted(matching, key=lambda p: p.confidence, reverse=True)

    def _pattern_matches_context(
        self,
        condition: dict[str, Any],
        context: DecisionContext,
    ) -> bool:
        for key, expected in condition.items():
            actual = getattr(context, key, None)

            if actual is None:
                return False

            if isinstance(expected, str):
                if expected.lower() not in str(actual).lower():
                    return False
            elif isinstance(expected, list):
                if not any(e in str(actual) for e in expected):
                    return False

        return True

    def _infer_reasoning_from_patterns(
        self,
        decision: Decision,
        patterns: list[DecisionPattern],
    ) -> str:
        if not patterns:
            return ""

        best_pattern = patterns[0]

        reasoning = best_pattern.reasoning
        reasoning = reasoning.replace("{option}", decision.chosen_option)
        reasoning = reasoning.replace("{app}", decision.context.app)

        return reasoning

    async def _infer_reasoning_with_llm(self, decision: Decision) -> str:
        if not self.llm:
            return ""

        prompt = f"""Analyze this decision and infer the reasoning:

Decision Type: {decision.decision_type.value}
Chosen: {decision.chosen_option}
Rejected: {", ".join(decision.rejected_options) if decision.rejected_options else "N/A"}
Context:
- App: {decision.context.app}
- Window: {decision.context.window_title}
- Work: {decision.context.work_context}
- Recent actions: {", ".join(decision.context.recent_actions[-3:]) if decision.context.recent_actions else "N/A"}

In one sentence, explain WHY the user likely made this decision:"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.generate(messages)
            return response.strip()
        except Exception:
            return ""

    def _update_patterns(self, decision: Decision) -> None:
        pattern_key = self._generate_pattern_key(decision)

        if pattern_key in self._patterns:
            pattern = self._patterns[pattern_key]
            pattern.occurrence_count += 1
            pattern.last_occurrence = time.time()

            if decision.chosen_option == pattern.typical_decision:
                pattern.confidence = min(pattern.confidence + 0.05, 0.95)
            else:
                pattern.typical_decision = decision.chosen_option
                pattern.confidence = max(pattern.confidence - 0.1, 0.3)
        else:
            self._patterns[pattern_key] = DecisionPattern(
                id=pattern_key,
                pattern_type=decision.decision_type,
                condition=self._extract_pattern_condition(decision.context),
                typical_decision=decision.chosen_option,
                reasoning=decision.inferred_reasoning
                or f"User typically chooses {decision.chosen_option} in this context",
                occurrence_count=1,
                last_occurrence=time.time(),
                confidence=0.4,
            )

        self._save_patterns()

    def _generate_pattern_key(self, decision: Decision) -> str:
        ctx = decision.context
        parts = [
            decision.decision_type.value,
            ctx.app.lower().replace(" ", "_") if ctx.app else "unknown",
            ctx.work_context.lower().replace(" ", "_") if ctx.work_context else "unknown",
        ]
        return "_".join(parts)

    def _extract_pattern_condition(self, context: DecisionContext) -> dict[str, Any]:
        condition = {}

        if context.app:
            condition["app"] = context.app.lower()
        if context.work_context:
            condition["work_context"] = context.work_context

        return condition

    def _save_decision(self, decision: Decision) -> None:
        date_str = time.strftime("%Y-%m-%d")
        file_path = self.data_dir / f"decisions_{date_str}.jsonl"

        with open(file_path, "a") as f:
            f.write(decision.model_dump_json() + "\n")

    async def validate_reasoning(
        self,
        decision_id: str,
        user_explanation: str,
    ) -> dict[str, Any]:
        decision = next((d for d in self._decisions if d.id == decision_id), None)

        if not decision:
            return {"error": "Decision not found"}

        decision.explicit_reasoning = user_explanation
        decision.validated = True

        pattern_key = self._generate_pattern_key(decision)
        if pattern_key in self._patterns:
            self._patterns[pattern_key].reasoning = user_explanation
            self._patterns[pattern_key].confidence = min(
                self._patterns[pattern_key].confidence + 0.2, 0.95
            )
            self._save_patterns()

        return {
            "validated": True,
            "pattern_updated": pattern_key in self._patterns,
            "new_confidence": self._patterns.get(
                pattern_key,
                DecisionPattern(
                    id="",
                    pattern_type=DecisionType.ACTION_CHOICE,
                    condition={},
                    typical_decision="",
                    reasoning="",
                ),
            ).confidence,
        }

    async def predict_decision(
        self,
        decision_type: DecisionType,
        context: DecisionContext,
        options: list[str],
    ) -> dict[str, Any]:
        mock_decision = Decision(
            id="pred",
            decision_type=decision_type,
            timestamp=time.time(),
            chosen_option="",
            context=context,
        )

        matching_patterns = self._find_matching_patterns(mock_decision)

        if matching_patterns:
            best = matching_patterns[0]

            if best.typical_decision in options:
                return {
                    "predicted_choice": best.typical_decision,
                    "reasoning": best.reasoning,
                    "confidence": best.confidence,
                    "pattern_based": True,
                }

        if self.llm:
            prediction = await self._predict_with_llm(decision_type, context, options)
            return prediction

        return {
            "predicted_choice": options[0] if options else None,
            "reasoning": "No pattern found, defaulting to first option",
            "confidence": 0.1,
            "pattern_based": False,
        }

    async def _predict_with_llm(
        self,
        decision_type: DecisionType,
        context: DecisionContext,
        options: list[str],
    ) -> dict[str, Any]:
        if not self.llm:
            return {"predicted_choice": None, "confidence": 0.0}

        recent_decisions = [d for d in self._decisions[-20:] if d.decision_type == decision_type]

        examples = ""
        for d in recent_decisions[:5]:
            examples += f"- Chose '{d.chosen_option}' because: {d.inferred_reasoning or d.explicit_reasoning}\n"

        prompt = f"""Based on user's decision history, predict their choice.

Decision Type: {decision_type.value}
Context:
- App: {context.app}
- Work: {context.work_context}

Options: {", ".join(options)}

User's past decisions in similar situations:
{examples if examples else "No similar decisions recorded yet."}

Predict which option the user would choose and explain why.
Return JSON: {{"choice": "option", "reasoning": "why", "confidence": 0.0-1.0}}"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.generate(messages)

            response_text = response.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            result = json.loads(response_text)

            return {
                "predicted_choice": result.get("choice"),
                "reasoning": result.get("reasoning", ""),
                "confidence": result.get("confidence", 0.5),
                "pattern_based": False,
            }
        except Exception:
            return {
                "predicted_choice": options[0] if options else None,
                "reasoning": "LLM prediction failed",
                "confidence": 0.1,
                "pattern_based": False,
            }

    def get_decision_patterns(self, min_confidence: float = 0.5) -> list[DecisionPattern]:
        return [p for p in self._patterns.values() if p.confidence >= min_confidence]

    def get_reasoning_stats(self) -> dict[str, Any]:
        total = len(self._decisions)
        validated = sum(1 for d in self._decisions if d.validated)

        type_counts = {}
        for d in self._decisions:
            t = d.decision_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_decisions": total,
            "validated_decisions": validated,
            "validation_rate": validated / total if total > 0 else 0,
            "patterns_count": len(self._patterns),
            "decisions_by_type": type_counts,
            "avg_inference_confidence": sum(d.confidence_in_inference for d in self._decisions)
            / total
            if total > 0
            else 0,
        }
