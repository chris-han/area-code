# Main entry point for moose. Moose reads these imports & figures out
# which infrastructure to setup.

from app.ingest import models, transforms
from app.blobs.extract import blob_workflow, blob_task
from app.logs.extract import logs_workflow, logs_task
from app.events.extract import events_workflow, events_task
from app.unstructured_data.extract import (
    unstructured_data_workflow,
    unstructured_data_task,
)
from app.azure_billing.extract import azure_billing_workflow, azure_billing_task
from app.views.daily_pageviews import daily_pageviews_mv


import app.apis.get_blobs
import app.apis.get_logs
import app.apis.extract_blob
import app.apis.extract_logs
import app.apis.extract_events
import app.apis.get_events
import app.apis.get_daily_pageviews
import app.apis.extract_unstructured_data
import app.apis.get_unstructured_data
import app.apis.get_medical
import app.apis.get_workflows
import app.apis.extract_azure_billing
import app.apis.get_azure_billing
import app.apis.get_azure_billing_summary
import app.apis.get_azure_subscriptions
import app.apis.get_azure_resource_groups
import app.apis.test_azure_connection
