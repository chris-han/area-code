"""
Azure Billing Intelligence FastAPI Application

Extended FastAPI application that integrates with Moose framework
for ABI-specific endpoints, dependency injection, and middleware.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
import logging
import asyncio
from datetime import datetime
from pathlib import Path

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

# ABI imports
from app.azure_billing.plugins.manager.plugin_manager import (
    PluginManager,
    PluginManagerConfig,
)
from app.azure_billing.plugins.registry.plugin_registry import (
    PluginRegistry,
    PluginRegistryConfig,
)

logger = logging.getLogger(__name__)


class ABIApplication:
    """Azure Billing Intelligence FastAPI Application"""
    
    def __init__(self):
        self.app: Optional[FastAPI] = None
        self.plugin_manager: Optional[PluginManager] = None
        self.plugin_registry: Optional[PluginRegistry] = None
        self._clickhouse_client = None
        self._temporal_client = None
        self._redis_client = None
        self._moose_config: Optional[Dict[str, Any]] = None
    
    async def initialize_dependencies(self):
        """Initialize ABI system dependencies"""
        try:
            config = self._load_moose_config()
            registry_config = PluginRegistryConfig.from_dict(
                config.get("plugin_registry_db", {})
            )
            
            # Initialize plugin registry
            self.plugin_registry = PluginRegistry(registry_config)
            await self.plugin_registry.initialize()
            
            # Initialize plugin manager
            plugin_system = config.get("plugin_system", {})
            manager_config = PluginManagerConfig(
                plugin_directory=plugin_system.get("plugin_directory", "./plugins"),
                registry_config=registry_config,
                lazy_loading=plugin_system.get("lazy_loading", True),
                cache_plugins=plugin_system.get("cache_plugins", True),
                auto_health_check=plugin_system.get("auto_health_check", True),
            )
            self.plugin_manager = PluginManager(manager_config)
            await self.plugin_manager.initialize()
            # Ensure the manager reuses the already-initialized registry pool
            self.plugin_manager.registry = self.plugin_registry
            
            # Initialize other clients (ClickHouse, Temporal, Redis)
            await self._initialize_clients()
            
            logger.info("ABI dependencies initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ABI dependencies: {e}")
            raise
    
    async def _initialize_clients(self):
        """Initialize database and service clients"""
        # ClickHouse client initialization
        try:
            import clickhouse_connect
            self._clickhouse_client = clickhouse_connect.get_client(
                host='ck.mightytech.cn',
                port=8443,
                username='finops',
                password='cU2f947&9T{6d',
                database='finops-odw',
                secure=True
            )
            logger.info("ClickHouse client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ClickHouse client: {e}")
        
        # Temporal client initialization
        try:
            from temporalio.client import Client
            self._temporal_client = await Client.connect("localhost:7233")
            logger.info("Temporal client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Temporal client: {e}")
        
        # Redis client initialization
        try:
            import redis.asyncio as redis
            self._redis_client = redis.from_url("redis://localhost:6379")
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")   
 
    async def cleanup_dependencies(self):
        """Cleanup ABI system dependencies"""
        try:
            if self._temporal_client:
                await self._temporal_client.close()
            
            if self._redis_client:
                await self._redis_client.close()
            
            if self._clickhouse_client:
                self._clickhouse_client.close()
            
            if self.plugin_manager:
                try:
                    await self.plugin_manager.shutdown()
                except Exception as shutdown_error:  # pragma: no cover - cleanup best effort
                    logger.warning(f"Plugin manager shutdown issue: {shutdown_error}")
            
            if self.plugin_registry:
                await self.plugin_registry.close()
            
            logger.info("ABI dependencies cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _load_moose_config(self) -> Dict[str, Any]:
        """Load and cache moose.config.toml."""
        if self._moose_config is not None:
            return self._moose_config
        
        config_path = Path(__file__).resolve().parents[4] / "moose.config.toml"
        if not config_path.exists():
            raise FileNotFoundError(
                f"Missing moose configuration file at {config_path}"
            )
        
        with config_path.open("rb") as fh:
            config = tomllib.load(fh)
        
        self._moose_config = config
        return config
    
    def get_clickhouse_client(self):
        """Get ClickHouse client dependency"""
        if not self._clickhouse_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ClickHouse client not available"
            )
        return self._clickhouse_client
    
    def get_temporal_client(self):
        """Get Temporal client dependency"""
        if not self._temporal_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Temporal client not available"
            )
        return self._temporal_client
    
    def get_redis_client(self):
        """Get Redis client dependency"""
        if not self._redis_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis client not available"
            )
        return self._redis_client
    
    def get_plugin_manager(self) -> PluginManager:
        """Get plugin manager dependency"""
        if not self.plugin_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Plugin manager not available"
            )
        return self.plugin_manager
    
    def get_plugin_registry(self) -> PluginRegistry:
        """Get plugin registry dependency."""
        if not self.plugin_registry:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Plugin registry not available"
            )
        return self.plugin_registry
    
    def create_app(self) -> FastAPI:
        """Create and configure FastAPI application"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            await self.initialize_dependencies()
            yield
            # Shutdown
            await self.cleanup_dependencies()
        
        # Create FastAPI app
        app = FastAPI(
            title="Azure Billing Intelligence API",
            description="FOCUS-compliant billing analytics and workflow orchestration",
            version="1.0.0",
            lifespan=lifespan
        )
        
        # Add middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:3000",
                "http://localhost:3003",
                "http://localhost:8080",
                "http://localhost:8081",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        # Add dependency providers
        app.dependency_overrides[self.get_clickhouse_client] = self.get_clickhouse_client
        app.dependency_overrides[self.get_temporal_client] = self.get_temporal_client
        app.dependency_overrides[self.get_redis_client] = self.get_redis_client
        app.dependency_overrides[self.get_plugin_manager] = self.get_plugin_manager
        app.dependency_overrides[self.get_plugin_registry] = self.get_plugin_registry
        
        self.app = app
        return app


# Global ABI application instance
abi_app = ABIApplication()


# Dependency functions for FastAPI
def get_clickhouse_client():
    """FastAPI dependency for ClickHouse client"""
    return abi_app.get_clickhouse_client()


def get_temporal_client():
    """FastAPI dependency for Temporal client"""
    return abi_app.get_temporal_client()


def get_redis_client():
    """FastAPI dependency for Redis client"""
    return abi_app.get_redis_client()


def get_plugin_manager() -> PluginManager:
    """FastAPI dependency for plugin manager"""
    return abi_app.get_plugin_manager()


def get_plugin_registry() -> PluginRegistry:
    """FastAPI dependency for plugin registry"""
    return abi_app.get_plugin_registry()
