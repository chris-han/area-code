from app.ingest.models import BlobSource
from app.utils.simulator import simulate_failures
# from connectors.connector_factory import ConnectorFactory, ConnectorType
# from connectors.blob_connector import BlobConnectorConfig
from moose_lib import Task, TaskConfig, Workflow, WorkflowConfig, cli_log, CliLogData
from pydantic import BaseModel
from typing import Optional
import requests
import json

# This workflow extracts Blob data and sends it to the ingest API.
# For more information on workflows, see: https://docs.fiveonefour.com/moose/building/workflows.
#
# You may also direct insert into the table: https://docs.fiveonefour.com/moose/building/olap-table#direct-data-insertion.
#
# When the data lands in ingest, it goes through a stream where it is transformed.
# See app/ingest/transforms.py for the transformation logic.

class BlobExtractParams(BaseModel):
    batch_size: Optional[int] = 100
    fail_percentage: Optional[int] = 0

def run_task(input: BlobExtractParams) -> None:
    cli_log(CliLogData(action="BlobWorkflow", message="Blob workflow disabled - connectors module not available", message_type="Info"))
    # TODO: Implement connector-based extraction when connectors module is available
    # connector = ConnectorFactory[BlobSource].create(
    #     ConnectorType.Blob,
    #     BlobConnectorConfig(batch_size=input.batch_size)
    # )
    # data = connector.extract()

blob_task = Task[BlobExtractParams, None](
    name="blob-task",
    config=TaskConfig(run=run_task)
)

blob_workflow = Workflow(
    name="blob-workflow",
    config=WorkflowConfig(starting_task=blob_task)
)
