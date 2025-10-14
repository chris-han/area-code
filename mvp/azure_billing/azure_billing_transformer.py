"""
Azure Billing Data Transformer

This module provides the AzureBillingTransformer class for transforming raw Azure EA API
data into the warehouse schema format with proper field mappings, type conversions,
and computed field derivation.
"""

import logging
import polars as pl
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
import json
import re

logger = logging.getLogger(__name__)


class AzureBillingTransformer:
    """
    Transformer for Azure billing data from EA API to warehouse schema
    
    Handles schema mapping, type conversions, computed fields, and JSON processing
    for Azure billing records.
    """
    
    @staticmethod
    def transform_raw_data(raw_data: pl.DataFrame, tracking_patterns: Optional[List[Tuple]] = None) -> pl.DataFrame:
        """
        Transform raw API data to warehouse schema
        
        Args:
            raw_data: Raw DataFrame from Azure EA API
            tracking_patterns: Optional resource tracking patterns for application
            
        Returns:
            Transformed DataFrame matching warehouse schema
            
        Raises:
            ValueError: If required fields are missing or transformation fails
        """
        try:
            logger.info(f"Starting transformation of {len(raw_data)} raw billing records")
            
            # Validate input DataFrame
            if len(raw_data) == 0:
                logger.warning("Empty DataFrame provided for transformation")
                return AzureBillingTransformer._create_empty_transformed_df()
            
            # Start with a copy of the raw data
            df = raw_data.clone()
            
            # Apply field mappings and type conversions
            df = AzureBillingTransformer._apply_field_mappings(df)
            
            # Convert data types
            df = AzureBillingTransformer._convert_data_types(df)
            
            # Derive computed fields
            df = AzureBillingTransformer._derive_computed_fields(df)
            
            # Clean and process JSON fields
            df = AzureBillingTransformer._process_json_fields(df)
            
            logger.info(f"Successfully transformed {len(df)} billing records")
            return df
            
        except Exception as e:
            logger.error(f"Failed to transform raw data: {str(e)}")
            raise
    
    @staticmethod
    def _create_empty_transformed_df() -> pl.DataFrame:
        """
        Create empty DataFrame with correct schema for transformed data
        
        Returns:
            Empty DataFrame with warehouse schema
        """
        schema = {
            'id': pl.Utf8,
            'account_owner_id': pl.Utf8,
            'account_name': pl.Utf8,
            'service_administrator_id': pl.Utf8,
            'subscription_id': pl.Int64,
            'subscription_guid': pl.Utf8,
            'subscription_name': pl.Utf8,
            'date': pl.Date,
            'month': pl.Int32,
            'day': pl.Int32,
            'year': pl.Int32,
            'product': pl.Utf8,
            'meter_id': pl.Utf8,
            'meter_category': pl.Utf8,
            'meter_sub_category': pl.Utf8,
            'meter_region': pl.Utf8,
            'meter_name': pl.Utf8,
            'consumed_quantity': pl.Float64,
            'resource_rate': pl.Float64,
            'extended_cost': pl.Float64,
            'resource_location': pl.Utf8,
            'consumed_service': pl.Utf8,
            'instance_id': pl.Utf8,
            'service_info1': pl.Utf8,
            'service_info2': pl.Utf8,
            'additional_info': pl.Utf8,
            'tags': pl.Utf8,
            'store_service_identifier': pl.Utf8,
            'department_name': pl.Utf8,
            'cost_center': pl.Utf8,
            'unit_of_measure': pl.Utf8,
            'resource_group': pl.Utf8,
            'extended_cost_tax': pl.Float64,
            'resource_tracking': pl.Utf8,
            'resource_name': pl.Utf8,
            'vm_name': pl.Utf8,
            'latest_resource_type': pl.Utf8,
            'newmonth': pl.Utf8,
            'month_date': pl.Date,
            'sku': pl.Utf8,
            'cmdb_mapped_application_service': pl.Utf8,
            'ppm_billing_item': pl.Utf8,
            'ppm_id_owner': pl.Utf8,
            'ppm_io_cc': pl.Utf8
        }
        
        return pl.DataFrame(schema=schema)
    
    @staticmethod
    def _apply_field_mappings(df: pl.DataFrame) -> pl.DataFrame:
        """
        Apply field name mappings from Azure EA API to warehouse schema
        
        Args:
            df: DataFrame with raw API field names
            
        Returns:
            DataFrame with mapped field names
        """
        try:
            # Define field mappings from API to warehouse schema
            field_mappings = {
                # Direct mappings (same name)
                'accountOwnerId': 'account_owner_id',
                'accountName': 'account_name',
                'serviceAdministratorId': 'service_administrator_id',
                'subscriptionId': 'subscription_id',
                'subscriptionGuid': 'subscription_guid',
                'subscriptionName': 'subscription_name',
                'meterId': 'meter_id',
                'meterCategory': 'meter_category',
                'meterSubCategory': 'meter_sub_category',
                'meterRegion': 'meter_region',
                'meterName': 'meter_name',
                'consumedQuantity': 'consumed_quantity',
                'resourceRate': 'resource_rate',
                'extendedCost': 'extended_cost',
                'resourceLocation': 'resource_location',
                'consumedService': 'consumed_service',
                'instanceId': 'instance_id',
                'serviceInfo1': 'service_info1',
                'serviceInfo2': 'service_info2',
                'additionalInfo': 'additional_info',
                'storeServiceIdentifier': 'store_service_identifier',
                'departmentName': 'department_name',
                'costCenter': 'cost_center',
                'unitOfMeasure': 'unit_of_measure',
                'resourceGroup': 'resource_group'
            }
            
            # Apply mappings where columns exist
            for api_field, warehouse_field in field_mappings.items():
                if api_field in df.columns:
                    df = df.rename({api_field: warehouse_field})
            
            # Ensure required fields exist (create with null if missing)
            required_fields = ['instance_id', 'date']
            for field in required_fields:
                if field not in df.columns:
                    logger.warning(f"Required field '{field}' missing, creating with null values")
                    df = df.with_columns(pl.lit(None).alias(field))
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to apply field mappings: {str(e)}")
            raise
    
    @staticmethod
    def _convert_data_types(df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert data types to match warehouse schema
        
        Args:
            df: DataFrame with mapped field names
            
        Returns:
            DataFrame with correct data types
        """
        try:
            logger.debug("Converting data types to warehouse schema")
            
            # Date conversions
            if 'date' in df.columns:
                df = df.with_columns(
                    pl.col('date').str.to_date('%Y-%m-%d', strict=False).alias('date')
                )
            
            # Numeric conversions
            numeric_fields = [
                'subscription_id', 'consumed_quantity', 'resource_rate', 
                'extended_cost', 'month', 'day', 'year'
            ]
            
            for field in numeric_fields:
                if field in df.columns:
                    if field in ['month', 'day', 'year']:
                        # Integer fields
                        df = df.with_columns(
                            pl.col(field).cast(pl.Int32, strict=False).alias(field)
                        )
                    elif field == 'subscription_id':
                        # Big integer field
                        df = df.with_columns(
                            pl.col(field).cast(pl.Int64, strict=False).alias(field)
                        )
                    else:
                        # Float fields
                        df = df.with_columns(
                            pl.col(field).cast(pl.Float64, strict=False).alias(field)
                        )
            
            # String fields (ensure they're strings)
            string_fields = [
                'account_owner_id', 'account_name', 'service_administrator_id',
                'subscription_guid', 'subscription_name', 'product', 'meter_id',
                'meter_category', 'meter_sub_category', 'meter_region', 'meter_name',
                'resource_location', 'consumed_service', 'instance_id', 'service_info1',
                'service_info2', 'store_service_identifier', 'department_name',
                'cost_center', 'unit_of_measure', 'resource_group'
            ]
            
            for field in string_fields:
                if field in df.columns:
                    df = df.with_columns(
                        pl.col(field).cast(pl.Utf8, strict=False).alias(field)
                    )
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to convert data types: {str(e)}")
            raise
    
    @staticmethod
    def _derive_computed_fields(df: pl.DataFrame) -> pl.DataFrame:
        """
        Derive computed fields from existing data
        
        Args:
            df: DataFrame with basic fields
            
        Returns:
            DataFrame with computed fields added
        """
        try:
            logger.debug("Deriving computed fields")
            
            # Derive month_date from date field
            if 'date' in df.columns:
                df = df.with_columns([
                    # month_date: first day of the month from date
                    pl.col('date').dt.truncate('1mo').alias('month_date'),
                    
                    # Extract month, day, year from date
                    pl.col('date').dt.month().alias('month'),
                    pl.col('date').dt.day().alias('day'),
                    pl.col('date').dt.year().alias('year')
                ])
            
            # Derive newmonth field (YYYY-MM format)
            if 'date' in df.columns:
                df = df.with_columns(
                    pl.col('date').dt.strftime('%Y-%m').alias('newmonth')
                )
            
            # Derive extended_cost_tax (extended_cost with tax calculation)
            if 'extended_cost' in df.columns:
                df = df.with_columns(
                    # For now, assume no tax adjustment (multiply by 1.0)
                    # This can be modified based on business rules
                    (pl.col('extended_cost') * 1.0).alias('extended_cost_tax')
                )
            
            # Generate unique ID if not present
            if 'id' not in df.columns:
                df = df.with_row_count('id').with_columns(
                    pl.col('id').cast(pl.Utf8).alias('id')
                )
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to derive computed fields: {str(e)}")
            raise
    
    @staticmethod
    def _process_json_fields(df: pl.DataFrame) -> pl.DataFrame:
        """
        Process JSON fields (tags, additional_info) and extract structured data
        
        Args:
            df: DataFrame with JSON fields to process
            
        Returns:
            DataFrame with processed JSON fields and extracted values
        """
        try:
            logger.debug("Processing JSON fields")
            
            # Process tags field
            if 'tags' in df.columns:
                df = df.with_columns([
                    # Clean and validate tags JSON
                    pl.col('tags').map_elements(
                        AzureBillingTransformer._clean_json_string,
                        return_dtype=pl.Utf8
                    ).alias('tags'),
                    
                    # Extract specific tag values
                    pl.col('tags').map_elements(
                        lambda x: AzureBillingTransformer._extract_tag_value(x, 'app'),
                        return_dtype=pl.Utf8
                    ).alias('ppm_billing_item'),
                    
                    pl.col('tags').map_elements(
                        lambda x: AzureBillingTransformer._extract_tag_value(x, 'ppm_billing_owner'),
                        return_dtype=pl.Utf8
                    ).alias('ppm_id_owner'),
                    
                    pl.col('tags').map_elements(
                        lambda x: AzureBillingTransformer._extract_tag_value(x, 'ppm_io_cc'),
                        return_dtype=pl.Utf8
                    ).alias('ppm_io_cc')
                ])
            
            # Process additional_info field
            if 'additional_info' in df.columns:
                df = df.with_columns(
                    pl.col('additional_info').map_elements(
                        AzureBillingTransformer._clean_json_string,
                        return_dtype=pl.Utf8
                    ).alias('additional_info')
                )
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to process JSON fields: {str(e)}")
            raise
    
    @staticmethod
    def _clean_json_string(json_str: Optional[str]) -> Optional[str]:
        """
        Clean and validate JSON string
        
        Args:
            json_str: Raw JSON string from API
            
        Returns:
            Cleaned JSON string or None if invalid
        """
        if not json_str or json_str.strip() == '':
            return None
        
        try:
            # Try to parse and re-serialize to ensure valid JSON
            parsed = json.loads(json_str)
            return json.dumps(parsed, separators=(',', ':'))
        except (json.JSONDecodeError, TypeError):
            # Log warning but don't fail the entire transformation
            logger.warning(f"Invalid JSON encountered: {json_str[:100]}...")
            return None
    
    @staticmethod
    def _extract_tag_value(tags_json: Optional[str], tag_key: str) -> Optional[str]:
        """
        Extract specific tag value from tags JSON
        
        Args:
            tags_json: JSON string containing tags
            tag_key: Key to extract from tags
            
        Returns:
            Tag value or None if not found
        """
        if not tags_json:
            return None
        
        try:
            tags = json.loads(tags_json)
            if isinstance(tags, dict):
                return tags.get(tag_key)
        except (json.JSONDecodeError, TypeError):
            pass
        
        return None 
   
    @staticmethod
    def clean_json_string(json_str: Optional[str]) -> Optional[str]:
        """
        Public method to clean JSON strings with comprehensive error handling
        
        Args:
            json_str: Raw JSON string that may contain malformed data
            
        Returns:
            Cleaned and validated JSON string or None if unrecoverable
        """
        if not json_str or not isinstance(json_str, str):
            return None
        
        # Remove common formatting issues
        cleaned = json_str.strip()
        
        # Handle empty or whitespace-only strings
        if not cleaned or cleaned in ['{}', '[]', 'null', 'NULL']:
            return None
        
        try:
            # First attempt: direct parsing
            parsed = json.loads(cleaned)
            return json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
            
        except json.JSONDecodeError:
            try:
                # Second attempt: fix common issues
                # Remove trailing commas
                cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
                
                # Fix unquoted keys (basic cases)
                cleaned = re.sub(r'(\w+):', r'"\1":', cleaned)
                
                # Fix single quotes to double quotes
                cleaned = cleaned.replace("'", '"')
                
                parsed = json.loads(cleaned)
                return json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
                
            except json.JSONDecodeError:
                # Third attempt: extract key-value pairs manually
                try:
                    return AzureBillingTransformer._extract_key_value_pairs(json_str)
                except Exception:
                    logger.warning(f"Unable to parse JSON, returning null: {json_str[:100]}...")
                    return None
        
        except Exception as e:
            logger.warning(f"Unexpected error cleaning JSON: {str(e)}")
            return None
    
    @staticmethod
    def _extract_key_value_pairs(malformed_json: str) -> Optional[str]:
        """
        Extract key-value pairs from malformed JSON using regex
        
        Args:
            malformed_json: Malformed JSON string
            
        Returns:
            Valid JSON string with extracted pairs or None
        """
        try:
            # Pattern to match key-value pairs
            pattern = r'["\']?(\w+)["\']?\s*:\s*["\']?([^,}]+?)["\']?(?=\s*[,}])'
            matches = re.findall(pattern, malformed_json)
            
            if matches:
                # Build dictionary from matches
                result = {}
                for key, value in matches:
                    # Clean up the value
                    value = value.strip().strip('"\'')
                    result[key] = value
                
                return json.dumps(result, separators=(',', ':'))
            
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def extract_structured_tags(tags_json: Optional[str]) -> Dict[str, Optional[str]]:
        """
        Extract all structured data from tags JSON with error handling
        
        Args:
            tags_json: JSON string containing resource tags
            
        Returns:
            Dictionary with extracted tag values (app, ppm_billing_item, etc.)
        """
        result = {
            'app': None,
            'ppm_billing_item': None,
            'ppm_billing_owner': None,
            'ppm_io_cc': None,
            'cost_center': None,
            'environment': None,
            'project': None
        }
        
        if not tags_json:
            return result
        
        try:
            # Clean the JSON first
            cleaned_json = AzureBillingTransformer.clean_json_string(tags_json)
            if not cleaned_json:
                return result
            
            tags = json.loads(cleaned_json)
            if not isinstance(tags, dict):
                return result
            
            # Extract known tag keys (case-insensitive)
            for key, value in tags.items():
                key_lower = key.lower()
                
                if key_lower in ['app', 'application']:
                    result['app'] = str(value) if value else None
                elif key_lower in ['ppm_billing_item', 'billing_item']:
                    result['ppm_billing_item'] = str(value) if value else None
                elif key_lower in ['ppm_billing_owner', 'billing_owner', 'owner']:
                    result['ppm_billing_owner'] = str(value) if value else None
                elif key_lower in ['ppm_io_cc', 'cost_center', 'costcenter']:
                    result['ppm_io_cc'] = str(value) if value else None
                elif key_lower == 'cost_center':
                    result['cost_center'] = str(value) if value else None
                elif key_lower in ['environment', 'env']:
                    result['environment'] = str(value) if value else None
                elif key_lower in ['project', 'proj']:
                    result['project'] = str(value) if value else None
            
            return result
            
        except Exception as e:
            logger.warning(f"Error extracting structured tags: {str(e)}")
            return result
    
    @staticmethod
    def extract_additional_info_data(additional_info_json: Optional[str]) -> Dict[str, Optional[str]]:
        """
        Extract structured data from additional_info JSON field
        
        Args:
            additional_info_json: JSON string containing additional resource information
            
        Returns:
            Dictionary with extracted additional info values
        """
        result = {
            'resource_type': None,
            'location': None,
            'sku_name': None,
            'service_tier': None
        }
        
        if not additional_info_json:
            return result
        
        try:
            # Clean the JSON first
            cleaned_json = AzureBillingTransformer.clean_json_string(additional_info_json)
            if not cleaned_json:
                return result
            
            info = json.loads(cleaned_json)
            if not isinstance(info, dict):
                return result
            
            # Extract known fields (case-insensitive)
            for key, value in info.items():
                key_lower = key.lower()
                
                if key_lower in ['resourcetype', 'resource_type', 'type']:
                    result['resource_type'] = str(value) if value else None
                elif key_lower in ['location', 'region']:
                    result['location'] = str(value) if value else None
                elif key_lower in ['skuname', 'sku_name', 'sku']:
                    result['sku_name'] = str(value) if value else None
                elif key_lower in ['servicetier', 'service_tier', 'tier']:
                    result['service_tier'] = str(value) if value else None
            
            return result
            
        except Exception as e:
            logger.warning(f"Error extracting additional info data: {str(e)}")
            return result   
 
    @staticmethod
    def derive_vm_specific_fields(df: pl.DataFrame) -> pl.DataFrame:
        """
        Derive VM-specific business logic fields (SKU, resource_name, vm_name)
        
        Args:
            df: DataFrame with basic billing fields
            
        Returns:
            DataFrame with VM-specific fields derived
        """
        try:
            logger.debug("Deriving VM-specific business logic fields")
            
            # Derive SKU based on meter_category and product
            sku_expr = pl.when(
                (pl.col('meter_category') == 'Virtual Machines') & 
                pl.col('product').is_not_null()
            ).then(
                # Extract SKU from product field for VMs
                pl.col('product').str.extract(r'([A-Z]\d+[a-z]*\s*v\d+)', 1)
            )
            
            # Add fallbacks based on available columns
            if 'meter_sub_category' in df.columns:
                sku_expr = sku_expr.when(pl.col('meter_category') == 'Storage').then(
                    pl.col('meter_sub_category')
                )
            
            if 'meter_name' in df.columns:
                sku_expr = sku_expr.otherwise(pl.col('meter_name'))
            else:
                sku_expr = sku_expr.otherwise(pl.col('product'))
            
            df = df.with_columns([sku_expr.alias('sku')])
            
            # Derive resource_name from instance_id and additional_info
            df = df.with_columns([
                pl.when(pl.col('instance_id').is_not_null())
                .then(
                    # Extract resource name from instance_id path
                    pl.col('instance_id').str.extract(r'/([^/]+)$', 1)
                    .fill_null(
                        # Fallback: extract from additional_info if available
                        pl.col('additional_info').map_elements(
                            AzureBillingTransformer._extract_resource_name_from_json,
                            return_dtype=pl.Utf8
                        )
                    )
                )
                .otherwise(None)
                .alias('resource_name')
            ])
            
            # Derive vm_name with special AKS handling
            df = df.with_columns([
                pl.when(
                    (pl.col('meter_category') == 'Virtual Machines') &
                    pl.col('instance_id').is_not_null()
                )
                .then(
                    pl.when(
                        # Special handling for AKS nodes
                        pl.col('instance_id').str.contains('aks-')
                    )
                    .then(
                        # For AKS, extract node pool name
                        (pl.col('instance_id').str.extract(r'aks-([^-]+)', 1)
                         .str.to_uppercase() + pl.lit('-NODE'))
                    )
                    .otherwise(
                        # For regular VMs, use resource_name
                        pl.col('resource_name')
                    )
                )
                .otherwise(None)
                .alias('vm_name')
            ])
            
            # Derive latest_resource_type from meter_category and service info
            resource_type_expr = pl.when(pl.col('meter_category') == 'Virtual Machines').then(pl.lit('VirtualMachine'))
            resource_type_expr = resource_type_expr.when(pl.col('meter_category') == 'Storage').then(pl.lit('StorageAccount'))
            resource_type_expr = resource_type_expr.when(pl.col('meter_category') == 'Networking').then(pl.lit('NetworkInterface'))
            
            # Add consumed_service logic only if column exists
            if 'consumed_service' in df.columns:
                resource_type_expr = resource_type_expr.when(pl.col('consumed_service').str.contains('Microsoft.Compute')).then(pl.lit('Compute'))
                resource_type_expr = resource_type_expr.when(pl.col('consumed_service').str.contains('Microsoft.Storage')).then(pl.lit('Storage'))
                resource_type_expr = resource_type_expr.when(pl.col('consumed_service').str.contains('Microsoft.Network')).then(pl.lit('Network'))
                resource_type_expr = resource_type_expr.otherwise(pl.col('consumed_service').str.extract(r'Microsoft\.(\w+)', 1))
            else:
                resource_type_expr = resource_type_expr.otherwise(pl.lit(None))
            
            df = df.with_columns([resource_type_expr.alias('latest_resource_type')])
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to derive VM-specific fields: {str(e)}")
            raise
    
    @staticmethod
    def _extract_resource_name_from_json(additional_info_json: Optional[str]) -> Optional[str]:
        """
        Extract resource name from additional_info JSON
        
        Args:
            additional_info_json: JSON string containing additional resource info
            
        Returns:
            Resource name or None if not found
        """
        if not additional_info_json:
            return None
        
        try:
            info_data = AzureBillingTransformer.extract_additional_info_data(additional_info_json)
            
            # Try different possible field names for resource name
            for field in ['resource_name', 'name', 'resourceName', 'vmName']:
                if field in info_data and info_data[field]:
                    return info_data[field]
            
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def apply_business_rules(df: pl.DataFrame) -> pl.DataFrame:
        """
        Apply comprehensive business rules for Azure billing data
        
        Args:
            df: DataFrame with transformed billing data
            
        Returns:
            DataFrame with business rules applied
        """
        try:
            logger.debug("Applying business rules to billing data")
            
            # Apply VM-specific derivations
            df = AzureBillingTransformer.derive_vm_specific_fields(df)
            
            # Apply cost center mapping from tags
            cost_center_expr = pl.when(pl.col('ppm_io_cc').is_not_null()).then(pl.col('ppm_io_cc'))
            
            # Check if cost_center column already exists
            if 'cost_center' in df.columns:
                cost_center_expr = cost_center_expr.when(pl.col('cost_center').is_not_null()).then(pl.col('cost_center'))
            
            cost_center_expr = cost_center_expr.otherwise(
                # Extract from tags if available
                pl.col('tags').map_elements(
                    lambda x: AzureBillingTransformer._extract_tag_value(x, 'cost_center'),
                    return_dtype=pl.Utf8
                )
            )
            
            df = df.with_columns([cost_center_expr.alias('cost_center')])
            
            # Normalize resource group names (remove /resourceGroups/ prefix if present)
            df = df.with_columns([
                pl.when(pl.col('resource_group').str.contains('/resourceGroups/'))
                .then(
                    pl.col('resource_group').str.extract(r'/resourceGroups/([^/]+)', 1)
                )
                .otherwise(pl.col('resource_group'))
                .alias('resource_group')
            ])
            
            # Set default values for required fields
            df = df.with_columns([
                # Ensure month_date is set (required field)
                pl.when(pl.col('month_date').is_null())
                .then(pl.col('date').dt.truncate('1mo'))
                .otherwise(pl.col('month_date'))
                .alias('month_date'),
                
                # Ensure instance_id is not null (required field)
                pl.when(pl.col('instance_id').is_null())
                .then(pl.lit('unknown'))
                .otherwise(pl.col('instance_id'))
                .alias('instance_id')
            ])
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to apply business rules: {str(e)}")
            raise