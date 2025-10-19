"""
Scheduled Workflow Automation System

Comprehensive automation system for scheduled Azure billing workflows,
data quality monitoring, and report generation with alerting capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

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
from .workflow_monitor import WorkflowMonitor, AlertSeverity, WorkflowAlert

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Types of scheduled workflows"""
    DAILY_EXTRACTION = "daily_extraction"
    WEEKLY_VALIDATION = "weekly_validation"
    MONTHLY_REFRESH = "monthly_refresh"
    HOURLY_MONITORING = "hourly_monitoring"
    CUSTOM = "custom"


@dataclass
class ScheduledWorkflowConfig:
    """Configuration for a scheduled workflow"""
    name: str
    schedule_type: ScheduleType
    cron_expression: str
    workflow_class: str
    parameters: Dict[str, Any]
    enabled: bool = True
    max_concurrent: int = 1
    timeout_minutes: int = 120
    retry_policy: Optional[Dict[str, Any]] = None
    alert_on_failure: bool = True
    alert_recipients: List[str] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class WorkflowExecution:
    """Tracking information for workflow execution"""
    execution_id: str
    workflow_name: str
    schedule_type: ScheduleType
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"
    result: Optional[WorkflowResult] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class AlertManager:
    """Manages alerting for workflow failures and monitoring"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.smtp_config = config.get('smtp', {})
        self.webhook_config = config.get('webhook', {})
        self.enabled = config.get('enabled', True)
    
    async def send_alert(
        self,
        alert: WorkflowAlert,
        recipients: List[str],
        workflow_execution: Optional[WorkflowExecution] = None
    ):
        """Send alert notification"""
        if not self.enabled:
            return
        
        try:
            # Send email alert
            if self.smtp_config and recipients:
                await self._send_email_alert(alert, recipients, workflow_execution)
            
            # Send webhook alert
            if self.webhook_config:
                await self._send_webhook_alert(alert, workflow_execution)
            
            logger.info(f"Alert sent: {alert.message}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def _send_email_alert(
        self,
        alert: WorkflowAlert,
        recipients: List[str],
        workflow_execution: Optional[WorkflowExecution]
    ):
        """Send email alert"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"ABI Workflow Alert: {alert.severity.value.upper()} - {alert.workflow_type}"
            
            # Create email body
            body = self._create_alert_email_body(alert, workflow_execution)
            msg.attach(MimeText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config.get('use_tls'):
                    server.starttls()
                if self.smtp_config.get('username'):
                    server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _create_alert_email_body(
        self,
        alert: WorkflowAlert,
        workflow_execution: Optional[WorkflowExecution]
    ) -> str:
        """Create HTML email body for alert"""
        severity_colors = {
            AlertSeverity.INFO: "#17a2b8",
            AlertSeverity.WARNING: "#ffc107",
            AlertSeverity.ERROR: "#dc3545",
            AlertSeverity.CRITICAL: "#6f42c1"
        }
        
        color = severity_colors.get(alert.severity, "#6c757d")
        
        html = f"""
        <html>
        <body>
            <h2 style="color: {color};">Azure Billing Intelligence Alert</h2>
            <p><strong>Severity:</strong> {alert.severity.value.upper()}</p>
            <p><strong>Workflow:</strong> {alert.workflow_type}</p>
            <p><strong>Workflow ID:</strong> {alert.workflow_id}</p>
            <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p><strong>Message:</strong> {alert.message}</p>
        """
        
        if workflow_execution:
            html += f"""
            <h3>Execution Details</h3>
            <p><strong>Execution ID:</strong> {workflow_execution.execution_id}</p>
            <p><strong>Status:</strong> {workflow_execution.status}</p>
            <p><strong>Start Time:</strong> {workflow_execution.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            """
            
            if workflow_execution.end_time:
                duration = workflow_execution.end_time - workflow_execution.start_time
                html += f"<p><strong>Duration:</strong> {duration.total_seconds():.2f} seconds</p>"
            
            if workflow_execution.error_message:
                html += f"<p><strong>Error:</strong> {workflow_execution.error_message}</p>"
        
        if alert.metadata:
            html += f"""
            <h3>Additional Information</h3>
            <pre>{json.dumps(alert.metadata, indent=2)}</pre>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    async def _send_webhook_alert(
        self,
        alert: WorkflowAlert,
        workflow_execution: Optional[WorkflowExecution]
    ):
        """Send webhook alert"""
        # Implementation for webhook alerts (Slack, Teams, etc.)
        pass


class ScheduledWorkflowAutomation:
    """
    Main automation system for scheduled workflows.
    
    Manages the complete lifecycle of scheduled workflows including:
    - Daily Azure billing data extraction
    - Weekly data quality validation
    - Monthly full data refresh
    - Automated monitoring and alerting
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client: Optional[Client] = None
        self.monitor: Optional[WorkflowMonitor] = None
        self.alert_manager: Optional[AlertManager] = None
        
        self.scheduled_workflows: Dict[str, ScheduledWorkflowConfig] = {}
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_history: List[WorkflowExecution] = []
        
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.monitor_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize the automation system"""
        try:
            # Connect to Temporal
            temporal_host = self.config.get('temporal_host', 'localhost:7233')
            self.client = await Client.connect(temporal_host)
            
            # Initialize monitoring
            self.monitor = WorkflowMonitor(self.config.get('monitoring', {}))
            await self.monitor.initialize()
            
            # Initialize alert manager
            self.alert_manager = AlertManager(self.config.get('alerting', {}))
            
            # Load default scheduled workflows
            await self._load_default_schedules()
            
            logger.info("Scheduled workflow automation initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize automation system: {e}")
            raise
    
    async def _load_default_schedules(self):
        """Load default scheduled workflow configurations"""
        
        # Daily Azure billing extraction at 2 AM UTC
        daily_extraction = ScheduledWorkflowConfig(
            name="daily_azure_billing_extraction",
            schedule_type=ScheduleType.DAILY_EXTRACTION,
            cron_expression="0 2 * * *",  # Daily at 2 AM UTC
            workflow_class="AzureBillingWorkflow",
            parameters={
                "start_date": "yesterday",
                "end_date": "yesterday",
                "batch_size": 1000,
                "enrollment_number": None  # Will use default from config
            },
            enabled=True,
            max_concurrent=1,
            timeout_minutes=120,
            alert_on_failure=True,
            alert_recipients=self.config.get('default_alert_recipients', []),
            description="Daily extraction of Azure billing data for the previous day",
            tags=["daily", "extraction", "azure", "billing"]
        )
        
        # Weekly data quality validation on Sundays at 3 AM UTC
        weekly_validation = ScheduledWorkflowConfig(
            name="weekly_data_quality_validation",
            schedule_type=ScheduleType.WEEKLY_VALIDATION,
            cron_expression="0 3 * * 0",  # Sundays at 3 AM UTC
            workflow_class="DataValidationWorkflow",
            parameters={
                "data_location": "focus_billing_data",
                "validation_config": {
                    "strict_mode": True,
                    "generate_report": True,
                    "check_completeness": True,
                    "validate_focus_compliance": True
                }
            },
            enabled=True,
            max_concurrent=1,
            timeout_minutes=60,
            alert_on_failure=True,
            alert_recipients=self.config.get('default_alert_recipients', []),
            description="Weekly comprehensive data quality validation",
            tags=["weekly", "validation", "quality", "focus"]
        )
        
        # Monthly full data refresh on 1st at 1 AM UTC
        monthly_refresh = ScheduledWorkflowConfig(
            name="monthly_full_data_refresh",
            schedule_type=ScheduleType.MONTHLY_REFRESH,
            cron_expression="0 1 1 * *",  # 1st of month at 1 AM UTC
            workflow_class="AzureBillingWorkflow",
            parameters={
                "start_date": "last_month_start",
                "end_date": "last_month_end",
                "batch_size": 5000,
                "enrollment_number": None,
                "full_refresh": True
            },
            enabled=False,  # Disabled by default - enable manually
            max_concurrent=1,
            timeout_minutes=240,
            alert_on_failure=True,
            alert_recipients=self.config.get('default_alert_recipients', []),
            description="Monthly full refresh of billing data for the previous month",
            tags=["monthly", "refresh", "full", "azure"]
        )
        
        # Hourly data quality monitoring
        hourly_monitoring = ScheduledWorkflowConfig(
            name="hourly_data_quality_monitoring",
            schedule_type=ScheduleType.HOURLY_MONITORING,
            cron_expression="0 * * * *",  # Every hour
            workflow_class="DataValidationWorkflow",
            parameters={
                "data_location": "focus_billing_data",
                "validation_config": {
                    "quick_check": True,
                    "check_recent_data": True,
                    "alert_on_anomalies": True
                }
            },
            enabled=True,
            max_concurrent=1,
            timeout_minutes=15,
            alert_on_failure=False,  # Only alert on data anomalies, not workflow failures
            alert_recipients=self.config.get('monitoring_alert_recipients', []),
            description="Hourly monitoring for data quality and anomalies",
            tags=["hourly", "monitoring", "quality", "anomalies"]
        )
        
        self.scheduled_workflows = {
            "daily_extraction": daily_extraction,
            "weekly_validation": weekly_validation,
            "monthly_refresh": monthly_refresh,
            "hourly_monitoring": hourly_monitoring
        }
        
        # Calculate next execution times
        for workflow in self.scheduled_workflows.values():
            self._update_next_execution(workflow)
    
    def _update_next_execution(self, workflow: ScheduledWorkflowConfig):
        """Update next execution time for a workflow"""
        if workflow.enabled:
            cron = croniter(workflow.cron_expression, datetime.utcnow())
            workflow.next_execution = cron.get_next(datetime)
        else:
            workflow.next_execution = None
    
    def _resolve_date_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve dynamic date parameters"""
        resolved = parameters.copy()
        now = datetime.utcnow()
        
        # Date resolution mappings
        date_mappings = {
            "yesterday": (now - timedelta(days=1)).strftime('%Y-%m-%d'),
            "today": now.strftime('%Y-%m-%d'),
            "last_week_start": (now - timedelta(days=now.weekday() + 7)).strftime('%Y-%m-%d'),
            "last_week_end": (now - timedelta(days=now.weekday() + 1)).strftime('%Y-%m-%d'),
            "last_month_start": (now.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d'),
            "last_month_end": (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d'),
            "current_month_start": now.replace(day=1).strftime('%Y-%m-%d')
        }
        
        # Recursively resolve date parameters
        def resolve_value(value):
            if isinstance(value, str) and value in date_mappings:
                return date_mappings[value]
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            return value
        
        for key, value in resolved.items():
            resolved[key] = resolve_value(value)
        
        return resolved
    
    async def add_scheduled_workflow(self, workflow: ScheduledWorkflowConfig):
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
    
    async def trigger_workflow_now(
        self,
        name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Manually trigger a scheduled workflow"""
        if name not in self.scheduled_workflows:
            raise ValueError(f"Scheduled workflow not found: {name}")
        
        workflow_config = self.scheduled_workflows[name]
        
        # Check concurrent execution limit
        active_count = sum(
            1 for exec in self.active_executions.values()
            if exec.workflow_name == name and exec.status == "running"
        )
        
        if active_count >= workflow_config.max_concurrent:
            raise ValueError(f"Maximum concurrent executions ({workflow_config.max_concurrent}) reached for {name}")
        
        # Resolve parameters
        workflow_params = parameters or workflow_config.parameters
        resolved_params = self._resolve_date_parameters(workflow_params)
        
        # Generate execution ID
        execution_id = f"{name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Create execution tracking
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_name=name,
            schedule_type=workflow_config.schedule_type,
            start_time=datetime.utcnow()
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            # Start workflow based on type
            if workflow_config.workflow_class == "AzureBillingWorkflow":
                input_params = AzureBillingWorkflowInput(**resolved_params)
                handle = await self.client.start_workflow(
                    AzureBillingWorkflow.run,
                    input_params,
                    id=execution_id,
                    task_queue="abi-workflows",
                    execution_timeout=timedelta(minutes=workflow_config.timeout_minutes)
                )
            elif workflow_config.workflow_class == "DataValidationWorkflow":
                handle = await self.client.start_workflow(
                    DataValidationWorkflow.run,
                    resolved_params["data_location"],
                    resolved_params["validation_config"],
                    id=execution_id,
                    task_queue="abi-workflows",
                    execution_timeout=timedelta(minutes=workflow_config.timeout_minutes)
                )
            else:
                raise ValueError(f"Unknown workflow class: {workflow_config.workflow_class}")
            
            logger.info(f"Triggered workflow {name} with execution ID: {execution_id}")
            return execution_id
            
        except Exception as e:
            # Update execution with error
            execution.status = "failed"
            execution.end_time = datetime.utcnow()
            execution.error_message = str(e)
            
            # Send alert if configured
            if workflow_config.alert_on_failure:
                alert = WorkflowAlert(
                    workflow_id=execution_id,
                    workflow_type=name,
                    severity=AlertSeverity.ERROR,
                    message=f"Failed to start workflow: {str(e)}",
                    timestamp=datetime.utcnow(),
                    metadata={"parameters": resolved_params}
                )
                await self.alert_manager.send_alert(alert, workflow_config.alert_recipients, execution)
            
            raise
    
    async def check_workflow_completion(self, execution_id: str):
        """Check if a workflow has completed and update tracking"""
        if execution_id not in self.active_executions:
            return
        
        execution = self.active_executions[execution_id]
        workflow_config = self.scheduled_workflows.get(execution.workflow_name)
        
        try:
            handle = self.client.get_workflow_handle(execution_id)
            result = await handle.result()
            
            # Update execution
            execution.status = "completed" if result.success else "failed"
            execution.end_time = datetime.utcnow()
            execution.result = result
            
            if not result.success:
                execution.error_message = result.error_message
                
                # Send failure alert
                if workflow_config and workflow_config.alert_on_failure:
                    alert = WorkflowAlert(
                        workflow_id=execution_id,
                        workflow_type=execution.workflow_name,
                        severity=AlertSeverity.ERROR,
                        message=f"Workflow failed: {result.error_message}",
                        timestamp=datetime.utcnow(),
                        metadata={"result": result.__dict__}
                    )
                    await self.alert_manager.send_alert(
                        alert,
                        workflow_config.alert_recipients,
                        execution
                    )
            else:
                logger.info(f"Workflow {execution.workflow_name} ({execution_id}) completed successfully")
            
            # Move to history
            self.execution_history.append(execution)
            del self.active_executions[execution_id]
            
        except Exception as e:
            logger.error(f"Error checking workflow completion for {execution_id}: {e}")
    
    async def run_scheduler(self):
        """Main scheduler loop"""
        self.running = True
        logger.info("Starting scheduled workflow automation")
        
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                # Check each scheduled workflow
                for name, workflow in self.scheduled_workflows.items():
                    if not workflow.enabled or not hasattr(workflow, 'next_execution') or not workflow.next_execution:
                        continue
                    
                    # Check if it's time to execute
                    if current_time >= workflow.next_execution:
                        try:
                            # Trigger workflow
                            execution_id = await self.trigger_workflow_now(name)
                            
                            # Update next execution time
                            self._update_next_execution(workflow)
                            
                            logger.info(f"Scheduled execution triggered: {name} ({execution_id})")
                            
                        except Exception as e:
                            logger.error(f"Failed to trigger scheduled workflow {name}: {e}")
                
                # Check completion of active workflows
                for execution_id in list(self.active_executions.keys()):
                    await self.check_workflow_completion(execution_id)
                
                # Sleep for 60 seconds before next check
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    async def run_monitoring(self):
        """Run continuous monitoring for data quality and system health"""
        logger.info("Starting continuous monitoring")
        
        while self.running:
            try:
                # Monitor workflow performance
                if self.monitor:
                    await self.monitor.check_workflow_health()
                
                # Check for data quality issues
                await self._check_data_quality_alerts()
                
                # Check system health
                await self._check_system_health()
                
                # Sleep for 5 minutes before next monitoring cycle
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(300)
    
    async def _check_data_quality_alerts(self):
        """Check for data quality issues and send alerts"""
        # Implementation for data quality monitoring
        # This would check for:
        # - Missing data for expected time periods
        # - Data anomalies (unusual cost spikes, etc.)
        # - FOCUS compliance violations
        # - Data freshness issues
        pass
    
    async def _check_system_health(self):
        """Check overall system health and send alerts"""
        # Implementation for system health monitoring
        # This would check:
        # - ClickHouse connectivity and performance
        # - Temporal server health
        # - Plugin system status
        # - Storage system health
        pass
    
    async def start(self):
        """Start the automation system"""
        await self.initialize()
        
        # Start scheduler task
        self.scheduler_task = asyncio.create_task(self.run_scheduler())
        
        # Start monitoring task
        self.monitor_task = asyncio.create_task(self.run_monitoring())
        
        logger.info("Scheduled workflow automation started")
    
    async def stop(self):
        """Stop the automation system"""
        self.running = False
        
        # Cancel tasks
        if self.scheduler_task:
            self.scheduler_task.cancel()
        if self.monitor_task:
            self.monitor_task.cancel()
        
        # Close connections
        if self.client:
            await self.client.close()
        if self.monitor:
            await self.monitor.stop()
        
        logger.info("Scheduled workflow automation stopped")
    
    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation system status"""
        return {
            "running": self.running,
            "scheduled_workflows": {
                name: {
                    "enabled": workflow.enabled,
                    "schedule_type": workflow.schedule_type.value,
                    "cron_expression": workflow.cron_expression,
                    "next_execution": workflow.next_execution.isoformat() if hasattr(workflow, 'next_execution') and workflow.next_execution else None,
                    "description": workflow.description,
                    "tags": workflow.tags
                }
                for name, workflow in self.scheduled_workflows.items()
            },
            "active_executions": {
                execution_id: {
                    "workflow_name": execution.workflow_name,
                    "schedule_type": execution.schedule_type.value,
                    "start_time": execution.start_time.isoformat(),
                    "status": execution.status
                }
                for execution_id, execution in self.active_executions.items()
            },
            "recent_executions": [
                {
                    "execution_id": execution.execution_id,
                    "workflow_name": execution.workflow_name,
                    "start_time": execution.start_time.isoformat(),
                    "end_time": execution.end_time.isoformat() if execution.end_time else None,
                    "status": execution.status,
                    "success": execution.result.success if execution.result else None
                }
                for execution in self.execution_history[-10:]  # Last 10 executions
            ]
        }


async def run_automation_system(config: Dict[str, Any] = None):
    """
    Run the scheduled workflow automation system.
    
    Args:
        config: Automation system configuration
    """
    
    if config is None:
        config = {
            'temporal_host': 'localhost:7233',
            'default_alert_recipients': [],
            'monitoring_alert_recipients': [],
            'alerting': {
                'enabled': True,
                'smtp': {
                    'host': 'localhost',
                    'port': 587,
                    'use_tls': True,
                    'from_email': 'abi-system@company.com'
                }
            }
        }
    
    automation = ScheduledWorkflowAutomation(config)
    
    try:
        await automation.start()
        
        # Keep running until interrupted
        while automation.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await automation.stop()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the automation system
    asyncio.run(run_automation_system())