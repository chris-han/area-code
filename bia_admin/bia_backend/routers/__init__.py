"""
BIA FastAPI Routers

FastAPI routers for the Billing Intelligence API (BIA) that extend the Moose stack
with additional functionality and proper dependency injection.
"""

from .billing_analytics_router import billing_analytics_router
from .workflow_management_router import workflow_management_router
from .plugin_management_router import plugin_management_router
from .focus_data_router import focus_data_router
from .health_check_router import health_check_router
from .storage_management_router import storage_management_router
from .budget_tracking_router import budget_tracking_router

__all__ = [
    "billing_analytics_router",
    "workflow_management_router",
    "plugin_management_router",
    "focus_data_router",
    "health_check_router",
    "storage_management_router",
    "budget_tracking_router",
]
