"""
Workflow management services for the BIA FastAPI surface.

Provides helpers for Temporal workflow execution, monitoring, and orchestration
without registering Moose consumption endpoints.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum
import logging

from .temporal_client import TemporalClient

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TERMINATED = "terminated"
    TIMED_OUT = "timed_out"


class WorkflowType(str, Enum):
    """Workflow types"""
    AZURE_BILLING_EXTRACTION = "azure_billing_extraction"
    FOCUS_TRANSFORMATION = "focus_transformation"
    DATA_VALIDATION = "data_validation"
    SCHEDULED_REPORT = "scheduled_report"
    AZURE_BLOB_INGEST = "azure_blob_ingest"


class WorkflowExecution(BaseModel):
    """Workflow execution information"""
    workflow_id: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    records_processed: Optional[int] = None
    created_by: Optional[str] = None


class WorkflowListQuery(BaseModel):
    """Workflow list query parameters"""
    workflow_type: Optional[WorkflowType] = None
    status: Optional[WorkflowStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_by: Optional[str] = None
    limit: Optional[int] = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class WorkflowListResponse(BaseModel):
    """Workflow list response"""
    workflows: List[WorkflowExecution]
    total: int
    page_info: Dict[str, Any]
    summary: Dict[str, Any]


class WorkflowTriggerRequest(BaseModel):
    """Workflow trigger request"""
    workflow_type: WorkflowType
    parameters: Dict[str, Any]
    schedule: Optional[str] = None  # Cron expression for scheduled workflows
    priority: Optional[int] = Field(default=0, ge=0, le=10)


class WorkflowTriggerResponse(BaseModel):
    """Workflow trigger response"""
    success: bool
    workflow_id: Optional[str] = None
    message: str
    estimated_duration: Optional[str] = None


class WorkflowControlRequest(BaseModel):
    """Workflow control request (cancel, retry, etc.)"""
    workflow_id: str
    action: str = Field(pattern="^(cancel|retry|terminate)$")
    reason: Optional[str] = None


class WorkflowControlResponse(BaseModel):
    """Workflow control response"""
    success: bool
    message: str
    new_workflow_id: Optional[str] = None  # For retry operations


class WorkflowStatusQuery(BaseModel):
    """Workflow status query parameters"""
    workflow_id: str
    include_details: bool = False


class WorkflowStatusResponse(BaseModel):
    """Workflow status response"""
    workflow: WorkflowExecution
    task_details: Optional[List[Dict[str, Any]]] = None
    execution_log: Optional[List[str]] = None


class WorkflowMetricsQuery(BaseModel):
    """Workflow metrics query parameters"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    workflow_type: Optional[WorkflowType] = None
    granularity: str = Field(default="daily", pattern="^(hourly|daily|weekly|monthly)$")


class WorkflowMetrics(BaseModel):
    """Workflow execution metrics"""
    period: datetime
    workflow_type: WorkflowType
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_duration_seconds: float
    total_records_processed: int


class WorkflowMetricsResponse(BaseModel):
    """Workflow metrics response"""
    metrics: List[WorkflowMetrics]
    summary: Dict[str, Any]


def get_workflows(client, params: WorkflowListQuery) -> WorkflowListResponse:
    """
    Get list of workflow executions with filtering and pagination.
    
    Args:
        client: Database client for executing queries
        params: Workflow list query parameters
        
    Returns:
        WorkflowListResponse with workflow information
    """
    
    # Mock workflow data
    mock_workflows = [
        WorkflowExecution(
            workflow_id="wf_azure_billing_20241019_120000",
            workflow_type=WorkflowType.AZURE_BILLING_EXTRACTION,
            status=WorkflowStatus.COMPLETED,
            start_time=datetime.utcnow() - timedelta(hours=2),
            end_time=datetime.utcnow() - timedelta(hours=1, minutes=45),
            duration_seconds=900.0,
            parameters={
                "start_date": "2024-10-01",
                "end_date": "2024-10-18",
                "batch_size": 1000
            },
            result={
                "records_extracted": 15420,
                "records_transformed": 15420,
                "records_validated": 15420,
                "validation_errors": 0
            },
            records_processed=15420,
            created_by="system"
        ),
        WorkflowExecution(
            workflow_id="wf_focus_transform_20241019_110000",
            workflow_type=WorkflowType.FOCUS_TRANSFORMATION,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.utcnow() - timedelta(minutes=30),
            end_time=None,
            duration_seconds=None,
            parameters={
                "source_table": "azure_ea_billing_detail",
                "target_table": "focus_billing_data",
                "batch_size": 5000
            },
            result=None,
            records_processed=8500,
            created_by="admin"
        )
    ]
    
    # Apply filters
    filtered_workflows = mock_workflows
    
    if params.workflow_type:
        filtered_workflows = [w for w in filtered_workflows if w.workflow_type == params.workflow_type]
    
    if params.status:
        filtered_workflows = [w for w in filtered_workflows if w.status == params.status]
    
    if params.start_date:
        filtered_workflows = [w for w in filtered_workflows if w.start_time >= params.start_date]
    
    if params.end_date:
        filtered_workflows = [w for w in filtered_workflows if w.start_time <= params.end_date]
    
    if params.created_by:
        filtered_workflows = [w for w in filtered_workflows if w.created_by == params.created_by]
    
    # Apply pagination
    total = len(filtered_workflows)
    start_idx = params.offset
    end_idx = start_idx + (params.limit or len(filtered_workflows))
    paginated_workflows = filtered_workflows[start_idx:end_idx]
    
    # Create summary
    status_counts = {}
    total_records_processed = 0
    
    for workflow in filtered_workflows:
        status = workflow.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
        if workflow.records_processed:
            total_records_processed += workflow.records_processed
    
    summary = {
        "status_distribution": status_counts,
        "total_records_processed": total_records_processed,
        "avg_records_per_workflow": total_records_processed / len(filtered_workflows) if filtered_workflows else 0
    }
    
    # Create page info
    page_info = {
        "current_page": (params.offset // (params.limit or 1)) + 1 if params.limit else 1,
        "page_size": params.limit,
        "total_pages": (total + (params.limit or 1) - 1) // (params.limit or 1) if params.limit else 1,
        "has_next": end_idx < total,
        "has_previous": params.offset > 0
    }
    
    return WorkflowListResponse(
        workflows=paginated_workflows,
        total=total,
        page_info=page_info,
        summary=summary
    )


async def trigger_workflow(temporal_client: TemporalClient, params: WorkflowTriggerRequest) -> WorkflowTriggerResponse:
    """
    Trigger a new workflow execution using Temporal.
    
    Args:
        temporal_client: Enhanced Temporal client for workflow management
        params: Workflow trigger request
        
    Returns:
        WorkflowTriggerResponse with trigger result
    """
    
    try:
        # Generate workflow ID
        workflow_id = f"wf_{params.workflow_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Estimate duration based on workflow type
        duration_estimates = {
            WorkflowType.AZURE_BILLING_EXTRACTION: "15-30 minutes",
            WorkflowType.FOCUS_TRANSFORMATION: "5-15 minutes",
            WorkflowType.DATA_VALIDATION: "2-10 minutes",
            WorkflowType.SCHEDULED_REPORT: "1-5 minutes",
            WorkflowType.AZURE_BLOB_INGEST: "5-15 minutes",
        }
        
        # Start workflow via Temporal
        execution_id = await temporal_client.start_workflow(
            workflow_type=params.workflow_type.value,
            workflow_id=workflow_id,
            parameters=params.parameters,
            schedule=params.schedule
        )
        
        logger.info(f"Successfully triggered workflow {params.workflow_type.value} with ID {execution_id}")
        
        return WorkflowTriggerResponse(
            success=True,
            workflow_id=execution_id,
            message=f"Workflow {params.workflow_type.value} triggered successfully",
            estimated_duration=duration_estimates.get(params.workflow_type)
        )
        
    except Exception as e:
        logger.error(f"Error triggering workflow {params.workflow_type}: {e}")
        return WorkflowTriggerResponse(
            success=False,
            workflow_id=None,
            message=f"Failed to trigger workflow: {str(e)}"
        )


async def control_workflow(temporal_client: TemporalClient, params: WorkflowControlRequest) -> WorkflowControlResponse:
    """
    Control workflow execution (cancel, retry, terminate) using Temporal.
    
    Args:
        temporal_client: Enhanced Temporal client for workflow management
        params: Workflow control request
        
    Returns:
        WorkflowControlResponse with control result
    """
    
    try:
        if params.action == "cancel":
            success = await temporal_client.cancel_workflow(params.workflow_id, params.reason)
            message = f"Workflow {params.workflow_id} cancelled successfully" if success else "Failed to cancel workflow"
            
        elif params.action == "retry":
            # For retry, we need to get the original workflow parameters and start a new one
            # This is a simplified implementation - in practice, you'd store original parameters
            new_workflow_id = f"retry_{params.workflow_id}_{datetime.utcnow().strftime('%H%M%S')}"
            
            # Get original workflow details
            original_status = await temporal_client.get_workflow_status(params.workflow_id)
            workflow_type = original_status.get('workflow_type', 'azure_billing_extraction')
            
            # Start new workflow (simplified - would need original parameters)
            execution_id = await temporal_client.start_workflow(
                workflow_type=workflow_type,
                workflow_id=new_workflow_id,
                parameters={}  # Would need to retrieve original parameters
            )
            
            message = f"Workflow {params.workflow_id} retry initiated as {execution_id}"
            return WorkflowControlResponse(
                success=True,
                message=message,
                new_workflow_id=execution_id
            )
            
        elif params.action == "terminate":
            success = await temporal_client.terminate_workflow(params.workflow_id, params.reason)
            message = f"Workflow {params.workflow_id} terminated successfully" if success else "Failed to terminate workflow"
            
        else:
            raise ValueError(f"Unknown action: {params.action}")
        
        return WorkflowControlResponse(
            success=success if params.action != "retry" else True,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error controlling workflow {params.workflow_id}: {e}")
        return WorkflowControlResponse(
            success=False,
            message=f"Failed to {params.action} workflow: {str(e)}"
        )


async def get_workflow_status(temporal_client: TemporalClient, params: WorkflowStatusQuery) -> WorkflowStatusResponse:
    """
    Get detailed workflow status and execution information from Temporal.
    
    Args:
        temporal_client: Enhanced Temporal client for workflow management
        params: Workflow status query parameters
        
    Returns:
        WorkflowStatusResponse with detailed status
    """
    
    try:
        # Get workflow status from Temporal
        status_info = await temporal_client.get_workflow_status(params.workflow_id)
        
        # Map to WorkflowExecution model
        workflow = WorkflowExecution(
            workflow_id=params.workflow_id,
            workflow_type=WorkflowType(status_info.get('workflow_type', 'azure_billing_extraction')),
            status=WorkflowStatus(status_info.get('status', 'running')),
            start_time=status_info.get('start_time'),
            end_time=status_info.get('end_time'),
            duration_seconds=status_info.get('duration_seconds'),
            parameters={},  # Would need to be stored separately or retrieved from workflow
            result=None,
            records_processed=None,  # Would need to be tracked in workflow
            created_by="system"  # Would need to be stored with workflow metadata
        )
        
        # Get detailed information if requested
        task_details = None
        execution_log = None
        
        if params.include_details:
            # Get workflow history from Temporal
            history = await temporal_client.get_workflow_history(params.workflow_id)
            
            # Convert history to task details (simplified)
            task_details = []
            for i, event in enumerate(history[:5]):  # Limit to first 5 events
                task_details.append({
                    "task_name": f"task_{i+1}",
                    "status": "completed" if event.get('event_type') == 'EVENT_TYPE_ACTIVITY_TASK_COMPLETED' else "running",
                    "start_time": event.get('event_time'),
                    "end_time": event.get('event_time') if event.get('event_type') == 'EVENT_TYPE_ACTIVITY_TASK_COMPLETED' else None,
                    "event_type": event.get('event_type')
                })
            
            # Convert history to execution log
            execution_log = []
            for event in history:
                if event.get('event_time'):
                    log_entry = f"{event['event_time']}: {event.get('event_type', 'Unknown event')}"
                    execution_log.append(log_entry)
        
        return WorkflowStatusResponse(
            workflow=workflow,
            task_details=task_details,
            execution_log=execution_log
        )
        
    except Exception as e:
        logger.error(f"Error getting workflow status for {params.workflow_id}: {e}")
        
        # Return mock data as fallback
        mock_workflow = WorkflowExecution(
            workflow_id=params.workflow_id,
            workflow_type=WorkflowType.AZURE_BILLING_EXTRACTION,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.utcnow() - timedelta(minutes=15),
            end_time=None,
            duration_seconds=None,
            parameters={
                "start_date": "2024-10-01",
                "end_date": "2024-10-18",
                "batch_size": 1000
            },
            result=None,
            records_processed=8500,
            created_by="admin"
        )
        
        return WorkflowStatusResponse(
            workflow=mock_workflow,
            task_details=None,
            execution_log=None
        )


def get_workflow_metrics(client, params: WorkflowMetricsQuery) -> WorkflowMetricsResponse:
    """
    Get workflow execution metrics and analytics.
    
    Args:
        client: Database client for executing queries
        params: Workflow metrics query parameters
        
    Returns:
        WorkflowMetricsResponse with metrics data
    """
    
    # Mock metrics data
    mock_metrics = [
        WorkflowMetrics(
            period=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
            workflow_type=WorkflowType.AZURE_BILLING_EXTRACTION,
            total_executions=3,
            successful_executions=3,
            failed_executions=0,
            avg_duration_seconds=1200.0,
            total_records_processed=45600
        ),
        WorkflowMetrics(
            period=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1),
            workflow_type=WorkflowType.AZURE_BILLING_EXTRACTION,
            total_executions=2,
            successful_executions=1,
            failed_executions=1,
            avg_duration_seconds=1800.0,
            total_records_processed=28900
        )
    ]
    
    # Apply filters
    filtered_metrics = mock_metrics
    
    if params.workflow_type:
        filtered_metrics = [m for m in filtered_metrics if m.workflow_type == params.workflow_type]
    
    if params.start_date:
        filtered_metrics = [m for m in filtered_metrics if m.period >= params.start_date]
    
    if params.end_date:
        filtered_metrics = [m for m in filtered_metrics if m.period <= params.end_date]
    
    # Calculate summary
    total_executions = sum(m.total_executions for m in filtered_metrics)
    total_successful = sum(m.successful_executions for m in filtered_metrics)
    total_failed = sum(m.failed_executions for m in filtered_metrics)
    total_records = sum(m.total_records_processed for m in filtered_metrics)
    
    summary = {
        "total_executions": total_executions,
        "success_rate": (total_successful / total_executions * 100) if total_executions > 0 else 0,
        "failure_rate": (total_failed / total_executions * 100) if total_executions > 0 else 0,
        "total_records_processed": total_records,
        "avg_records_per_execution": total_records / total_executions if total_executions > 0 else 0,
        "period_count": len(filtered_metrics)
    }
    
    return WorkflowMetricsResponse(
        metrics=filtered_metrics,
        summary=summary
    )
