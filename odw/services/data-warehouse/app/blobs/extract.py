from app.ingest.models import BlobSource
from app.utils.simulator import simulate_failures
from connectors.connector_factory import ConnectorFactory, ConnectorType
from connectors.blob_connector import BlobConnectorConfig
from moose_lib import Task, TaskConfig, Workflow, WorkflowConfig, cli_log, CliLogData, TaskContext
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

def run_task(context: TaskContext[BlobExtractParams]) -> None:
    cli_log(CliLogData(action="BlobWorkflow", message="Running Blob task...", message_type="Info"))

    # Create a connector to extract data from Blob
    connector = ConnectorFactory[BlobSource].create(
        ConnectorType.Blob,
        BlobConnectorConfig(batch_size=context.input.batch_size)
    )

    # Extract data from Blob
    data = connector.extract()

    cli_log(CliLogData(
        action="BlobWorkflow",
        message=f"Extracted {len(data)} items",
        message_type="Info"
    ))

    failed_count = simulate_failures(data, context.input.fail_percentage)
    if failed_count > 0:
        cli_log(CliLogData(
            action="BlobWorkflow",
            message=f"Marked {failed_count} items ({context.input.fail_percentage}%) as failed",
            message_type="Info"
        ))

    data_dicts = [item.model_dump() for item in data]
    
    try:
        response = requests.post(
            "http://localhost:4200/ingest/BlobSource",
            json=data_dicts,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        cli_log(CliLogData(
            action="BlobWorkflow",
            message=f"Successfully sent {len(data)} items to ingest API",
            message_type="Info"
        ))
    except Exception as e:
        cli_log(CliLogData(
            action="BlobWorkflow",
            message=f"Failed to send data to ingest API: {str(e)}",
            message_type="Error"
        ))

blob_task = Task[BlobExtractParams, None](
    name="blob-task",
    config=TaskConfig(run=run_task)
)

blob_workflow = Workflow(
    name="blob-workflow",
    config=WorkflowConfig(starting_task=blob_task)
)
