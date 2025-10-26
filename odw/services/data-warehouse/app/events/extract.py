from app.ingest.models import EventSource
from app.utils.simulator import simulate_failures
# from connectors.connector_factory import ConnectorFactory, ConnectorType
# from connectors.events_connector import EventsConnectorConfig
from moose_lib import Task, TaskConfig, Workflow, WorkflowConfig, cli_log, CliLogData
from pydantic import BaseModel
from typing import Optional
import requests
import json

# This workflow extracts Events data and sends it to the ingest API.
# For more information on workflows, see: https://docs.fiveonefour.com/moose/building/workflows.
#
# You may also direct insert into the table: https://docs.fiveonefour.com/moose/building/olap-table#direct-data-insertion.
#
# When the data lands in ingest, it goes through a stream where it is transformed.
# See app/ingest/transforms.py for the transformation logic.

class EventsExtractParams(BaseModel):
    batch_size: Optional[int] = 100
    fail_percentage: Optional[int] = 0

def run_task(input: EventsExtractParams) -> None:
    cli_log(CliLogData(action="EventsWorkflow", message="Events workflow disabled - connectors module not available", message_type="Info"))
    # TODO: Implement connector-based extraction when connectors module is available

events_task = Task[EventsExtractParams, None](
    name="events-task",
    config=TaskConfig(run=run_task)
)

events_workflow = Workflow(
    name="events-workflow",
    config=WorkflowConfig(starting_task=events_task)
) 