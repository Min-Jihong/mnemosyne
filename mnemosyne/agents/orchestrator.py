"""Agent orchestrator for coordinating multiple agents."""

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from mnemosyne.agents.base import AGENT_CLASSES, BaseAgent
from mnemosyne.agents.types import (
    AgentContext,
    AgentResult,
    AgentStatus,
    AgentType,
)

if TYPE_CHECKING:
    from mnemosyne.llm.base import LLMProvider
    from mnemosyne.memory.persistent import PersistentMemory

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates multiple specialized agents.

    Features:
    - Single agent execution
    - Parallel agent execution
    - Sequential pipelines
    - Context sharing between agents
    - Result aggregation
    """

    def __init__(
        self,
        llm: "LLMProvider",
        memory: "PersistentMemory | None" = None,
    ) -> None:
        self.llm = llm
        self.memory = memory
        self._agents: dict[AgentType, BaseAgent] = {}
        self._execution_history: list[AgentResult] = []

    def get_agent(self, agent_type: AgentType) -> BaseAgent:
        """Get or create an agent of the specified type."""
        if agent_type not in self._agents:
            agent_class = AGENT_CLASSES.get(agent_type)
            if agent_class is None:
                raise ValueError(f"No agent class for type: {agent_type}")
            self._agents[agent_type] = agent_class(
                llm=self.llm,
                memory=self.memory,
            )
        return self._agents[agent_type]

    async def run(
        self,
        agent_type: AgentType,
        query: str,
        context: AgentContext | None = None,
    ) -> AgentResult:
        """
        Run a single agent.

        Args:
            agent_type: Type of agent to run
            query: Query or task for the agent
            context: Optional context (created if not provided)

        Returns:
            AgentResult
        """
        if context is None:
            context = AgentContext(user_query=query)

        context.previous_results = self._execution_history.copy()

        agent = self.get_agent(agent_type)

        logger.info(f"Running {agent_type.value} agent: {query[:50]}...")

        try:
            result = await agent.execute(query, context)
        except Exception as e:
            logger.error(f"Agent {agent_type.value} failed: {e}")
            result = AgentResult(
                agent_type=agent_type,
                status=AgentStatus.FAILED,
                error=str(e),
                completed_at=datetime.now(),
            )

        self._execution_history.append(result)

        return result

    async def run_parallel(
        self,
        tasks: list[tuple[AgentType, str]],
        context: AgentContext | None = None,
    ) -> list[AgentResult]:
        """
        Run multiple agents in parallel.

        Args:
            tasks: List of (AgentType, query) tuples
            context: Shared context for all agents

        Returns:
            List of AgentResults (same order as tasks)
        """
        if context is None:
            context = AgentContext()

        context.previous_results = self._execution_history.copy()

        async def run_task(agent_type: AgentType, query: str) -> AgentResult:
            agent = self.get_agent(agent_type)
            try:
                return await agent.execute(query, context)
            except Exception as e:
                return AgentResult(
                    agent_type=agent_type,
                    status=AgentStatus.FAILED,
                    error=str(e),
                    completed_at=datetime.now(),
                )

        logger.info(f"Running {len(tasks)} agents in parallel")

        results = await asyncio.gather(*[
            run_task(agent_type, query)
            for agent_type, query in tasks
        ])

        self._execution_history.extend(results)

        return list(results)

    async def run_pipeline(
        self,
        pipeline: list[tuple[AgentType, str]],
        context: AgentContext | None = None,
    ) -> list[AgentResult]:
        """
        Run agents sequentially, passing results to next agent.

        Args:
            pipeline: List of (AgentType, query) tuples to run in order
            context: Initial context

        Returns:
            List of AgentResults in execution order
        """
        if context is None:
            context = AgentContext()

        results = []

        for agent_type, query in pipeline:
            context.previous_results = results.copy()

            result = await self.run(agent_type, query, context)
            results.append(result)

            if result.status == AgentStatus.FAILED:
                logger.warning(
                    f"Pipeline stopped at {agent_type.value}: {result.error}"
                )
                break

        return results

    async def analyze_and_plan(self, goal: str) -> dict[str, Any]:
        """
        Common workflow: Analyze context then create a plan.

        Args:
            goal: The user's goal

        Returns:
            Combined analysis and plan
        """
        context = AgentContext(user_query=goal)

        if self.memory:
            memories = self.memory.recall(goal, n_results=5)
            context.memory_results = [
                {"content": m.content, "type": m.type.value}
                for m in memories
            ]

        analysis_result, library_result = await self.run_parallel(
            [
                (AgentType.ANALYZER, f"Analyze context for goal: {goal}"),
                (AgentType.LIBRARIAN, f"Find relevant memories for: {goal}"),
            ],
            context,
        )

        context.previous_results = [analysis_result, library_result]

        plan_result = await self.run(
            AgentType.PLANNER,
            f"Create a plan for: {goal}",
            context,
        )

        return {
            "goal": goal,
            "analysis": analysis_result.output if analysis_result.success else None,
            "memories": library_result.data.get("memories_searched", 0),
            "plan": plan_result.output if plan_result.success else None,
            "steps": plan_result.data.get("steps", []),
            "success": plan_result.success,
        }

    def get_history(self, limit: int = 10) -> list[AgentResult]:
        """Get recent execution history."""
        return self._execution_history[-limit:]

    def clear_history(self) -> None:
        """Clear execution history."""
        self._execution_history.clear()

    def stats(self) -> dict[str, Any]:
        """Get orchestrator statistics."""
        total = len(self._execution_history)
        successful = sum(1 for r in self._execution_history if r.success)
        total_tokens = sum(r.tokens_used for r in self._execution_history)

        by_type: dict[str, int] = {}
        for r in self._execution_history:
            by_type[r.agent_type.value] = by_type.get(r.agent_type.value, 0) + 1

        return {
            "total_executions": total,
            "successful": successful,
            "success_rate": successful / total if total > 0 else 0,
            "total_tokens": total_tokens,
            "by_agent_type": by_type,
        }
