"""Base classes for LLM and Embedding providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Literal


@dataclass
class Message:
    """A message in a conversation."""
    role: Literal["user", "assistant", "system"]
    content: str
    images: list[bytes] = field(default_factory=list)


@dataclass
class Response:
    """Response from an LLM."""
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str | None = None


class LLMProvider(ABC):
    """Base class for all LLM providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Response:
        """Generate a completion."""
        pass
    
    @abstractmethod
    async def complete_with_vision(
        self,
        messages: list[Message],
        images: list[bytes],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Response:
        """Generate completion with image understanding."""
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        pass
    
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        try:
            await self.complete(
                messages=[Message(role="user", content="Hi")],
                max_tokens=10,
            )
            return True
        except Exception:
            return False


BaseLLMProvider = LLMProvider


class EmbeddingProvider(ABC):
    """Base class for embedding providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        pass
    
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass
    
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        try:
            result = await self.embed(["test"])
            return len(result) == 1 and len(result[0]) == self.dimension()
        except Exception:
            return False
