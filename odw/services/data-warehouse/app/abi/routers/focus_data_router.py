"""
FOCUS Data FastAPI Router

FastAPI router for FOCUS-compliant billing data endpoints with
ClickHouse integration and advanced filtering capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
import logging

from app.abi_app import get_clickhouse_client, get_redis_client
from app.abi.focus_data import (
    FOCUSDataQuery, FOCUSDataResponse, get_focus_billing_data,
    FOCUSAggregationQuery, FOCUSAggregationResponse, get_focus_aggregation
)

logger = logging.getLogger(__name__)

focus_data_router = APIRouter(
    prefix="/api/v1/focus",
    tags=["FOCUS Data"],
    responses={404: {"description": "Not found"}},
)


@focus_data_router.post("/billing-data", response_model=FOCUSDataResponse)
async def get_focus_billing_data_endpoint(
    query: FOCUSDataQuery,
    clickhouse_client: Any = Depends(get_clickhouse_client),
    redis_client: Any = Depends(get_redis_client)
):
    """
    Retrieve FOCUS-compliant billing data with filtering and pagination.
    
    - **limit**: Maximum number of records to return (1-10000)
    - **offset**: Pagination offset
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    - **billing_account_ids**: Optional account ID filtering
    - **service_categories**: Optional service category filtering
    - **service_names**: Optional service name filtering
    - **resource_types**: Optional resource type filtering
    - **regions**: Optional region filtering
    - **min_cost**: Optional minimum cost filter
    - **max_cost**: Optional maximum cost filter
    - **providers**: Optional provider filtering
    - **sort_by**: Sort field (usage_date, billed_cost, created_at)
    - **sort_order**: Sort order (asc, desc)
    """
    try:
        # Check cache first
        cache_key = f"focus_billing_data:{hash(str(query.dict()))}"
        
        if redis_client:
            try:
                cached_result = await redis_client.get(cache_key)
                if cached_result:
                    logger.info("Returning cached FOCUS billing data")
                    return FOCUSDataResponse.parse_raw(cached_result)
            except Exception as e:
                logger.warning(f"Failed to check cache: {e}")
        
        # Execute query
        result = get_focus_billing_data(clickhouse_client, query)
        
        # Cache result for 5 minutes
        if redis_client:
            try:
                await redis_client.setex(cache_key, 300, result.json())
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving FOCUS billing data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve FOCUS billing data: {str(e)}"
        )


@focus_data_router.post("/aggregation", response_model=FOCUSAggregationResponse)
async def get_focus_aggregation_endpoint(
    query: FOCUSAggregationQuery,
    clickhouse_client: Any = Depends(get_clickhouse_client),
    redis_client: Any = Depends(get_redis_client)
):
    """
    Get aggregated FOCUS billing data with grouping and metrics.
    
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    - **group_by**: Grouping dimensions (service_category, service_name, region, etc.)
    - **metrics**: Aggregation metrics (total_cost, avg_cost, min_cost, max_cost, etc.)
    - **billing_account_ids**: Optional account ID filtering
    - **service_categories**: Optional service category filtering
    - **service_names**: Optional service name filtering
    - **resource_types**: Optional resource type filtering
    - **regions**: Optional region filtering
    - **providers**: Optional provider filtering
    - **limit**: Maximum number of results (1-1000)
    """
    try:
        # Check cache first
        cache_key = f"focus_aggregation:{hash(str(query.dict()))}"
        
        if redis_client:
            try:
                cached_result = await redis_client.get(cache_key)
                if cached_result:
                    logger.info("Returning cached FOCUS aggregation data")
                    return FOCUSAggregationResponse.parse_raw(cached_result)
            except Exception as e:
                logger.warning(f"Failed to check cache: {e}")
        
        # Execute query
        result = get_focus_aggregation(clickhouse_client, query)
        
        # Cache result for 10 minutes
        if redis_client:
            try:
                await redis_client.setex(cache_key, 600, result.json())
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving FOCUS aggregation data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve FOCUS aggregation data: {str(e)}"
        )
