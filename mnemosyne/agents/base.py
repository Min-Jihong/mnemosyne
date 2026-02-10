"""Base agent class."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any

from mnemosyne.agents.types import (
    AgentContext,
    AgentResult,
    AgentStatus,
    AgentType,
    AGENT_PROMPTS,
)

if TYPE_CHECKING:
    from mnemosyne.llm.base import LLMProvider
    from mnemosyne.memory.persistent import PersistentMemory


class BaseAgent(ABC):
    """Base class for all Mnemosyne agents."""

    agent_type: AgentType

    def __init__(
        self,
        llm: "LLMProvider",
        memory: "PersistentMemory | None" = None,
    ) -> None:
        self.llm = llm
        self.memory = memory

    @property
    def system_prompt(self) -> str:
        return AGENT_PROMPTS.get(self.agent_type, "")

    @abstractmethod
    async def execute(self, query: str, context: AgentContext) -> AgentResult:
        """Execute the agent's task."""
        ...

    async def _call_llm(self, prompt: str) -> tuple[str, int]:
        """Call the LLM and return response with token count."""
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
        )
        return response.text, response.usage.total_tokens if response.usage else 0

    def _create_result(
        self,
        status: AgentStatus,
        output: str = "",
        data: dict[str, Any] | None = None,
        error: str | None = None,
        tokens: int = 0,
        confidence: float = 0.0,
    ) -> AgentResult:
        return AgentResult(
            agent_type=self.agent_type,
            status=status,
            output=output,
            data=data or {},
            error=error,
            tokens_used=tokens,
            confidence=confidence,
            completed_at=datetime.now(),
        )


class AnalyzerAgent(BaseAgent):
    """Agent that analyzes behavior patterns."""

    agent_type = AgentType.ANALYZER

    async def execute(self, query: str, context: AgentContext) -> AgentResult:
        prompt = f"""Analyze the following query about user behavior:

Query: {query}

Context:
- Session: {context.session_id}
- Previous results: {len(context.previous_results)} available
- Memory results: {len(context.memory_results)} items

Provide your analysis:"""

        try:
            output, tokens = await self._call_llm(prompt)
            return self._create_result(
                status=AgentStatus.COMPLETED,
                output=output,
                tokens=tokens,
                confidence=0.8,
            )
        except Exception as e:
            return self._create_result(
                status=AgentStatus.FAILED,
                error=str(e),
            )


class PlannerAgent(BaseAgent):
    """Agent that creates execution plans."""

    agent_type = AgentType.PLANNER

    async def execute(self, query: str, context: AgentContext) -> AgentResult:
        prompt = f"""Create a plan for the following goal:

Goal: {query}

Context:
- Available memory items: {len(context.memory_results)}
- Metadata: {context.metadata}

Provide a step-by-step plan:"""

        try:
            output, tokens = await self._call_llm(prompt)

            steps = self._parse_steps(output)

            return self._create_result(
                status=AgentStatus.COMPLETED,
                output=output,
                data={"steps": steps},
                tokens=tokens,
                confidence=0.7,
            )
        except Exception as e:
            return self._create_result(
                status=AgentStatus.FAILED,
                error=str(e),
            )

    def _parse_steps(self, output: str) -> list[str]:
        """Extract numbered steps from output."""
        steps = []
        for line in output.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                steps.append(line.lstrip("0123456789.-) "))
        return steps


class LibrarianAgent(BaseAgent):
    """Agent that searches memory."""

    agent_type = AgentType.LIBRARIAN

    async def execute(self, query: str, context: AgentContext) -> AgentResult:
        memories = []
        if self.memory:
            memories = self.memory.recall(query, n_results=10)

        prompt = f"""Search for information related to:

Query: {query}

Available memories:
{self._format_memories(memories)}

Summarize relevant findings:"""

        try:
            output, tokens = await self._call_llm(prompt)
            return self._create_result(
                status=AgentStatus.COMPLETED,
                output=output,
                data={"memories_searched": len(memories)},
                tokens=tokens,
                confidence=0.9,
            )
        except Exception as e:
            return self._create_result(
                status=AgentStatus.FAILED,
                error=str(e),
            )

    def _format_memories(self, memories: list) -> str:
        if not memories:
            return "(No memories found)"
        lines = []
        for m in memories[:5]:
            lines.append(f"- {m.content[:100]}...")
        return "\n".join(lines)


class CuriousAgent(BaseAgent):
    """Agent that asks probing questions."""

    agent_type = AgentType.CURIOUS

    async def execute(self, query: str, context: AgentContext) -> AgentResult:
        prompt = f"""Given this context, generate thoughtful questions:

Context: {query}

Previous observations: {len(context.memory_results)} items

Generate 3-5 questions that would help understand the user better:"""

        try:
            output, tokens = await self._call_llm(prompt)

            questions = self._parse_questions(output)

            return self._create_result(
                status=AgentStatus.COMPLETED,
                output=output,
                data={"questions": questions},
                tokens=tokens,
                confidence=0.75,
            )
        except Exception as e:
            return self._create_result(
                status=AgentStatus.FAILED,
                error=str(e),
            )

    def _parse_questions(self, output: str) -> list[str]:
        questions = []
        for line in output.split("\n"):
            line = line.strip()
            if line and "?" in line:
                questions.append(line.lstrip("0123456789.-) "))
        return questions


AGENT_CLASSES: dict[AgentType, type[BaseAgent]] = {
    AgentType.ANALYZER: AnalyzerAgent,
    AgentType.PLANNER: PlannerAgent,
    AgentType.LIBRARIAN: LibrarianAgent,
    AgentType.CURIOUS: CuriousAgent,
}
