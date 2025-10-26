from app.ingest.models import LogSource
from app.utils.simulator import simulate_failures
# from connectors.connector_factory import ConnectorFactory, ConnectorType
# from connectors.logs_connector import LogsConnectorConfig
from moose_lib import Task, TaskConfig, Workflow, WorkflowConfig, cli_log, CliLogData
from pydantic import BaseModel
from typing import Optional
import requests
import json

# This workflow extracts Logs data and sends it to the ingest API.
# For more information on workflows, see: https://docs.fiveonefour.com/moose/building/workflows.
#
# You may also direct insert into the table: https://docs.fiveonefour.com/moose/building/olap-table#direct-data-insertion.
#
# When the data lands in ingest, it goes through a stream where it is transformed.
# See app/ingest/transforms.py for the transformation logic.

class LogsExtractParams(BaseModel):
    batch_size: Optional[int] = 100
    fail_percentage: Optional[int] = 0

def run_task(input: LogsExtractParams) -> None:
    cli_log(CliLogData(action="LogsWorkflow", message="Logs workflow disabled - connectors module not available", message_type="Info"))

logs_task = Task[LogsExtractParams, None](
    name="logs-task",
    config=TaskConfig(run=run_task)
)

logs_workflow = Workflow(
    name="logs-workflow",
    config=WorkflowConfig(starting_task=logs_task)
)
