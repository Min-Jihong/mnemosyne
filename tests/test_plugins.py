"""Tests for the plugin system."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mnemosyne.plugins.base import (
    MnemosynePlugin,
    PluginCapability,
    PluginContext,
    PluginManifest,
    PluginMetadata,
    PluginState,
)
from mnemosyne.plugins.exceptions import (
    PluginLoadError,
    PluginNotFoundError,
    PluginValidationError,
)
from mnemosyne.plugins.manager import PluginManager


class TestPluginManifest:
    """Tests for PluginManifest model."""

    def test_minimal_manifest(self) -> None:
        """Test manifest with only required fields."""
        manifest = PluginManifest(name="test-plugin", version="1.0.0")
        assert manifest.name == "test-plugin"
        assert manifest.version == "1.0.0"
        assert manifest.entry_point == "__init__.py"
        assert manifest.plugin_class == "Plugin"

    def test_full_manifest(self) -> None:
        """Test manifest with all fields."""
        manifest = PluginManifest(
            name="full-plugin",
            version="2.0.0",
            description="A full plugin",
            author="Test Author",
            license="MIT",
            entry_point="main.py",
            plugin_class="MyPlugin",
            capabilities=[PluginCapability.HOOKS, PluginCapability.CLI_COMMANDS],
            hooks=["post_capture", "pre_inference"],
            dependencies=["other-plugin"],
            python_requires=">=3.11",
            pip_dependencies=["requests"],
            config_schema={"type": "object"},
            default_config={"key": "value"},
        )
        assert manifest.description == "A full plugin"
        assert manifest.author == "Test Author"
        assert len(manifest.capabilities) == 2
        assert len(manifest.hooks) == 2
        assert manifest.dependencies == ["other-plugin"]


class TestPluginMetadata:
    """Tests for PluginMetadata dataclass."""

    def test_metadata_creation(self) -> None:
        """Test creating plugin metadata."""
        manifest = PluginManifest(name="test", version="1.0.0")
        metadata = PluginMetadata(
            manifest=manifest,
            path=Path("/tmp/test"),
        )
        assert metadata.state == PluginState.DISCOVERED
        assert metadata.loaded_at is None
        assert metadata.error_message is None


class TestPluginContext:
    """Tests for PluginContext."""

    def test_context_creation(self) -> None:
        """Test creating plugin context."""
        manager = MagicMock()
        context = PluginContext(
            manager=manager,
            plugin_name="test",
            plugin_path=Path("/tmp/test"),
            config={"key": "value"},
            data_dir=Path("/tmp/data"),
        )
        assert context.plugin_name == "test"
        assert context.config["key"] == "value"

    def test_context_get_plugin(self) -> None:
        """Test getting another plugin from context."""
        mock_plugin = MagicMock()
        manager = MagicMock()
        manager.get_plugin.return_value = mock_plugin

        context = PluginContext(
            manager=manager,
            plugin_name="test",
            plugin_path=Path("/tmp/test"),
            config={},
            data_dir=Path("/tmp/data"),
        )

        result = context.get_plugin("other")
        manager.get_plugin.assert_called_once_with("other")
        assert result == mock_plugin


class TestPluginManager:
    """Tests for PluginManager."""

    @pytest.fixture
    def plugin_dir(self) -> Path:
        """Create a temporary plugin directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def create_plugin(self, plugin_dir: Path):
        """Factory to create test plugins."""

        def _create(name: str, manifest_extra: dict | None = None) -> Path:
            plugin_path = plugin_dir / name
            plugin_path.mkdir(parents=True, exist_ok=True)

            # Create manifest
            manifest = {
                "name": name,
                "version": "1.0.0",
                **(manifest_extra or {}),
            }
            with open(plugin_path / "plugin.json", "w") as f:
                json.dump(manifest, f)

            # Create entry point
            init_content = '''
from mnemosyne.plugins.base import MnemosynePlugin, PluginContext

class Plugin(MnemosynePlugin):
    async def on_load(self, context: PluginContext) -> None:
        self.context = context
        self.loaded = True

    async def on_event(self, event_type: str, payload: dict) -> dict | None:
        payload["processed_by"] = self.context.plugin_name
        return payload
'''
            with open(plugin_path / "__init__.py", "w") as f:
                f.write(init_content)

            return plugin_path

        return _create

    @pytest.fixture
    def manager(self, plugin_dir: Path) -> PluginManager:
        """Create a plugin manager with the test directory."""
        with tempfile.TemporaryDirectory() as data_dir:
            return PluginManager(
                plugin_dirs=[plugin_dir],
                data_dir=Path(data_dir),
            )

    @pytest.mark.asyncio
    async def test_discover_plugins(
        self, manager: PluginManager, create_plugin
    ) -> None:
        """Test plugin discovery."""
        create_plugin("plugin-a")
        create_plugin("plugin-b")

        discovered = await manager.discover_plugins()
        assert len(discovered) == 2
        assert "plugin-a" in discovered
        assert "plugin-b" in discovered

    @pytest.mark.asyncio
    async def test_load_plugin(
        self, manager: PluginManager, create_plugin
    ) -> None:
        """Test loading a plugin."""
        create_plugin("test-plugin")
        await manager.discover_plugins()

        plugin = await manager.load_plugin("test-plugin")
        assert plugin is not None
        assert hasattr(plugin, "loaded")
        assert plugin.loaded is True

        metadata = manager.get_metadata("test-plugin")
        assert metadata is not None
        assert metadata.state == PluginState.ACTIVE

    @pytest.mark.asyncio
    async def test_load_plugin_not_found(self, manager: PluginManager) -> None:
        """Test loading non-existent plugin."""
        with pytest.raises(PluginNotFoundError):
            await manager.load_plugin("nonexistent")

    @pytest.mark.asyncio
    async def test_load_plugin_invalid_entry(
        self, manager: PluginManager, plugin_dir: Path
    ) -> None:
        """Test loading plugin with missing entry point."""
        plugin_path = plugin_dir / "bad-plugin"
        plugin_path.mkdir()

        manifest = {"name": "bad-plugin", "version": "1.0.0"}
        with open(plugin_path / "plugin.json", "w") as f:
            json.dump(manifest, f)

        await manager.discover_plugins()

        with pytest.raises(PluginValidationError):
            await manager.load_plugin("bad-plugin")

    @pytest.mark.asyncio
    async def test_unload_plugin(
        self, manager: PluginManager, create_plugin
    ) -> None:
        """Test unloading a plugin."""
        create_plugin("test-plugin")
        await manager.discover_plugins()
        await manager.load_plugin("test-plugin")

        assert manager.get_plugin("test-plugin") is not None

        await manager.unload_plugin("test-plugin")

        assert manager.get_plugin("test-plugin") is None
        metadata = manager.get_metadata("test-plugin")
        assert metadata.state == PluginState.DISCOVERED

    @pytest.mark.asyncio
    async def test_dispatch_event(
        self, manager: PluginManager, create_plugin
    ) -> None:
        """Test event dispatch to plugins."""
        create_plugin("test-plugin", {"hooks": ["test_event"]})
        await manager.discover_plugins()
        await manager.load_plugin("test-plugin")

        payload = {"data": "original"}
        result = await manager.dispatch_event("test_event", payload)

        assert result["processed_by"] == "test-plugin"

    @pytest.mark.asyncio
    async def test_load_all_plugins(
        self, manager: PluginManager, create_plugin
    ) -> None:
        """Test loading all discovered plugins."""
        create_plugin("plugin-a")
        create_plugin("plugin-b")
        await manager.discover_plugins()

        results = await manager.load_all_plugins()

        assert len(results) == 2
        assert all(
            not isinstance(r, Exception) for r in results.values()
        )

    @pytest.mark.asyncio
    async def test_dependency_order(
        self, manager: PluginManager, plugin_dir: Path
    ) -> None:
        """Test plugins are loaded in dependency order."""
        # Create plugin B that depends on plugin A
        plugin_a = plugin_dir / "plugin-a"
        plugin_a.mkdir()
        with open(plugin_a / "plugin.json", "w") as f:
            json.dump({"name": "plugin-a", "version": "1.0.0"}, f)
        with open(plugin_a / "__init__.py", "w") as f:
            f.write("""
from mnemosyne.plugins.base import MnemosynePlugin, PluginContext
class Plugin(MnemosynePlugin):
    async def on_load(self, context: PluginContext) -> None:
        pass
""")

        plugin_b = plugin_dir / "plugin-b"
        plugin_b.mkdir()
        with open(plugin_b / "plugin.json", "w") as f:
            json.dump({
                "name": "plugin-b",
                "version": "1.0.0",
                "dependencies": ["plugin-a"]
            }, f)
        with open(plugin_b / "__init__.py", "w") as f:
            f.write("""
from mnemosyne.plugins.base import MnemosynePlugin, PluginContext
class Plugin(MnemosynePlugin):
    async def on_load(self, context: PluginContext) -> None:
        # Verify plugin-a is already loaded
        assert context.get_plugin("plugin-a") is not None
""")

        await manager.discover_plugins()
        results = await manager.load_all_plugins()

        # Both should load successfully
        assert not isinstance(results.get("plugin-a"), Exception)
        assert not isinstance(results.get("plugin-b"), Exception)

    @pytest.mark.asyncio
    async def test_enable_disable_plugin(
        self, manager: PluginManager, create_plugin
    ) -> None:
        """Test enabling and disabling plugins."""
        create_plugin("test-plugin")
        await manager.discover_plugins()
        await manager.load_plugin("test-plugin")

        # Disable
        await manager.disable_plugin("test-plugin")
        metadata = manager.get_metadata("test-plugin")
        assert metadata.state == PluginState.DISABLED

        # Events should not be dispatched to disabled plugins
        payload = {"data": "test"}
        result = await manager.dispatch_event("test_event", payload)
        assert "processed_by" not in result

        # Enable
        await manager.enable_plugin("test-plugin")
        metadata = manager.get_metadata("test-plugin")
        assert metadata.state == PluginState.ACTIVE
