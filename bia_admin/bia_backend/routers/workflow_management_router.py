"""
Workflow Management FastAPI Router

FastAPI router for Temporal workflow management endpoints with
workflow orchestration and monitoring capabilities.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from bia_backend.services.temporal_client import TemporalClient
from bia_backend.services.workflow_management import (
    WorkflowListQuery, WorkflowListResponse, get_workflows,
    WorkflowTriggerRequest, WorkflowTriggerResponse, trigger_workflow,
    WorkflowControlRequest, WorkflowControlResponse, control_workflow,
    WorkflowStatusQuery, WorkflowStatusResponse, get_workflow_status,
    WorkflowMetricsQuery, WorkflowMetricsResponse, get_workflow_metrics,
)
from bia_backend.services.worker_management import get_worker_manager

logger = logging.getLogger(__name__)


def get_temporal_host():
    """Get Temporal host from moose.config.toml"""
    import os
    from pathlib import Path

    try:
        import tomli
    except ImportError:
        import tomllib as tomli

    # First check environment variable
    temporal_host = os.environ.get('TEMPORAL_HOST')
    if temporal_host:
        return temporal_host

    # Try to read from moose.config.toml
    try:
        repo_root = Path(__file__).resolve().parents[3]
        config_path = repo_root / "odw" / "services" / "data-warehouse" / "moose.config.toml"
        with open(config_path, "rb") as f:
            config = tomli.load(f)

        temporal_config = config.get("temporal_config", {})
        host = temporal_config.get("temporal_host", "localhost")
        port = temporal_config.get("temporal_port", 7233)

        return f"{host}:{port}"
    except Exception as e:
        # Re-raise exception if config file cannot be read
        raise RuntimeError(f"Failed to read Temporal host configuration from moose.config.toml: {str(e)}") from e


def create_temporal_client() -> TemporalClient:
    """Construct a Temporal client from configuration."""

    temporal_host = get_temporal_host()
    return TemporalClient(
        {
            "host": temporal_host,
            "namespace": "default",
            "task_queue": "bia-workflows",
        }
    )


workflow_management_router = APIRouter(
    prefix="/api/v1/workflows",
    tags=["Workflow Management"],
    responses={404: {"description": "Not found"}},
)


@workflow_management_router.post("/list", response_model=WorkflowListResponse)
async def list_workflows_endpoint(
    query: WorkflowListQuery,
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
        temporal_client_instance = create_temporal_client()
        try:
            result = await get_workflows(temporal_client_instance, query)
            return result
        finally:
            await temporal_client_instance.disconnect()

    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {str(e)}"
        )


@workflow_management_router.post("/trigger", response_model=WorkflowTriggerResponse)
async def trigger_workflow_endpoint(
    request: WorkflowTriggerRequest,
):
    """
    Trigger a new workflow execution.
    
    - **workflow_type**: Type of workflow to trigger
    - **parameters**: Workflow parameters
    - **schedule**: Optional cron schedule for recurring workflows
    - **priority**: Workflow priority (0-10)
    """
    try:
        temporal_client_instance = create_temporal_client()
        try:
            result = await trigger_workflow(temporal_client_instance, request)

            return result
        finally:
            await temporal_client_instance.disconnect()

    except Exception as e:
        logger.error(f"Error triggering workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger workflow: {str(e)}"
        )


@workflow_management_router.post("/control", response_model=WorkflowControlResponse)
async def control_workflow_endpoint(
    request: WorkflowControlRequest,
):
    """
    Control workflow execution (cancel, retry, terminate).
    
    - **workflow_id**: ID of workflow to control
    - **action**: Action to perform (cancel, retry, terminate)
    - **reason**: Optional reason for the action
    """
    try:
        temporal_client_instance = create_temporal_client()
        try:
            result = await control_workflow(temporal_client_instance, request)

            # In a real implementation, this would also:
            # 1. Execute control action via temporal_client
            # 2. Update workflow status in database
            # 3. Send notifications if configured

            return result
        finally:
            await temporal_client_instance.disconnect()

    except Exception as e:
        logger.error(f"Error controlling workflow {request.workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to control workflow: {str(e)}"
        )


@workflow_management_router.post("/status", response_model=WorkflowStatusResponse)
async def get_workflow_status_endpoint(
    query: WorkflowStatusQuery,
):
    """
    Get detailed workflow status and execution information.
    
    - **workflow_id**: ID of workflow to check
    - **include_details**: Whether to include task details and logs
    """
    try:
        temporal_client_instance = create_temporal_client()
        try:
            result = await get_workflow_status(temporal_client_instance, query)

            # In a real implementation, this would also:
            # 1. Query Temporal for real-time workflow status
            # 2. Merge with stored metadata from database
            # 3. Include execution history and task details

            return result
        finally:
            await temporal_client_instance.disconnect()

    except Exception as e:
        logger.error(f"Error getting workflow status for {query.workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow status: {str(e)}"
        )


@workflow_management_router.post("/metrics", response_model=WorkflowMetricsResponse)
async def get_workflow_metrics_endpoint(
    query: WorkflowMetricsQuery,
):
    """
    Get workflow execution metrics and analytics.
    
    - **start_date**: Optional start date for metrics
    - **end_date**: Optional end date for metrics
    - **workflow_type**: Optional workflow type filtering
    - **granularity**: Time granularity for metrics
    """
    try:
        temporal_client_instance = create_temporal_client()
        try:
            result = await get_workflow_metrics(temporal_client_instance, query)
            return result
        finally:
            await temporal_client_instance.disconnect()

    except Exception as e:
        logger.error(f"Error getting workflow metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow metrics: {str(e)}"
        )


@workflow_management_router.get("/worker/status")
async def get_worker_status():
    """
    Get current Temporal worker status.

    Returns information about the worker process including:
    - Whether it's running
    - Process ID
    - Script being used (run_worker_with_correct_host.py)
    - Current status
    """
    try:
        worker_manager = get_worker_manager()
        status_info = await worker_manager.get_worker_status()

        return {
            "success": True,
            "worker": status_info,
            "message": "Worker status retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Error getting worker status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get worker status: {str(e)}"
        )


@workflow_management_router.post("/worker/start")
async def start_worker():
    """
    Manually start the Temporal worker.

    Uses run_worker_with_correct_host.py as the default worker script.
    This endpoint is useful for manually ensuring a worker is running.
    """
    try:
        worker_manager = get_worker_manager()
        success = await worker_manager.ensure_worker_running()

        if success:
            return {
                "success": True,
                "message": "Worker started successfully using run_worker_with_correct_host.py"
            }
        else:
            return {
                "success": False,
                "message": "Failed to start worker"
            }

    except Exception as e:
        logger.error(f"Error starting worker: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start worker: {str(e)}"
        )


@workflow_management_router.post("/worker/restart")
async def restart_worker():
    """
    Restart the Temporal worker.

    Stops the current worker process and starts a new one using
    run_worker_with_correct_host.py.
    """
    try:
        worker_manager = get_worker_manager()
        success = await worker_manager.restart_worker()

        if success:
            return {
                "success": True,
                "message": "Worker restarted successfully using run_worker_with_correct_host.py"
            }
        else:
            return {
                "success": False,
                "message": "Failed to restart worker"
            }

    except Exception as e:
        logger.error(f"Error restarting worker: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart worker: {str(e)}"
        )
