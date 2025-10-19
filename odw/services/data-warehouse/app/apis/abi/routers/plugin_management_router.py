"""
Plugin Management FastAPI Router

FastAPI router for plugin management endpoints with plugin registry
integration and data source connector management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
import logging

from app.abi_app import get_plugin_manager, get_clickhouse_client
from app.azure_billing.plugins.manager.plugin_manager import PluginManager
from app.apis.abi.plugin_management import (
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