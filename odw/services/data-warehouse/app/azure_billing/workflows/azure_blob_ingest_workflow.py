from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import requests
from moose_lib import CliLogData, Task, TaskConfig, Workflow, WorkflowConfig, cli_log
from pydantic import BaseModel, Field

from app.azure_billing.plugins.marketplace_api import get_azure_blob_plugin_metadata
from app.ingest.models import AzureBlobStagingRecord
from connectors.azure_blob_connector import (
    AzureBlobConnector,
    AzureBlobConnectorConfig,
    AzureBlobRow,
)

DEFAULT_LOCAL_DATA_DIR = Path(__file__).resolve().parents[2] / "blobs"
DEFAULT_INGEST_ENDPOINT = "http://localhost:4200"


class AzureBlobIngestParams(BaseModel):
    """
    Runtime parameters for the Azure Blob ingestion workflow.

    Values default to environment variables to keep the workflow compatible with
    existing plugin metadata and the bia plugin configuration UX.
    """

    account_url: Optional[str] = Field(
        default=None, description="Azure Storage account URL (includes https://)."
    )
    sas_token: Optional[str] = Field(
        default=None, description="Shared access signature for Azure Storage."
    )
    containers: Optional[List[str]] = Field(
        default=None,
        description="Containers to scan for parquet files. Comma-separated string is also accepted.",
    )
    path_prefix: Optional[str] = Field(
        default=None,
        description="Optional path prefix (virtual folder) to scope parquet discovery.",
    )
    local_data_dir: Optional[str] = Field(
        default=None,
        description="Local directory mirroring blob contents for offline development.",
    )
    max_files: Optional[int] = Field(
        default=None,
        description="Optional cap on the number of parquet files processed per run.",
    )
    ingest_endpoint: Optional[str] = Field(
        default=None,
        description="Base URL for Moose ingest API (defaults to http://localhost:4200).",
    )

    def resolved_containers(self) -> List[str]:
        if isinstance(self.containers, str):
            return [c.strip() for c in self.containers.split(",") if c.strip()]

        if self.containers:
            return self.containers

        env_value = os.getenv("AZURE_BLOB_CONTAINERS")
        if env_value:
            return [c.strip() for c in env_value.split(",") if c.strip()]

        # Fall back to the metadata-required singular field name
        single_container = os.getenv("AZURE_BLOB_CONTAINER_NAME")
        if single_container:
            return [single_container]

        # Use a sensible default that matches the sample assets
        return ["focus-data"]

    def resolved_account_url(self) -> Optional[str]:
        return self.account_url or os.getenv("AZURE_BLOB_ACCOUNT_URL")

    def resolved_sas_token(self) -> Optional[str]:
        return self.sas_token or os.getenv("AZURE_BLOB_SAS_TOKEN")

    def resolved_path_prefix(self) -> Optional[str]:
        return self.path_prefix or os.getenv("AZURE_BLOB_PATH_PREFIX")

    def resolved_local_dir(self) -> Path:
        candidate = self.local_data_dir or os.getenv("AZURE_BLOB_LOCAL_PATH")
        if candidate:
            return Path(candidate).expanduser().resolve()
        return DEFAULT_LOCAL_DATA_DIR

    def resolved_ingest_endpoint(self) -> str:
        return (
            self.ingest_endpoint
            or os.getenv("MOOSE_INGEST_BASE_URL")
            or DEFAULT_INGEST_ENDPOINT
        )


def _validate_against_metadata(params: AzureBlobIngestParams) -> None:
    """Ensure required metadata fields are present using plugin metadata."""

    metadata = get_azure_blob_plugin_metadata()
    required_fields = (metadata.configSchema or {}).get("required", [])

    provided: Dict[str, Optional[str]] = {
        "accountUrl": params.resolved_account_url(),
        "sasToken": params.resolved_sas_token(),
        # The marketplace schema expresses this as a single container
        "containerName": next(iter(params.resolved_containers()), None),
    }

    missing = [field for field in required_fields if not provided.get(field)]
    if missing:
        raise ValueError(
            "Azure Blob connector is missing required configuration fields: "
            + ", ".join(missing)
        )


def _build_connector(params: AzureBlobIngestParams) -> AzureBlobConnector:
    config = AzureBlobConnectorConfig(
        account_url=params.resolved_account_url(),
        sas_token=params.resolved_sas_token(),
        containers=params.resolved_containers(),
        path_prefix=params.resolved_path_prefix(),
        local_data_dir=str(params.resolved_local_dir()),
    )
    return AzureBlobConnector(config)


def _rows_to_ingest_payload(rows: List[AzureBlobRow]) -> List[Dict[str, object]]:
    payload: List[Dict[str, object]] = []
    ingested_at = datetime.now(timezone.utc).isoformat()

    for row in rows:
        record = AzureBlobStagingRecord(
            id=f"{row.container_name}:{row.blob_path}:{row.row_index}",
            container_name=row.container_name,
            blob_path=row.blob_path,
            record_index=row.row_index,
            payload_json=AzureBlobConnector.serialise_payload(row.payload),
            ingested_at=ingested_at,
        )
        payload.append(record.model_dump())
    return payload


def _send_to_ingest(endpoint: str, payload: List[Dict[str, object]]) -> None:
    ingest_url = f"{endpoint.rstrip('/')}/ingest/AzureBlobStaging"
    response = requests.post(
        ingest_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    response.raise_for_status()


def execute_azure_blob_ingest(params: AzureBlobIngestParams) -> Dict[str, object]:
    """Shared execution helper for Moose tasks and Temporal activities."""

    _validate_against_metadata(params)
    connector = _build_connector(params)

    files = connector.list_parquet_files()
    if params.max_files is not None:
        files = files[: params.max_files]

    rows = list(connector.iter_blob_rows(files))
    if not rows:
        return {
            "containers": params.resolved_containers(),
            "files_discovered": len(files),
            "rows_ingested": 0,
        }

    ingest_payload = _rows_to_ingest_payload(rows)
    _send_to_ingest(params.resolved_ingest_endpoint(), ingest_payload)

    return {
        "containers": params.resolved_containers(),
        "files_discovered": len(files),
        "rows_ingested": len(ingest_payload),
    }


def run_task(params: AzureBlobIngestParams) -> None:
    cli_log(
        CliLogData(
            action="AzureBlobIngest",
            message="Starting Azure Blob ingestion workflow",
            message_type="Info",
        )
    )

    result = execute_azure_blob_ingest(params)

    cli_log(
        CliLogData(
            action="AzureBlobIngest",
            message=(
                f"Discovered {result['files_discovered']} parquet file(s) across "
                f"containers {', '.join(result['containers'])}"
            ),
            message_type="Info",
        )
    )

    if result["rows_ingested"] == 0:
        cli_log(
            CliLogData(
                action="AzureBlobIngest",
                message="No parquet rows discovered – nothing to ingest.",
                message_type="Warning",
            )
        )
        return

    cli_log(
        CliLogData(
            action="AzureBlobIngest",
            message=f"Ingested {result['rows_ingested']} rows into AzureBlobStaging",
            message_type="Success",
        )
    )


azure_blob_ingest_task = Task[AzureBlobIngestParams, None](
    name="azure-blob-ingest-task",
    config=TaskConfig(run=run_task),
)

azure_blob_ingest_workflow = Workflow(
    name="azure-blob-ingest-workflow",
    config=WorkflowConfig(starting_task=azure_blob_ingest_task),
)
