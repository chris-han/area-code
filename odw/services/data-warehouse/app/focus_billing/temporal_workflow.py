"""Temporal workflow adaptation for the Focus Billing ingestion pipeline."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict

from temporalio import activity, workflow
from temporalio.common import RetryPolicy

from .workflow import FocusBillingIngestParams, FocusBillingIngestWorkflow


logger = logging.getLogger(__name__)


def _stats_to_dict(stats) -> Dict[str, Any]:
    """Convert ``WorkflowStats`` into a JSON-serialisable dictionary."""

    return {
        "files_discovered": stats.files_discovered,
        "files_processed": stats.files_processed,
        "files_skipped": stats.files_skipped,
        "files_failed": stats.files_failed,
        "total_rows_processed": stats.total_rows_processed,
        "total_processing_time": stats.total_processing_time,
        "errors": list(stats.errors or []),
    }


@activity.defn
async def run_focus_billing_ingest_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """Temporal activity that executes the Focus Billing ingestion workflow."""

    params_obj = FocusBillingIngestParams(**params)
    workflow_obj = FocusBillingIngestWorkflow(params_obj)

    logger.info("Starting Focus Billing ingestion activity")
    stats = await asyncio.to_thread(workflow_obj.execute)
    logger.info(
        "Focus Billing ingestion activity completed: %s files processed, %s rows",
        stats.files_processed,
        stats.total_rows_processed,
    )

    return _stats_to_dict(stats)


@workflow.defn
class FocusBillingTemporalWorkflow:
    """Temporal workflow wrapper that runs the Focus Billing ingestion pipeline."""

    @workflow.run
    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Focus Billing Temporal workflow started")

        result = await workflow.execute_activity(
            run_focus_billing_ingest_activity,
            args=[params],
            start_to_close_timeout=timedelta(hours=3),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=10),
                maximum_interval=timedelta(minutes=5),
                backoff_coefficient=2.0,
                maximum_attempts=3,
            ),
        )

        logger.info("Focus Billing Temporal workflow finished")
        return result

