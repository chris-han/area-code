"""
Alerting System Tests

Tests for alerting system functionality and alert generation.
"""

from datetime import datetime, timedelta

import pytest


class TestAlertingSystem:
    """Test alerting system functionality."""

    def test_workflow_failure_alerting(self):
        """Test alerting for workflow failures."""

        # Mock workflow failure scenario
        workflow_failure = {
            "workflow_id": "azure-ncei-workflow-456",
            "status": "failed",
            "error_message": "Azure Blob Storage connection timeout",
            "failed_at": datetime.utcnow().isoformat(),
            "retry_count": 3,
            "files_processed_before_failure": 25,
            "total_files": 100,
        }

        # Mock alert generation
        alert = {
            "alert_id": "alert-workflow-failure-456",
            "severity": "high",
            "title": "Workflow Execution Failed",
            "description": f"Workflow {workflow_failure['workflow_id']} failed: {workflow_failure['error_message']}",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "workflow_monitor",
            "metadata": {
                "workflow_id": workflow_failure["workflow_id"],
                "error_type": "connection_timeout",
                "retry_count": workflow_failure["retry_count"],
                "progress_lost": workflow_failure["files_processed_before_failure"],
            },
        }

        # Test alert properties
        assert alert["severity"] in ["low", "medium", "high", "critical"]
        assert alert["severity"] == "high"  # Workflow failures should be high severity
        assert "workflow_id" in alert["metadata"]
        assert alert["metadata"]["retry_count"] == 3
        assert alert["metadata"]["progress_lost"] == 25

    def test_performance_degradation_alerting(self):
        """Test alerting for performance degradation."""

        # Mock performance degradation scenario
        performance_issue = {
            "metric": "query_response_time",
            "current_value": 2500,  # 2.5 seconds
            "threshold": 1000,  # 1 second threshold
            "severity_multiplier": 2.5,
            "duration_minutes": 15,
            "affected_queries": 45,
        }

        # Generate performance alert
        alert = {
            "alert_id": "alert-performance-degradation-789",
            "severity": "medium" if performance_issue["severity_multiplier"] < 3 else "high",
            "title": "Query Performance Degradation Detected",
            "description": f"Query response time ({performance_issue['current_value']}ms) exceeds threshold ({performance_issue['threshold']}ms)",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "performance_monitor",
            "metadata": {
                "metric": performance_issue["metric"],
                "current_value": performance_issue["current_value"],
                "threshold": performance_issue["threshold"],
                "duration_minutes": performance_issue["duration_minutes"],
                "affected_queries": performance_issue["affected_queries"],
            },
        }

        # Test performance alert
        assert alert["severity"] == "medium"  # 2.5x threshold = medium severity
        assert alert["metadata"]["current_value"] > alert["metadata"]["threshold"]
        assert alert["metadata"]["duration_minutes"] > 0
        assert alert["metadata"]["affected_queries"] > 0

    def test_data_quality_alerting(self):
        """Test alerting for data quality issues."""

        # Mock data quality issue
        data_quality_issue = {
            "issue_type": "missing_required_fields",
            "affected_records": 150,
            "total_records": 10000,
            "missing_fields": ["billing_account_id", "usage_date"],
            "file_path": "focus-data/2024/01/billing_data_20240115.parquet",
            "detected_at": datetime.utcnow().isoformat(),
        }

        # Calculate severity based on impact
        impact_percentage = (
            data_quality_issue["affected_records"] / data_quality_issue["total_records"]
        ) * 100
        severity = "low" if impact_percentage < 1 else "medium" if impact_percentage < 5 else "high"

        # Generate data quality alert
        alert = {
            "alert_id": "alert-data-quality-101",
            "severity": severity,
            "title": "Data Quality Issue Detected",
            "description": f"Missing required fields in {data_quality_issue['affected_records']} records ({impact_percentage:.1f}%)",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "data_quality_monitor",
            "metadata": {
                "issue_type": data_quality_issue["issue_type"],
                "affected_records": data_quality_issue["affected_records"],
                "impact_percentage": impact_percentage,
                "missing_fields": data_quality_issue["missing_fields"],
                "file_path": data_quality_issue["file_path"],
            },
        }

        # Test data quality alert
        assert alert["severity"] == "medium"  # 1.5% impact = medium severity (1% < 1.5% < 5%)
        assert alert["metadata"]["impact_percentage"] == 1.5
        assert len(alert["metadata"]["missing_fields"]) == 2
        assert "billing_account_id" in alert["metadata"]["missing_fields"]

    def test_system_resource_alerting(self):
        """Test alerting for system resource issues."""

        # Mock system resource issue
        resource_issue = {
            "resource_type": "memory",
            "current_usage": 92.5,  # 92.5% memory usage
            "threshold": 85.0,  # 85% threshold
            "duration_minutes": 10,
            "affected_services": ["clickhouse", "temporal"],
            "detected_at": datetime.utcnow().isoformat(),
        }

        # Generate resource alert
        severity = "critical" if resource_issue["current_usage"] > 95 else "high"
        alert = {
            "alert_id": "alert-resource-memory-202",
            "severity": severity,
            "title": f"{resource_issue['resource_type'].title()} Usage Critical",
            "description": f"Memory usage at {resource_issue['current_usage']}% exceeds threshold",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "resource_monitor",
            "metadata": {
                "resource_type": resource_issue["resource_type"],
                "current_usage": resource_issue["current_usage"],
                "threshold": resource_issue["threshold"],
                "duration_minutes": resource_issue["duration_minutes"],
                "affected_services": resource_issue["affected_services"],
            },
        }

        # Test resource alert
        assert alert["severity"] == "high"  # 92.5% = high severity
        assert alert["metadata"]["current_usage"] > alert["metadata"]["threshold"]
        assert len(alert["metadata"]["affected_services"]) == 2
        assert "clickhouse" in alert["metadata"]["affected_services"]

    def test_focus_compliance_alerting(self):
        """Test alerting for FOCUS compliance violations."""

        # Mock FOCUS compliance issue
        compliance_issue = {
            "violation_type": "invalid_field_format",
            "field_name": "billing_account_id",
            "expected_format": "UUID",
            "actual_format": "string",
            "affected_records": 500,
            "total_records": 10000,
            "file_path": "focus-data/2024/01/billing_data_20240120.parquet",
            "detected_at": datetime.utcnow().isoformat(),
        }

        # Calculate compliance score
        compliance_score = (
            (compliance_issue["total_records"] - compliance_issue["affected_records"])
            / compliance_issue["total_records"]
        ) * 100

        # Generate compliance alert
        severity = "high" if compliance_score < 90 else "medium" if compliance_score < 95 else "low"
        alert = {
            "alert_id": "alert-focus-compliance-303",
            "severity": severity,
            "title": "FOCUS Compliance Violation Detected",
            "description": f"Field format violation in {compliance_issue['field_name']}",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "focus_compliance_monitor",
            "metadata": {
                "violation_type": compliance_issue["violation_type"],
                "field_name": compliance_issue["field_name"],
                "expected_format": compliance_issue["expected_format"],
                "actual_format": compliance_issue["actual_format"],
                "compliance_score": compliance_score,
                "affected_records": compliance_issue["affected_records"],
                "file_path": compliance_issue["file_path"],
            },
        }

        # Test compliance alert
        assert alert["severity"] == "low"  # 95% compliance = low severity (>95%)
        assert alert["metadata"]["compliance_score"] == 95.0
        assert alert["metadata"]["field_name"] == "billing_account_id"
        assert alert["metadata"]["violation_type"] == "invalid_field_format"

    def test_alert_escalation_logic(self):
        """Test alert escalation based on severity and duration."""

        # Mock alert escalation scenario
        base_alert = {
            "alert_id": "alert-escalation-test-404",
            "severity": "medium",
            "title": "Test Alert for Escalation",
            "first_occurrence": datetime.utcnow() - timedelta(minutes=30),
            "last_occurrence": datetime.utcnow(),
            "occurrence_count": 5,
            "escalation_level": 0,
        }

        # Test escalation logic
        duration_minutes = (
            base_alert["last_occurrence"] - base_alert["first_occurrence"]
        ).total_seconds() / 60

        # Escalate if alert persists for more than 20 minutes with multiple occurrences
        should_escalate = duration_minutes > 20 and base_alert["occurrence_count"] >= 3

        if should_escalate:
            escalated_alert = base_alert.copy()
            escalated_alert["severity"] = (
                "high" if base_alert["severity"] == "medium" else "critical"
            )
            escalated_alert["escalation_level"] = base_alert["escalation_level"] + 1
            escalated_alert["escalated_at"] = datetime.utcnow().isoformat()

            # Test escalation results
            assert escalated_alert["severity"] == "high"
            assert escalated_alert["escalation_level"] == 1
            assert "escalated_at" in escalated_alert
        else:
            # Should not escalate
            assert base_alert["escalation_level"] == 0

    def test_alert_notification_routing(self):
        """Test alert notification routing based on severity and type."""

        # Mock different alert types
        alerts = [
            {
                "alert_id": "alert-critical-system-505",
                "severity": "critical",
                "source": "system_monitor",
                "alert_type": "system_failure",
            },
            {
                "alert_id": "alert-medium-performance-506",
                "severity": "medium",
                "source": "performance_monitor",
                "alert_type": "performance_degradation",
            },
            {
                "alert_id": "alert-low-data-quality-507",
                "severity": "low",
                "source": "data_quality_monitor",
                "alert_type": "data_quality_issue",
            },
        ]

        # Test notification routing logic
        for alert in alerts:
            notification_channels = []

            # Route based on severity
            if alert["severity"] == "critical":
                notification_channels.extend(["pager", "email", "slack", "sms"])
            elif alert["severity"] == "high":
                notification_channels.extend(["email", "slack"])
            elif alert["severity"] == "medium":
                notification_channels.extend(["email"])
            else:  # low severity
                notification_channels.extend(["slack"])

            # Route based on alert type
            if alert["alert_type"] == "system_failure":
                notification_channels.append("incident_management")
            elif alert["alert_type"] == "performance_degradation":
                notification_channels.append("performance_team")
            elif alert["alert_type"] == "data_quality_issue":
                notification_channels.append("data_team")

            # Test routing results
            if alert["severity"] == "critical":
                assert "pager" in notification_channels
                assert "sms" in notification_channels
                assert "incident_management" in notification_channels
            elif alert["severity"] == "medium":
                assert "email" in notification_channels
                assert "performance_team" in notification_channels
            elif alert["severity"] == "low":
                assert "slack" in notification_channels
                assert "data_team" in notification_channels

    def test_alert_suppression_logic(self):
        """Test alert suppression to prevent spam."""

        # Mock alert suppression scenario
        recent_alerts = [
            {
                "alert_id": f"alert-duplicate-{i}",
                "alert_type": "query_timeout",
                "source": "performance_monitor",
                "timestamp": datetime.utcnow() - timedelta(minutes=i),
                "suppressed": False,
            }
            for i in range(10)  # 10 similar alerts in last 10 minutes
        ]

        # Test suppression logic
        alert_type_counts = {}
        suppression_threshold = 5  # Suppress after 5 similar alerts
        suppression_window_minutes = 15

        for alert in recent_alerts:
            alert_key = f"{alert['alert_type']}_{alert['source']}"

            # Count alerts of same type within suppression window
            if alert_key not in alert_type_counts:
                alert_type_counts[alert_key] = 0

            alert_age_minutes = (datetime.utcnow() - alert["timestamp"]).total_seconds() / 60

            if alert_age_minutes <= suppression_window_minutes:
                alert_type_counts[alert_key] += 1

                # Suppress if threshold exceeded
                if alert_type_counts[alert_key] > suppression_threshold:
                    alert["suppressed"] = True

        # Test suppression results
        suppressed_count = sum(1 for alert in recent_alerts if alert["suppressed"])
        assert suppressed_count > 0  # Some alerts should be suppressed
        assert suppressed_count == 5  # Last 5 alerts should be suppressed

        # First 5 alerts should not be suppressed
        for i in range(5):
            assert not recent_alerts[i]["suppressed"]


class TestAlertMetrics:
    """Test alert metrics and analytics."""

    def test_alert_frequency_analysis(self):
        """Test alert frequency analysis and trending."""

        # Mock alert history data
        alert_history = [
            {"date": "2024-01-01", "alert_count": 15, "critical_count": 2, "high_count": 5},
            {"date": "2024-01-02", "alert_count": 22, "critical_count": 3, "high_count": 8},
            {"date": "2024-01-03", "alert_count": 18, "critical_count": 1, "high_count": 6},
            {"date": "2024-01-04", "alert_count": 35, "critical_count": 5, "high_count": 12},
            {"date": "2024-01-05", "alert_count": 28, "critical_count": 4, "high_count": 9},
        ]

        # Calculate metrics
        total_alerts = sum(day["alert_count"] for day in alert_history)
        avg_daily_alerts = total_alerts / len(alert_history)
        critical_percentage = (
            sum(day["critical_count"] for day in alert_history) / total_alerts
        ) * 100

        # Test metrics
        assert total_alerts == 118
        assert avg_daily_alerts == 23.6
        assert critical_percentage == pytest.approx(12.7, rel=0.1)

        # Test trending
        recent_avg = sum(day["alert_count"] for day in alert_history[-2:]) / 2
        earlier_avg = sum(day["alert_count"] for day in alert_history[:2]) / 2
        trend_direction = "increasing" if recent_avg > earlier_avg else "decreasing"

        assert trend_direction == "increasing"  # 31.5 > 18.5

    def test_alert_resolution_tracking(self):
        """Test alert resolution time tracking."""

        # Mock alert resolution data
        resolved_alerts = [
            {
                "alert_id": "alert-resolved-1",
                "created_at": datetime.utcnow() - timedelta(hours=2),
                "resolved_at": datetime.utcnow() - timedelta(hours=1, minutes=30),
                "severity": "high",
                "resolution_method": "automatic",
            },
            {
                "alert_id": "alert-resolved-2",
                "created_at": datetime.utcnow() - timedelta(hours=4),
                "resolved_at": datetime.utcnow() - timedelta(hours=3, minutes=45),
                "severity": "medium",
                "resolution_method": "manual",
            },
            {
                "alert_id": "alert-resolved-3",
                "created_at": datetime.utcnow() - timedelta(hours=1),
                "resolved_at": datetime.utcnow() - timedelta(minutes=45),
                "severity": "critical",
                "resolution_method": "automatic",
            },
        ]

        # Calculate resolution metrics
        resolution_times = []
        for alert in resolved_alerts:
            resolution_time = (alert["resolved_at"] - alert["created_at"]).total_seconds() / 60
            resolution_times.append(resolution_time)

        avg_resolution_time = sum(resolution_times) / len(resolution_times)
        automatic_resolutions = sum(
            1 for alert in resolved_alerts if alert["resolution_method"] == "automatic"
        )
        automation_rate = (automatic_resolutions / len(resolved_alerts)) * 100

        # Test resolution metrics
        assert len(resolution_times) == 3
        assert avg_resolution_time == pytest.approx(20.0, rel=0.1)  # ~20 minutes average
        assert automation_rate == pytest.approx(66.7, rel=0.1)  # 2/3 automatic
