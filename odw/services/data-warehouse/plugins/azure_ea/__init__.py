"""
Azure Enterprise Agreement Plugin

Data source plugin for Azure EA API integration with FOCUS transformation.
"""

from .plugin import AzureEAPlugin, create_plugin

__all__ = ["AzureEAPlugin", "create_plugin"]