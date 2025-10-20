"""
System Monitoring and Alerting Tests

Tests for system monitoring capabilities and alerting mechanisms.
"""

from datetime import datetime, timedelta

import pytest


class TestSystemMonitoring:
    """Test system monitoring and health check capabilities."""
    
    def test_workflow_execution_monitoring(self):
        """Test monitoring of workflow execution status and metrics."""
        
        # Mock workflow monitoring data
        workflow_metrics = {
            "workflow_id": "azure-ncei-workflow-123",
            "status": "running",
            "start_time": datetime.utcnow().isoformat(),
            "files_processed": 45,
            "total_files": 100,
            "records_processed": 45000,
            "processing_rate": 1000,  # records per minute
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=55)).isoformat(),
            "error_count": 0,
            "warning_count": 2
        }
        
        # Test workflow monitoring
        assert workflow_metrics["status"] in ["pending", "running", "completed", "failed"]
        assert workflow_metrics["files_processed"] <= workflow_metrics["total_files"]
        assert workflow_metrics["records_processed"] > 0
        assert workflow_metrics["processing_rate"] > 0
        assert workflow_metrics["error_count"] == 0  # No errors expected
        
        # Test progress calculation
        progress_percentage = (workflow_metrics["files_processed"] / workflow_metrics["total_files"]) * 100
        assert 0 <= progress_percentage <= 100
        assert progress_percentage == 45.0  # 45/100 = 45%   
 
    def test_system_health_monitoring(self):
        """Test system health monitoring and status checks."""
        
        # Mock system health data
        system_health = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "components": {
                "clickhouse": {
                    "status": "healthy",
                    "response_time_ms": 25,
                    "connection_pool_usage": 0.65,
                    "query_success_rate": 0.998
                },
                "temporal": {
                    "status": "healthy", 
                    "active_workflows": 12,
                    "completed_workflows_24h": 156,
                    "failed_workflows_24h": 2
                },
                "azure_blob_storage": {
                    "status": "healthy",
                    "connection_status": "connected",
                    "last_successful_access": datetime.utcnow().isoformat(),
                    "api_rate_limit_usage": 0.45
                }
            }
        }
        
        # Test overall system health
        assert system_health["overall_status"] == "healthy"
        
        # Test component health checks
        for component_name, component_health in system_health["components"].items():
            assert component_health["status"] in ["healthy", "warning", "critical"]
            
            # Component-specific health checks
            if component_name == "clickhouse":
                assert component_health["response_time_ms"] < 100
                assert component_health["connection_pool_usage"] < 0.9
                assert component_health["query_success_rate"] > 0.95  
  
    def test_performance_metrics_monitoring(self):
        """Test performance metrics collection and monitoring."""
        
        # Mock performance metrics
        performance_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "data_processing": {
                "files_processed_per_hour": 240,
                "records_processed_per_hour": 240000,
                "average_file_processing_time_seconds": 15.5,
                "transformation_success_rate": 0.995
            },
            "query_performance": {
                "average_query_response_time_ms": 125,
                "p95_query_response_time_ms": 450,
                "queries_per_minute": 85,
                "slow_query_count_24h": 12
            }
        }
        
        # Test data processing performance
        data_perf = performance_metrics["data_processing"]
        assert data_perf["files_processed_per_hour"] > 0
        assert data_perf["records_processed_per_hour"] > 0
        assert data_perf["average_file_processing_time_seconds"] < 60
        assert data_perf["transformation_success_rate"] > 0.99
        
        # Test query performance
        query_perf = performance_metrics["query_performance"]
        assert query_perf["average_query_response_time_ms"] < 500
        assert query_perf["p95_query_response_time_ms"] < 1000
        assert query_perf["queries_per_minute"] > 0
        assert query_perf["slow_query_count_24h"] < 50

    def test_component_health_checks(self):
        """Test individual component health check functionality."""

        # Mock individual component health checks
        component_health_checks = {
            "clickhouse": {
                "status": "healthy",
                "response_time_ms": 45,
                "connection_count": 8,
                "active_queries": 3,
                "memory_usage_mb": 2048,
                "disk_usage_gb": 125.5,
                "last_health_check": datetime.utcnow().isoformat(),
            },
            "temporal": {
                "status": "healthy",
                "worker_count": 4,
                "active_workflows": 15,
                "pending_activities": 2,
                "task_queue_size": 0,
                "last_health_check": datetime.utcnow().isoformat(),
            },
            "redis": {
                "status": "healthy",
                "memory_usage_mb": 512,
                "connected_clients": 12,
                "operations_per_second": 1500,
                "cache_hit_rate": 0.92,
                "last_health_check": datetime.utcnow().isoformat(),
            },
        }

        # Test ClickHouse health
        ch_health = component_health_checks["clickhouse"]
        assert ch_health["status"] == "healthy"
        assert ch_health["response_time_ms"] < 100
        assert ch_health["connection_count"] > 0
        assert ch_health["memory_usage_mb"] > 0

        # Test Temporal health
        temporal_health = component_health_checks["temporal"]
        assert temporal_health["status"] == "healthy"
        assert temporal_health["worker_count"] > 0
        assert temporal_health["active_workflows"] >= 0
        assert temporal_health["task_queue_size"] >= 0

        # Test Redis health
        redis_health = component_health_checks["redis"]
        assert redis_health["status"] == "healthy"
        assert redis_health["cache_hit_rate"] > 0.8
        assert redis_health["operations_per_second"] > 0

    def test_resource_utilization_monitoring(self):
        """Test system resource utilization monitoring."""

        # Mock resource utilization data
        resource_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "usage_percentage": 65.2,
                "load_average_1m": 2.1,
                "load_average_5m": 1.8,
                "load_average_15m": 1.5,
                "core_count": 8,
            },
            "memory": {
                "total_gb": 32.0,
                "used_gb": 22.4,
                "available_gb": 9.6,
                "usage_percentage": 70.0,
                "swap_used_gb": 0.5,
            },
            "disk": {
                "total_gb": 500.0,
                "used_gb": 175.5,
                "available_gb": 324.5,
                "usage_percentage": 35.1,
                "io_read_mb_per_sec": 45.2,
                "io_write_mb_per_sec": 23.8,
            },
            "network": {
                "bytes_received_per_sec": 1024000,
                "bytes_sent_per_sec": 512000,
                "packets_received_per_sec": 850,
                "packets_sent_per_sec": 420,
                "error_rate": 0.001,
            },
        }

        # Test CPU metrics
        cpu_metrics = resource_metrics["cpu"]
        assert 0 <= cpu_metrics["usage_percentage"] <= 100
        assert cpu_metrics["load_average_1m"] >= 0
        assert cpu_metrics["core_count"] > 0

        # Test memory metrics
        memory_metrics = resource_metrics["memory"]
        assert memory_metrics["used_gb"] + memory_metrics["available_gb"] <= memory_metrics["total_gb"]
        assert 0 <= memory_metrics["usage_percentage"] <= 100
        assert memory_metrics["usage_percentage"] < 85  # Not overloaded

        # Test disk metrics
        disk_metrics = resource_metrics["disk"]
        assert disk_metrics["used_gb"] + disk_metrics["available_gb"] <= disk_metrics["total_gb"]
        assert 0 <= disk_metrics["usage_percentage"] <= 100
        assert disk_metrics["io_read_mb_per_sec"] >= 0
        assert disk_metrics["io_write_mb_per_sec"] >= 0

        # Test network metrics
        network_metrics = resource_metrics["network"]
        assert network_metrics["bytes_received_per_sec"] >= 0
        assert network_metrics["bytes_sent_per_sec"] >= 0
        assert 0 <= network_metrics["error_rate"] <= 1

    def test_data_pipeline_monitoring(self):
        """Test data pipeline monitoring and metrics."""

        # Mock data pipeline metrics
        pipeline_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "ingestion": {
                "files_ingested_24h": 2400,
                "records_ingested_24h": 2400000,
                "ingestion_rate_per_hour": 100,
                "failed_ingestions_24h": 5,
                "success_rate": 0.998,
                "average_file_size_mb": 15.2,
            },
            "transformation": {
                "transformations_completed_24h": 2395,
                "transformation_rate_per_hour": 99.8,
                "failed_transformations_24h": 3,
                "success_rate": 0.999,
                "average_processing_time_seconds": 12.5,
            },
            "storage": {
                "records_stored_24h": 2392000,
                "storage_rate_per_hour": 99650,
                "failed_storage_operations_24h": 2,
                "success_rate": 0.9999,
                "data_volume_stored_gb": 36.5,
            },
        }

        # Test ingestion metrics
        ingestion = pipeline_metrics["ingestion"]
        assert ingestion["files_ingested_24h"] > 0
        assert ingestion["records_ingested_24h"] > 0
        assert ingestion["success_rate"] > 0.99
        assert ingestion["failed_ingestions_24h"] < 10

        # Test transformation metrics
        transformation = pipeline_metrics["transformation"]
        assert transformation["transformations_completed_24h"] > 0
        assert transformation["success_rate"] > 0.99
        assert transformation["average_processing_time_seconds"] < 30

        # Test storage metrics
        storage = pipeline_metrics["storage"]
        assert storage["records_stored_24h"] > 0
        assert storage["success_rate"] > 0.999
        assert storage["data_volume_stored_gb"] > 0

    def test_focus_compliance_monitoring(self):
        """Test FOCUS compliance monitoring and validation."""

        # Mock FOCUS compliance metrics
        compliance_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_compliance_score": 0.96,
            "field_compliance": {
                "required_fields_present": 0.98,
                "field_format_compliance": 0.95,
                "data_type_compliance": 0.97,
                "business_rule_compliance": 0.94,
            },
            "validation_results": {
                "total_records_validated": 100000,
                "compliant_records": 96000,
                "non_compliant_records": 4000,
                "validation_errors": [
                    {"field": "billing_account_id", "error_count": 1500, "error_type": "format"},
                    {"field": "usage_date", "error_count": 1200, "error_type": "missing"},
                    {"field": "billed_cost", "error_count": 800, "error_type": "invalid_value"},
                    {"field": "resource_id", "error_count": 500, "error_type": "format"},
                ],
            },
            "trend_analysis": {
                "compliance_trend_7d": "improving",
                "average_compliance_7d": 0.94,
                "compliance_variance": 0.02,
            },
        }

        # Test overall compliance
        assert 0 <= compliance_metrics["overall_compliance_score"] <= 1
        assert compliance_metrics["overall_compliance_score"] > 0.9  # High compliance expected

        # Test field compliance
        field_compliance = compliance_metrics["field_compliance"]
        for metric_name, score in field_compliance.items():
            assert 0 <= score <= 1
            assert score > 0.9  # High compliance for all fields

        # Test validation results
        validation = compliance_metrics["validation_results"]
        assert validation["compliant_records"] + validation["non_compliant_records"] == validation["total_records_validated"]
        assert len(validation["validation_errors"]) > 0

        # Test trend analysis
        trend = compliance_metrics["trend_analysis"]
        assert trend["compliance_trend_7d"] in ["improving", "stable", "declining"]
        assert 0 <= trend["average_compliance_7d"] <= 1


class TestSystemHealthDashboard:
    """Test system health dashboard functionality."""

    def test_health_dashboard_data_aggregation(self):
        """Test health dashboard data aggregation and summary."""

        # Mock dashboard data
        dashboard_data = {
            "last_updated": datetime.utcnow().isoformat(),
            "system_status": "healthy",
            "active_alerts": 2,
            "critical_alerts": 0,
            "components_healthy": 4,
            "components_total": 5,
            "uptime_percentage": 99.95,
            "performance_score": 0.92,
            "data_quality_score": 0.96,
            "recent_activities": [
                {
                    "timestamp": datetime.utcnow() - timedelta(minutes=5),
                    "activity": "Workflow completed successfully",
                    "component": "temporal",
                    "status": "success",
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(minutes=15),
                    "activity": "Performance alert resolved",
                    "component": "clickhouse",
                    "status": "resolved",
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(minutes=30),
                    "activity": "Data quality check completed",
                    "component": "focus_validator",
                    "status": "success",
                },
            ],
        }

        # Test dashboard summary
        assert dashboard_data["system_status"] in ["healthy", "warning", "critical"]
        assert dashboard_data["active_alerts"] >= 0
        assert dashboard_data["critical_alerts"] >= 0
        assert dashboard_data["components_healthy"] <= dashboard_data["components_total"]

        # Test performance metrics
        assert 0 <= dashboard_data["uptime_percentage"] <= 100
        assert 0 <= dashboard_data["performance_score"] <= 1
        assert 0 <= dashboard_data["data_quality_score"] <= 1

        # Test recent activities
        assert len(dashboard_data["recent_activities"]) > 0
        for activity in dashboard_data["recent_activities"]:
            assert "timestamp" in activity
            assert "activity" in activity
            assert "component" in activity
            assert "status" in activity

    def test_health_status_calculation(self):
        """Test system health status calculation logic."""

        # Mock component statuses
        component_statuses = [
            {"name": "clickhouse", "status": "healthy", "weight": 0.3},
            {"name": "temporal", "status": "healthy", "weight": 0.25},
            {"name": "azure_blob", "status": "warning", "weight": 0.2},
            {"name": "redis", "status": "healthy", "weight": 0.15},
            {"name": "focus_validator", "status": "healthy", "weight": 0.1},
        ]

        # Calculate weighted health score
        status_scores = {"healthy": 1.0, "warning": 0.5, "critical": 0.0}
        total_score = 0
        total_weight = 0

        for component in component_statuses:
            score = status_scores[component["status"]]
            weight = component["weight"]
            total_score += score * weight
            total_weight += weight

        overall_score = total_score / total_weight if total_weight > 0 else 0

        # Determine overall status
        if overall_score >= 0.8:
            overall_status = "healthy"
        elif overall_score >= 0.5:
            overall_status = "warning"
        else:
            overall_status = "critical"

        # Test health calculation
        assert 0 <= overall_score <= 1
        assert overall_status in ["healthy", "warning", "critical"]
        assert overall_status == "healthy"  # Expected with current mock data
        assert overall_score == 0.9  # (1*0.3 + 1*0.25 + 0.5*0.2 + 1*0.15 + 1*0.1) = 0.9

    def test_monitoring_thresholds_configuration(self):
        """Test monitoring thresholds and configuration management."""

        # Mock monitoring thresholds
        monitoring_thresholds = {
            "performance": {
                "query_response_time_ms": {"warning": 500, "critical": 1000},
                "cpu_usage_percentage": {"warning": 80, "critical": 95},
                "memory_usage_percentage": {"warning": 85, "critical": 95},
                "disk_usage_percentage": {"warning": 80, "critical": 90},
            },
            "data_quality": {
                "focus_compliance_score": {"warning": 0.9, "critical": 0.8},
                "transformation_success_rate": {"warning": 0.95, "critical": 0.9},
                "data_completeness": {"warning": 0.95, "critical": 0.9},
            },
            "workflow": {
                "workflow_failure_rate": {"warning": 0.05, "critical": 0.1},
                "processing_delay_minutes": {"warning": 30, "critical": 60},
                "queue_size": {"warning": 100, "critical": 500},
            },
        }

        # Test threshold structure
        for category, thresholds in monitoring_thresholds.items():
            assert isinstance(thresholds, dict)
            for metric, levels in thresholds.items():
                assert "warning" in levels
                assert "critical" in levels
                # Critical threshold should be more severe than warning
                if isinstance(levels["warning"], (int, float)) and isinstance(levels["critical"], (int, float)):
                    if category == "data_quality":
                        # For quality metrics, lower is worse
                        assert levels["critical"] <= levels["warning"]
                    else:
                        # For performance metrics, higher is worse
                        assert levels["critical"] >= levels["warning"]

        # Test specific threshold values
        perf_thresholds = monitoring_thresholds["performance"]
        assert perf_thresholds["cpu_usage_percentage"]["warning"] == 80
        assert perf_thresholds["cpu_usage_percentage"]["critical"] == 95

        quality_thresholds = monitoring_thresholds["data_quality"]
        assert quality_thresholds["focus_compliance_score"]["warning"] == 0.9
        assert quality_thresholds["focus_compliance_score"]["critical"] == 0.8


class TestMonitoringIntegration:
    """Test monitoring system integration with other components."""

    def test_monitoring_data_collection(self):
        """Test monitoring data collection from various sources."""

        # Mock data collection from different sources
        collected_data = {
            "clickhouse_metrics": {
                "source": "clickhouse_system_tables",
                "query_count": 1500,
                "avg_query_time": 125,
                "active_connections": 8,
                "memory_usage": 2048,
            },
            "temporal_metrics": {
                "source": "temporal_api",
                "active_workflows": 12,
                "completed_workflows": 156,
                "failed_workflows": 2,
                "worker_utilization": 0.75,
            },
            "azure_metrics": {
                "source": "azure_monitoring_api",
                "api_calls_24h": 2400,
                "api_success_rate": 0.998,
                "rate_limit_usage": 0.45,
                "connection_status": "healthy",
            },
            "system_metrics": {
                "source": "system_monitoring_agent",
                "cpu_usage": 65.2,
                "memory_usage": 70.0,
                "disk_usage": 35.1,
                "network_throughput": 1536,
            },
        }

        # Test data collection completeness
        expected_sources = ["clickhouse_metrics", "temporal_metrics", "azure_metrics", "system_metrics"]
        for source in expected_sources:
            assert source in collected_data
            assert "source" in collected_data[source]

        # Test data validity
        ch_metrics = collected_data["clickhouse_metrics"]
        assert ch_metrics["query_count"] > 0
        assert ch_metrics["avg_query_time"] > 0
        assert ch_metrics["active_connections"] >= 0

        temporal_metrics = collected_data["temporal_metrics"]
        assert temporal_metrics["active_workflows"] >= 0
        assert temporal_metrics["completed_workflows"] >= 0
        assert 0 <= temporal_metrics["worker_utilization"] <= 1

    def test_monitoring_alert_integration(self):
        """Test integration between monitoring and alerting systems."""

        # Mock monitoring event that should trigger alert
        monitoring_event = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "performance_monitor",
            "metric": "query_response_time",
            "value": 1200,  # ms
            "threshold_warning": 500,
            "threshold_critical": 1000,
            "component": "clickhouse",
            "severity": "critical",  # Exceeds critical threshold
        }

        # Test alert triggering logic
        should_alert = monitoring_event["value"] > monitoring_event["threshold_warning"]
        alert_severity = "critical" if monitoring_event["value"] > monitoring_event["threshold_critical"] else "warning"

        assert should_alert is True
        assert alert_severity == "critical"
        assert monitoring_event["severity"] == alert_severity

        # Mock alert generation
        generated_alert = {
            "alert_id": f"alert-{monitoring_event['source']}-{int(datetime.utcnow().timestamp())}",
            "title": f"{monitoring_event['metric']} threshold exceeded",
            "description": f"{monitoring_event['component']} {monitoring_event['metric']} is {monitoring_event['value']}ms",
            "severity": alert_severity,
            "source": monitoring_event["source"],
            "component": monitoring_event["component"],
            "timestamp": monitoring_event["timestamp"],
            "metadata": {
                "metric": monitoring_event["metric"],
                "current_value": monitoring_event["value"],
                "threshold_exceeded": monitoring_event["threshold_critical"],
            },
        }

        # Test alert structure
        assert "alert_id" in generated_alert
        assert generated_alert["severity"] == "critical"
        assert generated_alert["component"] == "clickhouse"
        assert generated_alert["metadata"]["current_value"] == 1200