"""
Plugin Manager Module

Manages plugin lifecycle with lazy loading, discovery, installation,
and configuration validation for the bia plugin system.
"""

from .plugin_manager import (
    PluginManager,
    PluginManagerConfig,
    BasePlugin,
    PluginInstance,
    PluginLifecycleState
)

from .config_validator import (
    PluginConfigValidator,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity
)

__all__ = [
    "PluginManager",
    "PluginManagerConfig",
    "BasePlugin", 
    "PluginInstance",
    "PluginLifecycleState",
    "PluginConfigValidator",
    "ValidationResult",
    "ValidationIssue",
    "ValidationSeverity"
]