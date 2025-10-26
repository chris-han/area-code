"""
Moose Ingestion Adapter for FOCUS Billing Data

Replaces direct ClickHouse insertion with Moose HTTP API ingestion.
Transforms Parquet data into Pydantic model instances and sends to Moose.
"""

import hashlib
import httpx
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
import pandas as pd
from dataclasses import dataclass

from .data_transformer import TransformationResult
from .file_discovery import ParquetFileInfo
from .config import get_focus_config


@dataclass
class MooseIngestionResult:
    """Result of Moose ingestion operation"""
    success: bool
    rows_inserted: int
    batches_processed: int
    error_message: Optional[str] = None
    ingestion_stats: Optional[Dict[str, Any]] = None


class MooseIngestionAdapter:
    """
    Adapter for ingesting FOCUS data via Moose HTTP API.

    Converts transformed Parquet data into Pydantic model format
    and sends batches to Moose ingestion endpoint.
    """

    def __init__(self, batch_size: int = 1000, moose_url: str = "http://localhost:4200"):
        """
        Initialize Moose ingestion adapter.

        Args:
            batch_size: Number of records per batch
            moose_url: Base URL for Moose API
        """
        self.batch_size = batch_size
        self.moose_url = moose_url
        self.ingest_endpoint = f"{moose_url}/ingest/FocusCostUsage"

    async def ingest_transformed_data(
        self,
        transformation_result: TransformationResult,
        file_info: ParquetFileInfo,
        manifest_id: str
    ) -> MooseIngestionResult:
        """
        Ingest transformed data via Moose HTTP API.

        Args:
            transformation_result: Transformed data from data transformer
            file_info: Information about source file
            manifest_id: Tracking ID for manifest

        Returns:
            MooseIngestionResult with ingestion status
        """
        if not transformation_result.success or transformation_result.transformed_data is None:
            return MooseIngestionResult(
                success=False,
                rows_inserted=0,
                batches_processed=0,
                error_message="No valid transformed data to ingest"
            )

        df = transformation_result.transformed_data

        if df.empty:
            return MooseIngestionResult(
                success=True,
                rows_inserted=0,
                batches_processed=0
            )

        try:
            total_rows = len(df)
            batches_processed = 0
            rows_inserted = 0

            # Process in batches
            for start_idx in range(0, total_rows, self.batch_size):
                end_idx = min(start_idx + self.batch_size, total_rows)
                batch_df = df.iloc[start_idx:end_idx]

                # Convert batch to Moose format
                records = self._convert_batch_to_moose_format(batch_df)

                # Send to Moose API
                await self._send_batch_to_moose(records)

                batches_processed += 1
                rows_inserted += len(records)

            return MooseIngestionResult(
                success=True,
                rows_inserted=rows_inserted,
                batches_processed=batches_processed,
                ingestion_stats={
                    'total_batches': batches_processed,
                    'avg_batch_size': rows_inserted / batches_processed if batches_processed > 0 else 0
                }
            )

        except Exception as e:
            return MooseIngestionResult(
                success=False,
                rows_inserted=rows_inserted,
                batches_processed=batches_processed,
                error_message=f"Moose ingestion failed: {str(e)}"
            )

    def _convert_batch_to_moose_format(self, batch_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Convert DataFrame batch to list of dictionaries for Moose API.

        Args:
            batch_df: Batch of transformed data

        Returns:
            List of record dictionaries
        """
        records = []

        for _, row in batch_df.iterrows():
            record = {}

            for col in batch_df.columns:
                value = row[col]

                # Handle pandas NA/NaN/None
                if pd.isna(value):
                    record[col] = None
                    continue

                # Convert value to JSON-serializable type
                converted_value = self._convert_value_for_json(value, col)
                record[col] = converted_value

            # Generate deterministic ID if not present
            if 'id' not in record or not record['id']:
                record['id'] = self._generate_record_id(record)

            # Add audit fields if not present
            if 'source_system' not in record or not record['source_system']:
                record['source_system'] = 'focus_parquet'

            if 'ingested_at' not in record or not record['ingested_at']:
                record['ingested_at'] = datetime.utcnow().isoformat()

            records.append(record)

        return records

    def _convert_value_for_json(self, value: Any, column_name: str) -> Any:
        """
        Convert Python value to JSON-serializable format.

        Args:
            value: Value to convert
            column_name: Name of column (for type hints)

        Returns:
            JSON-serializable value
        """
        # Handle Decimal
        if isinstance(value, Decimal):
            # Convert to string, avoiding scientific notation for JSON
            # Use fixed-point notation for JSON compatibility
            return float(value)

        # Handle datetime
        if isinstance(value, (datetime, pd.Timestamp)):
            return value.isoformat()

        # Handle numpy/pandas numeric types
        if hasattr(value, 'item'):  # numpy scalar
            return value.item()

        # Handle boolean
        if isinstance(value, bool):
            return value

        # Handle string
        if isinstance(value, str):
            return value

        # Default: convert to string
        return str(value)

    def _generate_record_id(self, record: Dict[str, Any]) -> str:
        """
        Generate deterministic ID from record key fields.

        Uses: billing_account_id + charge_period_start + resource_id + sku_meter

        Args:
            record: Record dictionary

        Returns:
            Deterministic hash string
        """
        key_fields = [
            str(record.get('billing_account_id', '')),
            str(record.get('charge_period_start', '')),
            str(record.get('resource_id', '')),
            str(record.get('sku_meter', ''))
        ]

        key_string = '|'.join(key_fields)
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()

    async def _send_batch_to_moose(self, records: List[Dict[str, Any]]) -> None:
        """
        Send batch of records to Moose ingestion API.

        Args:
            records: List of record dictionaries

        Raises:
            Exception: If ingestion fails
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.ingest_endpoint,
                json=records,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code != 200:
                raise Exception(
                    f"Moose API returned status {response.status_code}: {response.text}"
                )

    def close(self) -> None:
        """Cleanup resources (no-op for HTTP client)"""
        pass


def create_moose_ingestion_adapter(batch_size: Optional[int] = None) -> MooseIngestionAdapter:
    """
    Factory function to create MooseIngestionAdapter with config defaults.

    Args:
        batch_size: Optional batch size override

    Returns:
        Configured MooseIngestionAdapter instance
    """
    config = get_focus_config()
    batch_size = batch_size or config.batch_size

    return MooseIngestionAdapter(batch_size=batch_size)
