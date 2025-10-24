"""
Azure NCEI Workflow API

FastAPI endpoints for managing Azure NCEI to FOCUS workflows.
Replaces S3 CSV API endpoints.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from .ncei_scheduler import NCEIWorkflowScheduler, create_ncei_scheduler
from temporalio.client import Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/azure-ncei", tags=["Azure NCEI"])


# Dependency injection functions (must be defined before use in decorators)
async def get_temporal_client() -> Client:
    """Get Temporal client instance"""
    # This would typically be injected from your application setup
    # For now, return None as placeholder
    return None


async def get_ncei_scheduler() -> NCEIWorkflowScheduler:
    """Get NCEI workflow scheduler instance"""
    client = await get_temporal_client()
    return create_ncei_scheduler(client)


class NCEIWorkflowRequest(BaseModel):
    """Request model for NCEI workflow execution"""
    start_date: str = Field(description="Start date (YYYY-MM-DD)")
    end_date: str = Field(description="End date (YYYY-MM-DD)")
    container_name: Optional[str] = Field(description="Override container name")
    secondary_container: Optional[str] = Field(description="Optional secondary container")
    path_prefix: Optional[str] = Field(description="Path prefix filter")
    batch_size: Optional[int] = Field(default=10, description="Processing batch size")


class NCEIWorkflowResponse(BaseModel):
    """Response model for NCEI workflow execution"""
    workflow_id: str
    status: str
    message: str
    started_at: str


@router.post("/workflows/start", response_model=NCEIWorkflowResponse)
async def start_ncei_workflow(
    request: NCEIWorkflowRequest,
    scheduler: NCEIWorkflowScheduler = Depends(get_ncei_scheduler)
) -> NCEIWorkflowResponse:
    """
    Start a manual NCEI workflow execution.
    
    Args:
        request: Workflow request parameters
        scheduler: NCEI workflow scheduler
        
    Returns:
        Workflow execution response
    """
    try:
        # Parse dates
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        
        # Validate date range
        if start_date >= end_date:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before end date"
            )
        
        if (end_date - start_date).days > 31:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 31 days"
            )
        
        # Prepare custom configuration
        custom_config = {}
        if request.container_name:
            custom_config["container_name"] = request.container_name
        if request.secondary_container:
            custom_config["secondary_container"] = request.secondary_container
        if request.path_prefix:
            custom_config["path_prefix"] = request.path_prefix
        if request.batch_size:
            custom_config["batch_size"] = request.batch_size
        
        # Start workflow
        workflow_id = await scheduler.schedule_manual_workflow(
            start_date=start_date,
            end_date=end_date,
            custom_config=custom_config if custom_config else None
        )
        
        return NCEIWorkflowResponse(
            workflow_id=workflow_id,
            status="started",
            message=f"NCEI workflow started for date range {request.start_date} to {request.end_date}",
            started_at=datetime.utcnow().isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error starting NCEI workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/daily", response_model=NCEIWorkflowResponse)
async def start_daily_ncei_workflow(
    date: Optional[str] = None,
    scheduler: NCEIWorkflowScheduler = Depends(get_ncei_scheduler)
) -> NCEIWorkflowResponse:
    """
    Start a daily NCEI workflow execution.
    
    Args:
        date: Optional date (YYYY-MM-DD), defaults to yesterday
        scheduler: NCEI workflow scheduler
        
    Returns:
        Workflow execution response
    """
    try:
        # Parse date or use yesterday
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            target_date = datetime.utcnow() - timedelta(days=1)
        
        # Start daily workflow
        workflow_id = await scheduler.schedule_daily_workflow(start_date=target_date)
        
        return NCEIWorkflowResponse(
            workflow_id=workflow_id,
            status="started",
            message=f"Daily NCEI workflow started for {target_date.strftime('%Y-%m-%d')}",
            started_at=datetime.utcnow().isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error starting daily NCEI workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """
    Get the status of an NCEI workflow.
    
    Args:
        workflow_id: Workflow identifier
        
    Returns:
        Workflow status information
    """
    try:
        # This would typically query Temporal for workflow status
        # For now, return a placeholder response
        return {
            "workflow_id": workflow_id,
            "status": "running",
            "message": "Workflow status check not implemented yet"
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


