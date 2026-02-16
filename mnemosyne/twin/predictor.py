from __future__ import annotations

import json
import time
from typing import Any, Sequence

import numpy as np
from pydantic import BaseModel, Field

from mnemosyne.llm.base import BaseLLMProvider, Message
from mnemosyne.twin.encoder import BehavioralEncoder, SequenceEmbedding
from mnemosyne.twin.profile import UserProfile, TimeOfDay


class PredictionResult(BaseModel):
    predicted_action: str
    confidence: float
    reasoning: str | None = None

    alternatives: list[tuple[str, float]] = Field(default_factory=list)

    context_used: dict[str, Any] = Field(default_factory=dict)
    prediction_method: str = "unknown"
    latency_ms: float = 0.0


class ActionPrediction(BaseModel):
    action_type: str
    probability: float
    parameters: dict[str, Any] = Field(default_factory=dict)


class IntentPrediction(BaseModel):
    intent: str
    confidence: float
    supporting_evidence: list[str] = Field(default_factory=list)


class IntentPredictor:
    INTENT_CATEGORIES = [
        "navigation",
        "data_entry",
        "communication",
        "file_management",
        "development",
        "research",
        "entertainment",
        "system_control",
        "creative_work",
        "unknown",
    ]

    def __init__(
        self,
        encoder: BehavioralEncoder,
        llm: BaseLLMProvider | None = None,
        use_llm_fallback: bool = True,
    ):
        self.encoder = encoder
        self.llm = llm
        self.use_llm_fallback = use_llm_fallback

        self._pattern_cache: dict[str, list[tuple[SequenceEmbedding, str]]] = {}
        self._intent_history: list[tuple[str, str, float]] = []

        self._action_intent_map: dict[str, dict[str, float]] = {}
        self._sequence_intent_map: dict[str, str] = {}

    def predict_next_action(
        self,
        recent_events: Sequence[dict[str, Any]],
        current_context: dict[str, Any],
        user_profile: UserProfile | None = None,
    ) -> PredictionResult:
        start_time = time.time()

        if not recent_events:
            return PredictionResult(
                predicted_action="unknown",
                confidence=0.0,
                prediction_method="no_data",
            )

        sequence_embedding = self.encoder.encode_sequence(list(recent_events))

        pattern_prediction = self._predict_from_patterns(
            sequence_embedding,
            recent_events,
        )

        if pattern_prediction and pattern_prediction.confidence > 0.7:
            pattern_prediction.latency_ms = (time.time() - start_time) * 1000
            return pattern_prediction

        profile_prediction = None
        if user_profile:
            profile_prediction = self._predict_from_profile(
                recent_events,
                current_context,
                user_profile,
            )

        if profile_prediction and profile_prediction.confidence > 0.6:
            profile_prediction.latency_ms = (time.time() - start_time) * 1000
            return profile_prediction

        statistical_prediction = self._predict_from_statistics(recent_events)

        if pattern_prediction and profile_prediction:
            combined = self._combine_predictions(
                [
                    pattern_prediction,
                    profile_prediction,
                    statistical_prediction,
                ]
            )
            combined.latency_ms = (time.time() - start_time) * 1000
            return combined

        best = max(
            [p for p in [pattern_prediction, profile_prediction, statistical_prediction] if p],
            key=lambda p: p.confidence,
            default=statistical_prediction,
        )

        if best:
            best.latency_ms = (time.time() - start_time) * 1000

        return best or PredictionResult(
            predicted_action="unknown",
            confidence=0.0,
            prediction_method="fallback",
            latency_ms=(time.time() - start_time) * 1000,
        )

    def _predict_from_patterns(
        self,
        sequence_embedding: SequenceEmbedding,
        recent_events: Sequence[dict[str, Any]],
    ) -> PredictionResult | None:
        last_actions = tuple(e.get("action_type", "") for e in recent_events[-3:])
        pattern_key = "→".join(last_actions)

        if pattern_key in self._sequence_intent_map:
            return PredictionResult(
                predicted_action=self._sequence_intent_map[pattern_key],
                confidence=0.75,
                reasoning=f"Matched learned pattern: {pattern_key}",
                prediction_method="pattern_match",
                context_used={"pattern": pattern_key},
            )

        if sequence_embedding.dominant_app in self._pattern_cache:
            cached_patterns = self._pattern_cache[sequence_embedding.dominant_app]

            query_vec = np.array(sequence_embedding.vector)
            best_match = None
            best_similarity = 0.0

            for cached_emb, next_action in cached_patterns:
                cached_vec = np.array(cached_emb.vector)

                norm_q = np.linalg.norm(query_vec)
                norm_c = np.linalg.norm(cached_vec)

                if norm_q > 0 and norm_c > 0:
                    similarity = float(np.dot(query_vec, cached_vec) / (norm_q * norm_c))
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = next_action

            if best_match and best_similarity > 0.8:
                return PredictionResult(
                    predicted_action=best_match,
                    confidence=best_similarity * 0.9,
                    reasoning=f"Similar sequence found (similarity: {best_similarity:.2f})",
                    prediction_method="embedding_similarity",
                )

        return None

    def _predict_from_profile(
        self,
        recent_events: Sequence[dict[str, Any]],
        current_context: dict[str, Any],
        user_profile: UserProfile,
    ) -> PredictionResult | None:
        current_app = current_context.get("app", "")
        if not current_app and recent_events:
            current_app = recent_events[-1].get("window_app", "")

        hour = time.localtime().tm_hour
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

        predictions = user_profile.preferences.app_transitions

        for transition in predictions:
            if transition.from_app.lower() == current_app.lower():
                confidence = min(transition.count / 50, 0.8)
                return PredictionResult(
                    predicted_action=f"switch_to:{transition.to_app}",
                    confidence=confidence,
                    reasoning=f"User typically switches from {current_app} to {transition.to_app}",
                    prediction_method="profile_transition",
                    context_used={
                        "from_app": current_app,
                        "to_app": transition.to_app,
                        "historical_count": transition.count,
                    },
                )

        hotkeys = user_profile.preferences.hotkey_preferences
        for hotkey in hotkeys[:5]:
            if hotkey.associated_app and hotkey.associated_app.lower() == current_app.lower():
                confidence = min(hotkey.frequency / 30, 0.7)
                key_str = "+".join(hotkey.keys)
                return PredictionResult(
                    predicted_action=f"hotkey:{key_str}",
                    confidence=confidence,
                    reasoning=f"User frequently uses {key_str} in {current_app}",
                    prediction_method="profile_hotkey",
                    context_used={
                        "hotkey": key_str,
                        "frequency": hotkey.frequency,
                    },
                )

        return None

    def _predict_from_statistics(
        self,
        recent_events: Sequence[dict[str, Any]],
    ) -> PredictionResult:
        if not recent_events:
            return PredictionResult(
                predicted_action="unknown",
                confidence=0.0,
                prediction_method="statistical_empty",
            )

        action_counts: dict[str, int] = {}
        for event in recent_events:
            action = event.get("action_type", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1

        total = sum(action_counts.values())
        action_probs = {a: c / total for a, c in action_counts.items()}

        most_common = max(action_probs.items(), key=lambda x: x[1])

        alternatives = sorted(
            [(a, p) for a, p in action_probs.items() if a != most_common[0]],
            key=lambda x: x[1],
            reverse=True,
        )[:3]

        return PredictionResult(
            predicted_action=most_common[0],
            confidence=most_common[1] * 0.5,
            reasoning=f"Most frequent action in recent history ({most_common[1]:.0%})",
            prediction_method="statistical",
            alternatives=alternatives,
            context_used={"action_distribution": action_probs},
        )

    def _combine_predictions(
        self,
        predictions: list[PredictionResult],
    ) -> PredictionResult:
        valid_predictions = [p for p in predictions if p and p.confidence > 0]

        if not valid_predictions:
            return PredictionResult(
                predicted_action="unknown",
                confidence=0.0,
                prediction_method="combined_empty",
            )

        action_scores: dict[str, float] = {}
        action_reasoning: dict[str, list[str]] = {}

        for pred in valid_predictions:
            action = pred.predicted_action
            weight = pred.confidence

            action_scores[action] = action_scores.get(action, 0) + weight

            if action not in action_reasoning:
                action_reasoning[action] = []
            if pred.reasoning:
                action_reasoning[action].append(pred.reasoning)

        best_action = max(action_scores.items(), key=lambda x: x[1])
        total_weight = sum(action_scores.values())

        alternatives = sorted(
            [(a, s / total_weight) for a, s in action_scores.items() if a != best_action[0]],
            key=lambda x: x[1],
            reverse=True,
        )[:3]

        return PredictionResult(
            predicted_action=best_action[0],
            confidence=best_action[1] / total_weight,
            reasoning=" | ".join(action_reasoning.get(best_action[0], [])),
            prediction_method="combined",
            alternatives=alternatives,
            context_used={
                "methods_used": [p.prediction_method for p in valid_predictions],
            },
        )

    async def predict_intent(
        self,
        events: Sequence[dict[str, Any]],
        use_llm: bool = True,
    ) -> IntentPrediction:
        if not events:
            return IntentPrediction(
                intent="unknown",
                confidence=0.0,
            )

        action_types = [e.get("action_type", "") for e in events]
        apps = list(set(e.get("window_app", "") for e in events))

        evidence = []

        if len(apps) == 1:
            app = apps[0].lower()
            if any(x in app for x in ["code", "vscode", "pycharm", "intellij"]):
                evidence.append(f"Working in development tool: {apps[0]}")
                intent = "development"
            elif any(x in app for x in ["slack", "discord", "mail", "messages"]):
                evidence.append(f"Using communication app: {apps[0]}")
                intent = "communication"
            elif any(x in app for x in ["chrome", "safari", "firefox", "arc"]):
                evidence.append(f"Browsing in: {apps[0]}")
                intent = "research"
            else:
                intent = "unknown"
        else:
            evidence.append(f"Multiple apps used: {', '.join(apps[:3])}")
            intent = "multitasking"

        typing_count = sum(1 for a in action_types if a in ("key_type", "key_press"))
        click_count = sum(1 for a in action_types if "click" in a)

        if typing_count > click_count * 2:
            evidence.append(f"Heavy typing ({typing_count} events)")
            if intent == "unknown":
                intent = "data_entry"
        elif click_count > typing_count * 2:
            evidence.append(f"Heavy clicking ({click_count} events)")
            if intent == "unknown":
                intent = "navigation"

        if use_llm and self.llm and self.use_llm_fallback and intent == "unknown":
            llm_intent = await self._predict_intent_with_llm(events)
            if llm_intent:
                return llm_intent

        confidence = 0.3 if intent == "unknown" else 0.6 + (len(evidence) * 0.1)

        return IntentPrediction(
            intent=intent,
            confidence=min(confidence, 0.9),
            supporting_evidence=evidence,
        )

    async def _predict_intent_with_llm(
        self,
        events: Sequence[dict[str, Any]],
    ) -> IntentPrediction | None:
        if not self.llm:
            return None

        event_summary = []
        for e in events[:10]:
            action = e.get("action_type", "unknown")
            app = e.get("window_app", "unknown")
            event_summary.append(f"- {action} in {app}")

        prompt = f"""Analyze these user actions and determine the high-level intent:

{chr(10).join(event_summary)}

Respond with JSON:
{{"intent": "one of: {", ".join(self.INTENT_CATEGORIES)}", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

        messages = [
            Message(role="system", content="You analyze user behavior to understand intent."),
            Message(role="user", content=prompt),
        ]

        try:
            response = await self.llm.complete(messages)
            data = json.loads(response.content)

            return IntentPrediction(
                intent=data.get("intent", "unknown"),
                confidence=data.get("confidence", 0.5),
                supporting_evidence=[data.get("reasoning", "LLM inference")],
            )
        except Exception:
            return None

    def learn_pattern(
        self,
        events: Sequence[dict[str, Any]],
        next_action: str,
    ) -> None:
        if len(events) < 2:
            return

        sequence_embedding = self.encoder.encode_sequence(list(events))

        app = sequence_embedding.dominant_app
        if app not in self._pattern_cache:
            self._pattern_cache[app] = []

        self._pattern_cache[app].append((sequence_embedding, next_action))

        if len(self._pattern_cache[app]) > 1000:
            self._pattern_cache[app] = self._pattern_cache[app][-500:]

        action_sequence = "→".join(e.get("action_type", "") for e in events[-3:])
        self._sequence_intent_map[action_sequence] = next_action

    def learn_from_correction(
        self,
        events: Sequence[dict[str, Any]],
        predicted_action: str,
        actual_action: str,
    ) -> None:
        self.learn_pattern(events, actual_action)

        last_action = events[-1].get("action_type", "") if events else ""
        app = events[-1].get("window_app", "") if events else ""

        key = f"{last_action}:{app}"
        if key not in self._action_intent_map:
            self._action_intent_map[key] = {}

        self._action_intent_map[key][predicted_action] = (
            self._action_intent_map[key].get(predicted_action, 0.5) * 0.8
        )
        self._action_intent_map[key][actual_action] = (
            self._action_intent_map[key].get(actual_action, 0.5) * 1.2
        )

    def get_prediction_stats(self) -> dict[str, Any]:
        return {
            "cached_patterns": sum(len(v) for v in self._pattern_cache.values()),
            "apps_with_patterns": list(self._pattern_cache.keys()),
            "sequence_patterns": len(self._sequence_intent_map),
            "action_intent_mappings": len(self._action_intent_map),
            "intent_history_size": len(self._intent_history),
        }
