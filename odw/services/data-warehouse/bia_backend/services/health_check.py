"""
Health-check service helpers for the BIA FastAPI surface.

Provides utilities for system health monitoring and service status reporting.
"""

from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class ServiceStatus(BaseModel):
    """Service status model"""
    name: str
    status: str  # healthy, unhealthy, unknown
    url: Optional[str] = None
    response_time_ms: Optional[float] = None
    last_check: datetime
    error_message: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    services: List[ServiceStatus]
    summary: Dict[str, Any]


class HealthCheckQuery(BaseModel):
    """Health check query parameters"""
    include_services: Optional[List[str]] = None
    detailed: bool = False


def get_health_status(client, params: HealthCheckQuery) -> HealthCheckResponse:
    """
    Get comprehensive system health status.
    
    Args:
        client: Database client for executing queries
        params: Health check parameters
        
    Returns:
        HealthCheckResponse with system status
    """
    
    services = []
    timestamp = datetime.utcnow()
    
    # Define services to check
    service_configs = {
        "clickhouse": {
            "name": "ClickHouse",
            "url": "http://localhost:18123",
            "check_query": "SELECT 1"
        },
        "temporal": {
            "name": "Temporal",
            "url": "http://localhost:7233",
            "check_query": None
        },
        "redis": {
            "name": "Redis",
            "url": "redis://localhost:6379",
            "check_query": None
        },
        "minio": {
            "name": "MinIO",
            "url": "http://localhost:9500",
            "check_query": None
        },
        "redpanda": {
            "name": "RedPanda",
            "url": "http://localhost:19092",
            "check_query": None
        }
    }
    
    # Filter services if specified
    if params.include_services:
        service_configs = {
            k: v for k, v in service_configs.items() 
            if k in params.include_services
        }
    
    # Check ClickHouse (primary database)
    clickhouse_status = _check_clickhouse_health(client)
    services.append(clickhouse_status)
    
    # Check other services if detailed check requested
    if params.detailed:
        for service_key, config in service_configs.items():
            if service_key != "clickhouse":  # Already checked
                status = _check_service_health(config)
                services.append(status)
    
    # Calculate overall status
    healthy_count = sum(1 for s in services if s.status == "healthy")
    total_count = len(services)
    
    if healthy_count == total_count:
        overall_status = "healthy"
    elif healthy_count > total_count / 2:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    # Create summary
    summary = {
        "total_services": total_count,
        "healthy_services": healthy_count,
        "unhealthy_services": total_count - healthy_count,
        "health_percentage": (healthy_count / total_count * 100) if total_count > 0 else 0
    }
    
    return HealthCheckResponse(
        status=overall_status,
        timestamp=timestamp,
        services=services,
        summary=summary
    )


def _check_clickhouse_health(client) -> ServiceStatus:
    """Check ClickHouse database health"""
    start_time = datetime.utcnow()
    
    try:
        # Execute simple health check query
        result = client.query.execute("SELECT 1 as health_check")
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        if result and len(result) > 0:
            return ServiceStatus(
                name="ClickHouse",
                status="healthy",
                url="http://localhost:18123",
                response_time_ms=response_time,
                last_check=datetime.utcnow()
            )
        else:
            return ServiceStatus(
                name="ClickHouse",
                status="unhealthy",
                url="http://localhost:18123",
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error_message="Query returned no results"
            )
            
    except Exception as e:
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return ServiceStatus(
            name="ClickHouse",
            status="unhealthy",
            url="http://localhost:18123",
            response_time_ms=response_time,
            last_check=datetime.utcnow(),
            error_message=str(e)
        )


def _check_service_health(config: Dict[str, Any]) -> ServiceStatus:
    """Check generic service health"""
    start_time = datetime.utcnow()
    
    try:
        # For now, return unknown status for other services
        # In a real implementation, you would make actual health check requests
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return ServiceStatus(
            name=config["name"],
            status="unknown",
            url=config["url"],
            response_time_ms=response_time,
            last_check=datetime.utcnow(),
            error_message="Health check not implemented"
        )
        
    except Exception as e:
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return ServiceStatus(
            name=config["name"],
            status="unhealthy",
            url=config["url"],
            response_time_ms=response_time,
            last_check=datetime.utcnow(),
            error_message=str(e)
        )

