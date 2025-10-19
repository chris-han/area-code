"""
FOCUS Compliance Validation Engine

Comprehensive validation engine for FOCUS specification compliance
with business rule validation, data quality checks, and error quarantine.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from enum import Enum
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(Enum):
    """Validation categories"""
    REQUIRED_FIELD = "required_field"
    DATA_TYPE = "data_type"
    BUSINESS_RULE = "business_rule"
    DATA_QUALITY = "data_quality"
    FOCUS_COMPLIANCE = "focus_compliance"


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    severity: ValidationSeverity
    category: ValidationCategory
    field_name: Optional[str]
    message: str
    actual_value: Any = None
    expected_value: Any = None
    rule_name: Optional[str] = None


@dataclass
class ValidationResult:
    """Validation result for a single record"""
    record_id: str
    is_valid: bool
    is_focus_compliant: bool
    issues: List[ValidationIssue]
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]


class FOCUSComplianceValidator:
    """
    FOCUS specification compliance validator with comprehensive
    business rule validation and data quality checks.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.focus_spec = self._load_focus_specification()
        self.business_rules = self._load_business_rules()
        self.data_quality_rules = self._load_data_quality_rules()
    
    def _load_focus_specification(self) -> Dict[str, Any]:
        """Load FOCUS specification requirements"""
        return {
            "version": "1.0",
            "required_dimensions": {
                "billing_account_id": {
                    "type": "string",
                    "nullable": False,
                    "description": "Unique identifier for the billing account"
                },
                "usage_date": {
                    "type": "date",
                    "nullable": False,
                    "description": "The date when the resource usage occurred"
                },
                "billed_cost": {
                    "type": "decimal",
                    "nullable": False,
                    "min_value": 0,
                    "description": "The cost that was charged for this line item"
                },
                "billing_currency": {
                    "type": "string",
                    "nullable": False,
                    "pattern": r"^[A-Z]{3}$",
                    "description": "Currency code for billing amounts (ISO 4217)"
                },
                "provider": {
                    "type": "string",
                    "nullable": False,
                    "allowed_values": ["Azure", "AWS", "GCP", "Oracle", "IBM"],
                    "description": "Cloud provider name"
                }
            },
            "optional_dimensions": {
                "billing_account_name": {
                    "type": "string",
                    "nullable": True,
                    "description": "Display name of the billing account"
                },
                "effective_cost": {
                    "type": "decimal",
                    "nullable": True,
                    "min_value": 0,
                    "description": "The amortized cost after applying discounts"
                },
                "list_cost": {
                    "type": "decimal",
                    "nullable": True,
                    "min_value": 0,
                    "description": "The cost without any discounts applied"
                },
                "list_unit_price": {
                    "type": "decimal",
                    "nullable": True,
                    "min_value": 0,
                    "description": "The unit price without discounts"
                },
                "usage_quantity": {
                    "type": "decimal",
                    "nullable": True,
                    "min_value": 0,
                    "description": "The quantity of the resource that was used"
                },
                "usage_unit": {
                    "type": "string",
                    "nullable": True,
                    "description": "The unit of measure for the usage quantity"
                },
                "resource_id": {
                    "type": "string",
                    "nullable": True,
                    "description": "Unique identifier for the resource"
                },
                "resource_name": {
                    "type": "string",
                    "nullable": True,
                    "description": "Display name of the resource"
                },
                "resource_type": {
                    "type": "string",
                    "nullable": True,
                    "description": "The type or category of the resource"
                },
                "service_category": {
                    "type": "string",
                    "nullable": True,
                    "allowed_values": ["Compute", "Storage", "Networking", "Database", "Analytics", "Security", "Management", "Other"],
                    "description": "High-level category of the service"
                },
                "service_name": {
                    "type": "string",
                    "nullable": True,
                    "description": "Name of the service that generated the cost"
                },
                "availability_zone": {
                    "type": "string",
                    "nullable": True,
                    "description": "Availability zone where the resource is located"
                },
                "region": {
                    "type": "string",
                    "nullable": True,
                    "description": "Geographic region where the resource is located"
                }
            }
        }
    
    def _load_business_rules(self) -> Dict[str, Any]:
        """Load FOCUS business rules"""
        return {
            "cost_consistency": {
                "name": "Cost Consistency Check",
                "description": "Validate cost field relationships",
                "rules": [
                    {
                        "name": "effective_cost_vs_billed_cost",
                        "condition": "effective_cost <= billed_cost * 1.1",  # Allow 10% variance
                        "message": "Effective cost should not exceed billed cost by more than 10%"
                    },
                    {
                        "name": "list_cost_vs_billed_cost",
                        "condition": "list_cost >= billed_cost * 0.9",  # List cost should be >= billed cost
                        "message": "List cost should be greater than or equal to billed cost"
                    }
                ]
            },
            "usage_consistency": {
                "name": "Usage Consistency Check",
                "description": "Validate usage quantity and unit relationships",
                "rules": [
                    {
                        "name": "quantity_unit_consistency",
                        "condition": "usage_quantity IS NULL OR usage_unit IS NOT NULL",
                        "message": "Usage unit must be provided when usage quantity is specified"
                    },
                    {
                        "name": "zero_quantity_zero_cost",
                        "condition": "usage_quantity > 0 OR billed_cost = 0",
                        "message": "Zero usage quantity should result in zero cost"
                    }
                ]
            },
            "temporal_consistency": {
                "name": "Temporal Consistency Check",
                "description": "Validate date field relationships",
                "rules": [
                    {
                        "name": "billing_period_consistency",
                        "condition": "billing_period_start_date <= billing_period_end_date",
                        "message": "Billing period start date must be before or equal to end date"
                    },
                    {
                        "name": "usage_date_in_period",
                        "condition": "usage_date >= billing_period_start_date AND usage_date <= billing_period_end_date",
                        "message": "Usage date must be within billing period"
                    }
                ]
            }
        }
    
    def _load_data_quality_rules(self) -> Dict[str, Any]:
        """Load data quality validation rules"""
        return {
            "completeness": {
                "recommended_fields": [
                    "billing_account_name",
                    "service_name",
                    "resource_id",
                    "region"
                ],
                "completeness_threshold": 0.8  # 80% of recommended fields should be present
            },
            "accuracy": {
                "cost_thresholds": {
                    "min_cost": 0.01,
                    "max_cost": 1000000,
                    "suspicious_cost": 50000
                },
                "date_ranges": {
                    "min_date": "2020-01-01",
                    "max_future_days": 30
                }
            },
            "consistency": {
                "currency_codes": ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CNY", "INR"],
                "provider_standardization": {
                    "azure": ["Azure", "Microsoft Azure", "AZURE"],
                    "aws": ["AWS", "Amazon Web Services", "Amazon"],
                    "gcp": ["GCP", "Google Cloud Platform", "Google Cloud", "Google"]
                }
            }
        }
    
    def validate_record(self, record: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single FOCUS billing record.
        
        Args:
            record: FOCUS billing record to validate
            
        Returns:
            ValidationResult with detailed validation information
        """
        record_id = record.get("id", f"unknown_{datetime.utcnow().timestamp()}")
        issues = []
        
        # Validate required dimensions
        issues.extend(self._validate_required_dimensions(record))
        
        # Validate data types
        issues.extend(self._validate_data_types(record))
        
        # Validate business rules
        issues.extend(self._validate_business_rules(record))
        
        # Validate data quality
        issues.extend(self._validate_data_quality(record))
        
        # Determine overall validation status
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        is_valid = not has_errors
        
        # FOCUS compliance requires no errors and minimal warnings
        warning_count = len([issue for issue in issues if issue.severity == ValidationSeverity.WARNING])
        is_focus_compliant = is_valid and warning_count <= 2
        
        return ValidationResult(
            record_id=record_id,
            is_valid=is_valid,
            is_focus_compliant=is_focus_compliant,
            issues=issues
        )
    
    def _validate_required_dimensions(self, record: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate required FOCUS dimensions"""
        issues = []
        
        for field_name, field_spec in self.focus_spec["required_dimensions"].items():
            if field_name not in record or record[field_name] is None:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.REQUIRED_FIELD,
                    field_name=field_name,
                    message=f"Missing required FOCUS field: {field_name}",
                    rule_name="required_dimension"
                ))
        
        return issues
    
    def _validate_data_types(self, record: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate data types for all dimensions"""
        issues = []
        
        all_dimensions = {**self.focus_spec["required_dimensions"], **self.focus_spec["optional_dimensions"]}
        
        for field_name, field_spec in all_dimensions.items():
            if field_name in record and record[field_name] is not None:
                value = record[field_name]
                expected_type = field_spec["type"]
                
                if not self._validate_field_type(value, expected_type):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.DATA_TYPE,
                        field_name=field_name,
                        message=f"Invalid data type for {field_name}: expected {expected_type}",
                        actual_value=type(value).__name__,
                        expected_value=expected_type,
                        rule_name="data_type_validation"
                    ))
                
                # Validate additional constraints
                issues.extend(self._validate_field_constraints(field_name, value, field_spec))
        
        return issues
    
    def _validate_field_type(self, value: Any, expected_type: str) -> bool:
        """Validate field data type"""
        try:
            if expected_type == "string":
                return isinstance(value, str)
            elif expected_type == "decimal":
                if isinstance(value, (int, float, Decimal)):
                    return True
                # Try to convert string to decimal
                Decimal(str(value))
                return True
            elif expected_type == "date":
                if isinstance(value, (date, datetime)):
                    return True
                # Try to parse as date string
                if isinstance(value, str):
                    datetime.strptime(value, "%Y-%m-%d")
                    return True
            return False
        except (ValueError, TypeError, InvalidOperation):
            return False
    
    def _validate_field_constraints(self, field_name: str, value: Any, field_spec: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate field-specific constraints"""
        issues = []
        
        # Validate minimum value for numeric fields
        if "min_value" in field_spec:
            try:
                numeric_value = float(value)
                if numeric_value < field_spec["min_value"]:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.BUSINESS_RULE,
                        field_name=field_name,
                        message=f"{field_name} cannot be less than {field_spec['min_value']}",
                        actual_value=numeric_value,
                        expected_value=f">= {field_spec['min_value']}",
                        rule_name="min_value_constraint"
                    ))
            except (ValueError, TypeError):
                pass  # Type validation will catch this
        
        # Validate allowed values
        if "allowed_values" in field_spec:
            if value not in field_spec["allowed_values"]:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.BUSINESS_RULE,
                    field_name=field_name,
                    message=f"Invalid value for {field_name}: {value}",
                    actual_value=value,
                    expected_value=field_spec["allowed_values"],
                    rule_name="allowed_values_constraint"
                ))
        
        # Validate pattern matching
        if "pattern" in field_spec and isinstance(value, str):
            if not re.match(field_spec["pattern"], value):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.BUSINESS_RULE,
                    field_name=field_name,
                    message=f"{field_name} does not match required pattern",
                    actual_value=value,
                    expected_value=field_spec["pattern"],
                    rule_name="pattern_constraint"
                ))
        
        return issues
    
    def _validate_business_rules(self, record: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate FOCUS business rules"""
        issues = []
        
        # Cost consistency checks
        if "billed_cost" in record and "effective_cost" in record:
            try:
                billed_cost = float(record["billed_cost"])
                effective_cost = float(record["effective_cost"])
                
                if effective_cost > billed_cost * 1.1:  # Allow 10% variance
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.BUSINESS_RULE,
                        field_name="effective_cost",
                        message="Effective cost exceeds billed cost by more than 10%",
                        actual_value=effective_cost,
                        expected_value=f"<= {billed_cost * 1.1}",
                        rule_name="cost_consistency"
                    ))
            except (ValueError, TypeError):
                pass
        
        # Usage consistency checks
        if "usage_quantity" in record and record["usage_quantity"] is not None:
            if "usage_unit" not in record or record["usage_unit"] is None:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.BUSINESS_RULE,
                    field_name="usage_unit",
                    message="Usage unit should be provided when usage quantity is specified",
                    rule_name="usage_consistency"
                ))
        
        # Temporal consistency checks
        if all(field in record for field in ["billing_period_start_date", "billing_period_end_date"]):
            try:
                start_date = record["billing_period_start_date"]
                end_date = record["billing_period_end_date"]
                
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                
                if start_date > end_date:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.BUSINESS_RULE,
                        field_name="billing_period_start_date",
                        message="Billing period start date must be before or equal to end date",
                        rule_name="temporal_consistency"
                    ))
            except (ValueError, TypeError):
                pass
        
        return issues
    
    def _validate_data_quality(self, record: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate data quality aspects"""
        issues = []
        
        # Check completeness of recommended fields
        recommended_fields = self.data_quality_rules["completeness"]["recommended_fields"]
        missing_recommended = []
        
        for field in recommended_fields:
            if field not in record or record[field] is None or record[field] == "":
                missing_recommended.append(field)
        
        if missing_recommended:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DATA_QUALITY,
                field_name=None,
                message=f"Missing recommended fields: {', '.join(missing_recommended)}",
                rule_name="completeness_check"
            ))
        
        # Check for suspicious cost values
        if "billed_cost" in record:
            try:
                cost = float(record["billed_cost"])
                cost_thresholds = self.data_quality_rules["accuracy"]["cost_thresholds"]
                
                if cost > cost_thresholds["suspicious_cost"]:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.DATA_QUALITY,
                        field_name="billed_cost",
                        message=f"Unusually high cost detected: {cost}",
                        actual_value=cost,
                        rule_name="suspicious_cost_check"
                    ))
                
                if cost > cost_thresholds["max_cost"]:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.DATA_QUALITY,
                        field_name="billed_cost",
                        message=f"Cost exceeds maximum threshold: {cost}",
                        actual_value=cost,
                        expected_value=f"<= {cost_thresholds['max_cost']}",
                        rule_name="max_cost_check"
                    ))
            except (ValueError, TypeError):
                pass
        
        # Check date ranges
        if "usage_date" in record:
            try:
                usage_date = record["usage_date"]
                if isinstance(usage_date, str):
                    usage_date = datetime.strptime(usage_date, "%Y-%m-%d").date()
                
                min_date = datetime.strptime(self.data_quality_rules["accuracy"]["date_ranges"]["min_date"], "%Y-%m-%d").date()
                max_future_date = datetime.utcnow().date()
                
                if usage_date < min_date:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.DATA_QUALITY,
                        field_name="usage_date",
                        message=f"Usage date is before minimum allowed date: {usage_date}",
                        actual_value=usage_date,
                        expected_value=f">= {min_date}",
                        rule_name="date_range_check"
                    ))
                
                if usage_date > max_future_date:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.DATA_QUALITY,
                        field_name="usage_date",
                        message=f"Usage date is in the future: {usage_date}",
                        actual_value=usage_date,
                        expected_value=f"<= {max_future_date}",
                        rule_name="future_date_check"
                    ))
            except (ValueError, TypeError):
                pass
        
        return issues
    
    def validate_batch(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of FOCUS billing records.
        
        Args:
            records: List of FOCUS billing records
            
        Returns:
            Comprehensive batch validation results
        """
        batch_start_time = datetime.utcnow()
        validation_results = []
        
        for record in records:
            result = self.validate_record(record)
            validation_results.append(result)
        
        # Aggregate results
        total_records = len(records)
        valid_records = sum(1 for result in validation_results if result.is_valid)
        focus_compliant_records = sum(1 for result in validation_results if result.is_focus_compliant)
        
        # Aggregate issues by type
        issue_summary = {}
        for result in validation_results:
            for issue in result.issues:
                key = f"{issue.category.value}_{issue.rule_name}"
                if key not in issue_summary:
                    issue_summary[key] = {
                        "category": issue.category.value,
                        "rule_name": issue.rule_name,
                        "message": issue.message,
                        "count": 0,
                        "severity": issue.severity.value
                    }
                issue_summary[key]["count"] += 1
        
        batch_result = {
            "validation_timestamp": batch_start_time,
            "processing_time_seconds": (datetime.utcnow() - batch_start_time).total_seconds(),
            "total_records": total_records,
            "valid_records": valid_records,
            "invalid_records": total_records - valid_records,
            "focus_compliant_records": focus_compliant_records,
            "validation_rate": valid_records / total_records if total_records > 0 else 0,
            "compliance_rate": focus_compliant_records / total_records if total_records > 0 else 0,
            "issue_summary": list(issue_summary.values()),
            "detailed_results": validation_results
        }
        
        return batch_result


class ValidationErrorHandler:
    """
    Handles validation errors and manages quarantine system
    for invalid records.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.quarantine_enabled = self.config.get("quarantine_enabled", True)
        self.auto_fix_enabled = self.config.get("auto_fix_enabled", False)
    
    def handle_validation_result(self, result: ValidationResult, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle validation result and determine action.
        
        Args:
            result: Validation result
            record: Original record
            
        Returns:
            Action result with processed record or quarantine information
        """
        action_result = {
            "record_id": result.record_id,
            "action": "none",
            "processed_record": record.copy(),
            "quarantine_reason": None,
            "auto_fixes_applied": []
        }
        
        if not result.is_valid:
            if self.quarantine_enabled:
                action_result["action"] = "quarantine"
                action_result["quarantine_reason"] = self._get_quarantine_reason(result)
                action_result["processed_record"] = None
            else:
                action_result["action"] = "reject"
        elif self.auto_fix_enabled and result.warnings:
            # Attempt to auto-fix warnings
            fixed_record, fixes_applied = self._apply_auto_fixes(record, result.warnings)
            action_result["processed_record"] = fixed_record
            action_result["auto_fixes_applied"] = fixes_applied
            action_result["action"] = "auto_fix" if fixes_applied else "accept"
        else:
            action_result["action"] = "accept"
        
        return action_result
    
    def _get_quarantine_reason(self, result: ValidationResult) -> str:
        """Generate quarantine reason from validation errors"""
        error_messages = [issue.message for issue in result.errors]
        return "; ".join(error_messages[:3])  # Limit to first 3 errors
    
    def _apply_auto_fixes(self, record: Dict[str, Any], warnings: List[ValidationIssue]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Apply automatic fixes for common validation warnings.
        
        Args:
            record: Original record
            warnings: List of validation warnings
            
        Returns:
            Tuple of (fixed_record, list_of_fixes_applied)
        """
        fixed_record = record.copy()
        fixes_applied = []
        
        for warning in warnings:
            if warning.rule_name == "completeness_check" and warning.field_name:
                # Set default values for missing recommended fields
                if warning.field_name == "service_category" and "service_name" in fixed_record:
                    service_name = fixed_record["service_name"].lower()
                    if "compute" in service_name:
                        fixed_record["service_category"] = "Compute"
                        fixes_applied.append(f"Set service_category to 'Compute' based on service_name")
                    elif "storage" in service_name:
                        fixed_record["service_category"] = "Storage"
                        fixes_applied.append(f"Set service_category to 'Storage' based on service_name")
                
                elif warning.field_name == "region" and not fixed_record.get("region"):
                    fixed_record["region"] = "Unknown Region"
                    fixes_applied.append("Set region to 'Unknown Region' for missing value")
            
            elif warning.rule_name == "suspicious_cost_check":
                # Flag suspicious costs but don't modify them
                fixes_applied.append("Flagged suspicious cost for manual review")
        
        return fixed_record, fixes_applied