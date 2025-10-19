"""
Plugin Management API

Endpoints for plugin discovery, installation, configuration, and monitoring
integrated with the ABI plugin system.
"""

from moose_lib import ConsumptionApi, EgressConfig
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)


class PluginInfo(BaseModel):
    """Plugin information model"""
    id: str
    name: str
    display_name: str
    description: str
    version: str
    author: str
    category: str
    plugin_type: str
    tags: List[str]
    rating: float
    review_count: int
    download_count: int
    is_official: bool
    is_verified: bool
    status: str
    icon_url: Optional[str] = None
    documentation_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PluginInstallationInfo(BaseModel):
    """Plugin installation information"""
    id: str
    plugin_id: str
    installation_id: str
    instance_id: str
    status: str
    health_status: str
    config: Optional[Dict[str, Any]] = None
    installed_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int
    error_message: Optional[str] = None


class PluginListQuery(BaseModel):
    """Plugin list query parameters"""
    category: Optional[str] = None
    plugin_type: Optional[str] = None
    status: Optional[str] = None
    search_query: Optional[str] = None
    tags: Optional[List[str]] = None
    installed_only: bool = False
    limit: Optional[int] = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class PluginListResponse(BaseModel):
    """Plugin list response"""
    plugins: List[PluginInfo]
    total: int
    page_info: Dict[str, Any]


class PluginInstallationQuery(BaseModel):
    """Plugin installation query parameters"""
    instance_id: Optional[str] = None
    plugin_id: Optional[str] = None
    status: Optional[str] = None


class PluginInstallationResponse(BaseModel):
    """Plugin installation response"""
    installations: List[PluginInstallationInfo]
    total: int


class PluginInstallRequest(BaseModel):
    """Plugin installation request"""
    plugin_id: str
    config: Optional[Dict[str, Any]] = None
    auto_activate: bool = True


class PluginInstallResponse(BaseModel):
    """Plugin installation response"""
    success: bool
    installation_id: Optional[str] = None
    message: str


class PluginConfigRequest(BaseModel):
    """Plugin configuration request"""
    config: Dict[str, Any]


class PluginConfigResponse(BaseModel):
    """Plugin configuration response"""
    success: bool
    message: str
    validation_errors: Optional[List[str]] = None


class PluginTestRequest(BaseModel):
    """Plugin test request"""
    config: Dict[str, Any]


class PluginTestResponse(BaseModel):
    """Plugin test response"""
    success: bool
    message: str
    test_results: Optional[Dict[str, Any]] = None


class PluginStatusQuery(BaseModel):
    """Plugin status query parameters"""
    installation_ids: Optional[List[str]] = None
    detailed: bool = False


class PluginStatusInfo(BaseModel):
    """Plugin status information"""
    installation_id: str
    plugin_name: str
    status: str
    health_status: str
    last_health_check: Optional[datetime] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class PluginStatusResponse(BaseModel):
    """Plugin status response"""
    statuses: List[PluginStatusInfo]
    summary: Dict[str, Any]


def get_plugins(client, params: PluginListQuery) -> PluginListResponse:
    """
    Get list of available plugins with filtering and pagination.
    
    Args:
        client: Database client for executing queries
        params: Plugin list query parameters
        
    Returns:
        PluginListResponse with plugin information
    """
    
    # Note: This is a mock implementation since we don't have the plugin registry
    # integrated with ClickHouse. In a real implementation, this would query
    # the PostgreSQL plugin registry.
    
    # Mock plugin data
    mock_plugins = [
        PluginInfo(
            id="azure-ea-api",
            name="azure-ea-api",
            display_name="Azure Enterprise Agreement API",
            description="Azure Enterprise Agreement API connector for billing data extraction",
            version="1.0.0",
            author="ABI Team",
            category="data_source",
            plugin_type="data_source",
            tags=["azure", "billing", "enterprise", "ea"],
            rating=4.5,
            review_count=12,
            download_count=156,
            is_official=True,
            is_verified=True,
            status="active",
            icon_url="https://azure.microsoft.com/favicon.ico",
            documentation_url="https://docs.microsoft.com/en-us/rest/api/consumption/",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        PluginInfo(
            id="s3-minio-csv",
            name="s3-minio-csv",
            display_name="S3/MinIO CSV Data Source",
            description="S3/MinIO CSV data source plugin for billing data extraction",
            version="1.0.0",
            author="ABI Team",
            category="data_source",
            plugin_type="data_source",
            tags=["s3", "minio", "csv", "billing", "storage"],
            rating=4.2,
            review_count=8,
            download_count=89,
            is_official=True,
            is_verified=True,
            status="active",
            icon_url="https://aws.amazon.com/favicon.ico",
            documentation_url="https://boto3.amazonaws.com/v1/documentation/api/latest/index.html",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]
    
    # Apply filters
    filtered_plugins = mock_plugins
    
    if params.category:
        filtered_plugins = [p for p in filtered_plugins if p.category == params.category]
    
    if params.plugin_type:
        filtered_plugins = [p for p in filtered_plugins if p.plugin_type == params.plugin_type]
    
    if params.status:
        filtered_plugins = [p for p in filtered_plugins if p.status == params.status]
    
    if params.search_query:
        query = params.search_query.lower()
        filtered_plugins = [
            p for p in filtered_plugins 
            if query in p.name.lower() or 
               query in p.display_name.lower() or 
               query in p.description.lower()
        ]
    
    if params.tags:
        filtered_plugins = [
            p for p in filtered_plugins 
            if any(tag in p.tags for tag in params.tags)
        ]
    
    # Apply pagination
    total = len(filtered_plugins)
    start_idx = params.offset
    end_idx = start_idx + (params.limit or len(filtered_plugins))
    paginated_plugins = filtered_plugins[start_idx:end_idx]
    
    # Create page info
    page_info = {
        "current_page": (params.offset // (params.limit or 1)) + 1 if params.limit else 1,
        "page_size": params.limit,
        "total_pages": (total + (params.limit or 1) - 1) // (params.limit or 1) if params.limit else 1,
        "has_next": end_idx < total,
        "has_previous": params.offset > 0
    }
    
    return PluginListResponse(
        plugins=paginated_plugins,
        total=total,
        page_info=page_info
    )


def get_plugin_installations(client, params: PluginInstallationQuery) -> PluginInstallationResponse:
    """
    Get list of plugin installations with filtering.
    
    Args:
        client: Database client for executing queries
        params: Plugin installation query parameters
        
    Returns:
        PluginInstallationResponse with installation information
    """
    
    # Mock installation data
    mock_installations = [
        PluginInstallationInfo(
            id="inst-1",
            plugin_id="azure-ea-api",
            installation_id="default_azure-ea-api_20241019_120000",
            instance_id="default",
            status="active",
            health_status="healthy",
            config={
                "enrollment_number": "123456789",
                "api_key": "***",
                "timeout": 30
            },
            installed_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
            usage_count=45,
            error_message=None
        ),
        PluginInstallationInfo(
            id="inst-2",
            plugin_id="s3-minio-csv",
            installation_id="default_s3-minio-csv_20241019_120100",
            instance_id="default",
            status="installed",
            health_status="unknown",
            config={
                "bucket_name": "billing-data",
                "access_key_id": "minioadmin",
                "endpoint_url": "http://localhost:9500"
            },
            installed_at=datetime.utcnow(),
            last_used=None,
            usage_count=0,
            error_message=None
        )
    ]
    
    # Apply filters
    filtered_installations = mock_installations
    
    if params.instance_id:
        filtered_installations = [i for i in filtered_installations if i.instance_id == params.instance_id]
    
    if params.plugin_id:
        filtered_installations = [i for i in filtered_installations if i.plugin_id == params.plugin_id]
    
    if params.status:
        filtered_installations = [i for i in filtered_installations if i.status == params.status]
    
    return PluginInstallationResponse(
        installations=filtered_installations,
        total=len(filtered_installations)
    )


def install_plugin(client, params: PluginInstallRequest) -> PluginInstallResponse:
    """
    Install a plugin with configuration.
    
    Args:
        client: Database client for executing queries
        params: Plugin installation request
        
    Returns:
        PluginInstallResponse with installation result
    """
    
    try:
        # Mock installation process
        installation_id = f"default_{params.plugin_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # In a real implementation, this would:
        # 1. Validate the plugin exists
        # 2. Validate the configuration
        # 3. Create installation record in PostgreSQL
        # 4. Initialize the plugin with the plugin manager
        # 5. Activate the plugin if auto_activate is True
        
        return PluginInstallResponse(
            success=True,
            installation_id=installation_id,
            message=f"Plugin {params.plugin_id} installed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error installing plugin {params.plugin_id}: {e}")
        return PluginInstallResponse(
            success=False,
            installation_id=None,
            message=f"Failed to install plugin: {str(e)}"
        )


def configure_plugin(client, params: PluginConfigRequest) -> PluginConfigResponse:
    """
    Configure an installed plugin.
    
    Args:
        client: Database client for executing queries
        params: Plugin configuration request
        
    Returns:
        PluginConfigResponse with configuration result
    """
    
    try:
        # Mock configuration validation
        validation_errors = []
        
        # Basic validation
        if not params.config:
            validation_errors.append("Configuration cannot be empty")
        
        if validation_errors:
            return PluginConfigResponse(
                success=False,
                message="Configuration validation failed",
                validation_errors=validation_errors
            )
        
        # In a real implementation, this would:
        # 1. Validate configuration against plugin schema
        # 2. Update installation record in PostgreSQL
        # 3. Reload plugin configuration in plugin manager
        # 4. Test the new configuration
        
        return PluginConfigResponse(
            success=True,
            message="Plugin configuration updated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error configuring plugin: {e}")
        return PluginConfigResponse(
            success=False,
            message=f"Failed to configure plugin: {str(e)}"
        )


def test_plugin(client, params: PluginTestRequest) -> PluginTestResponse:
    """
    Test plugin configuration.
    
    Args:
        client: Database client for executing queries
        params: Plugin test request
        
    Returns:
        PluginTestResponse with test result
    """
    
    try:
        # Mock configuration test
        test_results = {
            "connection_test": True,
            "authentication_test": True,
            "data_access_test": True,
            "response_time_ms": 150
        }
        
        # In a real implementation, this would:
        # 1. Create temporary plugin instance with test configuration
        # 2. Run plugin health checks and connection tests
        # 3. Return detailed test results
        
        return PluginTestResponse(
            success=True,
            message="Plugin configuration test passed",
            test_results=test_results
        )
        
    except Exception as e:
        logger.error(f"Error testing plugin configuration: {e}")
        return PluginTestResponse(
            success=False,
            message=f"Plugin configuration test failed: {str(e)}"
        )


def get_plugin_status(client, params: PluginStatusQuery) -> PluginStatusResponse:
    """
    Get plugin status and health information.
    
    Args:
        client: Database client for executing queries
        params: Plugin status query parameters
        
    Returns:
        PluginStatusResponse with status information
    """
    
    # Mock status data
    mock_statuses = [
        PluginStatusInfo(
            installation_id="default_azure-ea-api_20241019_120000",
            plugin_name="Azure EA API",
            status="active",
            health_status="healthy",
            last_health_check=datetime.utcnow(),
            error_message=None,
            metrics={
                "execution_count": 45,
                "success_rate": 98.5,
                "avg_response_time_ms": 250,
                "last_execution": datetime.utcnow().isoformat()
            } if params.detailed else None
        ),
        PluginStatusInfo(
            installation_id="default_s3-minio-csv_20241019_120100",
            plugin_name="S3/MinIO CSV",
            status="installed",
            health_status="unknown",
            last_health_check=None,
            error_message=None,
            metrics={
                "execution_count": 0,
                "success_rate": 0.0,
                "avg_response_time_ms": 0,
                "last_execution": None
            } if params.detailed else None
        )
    ]
    
    # Apply filters
    filtered_statuses = mock_statuses
    
    if params.installation_ids:
        filtered_statuses = [
            s for s in filtered_statuses 
            if s.installation_id in params.installation_ids
        ]
    
    # Create summary
    total_plugins = len(filtered_statuses)
    active_plugins = len([s for s in filtered_statuses if s.status == "active"])
    healthy_plugins = len([s for s in filtered_statuses if s.health_status == "healthy"])
    
    summary = {
        "total_plugins": total_plugins,
        "active_plugins": active_plugins,
        "healthy_plugins": healthy_plugins,
        "health_percentage": (healthy_plugins / total_plugins * 100) if total_plugins > 0 else 0
    }
    
    return PluginStatusResponse(
        statuses=filtered_statuses,
        summary=summary
    )


# Create the consumption APIs
plugin_list_api = ConsumptionApi[PluginListQuery, PluginListResponse](
    "getPlugins",
    query_function=get_plugins,
    source="plugins",
    config=EgressConfig()
)

plugin_installations_api = ConsumptionApi[PluginInstallationQuery, PluginInstallationResponse](
    "getPluginInstallations",
    query_function=get_plugin_installations,
    source="plugin_installations",
    config=EgressConfig()
)

plugin_install_api = ConsumptionApi[PluginInstallRequest, PluginInstallResponse](
    "installPlugin",
    query_function=install_plugin,
    source="plugins",
    config=EgressConfig()
)

plugin_configure_api = ConsumptionApi[PluginConfigRequest, PluginConfigResponse](
    "configurePlugin",
    query_function=configure_plugin,
    source="plugin_installations",
    config=EgressConfig()
)

plugin_test_api = ConsumptionApi[PluginTestRequest, PluginTestResponse](
    "testPlugin",
    query_function=test_plugin,
    source="plugins",
    config=EgressConfig()
)

plugin_status_api = ConsumptionApi[PluginStatusQuery, PluginStatusResponse](
    "getPluginStatus",
    query_function=get_plugin_status,
    source="plugin_installations",
    config=EgressConfig()
)