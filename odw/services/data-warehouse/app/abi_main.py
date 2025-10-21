"""
ABI FastAPI Main Application

Main FastAPI application that extends Moose with ABI-specific endpoints,
dependency injection, and middleware integration.
"""

from fastapi import FastAPI
import logging

from app.abi_app import abi_app
from app.abi.routers import (
    billing_analytics_router,
    workflow_management_router,
    plugin_management_router,
    focus_data_router,
    health_check_router,
    storage_management_router,
    budget_tracking_router
)

logger = logging.getLogger(__name__)


def create_abi_fastapi_app() -> FastAPI:
    """
    Create and configure the ABI FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    
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
    
    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information"""
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
                "storage": "/api/v1/storage"
            },
            "docs": "/docs",
            "redoc": "/redoc"
        }
    
    # Add API info endpoint
    @app.get("/api/v1/info")
    async def api_info():
        """API information and capabilities"""
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
                "real_time_processing": True
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


# Create the FastAPI app instance
fastapi_app = create_abi_fastapi_app()

# Export for use by ASGI servers
abi_fastapi_app = fastapi_app
