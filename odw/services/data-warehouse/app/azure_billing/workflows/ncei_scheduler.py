"""
Azure NCEI Workflow Scheduler

Schedules and manages Azure NCEI to FOCUS transformation workflows.
Replaces S3 CSV scheduling with Azure Blob Storage parquet processing.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from temporalio import workflow
from temporalio.client import Client

from .azure_ncei_workflow import AzureNCEIToFOCUSWorkflow

logger = logging.getLogger(__name__)


class NCEIWorkflowScheduler:
    """
    Scheduler for Azure NCEI workflows with configurable frequency.
    """
    
    def __init__(self, temporal_client: Client, config: Dict[str, Any]):
        self.client = temporal_client
        self.config = config
        self.ncei_config = self._load_ncei_config()
    
    def _load_ncei_config(self) -> Dict[str, Any]:
        """Load NCEI-specific configuration"""
        return {
            "account_url": "https://finopsbilling.blob.core.chinacloudapi.cn",
            "sas_token": "sv=2024-11-04&ss=bfqt&srt=sco&sp=rltfx&se=2045-10-19T12:52:39Z&st=2025-10-19T04:37:39Z&spr=https&sig=g44Cxk0eqgrn5N6DrZF8s60a3qaWp6cWLnPaNJtXw40%3D",
            "container_name": "billing-data",
            "secondary_container": None,
            "path_prefix": "focus-data/",
            "batch_size": 10,
            "default_currency": "USD",
            "provider": "Azure"
        }
    
    async def schedule_daily_workflow(self, start_date: Optional[datetime] = None) -> str:
        """
        Schedule daily NCEI workflow execution.
        
        Args:
            start_date: Optional start date, defaults to yesterday
            
        Returns:
            Workflow ID
        """
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=1)
        
        end_date = start_date + timedelta(days=1)
        
        workflow_params = {
            **self.ncei_config,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "workflow_type": "daily"
        }
        
        workflow_id = f"azure-ncei-daily-{start_date.strftime('%Y%m%d')}"
        
        handle = await self.client.start_workflow(
            AzureNCEIToFOCUSWorkflow.run,
            workflow_params,
            id=workflow_id,
            task_queue="azure-billing-queue"
        )
        
        logger.info(f"Scheduled daily NCEI workflow: {workflow_id}")
        return workflow_id
    
    async def schedule_manual_workflow(self, 
                                     start_date: datetime, 
                                     end_date: datetime,
                                     custom_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Schedule manual NCEI workflow execution.
        
        Args:
            start_date: Start date for processing
            end_date: End date for processing
            custom_config: Optional custom configuration
            
        Returns:
            Workflow ID
        """
        workflow_params = {
            **self.ncei_config,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "workflow_type": "manual"
        }
        
        if custom_config:
            workflow_params.update(custom_config)
        
        workflow_id = f"azure-ncei-manual-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        handle = await self.client.start_workflow(
            AzureNCEIToFOCUSWorkflow.run,
            workflow_params,
            id=workflow_id,
            task_queue="azure-billing-queue"
        )
        
        logger.info(f"Scheduled manual NCEI workflow: {workflow_id}")
        return workflow_id


# Factory function for creating scheduler
def create_ncei_scheduler(temporal_client: Client, config: Optional[Dict[str, Any]] = None) -> NCEIWorkflowScheduler:
    """
    Factory function to create NCEI workflow scheduler.
    
    Args:
        temporal_client: Temporal client instance
        config: Optional configuration dictionary
        
    Returns:
        Configured NCEIWorkflowScheduler instance
    """
    default_config = {
        "task_queue": "azure-billing-queue",
        "workflow_timeout": timedelta(hours=2),
        "retry_policy": {
            "maximum_attempts": 3,
            "initial_interval": timedelta(seconds=30)
        }
    }
    
    if config:
        default_config.update(config)
    
    return NCEIWorkflowScheduler(temporal_client, default_config)