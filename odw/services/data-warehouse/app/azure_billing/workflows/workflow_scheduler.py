"""
Workflow Scheduler for Azure Billing Intelligence

Manages scheduled workflow execution, monitoring, and automation
for Azure billing data processing workflows.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from croniter import croniter

from temporalio.client import Client, WorkflowHandle
from temporalio.common import RetryPolicy

from .temporal_workflows import (
    AzureBillingWorkflow,
    FOCUSTransformationWorkflow,
    DataValidationWorkflow,
    AzureBillingWorkflowInput,
    WorkflowResult
)

logger = logging.getLogger(__name__)


class ScheduledWorkflow:
    """Configuration for a scheduled workflow"""
    
    def __init__(
        self,
        name: str,
        workflow_class: str,
        schedule: str,  # Cron expression
        parameters: Dict[str, Any],
        enabled: bool = True,
        max_concurrent: int = 1,
        timeout_minutes: int = 120
    ):
        self.name = name
        self.workflow_class = workflow_class
        self.schedule = schedule
        self.parameters = parameters
        self.enabled = enabled
        self.max_concurrent = max_concurrent
        self.timeout_minutes = timeout_minutes
        self.last_execution: Optional[datetime] = None
        self.next_execution: Optional[datetime] = None
        self.running_workflows: List[str] = []


class WorkflowScheduler:
    """Scheduler for managing automated workflow execution"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client: Optional[Client] = None
        self.scheduled_workflows: Dict[str, ScheduledWorkflow] = {}
        self.running = False
        
    async def initialize(self):
        """Initialize Temporal client and load scheduled workflows"""
        try:
            # Connect to Temporal
            temporal_host = self.config.get('temporal_host', 'localhost:7233')
            self.client = await Client.connect(temporal_host)
            
            # Load default scheduled workflows
            await self._load_default_schedules()
            
            logger.info("Workflow scheduler initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize workflow scheduler: {e}")
            raise
    
    async def _load_default_schedules(self):
        """Load default scheduled workflows"""
        
        # Daily Azure billing extraction at 2 AM
        daily_extraction = ScheduledWorkflow(
            name="daily_azure_billing_extraction",
            workflow_class="AzureBillingWorkflow",
            schedule="0 2 * * *",  # Daily at 2 AM
            parameters={
                "start_date": "yesterday",  # Will be resolved at runtime
                "end_date": "yesterday",
                "batch_size": 1000,
                "enrollment_number": None  # Will use default from config
            },
            enabled=True,
            max_concurrent=1,
            timeout_minutes=120
        )
        
        # Weekly data validation on Sundays at 3 AM
        weekly_validation = ScheduledWorkflow(
            name="weekly_data_validation",
            workflow_class="DataValidationWorkflow",
            schedule="0 3 * * 0",  # Sundays at 3 AM
            parameters={
                "data_location": "focus_billing_data",
                "validation_config": {
                    "strict_mode": True,
                    "generate_report": True
                }
            },
            enabled=True,
            max_concurrent=1,
            timeout_minutes=60
        )
        
        # Monthly full data refresh on 1st at 1 AM
        monthly_refresh = ScheduledWorkflow(
            name="monthly_full_refresh",
            workflow_class="AzureBillingWorkflow",
            schedule="0 1 1 * *",  # 1st of month at 1 AM
            parameters={
                "start_date": "last_month_start",  # Will be resolved at runtime
                "end_date": "last_month_end",
                "batch_size": 5000,
                "enrollment_number": None
            },
            enabled=False,  # Disabled by default
            max_concurrent=1,
            timeout_minutes=240
        )
        
        self.scheduled_workflows = {
            "daily_extraction": daily_extraction,
            "weekly_validation": weekly_validation,
            "monthly_refresh": monthly_refresh
        }
        
        # Calculate next execution times
        for workflow in self.scheduled_workflows.values():
            self._update_next_execution(workflow)
    
    def _update_next_execution(self, workflow: ScheduledWorkflow):
        """Update next execution time for a workflow"""
        if workflow.enabled:
            cron = croniter(workflow.schedule, datetime.utcnow())
            workflow.next_execution = cron.get_next(datetime)
        else:
            workflow.next_execution = None
    
    def _resolve_date_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve dynamic date parameters"""
        resolved = parameters.copy()
        now = datetime.utcnow()
        
        # Resolve date placeholders
        date_mappings = {
            "yesterday": (now - timedelta(days=1)).strftime('%Y-%m-%d'),
            "today": now.strftime('%Y-%m-%d'),
            "last_month_start": (now.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d'),
            "last_month_end": (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
        }
        
        for key, value in resolved.items():
            if isinstance(value, str) and value in date_mappings:
                resolved[key] = date_mappings[value]
        
        return resolved
    
    async def add_scheduled_workflow(self, workflow: ScheduledWorkflow):
        """Add a new scheduled workflow"""
        self.scheduled_workflows[workflow.name] = workflow
        self._update_next_execution(workflow)
        logger.info(f"Added scheduled workflow: {workflow.name}")
    
    async def remove_scheduled_workflow(self, name: str):
        """Remove a scheduled workflow"""
        if name in self.scheduled_workflows:
            del self.scheduled_workflows[name]
            logger.info(f"Removed scheduled workflow: {name}")
    
    async def enable_workflow(self, name: str):
        """Enable a scheduled workflow"""
        if name in self.scheduled_workflows:
            workflow = self.scheduled_workflows[name]
            workflow.enabled = True
            self._update_next_execution(workflow)
            logger.info(f"Enabled scheduled workflow: {name}")
    
    async def disable_workflow(self, name: str):
        """Disable a scheduled workflow"""
        if name in self.scheduled_workflows:
            workflow = self.scheduled_workflows[name]
            workflow.enabled = False
            workflow.next_execution = None
            logger.info(f"Disabled scheduled workflow: {name}")
    
    async def trigger_workflow_now(self, name: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Manually trigger a scheduled workflow"""
        if name not in self.scheduled_workflows:
            raise ValueError(f"Scheduled workflow not found: {name}")
        
        workflow_config = self.scheduled_workflows[name]
        
        # Use provided parameters or default ones
        workflow_params = parameters or workflow_config.parameters
        resolved_params = self._resolve_date_parameters(workflow_params)
        
        # Generate workflow ID
        workflow_id = f"{name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Start workflow based on type
        if workflow_config.workflow_class == "AzureBillingWorkflow":
            input_params = AzureBillingWorkflowInput(**resolved_params)
            handle = await self.client.start_workflow(
                AzureBillingWorkflow.run,
                input_params,
                id=workflow_id,
                task_queue="abi-workflows",
                execution_timeout=timedelta(minutes=workflow_config.timeout_minutes)
            )
        elif workflow_config.workflow_class == "DataValidationWorkflow":
            handle = await self.client.start_workflow(
                DataValidationWorkflow.run,
                resolved_params["data_location"],
                resolved_params["validation_config"],
                id=workflow_id,
                task_queue="abi-workflows",
                execution_timeout=timedelta(minutes=workflow_config.timeout_minutes)
            )
        else:
            raise ValueError(f"Unknown workflow class: {workflow_config.workflow_class}")
        
        # Track running workflow
        workflow_config.running_workflows.append(workflow_id)
        
        logger.info(f"Triggered workflow {name} with ID: {workflow_id}")
        return workflow_id
    
    async def check_workflow_completion(self, workflow_name: str, workflow_id: str):
        """Check if a workflow has completed and update tracking"""
        try:
            handle = self.client.get_workflow_handle(workflow_id)
            result = await handle.result()
            
            # Remove from running workflows
            if workflow_name in self.scheduled_workflows:
                workflow_config = self.scheduled_workflows[workflow_name]
                if workflow_id in workflow_config.running_workflows:
                    workflow_config.running_workflows.remove(workflow_id)
                
                workflow_config.last_execution = datetime.utcnow()
            
            logger.info(f"Workflow {workflow_name} ({workflow_id}) completed successfully")
            
        except Exception as e:
            logger.error(f"Error checking workflow completion for {workflow_id}: {e}")
    
    async def run_scheduler(self):
        """Main scheduler loop"""
        self.running = True
        logger.info("Starting workflow scheduler")
        
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                # Check each scheduled workflow
                for name, workflow in self.scheduled_workflows.items():
                    if not workflow.enabled or not workflow.next_execution:
                        continue
                    
                    # Check if it's time to execute
                    if current_time >= workflow.next_execution:
                        # Check concurrent execution limit
                        if len(workflow.running_workflows) >= workflow.max_concurrent:
                            logger.warning(f"Skipping {name}: max concurrent executions reached")
                            continue
                        
                        try:
                            # Trigger workflow
                            workflow_id = await self.trigger_workflow_now(name)
                            
                            # Update next execution time
                            self._update_next_execution(workflow)
                            
                        except Exception as e:
                            logger.error(f"Failed to trigger scheduled workflow {name}: {e}")
                
                # Clean up completed workflows
                for name, workflow in self.scheduled_workflows.items():
                    for workflow_id in workflow.running_workflows.copy():
                        await self.check_workflow_completion(name, workflow_id)
                
                # Sleep for 60 seconds before next check
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.client:
            await self.client.close()
        logger.info("Workflow scheduler stopped")
    
    def get_schedule_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        status = {
            "running": self.running,
            "workflows": {}
        }
        
        for name, workflow in self.scheduled_workflows.items():
            status["workflows"][name] = {
                "enabled": workflow.enabled,
                "schedule": workflow.schedule,
                "next_execution": workflow.next_execution.isoformat() if workflow.next_execution else None,
                "last_execution": workflow.last_execution.isoformat() if workflow.last_execution else None,
                "running_count": len(workflow.running_workflows),
                "max_concurrent": workflow.max_concurrent
            }
        
        return status


async def run_scheduler(config: Dict[str, Any] = None):
    """
    Run the workflow scheduler process.
    
    Args:
        config: Scheduler configuration
    """
    
    if config is None:
        config = {
            'temporal_host': 'localhost:7233'
        }
    
    scheduler = WorkflowScheduler(config)
    
    try:
        await scheduler.initialize()
        await scheduler.run_scheduler()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await scheduler.stop()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the scheduler
    asyncio.run(run_scheduler())