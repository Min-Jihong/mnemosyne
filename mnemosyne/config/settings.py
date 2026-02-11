"""Settings management and loading."""

import os
from pathlib import Path
from typing import Any

import toml
from pydantic import BaseModel

from mnemosyne.config.schema import (
    LLMConfig,
    EmbeddingConfig,
    CaptureConfig,
    MemoryConfig,
    CuriosityConfig,
    PrivacyConfig,
)


class Settings(BaseModel):
    """Main settings container."""
    llm: LLMConfig = LLMConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    capture: CaptureConfig = CaptureConfig()
    memory: MemoryConfig = MemoryConfig()
    curiosity: CuriosityConfig = CuriosityConfig()
    privacy: PrivacyConfig = PrivacyConfig()
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Settings":
        """Create Settings from dictionary."""
        return cls(
            llm=LLMConfig(**data.get("llm", {})),
            embedding=EmbeddingConfig(**data.get("embedding", {})),
            capture=CaptureConfig(**data.get("capture", {})),
            memory=MemoryConfig(**data.get("memory", {})),
            curiosity=CuriosityConfig(**data.get("curiosity", {})),
            privacy=PrivacyConfig(**data.get("privacy", {})),
        )


def get_config_path() -> Path:
    """Get the config file path."""
    # Check environment variable first
    if env_path := os.environ.get("MNEMOSYNE_CONFIG"):
        return Path(env_path)
    
    # Default to ~/.mnemosyne/config.toml
    return Path.home() / ".mnemosyne" / "config.toml"


def load_settings(config_path: Path | None = None) -> Settings:
    """Load settings from config file."""
    path = config_path or get_config_path()
    
    if not path.exists():
        # Return default settings if no config file
        return Settings()
    
    with open(path) as f:
        data = toml.load(f)
    
    return Settings.from_dict(data)


def save_settings(settings: Settings, config_path: Path | None = None) -> None:
    """Save settings to config file."""
    path = config_path or get_config_path()
    
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict, handling Path objects
    data = settings.model_dump(mode="json")
    
    with open(path, "w") as f:
        toml.dump(data, f)


def ensure_config_dir() -> Path:
    """Ensure the config directory exists and return its path."""
    config_dir = Path.home() / ".mnemosyne"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir
