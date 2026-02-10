"""
Example Plugin for Mnemosyne

This plugin demonstrates how to create a Mnemosyne plugin with:
- Event hooks (post_capture, pre_inference)
- Configuration handling
- Logging

Use this as a template for creating your own plugins.
"""

from typing import Any

from mnemosyne.plugins.base import MnemosynePlugin, PluginContext


class ExamplePlugin(MnemosynePlugin):
    """
    Example plugin that logs events and demonstrates the plugin lifecycle.
    """

    def __init__(self) -> None:
        self.context: PluginContext | None = None
        self.event_count = 0

    async def on_load(self, context: PluginContext) -> None:
        """Called when the plugin is loaded."""
        self.context = context
        greeting = context.config.get("greeting", "Hello!")
        context.log(f"Example plugin loaded! {greeting}")

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded."""
        if self.context:
            self.context.log(f"Example plugin unloaded. Processed {self.event_count} events.")

    async def on_enable(self) -> None:
        """Called when the plugin is enabled."""
        if self.context:
            self.context.log("Example plugin enabled")

    async def on_disable(self) -> None:
        """Called when the plugin is disabled."""
        if self.context:
            self.context.log("Example plugin disabled")

    async def on_event(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        """
        Handle events from the hook system.

        Args:
            event_type: Type of event (post_capture, pre_inference, etc.)
            payload: Event data

        Returns:
            Modified payload or None
        """
        if not self.context:
            return None

        self.event_count += 1
        log_events = self.context.config.get("log_events", True)

        if log_events:
            self.context.log(f"Received event: {event_type} (#{self.event_count})")

        if event_type == "post_capture":
            # Example: Add metadata to captured events
            if "events" in payload:
                payload["plugin_processed"] = True
                payload["event_count"] = self.event_count

        elif event_type == "pre_inference":
            # Example: Modify inference context
            if "context" in payload:
                payload["context"]["example_plugin_active"] = True

        return payload

    def get_config_schema(self) -> dict[str, Any]:
        """Return the configuration schema for this plugin."""
        return {
            "type": "object",
            "properties": {
                "greeting": {
                    "type": "string",
                    "description": "Greeting message shown on load",
                },
                "log_events": {
                    "type": "boolean",
                    "description": "Whether to log each received event",
                },
            },
        }


# Required: Export the plugin class
Plugin = ExamplePlugin
