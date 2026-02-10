"""Base classes for the plugin system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from mnemosyne.plugins.manager import PluginManager


class PluginState(str, Enum):
    """Plugin lifecycle states."""

    DISCOVERED = "discovered"  # Found but not loaded
    LOADING = "loading"  # Currently loading
    LOADED = "loaded"  # Successfully loaded
    ACTIVE = "active"  # Running and handling events
    DISABLED = "disabled"  # Manually disabled
    ERROR = "error"  # Failed to load or crashed


class PluginCapability(str, Enum):
    """Capabilities a plugin can provide."""

    CLI_COMMANDS = "cli_commands"  # Add CLI commands
    WEB_ROUTES = "web_routes"  # Add web routes
    LLM_PROVIDER = "llm_provider"  # Add LLM provider
    CAPTURE_SOURCE = "capture_source"  # Add capture source
    MEMORY_BACKEND = "memory_backend"  # Add memory backend
    HOOKS = "hooks"  # Register event hooks
    MIDDLEWARE = "middleware"  # Add processing middleware


class PluginManifest(BaseModel):
    """Plugin manifest (plugin.json) schema."""

    # Required fields
    name: str = Field(..., description="Unique plugin identifier")
    version: str = Field(..., description="Semantic version (e.g., 1.0.0)")

    # Optional metadata
    description: str = Field(default="", description="Plugin description")
    author: str = Field(default="", description="Plugin author")
    license: str = Field(default="", description="Plugin license")
    homepage: str = Field(default="", description="Plugin homepage URL")
    repository: str = Field(default="", description="Source repository URL")

    # Entry point
    entry_point: str = Field(
        default="__init__.py", description="Main module file"
    )
    plugin_class: str = Field(
        default="Plugin", description="Plugin class name in entry point"
    )

    # Capabilities and requirements
    capabilities: list[PluginCapability] = Field(
        default_factory=list, description="Plugin capabilities"
    )
    hooks: list[str] = Field(
        default_factory=list, description="Hooks this plugin listens to"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="Required plugins"
    )
    python_requires: str = Field(
        default=">=3.11", description="Python version requirement"
    )
    pip_dependencies: list[str] = Field(
        default_factory=list, description="PyPI packages to install"
    )

    # Configuration
    config_schema: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for plugin config"
    )
    default_config: dict[str, Any] = Field(
        default_factory=dict, description="Default configuration values"
    )

    # Compatibility
    mnemosyne_version: str = Field(
        default=">=0.1.0", description="Compatible Mnemosyne versions"
    )


@dataclass
class PluginMetadata:
    """Runtime metadata for a loaded plugin."""

    manifest: PluginManifest
    path: Path
    state: PluginState = PluginState.DISCOVERED
    loaded_at: datetime | None = None
    error_message: str | None = None
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginContext:
    """Context passed to plugins during lifecycle events."""

    manager: "PluginManager"
    plugin_name: str
    plugin_path: Path
    config: dict[str, Any]
    data_dir: Path  # Plugin-specific data directory

    def get_plugin(self, name: str) -> "MnemosynePlugin | None":
        """Get another loaded plugin by name."""
        return self.manager.get_plugin(name)

    def log(self, message: str, level: str = "info") -> None:
        """Log a message with the plugin's name prefixed."""
        import logging

        logger = logging.getLogger(f"mnemosyne.plugins.{self.plugin_name}")
        getattr(logger, level)(message)


class MnemosynePlugin(ABC):
    """
    Base class for all Mnemosyne plugins.

    Plugins must implement on_load() and can optionally implement
    other lifecycle methods and event handlers.

    Example:
        class MyPlugin(MnemosynePlugin):
            async def on_load(self, context: PluginContext) -> None:
                self.context = context
                context.log("Plugin loaded!")

            async def on_event(self, event_type: str, payload: dict) -> dict | None:
                if event_type == "post_capture":
                    # Process captured events
                    return {"processed": True}
                return None
    """

    @abstractmethod
    async def on_load(self, context: PluginContext) -> None:
        """
        Called when the plugin is loaded.

        Initialize resources, register handlers, etc.

        Args:
            context: Plugin context with access to manager and config
        """
        ...

    async def on_unload(self) -> None:
        """
        Called when the plugin is being unloaded.

        Clean up resources, close connections, etc.
        """
        pass

    async def on_enable(self) -> None:
        """Called when the plugin is enabled after being disabled."""
        pass

    async def on_disable(self) -> None:
        """Called when the plugin is being disabled."""
        pass

    async def on_event(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        """
        Handle an event from the hook system.

        Args:
            event_type: Type of event (e.g., "post_capture", "pre_inference")
            payload: Event data

        Returns:
            Modified payload or None to pass through unchanged
        """
        return None

    def get_cli_commands(self) -> list[Any]:
        """
        Return CLI commands to register.

        Returns:
            List of Typer command functions
        """
        return []

    def get_web_routes(self) -> list[Any]:
        """
        Return web routes to register.

        Returns:
            List of FastAPI route definitions
        """
        return []

    def get_config_schema(self) -> dict[str, Any]:
        """
        Return JSON Schema for plugin configuration.

        Returns:
            JSON Schema dict
        """
        return {}
