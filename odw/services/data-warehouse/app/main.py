"""
Main Moose Application Entry Point (app/main.py)

⚠️ NOTE: This file MUST be named 'main.py' for Moose CLI compatibility.
The Moose CLI (`moose dev`, `moose build`, etc.) looks for this module.

This module is responsible for registering Moose-managed components only:
1. Moose data models and transformations
2. Moose ingestion pipelines and workflows
3. Moose materialized views
4. Moose Consumption APIs (including the bia analytics endpoints implemented with `ConsumptionApi`)

General-purpose FastAPI routes now live in `bia_backend/` and are served separately
on port 4300. This `app` object remains a bare FastAPI instance so tooling that
expects `app.main:app` continues to work, but no additional routers are mounted here.
"""

from fastapi import FastAPI

# Moose data models and transformations
from app.ingest import models, transforms

# Moose workflows for data extraction
from app.blobs.extract import blob_workflow, blob_task
from app.logs.extract import logs_workflow, logs_task
from app.events.extract import events_workflow, events_task
from app.unstructured_data.extract import (
    unstructured_data_workflow,
    unstructured_data_task
)

# Moose materialized views
from app.views.daily_pageviews import daily_pageviews_mv

# Moose consumption APIs (data retrieval)
import app.apis.get_blobs
import app.apis.get_logs
import app.apis.get_events
import app.apis.get_daily_pageviews
import app.apis.get_unstructured_data
import app.apis.get_medical

# Moose ingestion APIs (data extraction/processing)
import app.apis.extract_blob
import app.apis.extract_logs
import app.apis.extract_events
import app.apis.extract_unstructured_data
import app.azure_billing.workflows.azure_blob_ingest_workflow  # noqa: F401

# Bare FastAPI application for Moose-managed endpoints. Moose CLI mounts
# ingestion and consumption routes automatically; no bespoke routers are added here.
app = FastAPI(
    title="Moose Analytics Service",
    description="Moose-managed ingestion and consumption APIs (no general FastAPI routes).",
    version="1.0.0",
)

__all__ = [
    'app',  # FastAPI application
    'models',
    'transforms',
    'blob_workflow',
    'blob_task',
    'logs_workflow',
    'logs_task',
    'events_workflow',
    'events_task',
    'unstructured_data_workflow',
    'unstructured_data_task',
    'daily_pageviews_mv',
]
