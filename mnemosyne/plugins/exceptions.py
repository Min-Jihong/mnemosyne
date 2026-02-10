"""Plugin system exceptions."""


class PluginError(Exception):
    """Base exception for plugin-related errors."""

    pass


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""

    def __init__(self, plugin_name: str, reason: str) -> None:
        self.plugin_name = plugin_name
        self.reason = reason
        super().__init__(f"Failed to load plugin '{plugin_name}': {reason}")


class PluginNotFoundError(PluginError):
    """Raised when a requested plugin is not found."""

    def __init__(self, plugin_name: str) -> None:
        self.plugin_name = plugin_name
        super().__init__(f"Plugin '{plugin_name}' not found")


class PluginValidationError(PluginError):
    """Raised when plugin validation fails."""

    def __init__(self, plugin_name: str, errors: list[str]) -> None:
        self.plugin_name = plugin_name
        self.errors = errors
        error_str = "; ".join(errors)
        super().__init__(f"Plugin '{plugin_name}' validation failed: {error_str}")


class PluginDependencyError(PluginError):
    """Raised when plugin dependencies cannot be satisfied."""

    def __init__(self, plugin_name: str, missing: list[str]) -> None:
        self.plugin_name = plugin_name
        self.missing = missing
        missing_str = ", ".join(missing)
        super().__init__(f"Plugin '{plugin_name}' missing dependencies: {missing_str}")


class PluginConflictError(PluginError):
    """Raised when plugins conflict with each other."""

    def __init__(self, plugin_a: str, plugin_b: str, reason: str) -> None:
        self.plugin_a = plugin_a
        self.plugin_b = plugin_b
        self.reason = reason
        super().__init__(f"Plugin conflict between '{plugin_a}' and '{plugin_b}': {reason}")
