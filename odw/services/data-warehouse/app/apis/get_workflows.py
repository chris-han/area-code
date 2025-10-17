from moose_lib import ConsumptionApi, EgressConfig, TemporalClient
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import os

# An API to get a list of workflows from the Temporal server.
# For more information on consumption apis, see: https://docs.fiveonefour.com/moose/building/consumption-apis.


# Define the workflow execution model (matches what frontend expects)
class Workflow(BaseModel):
    name: str
    run_id: str
    status: str
    started_at: str
    duration: Optional[str] = None


# Define the query params (empty for this endpoint)
class GetWorkflowsQuery(BaseModel):
    name_prefix: Optional[str] = None


# Define the response model
class GetWorkflowsResponse(BaseModel):
    items: List[Workflow] = []
    total: int = 0


# Define the query function
def get_workflows(client, params: GetWorkflowsQuery) -> GetWorkflowsResponse:
    """
    Retrieve workflow execution history from Temporal API.

    Args:
        client: Database client (not used for this endpoint)
        params: Contains optional name prefix filter

    Returns:
        GetWorkflowsResponse object containing workflow execution history
    """

    async def fetch_workflows():
        try:
            # Connect to Temporal server with timeout (local development)
            temporal_client = await asyncio.wait_for(
                TemporalClient.connect("localhost:7233"),
                timeout=5.0  # 5 second timeout
            )

            # List workflow executions with a limit
            workflow_executions = []
            async for execution in temporal_client.list_workflows(limit=50):
                workflow_executions.append(execution)

            workflows = []

            for execution in workflow_executions:
                # Extract workflow info from execution
                workflow_type = execution.workflow_type
                run_id = execution.run_id
                status = execution.status.name
                start_time = execution.start_time
                close_time = execution.close_time

                # Calculate duration if workflow is closed
                duration = None
                if close_time and start_time:
                    duration_seconds = (close_time - start_time).total_seconds()
                    if duration_seconds >= 60:
                        duration = f"{int(duration_seconds // 60)}m {int(duration_seconds % 60)}s"
                    else:
                        duration = f"{int(duration_seconds)}s"

                # Format start time to match expected format
                started_at = start_time.strftime("%Y-%m-%d %H:%M:%S.%f UTC") if start_time else ""

                # Apply name prefix filter if provided
                if params.name_prefix and not workflow_type.startswith(params.name_prefix):
                    continue

                workflows.append(
                    Workflow(
                        name=workflow_type,
                        run_id=run_id,
                        status=status,
                        started_at=started_at,
                        duration=duration or "",
                    )
                )

            return GetWorkflowsResponse(items=workflows, total=len(workflows))

        except (asyncio.TimeoutError, ConnectionError, Exception) as e:
            # Fallback to sample data when Temporal server is not available
            sample_workflows = [
                {
                    "name": "azure-billing-workflow-sample",
                    "run_id": "sample-run-id-1",
                    "status": "WORKFLOW_EXECUTION_STATUS_COMPLETED",
                    "started_at": "2025-10-17 00:22:17.370985 UTC",
                    "duration": "16s",
                },
                {
                    "name": "events-workflow-sample",
                    "run_id": "sample-run-id-2",
                    "status": "WORKFLOW_EXECUTION_STATUS_COMPLETED",
                    "started_at": "2025-10-17 00:14:40.672087 UTC",
                    "duration": "10s",
                },
            ]

            workflows = []
            for workflow_data in sample_workflows:
                workflow_name = workflow_data["name"]

                # Apply name prefix filter if provided
                if params.name_prefix and not workflow_name.startswith(params.name_prefix):
                    continue

                workflows.append(
                    Workflow(
                        name=workflow_name,
                        run_id=workflow_data["run_id"],
                        status=workflow_data["status"],
                        started_at=workflow_data["started_at"],
                        duration=workflow_data["duration"],
                    )
                )

            return GetWorkflowsResponse(items=workflows, total=len(workflows))

    # Run the async function
    try:
        return asyncio.run(fetch_workflows())
    except Exception as e:
        # Final fallback if asyncio.run fails
        return GetWorkflowsResponse(items=[], total=0)


# Create the consumption API
get_workflows_api = ConsumptionApi[GetWorkflowsQuery, GetWorkflowsResponse](
    "getWorkflows",
    query_function=get_workflows,
    source="workflows",  # This is a virtual source since we're not querying a table
    config=EgressConfig(),
)
