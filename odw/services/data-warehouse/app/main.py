# Main entry point for moose. Moose reads these imports & figures out
# which infrastructure to setup.

from app.ingest import models, transforms
from app.blobs.extract import blob_workflow, blob_task
from app.logs.extract import logs_workflow, logs_task
from app.events.extract import events_workflow, events_task
from app.unstructured_data.extract import unstructured_data_workflow, unstructured_data_task
from app.views.daily_pageviews import daily_pageviews_mv

# Import existing APIs
import app.moose_apis.get_blobs
import app.moose_apis.get_logs
import app.moose_apis.extract_blob
import app.moose_apis.extract_logs
import app.moose_apis.extract_events
import app.moose_apis.get_events
import app.moose_apis.get_daily_pageviews
import app.moose_apis.extract_unstructured_data
import app.moose_apis.get_unstructured_data
import app.moose_apis.get_medical

# Import ABI APIs - this registers them with Moose
import app.abi
