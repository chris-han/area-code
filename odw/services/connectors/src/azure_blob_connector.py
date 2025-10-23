from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import pyarrow.parquet as pq


@dataclass
class AzureBlobFile:
    """Metadata describing a single parquet blob."""

    container_name: str
    blob_path: str
    absolute_path: Path
    size_bytes: int


@dataclass
class AzureBlobConnectorConfig:
    """
    Configuration for the Azure Blob connector.

    Attributes:
        account_url: Azure storage account URL. Optional when operating in local mode.
        sas_token: Shared access signature for authentication. Optional for local mode.
        containers: Containers to scan for parquet files.
        path_prefix: Optional prefix filter for blobs within each container.
        local_data_dir: Local directory used when running without Azure access.
        file_extension: File suffix to include (defaults to '.parquet').
    """

    account_url: Optional[str] = None
    sas_token: Optional[str] = None
    containers: Sequence[str] = ()
    path_prefix: Optional[str] = None
    local_data_dir: Optional[str] = None
    file_extension: str = ".parquet"


@dataclass
class AzureBlobRow:
    """Single record extracted from a parquet blob."""

    container_name: str
    blob_path: str
    row_index: int
    payload: Dict[str, object]


class AzureBlobConnector:
    """
    Lightweight Azure Blob Storage connector tailored for local development.

    The connector currently operates in a "local filesystem" mode that mirrors the blob
    layout on disk. This allows workflows to be exercised without live Azure credentials.
    If Azure dependencies are available, this class can be extended to stream directly
    from Azure Storage.
    """

    def __init__(self, config: AzureBlobConnectorConfig):
        self._config = config
        self._local_root = (
            Path(config.local_data_dir).resolve()
            if config.local_data_dir
            else None
        )

    # Public API -----------------------------------------------------------------

    def list_parquet_files(self) -> List[AzureBlobFile]:
        """Return all parquet files that match the configured containers/prefix."""

        if self._local_root is None:
            raise RuntimeError(
                "AzureBlobConnector requires `local_data_dir` in this environment. "
                "Provide Azure credentials and extend the connector to use "
                "`azure.storage.blob.BlobServiceClient` for live access."
            )

        containers = list(self._config.containers) or ["default"]
        discovered: List[AzureBlobFile] = []

        for container in containers:
            container_path = self._resolve_container_path(container)
            if not container_path.exists():
                continue

            for path in container_path.rglob(f"*{self._config.file_extension}"):
                if self._config.path_prefix:
                    relative = path.relative_to(container_path).as_posix()
                    if not relative.startswith(self._config.path_prefix):
                        continue

                blob_path = path.relative_to(container_path).as_posix()
                discovered.append(
                    AzureBlobFile(
                        container_name=container,
                        blob_path=blob_path,
                        absolute_path=path,
                        size_bytes=path.stat().st_size,
                    )
                )

        return discovered

    def iter_blob_rows(
        self,
        files: Optional[Sequence[AzureBlobFile]] = None,
    ) -> Iterable[AzureBlobRow]:
        """Yield rows across all matching blobs."""

        target_files = files or self.list_parquet_files()
        for blob in target_files:
            table = pq.read_table(blob.absolute_path)
            for row_index, payload in enumerate(self._table_rows(table)):
                yield AzureBlobRow(
                    container_name=blob.container_name,
                    blob_path=blob.blob_path,
                    row_index=row_index,
                    payload=payload,
                )

    def extract(self) -> List[AzureBlobRow]:
        """
        Extract all rows from available parquet blobs.

        Returns:
            A list of AzureBlobRow instances representing the flattened parquet contents.
        """

        return list(self.iter_blob_rows())

    # Internal helpers -----------------------------------------------------------

    def _resolve_container_path(self, container: str) -> Path:
        if self._local_root is None:
            raise RuntimeError("Local root directory is not configured.")
        candidate = self._local_root / container
        if candidate.exists():
            return candidate
        return self._local_root

    def _table_rows(self, table) -> Iterable[Dict[str, object]]:
        """
        Convert a PyArrow table to JSON-serializable dicts.

        PyArrow returns Arrow scalar types (Decimal128, Timestamp, etc.) which
        need to be normalised before we serialise them as JSON payloads.
        """

        for row in table.to_pylist():
            yield {key: self._normalise_value(value) for key, value in row.items()}

    @staticmethod
    def _normalise_value(value: object) -> object:
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8")
            except Exception:
                return value.hex()
        if isinstance(value, dict):
            return {k: AzureBlobConnector._normalise_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [AzureBlobConnector._normalise_value(v) for v in value]
        return value

    @staticmethod
    def serialise_payload(payload: Dict[str, object]) -> str:
        """Helper to turn payload dictionaries into JSON strings."""

        return json.dumps(payload, default=str)
