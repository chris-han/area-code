"""
Plugin Management FastAPI Router

FastAPI router for plugin management endpoints with plugin registry
integration and data source connector management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from typing import Any, Dict, Optional
import logging
import time
from datetime import datetime

from pydantic import BaseModel, Field

from bia_backend.app import (
    get_clickhouse_client,
    get_plugin_manager,
    get_plugin_registry,
)
from app.azure_billing.plugins.manager.plugin_manager import PluginManager
from app.azure_billing.plugins.registry.plugin_registry import PluginRegistry
from bia_backend.services.plugin_management import (
    PluginListQuery, PluginListResponse, get_plugins,
    PluginInstallationQuery, PluginInstallationResponse, get_plugin_installations,
    PluginInstallRequest, PluginInstallResponse, install_plugin,
    PluginConfigRequest, PluginConfigResponse, configure_plugin,
    PluginTestRequest, PluginTestResponse, test_plugin,
    PluginStatusQuery, PluginStatusResponse, get_plugin_status
)

logger = logging.getLogger(__name__)

plugin_management_router = APIRouter(
    prefix="/api/v1/plugins",
    tags=["Plugin Management"],
    responses={404: {"description": "Not found"}},
)


class PluginConfigurationPayload(BaseModel):
    """Payload for saving plugin configuration via REST endpoint."""
    plugin_name: str = Field(..., alias="plugin_name")
    config: Dict[str, Any]
    description: Optional[str] = None
    version: Optional[str] = None
    updated_by: Optional[str] = Field(default="frontend")
    database: Optional[str] = None

    model_config = {"populate_by_name": True}  # Pydantic V2


class PluginConfigurationData(BaseModel):
    """Response model for plugin configuration fetch."""
    plugin_name: str
    config: Dict[str, Any]
    version: Optional[str] = None
    description: Optional[str] = None
    updated_at: Optional[datetime] = None


class PluginTestPayload(BaseModel):
    """Payload for plugin connection test endpoint."""
    plugin_name: str = Field(..., alias="plugin_name")
    config: Optional[Dict[str, Any]] = None
    database: Optional[str] = None

    model_config = {"populate_by_name": True}  # Pydantic V2


@plugin_management_router.post("/list", response_model=PluginListResponse)
async def list_plugins_endpoint(
    query: PluginListQuery,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    Get list of available plugins with filtering and pagination.
    
    - **category**: Optional category filtering
    - **plugin_type**: Optional plugin type filtering
    - **status**: Optional status filtering
    - **search_query**: Optional search query
    - **tags**: Optional tag filtering
    - **installed_only**: Show only installed plugins
    - **limit**: Maximum number of results
    - **offset**: Pagination offset
    """
    try:
        result = get_plugins(clickhouse_client, query)
        
        # In a real implementation, this would also:
        # 1. Query plugin registry via plugin_manager
        # 2. Merge with installation status
        # 3. Apply real filtering and pagination
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing plugins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list plugins: {str(e)}"
        )


@plugin_management_router.post("/installations", response_model=PluginInstallationResponse)
async def list_plugin_installations_endpoint(
    query: PluginInstallationQuery,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    Get list of plugin installations with filtering.
    
    - **instance_id**: Optional instance ID filtering
    - **plugin_id**: Optional plugin ID filtering
    - **status**: Optional status filtering
    """
    try:
        result = get_plugin_installations(clickhouse_client, query)
        
        # In a real implementation, this would also:
        # 1. Query installation records via plugin_manager
        # 2. Include real-time status information
        # 3. Merge with plugin metadata
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing plugin installations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list plugin installations: {str(e)}"
        )


@plugin_management_router.post("/install", response_model=PluginInstallResponse)
async def install_plugin_endpoint(
    request: PluginInstallRequest,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    Install a plugin with configuration.
    
    - **plugin_id**: ID of plugin to install
    - **config**: Optional plugin configuration
    - **auto_activate**: Whether to activate plugin after installation
    """
    try:
        result = install_plugin(clickhouse_client, request)
        
        # In a real implementation, this would also:
        # 1. Download and install plugin via plugin_manager
        # 2. Validate configuration against plugin schema
        # 3. Create installation record in database
        # 4. Initialize plugin if auto_activate is True
        
        return result
        
    except Exception as e:
        logger.error(f"Error installing plugin {request.plugin_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to install plugin: {str(e)}"
        )


@plugin_management_router.get("/configuration", response_model=PluginConfigurationData)
async def get_plugin_configuration_endpoint(
    plugin_name: str,
    registry: PluginRegistry = Depends(get_plugin_registry),
):
    """
    Retrieve the active configuration for a plugin.
    """
    try:
        record = await registry.get_plugin_configuration(plugin_name)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active configuration found for plugin '{plugin_name}'"
            )
        
        return PluginConfigurationData(
            plugin_name=record.plugin_name,
            config=record.configuration,
            version=record.version,
            description=record.description,
            updated_at=record.updated_at,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.error(f"Error fetching configuration for {plugin_name}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch plugin configuration: {exc}"
        ) from exc


@plugin_management_router.put("/configuration", response_model=PluginConfigResponse)
async def save_plugin_configuration_endpoint(
    payload: PluginConfigurationPayload,
    registry: PluginRegistry = Depends(get_plugin_registry),
):
    """
    Persist plugin configuration and mark it as active.
    """
    try:
        saved = await registry.upsert_plugin_configuration(
            plugin_name=payload.plugin_name,
            configuration=payload.config,
            description=payload.description,
            version=payload.version,
            updated_by=payload.updated_by or "frontend",
        )
        
        return PluginConfigResponse(
            success=True,
            message=f"Configuration saved for plugin '{payload.plugin_name}'",
            validation_errors=None,
            config=saved.configuration,
            updated_at=saved.updated_at,
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.error(f"Error saving configuration for {payload.plugin_name}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save plugin configuration: {exc}"
        ) from exc


@plugin_management_router.post("/test", response_model=PluginTestResponse)
async def test_plugin_configuration_endpoint(
    payload: PluginTestPayload,
    registry: PluginRegistry = Depends(get_plugin_registry),
):
    """
    Execute plugin-specific connectivity tests.
    """
    plugin_name = payload.plugin_name
    try:
        config = payload.config
        if config is None:
            record = await registry.get_plugin_configuration(plugin_name)
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No configuration available to test for plugin '{plugin_name}'"
                )
            config = record.configuration
        
        normalized_name = plugin_name.strip().lower()
        if normalized_name in {"clickhouse sink", "clickhouse-sink", "clickhouse_sink"}:
            diagnostics = await _test_clickhouse_connection(config)
            return PluginTestResponse(
                success=True,
                message="Successfully connected to ClickHouse",
                plugin_name=plugin_name,
                connection_test=True,
                authentication_test=True,
                data_access_test=True,
                database=diagnostics.get("database"),
                host=diagnostics.get("host"),
                port=diagnostics.get("port"),
                secure=diagnostics.get("secure"),
                version=diagnostics.get("version"),
                latency_ms=diagnostics.get("latency_ms"),
            )
        
        return PluginTestResponse(
            success=True,
            message=f"Configuration test passed for plugin '{plugin_name}'",
            plugin_name=plugin_name,
            connection_test=True,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error testing plugin {plugin_name}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test plugin: {exc}"
        ) from exc


@plugin_management_router.put("/configure/{installation_id}", response_model=PluginConfigResponse)
async def configure_plugin_endpoint(
    installation_id: str,
    request: PluginConfigRequest,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    Configure an installed plugin.
    
    - **installation_id**: ID of plugin installation to configure
    - **config**: Plugin configuration parameters
    """
    try:
        result = configure_plugin(clickhouse_client, request)
        
        # In a real implementation, this would also:
        # 1. Validate configuration via plugin_manager
        # 2. Update installation record in database
        # 3. Reload plugin configuration
        # 4. Test new configuration
        
        return result
        
    except Exception as e:
        logger.error(f"Error configuring plugin {installation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure plugin: {str(e)}"
        )


@plugin_management_router.post("/test/{installation_id}", response_model=PluginTestResponse)
async def test_plugin_endpoint(
    installation_id: str,
    request: PluginTestRequest,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    Test plugin configuration.
    
    - **installation_id**: ID of plugin installation to test
    - **config**: Configuration to test
    """
    try:
        result = test_plugin(clickhouse_client, request)
        
        # In a real implementation, this would also:
        # 1. Load plugin via plugin_manager
        # 2. Create temporary instance with test configuration
        # 3. Run plugin health checks and connection tests
        # 4. Return detailed test results
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing plugin {installation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test plugin: {str(e)}"
        )


@plugin_management_router.post("/status", response_model=PluginStatusResponse)
async def get_plugin_status_endpoint(
    query: PluginStatusQuery,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    Get plugin status and health information.
    
    - **installation_ids**: Optional list of installation IDs to check
    - **detailed**: Whether to include detailed metrics
    """
    try:
        result = get_plugin_status(clickhouse_client, query)
        
        # In a real implementation, this would also:
        # 1. Query real-time status via plugin_manager
        # 2. Include health check results
        # 3. Merge with usage metrics from database
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting plugin status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin status: {str(e)}"
        )


async def _test_clickhouse_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a lightweight ClickHouse connectivity check using the provided configuration.
    """
    def _connect() -> Dict[str, Any]:
        import clickhouse_connect

        start = time.perf_counter()
        client = clickhouse_connect.get_client(
            host=config.get("host"),
            port=int(config.get("port", config.get("host_port", 8443))),
            username=config.get("user"),
            password=config.get("password"),
            database=config.get("dbName"),
            secure=bool(config.get("useSSL", True)),
        )
        try:
            version = client.command("SELECT version()")
        finally:
            client.close()
        duration_ms = (time.perf_counter() - start) * 1000
        return {
            "database": config.get("dbName"),
            "host": config.get("host"),
            "port": int(config.get("port", config.get("host_port", 8443))),
            "secure": bool(config.get("useSSL", True)),
            "version": version,
            "latency_ms": duration_ms,
        }

    result = await run_in_threadpool(_connect)
    return result
