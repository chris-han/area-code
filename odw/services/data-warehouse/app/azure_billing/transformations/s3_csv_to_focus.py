"""
S3 CSV to FOCUS Transformation Module

SQL-based transformation logic for converting S3 CSV billing data
to FOCUS-compliant format with schema detection and validation.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .azure_ea_to_focus import BaseTransformationEngine

logger = logging.getLogger(__name__)


class S3CSVToFOCUSTransformer(BaseTransformationEngine):
    """
    Transforms S3 CSV billing data to FOCUS-compliant format.
    
    This class provides flexible transformation logic for various CSV schemas
    with automatic field mapping and validation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.schema_mappings = self._load_schema_mappings()
    
    def _get_field_mappings(self) -> Dict[str, str]:
        """Return default field mappings from S3 CSV to FOCUS format"""
        return {
            "account_id": "billing_account_id",
            "account_name": "billing_account_name",
            "usage_date": "usage_date",
            "cost": "billed_cost",
            "unit_price": "list_unit_price",
            "usage_quantity": "usage_quantity",
            "usage_unit": "usage_unit",
            "resource_id": "resource_id",
            "resource_name": "resource_name",
            "service_name": "service_name",
            "service_category": "service_category",
            "region": "region",
            "availability_zone": "availability_zone",
            "currency": "billing_currency"
        }
    
    def _get_transformation_sql(self) -> str:
        """Generate SQL transformation query for S3 CSV to FOCUS conversion"""
        return """
        INSERT INTO focus_billing_data
        SELECT 
            CONCAT(
                coalesce(account_id, 'unknown'), '_',
                toString(toDate(usage_date)), '_',
                coalesce(resource_id, 'unknown'), '_',
                randomString(8)
            ) as id,
            
            coalesce(account_id, 'unknown') as billing_account_id,
            coalesce(account_name, 'Unknown Account') as billing_account_name,
            coalesce(currency, '{default_currency}') as billing_currency,
            toDate(usage_date) as billing_period_start_date,
            toDate(usage_date) as billing_period_end_date,
            
            toDecimal64(coalesce(cost, 0), 4) as billed_cost,
            toDecimal64(
                CASE 
                    WHEN unit_price IS NOT NULL AND usage_quantity IS NOT NULL 
                    THEN unit_price * usage_quantity
                    ELSE cost
                END, 4
            ) as effective_cost,
            toDecimal64(
                CASE 
                    WHEN unit_price IS NOT NULL AND usage_quantity IS NOT NULL 
                    THEN unit_price * usage_quantity
                    ELSE cost
                END, 4
            ) as list_cost,
            toDecimal64(coalesce(unit_price, 0), 4) as list_unit_price,
            
            toDate(usage_date) as usage_date,
            toDecimal64(coalesce(usage_quantity, 0), 4) as usage_quantity,
            coalesce(usage_unit, 'Unknown') as usage_unit,
            
            resource_id as resource_id,
            coalesce(resource_name, 'Unknown Resource') as resource_name,
            coalesce(resource_type, 'Other') as resource_type,
            
            CASE 
                WHEN lower(service_category) IS NOT NULL THEN service_category
                WHEN lower(service_name) LIKE '%compute%' THEN 'Compute'
                WHEN lower(service_name) LIKE '%storage%' THEN 'Storage'
                WHEN lower(service_name) LIKE '%network%' THEN 'Networking'
                WHEN lower(service_name) LIKE '%database%' THEN 'Database'
                ELSE 'Other'
            END as service_category,
            coalesce(service_name, 'Unknown Service') as service_name,
            
            availability_zone as availability_zone,
            coalesce(region, 'Unknown Region') as region,
            
            coalesce('{provider}', 'Unknown') as provider,
            
            now() as created_at,
            now() as updated_at,
            's3_csv' as source_system
            
        FROM s3_csv_billing_record
        WHERE usage_date >= toDate('{start_date}')
          AND usage_date <= toDate('{end_date}')
          AND cost IS NOT NULL
          AND cost > 0
          AND account_id IS NOT NULL
        ORDER BY usage_date, account_id
        """
    
    def _get_validation_rules(self) -> Dict[str, Any]:
        """Return validation rules for S3 CSV transformation"""
        return {
            "required_fields": [
                "billing_account_id",
                "usage_date", 
                "billed_cost",
                "billing_currency"
            ],
            "numeric_fields": [
                "billed_cost",
                "effective_cost",
                "list_cost",
                "list_unit_price",
                "usage_quantity"
            ],
            "date_fields": [
                "usage_date",
                "billing_period_start_date",
                "billing_period_end_date"
            ]
        }
    
    def transform_record(self, csv_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single S3 CSV record to FOCUS format"""
        focus_record = {}
        
        try:
            # Apply field mappings
            for csv_field, focus_field in self.field_mappings.items():
                if csv_field in csv_record and csv_record[csv_field] is not None:
                    focus_record[focus_field] = csv_record[csv_field]
            
            # Apply business logic transformations
            focus_record = self._apply_business_rules(focus_record, csv_record)
            
            # Add metadata
            focus_record["created_at"] = datetime.utcnow()
            focus_record["updated_at"] = datetime.utcnow()
            focus_record["source_system"] = "s3_csv"
            
            return focus_record
            
        except Exception as e:
            logger.error(f"Error transforming S3 CSV record: {e}")
            raise
    
    def _apply_business_rules(self, focus_record: Dict[str, Any], csv_record: Dict[str, Any]) -> Dict[str, Any]:
        """Apply FOCUS business rules and data quality transformations"""
        # Generate unique ID
        account_id = focus_record.get("billing_account_id", "unknown")
        usage_date = focus_record.get("usage_date", datetime.utcnow().date())
        resource_id = focus_record.get("resource_id", "unknown")
        
        focus_record["id"] = f"{account_id}_{usage_date}_{resource_id}"
        
        # Set billing period dates
        if "usage_date" in focus_record:
            focus_record["billing_period_start_date"] = focus_record["usage_date"]
            focus_record["billing_period_end_date"] = focus_record["usage_date"]
        
        # Default currency
        if "billing_currency" not in focus_record:
            focus_record["billing_currency"] = self.config.get("default_currency", "USD")
        
        # Service category mapping
        if "service_category" not in focus_record and "service_name" in focus_record:
            service_name = focus_record["service_name"].lower()
            if "compute" in service_name:
                focus_record["service_category"] = "Compute"
            elif "storage" in service_name:
                focus_record["service_category"] = "Storage"
            elif "network" in service_name:
                focus_record["service_category"] = "Networking"
            elif "database" in service_name:
                focus_record["service_category"] = "Database"
            else:
                focus_record["service_category"] = "Other"
        
        # Ensure provider is set
        if "provider" not in focus_record:
            focus_record["provider"] = self.config.get("default_provider", "Unknown")
        
        return focus_record
    
    def _load_schema_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load predefined schema mappings for common CSV formats"""
        return {
            "aws_cost_and_usage": {
                "lineItem/UsageAccountId": "billing_account_id",
                "lineItem/UsageStartDate": "usage_date",
                "lineItem/BlendedCost": "billed_cost",
                "lineItem/CurrencyCode": "billing_currency",
                "product/ProductName": "service_name",
                "product/region": "region",
                "lineItem/ResourceId": "resource_id",
                "lineItem/UsageAmount": "usage_quantity",
                "pricing/unit": "usage_unit"
            },
            "azure_consumption": {
                "AccountName": "billing_account_name",
                "SubscriptionId": "billing_account_id",
                "Date": "usage_date",
                "ExtendedCost": "billed_cost",
                "ConsumedService": "service_name",
                "ResourceLocation": "region",
                "InstanceId": "resource_id",
                "ConsumedQuantity": "usage_quantity",
                "UnitOfMeasure": "usage_unit"
            }
        }    

    def detect_schema(self, csv_headers: List[str]) -> Optional[str]:
        """
        Detect CSV schema based on column headers
        
        Args:
            csv_headers: List of column headers from CSV file
            
        Returns:
            Schema name if detected, None otherwise
        """
        header_set = set(header.lower().strip() for header in csv_headers)
        
        # Check for AWS Cost and Usage Report
        aws_indicators = {
            "lineitem/usageaccountid", "lineitem/usagestartdate", 
            "lineitem/blendedcost", "product/productname"
        }
        if aws_indicators.issubset(header_set):
            return "aws_cost_and_usage"
        
        # Check for Azure Consumption API
        azure_indicators = {
            "subscriptionid", "date", "extendedcost", "consumedservice"
        }
        if azure_indicators.issubset(header_set):
            return "azure_consumption"
        
        # Check for generic billing format
        generic_indicators = {
            "account_id", "usage_date", "cost", "service_name"
        }
        if generic_indicators.issubset(header_set):
            return "generic_billing"
        
        logger.warning(f"Unknown CSV schema detected. Headers: {csv_headers}")
        return None
    
    def get_schema_mapping(self, schema_name: str) -> Dict[str, str]:
        """
        Get field mapping for a specific schema
        
        Args:
            schema_name: Name of the detected schema
            
        Returns:
            Dictionary mapping CSV fields to FOCUS fields
        """
        if schema_name in self.schema_mappings:
            return self.schema_mappings[schema_name]
        elif schema_name == "generic_billing":
            return self._get_field_mappings()
        else:
            logger.warning(f"No mapping found for schema: {schema_name}")
            return self._get_field_mappings()
    
    def transform_batch(self, csv_records: List[Dict[str, Any]], 
                       schema_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Transform a batch of CSV records to FOCUS format
        
        Args:
            csv_records: List of CSV records as dictionaries
            schema_name: Optional schema name for field mapping
            
        Returns:
            List of FOCUS-compliant records
        """
        if not csv_records:
            return []
        
        # Auto-detect schema if not provided
        if schema_name is None:
            headers = list(csv_records[0].keys())
            schema_name = self.detect_schema(headers)
        
        # Get appropriate field mapping
        if schema_name:
            self.field_mappings = self.get_schema_mapping(schema_name)
            logger.info(f"Using schema mapping: {schema_name}")
        else:
            self.field_mappings = self._get_field_mappings()
            logger.info("Using default field mapping")
        
        focus_records = []
        errors = []
        
        for i, csv_record in enumerate(csv_records):
            try:
                focus_record = self.transform_record(csv_record)
                
                # Validate the transformed record
                if self.validate_record(focus_record):
                    focus_records.append(focus_record)
                else:
                    errors.append(f"Record {i}: Validation failed")
                    
            except Exception as e:
                errors.append(f"Record {i}: {str(e)}")
                logger.error(f"Error transforming record {i}: {e}")
        
        if errors:
            logger.warning(f"Transformation completed with {len(errors)} errors: {errors[:5]}")
        
        logger.info(f"Successfully transformed {len(focus_records)}/{len(csv_records)} records")
        return focus_records
    
    def validate_record(self, record: Dict[str, Any]) -> bool:
        """
        Validate a FOCUS record against validation rules
        
        Args:
            record: FOCUS record to validate
            
        Returns:
            True if valid, False otherwise
        """
        validation_rules = self._get_validation_rules()
        
        # Check required fields
        for field in validation_rules["required_fields"]:
            if field not in record or record[field] is None:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate numeric fields
        for field in validation_rules["numeric_fields"]:
            if field in record and record[field] is not None:
                try:
                    float(record[field])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid numeric value for field {field}: {record[field]}")
                    return False
        
        # Validate date fields
        for field in validation_rules["date_fields"]:
            if field in record and record[field] is not None:
                if not isinstance(record[field], (datetime, str)):
                    logger.warning(f"Invalid date value for field {field}: {record[field]}")
                    return False
        
        return True
    
    def get_transformation_summary(self, input_count: int, output_count: int, 
                                 errors: List[str]) -> Dict[str, Any]:
        """
        Generate transformation summary statistics
        
        Args:
            input_count: Number of input records
            output_count: Number of successfully transformed records
            errors: List of error messages
            
        Returns:
            Summary dictionary
        """
        return {
            "input_records": input_count,
            "output_records": output_count,
            "success_rate": (output_count / input_count * 100) if input_count > 0 else 0,
            "error_count": len(errors),
            "errors": errors[:10],  # First 10 errors
            "transformation_timestamp": datetime.utcnow().isoformat(),
            "transformer": "S3CSVToFOCUSTransformer"
        }


# Utility functions for CSV processing
def normalize_csv_headers(headers: List[str]) -> List[str]:
    """
    Normalize CSV headers for consistent processing
    
    Args:
        headers: List of raw CSV headers
        
    Returns:
        List of normalized headers
    """
    normalized = []
    for header in headers:
        # Remove special characters and normalize spacing
        normalized_header = header.strip().lower()
        normalized_header = normalized_header.replace(' ', '_')
        normalized_header = normalized_header.replace('-', '_')
        normalized_header = normalized_header.replace('/', '_')
        normalized.append(normalized_header)
    
    return normalized


def detect_csv_delimiter(sample_line: str) -> str:
    """
    Detect CSV delimiter from a sample line
    
    Args:
        sample_line: Sample line from CSV file
        
    Returns:
        Detected delimiter character
    """
    common_delimiters = [',', ';', '\t', '|']
    delimiter_counts = {}
    
    for delimiter in common_delimiters:
        delimiter_counts[delimiter] = sample_line.count(delimiter)
    
    # Return delimiter with highest count
    return max(delimiter_counts, key=delimiter_counts.get)


def validate_csv_structure(headers: List[str], sample_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate CSV structure and provide quality metrics
    
    Args:
        headers: CSV headers
        sample_records: Sample of CSV records
        
    Returns:
        Validation results dictionary
    """
    validation_results = {
        "is_valid": True,
        "issues": [],
        "recommendations": [],
        "column_count": len(headers),
        "sample_size": len(sample_records)
    }
    
    # Check for duplicate headers
    if len(headers) != len(set(headers)):
        validation_results["is_valid"] = False
        validation_results["issues"].append("Duplicate column headers detected")
    
    # Check for empty headers
    empty_headers = [i for i, h in enumerate(headers) if not h.strip()]
    if empty_headers:
        validation_results["is_valid"] = False
        validation_results["issues"].append(f"Empty headers at positions: {empty_headers}")
    
    # Check data consistency across sample records
    if sample_records:
        expected_columns = len(headers)
        for i, record in enumerate(sample_records):
            if len(record) != expected_columns:
                validation_results["issues"].append(
                    f"Record {i} has {len(record)} columns, expected {expected_columns}"
                )
    
    # Provide recommendations
    if validation_results["column_count"] > 100:
        validation_results["recommendations"].append(
            "Large number of columns detected. Consider filtering unnecessary fields."
        )
    
    return validation_results


# Factory function for creating transformers
def create_s3_csv_transformer(config: Optional[Dict[str, Any]] = None) -> S3CSVToFOCUSTransformer:
    """
    Factory function to create S3 CSV to FOCUS transformer
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured S3CSVToFOCUSTransformer instance
    """
    default_config = {
        "default_currency": "USD",
        "default_provider": "Unknown",
        "batch_size": 1000,
        "validation_enabled": True,
        "schema_detection_enabled": True
    }
    
    if config:
        default_config.update(config)
    
    return S3CSVToFOCUSTransformer(default_config)