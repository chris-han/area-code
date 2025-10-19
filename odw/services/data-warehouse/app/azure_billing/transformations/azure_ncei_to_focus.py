"""
Azure NCEI to FOCUS Transformation Module

Transforms Azure Blob Storage parquet files (NCEI data source) 
to FOCUS-compliant format. Replaces S3 CSV transformation.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .azure_ea_to_focus import BaseTransformationEngine

logger = logging.getLogger(__name__)


class AzureNCEIToFOCUSTransformer(BaseTransformationEngine):
    """
    Transforms Azure NCEI parquet data to FOCUS-compliant format.
    
    This class handles FOCUS-compliant parquet files from Azure Blob Storage
    with minimal transformation required.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.ncei_config = self._load_ncei_config()
    
    def _load_ncei_config(self) -> Dict[str, Any]:
        """Load NCEI-specific configuration"""
        return {
            "account_url": "https://finopsbilling.blob.core.chinacloudapi.cn",
            "default_container": "billing-data",
            "path_prefix": "focus-data/",
            "expected_format": "parquet",
            "focus_version": "1.0",
            "provider": "Azure"
        }

    def _get_field_mappings(self) -> Dict[str, str]:
        """Return field mappings from NCEI parquet to FOCUS format"""
        return {
            # Direct FOCUS mappings (NCEI should already be FOCUS-compliant)
            "billing_account_id": "billing_account_id",
            "billing_account_name": "billing_account_name", 
            "billing_currency": "billing_currency",
            "billing_period_start_date": "billing_period_start_date",
            "billing_period_end_date": "billing_period_end_date",
            "billed_cost": "billed_cost",
            "effective_cost": "effective_cost",
            "list_cost": "list_cost",
            "list_unit_price": "list_unit_price",
            "usage_date": "usage_date",
            "usage_quantity": "usage_quantity",
            "usage_unit": "usage_unit",
            "resource_id": "resource_id",
            "resource_name": "resource_name",
            "resource_type": "resource_type",
            "service_category": "service_category",
            "service_name": "service_name",
            "availability_zone": "availability_zone",
            "region": "region",
            "provider": "provider"
        }

    def _get_transformation_sql(self) -> str:
        """Generate SQL transformation query for NCEI parquet to FOCUS conversion"""
        return """
        INSERT INTO focus_billing_data
        SELECT 
            coalesce(billing_account_id, 'unknown') as billing_account_id,
            coalesce(billing_account_name, 'Unknown Account') as billing_account_name,
            coalesce(billing_currency, 'USD') as billing_currency,
            toDate(billing_period_start_date) as billing_period_start_date,
            toDate(billing_period_end_date) as billing_period_end_date,
            
            toDecimal64(coalesce(billed_cost, 0), 4) as billed_cost,
            toDecimal64(coalesce(effective_cost, billed_cost, 0), 4) as effective_cost,
            toDecimal64(coalesce(list_cost, billed_cost, 0), 4) as list_cost,
            toDecimal64(coalesce(list_unit_price, 0), 4) as list_unit_price,
            
            toDate(usage_date) as usage_date,
            toDecimal64(coalesce(usage_quantity, 0), 4) as usage_quantity,
            coalesce(usage_unit, 'Unknown') as usage_unit,
            
            resource_id as resource_id,
            coalesce(resource_name, 'Unknown Resource') as resource_name,
            coalesce(resource_type, 'Other') as resource_type,
            
            coalesce(service_category, 'Other') as service_category,
            coalesce(service_name, 'Unknown Service') as service_name,
            
            availability_zone as availability_zone,
            coalesce(region, 'Unknown Region') as region,
            
            coalesce(provider, 'Azure') as provider,
            
            now() as created_at,
            now() as updated_at,
            'azure_ncei' as source_system
            
        FROM azure_ncei_parquet_data
        WHERE usage_date >= toDate('{start_date}')
          AND usage_date <= toDate('{end_date}')
          AND billed_cost IS NOT NULL
          AND billed_cost >= 0
          AND billing_account_id IS NOT NULL
        ORDER BY usage_date, billing_account_id
        """

    def _get_validation_rules(self) -> Dict[str, Any]:
        """Return validation rules for NCEI transformation"""
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