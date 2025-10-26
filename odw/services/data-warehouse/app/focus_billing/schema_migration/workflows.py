"""Temporal workflows for schema migration."""

from datetime import timedelta
from temporalio import workflow

from .activities import (
    detect_schema_diff,
    generate_transformation_code,
    apply_transformation_and_load_data
)


@workflow.defn
class SchemaMigrationWorkflow:
    """Detects schema drift and applies transformations."""

    @workflow.run
    async def run(
        self,
        source_parquet_path: str,
        canonical_schema_path: str,
        current_version: str = "0_0"
    ) -> dict:
        """
        Main workflow execution:
        1. Detect schema differences
        2. Generate transformation code if needed
        3. Apply migration and load data

        Args:
            source_parquet_path: Path to sample Parquet file for schema inference
            canonical_schema_path: Path to FOCUS spec datasets directory
            current_version: Current schema version (default: "0_0")

        Returns:
            Dictionary with migration result:
            {
                "migration_needed": bool,
                "version": str,
                "old_version": str (if migrated),
                "new_version": str (if migrated),
                "diff": dict (if migrated),
                "rows_migrated": int (if migrated)
            }
        """
        workflow.logger.info(
            f"Starting schema migration workflow: "
            f"source={source_parquet_path}, version={current_version}"
        )

        diff_dict = await workflow.execute_activity(
            detect_schema_diff,
            args=[source_parquet_path, canonical_schema_path, current_version],
            start_to_close_timeout=timedelta(minutes=5)
        )

        if not diff_dict['requires_migration']:
            workflow.logger.info("No schema drift detected, using existing version")
            return {
                "migration_needed": False,
                "version": current_version
            }

        workflow.logger.info(
            f"Schema drift detected, migrating to version {diff_dict['new_version']}"
        )

        transform_code = await workflow.execute_activity(
            generate_transformation_code,
            args=[diff_dict],
            start_to_close_timeout=timedelta(minutes=10)
        )

        workflow.logger.info(f"Generated transformation code ({len(transform_code)} bytes)")

        migration_result = await workflow.execute_activity(
            apply_transformation_and_load_data,
            args=[transform_code, diff_dict['new_version']],
            start_to_close_timeout=timedelta(hours=1)
        )

        workflow.logger.info(
            f"Migration complete: {migration_result['rows_migrated']} rows migrated"
        )

        return {
            "migration_needed": True,
            "old_version": current_version,
            "new_version": diff_dict['new_version'],
            "diff": diff_dict,
            "rows_migrated": migration_result.get("rows_migrated", 0),
            "status": migration_result.get("status", "unknown")
        }
