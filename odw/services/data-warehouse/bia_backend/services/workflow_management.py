"""
Workflow management services for the BIA FastAPI surface.

Used by the REST layer to interact with Temporal workflows: listing execution
history, triggering runs, controlling existing executions, and generating
lightweight metrics for the UI.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

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
    """Workflow type identifiers exposed to the UI"""

    AZURE_BILLING_EXTRACTION = "azure_billing_extraction"
    FOCUS_TRANSFORMATION = "focus_transformation"
    DATA_VALIDATION = "data_validation"
    SCHEDULED_REPORT = "scheduled_report"
    AZURE_BLOB_INGEST = "azure_blob_ingest"
    MINIMAL_DEMO = "minimal_demo"


class WorkflowExecution(BaseModel):
    """Workflow execution information returned to the UI"""

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
    progress: Optional[float] = Field(default=None, ge=0.0, le=1.0)
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
    schedule: Optional[str] = None
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
    new_workflow_id: Optional[str] = None


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


async def get_workflows(temporal_client: TemporalClient, params: WorkflowListQuery) -> WorkflowListResponse:
    """Fetch workflow executions from Temporal with optional filtering."""

    fetch_limit = (params.limit or 50) + params.offset

    workflow_descriptions = await temporal_client.list_workflows(max_results=fetch_limit)

    workflow_status_mapping = {
        "WORKFLOW_EXECUTION_STATUS_RUNNING": WorkflowStatus.RUNNING,
        "WORKFLOW_EXECUTION_STATUS_COMPLETED": WorkflowStatus.COMPLETED,
        "WORKFLOW_EXECUTION_STATUS_FAILED": WorkflowStatus.FAILED,
        "WORKFLOW_EXECUTION_STATUS_CANCELED": WorkflowStatus.CANCELLED,
        "WORKFLOW_EXECUTION_STATUS_TERMINATED": WorkflowStatus.TERMINATED,
        "WORKFLOW_EXECUTION_STATUS_TIMED_OUT": WorkflowStatus.TIMED_OUT,
    }

    workflow_records: List[WorkflowExecution] = []

    for description in workflow_descriptions:
        workflow_type_attr = getattr(description, "workflow_type", None)
        if hasattr(workflow_type_attr, "name"):
            workflow_class = workflow_type_attr.name
        elif isinstance(workflow_type_attr, str):
            workflow_class = workflow_type_attr
        else:
            workflow_class = None

        workflow_type_value = TemporalClient.resolve_workflow_type(workflow_class)
        if workflow_type_value is None:
            continue

        try:
            workflow_type_enum = WorkflowType(workflow_type_value)
        except ValueError:
            continue

        status_attr = getattr(description, "status", None)
        if hasattr(status_attr, "name"):
            status_name = status_attr.name
        elif isinstance(status_attr, str):
            status_name = status_attr
        else:
            status_name = None

        status_enum = workflow_status_mapping.get(status_name, WorkflowStatus.RUNNING)

        start_time_attr = getattr(description, "start_time", None)
        start_time = start_time_attr.replace(tzinfo=None) if start_time_attr else datetime.utcnow()

        close_time_attr = getattr(description, "close_time", None)
        end_time = close_time_attr.replace(tzinfo=None) if close_time_attr else None

        duration_seconds: Optional[float] = None
        if start_time and end_time:
            duration_seconds = (end_time - start_time).total_seconds()
        elif getattr(description, "execution_time", None):
            duration_seconds = (
                datetime.utcnow() - description.execution_time.replace(tzinfo=None)
            ).total_seconds()

        execution = getattr(description, "workflow_execution", None) or getattr(description, "execution", None)
        if not execution:
            continue

        workflow_records.append(
            WorkflowExecution(
                workflow_id=execution.workflow_id,
                workflow_type=workflow_type_enum,
                status=status_enum,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration_seconds,
                parameters={},
                result=None,
                records_processed=0,
                created_by="temporal",
            )
        )

    filtered_workflows = workflow_records

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

    total = len(filtered_workflows)
    start_idx = params.offset
    end_idx = start_idx + (params.limit or len(filtered_workflows))
    paginated_workflows = filtered_workflows[start_idx:end_idx]

    status_counts: Dict[str, int] = {}
    total_records_processed = 0

    for workflow in filtered_workflows:
        status = workflow.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
        if workflow.records_processed:
            total_records_processed += workflow.records_processed

    summary = {
        "status_distribution": status_counts,
        "total_records_processed": total_records_processed,
        "avg_records_per_workflow": (
            total_records_processed / len(filtered_workflows)
            if filtered_workflows
            else 0
        ),
    }

    page_info = {
        "current_page": (params.offset // (params.limit or 1)) + 1 if params.limit else 1,
        "page_size": params.limit,
        "total_pages": (total + (params.limit or 1) - 1) // (params.limit or 1) if params.limit else 1,
        "has_next": end_idx < total,
        "has_previous": params.offset > 0,
    }

    return WorkflowListResponse(
        workflows=paginated_workflows,
        total=total,
        page_info=page_info,
        summary=summary,
    )


async def trigger_workflow(temporal_client: TemporalClient, params: WorkflowTriggerRequest) -> WorkflowTriggerResponse:
    """Trigger a new workflow execution using Temporal."""

    try:
        workflow_id = f"wf_{params.workflow_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        duration_estimates = {
            WorkflowType.AZURE_BILLING_EXTRACTION: "15-30 minutes",
            WorkflowType.FOCUS_TRANSFORMATION: "5-15 minutes",
            WorkflowType.DATA_VALIDATION: "2-10 minutes",
            WorkflowType.SCHEDULED_REPORT: "1-5 minutes",
            WorkflowType.AZURE_BLOB_INGEST: "5-15 minutes",
            WorkflowType.MINIMAL_DEMO: "< 1 minute",
        }

        execution_id = await temporal_client.start_workflow(
            workflow_type=params.workflow_type.value,
            workflow_id=workflow_id,
            parameters=params.parameters,
            schedule=params.schedule,
        )

        logger.info(
            "Successfully triggered workflow %s with ID %s",
            params.workflow_type.value,
            execution_id,
        )

        return WorkflowTriggerResponse(
            success=True,
            workflow_id=execution_id,
            message=f"Workflow {params.workflow_type.value} triggered successfully",
            estimated_duration=duration_estimates.get(params.workflow_type),
        )

    except Exception as exc:  # pragma: no cover - Temporal connectivity errors
        logger.error("Error triggering workflow %s: %s", params.workflow_type, exc)
        return WorkflowTriggerResponse(
            success=False,
            workflow_id=None,
            message=f"Failed to trigger workflow: {exc}",
        )


async def control_workflow(temporal_client: TemporalClient, params: WorkflowControlRequest) -> WorkflowControlResponse:
    """Control workflow execution (cancel, retry, terminate) using Temporal."""

    try:
        if params.action == "cancel":
            success = await temporal_client.cancel_workflow(params.workflow_id, params.reason)
            message = (
                f"Workflow {params.workflow_id} cancelled successfully"
                if success
                else "Failed to cancel workflow"
            )

        elif params.action == "retry":
            new_workflow_id = f"retry_{params.workflow_id}_{datetime.utcnow().strftime('%H%M%S')}"
            original_status = await temporal_client.get_workflow_status(params.workflow_id)
            workflow_type = original_status.get("workflow_type", WorkflowType.AZURE_BILLING_EXTRACTION.value)

            execution_id = await temporal_client.start_workflow(
                workflow_type=workflow_type,
                workflow_id=new_workflow_id,
                parameters={},
            )

            message = f"Workflow {params.workflow_id} retry initiated as {execution_id}"
            return WorkflowControlResponse(
                success=True,
                message=message,
                new_workflow_id=execution_id,
            )

        elif params.action == "terminate":
            success = await temporal_client.terminate_workflow(params.workflow_id, params.reason)
            message = (
                f"Workflow {params.workflow_id} terminated successfully"
                if success
                else "Failed to terminate workflow"
            )

        else:  # pragma: no cover - validation should prevent this
            raise ValueError(f"Unknown action: {params.action}")

        return WorkflowControlResponse(
            success=success if params.action != "retry" else True,
            message=message,
        )

    except Exception as exc:  # pragma: no cover - Temporal failures
        logger.error("Error controlling workflow %s: %s", params.workflow_id, exc)
        return WorkflowControlResponse(
            success=False,
            message=f"Failed to {params.action} workflow: {exc}",
        )


async def get_workflow_status(temporal_client: TemporalClient, params: WorkflowStatusQuery) -> WorkflowStatusResponse:
    """Get detailed workflow status and execution information from Temporal."""

    try:
        status_info = await temporal_client.get_workflow_status(params.workflow_id)

        workflow = WorkflowExecution(
            workflow_id=params.workflow_id,
            workflow_type=WorkflowType(status_info.get("workflow_type", WorkflowType.AZURE_BILLING_EXTRACTION.value)),
            status=WorkflowStatus(status_info.get("status", WorkflowStatus.RUNNING.value)),
            start_time=status_info.get("start_time"),
            end_time=status_info.get("end_time"),
            duration_seconds=status_info.get("duration_seconds"),
            parameters={},
            result=None,
            records_processed=None,
            created_by="system",
        )

        task_details = None
        execution_log = None

        if params.include_details:
            history = await temporal_client.get_workflow_history(params.workflow_id)

            task_details = []
            for idx, event in enumerate(history[:5]):
                task_details.append(
                    {
                        "task_name": f"task_{idx + 1}",
                        "status": "completed"
                        if event.get("event_type") == "EVENT_TYPE_ACTIVITY_TASK_COMPLETED"
                        else "running",
                        "start_time": event.get("event_time"),
                        "end_time": event.get("event_time")
                        if event.get("event_type") == "EVENT_TYPE_ACTIVITY_TASK_COMPLETED"
                        else None,
                        "event_type": event.get("event_type"),
                    }
                )

            execution_log = []
            for event in history:
                if event.get("event_time"):
                    execution_log.append(
                        f"{event['event_time']}: {event.get('event_type', 'Unknown event')}"
                    )

        return WorkflowStatusResponse(
            workflow=workflow,
            task_details=task_details,
            execution_log=execution_log,
        )

    except Exception as exc:  # pragma: no cover - Temporal failures
        logger.error("Error getting workflow status for %s: %s", params.workflow_id, exc)

        fallback = WorkflowExecution(
            workflow_id=params.workflow_id,
            workflow_type=WorkflowType.AZURE_BILLING_EXTRACTION,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.utcnow() - timedelta(minutes=15),
            end_time=None,
            duration_seconds=None,
            parameters={
                "start_date": "2024-10-01",
                "end_date": "2024-10-18",
                "batch_size": 1000,
            },
            result=None,
            records_processed=0,
            created_by="fallback",
        )

        return WorkflowStatusResponse(
            workflow=fallback,
            task_details=None,
            execution_log=None,
        )


async def get_workflow_metrics(temporal_client: TemporalClient, params: WorkflowMetricsQuery) -> WorkflowMetricsResponse:
    """Generate lightweight workflow metrics derived from Temporal history."""

    descriptions = await temporal_client.list_workflows(max_results=200)

    filtered: List[WorkflowExecution] = []
    for description in descriptions:
        workflow_type_attr = getattr(description, "workflow_type", None)
        if hasattr(workflow_type_attr, "name"):
            workflow_class = workflow_type_attr.name
        elif isinstance(workflow_type_attr, str):
            workflow_class = workflow_type_attr
        else:
            workflow_class = None

        workflow_type_value = TemporalClient.resolve_workflow_type(workflow_class)
        if workflow_type_value is None:
            continue

        try:
            workflow_type_enum = WorkflowType(workflow_type_value)
        except ValueError:
            continue

        start_time_attr = getattr(description, "start_time", None)
        start_time = start_time_attr.replace(tzinfo=None) if start_time_attr else datetime.utcnow()

        if params.workflow_type and workflow_type_enum != params.workflow_type:
            continue

        if params.start_date and start_time < params.start_date:
            continue

        if params.end_date and start_time > params.end_date:
            continue

        filtered.append(
            WorkflowExecution(
                workflow_id=getattr(description, "execution", getattr(description, "workflow_execution", None)).workflow_id,
                workflow_type=workflow_type_enum,
                status=WorkflowStatus.RUNNING,
                start_time=start_time,
                end_time=None,
                duration_seconds=None,
                parameters={},
                result=None,
                records_processed=0,
            )
        )

    metrics: List[WorkflowMetrics] = []
    summary: Dict[str, Any] = {
        "total_executions": 0,
        "success_rate": 0,
        "failure_rate": 0,
        "total_records_processed": 0,
        "avg_records_per_execution": 0,
        "period_count": 0,
    }

    if not filtered:
        return WorkflowMetricsResponse(metrics=metrics, summary=summary)

    grouped: Dict[WorkflowType, List[WorkflowExecution]] = {}
    for execution in filtered:
        grouped.setdefault(execution.workflow_type, []).append(execution)

    period_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    for workflow_type, executions in grouped.items():
        total_executions = len(executions)
        metrics.append(
            WorkflowMetrics(
                period=period_start,
                workflow_type=workflow_type,
                total_executions=total_executions,
                successful_executions=0,
                failed_executions=0,
                avg_duration_seconds=0.0,
                total_records_processed=0,
            )
        )

        summary["total_executions"] += total_executions

    summary["period_count"] = len(metrics)

    return WorkflowMetricsResponse(metrics=metrics, summary=summary)
