"""
Quarantine System for Invalid Records

Manages quarantine, review, and reprocessing of invalid billing records
with comprehensive tracking and reporting capabilities.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import json
import logging

from .focus_validator import ValidationResult, ValidationIssue

logger = logging.getLogger(__name__)


class QuarantineStatus(Enum):
    """Quarantine record status"""
    QUARANTINED = "quarantined"
    UNDER_REVIEW = "under_review"
    FIXED = "fixed"
    REJECTED = "rejected"
    REPROCESSED = "reprocessed"


class QuarantineReason(Enum):
    """Quarantine reason categories"""
    VALIDATION_ERROR = "validation_error"
    DATA_QUALITY_ISSUE = "data_quality_issue"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"
    FOCUS_COMPLIANCE_FAILURE = "focus_compliance_failure"
    MANUAL_QUARANTINE = "manual_quarantine"


@dataclass
class QuarantineRecord:
    """Represents a quarantined record"""
    id: str
    original_record: Dict[str, Any]
    validation_result: Dict[str, Any]  # Serialized ValidationResult
    quarantine_timestamp: datetime
    quarantine_reason: QuarantineReason
    status: QuarantineStatus
    assigned_reviewer: Optional[str] = None
    review_notes: Optional[str] = None
    fixed_record: Optional[Dict[str, Any]] = None
    reprocess_attempts: int = 0
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert enums to strings
        data["quarantine_reason"] = self.quarantine_reason.value
        data["status"] = self.status.value
        # Convert datetime to ISO string
        data["quarantine_timestamp"] = self.quarantine_timestamp.isoformat()
        if self.last_updated:
            data["last_updated"] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuarantineRecord':
        """Create from dictionary"""
        # Convert strings back to enums
        data["quarantine_reason"] = QuarantineReason(data["quarantine_reason"])
        data["status"] = QuarantineStatus(data["status"])
        # Convert ISO strings back to datetime
        data["quarantine_timestamp"] = datetime.fromisoformat(data["quarantine_timestamp"])
        if data.get("last_updated"):
            data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        return cls(**data)


class QuarantineSystem:
    """
    Comprehensive quarantine system for managing invalid billing records
    with review workflows and reprocessing capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.storage_backend = self.config.get("storage_backend", "memory")  # memory, clickhouse, postgresql
        self.auto_retry_enabled = self.config.get("auto_retry_enabled", True)
        self.max_retry_attempts = self.config.get("max_retry_attempts", 3)
        self.retry_delay_hours = self.config.get("retry_delay_hours", 24)
        
        # In-memory storage for demo (would be replaced with actual database)
        self._quarantine_storage: Dict[str, QuarantineRecord] = {}
        self._quarantine_stats = {
            "total_quarantined": 0,
            "total_fixed": 0,
            "total_rejected": 0,
            "total_reprocessed": 0
        }
    
    def quarantine_record(self, 
                         record: Dict[str, Any], 
                         validation_result: ValidationResult,
                         reason: Optional[QuarantineReason] = None) -> str:
        """
        Quarantine a record with validation issues.
        
        Args:
            record: Original billing record
            validation_result: Validation result with issues
            reason: Optional specific quarantine reason
            
        Returns:
            Quarantine ID
        """
        # Determine quarantine reason if not provided
        if reason is None:
            reason = self._determine_quarantine_reason(validation_result)
        
        quarantine_id = f"quar_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{record.get('id', 'unknown')}"
        
        quarantine_record = QuarantineRecord(
            id=quarantine_id,
            original_record=record,
            validation_result=self._serialize_validation_result(validation_result),
            quarantine_timestamp=datetime.utcnow(),
            quarantine_reason=reason,
            status=QuarantineStatus.QUARANTINED,
            last_updated=datetime.utcnow()
        )
        
        # Store quarantine record
        self._store_quarantine_record(quarantine_record)
        
        # Update statistics
        self._quarantine_stats["total_quarantined"] += 1
        
        logger.info(f"Record quarantined: {quarantine_id}, reason: {reason.value}")
        return quarantine_id
    
    def get_quarantine_record(self, quarantine_id: str) -> Optional[QuarantineRecord]:
        """Get quarantine record by ID"""
        return self._quarantine_storage.get(quarantine_id)
    
    def list_quarantine_records(self, 
                              status: Optional[QuarantineStatus] = None,
                              reason: Optional[QuarantineReason] = None,
                              limit: int = 100,
                              offset: int = 0) -> List[QuarantineRecord]:
        """
        List quarantine records with optional filtering.
        
        Args:
            status: Filter by quarantine status
            reason: Filter by quarantine reason
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of quarantine records
        """
        records = list(self._quarantine_storage.values())
        
        # Apply filters
        if status:
            records = [r for r in records if r.status == status]
        if reason:
            records = [r for r in records if r.quarantine_reason == reason]
        
        # Sort by quarantine timestamp (newest first)
        records.sort(key=lambda r: r.quarantine_timestamp, reverse=True)
        
        # Apply pagination
        return records[offset:offset + limit]
    
    def assign_reviewer(self, quarantine_id: str, reviewer: str) -> bool:
        """
        Assign a reviewer to a quarantined record.
        
        Args:
            quarantine_id: Quarantine record ID
            reviewer: Reviewer identifier
            
        Returns:
            True if assignment successful
        """
        record = self.get_quarantine_record(quarantine_id)
        if not record:
            return False
        
        record.assigned_reviewer = reviewer
        record.status = QuarantineStatus.UNDER_REVIEW
        record.last_updated = datetime.utcnow()
        
        self._store_quarantine_record(record)
        logger.info(f"Assigned reviewer {reviewer} to quarantine record {quarantine_id}")
        return True
    
    def add_review_notes(self, quarantine_id: str, notes: str) -> bool:
        """
        Add review notes to a quarantined record.
        
        Args:
            quarantine_id: Quarantine record ID
            notes: Review notes
            
        Returns:
            True if notes added successfully
        """
        record = self.get_quarantine_record(quarantine_id)
        if not record:
            return False
        
        record.review_notes = notes
        record.last_updated = datetime.utcnow()
        
        self._store_quarantine_record(record)
        logger.info(f"Added review notes to quarantine record {quarantine_id}")
        return True
    
    def fix_record(self, quarantine_id: str, fixed_record: Dict[str, Any]) -> bool:
        """
        Provide a fixed version of a quarantined record.
        
        Args:
            quarantine_id: Quarantine record ID
            fixed_record: Corrected billing record
            
        Returns:
            True if fix applied successfully
        """
        record = self.get_quarantine_record(quarantine_id)
        if not record:
            return False
        
        record.fixed_record = fixed_record
        record.status = QuarantineStatus.FIXED
        record.last_updated = datetime.utcnow()
        
        self._store_quarantine_record(record)
        self._quarantine_stats["total_fixed"] += 1
        
        logger.info(f"Applied fix to quarantine record {quarantine_id}")
        return True
    
    def reject_record(self, quarantine_id: str, rejection_reason: str) -> bool:
        """
        Reject a quarantined record as unfixable.
        
        Args:
            quarantine_id: Quarantine record ID
            rejection_reason: Reason for rejection
            
        Returns:
            True if rejection successful
        """
        record = self.get_quarantine_record(quarantine_id)
        if not record:
            return False
        
        record.status = QuarantineStatus.REJECTED
        record.review_notes = f"REJECTED: {rejection_reason}"
        record.last_updated = datetime.utcnow()
        
        self._store_quarantine_record(record)
        self._quarantine_stats["total_rejected"] += 1
        
        logger.info(f"Rejected quarantine record {quarantine_id}: {rejection_reason}")
        return True
    
    def reprocess_record(self, quarantine_id: str) -> Dict[str, Any]:
        """
        Reprocess a fixed quarantined record.
        
        Args:
            quarantine_id: Quarantine record ID
            
        Returns:
            Reprocessing result
        """
        record = self.get_quarantine_record(quarantine_id)
        if not record or record.status != QuarantineStatus.FIXED:
            return {
                "success": False,
                "error": "Record not found or not in fixed status"
            }
        
        if not record.fixed_record:
            return {
                "success": False,
                "error": "No fixed record available"
            }
        
        # Increment reprocess attempts
        record.reprocess_attempts += 1
        record.status = QuarantineStatus.REPROCESSED
        record.last_updated = datetime.utcnow()
        
        self._store_quarantine_record(record)
        self._quarantine_stats["total_reprocessed"] += 1
        
        logger.info(f"Reprocessed quarantine record {quarantine_id}")
        
        return {
            "success": True,
            "quarantine_id": quarantine_id,
            "fixed_record": record.fixed_record,
            "reprocess_attempts": record.reprocess_attempts
        }
    
    def get_quarantine_statistics(self) -> Dict[str, Any]:
        """Get comprehensive quarantine statistics"""
        # Calculate status distribution
        status_counts = {}
        reason_counts = {}
        
        for record in self._quarantine_storage.values():
            status = record.status.value
            reason = record.quarantine_reason.value
            
            status_counts[status] = status_counts.get(status, 0) + 1
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        # Calculate age distribution
        now = datetime.utcnow()
        age_distribution = {
            "less_than_1_day": 0,
            "1_to_7_days": 0,
            "7_to_30_days": 0,
            "more_than_30_days": 0
        }
        
        for record in self._quarantine_storage.values():
            age_days = (now - record.quarantine_timestamp).days
            
            if age_days < 1:
                age_distribution["less_than_1_day"] += 1
            elif age_days <= 7:
                age_distribution["1_to_7_days"] += 1
            elif age_days <= 30:
                age_distribution["7_to_30_days"] += 1
            else:
                age_distribution["more_than_30_days"] += 1
        
        return {
            "total_records": len(self._quarantine_storage),
            "status_distribution": status_counts,
            "reason_distribution": reason_counts,
            "age_distribution": age_distribution,
            "cumulative_stats": self._quarantine_stats.copy(),
            "processing_rates": {
                "fix_rate": self._quarantine_stats["total_fixed"] / max(self._quarantine_stats["total_quarantined"], 1),
                "rejection_rate": self._quarantine_stats["total_rejected"] / max(self._quarantine_stats["total_quarantined"], 1),
                "reprocess_rate": self._quarantine_stats["total_reprocessed"] / max(self._quarantine_stats["total_fixed"], 1)
            }
        }
    
    def get_auto_retry_candidates(self) -> List[QuarantineRecord]:
        """
        Get records eligible for automatic retry.
        
        Returns:
            List of records that can be automatically retried
        """
        candidates = []
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retry_delay_hours)
        
        for record in self._quarantine_storage.values():
            if (record.status == QuarantineStatus.QUARANTINED and
                record.reprocess_attempts < self.max_retry_attempts and
                record.quarantine_timestamp <= cutoff_time):
                candidates.append(record)
        
        return candidates
    
    def generate_quarantine_report(self, 
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate comprehensive quarantine report.
        
        Args:
            start_date: Report start date (optional)
            end_date: Report end date (optional)
            
        Returns:
            Detailed quarantine report
        """
        # Filter records by date range if provided
        records = list(self._quarantine_storage.values())
        
        if start_date:
            records = [r for r in records if r.quarantine_timestamp >= start_date]
        if end_date:
            records = [r for r in records if r.quarantine_timestamp <= end_date]
        
        # Generate report sections
        report = {
            "report_generated": datetime.utcnow().isoformat(),
            "date_range": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "summary": {
                "total_records": len(records),
                "status_breakdown": {},
                "reason_breakdown": {},
                "top_validation_issues": []
            },
            "trends": {
                "daily_quarantine_counts": {},
                "resolution_times": []
            },
            "recommendations": []
        }
        
        # Calculate status and reason breakdowns
        for record in records:
            status = record.status.value
            reason = record.quarantine_reason.value
            
            report["summary"]["status_breakdown"][status] = report["summary"]["status_breakdown"].get(status, 0) + 1
            report["summary"]["reason_breakdown"][reason] = report["summary"]["reason_breakdown"].get(reason, 0) + 1
        
        # Analyze validation issues
        issue_counts = {}
        for record in records:
            validation_result = record.validation_result
            if "issues" in validation_result:
                for issue in validation_result["issues"]:
                    issue_key = f"{issue.get('category', 'unknown')}_{issue.get('rule_name', 'unknown')}"
                    issue_counts[issue_key] = issue_counts.get(issue_key, 0) + 1
        
        # Top 5 validation issues
        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        report["summary"]["top_validation_issues"] = [
            {"issue": issue, "count": count} for issue, count in top_issues
        ]
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(records, issue_counts)
        
        return report
    
    def _determine_quarantine_reason(self, validation_result: ValidationResult) -> QuarantineReason:
        """Determine quarantine reason from validation result"""
        if not validation_result.is_focus_compliant:
            return QuarantineReason.FOCUS_COMPLIANCE_FAILURE
        
        # Check for specific error categories
        for issue in validation_result.errors:
            if issue.category.value == "business_rule":
                return QuarantineReason.BUSINESS_RULE_VIOLATION
            elif issue.category.value == "data_quality":
                return QuarantineReason.DATA_QUALITY_ISSUE
        
        return QuarantineReason.VALIDATION_ERROR
    
    def _serialize_validation_result(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """Serialize validation result for storage"""
        return {
            "record_id": validation_result.record_id,
            "is_valid": validation_result.is_valid,
            "is_focus_compliant": validation_result.is_focus_compliant,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "category": issue.category.value,
                    "field_name": issue.field_name,
                    "message": issue.message,
                    "actual_value": str(issue.actual_value) if issue.actual_value is not None else None,
                    "expected_value": str(issue.expected_value) if issue.expected_value is not None else None,
                    "rule_name": issue.rule_name
                }
                for issue in validation_result.issues
            ]
        }
    
    def _store_quarantine_record(self, record: QuarantineRecord):
        """Store quarantine record (in-memory for demo)"""
        self._quarantine_storage[record.id] = record
    
    def _generate_recommendations(self, records: List[QuarantineRecord], issue_counts: Dict[str, int]) -> List[str]:
        """Generate recommendations based on quarantine patterns"""
        recommendations = []
        
        # High quarantine rate
        if len(records) > 100:
            recommendations.append("High quarantine rate detected. Consider reviewing data source quality.")
        
        # Common validation issues
        if issue_counts:
            top_issue = max(issue_counts.items(), key=lambda x: x[1])
            if top_issue[1] > len(records) * 0.3:  # More than 30% of records have this issue
                recommendations.append(f"Common validation issue: {top_issue[0]}. Consider upstream data fixes.")
        
        # Old unresolved records
        old_records = [r for r in records if (datetime.utcnow() - r.quarantine_timestamp).days > 7]
        if old_records:
            recommendations.append(f"{len(old_records)} records have been quarantined for more than 7 days. Consider review prioritization.")
        
        return recommendations