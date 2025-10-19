"""
Plugin Manager

Manages plugin lifecycle with lazy loading, discovery, installation,
and configuration validation for the ABI plugin system.
"""

from typing import Dict, Any, List, Optional, Type, Callable, Union
from datetime import datetime
from pathlib import Path
import importlib
import importlib.util
import sys
import os
import json
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from ..registry import (
    PluginRegistry, PluginRegistryConfig, PluginMetadata, PluginInstallation,
    PluginType, PluginStatus, InstallationStatus, HealthStatus
)

logger = logging.getLogger(__name__)


class PluginLifecycleState(Enum):
    """Plugin lifecycle states"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginInstance:
    """Represents a loaded plugin instance"""
    metadata: PluginMetadata
    installation: PluginInstallation
    instance: Any
    state: PluginLifecycleState
    last_health_check: Optional[datetime] = None
    error_message: Optional[str] = None
    load_time: Optional[datetime] = None


class BasePlugin(ABC):
    """
    Abstract base class for all ABI plugins.
    
    All plugins must inherit from this class and implement the required methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the plugin with the provided configuration.
        
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the plugin.
        
        Returns:
            Health check results
        """
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up plugin resources"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return plugin metadata"""
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized"""
        return self._initialized


class PluginManagerConfig:
    """Plugin manager configuration"""
    
    def __init__(self, 
                 plugin_directory: str = "./plugins",
                 registry_config: Optional[PluginRegistryConfig] = None,
                 lazy_loading: bool = True,
                 cache_plugins: bool = True,
                 auto_health_check: bool = True,
                 health_check_interval: int = 300,  # 5 minutes
                 max_load_retries: int = 3,
                 load_timeout: int = 30):
        self.plugin_directory = Path(plugin_directory)
        self.registry_config = registry_config
        self.lazy_loading = lazy_loading
        self.cache_plugins = cache_plugins
        self.auto_health_check = auto_health_check
        self.health_check_interval = health_check_interval
        self.max_load_retries = max_load_retries
        self.load_timeout = load_timeout


class PluginManager:
    """
    Comprehensive plugin manager with lazy loading, lifecycle management,
    and configuration validation capabilities.
    """
    
    def __init__(self, config: PluginManagerConfig):
        self.config = config
        self.registry: Optional[PluginRegistry] = None
        
        # Plugin storage
        self._loaded_plugins: Dict[str, PluginInstance] = {}
        self._plugin_cache: Dict[str, Type] = {}
        self._installation_cache: Dict[str, PluginInstallation] = {}
        
        # Lifecycle management
        self._health_check_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Instance identification
        self.instance_id = os.environ.get("ABI_INSTANCE_ID", "default")
    
    async def initialize(self):
        """Initialize the plugin manager"""
        # Initialize plugin registry if configured
        if self.config.registry_config:
            self.registry = PluginRegistry(self.config.registry_config)
            await self.registry.initialize()
        
        # Create plugin directory if it doesn't exist
        self.config.plugin_directory.mkdir(parents=True, exist_ok=True)
        
        # Start health check task if enabled
        if self.config.auto_health_check:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info("Plugin manager initialized")
    
    async def shutdown(self):
        """Shutdown the plugin manager and cleanup resources"""
        self._shutdown_event.set()
        
        # Stop health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup all loaded plugins
        for plugin_instance in self._loaded_plugins.values():
            try:
                if plugin_instance.instance and hasattr(plugin_instance.instance, 'cleanup'):
                    await plugin_instance.instance.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin {plugin_instance.metadata.name}: {e}")
        
        # Close registry connection
        if self.registry:
            await self.registry.close()
        
        logger.info("Plugin manager shutdown complete")
    
    async def discover_plugins(self) -> List[PluginMetadata]:
        """
        Discover available plugins from the plugin directory.
        
        Returns:
            List of discovered plugin metadata
        """
        discovered_plugins = []
        
        # Scan plugin directory
        for plugin_path in self.config.plugin_directory.iterdir():
            if plugin_path.is_dir():
                try:
                    metadata = await self._load_plugin_metadata(plugin_path)
                    if metadata:
                        discovered_plugins.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to load plugin metadata from {plugin_path}: {e}")
        
        # Also get plugins from registry if available
        if self.registry:
            try:
                registry_plugins = await self.registry.list_plugins(status=PluginStatus.ACTIVE)
                discovered_plugins.extend(registry_plugins)
            except Exception as e:
                logger.error(f"Failed to get plugins from registry: {e}")
        
        logger.info(f"Discovered {len(discovered_plugins)} plugins")
        return discovered_plugins
    
    async def install_plugin(self, 
                           plugin_name: str, 
                           config: Optional[Dict[str, Any]] = None,
                           auto_activate: bool = True) -> bool:
        """
        Install a plugin.
        
        Args:
            plugin_name: Name of the plugin to install
            config: Plugin configuration
            auto_activate: Whether to activate the plugin after installation
            
        Returns:
            True if installation successful
        """
        try:
            # Get plugin metadata from registry
            if not self.registry:
                raise ValueError("Plugin registry not available")
            
            plugin_metadata = await self.registry.get_plugin_by_name(plugin_name)
            if not plugin_metadata:
                raise ValueError(f"Plugin not found: {plugin_name}")
            
            # Create installation record
            installation_id = f"{self.instance_id}_{plugin_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            installation = PluginInstallation(
                id=None,
                plugin_id=plugin_metadata.id,
                version_id=None,  # TODO: Handle versions
                installation_id=installation_id,
                instance_id=self.instance_id,
                config=config or plugin_metadata.default_config,
                status=InstallationStatus.INSTALLED,
                installed_by="system",  # TODO: Get actual user
                installation_method="manager"
            )
            
            # Save installation to registry
            await self.registry.create_installation(installation)
            
            # Cache installation
            self._installation_cache[installation_id] = installation
            
            # Auto-activate if requested
            if auto_activate:
                await self.activate_plugin(installation_id)
            
            logger.info(f"Plugin installed successfully: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install plugin {plugin_name}: {e}")
            return False
    
    async def activate_plugin(self, installation_id: str) -> bool:
        """
        Activate an installed plugin (lazy loading).
        
        Args:
            installation_id: Installation identifier
            
        Returns:
            True if activation successful
        """
        try:
            # Get installation details
            installation = await self._get_installation(installation_id)
            if not installation:
                raise ValueError(f"Installation not found: {installation_id}")
            
            # Check if already loaded
            if installation_id in self._loaded_plugins:
                plugin_instance = self._loaded_plugins[installation_id]
                if plugin_instance.state == PluginLifecycleState.ACTIVE:
                    return True
            
            # Load plugin
            plugin_instance = await self._load_plugin(installation)
            if not plugin_instance:
                return False
            
            # Initialize plugin
            success = await self._initialize_plugin(plugin_instance)
            if success:
                plugin_instance.state = PluginLifecycleState.ACTIVE
                
                # Update installation status in registry
                if self.registry:
                    await self.registry.update_installation_status(
                        installation_id, 
                        InstallationStatus.ACTIVE,
                        HealthStatus.HEALTHY
                    )
                
                logger.info(f"Plugin activated: {installation_id}")
                return True
            else:
                plugin_instance.state = PluginLifecycleState.ERROR
                return False
                
        except Exception as e:
            logger.error(f"Failed to activate plugin {installation_id}: {e}")
            return False
    
    async def deactivate_plugin(self, installation_id: str) -> bool:
        """
        Deactivate a plugin.
        
        Args:
            installation_id: Installation identifier
            
        Returns:
            True if deactivation successful
        """
        try:
            if installation_id not in self._loaded_plugins:
                return True  # Already deactivated
            
            plugin_instance = self._loaded_plugins[installation_id]
            
            # Cleanup plugin
            if plugin_instance.instance and hasattr(plugin_instance.instance, 'cleanup'):
                await plugin_instance.instance.cleanup()
            
            # Update state
            plugin_instance.state = PluginLifecycleState.DISABLED
            
            # Update installation status in registry
            if self.registry:
                await self.registry.update_installation_status(
                    installation_id, 
                    InstallationStatus.DISABLED
                )
            
            logger.info(f"Plugin deactivated: {installation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate plugin {installation_id}: {e}")
            return False
    
    async def get_plugin(self, installation_id: str) -> Optional[Any]:
        """
        Get a plugin instance (lazy loading).
        
        Args:
            installation_id: Installation identifier
            
        Returns:
            Plugin instance or None
        """
        # Check if already loaded
        if installation_id in self._loaded_plugins:
            plugin_instance = self._loaded_plugins[installation_id]
            if plugin_instance.state == PluginLifecycleState.ACTIVE:
                return plugin_instance.instance
        
        # Lazy load if enabled
        if self.config.lazy_loading:
            success = await self.activate_plugin(installation_id)
            if success and installation_id in self._loaded_plugins:
                return self._loaded_plugins[installation_id].instance
        
        return None
    
    async def list_active_plugins(self) -> List[PluginInstance]:
        """
        List all active plugin instances.
        
        Returns:
            List of active plugin instances
        """
        return [
            plugin for plugin in self._loaded_plugins.values()
            if plugin.state == PluginLifecycleState.ACTIVE
        ]
    
    async def get_plugin_status(self, installation_id: str) -> Dict[str, Any]:
        """
        Get detailed plugin status.
        
        Args:
            installation_id: Installation identifier
            
        Returns:
            Plugin status information
        """
        status = {
            "installation_id": installation_id,
            "state": "unknown",
            "loaded": False,
            "healthy": False,
            "last_health_check": None,
            "error_message": None
        }
        
        if installation_id in self._loaded_plugins:
            plugin_instance = self._loaded_plugins[installation_id]
            status.update({
                "state": plugin_instance.state.value,
                "loaded": True,
                "last_health_check": plugin_instance.last_health_check,
                "error_message": plugin_instance.error_message
            })
            
            # Perform health check if plugin is active
            if plugin_instance.state == PluginLifecycleState.ACTIVE:
                try:
                    health_result = await plugin_instance.instance.health_check()
                    status["healthy"] = health_result.get("healthy", False)
                    status["health_details"] = health_result
                except Exception as e:
                    status["healthy"] = False
                    status["error_message"] = str(e)
        
        return status
    
    async def validate_plugin_config(self, 
                                   plugin_name: str, 
                                   config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate plugin configuration against schema.
        
        Args:
            plugin_name: Plugin name
            config: Configuration to validate
            
        Returns:
            Validation results
        """
        validation_result = {
            "valid": False,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Get plugin metadata
            if not self.registry:
                raise ValueError("Plugin registry not available")
            
            plugin_metadata = await self.registry.get_plugin_by_name(plugin_name)
            if not plugin_metadata:
                raise ValueError(f"Plugin not found: {plugin_name}")
            
            # Validate against schema if available
            if plugin_metadata.config_schema:
                # TODO: Implement JSON schema validation
                # For now, just check required fields
                schema = plugin_metadata.config_schema
                if "required" in schema:
                    for required_field in schema["required"]:
                        if required_field not in config:
                            validation_result["errors"].append(f"Missing required field: {required_field}")
            
            # Check if there are any errors
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
        except Exception as e:
            validation_result["errors"].append(str(e))
        
        return validation_result
    
    async def _load_plugin(self, installation: PluginInstallation) -> Optional[PluginInstance]:
        """Load a plugin from installation details"""
        try:
            # Get plugin metadata
            if not self.registry:
                raise ValueError("Plugin registry not available")
            
            plugin_metadata = await self.registry.get_plugin(installation.plugin_id)
            if not plugin_metadata:
                raise ValueError(f"Plugin metadata not found: {installation.plugin_id}")
            
            # Check cache first
            cache_key = f"{plugin_metadata.name}_{plugin_metadata.version}"
            if self.config.cache_plugins and cache_key in self._plugin_cache:
                plugin_class = self._plugin_cache[cache_key]
            else:
                # Load plugin module
                plugin_class = await self._load_plugin_module(plugin_metadata)
                if self.config.cache_plugins:
                    self._plugin_cache[cache_key] = plugin_class
            
            # Create plugin instance
            plugin_instance = PluginInstance(
                metadata=plugin_metadata,
                installation=installation,
                instance=None,
                state=PluginLifecycleState.LOADED,
                load_time=datetime.utcnow()
            )
            
            # Store in loaded plugins
            self._loaded_plugins[installation.installation_id] = plugin_instance
            
            return plugin_instance
            
        except Exception as e:
            logger.error(f"Failed to load plugin: {e}")
            return None
    
    async def _load_plugin_module(self, metadata: PluginMetadata) -> Type:
        """Load plugin module and return plugin class"""
        try:
            # Construct plugin path
            plugin_path = self.config.plugin_directory / metadata.name
            
            # Load module
            if plugin_path.exists():
                # Load from local directory
                spec = importlib.util.spec_from_file_location(
                    metadata.name, 
                    plugin_path / "__init__.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                # Try to import as installed package
                module = importlib.import_module(metadata.entry_point)
            
            # Get plugin class
            if hasattr(module, 'create_plugin'):
                return module.create_plugin
            elif hasattr(module, 'Plugin'):
                return module.Plugin
            else:
                raise ValueError(f"Plugin class not found in {metadata.entry_point}")
                
        except Exception as e:
            logger.error(f"Failed to load plugin module {metadata.name}: {e}")
            raise
    
    async def _initialize_plugin(self, plugin_instance: PluginInstance) -> bool:
        """Initialize a loaded plugin"""
        try:
            plugin_instance.state = PluginLifecycleState.INITIALIZING
            
            # Create plugin instance
            plugin_class = self._plugin_cache.get(
                f"{plugin_instance.metadata.name}_{plugin_instance.metadata.version}"
            )
            
            if not plugin_class:
                raise ValueError("Plugin class not found in cache")
            
            # Instantiate plugin with configuration
            config = plugin_instance.installation.config or {}
            plugin_instance.instance = plugin_class(config)
            
            # Initialize plugin
            success = await plugin_instance.instance.initialize()
            
            if success:
                plugin_instance.state = PluginLifecycleState.ACTIVE
                logger.info(f"Plugin initialized: {plugin_instance.metadata.name}")
                return True
            else:
                plugin_instance.state = PluginLifecycleState.ERROR
                plugin_instance.error_message = "Initialization failed"
                return False
                
        except Exception as e:
            plugin_instance.state = PluginLifecycleState.ERROR
            plugin_instance.error_message = str(e)
            logger.error(f"Failed to initialize plugin {plugin_instance.metadata.name}: {e}")
            return False
    
    async def _get_installation(self, installation_id: str) -> Optional[PluginInstallation]:
        """Get installation details with caching"""
        # Check cache first
        if installation_id in self._installation_cache:
            return self._installation_cache[installation_id]
        
        # Get from registry
        if self.registry:
            installation = await self.registry.get_installation(installation_id)
            if installation:
                self._installation_cache[installation_id] = installation
            return installation
        
        return None
    
    async def _load_plugin_metadata(self, plugin_path: Path) -> Optional[PluginMetadata]:
        """Load plugin metadata from plugin directory"""
        try:
            # Look for plugin.json or __init__.py
            metadata_file = plugin_path / "plugin.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata_dict = json.load(f)
                
                # Convert to PluginMetadata
                return PluginMetadata(
                    id=None,
                    name=metadata_dict["name"],
                    display_name=metadata_dict.get("display_name", metadata_dict["name"]),
                    description=metadata_dict.get("description", ""),
                    version=metadata_dict["version"],
                    author=metadata_dict.get("author", "Unknown"),
                    category=metadata_dict.get("category", "utility"),
                    tags=metadata_dict.get("tags", []),
                    plugin_type=PluginType(metadata_dict.get("plugin_type", "utility")),
                    entry_point=metadata_dict["entry_point"],
                    requirements=metadata_dict.get("requirements", []),
                    icon_url=metadata_dict.get("icon_url"),
                    documentation_url=metadata_dict.get("documentation_url"),
                    repository_url=metadata_dict.get("repository_url"),
                    license=metadata_dict.get("license"),
                    config_schema=metadata_dict.get("config_schema"),
                    default_config=metadata_dict.get("default_config")
                )
            
        except Exception as e:
            logger.error(f"Failed to load plugin metadata from {plugin_path}: {e}")
        
        return None
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                # Perform health checks on active plugins
                for installation_id, plugin_instance in self._loaded_plugins.items():
                    if plugin_instance.state == PluginLifecycleState.ACTIVE:
                        try:
                            health_result = await plugin_instance.instance.health_check()
                            plugin_instance.last_health_check = datetime.utcnow()
                            
                            # Update health status in registry
                            if self.registry:
                                health_status = HealthStatus.HEALTHY if health_result.get("healthy", False) else HealthStatus.UNHEALTHY
                                await self.registry.update_installation_status(
                                    installation_id,
                                    InstallationStatus.ACTIVE,
                                    health_status
                                )
                                
                        except Exception as e:
                            logger.warning(f"Health check failed for plugin {installation_id}: {e}")
                            plugin_instance.error_message = str(e)
                            
                            # Update as unhealthy
                            if self.registry:
                                await self.registry.update_installation_status(
                                    installation_id,
                                    InstallationStatus.ACTIVE,
                                    HealthStatus.UNHEALTHY
                                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")