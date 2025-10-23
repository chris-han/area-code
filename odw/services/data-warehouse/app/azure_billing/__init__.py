"""
Azure Billing Intelligence (ABI) Module

This module provides Azure Enterprise Agreement billing data integration,
FOCUS-compliant data transformation, and analytics capabilities.

Now includes Azure NCEI (National Cloud Economics Intelligence) workflow
for processing FOCUS-compliant parquet files from Azure Blob Storage.
"""

__version__ = "0.2.0"
__author__ = "ABI Team"

# Export NCEI workflow components - temporarily commented to fix FastAPI conflict
# from .workflows.azure_ncei_workflow import AzureNCEIToFOCUSWorkflow
# from .workflows.ncei_scheduler import NCEIWorkflowScheduler, create_ncei_scheduler
# Commented out FastAPI import that conflicts with Temporal workflow sandbox
# from .workflows.ncei_api import router as ncei_api_router
# Commented out models and transformations that cause datetime/clickhouse conflicts
# from .models.azure_blob_parquet_models import AzureNCEIParquetModel
# from .transformations.azure_ncei_to_focus import AzureNCEIToFOCUSTransformer

__all__ = [
    # "AzureNCEIToFOCUSWorkflow",  # Temporarily commented to fix FastAPI conflict
    # "NCEIWorkflowScheduler",  # Temporarily commented to fix FastAPI conflict
    # "create_ncei_scheduler",  # Temporarily commented to fix FastAPI conflict
    # "ncei_api_router",  # Commented out due to FastAPI import conflict
    # "AzureNCEIParquetModel",  # Commented out due to moose_lib/clickhouse conflicts
    # "AzureNCEIToFOCUSTransformer"  # Commented out due to dependency conflicts
]