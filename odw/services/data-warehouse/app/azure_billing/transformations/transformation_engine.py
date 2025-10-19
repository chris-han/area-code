"""
Transformation Engine Manager

Centralized management for all source-to-FOCUS transformations
with DataLens integration and validation.
"""

from typing import Dict, Any, Optional, List, Type
from datetime import datetime
from abc import ABC, abstractmethod
import logging
import asyncio

from .azure_ea_to_focus import AzureEAToFOCUSTransformer, DataLensTransformationEngine
from .s3_csv_to_focus import S3CSVToFOCUSTransformer

logger = logging.getLogger(__name__)


class TransformationEngineManager:
    """
    Manages all transformation engines and provides unified interface
    for source-to-FOCUS data transformations.
    """
    
    def __init__(self, datalens_config: Optional[Dict[str, Any]] = None):
        self.transformers: Dict[str, Any] = {}
        self.datalens_engine = None
        
        if datalens_config:
            self.datalens_engine = DataLensTransformationEngine(datalens_config)
        
        # Register default transformers
        self._register_default_transformers()
    
    def _register_default_transformers(self):
        """Register default transformation engines"""
        self.register_transformer("azure_ea", AzureEAToFOCUSTransformer)
        self.register_transformer("s3_csv", S3CSVToFOCUSTransformer)
    
    def register_transformer(self, source_type: str, transformer_class: Type):
        """
        Register a new transformation engine.
        
        Args:
            source_type: Source data type identifier
            transformer_class: Transformer class
        """
        self.transformers[source_type] = transformer_class
        logger.info(f"Registered transformer for source type: {source_type}")
    
    def get_transformer(self, source_type: str, config: Optional[Dict[str, Any]] = None):
        """
        Get transformer instance for a source type.
        
        Args:
            source_type: Source data type identifier
            config: Optional configuration for the transformer
            
        Returns:
            Transformer instance
        """
        if source_type not in self.transformers:
            raise ValueError(f"No transformer registered for source type: {source_type}")
        
        transformer_class = self.transformers[source_type]
        return transformer_class(config)
    
    async def execute_transformation(self, 
                                   source_type: str,
                                   transformation_params: Dict[str, Any],
                                   config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute transformation for a specific source type.
        
        Args:
            source_type: Source data type identifier
            transformation_params: Parameters for the transformation
            config: Optional transformer configuration
            
        Returns:
            Transformation results
        """
        transformer = self.get_transformer(source_type, config)
        
        # Get transformation SQL
        sql_query = transformer.get_transformation_sql_with_params(
            transformation_params.get("start_date"),
            transformation_params.get("end_date")
        )
        
        # Execute via DataLens if available
        if self.datalens_engine:
            transformation_id = f"{source_type}_to_focus_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            await self.datalens_engine.register_transformation(
                transformation_id=transformation_id,
                source_table=transformation_params.get("source_table", f"{source_type}_billing_detail"),
                target_table="focus_billing_data",
                sql_template=sql_query,
                validation_rules=transformer._get_validation_rules()
            )
            
            result = await self.datalens_engine.execute_transformation(
                transformation_id,
                transformation_params,
                transformation_params.get("batch_size", 10000)
            )
        else:
            # Direct execution (would integrate with ClickHouse client)
            result = {
                "transformation_id": f"{source_type}_to_focus",
                "status": "completed",
                "sql_query": sql_query,
                "records_processed": 0,  # Would be actual count
                "execution_time": datetime.utcnow()
            }
        
        logger.info(f"Transformation completed: {result}")
        return result
    
    def validate_transformation_config(self, source_type: str, config: Dict[str, Any]) -> List[str]:
        """
        Validate transformation configuration.
        
        Args:
            source_type: Source data type identifier
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if source_type not in self.transformers:
            errors.append(f"Unknown source type: {source_type}")
            return errors
        
        # Get transformer and validate
        try:
            transformer = self.get_transformer(source_type, config)
            
            # Check required configuration fields
            required_fields = getattr(transformer, 'required_config_fields', [])
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required config field: {field}")
            
        except Exception as e:
            errors.append(f"Error creating transformer: {str(e)}")
        
        return errors
    
    def get_supported_source_types(self) -> List[str]:
        """Get list of supported source types"""
        return list(self.transformers.keys())
    
    def get_transformation_metadata(self, source_type: str) -> Dict[str, Any]:
        """
        Get metadata about a transformation.
        
        Args:
            source_type: Source data type identifier
            
        Returns:
            Transformation metadata
        """
        if source_type not in self.transformers:
            raise ValueError(f"Unknown source type: {source_type}")
        
        transformer_class = self.transformers[source_type]
        transformer = transformer_class()
        
        return {
            "source_type": source_type,
            "transformer_class": transformer_class.__name__,
            "field_mappings": transformer._get_field_mappings(),
            "validation_rules": transformer._get_validation_rules(),
            "supported_formats": getattr(transformer, 'supported_formats', []),
            "description": transformer.__doc__ or "No description available"
        }


class FOCUSComplianceValidator:
    """
    Validates FOCUS compliance for transformed billing data.
    
    Provides comprehensive validation of FOCUS specification requirements
    including data quality checks and business rule validation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.validation_rules = self._load_focus_validation_rules()
    
    def _load_focus_validation_rules(self) -> Dict[str, Any]:
        """Load FOCUS specification validation rules"""
        return {
            "required_dimensions": [
                "billing_account_id",
                "usage_date",
                "billed_cost",
                "billing_currency",
                "provider"
            ],
            "optional_dimensions": [
                "billing_account_name",
                "effective_cost",
                "list_cost",
                "list_unit_price",
                "usage_quantity",
                "usage_unit",
                "resource_id",
                "resource_name",
                "resource_type",
                "service_category",
                "service_name",
                "availability_zone",
                "region"
            ],
            "data_types": {
                "billing_account_id": "string",
                "billing_account_name": "string",
                "billing_currency": "string",
                "usage_date": "date",
                "billed_cost": "decimal",
                "effective_cost": "decimal",
                "list_cost": "decimal",
                "list_unit_price": "decimal",
                "usage_quantity": "decimal",
                "usage_unit": "string",
                "resource_id": "string",
                "resource_name": "string",
                "resource_type": "string",
                "service_category": "string",
                "service_name": "string",
                "availability_zone": "string",
                "region": "string",
                "provider": "string"
            },
            "business_rules": {
                "billed_cost_min": 0,
                "currency_codes": ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"],
                "date_range_max_days": 366,
                "required_provider_values": ["Azure", "AWS", "GCP"]
            }
        }
    
    def validate_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single FOCUS billing record.
        
        Args:
            record: FOCUS billing record to validate
            
        Returns:
            Validation results with errors and warnings
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "record_id": record.get("id", "unknown")
        }
        
        # Check required dimensions
        for field in self.validation_rules["required_dimensions"]:
            if field not in record or record[field] is None:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["is_valid"] = False
        
        # Validate data types
        for field, expected_type in self.validation_rules["data_types"].items():
            if field in record and record[field] is not None:
                if not self._validate_data_type(record[field], expected_type):
                    validation_result["errors"].append(
                        f"Invalid data type for {field}: expected {expected_type}"
                    )
                    validation_result["is_valid"] = False
        
        # Validate business rules
        business_rule_errors = self._validate_business_rules(record)
        validation_result["errors"].extend(business_rule_errors)
        if business_rule_errors:
            validation_result["is_valid"] = False
        
        # Check for warnings
        warnings = self._check_data_quality_warnings(record)
        validation_result["warnings"].extend(warnings)
        
        return validation_result
    
    def validate_batch(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of FOCUS billing records.
        
        Args:
            records: List of FOCUS billing records
            
        Returns:
            Batch validation results
        """
        batch_result = {
            "total_records": len(records),
            "valid_records": 0,
            "invalid_records": 0,
            "records_with_warnings": 0,
            "validation_details": [],
            "summary_errors": {},
            "summary_warnings": {}
        }
        
        for record in records:
            record_result = self.validate_record(record)
            batch_result["validation_details"].append(record_result)
            
            if record_result["is_valid"]:
                batch_result["valid_records"] += 1
            else:
                batch_result["invalid_records"] += 1
            
            if record_result["warnings"]:
                batch_result["records_with_warnings"] += 1
            
            # Aggregate errors and warnings
            for error in record_result["errors"]:
                batch_result["summary_errors"][error] = batch_result["summary_errors"].get(error, 0) + 1
            
            for warning in record_result["warnings"]:
                batch_result["summary_warnings"][warning] = batch_result["summary_warnings"].get(warning, 0) + 1
        
        return batch_result
    
    def _validate_data_type(self, value: Any, expected_type: str) -> bool:
        """Validate data type of a field value"""
        try:
            if expected_type == "string":
                return isinstance(value, str)
            elif expected_type == "decimal":
                float(value)
                return True
            elif expected_type == "date":
                if isinstance(value, datetime):
                    return True
                # Try to parse as date string
                datetime.strptime(str(value), "%Y-%m-%d")
                return True
            else:
                return True
        except (ValueError, TypeError):
            return False
    
    def _validate_business_rules(self, record: Dict[str, Any]) -> List[str]:
        """Validate FOCUS business rules"""
        errors = []
        
        # Validate cost fields
        if "billed_cost" in record:
            try:
                cost = float(record["billed_cost"])
                if cost < self.validation_rules["business_rules"]["billed_cost_min"]:
                    errors.append("billed_cost cannot be negative")
            except (ValueError, TypeError):
                errors.append("billed_cost must be numeric")
        
        # Validate currency code
        if "billing_currency" in record:
            currency = record["billing_currency"]
            valid_currencies = self.validation_rules["business_rules"]["currency_codes"]
            if currency not in valid_currencies:
                errors.append(f"Invalid currency code: {currency}")
        
        # Validate provider
        if "provider" in record:
            provider = record["provider"]
            valid_providers = self.validation_rules["business_rules"]["required_provider_values"]
            if provider not in valid_providers:
                errors.append(f"Invalid provider: {provider}")
        
        return errors
    
    def _check_data_quality_warnings(self, record: Dict[str, Any]) -> List[str]:
        """Check for data quality warnings"""
        warnings = []
        
        # Check for missing optional but important fields
        important_optional_fields = [
            "billing_account_name",
            "service_name",
            "resource_id",
            "region"
        ]
        
        for field in important_optional_fields:
            if field not in record or record[field] is None:
                warnings.append(f"Missing recommended field: {field}")
        
        # Check for suspicious values
        if "billed_cost" in record:
            try:
                cost = float(record["billed_cost"])
                if cost > 10000:  # Configurable threshold
                    warnings.append("Unusually high cost detected")
            except (ValueError, TypeError):
                pass
        
        return warnings
    
    def generate_validation_report(self, batch_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable validation report.
        
        Args:
            batch_result: Batch validation results
            
        Returns:
            Formatted validation report
        """
        report = []
        report.append("FOCUS Compliance Validation Report")
        report.append("=" * 40)
        report.append(f"Total Records: {batch_result['total_records']}")
        report.append(f"Valid Records: {batch_result['valid_records']}")
        report.append(f"Invalid Records: {batch_result['invalid_records']}")
        report.append(f"Records with Warnings: {batch_result['records_with_warnings']}")
        
        if batch_result['summary_errors']:
            report.append("\nMost Common Errors:")
            for error, count in sorted(batch_result['summary_errors'].items(), 
                                     key=lambda x: x[1], reverse=True)[:5]:
                report.append(f"  - {error}: {count} occurrences")
        
        if batch_result['summary_warnings']:
            report.append("\nMost Common Warnings:")
            for warning, count in sorted(batch_result['summary_warnings'].items(), 
                                       key=lambda x: x[1], reverse=True)[:5]:
                report.append(f"  - {warning}: {count} occurrences")
        
        return "\n".join(report)