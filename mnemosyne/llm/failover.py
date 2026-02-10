"""Failover LLM provider that automatically retries with fallback providers."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import AsyncIterator

from mnemosyne.llm.base import LLMProvider, Message, Response

logger = logging.getLogger(__name__)


@dataclass
class ProviderStatus:
    """Status tracking for a provider."""
    provider: LLMProvider
    failures: int = 0
    last_failure: datetime | None = None
    cooldown_until: datetime | None = None
    
    def is_available(self) -> bool:
        """Check if provider is available (not in cooldown)."""
        if self.cooldown_until is None:
            return True
        return datetime.now() > self.cooldown_until
    
    def record_failure(self, cooldown_seconds: int = 60) -> None:
        """Record a failure and potentially enter cooldown."""
        self.failures += 1
        self.last_failure = datetime.now()
        
        if self.failures >= 3:
            self.cooldown_until = datetime.now() + timedelta(seconds=cooldown_seconds)
            logger.warning(
                f"Provider {self.provider.name} entering cooldown for {cooldown_seconds}s "
                f"after {self.failures} failures"
            )
    
    def record_success(self) -> None:
        """Record a successful call, resetting failure count."""
        self.failures = 0
        self.cooldown_until = None


@dataclass
class FailoverConfig:
    """Configuration for failover behavior."""
    max_retries: int = 3
    retry_delay: float = 1.0
    cooldown_seconds: int = 60
    exponential_backoff: bool = True


class FailoverLLMProvider(LLMProvider):
    """LLM provider with automatic failover to fallback providers."""
    
    def __init__(
        self,
        primary: LLMProvider,
        fallbacks: list[LLMProvider] | None = None,
        config: FailoverConfig | None = None,
    ):
        self._primary = ProviderStatus(provider=primary)
        self._fallbacks = [ProviderStatus(provider=p) for p in (fallbacks or [])]
        self._config = config or FailoverConfig()
    
    @property
    def name(self) -> str:
        return f"failover({self._primary.provider.name})"
    
    def _get_available_providers(self) -> list[ProviderStatus]:
        """Get list of available providers in priority order."""
        all_providers = [self._primary] + self._fallbacks
        available = [p for p in all_providers if p.is_available()]
        
        if not available:
            logger.warning("All providers in cooldown, using primary anyway")
            return [self._primary]
        
        return available
    
    async def _try_with_failover(
        self,
        operation: str,
        call_fn,
        **kwargs,
    ):
        """Execute an operation with failover support."""
        providers = self._get_available_providers()
        last_error: Exception | None = None
        
        for provider_status in providers:
            provider = provider_status.provider
            
            for attempt in range(self._config.max_retries):
                try:
                    result = await call_fn(provider, **kwargs)
                    provider_status.record_success()
                    return result
                    
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"{operation} failed on {provider.name} "
                        f"(attempt {attempt + 1}/{self._config.max_retries}): {e}"
                    )
                    
                    if attempt < self._config.max_retries - 1:
                        delay = self._config.retry_delay
                        if self._config.exponential_backoff:
                            delay *= 2 ** attempt
                        await asyncio.sleep(delay)
            
            provider_status.record_failure(self._config.cooldown_seconds)
        
        raise last_error or RuntimeError(f"{operation} failed on all providers")
    
    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Response:
        """Generate a completion with failover."""
        async def call(provider: LLMProvider, **kw) -> Response:
            return await provider.complete(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        
        return await self._try_with_failover("complete", call)
    
    async def complete_with_vision(
        self,
        messages: list[Message],
        images: list[bytes],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Response:
        """Generate completion with vision and failover."""
        async def call(provider: LLMProvider, **kw) -> Response:
            return await provider.complete_with_vision(
                messages=messages,
                images=images,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        
        return await self._try_with_failover("complete_with_vision", call)
    
    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream completion tokens with failover (uses first available provider)."""
        providers = self._get_available_providers()
        last_error: Exception | None = None
        
        for provider_status in providers:
            provider = provider_status.provider
            
            try:
                async for token in provider.stream(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                ):
                    yield token
                provider_status.record_success()
                return
                
            except Exception as e:
                last_error = e
                logger.warning(f"stream failed on {provider.name}: {e}")
                provider_status.record_failure(self._config.cooldown_seconds)
        
        raise last_error or RuntimeError("stream failed on all providers")
    
    def get_provider_stats(self) -> dict:
        """Get statistics about provider usage and failures."""
        all_providers = [self._primary] + self._fallbacks
        return {
            p.provider.name: {
                "failures": p.failures,
                "available": p.is_available(),
                "cooldown_until": p.cooldown_until.isoformat() if p.cooldown_until else None,
            }
            for p in all_providers
        }
