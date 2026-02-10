"""Plugin manager for discovering, loading, and managing plugins."""

import asyncio
import importlib.util
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from mnemosyne.plugins.base import (
    MnemosynePlugin,
    PluginContext,
    PluginManifest,
    PluginMetadata,
    PluginState,
)
from mnemosyne.plugins.exceptions import (
    PluginDependencyError,
    PluginLoadError,
    PluginNotFoundError,
    PluginValidationError,
)

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages the lifecycle of Mnemosyne plugins.

    Responsibilities:
    - Discover plugins from configured directories
    - Validate plugin manifests
    - Load and initialize plugins
    - Manage plugin dependencies
    - Route events to registered plugins
    - Handle plugin enable/disable
    """

    def __init__(
        self,
        plugin_dirs: list[Path] | None = None,
        data_dir: Path | None = None,
    ) -> None:
        """
        Initialize the plugin manager.

        Args:
            plugin_dirs: Directories to search for plugins
            data_dir: Base directory for plugin data storage
        """
        self._plugin_dirs = plugin_dirs or self._default_plugin_dirs()
        self._data_dir = data_dir or Path.home() / ".mnemosyne" / "plugin_data"
        self._data_dir.mkdir(parents=True, exist_ok=True)

        # Plugin storage
        self._metadata: dict[str, PluginMetadata] = {}
        self._plugins: dict[str, MnemosynePlugin] = {}
        self._hook_subscriptions: dict[str, list[str]] = {}  # hook -> [plugin_names]

        # State
        self._initialized = False

    @staticmethod
    def _default_plugin_dirs() -> list[Path]:
        """Get default plugin directories."""
        dirs = [
            Path.home() / ".mnemosyne" / "plugins",  # User plugins
            Path(__file__).parent / "builtin",  # Built-in plugins
        ]
        return [d for d in dirs if d.exists()]

    @property
    def plugins(self) -> dict[str, MnemosynePlugin]:
        """Get all loaded plugins."""
        return self._plugins.copy()

    @property
    def metadata(self) -> dict[str, PluginMetadata]:
        """Get metadata for all discovered plugins."""
        return self._metadata.copy()

    def get_plugin(self, name: str) -> MnemosynePlugin | None:
        """Get a loaded plugin by name."""
        return self._plugins.get(name)

    def get_metadata(self, name: str) -> PluginMetadata | None:
        """Get metadata for a plugin by name."""
        return self._metadata.get(name)

    async def discover_plugins(self) -> list[str]:
        """
        Discover available plugins from plugin directories.

        Returns:
            List of discovered plugin names
        """
        discovered = []

        for plugin_dir in self._plugin_dirs:
            if not plugin_dir.exists():
                continue

            for item in plugin_dir.iterdir():
                if not item.is_dir():
                    continue

                manifest_path = item / "plugin.json"
                if not manifest_path.exists():
                    continue

                try:
                    manifest = self._load_manifest(manifest_path)
                    self._metadata[manifest.name] = PluginMetadata(
                        manifest=manifest,
                        path=item,
                        state=PluginState.DISCOVERED,
                    )
                    discovered.append(manifest.name)
                    logger.debug(f"Discovered plugin: {manifest.name}")
                except Exception as e:
                    logger.warning(f"Failed to read manifest at {manifest_path}: {e}")

        return discovered

    def _load_manifest(self, path: Path) -> PluginManifest:
        """Load and validate a plugin manifest."""
        with open(path) as f:
            data = json.load(f)
        return PluginManifest(**data)

    def _validate_plugin(self, name: str) -> list[str]:
        """
        Validate a plugin before loading.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        meta = self._metadata.get(name)

        if not meta:
            errors.append("Plugin metadata not found")
            return errors

        manifest = meta.manifest

        # Check entry point exists
        entry_path = meta.path / manifest.entry_point
        if not entry_path.exists():
            errors.append(f"Entry point not found: {manifest.entry_point}")

        # Check dependencies are available
        for dep in manifest.dependencies:
            if dep not in self._metadata:
                errors.append(f"Missing dependency: {dep}")

        return errors

    async def load_plugin(self, name: str) -> MnemosynePlugin:
        """
        Load a single plugin by name.

        Args:
            name: Plugin name to load

        Returns:
            Loaded plugin instance

        Raises:
            PluginNotFoundError: If plugin is not discovered
            PluginValidationError: If validation fails
            PluginLoadError: If loading fails
        """
        meta = self._metadata.get(name)
        if not meta:
            raise PluginNotFoundError(name)

        # Check if already loaded
        if name in self._plugins:
            return self._plugins[name]

        # Validate
        errors = self._validate_plugin(name)
        if errors:
            meta.state = PluginState.ERROR
            meta.error_message = "; ".join(errors)
            raise PluginValidationError(name, errors)

        # Load dependencies first
        for dep in meta.manifest.dependencies:
            if dep not in self._plugins:
                await self.load_plugin(dep)

        # Update state
        meta.state = PluginState.LOADING

        try:
            # Import the plugin module
            entry_path = meta.path / meta.manifest.entry_point
            spec = importlib.util.spec_from_file_location(
                f"mnemosyne.plugins.{name}",
                entry_path,
            )
            if not spec or not spec.loader:
                raise PluginLoadError(name, "Could not create module spec")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get the plugin class
            plugin_class = getattr(module, meta.manifest.plugin_class, None)
            if not plugin_class:
                raise PluginLoadError(
                    name,
                    f"Plugin class '{meta.manifest.plugin_class}' not found",
                )

            if not issubclass(plugin_class, MnemosynePlugin):
                raise PluginLoadError(
                    name,
                    f"'{meta.manifest.plugin_class}' is not a MnemosynePlugin subclass",
                )

            # Instantiate the plugin
            plugin = plugin_class()

            # Create context
            plugin_data_dir = self._data_dir / name
            plugin_data_dir.mkdir(parents=True, exist_ok=True)

            context = PluginContext(
                manager=self,
                plugin_name=name,
                plugin_path=meta.path,
                config=meta.config or meta.manifest.default_config,
                data_dir=plugin_data_dir,
            )

            # Initialize
            await plugin.on_load(context)

            # Register hooks
            for hook in meta.manifest.hooks:
                if hook not in self._hook_subscriptions:
                    self._hook_subscriptions[hook] = []
                self._hook_subscriptions[hook].append(name)

            # Store plugin
            self._plugins[name] = plugin
            meta.state = PluginState.ACTIVE
            meta.loaded_at = datetime.now()

            logger.info(f"Loaded plugin: {name} v{meta.manifest.version}")
            return plugin

        except Exception as e:
            meta.state = PluginState.ERROR
            meta.error_message = str(e)
            raise PluginLoadError(name, str(e)) from e

    async def load_all_plugins(self) -> dict[str, MnemosynePlugin | Exception]:
        """
        Load all discovered plugins.

        Returns:
            Dict mapping plugin names to loaded plugins or exceptions
        """
        results: dict[str, MnemosynePlugin | Exception] = {}

        # Sort by dependencies
        load_order = self._topological_sort()

        for name in load_order:
            try:
                results[name] = await self.load_plugin(name)
            except Exception as e:
                results[name] = e
                logger.error(f"Failed to load plugin {name}: {e}")

        self._initialized = True
        return results

    def _topological_sort(self) -> list[str]:
        """Sort plugins by dependencies (dependencies first)."""
        visited: set[str] = set()
        result: list[str] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)

            meta = self._metadata.get(name)
            if meta:
                for dep in meta.manifest.dependencies:
                    visit(dep)

            result.append(name)

        for name in self._metadata:
            visit(name)

        return result

    async def unload_plugin(self, name: str) -> None:
        """
        Unload a plugin.

        Args:
            name: Plugin name to unload
        """
        plugin = self._plugins.get(name)
        if not plugin:
            return

        meta = self._metadata.get(name)

        try:
            await plugin.on_unload()
        except Exception as e:
            logger.error(f"Error during plugin unload {name}: {e}")

        # Remove from hooks
        for hook, plugins in self._hook_subscriptions.items():
            if name in plugins:
                plugins.remove(name)

        del self._plugins[name]

        if meta:
            meta.state = PluginState.DISCOVERED
            meta.loaded_at = None

        logger.info(f"Unloaded plugin: {name}")

    async def unload_all_plugins(self) -> None:
        """Unload all plugins in reverse dependency order."""
        load_order = self._topological_sort()
        for name in reversed(load_order):
            await self.unload_plugin(name)

    async def enable_plugin(self, name: str) -> None:
        """Enable a disabled plugin."""
        meta = self._metadata.get(name)
        if not meta:
            raise PluginNotFoundError(name)

        if meta.state != PluginState.DISABLED:
            return

        plugin = self._plugins.get(name)
        if plugin:
            await plugin.on_enable()
            meta.state = PluginState.ACTIVE

    async def disable_plugin(self, name: str) -> None:
        """Disable an active plugin without unloading."""
        meta = self._metadata.get(name)
        if not meta:
            raise PluginNotFoundError(name)

        if meta.state != PluginState.ACTIVE:
            return

        plugin = self._plugins.get(name)
        if plugin:
            await plugin.on_disable()
            meta.state = PluginState.DISABLED

    async def dispatch_event(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Dispatch an event to all subscribed plugins.

        Args:
            event_type: Type of event
            payload: Event data

        Returns:
            Potentially modified payload
        """
        subscribers = self._hook_subscriptions.get(event_type, [])

        for plugin_name in subscribers:
            plugin = self._plugins.get(plugin_name)
            meta = self._metadata.get(plugin_name)

            if not plugin or not meta or meta.state != PluginState.ACTIVE:
                continue

            try:
                result = await plugin.on_event(event_type, payload)
                if result is not None:
                    payload = result
            except Exception as e:
                logger.error(f"Plugin {plugin_name} error handling {event_type}: {e}")

        return payload

    def get_cli_commands(self) -> list[tuple[str, Any]]:
        """Get CLI commands from all active plugins."""
        commands = []
        for name, plugin in self._plugins.items():
            meta = self._metadata.get(name)
            if meta and meta.state == PluginState.ACTIVE:
                for cmd in plugin.get_cli_commands():
                    commands.append((name, cmd))
        return commands

    def get_web_routes(self) -> list[tuple[str, Any]]:
        """Get web routes from all active plugins."""
        routes = []
        for name, plugin in self._plugins.items():
            meta = self._metadata.get(name)
            if meta and meta.state == PluginState.ACTIVE:
                for route in plugin.get_web_routes():
                    routes.append((name, route))
        return routes

    def update_plugin_config(self, name: str, config: dict[str, Any]) -> None:
        """Update a plugin's configuration."""
        meta = self._metadata.get(name)
        if meta:
            meta.config = config

    async def reload_plugin(self, name: str) -> MnemosynePlugin:
        """Reload a plugin (unload and load again)."""
        await self.unload_plugin(name)
        return await self.load_plugin(name)


# Global plugin manager instance
_manager: PluginManager | None = None


def get_plugin_manager() -> PluginManager:
    """Get or create the global plugin manager."""
    global _manager
    if _manager is None:
        _manager = PluginManager()
    return _manager


async def initialize_plugins() -> dict[str, MnemosynePlugin | Exception]:
    """Initialize the plugin system and load all plugins."""
    manager = get_plugin_manager()
    await manager.discover_plugins()
    return await manager.load_all_plugins()
