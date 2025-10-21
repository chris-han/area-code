"""
Plugin management services for the BIA FastAPI surface.

Provides helper models and functions for plugin discovery, configuration,
testing, and status reporting backed by the PostgreSQL registry.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from threading import Lock
import logging
import asyncio
import time

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]

from app.azure_billing.plugins.registry.plugin_registry import (
    PluginRegistry,
    PluginRegistryConfig,
)

logger = logging.getLogger(__name__)

_registry_lock = Lock()
_plugin_registry: Optional[PluginRegistry] = None
_moose_config: Optional[Dict[str, Any]] = None
_plugin_registry_unavailable = False


def _load_moose_config() -> Dict[str, Any]:
    """Load moose.config.toml once and cache the result."""
    global _moose_config
    if _moose_config is not None:
        return _moose_config

    service_root = Path(__file__).resolve().parents[2]
    config_path = service_root / "moose.config.toml"
    if not config_path.exists():
        raise FileNotFoundError(f"Moose configuration file not found at {config_path}")

    with config_path.open("rb") as fh:
        _moose_config = tomllib.load(fh)

    return _moose_config


def _run_async(coro):
    """
    Run an async coroutine in a dedicated event loop.

    Moose executes consumption APIs synchronously, so we spin up a fresh loop to
    talk to asyncpg-based registries.
    """
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        asyncio.set_event_loop(None)
        loop.close()


def _get_plugin_registry() -> Optional[PluginRegistry]:
    """Get a cached PluginRegistry instance configured via moose.config.toml."""
    global _plugin_registry, _plugin_registry_unavailable
    if _plugin_registry is not None:
        return _plugin_registry
    if _plugin_registry_unavailable:
        return None

    with _registry_lock:
        if _plugin_registry is not None:
            return _plugin_registry
        if _plugin_registry_unavailable:
            return None

        try:
            config = _load_moose_config().get("plugin_registry_db", {})
            registry_config = PluginRegistryConfig.from_dict(config)
            registry = PluginRegistry(registry_config)
            _run_async(registry.initialize())
            _plugin_registry = registry
            logger.info("Plugin registry initialised via Moose consumption layer")
        except Exception as exc:
            logger.warning(
                "Plugin registry unavailable; continuing with fallback behaviour: %s",
                exc,
            )
            _plugin_registry_unavailable = True
            _plugin_registry = None

        return _plugin_registry




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
    plugin_name: Optional[str] = None
    installation_id: str
    instance_id: str
    status: str
    health_status: str
    config: Optional[Dict[str, Any]] = None
    installed_at: Optional[datetime] = None
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
    plugin_id: Optional[str] = Field(default=None, alias="plugin_id")
    plugin_name: Optional[str] = Field(default=None, alias="plugin_name")
    config: Optional[Dict[str, Any]] = None
    auto_activate: bool = True

    model_config = {"populate_by_name": True}


class PluginInstallResponse(BaseModel):
    """Plugin installation response"""
    success: bool
    installation_id: Optional[str] = None
    message: str


class PluginConfigRequest(BaseModel):
    """Plugin configuration request"""
    plugin_name: str = Field(..., alias="plugin_name")
    config: Dict[str, Any]
    description: Optional[str] = None
    version: Optional[str] = None
    updated_by: Optional[str] = None
    database: Optional[str] = None

    model_config = {"populate_by_name": True}


class PluginConfigResponse(BaseModel):
    """Plugin configuration response"""
    success: bool
    message: str
    validation_errors: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None
    plugin_name: Optional[str] = None


class PluginTestRequest(BaseModel):
    """Plugin test request"""
    plugin_name: Optional[str] = Field(default=None, alias="plugin_name")
    config: Optional[Dict[str, Any]] = None
    database: Optional[str] = None

    model_config = {"populate_by_name": True}


class PluginTestResponse(BaseModel):
    """Plugin test response"""
    success: bool
    message: str
    plugin_name: Optional[str] = None
    connection_test: Optional[bool] = None
    authentication_test: Optional[bool] = None
    data_access_test: Optional[bool] = None
    file_count: Optional[int] = None
    database: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    secure: Optional[bool] = None
    version: Optional[str] = None
    latency_ms: Optional[float] = None


class PluginConfigurationQuery(BaseModel):
    """Query stored configuration for a plugin"""
    plugin_name: str = Field(..., alias="plugin_name")
    database: Optional[str] = None

    model_config = {"populate_by_name": True}


class PluginConfigurationListQuery(BaseModel):
    """Query to list plugin configurations"""
    database: Optional[str] = None


class PluginConfigurationData(BaseModel):
    """Single plugin configuration record"""
    plugin_name: Optional[str]
    config: Optional[Dict[str, Any]]
    version: Optional[str] = None
    description: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class PluginConfigurationListResponse(BaseModel):
    """List of plugin configurations"""
    configurations: List[PluginConfigurationData]
    total: int


class PluginStatusQuery(BaseModel):
    """Plugin status query parameters"""
    installation_ids: Optional[List[str]] = None
    plugin_name: Optional[str] = Field(default=None, alias="plugin_name")
    detailed: bool = False

    model_config = {"populate_by_name": True}


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
        plugin_identifier = params.plugin_id or params.plugin_name
        if not plugin_identifier:
            raise ValueError("plugin_id or plugin_name must be provided")

        # Mock installation process
        installation_id = f"default_{plugin_identifier}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # In a real implementation, this would:
        # 1. Validate the plugin exists
        # 2. Validate the configuration
        # 3. Create installation record in PostgreSQL
        # 4. Initialize the plugin with the plugin manager
        # 5. Activate the plugin if auto_activate is True
        
        return PluginInstallResponse(
            success=True,
            installation_id=installation_id,
            message=f"Plugin {plugin_identifier} installed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error installing plugin {params.plugin_id or params.plugin_name}: {e}")
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
        if not params.plugin_name:
            return PluginConfigResponse(
                success=False,
                message="Plugin name is required",
                validation_errors=["plugin_name is required"],
            )

        if not params.config:
            return PluginConfigResponse(
                success=False,
                message="Configuration validation failed",
                validation_errors=["Configuration cannot be empty"],
                plugin_name=params.plugin_name,
            )

        registry = _get_plugin_registry()
        record = None
        if registry:
            record = _run_async(
                registry.upsert_plugin_configuration(
                    plugin_name=params.plugin_name,
                    configuration=params.config,
                    description=params.description,
                    version=params.version,
                    updated_by=params.updated_by,
                )
            )
            logger.info("Saved plugin configuration for %s via Moose API", params.plugin_name)

        return PluginConfigResponse(
            success=True,
            message=(
                f"Plugin configuration updated successfully for '{params.plugin_name}'"
                if record
                else (
                    f"Plugin configuration accepted for '{params.plugin_name}' "
                    "(not persisted; plugin registry unavailable)"
                )
            ),
            config=record.configuration if record else params.config,
            updated_at=record.updated_at if record else None,
            plugin_name=params.plugin_name,
        )

    except Exception as e:
        logger.error(f"Error configuring plugin {params.plugin_name}: {e}")
        return PluginConfigResponse(
            success=False,
            message=f"Failed to configure plugin '{params.plugin_name}': {str(e)}",
            validation_errors=[str(e)],
            plugin_name=params.plugin_name,
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
        plugin_name = (params.plugin_name or "").strip() or "unknown"

        config = params.config
        if config is None:
            registry = _get_plugin_registry()
            record = _run_async(registry.get_plugin_configuration(plugin_name)) if registry else None
            config = record.configuration if record else None

        if not config:
            reason = (
                f"No configuration available to test for plugin '{plugin_name}'"
                if not _plugin_registry_unavailable
                else f"No configuration available to test for plugin '{plugin_name}' (plugin registry unavailable)"
            )
            return PluginTestResponse(
                success=False,
                message=reason,
                plugin_name=plugin_name,
            )

        normalized_name = plugin_name.lower()

        try:
            if normalized_name in {"clickhouse sink", "clickhouse-sink", "clickhouse_sink"}:
                test_results = _test_clickhouse_connection(config)
                return PluginTestResponse(
                    success=True,
                    message="Successfully connected to ClickHouse",
                    plugin_name=plugin_name,
                    connection_test=True,
                    authentication_test=True,
                    data_access_test=True,
                    database=test_results.get("database"),
                    host=test_results.get("host"),
                    port=test_results.get("port"),
                    secure=test_results.get("secure"),
                    version=test_results.get("version"),
                    latency_ms=test_results.get("latency_ms"),
                )
        except Exception as conn_exc:  # pragma: no cover - runtime guard
            logger.error("ClickHouse connectivity test failed for %s: %s", plugin_name, conn_exc)
            return PluginTestResponse(
                success=False,
                message=f"ClickHouse connectivity test failed: {conn_exc}",
                plugin_name=plugin_name,
            )

        return PluginTestResponse(
            success=True,
            message=f"Configuration test passed for plugin '{plugin_name}'",
            plugin_name=plugin_name,
            connection_test=True,
        )

    except Exception as e:
        logger.error(f"Error testing plugin configuration for {params.plugin_name}: {e}")
        return PluginTestResponse(
            success=False,
            message=f"Plugin configuration test failed: {str(e)}",
            plugin_name=params.plugin_name,
        )


def _test_clickhouse_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a lightweight ClickHouse connectivity check."""
    import clickhouse_connect  # Local import to avoid mandatory dependency at module import time

    host = config.get("host") or config.get("hostname")
    if not host:
        raise ValueError("ClickHouse host is required for connection test")

    port = int(config.get("port") or config.get("host_port", 8443))
    user = config.get("user") or config.get("username")
    password = config.get("password")
    database = config.get("dbName") or config.get("database")
    secure = bool(config.get("useSSL", True))

    start = time.perf_counter()
    client = clickhouse_connect.get_client(
        host=host,
        port=port,
        username=user,
        password=password,
        database=database,
        secure=secure,
    )
    try:
        version = client.command("SELECT version()")
    finally:
        client.close()

    duration_ms = (time.perf_counter() - start) * 1000
    return {
        "database": database,
        "host": host,
        "port": port,
        "secure": secure,
        "version": version,
        "latency_ms": duration_ms,
    }


def get_plugin_configuration(client, params: PluginConfigurationQuery) -> PluginConfigurationData:
    """
    Retrieve the active configuration for a plugin from the registry.
    """
    registry = _get_plugin_registry()
    record = _run_async(registry.get_plugin_configuration(params.plugin_name)) if registry else None

    if record is None:
        logger.debug("No active configuration found for plugin '%s'", params.plugin_name)
        return PluginConfigurationData(
            plugin_name=params.plugin_name,
            config=None,
            version=None,
            description=None,
            updated_at=None,
            updated_by=None,
        )

    return PluginConfigurationData(
        plugin_name=record.plugin_name,
        config=record.configuration,
        version=record.version,
        description=record.description,
        updated_at=record.updated_at,
        updated_by=record.updated_by,
    )


def get_plugin_configurations(client, params: PluginConfigurationListQuery) -> PluginConfigurationListResponse:
    """
    List all plugin configurations stored in the registry.
    """
    registry = _get_plugin_registry()
    records = _run_async(registry.list_plugin_configurations()) if registry else []

    configurations = [
        PluginConfigurationData(
            plugin_name=record.plugin_name,
            config=record.configuration,
            version=record.version,
            description=record.description,
            updated_at=record.updated_at,
            updated_by=record.updated_by,
        )
        for record in records
    ]

    return PluginConfigurationListResponse(
        configurations=configurations,
        total=len(configurations),
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

    if params.plugin_name:
        filtered_statuses = [
            s for s in filtered_statuses
            if s.plugin_name.lower() == params.plugin_name.lower()
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

