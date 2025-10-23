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
    """Enhanced Temporal client for ABI workflow management"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._client: Optional[Client] = None
        self.namespace = config.get('namespace', 'default')
        self.task_queue = config.get('task_queue', 'abi-workflows')
        
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
            await self._client.close()
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
            }
            
            workflow_class = workflow_classes.get(workflow_type)
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
            
            # Map Temporal status to ABI status
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
    
    async def list_workflows(
        self,
        status_filter: Optional[str] = None,
        workflow_type_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List workflow executions with filtering.
        
        Args:
            status_filter: Optional status filter
            workflow_type_filter: Optional workflow type filter
            limit: Maximum number of results
            
        Returns:
            List of workflow information
        """
        if not self._client:
            await self.connect()
        
        try:
            # Build query filter
            query_parts = []
            
            if status_filter:
                query_parts.append(f"ExecutionStatus = '{status_filter}'")
            
            if workflow_type_filter:
                query_parts.append(f"WorkflowType = '{workflow_type_filter}'")
            
            query = " AND ".join(query_parts) if query_parts else None
            
            # List workflows
            workflows = []
            async for workflow in self._client.list_workflows(query=query):
                workflows.append({
                    "workflow_id": workflow.execution.workflow_id,
                    "run_id": workflow.execution.run_id,
                    "workflow_type": workflow.workflow_type.name if workflow.workflow_type else None,
                    "status": workflow.status.name if workflow.status else None,
                    "start_time": workflow.start_time.replace(tzinfo=None) if workflow.start_time else None,
                    "close_time": workflow.close_time.replace(tzinfo=None) if workflow.close_time else None,
                    "task_queue": workflow.task_queue
                })
                
                if len(workflows) >= limit:
                    break
            
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
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
