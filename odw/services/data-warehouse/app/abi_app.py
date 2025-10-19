"""
Azure Billing Intelligence FastAPI Application

Extended FastAPI application that integrates with Moose framework
for ABI-specific endpoints, dependency injection, and middleware.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from typing import Optional
import logging
import asyncio
from datetime import datetime

# ABI imports
from app.azure_billing.plugins.manager.plugin_manager import PluginManager
from app.azure_billing.plugins.registry.plugin_registry import PluginRegistry

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
    
    async def initialize_dependencies(self):
        """Initialize ABI system dependencies"""
        try:
            # Initialize plugin registry
            self.plugin_registry = PluginRegistry()
            await self.plugin_registry.initialize()
            
            # Initialize plugin manager
            self.plugin_manager = PluginManager(self.plugin_registry)
            
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
            
            logger.info("ABI dependencies cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
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
            allow_origins=["http://localhost:3000", "http://localhost:8080", "http://localhost:8081"],
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