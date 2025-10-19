"""
Workflow Management FastAPI Router

FastAPI router for Temporal workflow management endpoints with
workflow orchestration and monitoring capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
import logging

from app.abi_app import get_temporal_client, get_clickhouse_client
from app.apis.abi.temporal_client import TemporalClient
from app.apis.abi.workflow_management import (
    WorkflowListQuery, WorkflowListResponse, get_workflows,
    WorkflowTriggerRequest, WorkflowTriggerResponse, trigger_workflow,
    WorkflowControlRequest, WorkflowControlResponse, control_workflow,
    WorkflowStatusQuery, WorkflowStatusResponse, get_workflow_status,
    WorkflowMetricsQuery, WorkflowMetricsResponse, get_workflow_metrics
)

logger = logging.getLogger(__name__)

workflow_management_router = APIRouter(
    prefix="/api/v1/workflows",
    tags=["Workflow Management"],
    responses={404: {"description": "Not found"}},
)


@workflow_management_router.post("/list", response_model=WorkflowListResponse)
async def list_workflows_endpoint(
    query: WorkflowListQuery,
    temporal_client: Any = Depends(get_temporal_client),
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    Get list of workflow executions with filtering and pagination.
    
    - **workflow_type**: Optional workflow type filtering
    - **status**: Optional status filtering
    - **start_date**: Optional start date filtering
    - **end_date**: Optional end date filtering
    - **created_by**: Optional creator filtering
    - **limit**: Maximum number of results
    - **offset**: Pagination offset
    """
    try:
        result = get_workflows(clickhouse_client, query)
        return result
        
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {str(e)}"
        )


@workflow_management_router.post("/trigger", response_model=WorkflowTriggerResponse)
async def trigger_workflow_endpoint(
    request: WorkflowTriggerRequest,
    temporal_client: Any = Depends(get_temporal_client),
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    Trigger a new workflow execution.
    
    - **workflow_type**: Type of workflow to trigger
    - **parameters**: Workflow parameters
    - **schedule**: Optional cron schedule for recurring workflows
    - **priority**: Workflow priority (0-10)
    """
    try:
        # Create Temporal client instance
        temporal_client_instance = TemporalClient({
            'host': 'localhost:7233',
            'namespace': 'default',
            'task_queue': 'abi-workflows'
        })
        
        result = await trigger_workflow(temporal_client_instance, request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error triggering workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger workflow: {str(e)}"
        )


@workflow_management_router.post("/control", response_model=WorkflowControlResponse)
async def control_workflow_endpoint(
    request: WorkflowControlRequest,
    temporal_client: Any = Depends(get_temporal_client),
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    Control workflow execution (cancel, retry, terminate).
    
    - **workflow_id**: ID of workflow to control
    - **action**: Action to perform (cancel, retry, terminate)
    - **reason**: Optional reason for the action
    """
    try:
        result = control_workflow(clickhouse_client, request)
        
        # In a real implementation, this would also:
        # 1. Execute control action via temporal_client
        # 2. Update workflow status in database
        # 3. Send notifications if configured
        
        return result
        
    except Exception as e:
        logger.error(f"Error controlling workflow {request.workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to control workflow: {str(e)}"
        )


@workflow_management_router.post("/status", response_model=WorkflowStatusResponse)
async def get_workflow_status_endpoint(
    query: WorkflowStatusQuery,
    temporal_client: Any = Depends(get_temporal_client),
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    Get detailed workflow status and execution information.
    
    - **workflow_id**: ID of workflow to check
    - **include_details**: Whether to include task details and logs
    """
    try:
        result = get_workflow_status(clickhouse_client, query)
        
        # In a real implementation, this would also:
        # 1. Query Temporal for real-time workflow status
        # 2. Merge with stored metadata from database
        # 3. Include execution history and task details
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting workflow status for {query.workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow status: {str(e)}"
        )


@workflow_management_router.post("/metrics", response_model=WorkflowMetricsResponse)
async def get_workflow_metrics_endpoint(
    query: WorkflowMetricsQuery,
    temporal_client: Any = Depends(get_temporal_client),
    clickhouse_client: Any = Depends(get_clickhouse_client)
):
    """
    Get workflow execution metrics and analytics.
    
    - **start_date**: Optional start date for metrics
    - **end_date**: Optional end date for metrics
    - **workflow_type**: Optional workflow type filtering
    - **granularity**: Time granularity for metrics
    """
    try:
        result = get_workflow_metrics(clickhouse_client, query)
        return result
        
    except Exception as e:
        logger.error(f"Error getting workflow metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow metrics: {str(e)}"
        )