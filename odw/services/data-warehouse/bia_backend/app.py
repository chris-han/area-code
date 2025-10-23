"""
Azure Billing Intelligence FastAPI Application

Provides dependency injection, client management, lifecycle handling,
and application factory for ABI-specific endpoints and services.

This module serves as the complete ABI application factory, including:
- Dependency management (ClickHouse, Temporal, Redis, Plugins)
- FastAPI application creation with middleware
- ABI router registration
- Optional Moose framework integration
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

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
    """
    Azure Billing Intelligence FastAPI Application

    Manages application lifecycle, client initialization, and dependency injection
    for ABI services including ClickHouse, Temporal, Redis, and plugin systems.
    """

    def __init__(self):
        self.app: Optional[FastAPI] = None
        self.plugin_manager: Optional[PluginManager] = None
        self.plugin_registry: Optional[PluginRegistry] = None
        self._clickhouse_client = None
        self._temporal_client = None
        self._redis_client = None
        self._moose_config: Optional[Dict[str, Any]] = None
    
    async def initialize_dependencies(self):
        """
        Initialize ABI system dependencies.

        Initializes:
        - Plugin registry and manager
        - ClickHouse client
        - Temporal client
        - Redis client
        """
        try:
            config = self._load_moose_config()
            registry_config = PluginRegistryConfig.from_dict(
                config.get("plugin_registry_db", {})
            )

            # Initialize plugin registry (optional)
            try:
                self.plugin_registry = PluginRegistry(registry_config)
                await self.plugin_registry.initialize()
                registry_for_manager = registry_config
                logger.info("Plugin registry initialised successfully")
            except Exception as registry_error:
                logger.warning(
                    "Plugin registry unavailable; continuing without persistent plugin configs: %s",
                    registry_error,
                )
                self.plugin_registry = None
                registry_for_manager = None

            # Initialize plugin manager
            plugin_system = config.get("plugin_system", {})
            manager_config = PluginManagerConfig(
                plugin_directory=plugin_system.get("plugin_directory", "./plugins"),
                registry_config=registry_for_manager,
                lazy_loading=plugin_system.get("lazy_loading", True),
                cache_plugins=plugin_system.get("cache_plugins", True),
                auto_health_check=plugin_system.get("auto_health_check", True),
            )
            self.plugin_manager = PluginManager(manager_config)
            await self.plugin_manager.initialize()
            if self.plugin_registry:
                # Ensure the manager reuses the already-initialized registry pool
                self.plugin_manager.registry = self.plugin_registry

            # Initialize other clients (ClickHouse, Temporal, Redis)
            await self._initialize_clients(config)

            logger.info("ABI dependencies initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ABI dependencies: {e}")
            raise
    
    async def _initialize_clients(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize database and service clients.

        Initializes ClickHouse, Temporal, and Redis clients.
        Failures are logged but do not prevent other clients from initializing.
        """
        config = config or self._load_moose_config()
        temporal_settings: Dict[str, Any] = config.get("temporal_config", {}) if config else {}
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
            import subprocess

            # Resolve Temporal host configuration (env > moose.config > docker fallback)
            env_host = os.environ.get("TEMPORAL_HOST")
            env_port = os.environ.get("TEMPORAL_PORT")

            config_host = temporal_settings.get("temporal_host")
            config_port = temporal_settings.get("temporal_port")

            host = env_host or config_host
            port = env_port or config_port or 7233

            temporal_host = None
            if host:
                host_str = str(host)
                if ":" in host_str:
                    temporal_host = host_str
                else:
                    temporal_host = f"{host_str}:{port}"

            if not temporal_host:
                try:
                    # Check if we're in Docker environment by checking if Temporal container exists
                    subprocess.run(
                        ['docker', 'inspect', 'data-warehouse-temporal-1'],
                        capture_output=True, text=True, check=True
                    )
                    # Use container name (more stable than IP as requested by user)
                    temporal_host = f"data-warehouse-temporal-1:{port}"
                except Exception:
                    # Fallback to localhost if not in Docker environment
                    temporal_host = f"localhost:{port}"

            logger.info(f"Connecting to Temporal at: {temporal_host}")
            self._temporal_client = await Client.connect(temporal_host)
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
        """
        Cleanup ABI system dependencies.

        Closes all client connections and shuts down plugin systems.
        Errors during cleanup are logged but don't prevent other cleanups.
        """
        try:
            if self._temporal_client:
                close_method = getattr(self._temporal_client, "close", None)
                disconnect_method = getattr(self._temporal_client, "disconnect", None)

                if close_method:
                    result = close_method()
                    if asyncio.iscoroutine(result):
                        await result
                elif disconnect_method:
                    result = disconnect_method()
                    if asyncio.iscoroutine(result):
                        await result

                self._temporal_client = None

            if self._redis_client:
                await self._redis_client.close()

            if self._clickhouse_client:
                self._clickhouse_client.close()

            if self.plugin_manager:
                try:
                    await self.plugin_manager.shutdown()
                except Exception as shutdown_error:
                    logger.warning(f"Plugin manager shutdown issue: {shutdown_error}")

            if self.plugin_registry:
                await self.plugin_registry.close()

            logger.info("ABI dependencies cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _load_moose_config(self) -> Dict[str, Any]:
        """
        Load and cache moose.config.toml configuration file.

        Returns:
            Dict[str, Any]: Configuration dictionary

        Raises:
            FileNotFoundError: If moose.config.toml doesn't exist
        """
        if self._moose_config is not None:
            return self._moose_config

        service_root = Path(__file__).resolve().parents[1]
        config_path = service_root / "moose.config.toml"
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
        """
        Create and configure FastAPI application.

        Returns:
            FastAPI: Configured FastAPI application with middleware and lifecycle
        """

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

        # Add CORS middleware
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

        # Add GZip compression
        app.add_middleware(GZipMiddleware, minimum_size=1000)

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




def create_abi_fastapi_app() -> FastAPI:
    """
    Create and configure the complete ABI FastAPI application.

    This creates the application with:
    - ABI APIs (billing, workflows, plugins, health checks)
    - Base FastAPI configuration
    - Middleware setup

    Note: This is called from app.main which also loads Moose components.

    Returns:
        FastAPI: Configured FastAPI application with all ABI endpoints
    """
    # Import BIA routers (FastAPI surface)
    from bia_backend.routers import (
        billing_analytics_router,
        workflow_management_router,
        plugin_management_router,
        focus_data_router,
        health_check_router,
        storage_management_router,
        budget_tracking_router
    )

    # Create the base FastAPI app with ABI configuration
    app = abi_app.create_app()

    # Include all ABI routers
    app.include_router(billing_analytics_router)
    app.include_router(workflow_management_router)
    app.include_router(plugin_management_router)
    app.include_router(focus_data_router)
    app.include_router(health_check_router)
    app.include_router(storage_management_router)
    app.include_router(budget_tracking_router)

    # Root endpoint - API overview
    @app.get("/")
    async def root():
        """Root endpoint with API information and status"""
        return {
            "name": "Azure Billing Intelligence API",
            "version": "1.0.0",
            "description": "FOCUS-compliant billing analytics and workflow orchestration",
            "endpoints": {
                "health": "/api/v1/health",
                "focus_data": "/api/v1/focus",
                "billing_analytics": "/api/v1/billing/analytics",
                "workflows": "/api/v1/workflows",
                "plugins": "/api/v1/plugins",
                "storage": "/api/v1/storage",
                "moose_ingest": "/ingest/*",
                "moose_consumption": "/consumption/*"
            },
            "database_api_base": "http://localhost:4200/consumption",
            "notes": [
                "All database-backed APIs are served via Moose consumption on port 4200."
            ],
            "docs": "/docs",
            "redoc": "/redoc"
        }

    # API capabilities and information
    @app.get("/api/v1/info")
    async def api_info():
        """Get detailed API capabilities and infrastructure information"""
        return {
            "api_version": "v1",
            "focus_specification": "1.0",
            "supported_providers": ["azure", "aws", "gcp"],
            "supported_data_sources": ["azure_ea_api", "s3_csv", "custom_plugins"],
            "capabilities": {
                "billing_analytics": True,
                "workflow_orchestration": True,
                "plugin_marketplace": True,
                "focus_compliance": True,
                "real_time_processing": True,
                "moose_integration": True
            },
            "infrastructure": {
                "database": "ClickHouse",
                "workflow_engine": "Temporal",
                "cache": "Redis",
                "storage": "MinIO/S3",
                "messaging": "RedPanda"
            }
        }

    logger.info("ABI FastAPI application created successfully")
    return app


# Create the complete FastAPI app instance with all ABI routers
# This is imported by app.main to create the complete application
abi_fastapi_app = create_abi_fastapi_app()
# Backwards-compatible alias matching the new package name
bia_fastapi_app = abi_fastapi_app
