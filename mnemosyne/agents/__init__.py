"""
Mnemosyne Agent Orchestration System

A multi-agent system for coordinating specialized AI agents.

Agent Types:
- Observer: Watches and records user behavior
- Analyzer: Analyzes patterns and generates insights
- Executor: Takes actions based on learned behavior
- Planner: Plans multi-step task sequences
- Librarian: Searches and retrieves from memory

Usage:
    from mnemosyne.agents import AgentOrchestrator, AgentType

    orchestrator = AgentOrchestrator(llm=llm, memory=memory)

    # Run a single agent
    result = await orchestrator.run(AgentType.ANALYZER, "Why do I always...")

    # Run multiple agents in parallel
    results = await orchestrator.run_parallel([
        (AgentType.ANALYZER, "Analyze my morning routine"),
        (AgentType.LIBRARIAN, "Find similar patterns"),
    ])
"""

from mnemosyne.agents.types import AgentType, AgentResult, AgentContext
from mnemosyne.agents.base import BaseAgent
from mnemosyne.agents.orchestrator import AgentOrchestrator

__all__ = [
    "AgentType",
    "AgentResult",
    "AgentContext",
    "BaseAgent",
    "AgentOrchestrator",
]
