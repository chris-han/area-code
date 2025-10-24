"""
Azure EA to FOCUS Transformation Module

SQL-based transformation logic for converting Azure EA billing data
to FOCUS-compliant format with DataLens integration.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod
import logging
import json

logger = logging.getLogger(__name__)


class BaseTransformationEngine(ABC):
    """
    Abstract base class for all transformation engines.
    
    Provides common functionality for source-to-target transformations
    with FOCUS compliance validation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.field_mappings = self._get_field_mappings()
        self.transformation_sql = self._get_transformation_sql()
        self.validation_rules = self._get_validation_rules()
    
    @abstractmethod
    def _get_field_mappings(self) -> Dict[str, str]:
        """Return field mappings from source to FOCUS format"""
        pass
    
    @abstractmethod
    def _get_transformation_sql(self) -> str:
        """Return SQL transformation query"""
        pass
    
    @abstractmethod
    def _get_validation_rules(self) -> Dict[str, Any]:
        """Return validation rules for the transformation"""
        pass
    
    @abstractmethod
    def transform_record(self, source_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single source record to FOCUS format"""
        pass
    
    def validate_focus_record(self, record: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate FOCUS record compliance.
        
        Args:
            record: FOCUS billing record to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = self.validation_rules.get("required_fields", [])
        
        for field in required_fields:
            if field not in record or record[field] is None:
                return False, f"Missing required FOCUS field: {field}"
        
        # Validate data types
        numeric_fields = self.validation_rules.get("numeric_fields", [])
        for field in numeric_fields:
            if field in record and record[field] is not None:
                try:
                    float(record[field])
                except (ValueError, TypeError):
                    return False, f"{field} must be numeric"
                
                if float(record[field]) < 0:
                    return False, f"{field} cannot be negative"
        
        return True, None


class DataLensTransformationEngine:
    """
    DataLens-powered transformation engine for source-to-target mapping.
    
    Integrates with DataLens platform for advanced SQL transformations
    and materialized view management.
    """
    
    def __init__(self, datalens_config: Dict[str, Any]):
        self.datalens_config = datalens_config
        self.transformations = {}
        self.datasets = {}
    
    async def register_transformation(self, 
                                   transformation_id: str,
                                   source_table: str, 
                                   target_table: str, 
                                   sql_template: str,
                                   validation_rules: Optional[Dict[str, Any]] = None) -> str:
        """
        Register a new source-to-target transformation with DataLens.
        
        Args:
            transformation_id: Unique identifier for the transformation
            source_table: Source table name
            target_table: Target table name
            sql_template: SQL transformation template
            validation_rules: Optional validation rules
            
        Returns:
            Transformation ID
        """
        
        # Create DataLens dataset configuration
        dataset_config = {
            "id": transformation_id,
            "name": f"Transformation: {source_table} -> {target_table}",
            "source_connection": "clickhouse_focus",
            "source_table": source_table,
            "target_table": target_table,
            "transformation_sql": sql_template,
            "validation_rules": validation_rules or self._get_default_focus_validation_rules(),
            "materialization": {
                "enabled": True,
                "refresh_schedule": "0 */6 * * *",  # Every 6 hours
                "incremental": True
            }
        }
        
        self.transformations[transformation_id] = dataset_config
        logger.info(f"Registered transformation: {transformation_id}")
        
        return transformation_id
    
    async def execute_transformation(self, 
                                   transformation_id: str, 
                                   parameters: Optional[Dict[str, Any]] = None,
                                   batch_size: int = 10000) -> Dict[str, Any]:
        """
        Execute transformation using DataLens batch processing.
        
        Args:
            transformation_id: Transformation to execute
            parameters: SQL parameters for the transformation
            batch_size: Batch size for processing
            
        Returns:
            Execution results
        """
        
        if transformation_id not in self.transformations:
            raise ValueError(f"Transformation not found: {transformation_id}")
        
        config = self.transformations[transformation_id]
        sql_template = config["transformation_sql"]
        
        # Substitute parameters in SQL template
        if parameters:
            sql_query = sql_template.format(**parameters)
        else:
            sql_query = sql_template
        
        # Execute transformation (this would integrate with actual DataLens API)
        result = {
            "transformation_id": transformation_id,
            "status": "completed",
            "records_processed": 0,  # Would be actual count
            "execution_time": datetime.utcnow(),
            "sql_query": sql_query,
            "batch_size": batch_size
        }
        
        logger.info(f"Executed transformation {transformation_id}: {result}")
        return result
    
    def _get_default_focus_validation_rules(self) -> Dict[str, Any]:
        """Get default FOCUS validation rules"""
        return {
            "required_fields": [
                "billing_account_id",
                "usage_date", 
                "billed_cost",
                "billing_currency",
                "provider"
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


class AzureEAToFOCUSTransformer(BaseTransformationEngine):
    """
    Transforms Azure EA billing data to FOCUS-compliant format.
    
    This class provides SQL-based transformation logic and field mapping
    rules for converting Azure EA API data to the FOCUS specification.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
    
    def _get_field_mappings(self) -> Dict[str, str]:
        """
        Define field mappings from Azure EA to FOCUS format.
        
        Returns:
            Dictionary mapping Azure EA fields to FOCUS fields
        """
        return {
            # Account and billing mappings
            "subscription_id": "billing_account_id",
            "subscription_name": "billing_account_name",
            "date": "usage_date",
            "extended_cost": "billed_cost",
            "unit_price": "list_unit_price",
            "consumed_quantity": "usage_quantity",
            "unit_of_measure": "usage_unit",
            
            # Resource mappings
            "instance_id": "resource_id",
            "product": "resource_name",
            "meter_category": "service_category",
            "consumed_service": "service_name",
            "resource_location": "region",
            "meter_region": "availability_zone",
            
            # Cost mappings
            "resource_rate": "effective_cost",
            
            # Provider
            "provider": "'Azure'"
        }
    
    def _get_transformation_sql(self) -> str:
        """
        Generate SQL transformation query for Azure EA to FOCUS conversion.
        
        Returns:
            SQL query string for transformation
        """
        return """
        INSERT INTO focus_billing_data
        SELECT 
            -- Generate unique ID
            CONCAT(
                coalesce(subscription_id, 'unknown'), '_',
                toString(toDate(date)), '_',
                coalesce(instance_id, 'unknown'), '_',
                randomString(8)
            ) as id,
            
            -- FOCUS Required Dimensions
            coalesce(subscription_id, 'unknown') as billing_account_id,
            coalesce(subscription_name, 'Unknown Subscription') as billing_account_name,
            coalesce('{currency}', 'USD') as billing_currency,
            toDate(date) as billing_period_start_date,
            toDate(date) as billing_period_end_date,
            
            -- FOCUS Cost Dimensions
            toDecimal64(coalesce(extended_cost, 0), 4) as billed_cost,
            toDecimal64(
                CASE 
                    WHEN resource_rate IS NOT NULL AND consumed_quantity IS NOT NULL 
                    THEN resource_rate * consumed_quantity
                    ELSE extended_cost
                END, 4
            ) as effective_cost,
            toDecimal64(
                CASE 
                    WHEN unit_price IS NOT NULL AND consumed_quantity IS NOT NULL 
                    THEN unit_price * consumed_quantity
                    ELSE extended_cost
                END, 4
            ) as list_cost,
            toDecimal64(coalesce(unit_price, 0), 4) as list_unit_price,
            
            -- FOCUS Usage Dimensions
            toDate(date) as usage_date,
            toDecimal64(coalesce(consumed_quantity, 0), 4) as usage_quantity,
            coalesce(unit_of_measure, 'Unknown') as usage_unit,
            
            -- FOCUS Resource Dimensions
            instance_id as resource_id,
            coalesce(product, 'Unknown Product') as resource_name,
            coalesce(meter_category, 'Other') as resource_type,
            
            -- FOCUS Service Dimensions with enhanced mapping
            CASE 
                WHEN lower(meter_category) LIKE '%compute%' OR 
                     lower(meter_category) LIKE '%virtual machine%' OR
                     lower(consumed_service) LIKE '%compute%' THEN 'Compute'
                WHEN lower(meter_category) LIKE '%storage%' OR 
                     lower(consumed_service) LIKE '%storage%' THEN 'Storage'
                WHEN lower(meter_category) LIKE '%network%' OR 
                     lower(meter_category) LIKE '%bandwidth%' OR
                     lower(consumed_service) LIKE '%network%' THEN 'Networking'
                WHEN lower(meter_category) LIKE '%database%' OR 
                     lower(meter_category) LIKE '%sql%' OR
                     lower(consumed_service) LIKE '%database%' THEN 'Database'
                WHEN lower(meter_category) LIKE '%analytics%' OR 
                     lower(meter_category) LIKE '%data%' OR
                     lower(consumed_service) LIKE '%analytics%' THEN 'Analytics'
                WHEN lower(meter_category) LIKE '%security%' OR 
                     lower(consumed_service) LIKE '%security%' THEN 'Security'
                WHEN lower(meter_category) LIKE '%management%' OR 
                     lower(consumed_service) LIKE '%monitor%' THEN 'Management'
                ELSE 'Other'
            END as service_category,
            coalesce(consumed_service, 'Unknown Service') as service_name,
            
            -- FOCUS Geographic Dimensions
            meter_region as availability_zone,
            coalesce(resource_location, 'Unknown Region') as region,
            
            -- FOCUS Provider Dimensions
            'Azure' as provider,
            
            -- Metadata
            now() as created_at,
            now() as updated_at,
            'azure_ea_api' as source_system
            
        FROM azure_ea_billing_detail
        WHERE date >= toDate('{start_date}')
          AND date <= toDate('{end_date}')
          AND extended_cost IS NOT NULL
          AND extended_cost > 0
          AND subscription_id IS NOT NULL
        ORDER BY date, subscription_id
        """
    
    def _get_validation_rules(self) -> Dict[str, Any]:
        """Return validation rules for Azure EA transformation"""
        return {
            "required_fields": [
                "billing_account_id",
                "usage_date", 
                "billed_cost",
                "billing_currency",
                "provider"
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
            ],
            "business_rules": {
                "min_cost": 0.01,  # Minimum cost threshold
                "max_cost": 1000000,  # Maximum cost threshold for validation
                "valid_currencies": ["USD", "EUR", "GBP", "CAD", "AUD"],
                "valid_providers": ["Azure"]
            }
        }
    
    def transform_record(self, azure_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single Azure EA record to FOCUS format.
        
        Args:
            azure_record: Azure EA billing record
            
        Returns:
            FOCUS-compliant billing record
        """
        focus_record = {}
        
        try:
            # Apply field mappings
            for azure_field, focus_field in self.field_mappings.items():
                if azure_field in azure_record:
                    if focus_field.startswith("'") and focus_field.endswith("'"):
                        # Handle literal values
                        focus_record[focus_field.strip("'")] = focus_field.strip("'")
                    else:
                        focus_record[focus_field] = azure_record[azure_field]
            
            # Apply business logic transformations
            focus_record = self._apply_business_rules(focus_record, azure_record)
            
            # Add metadata
            focus_record["created_at"] = datetime.utcnow()
            focus_record["updated_at"] = datetime.utcnow()
            focus_record["source_system"] = "azure_ea_api"
            
            return focus_record
            
        except Exception as e:
            logger.error(f"Error transforming Azure EA record: {e}")
            raise
    
    def _apply_business_rules(self, focus_record: Dict[str, Any], azure_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply FOCUS business rules and data quality transformations.
        
        Args:
            focus_record: Partially transformed FOCUS record
            azure_record: Original Azure EA record
            
        Returns:
            FOCUS record with business rules applied
        """
        # Generate unique ID
        if "subscription_id" in azure_record and "date" in azure_record:
            focus_record["id"] = f"{azure_record['subscription_id']}_{azure_record['date']}_{azure_record.get('instance_id', 'unknown')}"
        
        # Set billing period dates
        if "usage_date" in focus_record:
            focus_record["billing_period_start_date"] = focus_record["usage_date"]
            focus_record["billing_period_end_date"] = focus_record["usage_date"]
        
        # Default currency
        if "billing_currency" not in focus_record:
            focus_record["billing_currency"] = "USD"
        
        # Service category mapping
        meter_category = azure_record.get("meter_category", "").lower()
        if "compute" in meter_category:
            focus_record["service_category"] = "Compute"
        elif "storage" in meter_category:
            focus_record["service_category"] = "Storage"
        elif "network" in meter_category:
            focus_record["service_category"] = "Networking"
        elif "database" in meter_category:
            focus_record["service_category"] = "Database"
        else:
            focus_record["service_category"] = "Other"
        
        # Calculate effective cost if not present
        if "effective_cost" not in focus_record and "resource_rate" in azure_record and "consumed_quantity" in azure_record:
            focus_record["effective_cost"] = float(azure_record["resource_rate"]) * float(azure_record["consumed_quantity"])
        
        # Ensure provider is set
        focus_record["provider"] = "Azure"
        
        return focus_record
    
    def get_transformation_sql_with_params(self, start_date: str, end_date: str) -> str:
        """
        Get parameterized transformation SQL.
        
        Args:
            start_date: Start date for data extraction (YYYY-MM-DD)
            end_date: End date for data extraction (YYYY-MM-DD)
            
        Returns:
            Parameterized SQL query
        """
        return self.transformation_sql.format(
            start_date=start_date,
            end_date=end_date
        )
    
    def validate_focus_record(self, record: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate FOCUS record compliance.
        
        Args:
            record: FOCUS billing record to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = [
            "billing_account_id",
            "usage_date", 
            "billed_cost",
            "billing_currency",
            "provider"
        ]
        
        for field in required_fields:
            if field not in record or record[field] is None:
                return False, f"Missing required FOCUS field: {field}"
        
        # Validate data types
        if not isinstance(record.get("billed_cost"), (int, float)):
            return False, "billed_cost must be numeric"
        
        if record.get("billed_cost", 0) < 0:
            return False, "billed_cost cannot be negative"
        
        return True, None