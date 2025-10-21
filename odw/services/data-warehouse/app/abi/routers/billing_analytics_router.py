"""
Billing Analytics FastAPI Router

FastAPI router for billing analytics endpoints with ClickHouse integration
and FOCUS-compliant data processing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
import logging

from app.abi_app import get_clickhouse_client, get_redis_client
from app.abi.billing_analytics import (
    CostTrendQuery, CostTrendResponse, get_cost_trends,
    ResourceUtilizationQuery, ResourceUtilizationResponse, get_resource_utilization,
    CostOptimizationQuery, CostOptimizationResponse, get_cost_optimization_opportunities,
    ServiceAnalysisQuery, ServiceAnalysisResponse, get_service_analysis
)

logger = logging.getLogger(__name__)

billing_analytics_router = APIRouter(
    prefix="/api/v1/billing/analytics",
    tags=["Billing Analytics"],
    responses={404: {"description": "Not found"}},
)


@billing_analytics_router.post("/cost-trends", response_model=CostTrendResponse)
async def get_cost_trends_endpoint(
    query: CostTrendQuery,
    clickhouse_client: Any = Depends(get_clickhouse_client),
    redis_client: Any = Depends(get_redis_client)
):
    """
    Analyze cost trends over time with configurable granularity.
    
    - **start_date**: Start date for analysis
    - **end_date**: End date for analysis  
    - **granularity**: Time granularity (daily, weekly, monthly)
    - **billing_account_ids**: Optional account filtering
    - **service_categories**: Optional service filtering
    - **regions**: Optional region filtering
    """
    try:
        # Check cache first
        cache_key = f"cost_trends:{hash(str(query.dict()))}"
        
        # Execute query
        result = await get_cost_trends(clickhouse_client, query)
        
        # Cache result for 5 minutes
        if redis_client:
            try:
                await redis_client.setex(cache_key, 300, result.json())
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in cost trends analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze cost trends: {str(e)}"
        )


@billing_analytics_router.post("/resource-utilization", response_model=ResourceUtilizationResponse)
async def get_resource_utilization_endpoint(
    query: ResourceUtilizationQuery,
    clickhouse_client: Any = Depends(get_clickhouse_client),
    redis_client: Any = Depends(get_redis_client)
):
    """
    Analyze resource utilization and efficiency metrics.
    
    - **start_date**: Start date for analysis
    - **end_date**: End date for analysis
    - **resource_types**: Optional resource type filtering
    - **service_categories**: Optional service filtering
    - **regions**: Optional region filtering
    - **min_cost_threshold**: Minimum cost threshold for inclusion
    - **limit**: Maximum number of results
    """
    try:
        # Check cache first
        cache_key = f"resource_utilization:{hash(str(query.dict()))}"
        
        # Execute query
        result = get_resource_utilization(clickhouse_client, query)
        
        # Cache result for 10 minutes
        if redis_client:
            try:
                await redis_client.setex(cache_key, 600, result.json())
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in resource utilization analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resource utilization: {str(e)}"
        )


@billing_analytics_router.post("/cost-optimization", response_model=CostOptimizationResponse)
async def get_cost_optimization_endpoint(
    query: CostOptimizationQuery,
    clickhouse_client: Any = Depends(get_clickhouse_client),
    redis_client: Any = Depends(get_redis_client)
):
    """
    Identify cost optimization opportunities and potential savings.
    
    - **start_date**: Start date for analysis
    - **end_date**: End date for analysis
    - **billing_account_ids**: Optional account filtering
    - **service_categories**: Optional service filtering
    - **min_savings_threshold**: Minimum savings threshold
    - **limit**: Maximum number of opportunities
    """
    try:
        # Check cache first
        cache_key = f"cost_optimization:{hash(str(query.dict()))}"
        
        # Execute query
        result = get_cost_optimization_opportunities(clickhouse_client, query)
        
        # Cache result for 15 minutes
        if redis_client:
            try:
                await redis_client.setex(cache_key, 900, result.json())
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in cost optimization analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze cost optimization: {str(e)}"
        )


@billing_analytics_router.post("/service-analysis", response_model=ServiceAnalysisResponse)
async def get_service_analysis_endpoint(
    query: ServiceAnalysisQuery,
    clickhouse_client: Any = Depends(get_clickhouse_client),
    redis_client: Any = Depends(get_redis_client)
):
    """
    Analyze service cost breakdown and trends.
    
    - **start_date**: Start date for analysis
    - **end_date**: End date for analysis
    - **billing_account_ids**: Optional account filtering
    - **top_n**: Number of top services to return
    - **include_trend**: Whether to include trend analysis
    """
    try:
        # Check cache first
        cache_key = f"service_analysis:{hash(str(query.dict()))}"
        
        # Execute query
        result = get_service_analysis(clickhouse_client, query)
        
        # Cache result for 10 minutes
        if redis_client:
            try:
                await redis_client.setex(cache_key, 600, result.json())
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in service analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze services: {str(e)}"
        )
