"""
Storage Management FastAPI Router

FastAPI router for MinIO/S3 configuration and management endpoints.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from bia_backend.app import get_clickhouse_client
from bia_backend.services.storage_management import (
    S3ConfigurationRequest, S3ConfigurationResponse, configure_s3_storage,
    S3ConnectionTest, S3ConnectionTestResponse, test_s3_connection,
    S3BucketListQuery, S3BucketListResponse, list_s3_buckets,
    S3ObjectListQuery, S3ObjectListResponse, list_s3_objects
)

logger = logging.getLogger(__name__)

storage_management_router = APIRouter(
    prefix="/api/v1/storage",
    tags=["Storage Management"],
    responses={404: {"description": "Not found"}},
)


@storage_management_router.post("/s3/configure", response_model=S3ConfigurationResponse)
async def configure_s3_storage_endpoint(
    request: S3ConfigurationRequest,
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    Configure S3/MinIO storage connection.
    
    - **configuration**: S3/MinIO configuration parameters
    - **test_connection**: Whether to test the connection after configuration
    """
    try:
        result = await configure_s3_storage(clickhouse_client, request)
        return result
        
    except Exception as e:
        logger.error(f"Error configuring S3 storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure S3 storage: {str(e)}"
        )


@storage_management_router.post("/s3/test", response_model=S3ConnectionTestResponse)
async def test_s3_connection_endpoint(
    request: S3ConnectionTest,
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    Test S3/MinIO connection and permissions.
    
    - **configuration**: S3/MinIO configuration to test
    """
    try:
        result = await test_s3_connection(clickhouse_client, request)
        return result
        
    except Exception as e:
        logger.error(f"Error testing S3 connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test S3 connection: {str(e)}"
        )


@storage_management_router.post("/s3/buckets", response_model=S3BucketListResponse)
async def list_s3_buckets_endpoint(
    query: S3BucketListQuery,
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    List S3/MinIO buckets.
    
    - **configuration_name**: Optional configuration name to use
    """
    try:
        result = await list_s3_buckets(clickhouse_client, query)
        return result
        
    except Exception as e:
        logger.error(f"Error listing S3 buckets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list S3 buckets: {str(e)}"
        )


@storage_management_router.post("/s3/objects", response_model=S3ObjectListResponse)
async def list_s3_objects_endpoint(
    query: S3ObjectListQuery,
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    List objects in S3/MinIO bucket.
    
    - **configuration_name**: Configuration name to use
    - **bucket_name**: Optional bucket name (uses default from config if not specified)
    - **prefix**: Optional prefix filter for objects
    - **max_keys**: Maximum number of objects to return (1-1000)
    """
    try:
        result = await list_s3_objects(clickhouse_client, query)
        return result
        
    except Exception as e:
        logger.error(f"Error listing S3 objects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list S3 objects: {str(e)}"
        )


@storage_management_router.get("/minio/console")
async def get_minio_console_info():
    """
    Get MinIO console access information.
    """
    return {
        "console_url": "http://localhost:9501",
        "api_url": "http://localhost:9500",
        "status": "available",
        "default_credentials": {
            "username": "minioadmin",
            "password": "minioadmin"
        },
        "note": "Default credentials should be changed in production"
    }


@storage_management_router.get("/configurations")
async def list_storage_configurations(
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    List all configured storage connections.
    """
    try:
        # In a real implementation, this would query the database
        # for stored storage configurations
        
        mock_configurations = [
            {
                "id": "default_minio",
                "name": "Default MinIO",
                "type": "minio",
                "endpoint_url": "http://localhost:9500",
                "bucket_name": "bia-data",
                "status": "active",
                "created_at": "2024-10-19T12:00:00Z",
                "last_tested": "2024-10-19T12:30:00Z"
            },
            {
                "id": "aws_s3_prod",
                "name": "AWS S3 Production",
                "type": "s3",
                "endpoint_url": None,
                "bucket_name": "bia-production-data",
                "status": "configured",
                "created_at": "2024-10-18T10:00:00Z",
                "last_tested": None
            }
        ]
        
        return {
            "configurations": mock_configurations,
            "total_count": len(mock_configurations)
        }
        
    except Exception as e:
        logger.error(f"Error listing storage configurations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list storage configurations: {str(e)}"
        )
