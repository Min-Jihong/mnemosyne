"""Configuration schema definitions."""

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""
    OPENAI = "openai"
    VOYAGE = "voyage"
    OLLAMA = "ollama"
    GOOGLE = "google"


class CuriosityMode(str, Enum):
    """LLM curiosity modes."""
    PASSIVE = "passive"          # Observe only, no questions
    CURIOUS = "curious"          # Generate questions internally
    INTERACTIVE = "interactive"  # Ask user when curious
    PROACTIVE = "proactive"      # Actively suggest improvements


class LLMModelConfig(BaseModel):
    """Configuration for a specific LLM model."""
    provider: LLMProvider
    model: str
    api_key_env: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    
    def get_api_key(self) -> str | None:
        """Get API key from env var or direct value."""
        import os
        if self.api_key_env:
            return os.environ.get(self.api_key_env)
        return self.api_key


class LLMConfig(BaseModel):
    """LLM configuration."""
    provider: LLMProvider = LLMProvider.ANTHROPIC
    model: str = "claude-3-5-sonnet-20241022"
    api_key_env: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    
    # Specialized models
    vision: LLMModelConfig | None = None  # For screenshot analysis
    fast: LLMModelConfig | None = None    # For quick tasks
    
    def get_api_key(self) -> str | None:
        """Get API key from env var or direct value."""
        import os
        if self.api_key_env:
            return os.environ.get(self.api_key_env)
        return self.api_key


class EmbeddingConfig(BaseModel):
    """Embedding configuration."""
    provider: EmbeddingProvider = EmbeddingProvider.OLLAMA
    model: str = "nomic-embed-text"
    api_key_env: str | None = None
    api_key: str | None = None
    base_url: str | None = "http://localhost:11434"
    
    def get_api_key(self) -> str | None:
        """Get API key from env var or direct value."""
        import os
        if self.api_key_env:
            return os.environ.get(self.api_key_env)
        return self.api_key


class CaptureConfig(BaseModel):
    """Capture settings."""
    screenshot_quality: int = Field(default=80, ge=1, le=100)
    screenshot_format: Literal["webp", "png", "jpeg"] = "webp"
    excluded_apps: list[str] = Field(default_factory=lambda: [
        "1Password",
        "Keychain Access",
        "System Preferences",
    ])
    mouse_move_throttle_ms: int = 50  # Throttle mouse move events
    screenshot_on_action: bool = True  # Capture screenshot on each action


class MemoryConfig(BaseModel):
    """Memory system configuration."""
    db_path: Path = Path("~/.mnemosyne/memory.db")
    vector_db_path: Path = Path("~/.mnemosyne/chroma")
    consolidation_interval: Literal["hourly", "daily", "weekly"] = "daily"
    max_episodic_age_days: int = 90  # Auto-prune old episodic memories
    importance_threshold: float = 0.3  # Below this, memories may be pruned


class CuriosityConfig(BaseModel):
    """Curiosity system configuration."""
    mode: CuriosityMode = CuriosityMode.CURIOUS
    anomaly_threshold: float = 0.7  # How different must an action be to trigger
    question_cooldown_seconds: int = 300  # Min time between user questions
    max_pending_questions: int = 10  # Max questions to queue


def export_json_schema() -> dict:
    """Export all configuration schemas as JSON Schema for IDE support."""
    from typing import Any

    schemas: dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Mnemosyne Configuration Schema",
        "type": "object",
        "definitions": {},
    }

    models = [
        ("LLMConfig", LLMConfig),
        ("EmbeddingConfig", EmbeddingConfig),
        ("CaptureConfig", CaptureConfig),
        ("MemoryConfig", MemoryConfig),
        ("CuriosityConfig", CuriosityConfig),
    ]

    for name, model in models:
        schemas["definitions"][name] = model.model_json_schema()

    schemas["properties"] = {
        "llm": {"$ref": "#/definitions/LLMConfig"},
        "embedding": {"$ref": "#/definitions/EmbeddingConfig"},
        "capture": {"$ref": "#/definitions/CaptureConfig"},
        "memory": {"$ref": "#/definitions/MemoryConfig"},
        "curiosity": {"$ref": "#/definitions/CuriosityConfig"},
    }

    return schemas


def write_json_schema(output_path: Path | None = None) -> Path:
    """Write JSON Schema to file for IDE support."""
    import json

    if output_path is None:
        output_path = Path(__file__).parent.parent.parent / "mnemosyne-config-schema.json"

    schema = export_json_schema()

    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)

    return output_path
