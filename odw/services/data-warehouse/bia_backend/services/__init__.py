"""
Service layer for the Billing Intelligence API (BIA).

This package houses business logic used by the FastAPI routers, keeping
management endpoints (typically backed by PostgreSQL) and analytical queries
separate from the Moose consumption layer.
"""

__all__ = [
    "billing_analytics",
    "focus_data",
    "plugin_management",
    "storage_management",
    "workflow_management",
    "health_check",
]
