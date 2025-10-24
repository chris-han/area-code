"""
Workflow Monitoring and Management System

Comprehensive monitoring, alerting, and management system for
Temporal workflows with performance metrics and error tracking.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from temporalio.client import Client, WorkflowHandle
from temporalio.common import WorkflowExecution

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class WorkflowAlert:
    """Workflow alert information"""
    workflow_id: str
    workflow_type: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class WorkflowMetrics:
    """Workflow performance metrics"""
    workflow_id: str
    workflow_type: str
    start_time: datetime
    end_time: Optional[datetime]
    execution_time_seconds: Optional[float]
    status: str
    records_processed: int
    records_failed: int
    memory_usage_mb: Optional[float]
    cpu_usage_percent: Optional[float]
    error_message: Optional[str]


class WorkflowMonitor:
    """
    Comprehensive workflow monitoring and alerting system.
    
    Monitors Temporal workflows for performance, errors, and SLA compliance.
    Provides alerting capabilities for proactive issue detection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client: Optional[Client] = None
        self.monitoring_active = False
        
        # Alert thresholds
        self.alert_thresholds = {
            "max_execution_time_minutes": 120,
            "max_retry_count": 3,
            "min_success_rate_percent": 95.0,
            "max_memory_usage_mb": 2048,
            "max_cpu_usage_percent": 80.0,
            "max_failed_records_percent": 5.0
        }
        
        # Performance tracking
        self.workflow_metrics: Dict[str, WorkflowMetrics] = {}
        self.alerts: List[WorkflowAlert] = []
        self.performance_history: List[WorkflowMetrics] = []