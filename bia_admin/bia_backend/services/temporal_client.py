"""
Temporal Client Integration

Enhanced Temporal client with workflow management, monitoring,
and Azure billing workflow orchestration capabilities.
"""

from temporalio import workflow
from temporalio.client import Client, WorkflowHandle
from temporalio.common import RetryPolicy
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import logging
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Temporal workflow status mapping"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TERMINATED = "terminated"
    TIMED_OUT = "timed_out"


class TemporalClient:
    """Enhanced Temporal client for bia workflow management"""

    WORKFLOW_CLASS_MAP = {
        "focus_billing_ingest": "FocusBillingTemporalWorkflow",
        "schema_migration": "SchemaMigrationWorkflow",
    }

    STATUS_MAP = {
        WorkflowStatus.RUNNING: "WORKFLOW_EXECUTION_STATUS_RUNNING",
        WorkflowStatus.COMPLETED: "WORKFLOW_EXECUTION_STATUS_COMPLETED",
        WorkflowStatus.FAILED: "WORKFLOW_EXECUTION_STATUS_FAILED",
        WorkflowStatus.CANCELLED: "WORKFLOW_EXECUTION_STATUS_CANCELED",
        WorkflowStatus.TERMINATED: "WORKFLOW_EXECUTION_STATUS_TERMINATED",
        WorkflowStatus.TIMED_OUT: "WORKFLOW_EXECUTION_STATUS_TIMED_OUT",
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._client: Optional[Client] = None
        self.namespace = config.get('namespace', 'default')
        self.task_queue = config.get('task_queue', 'bia-workflows')
        
    async def connect(self):
        """Connect to Temporal server"""
        try:
            temporal_host = self.config.get('host', 'localhost:7233')
            self._client = await Client.connect(temporal_host)
            logger.info(f"Connected to Temporal server at {temporal_host}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Temporal: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Temporal server"""
        if self._client:
            close_method = getattr(self._client, "close", None)
            if close_method:
                try:
                    result = close_method()
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as exc:  # pragma: no cover - defensive cleanup
                    logger.warning(f"Temporal client close failed: {exc}")
            self._client = None
            logger.info("Disconnected from Temporal server")
    
    async def start_workflow(
        self,
        workflow_type: str,
        workflow_id: str,
        parameters: Dict[str, Any],
        schedule: Optional[str] = None,
        retry_policy: Optional[RetryPolicy] = None
    ) -> str:
        """
        Start a new workflow execution.
        
        Args:
            workflow_type: Type of workflow to start
            workflow_id: Unique workflow identifier
            parameters: Workflow input parameters
            schedule: Optional cron schedule for recurring workflows
            retry_policy: Optional retry policy
            
        Returns:
            Workflow execution ID
        """
        if not self._client:
            await self.connect()
        
        try:
            # Map workflow types to actual workflow classes
            workflow_classes = {
                "azure_billing_extraction": "AzureBillingWorkflow",
                "focus_transformation": "FOCUSTransformationWorkflow",
                "data_validation": "DataValidationWorkflow",
                "scheduled_report": "ScheduledReportWorkflow",
                "azure_blob_ingest": "AzureBlobIngestWorkflow",
                "focus_billing_ingest": "FocusBillingTemporalWorkflow",
            }
            
            workflow_class = self.WORKFLOW_CLASS_MAP.get(workflow_type)
            if not workflow_class:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
            
            # Default retry policy
            if not retry_policy:
                retry_policy = RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(minutes=5),
                    maximum_attempts=3,
                    backoff_coefficient=2.0
                )
            
            # Start workflow
            # For schema_migration workflow, pass parameters as args list
            if workflow_type == "schema_migration":
                # SchemaMigrationWorkflow expects 3 positional args
                # Provide defaults if not specified
                from pathlib import Path
                repo_root = Path(__file__).resolve().parents[3]  # Go up to area-code root

                default_parquet = str(repo_root / "odw/services/data-warehouse/app/focus_billing/data/focus/20250701-20250731/202507220944/b1861aa3-c2fe-460d-9ff2-a6f28d0ef073/part_0_0001.snappy.parquet")
                default_spec = str(repo_root / "FOCUS_Spec/specification/datasets")

                workflow_args = [
                    parameters.get("source_parquet_path", default_parquet),
                    parameters.get("canonical_schema_path", default_spec),
                    parameters.get("current_version", "0_0")
                ]

                logger.info(f"Schema migration params: parquet={workflow_args[0]}, spec={workflow_args[1]}, version={workflow_args[2]}")

                handle = await self._client.start_workflow(
                    workflow_class,
                    args=workflow_args,
                    id=workflow_id,
                    task_queue=self.task_queue,
                    retry_policy=retry_policy,
                    execution_timeout=timedelta(hours=2),
                    run_timeout=timedelta(hours=1)
                )
            else:
                handle = await self._client.start_workflow(
                    workflow_class,
                    parameters,
                    id=workflow_id,
                    task_queue=self.task_queue,
                    retry_policy=retry_policy,
                    execution_timeout=timedelta(hours=2),
                    run_timeout=timedelta(hours=1)
                )
            
            logger.info(f"Started workflow {workflow_type} with ID {workflow_id}")
            return handle.id
            
        except Exception as e:
            logger.error(f"Failed to start workflow {workflow_type}: {e}")
            raise
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow execution status and details.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow status information
        """
        if not self._client:
            await self.connect()
        
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            
            # Get workflow description
            description = await handle.describe()
            
            # Map Temporal status to bia status
            status_mapping = {
                "WORKFLOW_EXECUTION_STATUS_RUNNING": WorkflowStatus.RUNNING,
                "WORKFLOW_EXECUTION_STATUS_COMPLETED": WorkflowStatus.COMPLETED,
                "WORKFLOW_EXECUTION_STATUS_FAILED": WorkflowStatus.FAILED,
                "WORKFLOW_EXECUTION_STATUS_CANCELED": WorkflowStatus.CANCELLED,
                "WORKFLOW_EXECUTION_STATUS_TERMINATED": WorkflowStatus.TERMINATED,
                "WORKFLOW_EXECUTION_STATUS_TIMED_OUT": WorkflowStatus.TIMED_OUT
            }
            
            status = status_mapping.get(
                description.status.name,
                WorkflowStatus.RUNNING
            )
            
            # Calculate duration
            start_time = description.start_time
            close_time = description.close_time
            duration = None
            
            if start_time:
                if close_time:
                    duration = (close_time - start_time).total_seconds()
                else:
                    duration = (datetime.utcnow() - start_time.replace(tzinfo=None)).total_seconds()
            
            return {
                "workflow_id": workflow_id,
                "status": status.value,
                "start_time": start_time.replace(tzinfo=None) if start_time else None,
                "end_time": close_time.replace(tzinfo=None) if close_time else None,
                "duration_seconds": duration,
                "workflow_type": description.workflow_type.name if description.workflow_type else None,
                "task_queue": description.task_queue,
                "run_id": description.run_id
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow status for {workflow_id}: {e}")
            raise

    async def list_workflows(
        self,
        *,
        query: str = "",
        max_results: int = 100
    ) -> List[Any]:
        """List workflow executions from Temporal."""

        if not self._client:
            await self.connect()

        results: List[Any] = []
        effective_query = query or ""

        try:
            async for description in self._client.list_workflows(query=effective_query):
                results.append(description)
                if len(results) >= max_results:
                    break
        except Exception as exc:  # pragma: no cover - network failure path
            logger.error(f"Failed to list workflows from Temporal: {exc}")

        return results

    @classmethod
    def resolve_workflow_class(cls, workflow_type: str) -> Optional[str]:
        return cls.WORKFLOW_CLASS_MAP.get(workflow_type)

    @classmethod
    def resolve_workflow_type(cls, workflow_class: Optional[str]) -> Optional[str]:
        if not workflow_class:
            return None

        for workflow_type, class_name in cls.WORKFLOW_CLASS_MAP.items():
            if workflow_class == class_name:
                return workflow_type
            if workflow_class.endswith(f".{class_name}"):
                return workflow_type

        short_name = workflow_class.split('.')[-1]
        for workflow_type, class_name in cls.WORKFLOW_CLASS_MAP.items():
            if short_name == class_name:
                return workflow_type

        return None
    
    async def cancel_workflow(self, workflow_id: str, reason: Optional[str] = None) -> bool:
        """
        Cancel a running workflow.
        
        Args:
            workflow_id: Workflow identifier
            reason: Optional cancellation reason
            
        Returns:
            True if cancellation was successful
        """
        if not self._client:
            await self.connect()
        
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            await handle.cancel()
            
            logger.info(f"Cancelled workflow {workflow_id}: {reason or 'No reason provided'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel workflow {workflow_id}: {e}")
            return False
    
    async def terminate_workflow(self, workflow_id: str, reason: Optional[str] = None) -> bool:
        """
        Terminate a running workflow.
        
        Args:
            workflow_id: Workflow identifier
            reason: Optional termination reason
            
        Returns:
            True if termination was successful
        """
        if not self._client:
            await self.connect()
        
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            await handle.terminate(reason=reason)
            
            logger.info(f"Terminated workflow {workflow_id}: {reason or 'No reason provided'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to terminate workflow {workflow_id}: {e}")
            return False
    
    async def get_workflow_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        Get workflow execution history.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            List of workflow history events
        """
        if not self._client:
            await self.connect()
        
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            
            # Get workflow history
            history = []
            async for event in handle.fetch_history():
                history.append({
                    "event_id": event.event_id,
                    "event_type": event.event_type.name,
                    "event_time": event.event_time.replace(tzinfo=None) if event.event_time else None,
                    "task_id": getattr(event, 'task_id', None),
                    "attributes": str(event)  # Simplified - would need proper parsing
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get workflow history for {workflow_id}: {e}")
            return []
    
    
    async def get_workflow_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get workflow execution metrics.
        
        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Workflow metrics summary
        """
        try:
            # Get workflow list for metrics calculation
            workflows = await self.list_workflows(limit=1000)
            
            # Filter by time range if specified
            if start_time or end_time:
                filtered_workflows = []
                for wf in workflows:
                    wf_start = wf.get('start_time')
                    if wf_start:
                        if start_time and wf_start < start_time:
                            continue
                        if end_time and wf_start > end_time:
                            continue
                    filtered_workflows.append(wf)
                workflows = filtered_workflows
            
            # Calculate metrics
            total_workflows = len(workflows)
            status_counts = {}
            workflow_type_counts = {}
            total_duration = 0
            completed_workflows = 0
            
            for wf in workflows:
                # Count by status
                status = wf.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count by workflow type
                wf_type = wf.get('workflow_type', 'unknown')
                workflow_type_counts[wf_type] = workflow_type_counts.get(wf_type, 0) + 1
                
                # Calculate duration for completed workflows
                if wf.get('start_time') and wf.get('close_time'):
                    duration = (wf['close_time'] - wf['start_time']).total_seconds()
                    total_duration += duration
                    completed_workflows += 1
            
            avg_duration = total_duration / completed_workflows if completed_workflows > 0 else 0
            success_rate = (status_counts.get('WORKFLOW_EXECUTION_STATUS_COMPLETED', 0) / total_workflows * 100) if total_workflows > 0 else 0
            
            return {
                "total_workflows": total_workflows,
                "status_distribution": status_counts,
                "workflow_type_distribution": workflow_type_counts,
                "success_rate": success_rate,
                "avg_duration_seconds": avg_duration,
                "completed_workflows": completed_workflows
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow metrics: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check if Temporal connection is healthy"""
        try:
            if not self._client:
                await self.connect()
            
            # Simple health check by listing workflows with limit 1
            workflows = await self.list_workflows(limit=1)
            return True
            
        except Exception as e:
            logger.error(f"Temporal health check failed: {e}")
            return False
