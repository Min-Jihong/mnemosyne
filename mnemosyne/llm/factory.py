"""Factory functions for creating LLM and Embedding providers."""

from mnemosyne.config.schema import LLMConfig, EmbeddingConfig, LLMProvider as LLMProviderEnum, EmbeddingProvider as EmbeddingProviderEnum
from mnemosyne.llm.base import LLMProvider, EmbeddingProvider


def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """Create an LLM provider based on configuration."""
    from mnemosyne.llm.providers.anthropic import AnthropicProvider
    from mnemosyne.llm.providers.openai import OpenAIProvider
    from mnemosyne.llm.providers.google import GoogleProvider
    from mnemosyne.llm.providers.ollama import OllamaProvider
    
    api_key = config.get_api_key()
    
    match config.provider:
        case LLMProviderEnum.ANTHROPIC:
            if not api_key:
                raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY or configure api_key.")
            return AnthropicProvider(api_key=api_key, default_model=config.model)
        
        case LLMProviderEnum.OPENAI:
            if not api_key:
                raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY or configure api_key.")
            return OpenAIProvider(
                api_key=api_key,
                base_url=config.base_url,
                default_model=config.model,
            )
        
        case LLMProviderEnum.GOOGLE:
            if not api_key:
                raise ValueError("Google API key is required. Set GOOGLE_API_KEY or configure api_key.")
            return GoogleProvider(api_key=api_key, default_model=config.model)
        
        case LLMProviderEnum.OLLAMA:
            return OllamaProvider(
                base_url=config.base_url or "http://localhost:11434",
                default_model=config.model,
            )
        
        case LLMProviderEnum.CUSTOM:
            if not api_key:
                raise ValueError("API key is required for custom provider.")
            if not config.base_url:
                raise ValueError("Base URL is required for custom provider.")
            return OpenAIProvider(
                api_key=api_key,
                base_url=config.base_url,
                default_model=config.model,
            )
        
        case _:
            raise ValueError(f"Unknown LLM provider: {config.provider}")


def create_llm_provider_with_failover(
    primary_config: LLMConfig,
    fallback_configs: list[LLMConfig] | None = None,
) -> LLMProvider:
    """Create an LLM provider with automatic failover to fallback providers."""
    from mnemosyne.llm.failover import FailoverLLMProvider, FailoverConfig
    
    primary = create_llm_provider(primary_config)
    
    if not fallback_configs:
        return primary
    
    fallbacks = []
    for config in fallback_configs:
        try:
            fallbacks.append(create_llm_provider(config))
        except ValueError:
            pass
    
    if not fallbacks:
        return primary
    
    return FailoverLLMProvider(
        primary=primary,
        fallbacks=fallbacks,
        config=FailoverConfig(max_retries=3, cooldown_seconds=60),
    )


def create_embedding_provider(config: EmbeddingConfig) -> EmbeddingProvider:
    """Create an embedding provider based on configuration."""
    from mnemosyne.llm.providers.openai import OpenAIEmbeddingProvider
    from mnemosyne.llm.providers.google import GoogleEmbeddingProvider
    from mnemosyne.llm.providers.ollama import OllamaEmbeddingProvider
    
    api_key = config.get_api_key()
    
    match config.provider:
        case EmbeddingProviderEnum.OPENAI:
            if not api_key:
                raise ValueError("OpenAI API key is required for embeddings.")
            return OpenAIEmbeddingProvider(
                api_key=api_key,
                model=config.model,
                base_url=config.base_url,
            )
        
        case EmbeddingProviderEnum.GOOGLE:
            if not api_key:
                raise ValueError("Google API key is required for embeddings.")
            return GoogleEmbeddingProvider(api_key=api_key, model=config.model)
        
        case EmbeddingProviderEnum.OLLAMA:
            return OllamaEmbeddingProvider(
                base_url=config.base_url or "http://localhost:11434",
                model=config.model,
            )
        
        case EmbeddingProviderEnum.VOYAGE:
            # Voyage uses OpenAI-compatible API
            if not api_key:
                raise ValueError("Voyage API key is required.")
            return OpenAIEmbeddingProvider(
                api_key=api_key,
                model=config.model,
                base_url="https://api.voyageai.com/v1",
            )
        
        case _:
            raise ValueError(f"Unknown embedding provider: {config.provider}")
