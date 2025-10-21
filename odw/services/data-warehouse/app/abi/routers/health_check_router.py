"""
Health Check FastAPI Router

FastAPI router for system health monitoring and service status endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
import logging

from app.abi_app import get_clickhouse_client, get_temporal_client, get_redis_client
from app.abi.health_check import (
    HealthCheckQuery, HealthCheckResponse, get_health_status
)

logger = logging.getLogger(__name__)

health_check_router = APIRouter(
    prefix="/api/v1/health",
    tags=["Health Check"],
    responses={404: {"description": "Not found"}},
)


@health_check_router.get("/", response_model=HealthCheckResponse)
async def get_health_status_endpoint(
    include_services: str = None,
    detailed: bool = False,
    clickhouse_client: Any = Depends(get_clickhouse_client),
    temporal_client: Any = Depends(get_temporal_client),
    redis_client: Any = Depends(get_redis_client)
):
    """
    Get comprehensive system health status.
    
    - **include_services**: Comma-separated list of services to check
    - **detailed**: Whether to include detailed service checks
    """
    try:
        # Parse include_services parameter
        services_list = None
        if include_services:
            services_list = [s.strip() for s in include_services.split(',')]
        
        query = HealthCheckQuery(
            include_services=services_list,
            detailed=detailed
        )
        
        result = get_health_status(clickhouse_client, query)
        
        # In a real implementation, this would also:
        # 1. Check Temporal service health via temporal_client
        # 2. Check Redis health via redis_client
        # 3. Check other infrastructure services
        # 4. Include real-time metrics and status
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health status: {str(e)}"
        )


@health_check_router.post("/", response_model=HealthCheckResponse)
async def post_health_status_endpoint(
    query: HealthCheckQuery,
    clickhouse_client: Any = Depends(get_clickhouse_client),
    temporal_client: Any = Depends(get_temporal_client),
    redis_client: Any = Depends(get_redis_client)
):
    """
    Get comprehensive system health status with detailed query parameters.
    
    - **include_services**: Optional list of services to check
    - **detailed**: Whether to include detailed service checks
    """
    try:
        result = get_health_status(clickhouse_client, query)
        
        # In a real implementation, this would also:
        # 1. Check Temporal service health via temporal_client
        # 2. Check Redis health via redis_client
        # 3. Check other infrastructure services
        # 4. Include real-time metrics and status
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health status: {str(e)}"
        )


@health_check_router.get("/ping")
async def ping_endpoint():
    """
    Simple ping endpoint for basic health checking.
    """
    return {"status": "ok", "message": "ABI system is running"}


@health_check_router.get("/ready")
async def readiness_endpoint(
    clickhouse_client: Any = Depends(get_clickhouse_client),
    temporal_client: Any = Depends(get_temporal_client),
    redis_client: Any = Depends(get_redis_client)
):
    """
    Readiness probe endpoint for Kubernetes deployments.
    """
    try:
        # Check critical dependencies
        services_ready = {
            "clickhouse": False,
            "temporal": False,
            "redis": False
        }
        
        # Check ClickHouse
        try:
            clickhouse_client.query.execute("SELECT 1")
            services_ready["clickhouse"] = True
        except Exception as e:
            logger.warning(f"ClickHouse not ready: {e}")
        
        # Check Temporal (simplified check)
        if temporal_client:
            services_ready["temporal"] = True
        
        # Check Redis
        try:
            await redis_client.ping()
            services_ready["redis"] = True
        except Exception as e:
            logger.warning(f"Redis not ready: {e}")
        
        # System is ready if all critical services are available
        all_ready = all(services_ready.values())
        
        if all_ready:
            return {
                "status": "ready",
                "services": services_ready
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "not_ready",
                    "services": services_ready
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking readiness: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed: {str(e)}"
        )


@health_check_router.get("/live")
async def liveness_endpoint():
    """
    Liveness probe endpoint for Kubernetes deployments.
    """
    return {"status": "alive", "message": "ABI system is alive"}
