"""
FOCUS Billing Observability and Metrics

Provides metrics emission, validation, and monitoring capabilities
for FOCUS billing data ingestion and processing.
"""

import time
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    import clickhouse_connect

from .config import get_focus_config


class MetricType(Enum):
    """Types of metrics that can be emitted"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """Represents a single metric measurement"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of a validation check"""
    check_name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FocusObservability:
    """
    Observability and metrics collection for FOCUS billing operations.
    
    Features:
    - Metrics emission (rows ingested, files processed, duration)
    - Table existence verification
    - Referential integrity validation
    - Performance monitoring
    """
    
    def __init__(self):
        """Initialize observability collector"""
        self.metrics: List[Metric] = []
        self.validation_results: List[ValidationResult] = []
        self.client = None
    
    def _get_client(self):
        """Get or create ClickHouse client"""
        if self.client is None:
            import clickhouse_connect
            self.client = clickhouse_connect.get_client(**get_focus_config().get_clickhouse_connection_params())
        return self.client
    
    def emit_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
        unit: Optional[str] = None
    ) -> None:
        """
        Emit a metric measurement.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            tags: Optional tags for the metric
            unit: Optional unit of measurement
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {},
            unit=unit
        )
        self.metrics.append(metric)
        
        # Log metric for immediate visibility
        tags_str = ", ".join(f"{k}={v}" for k, v in metric.tags.items()) if metric.tags else ""
        unit_str = f" {metric.unit}" if metric.unit else ""
        print(f"METRIC: {metric.name}={metric.value}{unit_str} [{metric.metric_type.value}] {tags_str}")
    
    def emit_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Emit a counter metric"""
        self.emit_metric(name, value, MetricType.COUNTER, tags)
    
    def emit_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, unit: Optional[str] = None) -> None:
        """Emit a gauge metric"""
        self.emit_metric(name, value, MetricType.GAUGE, tags, unit)
    
    def emit_timer(self, name: str, duration_seconds: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Emit a timer metric"""
        self.emit_metric(name, duration_seconds, MetricType.TIMER, tags, "seconds")
    
    def verify_table_exists(self, table_name: str) -> ValidationResult:
        """
        Verify that a table exists in ClickHouse.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            ValidationResult indicating if table exists
        """
        try:
            client = self._get_client()
            
            query = f"""
            SELECT 1 
            FROM system.tables 
            WHERE database = '{get_focus_config().clickhouse_database}' 
            AND name = '{table_name}'
            """
            
            result = client.query(query)
            exists = len(result.result_rows) > 0
            
            validation_result = ValidationResult(
                check_name=f"table_exists_{table_name}",
                passed=exists,
                message=f"Table {table_name} {'exists' if exists else 'does not exist'}",
                details={'table_name': table_name, 'database': get_focus_config().clickhouse_database}
            )
            
            self.validation_results.append(validation_result)
            self.emit_gauge(
                "focus.table.exists",
                1.0 if exists else 0.0,
                tags={'table': table_name}
            )
            
            return validation_result
            
        except Exception as e:
            validation_result = ValidationResult(
                check_name=f"table_exists_{table_name}",
                passed=False,
                message=f"Failed to check table existence: {str(e)}",
                details={'table_name': table_name, 'error': str(e)}
            )
            
            self.validation_results.append(validation_result)
            return validation_result
    
    def verify_tables_exist(self, table_names: List[str]) -> Dict[str, ValidationResult]:
        """
        Verify multiple tables exist.
        
        Args:
            table_names: List of table names to check
            
        Returns:
            Dict mapping table names to validation results
        """
        results = {}
        for table_name in table_names:
            results[table_name] = self.verify_table_exists(table_name)
        
        # Emit summary metric
        passed_count = sum(1 for result in results.values() if result.passed)
        self.emit_gauge(
            "focus.tables.verified",
            passed_count,
            tags={'total': str(len(table_names))}
        )
        
        return results
    
    def validate_contract_commitment_integrity(self) -> ValidationResult:
        """
        Validate referential integrity between cost_usage and contract_commitment tables.
        
        Returns:
            ValidationResult with integrity check status
        """
        try:
            client = self._get_client()
            
            # Check if both tables exist first
            cost_usage_exists = self.verify_table_exists(get_focus_config().cost_usage_table_name)
            commitment_exists = self.verify_table_exists(get_focus_config().contract_commitment_table_name)
            
            if not (cost_usage_exists.passed and commitment_exists.passed):
                return ValidationResult(
                    check_name="contract_commitment_integrity",
                    passed=False,
                    message="Cannot validate integrity: required tables do not exist",
                    details={
                        'cost_usage_exists': cost_usage_exists.passed,
                        'commitment_exists': commitment_exists.passed
                    }
                )
            
            # Find contract_commitment_ids in cost_usage that don't exist in contract_commitment
            orphaned_query = f"""
            SELECT COUNT(*) as orphaned_count
            FROM {get_focus_config().cost_usage_table_name} cu
            LEFT JOIN {get_focus_config().contract_commitment_table_name} cc 
                ON cu.contract_commitment_id = cc.contract_commitment_id
            WHERE cu.contract_commitment_id IS NOT NULL 
            AND cc.contract_commitment_id IS NULL
            """
            
            orphaned_result = client.query(orphaned_query)
            orphaned_count = orphaned_result.result_rows[0][0] if orphaned_result.result_rows else 0
            
            # Get total count of cost_usage records with contract_commitment_id
            total_query = f"""
            SELECT COUNT(*) as total_count
            FROM {get_focus_config().cost_usage_table_name}
            WHERE contract_commitment_id IS NOT NULL
            """
            
            total_result = client.query(total_query)
            total_count = total_result.result_rows[0][0] if total_result.result_rows else 0
            
            # Calculate integrity percentage
            integrity_percentage = 100.0 if total_count == 0 else ((total_count - orphaned_count) / total_count) * 100
            
            validation_result = ValidationResult(
                check_name="contract_commitment_integrity",
                passed=orphaned_count == 0,
                message=f"Found {orphaned_count} orphaned contract_commitment_id references out of {total_count} total ({integrity_percentage:.1f}% integrity)",
                details={
                    'orphaned_count': orphaned_count,
                    'total_count': total_count,
                    'integrity_percentage': integrity_percentage
                }
            )
            
            self.validation_results.append(validation_result)
            
            # Emit metrics
            self.emit_gauge("focus.integrity.orphaned_commitments", orphaned_count)
            self.emit_gauge("focus.integrity.total_commitments", total_count)
            self.emit_gauge("focus.integrity.percentage", integrity_percentage, unit="percent")
            
            return validation_result
            
        except Exception as e:
            validation_result = ValidationResult(
                check_name="contract_commitment_integrity",
                passed=False,
                message=f"Failed to validate contract commitment integrity: {str(e)}",
                details={'error': str(e)}
            )
            
            self.validation_results.append(validation_result)
            return validation_result
    
    def get_table_row_counts(self, table_names: List[str]) -> Dict[str, int]:
        """
        Get row counts for multiple tables.
        
        Args:
            table_names: List of table names
            
        Returns:
            Dict mapping table names to row counts
        """
        row_counts = {}
        
        try:
            client = self._get_client()
            
            for table_name in table_names:
                try:
                    query = f"SELECT COUNT(*) FROM {table_name}"
                    result = client.query(query)
                    count = result.result_rows[0][0] if result.result_rows else 0
                    row_counts[table_name] = count
                    
                    # Emit metric
                    self.emit_gauge(
                        "focus.table.row_count",
                        count,
                        tags={'table': table_name}
                    )
                    
                except Exception as e:
                    print(f"Warning: Failed to get row count for {table_name}: {e}")
                    row_counts[table_name] = -1
            
        except Exception as e:
            print(f"Warning: Failed to connect to ClickHouse for row counts: {e}")
        
        return row_counts
    
    def measure_ingestion_performance(
        self,
        rows_processed: int,
        files_processed: int,
        duration_seconds: float,
        dataset_type: Optional[str] = None
    ) -> None:
        """
        Measure and emit ingestion performance metrics.
        
        Args:
            rows_processed: Number of rows processed
            files_processed: Number of files processed
            duration_seconds: Total processing duration
            dataset_type: Optional dataset type for tagging
        """
        tags = {'dataset_type': dataset_type} if dataset_type else {}
        
        # Basic counts
        self.emit_gauge("focus.ingestion.rows_processed", rows_processed, tags)
        self.emit_gauge("focus.ingestion.files_processed", files_processed, tags)
        self.emit_timer("focus.ingestion.duration", duration_seconds, tags)
        
        # Performance rates
        if duration_seconds > 0:
            rows_per_second = rows_processed / duration_seconds
            files_per_second = files_processed / duration_seconds
            
            self.emit_gauge("focus.ingestion.rows_per_second", rows_per_second, tags, "rows/sec")
            self.emit_gauge("focus.ingestion.files_per_second", files_per_second, tags, "files/sec")
        
        if files_processed > 0:
            avg_rows_per_file = rows_processed / files_processed
            self.emit_gauge("focus.ingestion.avg_rows_per_file", avg_rows_per_file, tags, "rows/file")
    
    def run_comprehensive_validation(self) -> Dict[str, ValidationResult]:
        """
        Run all validation checks and return results.
        
        Returns:
            Dict mapping check names to validation results
        """
        print("Running comprehensive FOCUS billing validation...")
        
        validation_start = time.time()
        results = {}
        
        # Check core tables exist
        core_tables = [
            get_focus_config().cost_usage_table_name,
            get_focus_config().contract_commitment_table_name,
            get_focus_config().manifest_table_name
        ]
        
        table_results = self.verify_tables_exist(core_tables)
        results.update(table_results)
        
        # Check referential integrity
        integrity_result = self.validate_contract_commitment_integrity()
        results[integrity_result.check_name] = integrity_result
        
        # Get row counts for monitoring
        row_counts = self.get_table_row_counts(core_tables)
        print(f"Table row counts: {row_counts}")
        
        # Emit validation summary metrics
        validation_duration = time.time() - validation_start
        passed_count = sum(1 for result in results.values() if result.passed)
        total_count = len(results)
        
        self.emit_timer("focus.validation.duration", validation_duration)
        self.emit_gauge("focus.validation.checks_passed", passed_count)
        self.emit_gauge("focus.validation.checks_total", total_count)
        self.emit_gauge("focus.validation.success_rate", (passed_count / total_count) * 100 if total_count > 0 else 0, unit="percent")
        
        print(f"Validation completed: {passed_count}/{total_count} checks passed in {validation_duration:.2f}s")
        
        return results
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of all collected metrics.
        
        Returns:
            Dict with metrics summary
        """
        if not self.metrics:
            return {'total_metrics': 0}
        
        summary = {
            'total_metrics': len(self.metrics),
            'by_type': {},
            'latest_timestamp': max(m.timestamp for m in self.metrics),
            'earliest_timestamp': min(m.timestamp for m in self.metrics)
        }
        
        # Group by metric type
        for metric in self.metrics:
            metric_type = metric.metric_type.value
            if metric_type not in summary['by_type']:
                summary['by_type'][metric_type] = []
            summary['by_type'][metric_type].append({
                'name': metric.name,
                'value': metric.value,
                'timestamp': metric.timestamp,
                'tags': metric.tags,
                'unit': metric.unit
            })
        
        return summary
    
    def close(self) -> None:
        """Close ClickHouse connection"""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None


# Context manager for timed operations
class TimedOperation:
    """Context manager for measuring operation duration"""
    
    def __init__(self, observability: FocusObservability, metric_name: str, tags: Optional[Dict[str, str]] = None):
        self.observability = observability
        self.metric_name = metric_name
        self.tags = tags or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.observability.emit_timer(self.metric_name, duration, self.tags)


# Global observability instance
focus_observability = FocusObservability()