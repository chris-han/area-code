"""
Plugin Marketplace API

FastAPI endpoints that bridge frontend plugin management 
with data warehouse plugin market.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/plugins", tags=["Plugin Marketplace"])


class PluginMetadataResponse(BaseModel):
    """Plugin metadata response model"""
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
    """Plugin configuration response model"""
    pluginName: str
    connectorName: str
    config: Dict[str, Any]
    isValid: bool
    lastTested: Optional[str] = None
    connectionStatus: str
    errorMessage: Optional[str] = None@route
r.get("/marketplace", response_model=Dict[str, List[PluginMetadataResponse]])
async def get_marketplace_plugins() -> Dict[str, List[PluginMetadataResponse]]:
    """
    Get available plugins from the marketplace.
    
    Returns:
        Dictionary containing list of available plugins
    """
    try:
        # Mock marketplace plugins for now
        plugins = [
            PluginMetadataResponse(
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
                        "pathPrefix": {"type": "string", "title": "Path Prefix"}
                    },
                    "required": ["accountUrl", "sasToken", "containerName"]
                },
                isInstalled=False,
                isConfigured=False,
                isActive=False,
                downloadCount=150,
                rating=4.8,
                lastUpdated=datetime.utcnow().isoformat()
            ),
            PluginMetadataResponse(
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
                        "environment": {"type": "string", "enum": ["production", "sandbox"]}
                    },
                    "required": ["enrollmentNumber", "apiKey"]
                },
                isInstalled=True,
                isConfigured=True,
                isActive=True,
                downloadCount=89,
                rating=4.5,
                lastUpdated=datetime.utcnow().isoformat()
            )
        ]
        
        return {"plugins": plugins}
        
    except Exception as e:
        logger.error(f"Error getting marketplace plugins: {e}")
        raise HTTPException(status_code=500, detail=str(e))@
router.get("/installed", response_model=Dict[str, List[PluginMetadataResponse]])
async def get_installed_plugins() -> Dict[str, List[PluginMetadataResponse]]:
    """
    Get installed plugins.
    
    Returns:
        Dictionary containing list of installed plugins
    """
    try:
        # Mock installed plugins for now
        plugins = [
            PluginMetadataResponse(
                id="azure-ea-api",
                name="Azure EA API",
                version="1.2.0",
                description="Direct integration with Azure Enterprise Agreement API",
                author="ABI Team",
                category="billing",
                tags=["azure", "ea", "api", "billing"],
                iconUrl="/icons/azure-ea.png",
                documentationUrl="/docs/azure-ea-api",
                configSchema={},
                isInstalled=True,
                isConfigured=True,
                isActive=True,
                lastUpdated=datetime.utcnow().isoformat()
            )
        ]
        
        return {"plugins": plugins}
        
    except Exception as e:
        logger.error(f"Error getting installed plugins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configurations", response_model=Dict[str, List[PluginConfigurationResponse]])
async def get_plugin_configurations() -> Dict[str, List[PluginConfigurationResponse]]:
    """
    Get plugin configurations.
    
    Returns:
        Dictionary containing list of plugin configurations
    """
    try:
        # Mock configurations for now
        configurations = [
            PluginConfigurationResponse(
                pluginName="Azure EA API",
                connectorName="Production EA Connector",
                config={
                    "enrollmentNumber": "12345678",
                    "environment": "production"
                },
                isValid=True,
                lastTested=datetime.utcnow().isoformat(),
                connectionStatus="connected"
            )
        ]
        
        return {"configurations": configurations}
        
    except Exception as e:
        logger.error(f"Error getting plugin configurations: {e}")
        raise HTTPException(status_code=500, detail=str(e))