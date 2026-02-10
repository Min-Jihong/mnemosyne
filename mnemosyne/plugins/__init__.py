"""
Mnemosyne Plugin System

A flexible plugin architecture for extending Mnemosyne's capabilities.

Plugins can:
- Listen to lifecycle events (hooks)
- Add new commands to the CLI
- Extend the web interface
- Add new LLM providers
- Add new capture sources
- Extend memory capabilities

Example plugin structure:
    my_plugin/
    ├── plugin.json       # Manifest with metadata
    ├── __init__.py       # Plugin entry point
    └── handlers.py       # Event handlers

Example plugin.json:
    {
        "name": "my-plugin",
        "version": "1.0.0",
        "description": "My awesome plugin",
        "entry_point": "__init__.py",
        "hooks": ["post_capture", "pre_inference"]
    }
"""

from mnemosyne.plugins.base import (
    MnemosynePlugin,
    PluginContext,
    PluginManifest,
    PluginMetadata,
)
from mnemosyne.plugins.manager import PluginManager
from mnemosyne.plugins.exceptions import (
    PluginError,
    PluginLoadError,
    PluginNotFoundError,
    PluginValidationError,
)

__all__ = [
    "MnemosynePlugin",
    "PluginContext",
    "PluginManifest",
    "PluginMetadata",
    "PluginManager",
    "PluginError",
    "PluginLoadError",
    "PluginNotFoundError",
    "PluginValidationError",
]
