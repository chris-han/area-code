"""
Budget Tracking Router

FastAPI router for budget tracking and variance analysis endpoints.
"""

from fastapi import APIRouter

from bia_backend.budget_tracking import router as budget_tracking_api_router

# Create the main budget tracking router
budget_tracking_router = APIRouter()

# Include the budget tracking API routes
budget_tracking_router.include_router(budget_tracking_api_router)

__all__ = ["budget_tracking_router"]
