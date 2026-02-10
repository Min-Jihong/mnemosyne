"""Agent types and data structures."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any


class AgentType(str, Enum):
    """Types of specialized agents."""

    OBSERVER = "observer"
    ANALYZER = "analyzer"
    EXECUTOR = "executor"
    PLANNER = "planner"
    LIBRARIAN = "librarian"
    CURIOUS = "curious"


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentContext:
    """Context provided to agents during execution."""

    session_id: str | None = None
    user_query: str = ""
    memory_results: list[dict[str, Any]] = field(default_factory=list)
    previous_results: list["AgentResult"] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from an agent execution."""

    agent_type: AgentType
    status: AgentStatus
    output: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    tokens_used: int = 0
    confidence: float = 0.0

    @property
    def duration_ms(self) -> float | None:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None

    @property
    def success(self) -> bool:
        return self.status == AgentStatus.COMPLETED


AGENT_DESCRIPTIONS: dict[AgentType, str] = {
    AgentType.OBSERVER: "Watches and records user behavior patterns",
    AgentType.ANALYZER: "Analyzes patterns and generates insights from recorded data",
    AgentType.EXECUTOR: "Takes actions based on learned behavior models",
    AgentType.PLANNER: "Plans multi-step task sequences to achieve goals",
    AgentType.LIBRARIAN: "Searches and retrieves relevant information from memory",
    AgentType.CURIOUS: "Asks probing questions to understand user intent",
}


AGENT_PROMPTS: dict[AgentType, str] = {
    AgentType.ANALYZER: """You are an Analyzer agent for Mnemosyne, a digital twin system.
Your role is to analyze user behavior patterns and generate insights.

Given the context and query, provide:
1. Key patterns observed
2. Insights about user behavior
3. Recommendations based on analysis

Be specific and reference actual data when possible.""",

    AgentType.PLANNER: """You are a Planner agent for Mnemosyne, a digital twin system.
Your role is to create step-by-step plans to achieve user goals.

Given the goal and context, provide:
1. A clear sequence of steps
2. Dependencies between steps
3. Potential risks or blockers
4. Alternative approaches if available

Output a structured plan that can be executed.""",

    AgentType.LIBRARIAN: """You are a Librarian agent for Mnemosyne, a digital twin system.
Your role is to search and retrieve relevant information from the user's memory.

Given the query and context:
1. Identify relevant memories
2. Summarize key information
3. Highlight connections between memories
4. Note any gaps in available information""",

    AgentType.EXECUTOR: """You are an Executor agent for Mnemosyne, a digital twin system.
Your role is to execute actions based on learned user behavior.

Given the goal and context:
1. Determine the most appropriate action
2. Consider safety implications
3. Execute with the user's typical patterns
4. Report on execution status""",

    AgentType.CURIOUS: """You are a Curious agent for Mnemosyne, a digital twin system.
Your role is to ask probing questions that help understand user intent.

Given the context:
1. Identify gaps in understanding
2. Generate thoughtful questions
3. Prioritize questions by importance
4. Explain why each question matters""",

    AgentType.OBSERVER: """You are an Observer agent for Mnemosyne, a digital twin system.
Your role is to observe and summarize user activity.

Given the events and context:
1. Identify significant actions
2. Note patterns in behavior
3. Flag unusual activities
4. Summarize the observation period""",
}
