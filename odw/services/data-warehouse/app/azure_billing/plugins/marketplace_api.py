"""
Plugin Marketplace API

FastAPI endpoints that bridge frontend plugin management 
with data warehouse plugin market.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/plugins", tags=["Plugin Marketplace"])


class PluginMetadataResponse(BaseModel):
    """Plugin metadata response model."""

    id: str
    name: str
    version: str
    description: str
    author: str
    category: str
    tags: List[str]
    iconUrl: Optional[str] = None
    documentationUrl: Optional[str] = None
    configSchema: Optional[Dict[str, Any]] = None
    isInstalled: bool
    isConfigured: bool
    isActive: bool
    downloadCount: Optional[int] = None
    rating: Optional[float] = None
    lastUpdated: str


class PluginConfigurationResponse(BaseModel):
    """Plugin configuration response model."""

    pluginName: str
    connectorName: str
    config: Dict[str, Any]
    isValid: bool
    lastTested: Optional[str] = None
    connectionStatus: str
    errorMessage: Optional[str] = None


def _build_azure_blob_metadata() -> PluginMetadataResponse:
    """Reusable metadata instance for the Azure Blob Storage connector."""

    return PluginMetadataResponse(
        id="azure-blob-storage",
        name="Azure Blob Storage",
        version="1.0.0",
        description="FOCUS-compliant data source for Azure Blob Storage parquet files",
        author="ABI Team",
        category="storage",
        tags=["azure", "blob", "parquet", "focus", "ncei"],
        iconUrl="/icons/azure-blob.png",
        documentationUrl="/docs/azure-blob-storage",
        configSchema={
            "type": "object",
            "properties": {
                "accountUrl": {"type": "string", "title": "Account URL"},
                "sasToken": {"type": "string", "title": "SAS Token", "format": "password"},
                "containerName": {"type": "string", "title": "Container Name"},
                "secondaryContainer": {"type": "string", "title": "Secondary Container"},
                "pathPrefix": {"type": "string", "title": "Path Prefix"},
            },
            "required": ["accountUrl", "sasToken", "containerName"],
        },
        isInstalled=False,
        isConfigured=False,
        isActive=False,
        downloadCount=150,
        rating=4.8,
        lastUpdated=datetime.utcnow().isoformat(),
    )


def _build_azure_ea_metadata() -> PluginMetadataResponse:
    """Reusable metadata instance for the Azure EA API connector."""

    return PluginMetadataResponse(
        id="azure-ea-api",
        name="Azure EA API",
        version="1.2.0",
        description="Direct integration with Azure Enterprise Agreement API",
        author="ABI Team",
        category="billing",
        tags=["azure", "ea", "api", "billing"],
        iconUrl="/icons/azure-ea.png",
        documentationUrl="/docs/azure-ea-api",
        configSchema={
            "type": "object",
            "properties": {
                "enrollmentNumber": {"type": "string", "title": "Enrollment Number"},
                "apiKey": {"type": "string", "title": "API Key", "format": "password"},
                "environment": {"type": "string", "enum": ["production", "sandbox"]},
            },
            "required": ["enrollmentNumber", "apiKey"],
        },
        isInstalled=True,
        isConfigured=True,
        isActive=True,
        downloadCount=89,
        rating=4.5,
        lastUpdated=datetime.utcnow().isoformat(),
    )


def get_azure_blob_plugin_metadata() -> PluginMetadataResponse:
    """Expose Azure Blob plugin metadata for internal callers (e.g., workflows)."""

    return _build_azure_blob_metadata()


@router.get("/marketplace", response_model=Dict[str, List[PluginMetadataResponse]])
async def get_marketplace_plugins() -> Dict[str, List[PluginMetadataResponse]]:
    """Get available plugins from the marketplace."""

    try:
        plugins = [
            _build_azure_blob_metadata(),
            _build_azure_ea_metadata(),
        ]
        return {"plugins": plugins}
    except Exception as exc:  # pragma: no cover - logging branch
        logger.error("Error getting marketplace plugins: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/installed", response_model=Dict[str, List[PluginMetadataResponse]])
async def get_installed_plugins() -> Dict[str, List[PluginMetadataResponse]]:
    """Get installed plugins."""

    try:
        return {"plugins": [_build_azure_ea_metadata()]}
    except Exception as exc:  # pragma: no cover - logging branch
        logger.error("Error getting installed plugins: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/configurations", response_model=Dict[str, List[PluginConfigurationResponse]])
async def get_plugin_configurations() -> Dict[str, List[PluginConfigurationResponse]]:
    """Get plugin configurations."""

    try:
        configurations = [
            PluginConfigurationResponse(
                pluginName="Azure EA API",
                connectorName="Production EA Connector",
                config={
                    "enrollmentNumber": "12345678",
                    "environment": "production",
                },
                isValid=True,
                lastTested=datetime.utcnow().isoformat(),
                connectionStatus="connected",
            )
        ]
        return {"configurations": configurations}
    except Exception as exc:  # pragma: no cover - logging branch
        logger.error("Error getting plugin configurations: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
