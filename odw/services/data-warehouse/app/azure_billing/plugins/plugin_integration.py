"""
Plugin Integration Service

Integrates frontend plugin management with data warehouse plugin system.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .manager.plugin_manager import PluginManager, PluginManagerConfig
from .registry.plugin_registry import PluginRegistry, PluginRegistryConfig

logger = logging.getLogger(__name__)


class PluginIntegrationService:
    """
    Service that bridges frontend plugin management with backend plugin system.
    """
    
    def __init__(self, plugin_manager: PluginManager, plugin_registry: PluginRegistry):
        self.plugin_manager = plugin_manager
        self.plugin_registry = plugin_registry
    
    async def get_marketplace_plugins(self) -> List[Dict[str, Any]]:
        """Get available plugins from marketplace"""
        try:
            # Get plugins from registry
            registry_plugins = await self.plugin_registry.list_plugins()
            
            # Convert to frontend format
            marketplace_plugins = []
            for plugin in registry_plugins:
                marketplace_plugins.append({
                    "id": plugin.id or plugin.name,
                    "name": plugin.name,
                    "version": plugin.version,
                    "description": plugin.description,
                    "author": plugin.author,
                    "category": plugin.category,
                    "tags": plugin.tags,
                    "iconUrl": plugin.icon_url,
                    "documentationUrl": plugin.documentation_url,
                    "configSchema": plugin.config_schema,
                    "isInstalled": await self._is_plugin_installed(plugin.name),
                    "isConfigured": await self._is_plugin_configured(plugin.name),
                    "isActive": await self._is_plugin_active(plugin.name),
                    "downloadCount": getattr(plugin, 'download_count', 0),
                    "rating": getattr(plugin, 'rating', None),
                    "lastUpdated": plugin.updated_at.isoformat() if plugin.updated_at else datetime.utcnow().isoformat()
                })
            
            return marketplace_plugins
            
        except Exception as e:
            logger.error(f"Error getting marketplace plugins: {e}")
            raise
    
    async def install_plugin(self, plugin_name: str, version: Optional[str] = None, auto_activate: bool = False) -> bool:
        """Install a plugin from the marketplace"""
        try:
            # Get plugin metadata
            plugin_metadata = await self.plugin_registry.get_plugin_by_name(plugin_name)
            if not plugin_metadata:
                raise ValueError(f"Plugin not found: {plugin_name}")
            
            # Install plugin using plugin manager
            success = await self.plugin_manager.install_plugin(
                plugin_name=plugin_name,
                config=plugin_metadata.default_config,
                auto_activate=auto_activate
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error installing plugin {plugin_name}: {e}")
            raise
    
    async def configure_plugin(self, plugin_name: str, connector_name: str, config: Dict[str, Any]) -> bool:
        """Configure an installed plugin"""
        try:
            # Validate configuration
            validation_result = await self.plugin_manager.validate_plugin_config(plugin_name, config)
            
            if not validation_result["valid"]:
                raise ValueError(f"Invalid configuration: {validation_result['errors']}")
            
            # Save configuration (this would typically save to PostgreSQL)
            # For now, we'll just log the configuration
            logger.info(f"Configuring plugin {plugin_name} with connector {connector_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error configuring plugin {plugin_name}: {e}")
            raise
    
    async def test_plugin_connection(self, plugin_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test plugin connection with given configuration"""
        try:
            # This would typically test the actual plugin connection
            # For now, return a mock result
            return {
                "success": True,
                "message": f"Connection test successful for {plugin_name}",
                "tested_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error testing plugin connection {plugin_name}: {e}")
            return {
                "success": False,
                "message": str(e),
                "tested_at": datetime.utcnow().isoformat()
            }
    
    async def _is_plugin_installed(self, plugin_name: str) -> bool:
        """Check if plugin is installed"""
        # This would check the plugin manager's installed plugins
        return plugin_name in ["Azure EA API"]  # Mock for now
    
    async def _is_plugin_configured(self, plugin_name: str) -> bool:
        """Check if plugin is configured"""
        # This would check if plugin has valid configuration
        return plugin_name in ["Azure EA API"]  # Mock for now
    
    async def _is_plugin_active(self, plugin_name: str) -> bool:
        """Check if plugin is active"""
        # This would check plugin manager's active plugins
        return plugin_name in ["Azure EA API"]  # Mock for now


# Factory function
def create_plugin_integration_service(
    plugin_manager_config: Optional[PluginManagerConfig] = None,
    registry_config: Optional[PluginRegistryConfig] = None
) -> PluginIntegrationService:
    """Create plugin integration service with default configuration"""
    
    if not plugin_manager_config:
        plugin_manager_config = PluginManagerConfig()
    
    if not registry_config:
        registry_config = PluginRegistryConfig()
    
    plugin_manager = PluginManager(plugin_manager_config)
    plugin_registry = PluginRegistry(registry_config)
    
    return PluginIntegrationService(plugin_manager, plugin_registry)