"""
Curiosity Engine - AI's intrinsic motivation to understand WHY.

Builds deep understanding of user's decision-making process through strategic questioning.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field


class CuriosityType(str, Enum):
    DECISION_REASONING = "decision_reasoning"
    CONTEXT_UNDERSTANDING = "context_understanding"
    GOAL_CLARIFICATION = "goal_clarification"
    PROCESS_LEARNING = "process_learning"
    PATTERN_CONFIRMATION = "pattern_confirmation"
    PREFERENCE_DISCOVERY = "preference_discovery"
    SEMANTIC_CLARIFICATION = "semantic_clarification"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    RELATIONSHIP_MAPPING = "relationship_mapping"
    TIMING_UNDERSTANDING = "timing_understanding"
    PRIORITY_LEARNING = "priority_learning"
    INTERRUPTION_HANDLING = "interruption_handling"


class CuriosityDepth(str, Enum):
    SURFACE = "surface"
    INTERMEDIATE = "intermediate"
    DEEP = "deep"
    PHILOSOPHICAL = "philosophical"


@dataclass
class CuriousObservation:
    observation_type: str
    context: dict[str, Any]
    timestamp: float
    confidence: float
    triggers_curiosity: bool
    curiosity_score: float


@dataclass
class DeepQuestion:
    id: str
    question_text: str
    curiosity_type: CuriosityType
    depth: CuriosityDepth
    observation: CuriousObservation
    related_events: list[str]
    expected_insight: str
    learning_weight: float
    asked_at: float | None = None
    answered: bool = False
    answer: str | None = None
    user_confidence: float = 0.0
    follow_up_questions: list[str] = field(default_factory=list)
    leads_to_understanding: list[str] = field(default_factory=list)


class ThoughtModel(BaseModel):
    decision_factors: dict[str, float] = Field(default_factory=dict)
    risk_tolerance: float = 0.5
    perfectionism_level: float = 0.5
    focus_patterns: dict[str, Any] = Field(default_factory=dict)
    interruption_handling: str = "unknown"
    multitasking_style: str = "unknown"
    problem_decomposition: str = "unknown"
    research_vs_build: float = 0.5
    iteration_speed: str = "unknown"
    writing_style: dict[str, Any] = Field(default_factory=dict)
    code_style_preferences: dict[str, Any] = Field(default_factory=dict)
    expertise_areas: list[str] = Field(default_factory=list)
    learning_areas: list[str] = Field(default_factory=list)
    self_awareness: float = 0.5
    adaptability: float = 0.5


class CuriosityEngine:
    def __init__(
        self,
        data_dir: Path,
        llm: Any = None,
        vision_llm: Any = None,
        max_questions_per_session: int = 10,
        curiosity_cooldown_seconds: int = 120,
    ):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.llm = llm
        self.vision_llm = vision_llm
        self.max_questions_per_session = max_questions_per_session
        self.curiosity_cooldown_seconds = curiosity_cooldown_seconds

        self.thought_model = self._load_thought_model()
        self._pending_questions: list[DeepQuestion] = []
        self._asked_questions: list[DeepQuestion] = []
        self._answered_questions: list[DeepQuestion] = []
        self._last_question_time: float = 0
        self._session_question_count: int = 0
        self._understanding_gaps: dict[str, float] = {}
        self._observation_buffer: list[CuriousObservation] = []
        self._on_question: Callable[[DeepQuestion], None] | None = None
        self._on_insight: Callable[[str, Any], None] | None = None

    def _load_thought_model(self) -> ThoughtModel:
        model_path = self.data_dir / "thought_model.json"
        if model_path.exists():
            try:
                return ThoughtModel(**json.loads(model_path.read_text()))
            except Exception:
                pass
        return ThoughtModel()

    def _save_thought_model(self) -> None:
        model_path = self.data_dir / "thought_model.json"
        model_path.write_text(self.thought_model.model_dump_json(indent=2))

    def set_question_callback(self, callback: Callable[[DeepQuestion], None]) -> None:
        self._on_question = callback

    def set_insight_callback(self, callback: Callable[[str, Any], None]) -> None:
        self._on_insight = callback

    async def observe(
        self,
        event: dict[str, Any],
        screen_context: dict[str, Any] | None = None,
        semantic_context: dict[str, Any] | None = None,
    ) -> CuriousObservation | None:
        observation = self._create_observation(event, screen_context, semantic_context)

        if observation.triggers_curiosity:
            self._observation_buffer.append(observation)
            if self._should_ask_question():
                await self._generate_questions_from_observations()

        return observation

    def _create_observation(
        self,
        event: dict[str, Any],
        screen_context: dict[str, Any] | None,
        semantic_context: dict[str, Any] | None,
    ) -> CuriousObservation:
        observation_type = self._classify_observation(event)
        curiosity_score = self._calculate_curiosity_score(event, screen_context, semantic_context)

        return CuriousObservation(
            observation_type=observation_type,
            context={"event": event, "screen": screen_context, "semantic": semantic_context},
            timestamp=time.time(),
            confidence=0.8,
            triggers_curiosity=curiosity_score > 0.5,
            curiosity_score=curiosity_score,
        )

    def _classify_observation(self, event: dict[str, Any]) -> str:
        action = event.get("action_type", "")
        if action == "mouse_click":
            return "decision_point"
        if action == "window_change":
            return "context_switch"
        if action in ("key_type", "hotkey"):
            return "content_creation"
        if action == "mouse_scroll":
            return "navigation"
        return "general"

    def _calculate_curiosity_score(
        self,
        event: dict[str, Any],
        screen_context: dict[str, Any] | None,
        semantic_context: dict[str, Any] | None,
    ) -> float:
        score = 0.0
        action = event.get("action_type", "")

        if action == "mouse_click":
            score += 0.3
        if action == "window_change":
            score += 0.4

        app = event.get("window_app", "")
        app_understanding = self._understanding_gaps.get(f"app:{app}", 0.5)
        score += (1.0 - app_understanding) * 0.3

        if semantic_context and semantic_context.get("work_type") == "unknown":
            score += 0.3

        return min(max(score, 0.0), 1.0)

    def _should_ask_question(self) -> bool:
        if time.time() - self._last_question_time < self.curiosity_cooldown_seconds:
            return False
        if self._session_question_count >= self.max_questions_per_session:
            return False
        if len(self._observation_buffer) < 3:
            return False

        avg_curiosity = sum(o.curiosity_score for o in self._observation_buffer) / len(
            self._observation_buffer
        )
        return avg_curiosity > 0.4

    async def _generate_questions_from_observations(self) -> list[DeepQuestion]:
        if not self._observation_buffer:
            return []

        sorted_obs = sorted(
            self._observation_buffer, key=lambda o: o.curiosity_score, reverse=True
        )[:5]
        questions = []

        for obs in sorted_obs:
            curiosity_type = self._determine_curiosity_type(obs)
            depth = self._determine_depth(obs)
            question = await self._generate_question(obs, curiosity_type, depth)
            if question:
                questions.append(question)

        questions.sort(key=lambda q: q.learning_weight, reverse=True)
        self._pending_questions.extend(questions[:3])
        self._observation_buffer = []

        if questions and self._on_question:
            self._on_question(questions[0])
            self._last_question_time = time.time()
            self._session_question_count += 1

        return questions

    def _determine_curiosity_type(self, obs: CuriousObservation) -> CuriosityType:
        obs_type = obs.observation_type
        if obs_type == "decision_point":
            return CuriosityType.DECISION_REASONING
        elif obs_type == "context_switch":
            return CuriosityType.GOAL_CLARIFICATION
        elif obs_type == "content_creation":
            return CuriosityType.SEMANTIC_CLARIFICATION
        return CuriosityType.CONTEXT_UNDERSTANDING

    def _determine_depth(self, obs: CuriousObservation) -> CuriosityDepth:
        model_completeness = self._calculate_model_completeness()
        if model_completeness < 0.3:
            return CuriosityDepth.SURFACE
        elif model_completeness < 0.6:
            return CuriosityDepth.INTERMEDIATE
        elif model_completeness < 0.85:
            return CuriosityDepth.DEEP
        return CuriosityDepth.PHILOSOPHICAL

    def _calculate_model_completeness(self) -> float:
        model = self.thought_model
        completeness = 0.0
        total_fields = 6

        if model.decision_factors:
            completeness += 1
        if model.focus_patterns:
            completeness += 1
        if model.problem_decomposition != "unknown":
            completeness += 1
        if model.writing_style:
            completeness += 1
        if model.code_style_preferences:
            completeness += 1
        if model.expertise_areas:
            completeness += 1

        return completeness / total_fields

    async def _generate_question(
        self,
        obs: CuriousObservation,
        curiosity_type: CuriosityType,
        depth: CuriosityDepth,
    ) -> DeepQuestion | None:
        event = obs.context.get("event", {})
        screen = obs.context.get("screen", {})
        semantic = obs.context.get("semantic", {})
        templates = self._get_question_templates(curiosity_type, depth)

        if self.llm:
            question_text = await self._llm_generate_question(
                templates, event, screen, semantic, curiosity_type, depth
            )
        else:
            question_text = self._template_question(templates, event, screen, semantic)

        if not question_text:
            return None

        return DeepQuestion(
            id=f"q_{int(time.time() * 1000)}",
            question_text=question_text,
            curiosity_type=curiosity_type,
            depth=depth,
            observation=obs,
            related_events=[event.get("id", "")] if event else [],
            expected_insight=self._expected_insight_for_type(curiosity_type),
            learning_weight=self._calculate_learning_weight(curiosity_type, depth),
        )

    def _get_question_templates(
        self, curiosity_type: CuriosityType, depth: CuriosityDepth
    ) -> list[str]:
        templates = {
            CuriosityType.DECISION_REASONING: {
                CuriosityDepth.SURFACE: [
                    "I noticed you clicked on {element}. What were you trying to do?"
                ],
                CuriosityDepth.INTERMEDIATE: [
                    "When you clicked {element}, were there other options you considered?"
                ],
                CuriosityDepth.DEEP: ["When you chose {action}, how did you weigh the tradeoffs?"],
                CuriosityDepth.PHILOSOPHICAL: [
                    "Do you consciously apply rules when making choices like {action}?"
                ],
            },
            CuriosityType.GOAL_CLARIFICATION: {
                CuriosityDepth.SURFACE: ["What are you working on right now?"],
                CuriosityDepth.INTERMEDIATE: [
                    "You've been switching between {app1} and {app2}. How do these tasks relate?"
                ],
                CuriosityDepth.DEEP: ["How does this task fit into your larger objectives?"],
                CuriosityDepth.PHILOSOPHICAL: ["How do you decide what's important?"],
            },
            CuriosityType.SEMANTIC_CLARIFICATION: {
                CuriosityDepth.SURFACE: ["What are you writing/coding here?"],
                CuriosityDepth.INTERMEDIATE: [
                    "I see you're writing {content_type}. What's the context?"
                ],
                CuriosityDepth.DEEP: ["Why did you structure this {content_type} this way?"],
                CuriosityDepth.PHILOSOPHICAL: [
                    "Your writing/coding style seems to have patterns. Is this intentional?"
                ],
            },
            CuriosityType.CONTEXT_UNDERSTANDING: {
                CuriosityDepth.SURFACE: ["What's happening in your work right now?"],
                CuriosityDepth.INTERMEDIATE: ["Can you give me context on {app}?"],
                CuriosityDepth.DEEP: [
                    "Help me understand the broader context of your current work."
                ],
                CuriosityDepth.PHILOSOPHICAL: ["How do you typically organize your work context?"],
            },
        }
        return templates.get(curiosity_type, {}).get(depth, ["What are you doing?"])

    async def _llm_generate_question(
        self,
        templates: list[str],
        event: dict[str, Any],
        screen: dict[str, Any],
        semantic: dict[str, Any],
        curiosity_type: CuriosityType,
        depth: CuriosityDepth,
    ) -> str:
        if not self.llm:
            return ""

        system_prompt = f"""You are an AI learning about a user's work patterns.
Ask insightful questions about WHY they do things, HOW they think, and WHAT their goals are.
Focus: {curiosity_type.value}, Depth: {depth.value}
Generate ONE clear, conversational question."""

        context_parts = []
        if event:
            context_parts.append(
                f"Event: {event.get('action_type', 'unknown')} in {event.get('window_app', 'unknown')}"
            )
        if screen:
            context_parts.append(f"Screen shows: {screen.get('description', 'unknown')}")
        if semantic:
            context_parts.append(f"Work context: {semantic.get('work_type', 'unknown')}")

        user_prompt = f"Context:\n{chr(10).join(context_parts)}\n\nTemplates:\n{chr(10).join(templates)}\n\nGenerate a question:"

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = await self.llm.generate(messages)
            return response.strip()
        except Exception:
            return templates[0] if templates else "What are you working on?"

    def _template_question(
        self,
        templates: list[str],
        event: dict[str, Any],
        screen: dict[str, Any],
        semantic: dict[str, Any],
    ) -> str:
        if not templates:
            return "What are you working on?"

        template = templates[0]
        replacements = {
            "{app}": event.get("window_app", "this app"),
            "{app1}": event.get("window_app", "app"),
            "{app2}": "another app",
            "{action}": event.get("action_type", "that"),
            "{element}": screen.get("clicked_element", "that") if screen else "that",
            "{content_type}": semantic.get("work_type", "content") if semantic else "content",
        }

        for key, value in replacements.items():
            template = template.replace(key, value)
        return template

    def _expected_insight_for_type(self, curiosity_type: CuriosityType) -> str:
        insights = {
            CuriosityType.DECISION_REASONING: "Understanding of user's decision-making factors",
            CuriosityType.CONTEXT_UNDERSTANDING: "Broader context of current work",
            CuriosityType.GOAL_CLARIFICATION: "User's goals and priorities",
            CuriosityType.PROCESS_LEARNING: "How user approaches tasks",
            CuriosityType.PATTERN_CONFIRMATION: "Validation of observed patterns",
            CuriosityType.PREFERENCE_DISCOVERY: "User's preferences and style",
            CuriosityType.SEMANTIC_CLARIFICATION: "Meaning of current work",
            CuriosityType.DOMAIN_KNOWLEDGE: "Domain-specific knowledge",
            CuriosityType.RELATIONSHIP_MAPPING: "How concepts relate",
            CuriosityType.TIMING_UNDERSTANDING: "Why things happen when they do",
            CuriosityType.PRIORITY_LEARNING: "How user prioritizes",
            CuriosityType.INTERRUPTION_HANDLING: "How user handles interruptions",
        }
        return insights.get(curiosity_type, "General understanding")

    def _calculate_learning_weight(
        self, curiosity_type: CuriosityType, depth: CuriosityDepth
    ) -> float:
        type_weights = {
            CuriosityType.DECISION_REASONING: 0.9,
            CuriosityType.GOAL_CLARIFICATION: 0.85,
            CuriosityType.SEMANTIC_CLARIFICATION: 0.8,
            CuriosityType.PROCESS_LEARNING: 0.75,
            CuriosityType.CONTEXT_UNDERSTANDING: 0.7,
        }
        base_weight = type_weights.get(curiosity_type, 0.5)

        depth_multipliers = {
            CuriosityDepth.SURFACE: 0.6,
            CuriosityDepth.INTERMEDIATE: 0.8,
            CuriosityDepth.DEEP: 1.0,
            CuriosityDepth.PHILOSOPHICAL: 1.1,
        }
        depth_mult = depth_multipliers.get(depth, 0.7)
        gap_boost = 1.0 + (0.5 * (1.0 - self._calculate_model_completeness()))

        return min(base_weight * depth_mult * gap_boost, 1.0)

    async def process_answer(
        self, question_id: str, answer: str, confidence: float = 1.0
    ) -> dict[str, Any]:
        question = next(
            (q for q in self._pending_questions + self._asked_questions if q.id == question_id),
            None,
        )
        if not question:
            return {"error": "Question not found"}

        question.answered = True
        question.answer = answer
        question.user_confidence = confidence

        if question in self._pending_questions:
            self._pending_questions.remove(question)
        if question in self._asked_questions:
            self._asked_questions.remove(question)
        self._answered_questions.append(question)

        insights = await self._extract_insights(question, answer)
        self._update_thought_model(question, answer, insights)
        self._save_thought_model()

        if self._on_insight and insights:
            for insight_type, insight_value in insights.items():
                self._on_insight(insight_type, insight_value)

        follow_ups = await self._generate_follow_ups(question, answer, insights)
        return {
            "question_id": question_id,
            "insights_gained": insights,
            "model_updated": True,
            "follow_up_questions": len(follow_ups),
        }

    async def _extract_insights(self, question: DeepQuestion, answer: str) -> dict[str, Any]:
        if self.llm:
            system_prompt = """Analyze user's answer. Extract JSON with keys:
- decision_factors: dict of factor -> importance (0-1)
- work_goal: string
- process_description: string
- preference: string
- domain_knowledge: string
Return only valid JSON."""

            user_prompt = f"Question type: {question.curiosity_type.value}\nQuestion: {question.question_text}\nAnswer: {answer}\n\nExtract insights:"

            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
                response = await self.llm.generate(messages)
                return json.loads(response)
            except Exception:
                pass

        return {"raw_answer": answer, "question_type": question.curiosity_type.value}

    def _update_thought_model(
        self, question: DeepQuestion, answer: str, insights: dict[str, Any]
    ) -> None:
        model = self.thought_model

        if (
            question.curiosity_type == CuriosityType.DECISION_REASONING
            and "decision_factors" in insights
        ):
            for factor, importance in insights["decision_factors"].items():
                model.decision_factors[factor] = importance

        elif (
            question.curiosity_type == CuriosityType.GOAL_CLARIFICATION and "work_goal" in insights
        ):
            model.focus_patterns["current_goal"] = insights["work_goal"]

        elif (
            question.curiosity_type == CuriosityType.PROCESS_LEARNING
            and "process_description" in insights
        ):
            model.problem_decomposition = insights["process_description"]

        elif (
            question.curiosity_type == CuriosityType.PREFERENCE_DISCOVERY
            and "preference" in insights
        ):
            if "code" in answer.lower():
                model.code_style_preferences["preference"] = insights["preference"]
            else:
                model.writing_style["preference"] = insights["preference"]

        elif (
            question.curiosity_type == CuriosityType.SEMANTIC_CLARIFICATION
            and "domain_knowledge" in insights
        ):
            domain = insights["domain_knowledge"]
            if domain and domain not in model.expertise_areas:
                model.expertise_areas.append(domain)

        area = question.curiosity_type.value
        current_gap = self._understanding_gaps.get(area, 1.0)
        self._understanding_gaps[area] = current_gap * (1 - question.learning_weight * 0.3)

    async def _generate_follow_ups(
        self, question: DeepQuestion, answer: str, insights: dict[str, Any]
    ) -> list[DeepQuestion]:
        follow_ups = []

        if question.depth not in (CuriosityDepth.DEEP, CuriosityDepth.PHILOSOPHICAL):
            return follow_ups

        if len(answer) > 100 or "because" in answer.lower() or "usually" in answer.lower():
            relations = {
                CuriosityType.DECISION_REASONING: CuriosityType.PROCESS_LEARNING,
                CuriosityType.GOAL_CLARIFICATION: CuriosityType.PRIORITY_LEARNING,
                CuriosityType.SEMANTIC_CLARIFICATION: CuriosityType.DOMAIN_KNOWLEDGE,
                CuriosityType.CONTEXT_UNDERSTANDING: CuriosityType.GOAL_CLARIFICATION,
            }
            deeper_type = relations.get(
                question.curiosity_type, CuriosityType.CONTEXT_UNDERSTANDING
            )

            follow_up = await self._generate_question(
                question.observation, deeper_type, CuriosityDepth.DEEP
            )
            if follow_up:
                follow_up.question_text = f"That's interesting. {follow_up.question_text}"
                follow_ups.append(follow_up)
                self._pending_questions.append(follow_up)

        return follow_ups

    def get_next_question(self) -> DeepQuestion | None:
        if not self._pending_questions:
            return None

        self._pending_questions.sort(key=lambda q: q.learning_weight, reverse=True)
        question = self._pending_questions.pop(0)
        question.asked_at = time.time()
        self._asked_questions.append(question)
        return question

    def get_thought_model(self) -> ThoughtModel:
        return self.thought_model

    def get_understanding_level(self) -> dict[str, float]:
        base_understanding = {
            "decision_making": 1.0
            - self._understanding_gaps.get(CuriosityType.DECISION_REASONING.value, 1.0),
            "goals": 1.0
            - self._understanding_gaps.get(CuriosityType.GOAL_CLARIFICATION.value, 1.0),
            "process": 1.0
            - self._understanding_gaps.get(CuriosityType.PROCESS_LEARNING.value, 1.0),
            "preferences": 1.0
            - self._understanding_gaps.get(CuriosityType.PREFERENCE_DISCOVERY.value, 1.0),
            "domain": 1.0 - self._understanding_gaps.get(CuriosityType.DOMAIN_KNOWLEDGE.value, 1.0),
        }
        model_completeness = self._calculate_model_completeness()
        return {k: min(v + model_completeness * 0.2, 1.0) for k, v in base_understanding.items()}

    def get_curiosity_stats(self) -> dict[str, Any]:
        return {
            "pending_questions": len(self._pending_questions),
            "asked_questions": len(self._asked_questions),
            "answered_questions": len(self._answered_questions),
            "model_completeness": self._calculate_model_completeness(),
            "understanding_level": self.get_understanding_level(),
            "session_questions_asked": self._session_question_count,
        }

    def reset_session(self) -> None:
        self._session_question_count = 0
        self._last_question_time = 0
        self._observation_buffer = []
