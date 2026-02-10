import json
import random
from typing import Any
from dataclasses import dataclass, field

from mnemosyne.llm.base import BaseLLMProvider
from mnemosyne.store.models import StoredEvent
from mnemosyne.store.database import Database


@dataclass
class Curiosity:
    question: str
    context: str
    importance: float
    category: str
    answered: bool = False
    answer: str | None = None


@dataclass 
class Pattern:
    description: str
    frequency: int
    events: list[str]
    insight: str | None = None


class CuriousLLM:
    
    CURIOSITY_CATEGORIES = [
        "workflow",
        "habit",
        "decision",
        "emotion",
        "efficiency",
        "learning",
        "preference",
    ]
    
    CURIOSITY_PROMPTS = [
        "Why did the user switch from {app1} to {app2} at this moment?",
        "What pattern exists in how the user types? Fast/slow, corrections?",
        "Why does the user frequently use {hotkey}? What's the underlying need?",
        "The user paused for {seconds}s before clicking. What were they thinking?",
        "Why did the user scroll up to re-read something?",
        "What made the user decide to close {app} right now?",
        "Is there a pattern in when the user takes breaks?",
        "Why does the user prefer {action} over alternatives?",
    ]
    
    def __init__(
        self,
        llm: BaseLLMProvider,
        database: Database,
        curiosity_threshold: float = 0.7,
    ):
        self.llm = llm
        self.database = database
        self.curiosity_threshold = curiosity_threshold
        self._curiosities: list[Curiosity] = []
        self._patterns: list[Pattern] = []
    
    async def observe_and_wonder(
        self,
        events: list[StoredEvent],
    ) -> list[Curiosity]:
        if len(events) < 5:
            return []
        
        observations = self._extract_observations(events)
        
        prompt = self._build_curiosity_prompt(observations)
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a curious AI studying human-computer interaction. "
                    "Your goal is to deeply understand WHY humans behave the way they do. "
                    "Generate insightful questions about the observed behavior. "
                    "Be genuinely curious - ask questions that reveal thought patterns, "
                    "habits, and decision-making processes."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        
        response = await self.llm.generate(messages)
        curiosities = self._parse_curiosities(response, events)
        
        self._curiosities.extend(curiosities)
        
        return curiosities
    
    def _extract_observations(self, events: list[StoredEvent]) -> dict[str, Any]:
        app_switches = []
        typing_sessions = []
        hotkeys_used = []
        pauses = []
        
        prev_app = None
        for i, event in enumerate(events):
            if event.window_app != prev_app and prev_app is not None:
                app_switches.append({
                    "from": prev_app,
                    "to": event.window_app,
                    "timestamp": event.timestamp,
                })
            prev_app = event.window_app
            
            if event.action_type == "hotkey":
                hotkeys_used.append(event.data.get("keys", []))
            
            if event.action_type == "key_type":
                typing_sessions.append({
                    "text_length": len(event.data.get("text", "")),
                    "duration_ms": event.data.get("duration_ms", 0),
                })
            
            if i > 0:
                time_gap = event.timestamp - events[i - 1].timestamp
                if time_gap > 2.0:
                    pauses.append({
                        "duration": time_gap,
                        "before_action": event.action_type,
                    })
        
        return {
            "app_switches": app_switches,
            "typing_sessions": typing_sessions,
            "hotkeys_used": hotkeys_used,
            "pauses": pauses,
            "total_events": len(events),
            "time_span": events[-1].timestamp - events[0].timestamp if events else 0,
        }
    
    def _build_curiosity_prompt(self, observations: dict[str, Any]) -> str:
        lines = [
            "I observed the following user behavior:",
            "",
            f"Total events: {observations['total_events']}",
            f"Time span: {observations['time_span']:.1f} seconds",
            "",
        ]
        
        if observations["app_switches"]:
            lines.append("App switches:")
            for switch in observations["app_switches"][:5]:
                lines.append(f"  - {switch['from']} → {switch['to']}")
            lines.append("")
        
        if observations["hotkeys_used"]:
            lines.append("Hotkeys used:")
            for hotkey in observations["hotkeys_used"][:5]:
                lines.append(f"  - {'+'.join(hotkey)}")
            lines.append("")
        
        if observations["pauses"]:
            lines.append("Notable pauses:")
            for pause in observations["pauses"][:3]:
                lines.append(
                    f"  - {pause['duration']:.1f}s pause before {pause['before_action']}"
                )
            lines.append("")
        
        lines.extend([
            "Generate 3-5 curious questions about this behavior.",
            "Format as JSON array with objects containing:",
            "- question: The curious question",
            "- category: One of (workflow, habit, decision, emotion, efficiency, learning, preference)",
            "- importance: 0.0-1.0 score of how insightful this question is",
        ])
        
        return "\n".join(lines)
    
    def _parse_curiosities(
        self,
        response: str,
        events: list[StoredEvent],
    ) -> list[Curiosity]:
        try:
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])
            
            data = json.loads(response)
            
            if isinstance(data, dict) and "questions" in data:
                data = data["questions"]
            
            curiosities = []
            for item in data:
                curiosities.append(Curiosity(
                    question=item.get("question", ""),
                    context=f"Based on {len(events)} events",
                    importance=float(item.get("importance", 0.5)),
                    category=item.get("category", "workflow"),
                ))
            
            return curiosities
            
        except Exception:
            return [Curiosity(
                question=random.choice(self.CURIOSITY_PROMPTS),
                context="Generated from template",
                importance=0.5,
                category="workflow",
            )]
    
    async def answer_curiosity(self, curiosity: Curiosity) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI trying to understand human behavior. "
                    "Based on your observations, provide a thoughtful hypothesis "
                    "to answer the following question about user behavior."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {curiosity.question}\nContext: {curiosity.context}",
            },
        ]
        
        answer = await self.llm.generate(messages)
        curiosity.answer = answer
        curiosity.answered = True
        
        return answer
    
    async def find_patterns(
        self,
        session_id: str,
        min_frequency: int = 3,
    ) -> list[Pattern]:
        events = self.database.get_events(session_id=session_id, limit=1000)
        
        if len(events) < min_frequency:
            return []
        
        action_sequences = {}
        for i in range(len(events) - 2):
            seq = tuple(e.action_type for e in events[i:i + 3])
            if seq not in action_sequences:
                action_sequences[seq] = []
            action_sequences[seq].append(i)
        
        patterns = []
        for seq, indices in action_sequences.items():
            if len(indices) >= min_frequency:
                patterns.append(Pattern(
                    description=" → ".join(seq),
                    frequency=len(indices),
                    events=[events[i].id for i in indices[:5]],
                ))
        
        for pattern in patterns[:5]:
            insight = await self._generate_pattern_insight(pattern)
            pattern.insight = insight
        
        self._patterns.extend(patterns)
        
        return patterns
    
    async def _generate_pattern_insight(self, pattern: Pattern) -> str:
        messages = [
            {
                "role": "system",
                "content": "You are an AI analyzing human behavior patterns.",
            },
            {
                "role": "user",
                "content": (
                    f"I found this repeated pattern in user behavior:\n"
                    f"Pattern: {pattern.description}\n"
                    f"Frequency: {pattern.frequency} times\n\n"
                    "What does this pattern reveal about the user's habits or workflow?"
                ),
            },
        ]
        
        return await self.llm.generate(messages)
    
    def get_unanswered_curiosities(self) -> list[Curiosity]:
        return [c for c in self._curiosities if not c.answered]
    
    def get_top_curiosities(self, n: int = 5) -> list[Curiosity]:
        sorted_curiosities = sorted(
            self._curiosities,
            key=lambda c: c.importance,
            reverse=True,
        )
        return sorted_curiosities[:n]
