"""
FOCUS Data Transformation Pipeline

Handles loading Parquet files, transforming column names and data types,
and preparing data for ClickHouse insertion.
"""

import re
import hashlib
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass

from .file_discovery import ParquetFileInfo
from .config import get_focus_config


@dataclass
class TransformationResult:
    """Result of data transformation operation"""
    success: bool
    rows_processed: int
    transformed_data: Optional[pd.DataFrame] = None
    error_message: Optional[str] = None
    transformation_stats: Optional[Dict[str, Any]] = None


class FocusDataTransformer:
    """
    Transforms FOCUS Parquet data for ClickHouse insertion.
    
    Handles:
    - Column name conversion from PascalCase to snake_case
    - Data type conversions (INT96 to DateTime64, decimals, booleans)
    - Addition of computed columns (id, source_system, timestamps)
    - Schema validation and error handling
    """
    
    def __init__(self):
        self.source_system = "focus_parquet"
        
    def transform_parquet_file(self, file_info: ParquetFileInfo) -> TransformationResult:
        """
        Transform a single Parquet file for ClickHouse insertion.
        
        Args:
            file_info: Information about the Parquet file to transform
            
        Returns:
            TransformationResult with transformed data or error information
        """
        try:
            # Load Parquet file
            df = self._load_parquet_file(file_info.file_path)
            
            if df.empty:
                return TransformationResult(
                    success=True,
                    rows_processed=0,
                    transformed_data=pd.DataFrame(),
                    transformation_stats={'empty_file': True}
                )
            
            # Transform column names to snake_case
            df = self._transform_column_names(df)
            
            # Apply data type transformations
            df = self._transform_data_types(df, file_info.dataset_type)
            
            # Add computed columns
            df = self._add_computed_columns(df, file_info)
            
            # Validate transformed data
            validation_result = self._validate_transformed_data(df, file_info.dataset_type)
            if not validation_result['valid']:
                return TransformationResult(
                    success=False,
                    rows_processed=0,
                    error_message=f"Data validation failed: {validation_result['errors']}"
                )
            
            # Generate transformation statistics
            stats = self._generate_transformation_stats(df, file_info)
            
            return TransformationResult(
                success=True,
                rows_processed=len(df),
                transformed_data=df,
                transformation_stats=stats
            )
            
        except Exception as e:
            return TransformationResult(
                success=False,
                rows_processed=0,
                error_message=f"Transformation failed: {str(e)}"
            )
    
    def _load_parquet_file(self, file_path: Path) -> pd.DataFrame:
        """Load Parquet file using pyarrow with schema preservation"""
        try:
            # Read with pyarrow first to handle complex types
            table = pq.read_table(file_path)
            
            # Convert to pandas with proper type handling
            df = table.to_pandas(
                timestamp_as_object=True,  # Preserve timestamp precision
                types_mapper=pd.ArrowDtype  # Use Arrow types where possible
            )
            
            return df
            
        except Exception as e:
            # Fallback to pandas direct read
            try:
                return pd.read_parquet(file_path, engine='pyarrow')
            except Exception as fallback_e:
                raise Exception(f"Failed to load Parquet file: {e}. Fallback also failed: {fallback_e}")
    
    def _transform_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform column names from PascalCase to snake_case"""
        column_mapping = {}
        
        for col in df.columns:
            snake_case_col = self._pascal_to_snake_case(col)
            column_mapping[col] = snake_case_col
        
        return df.rename(columns=column_mapping)
    
    def _pascal_to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case"""
        # Handle special cases and acronyms
        name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)  # Handle acronyms
        name = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', name)      # Handle normal case
        return name.lower()
    
    def _transform_data_types(self, df: pd.DataFrame, dataset_type: str) -> pd.DataFrame:
        """Apply data type transformations for ClickHouse compatibility"""
        df = df.copy()
        
        for col in df.columns:
            try:
                df[col] = self._transform_column_type(df[col], col)
            except Exception as e:
                print(f"Warning: Failed to transform column {col}: {e}")
                # Keep original column if transformation fails
                continue
        
        return df
    
    def _transform_column_type(self, series: pd.Series, column_name: str) -> pd.Series:
        """Transform a single column's data type"""
        
        # Handle datetime columns (INT96 timestamps from Parquet)
        if self._is_datetime_column(series, column_name):
            return self._convert_to_datetime(series)
        
        # Handle decimal/numeric columns
        elif self._is_decimal_column(series, column_name):
            return self._convert_to_decimal(series)
        
        # Handle boolean columns
        elif self._is_boolean_column(series, column_name):
            return self._convert_to_boolean(series)
        
        # Handle JSON columns (keep as string for ClickHouse compatibility)
        elif self._is_json_column(column_name):
            return self._convert_to_json_string(series)
        
        # Handle string columns
        elif series.dtype == 'object':
            return self._convert_to_string(series)
        
        # Return as-is for other types
        return series
    
    def _is_datetime_column(self, series: pd.Series, column_name: str) -> bool:
        """Check if column should be treated as datetime"""
        datetime_patterns = [
            'date', 'time', 'period_start', 'period_end', 
            'submitted_time', 'created_at', 'updated_at'
        ]
        
        # Check column name patterns
        if any(pattern in column_name.lower() for pattern in datetime_patterns):
            return True
        
        # Check if series contains datetime-like data
        if pd.api.types.is_datetime64_any_dtype(series):
            return True
        
        # Check for timestamp integers (INT96 from Parquet)
        if series.dtype in ['int64', 'int32'] and not series.isna().all():
            # Sample a few values to see if they look like timestamps
            sample = series.dropna().head(5)
            if len(sample) > 0:
                # Check if values are in reasonable timestamp range
                min_val, max_val = sample.min(), sample.max()
                # Reasonable range: 2020-01-01 to 2030-12-31 in various timestamp formats
                if 1577836800 <= min_val <= 1924991999:  # Unix timestamp seconds
                    return True
                elif 1577836800000 <= min_val <= 1924991999000:  # Unix timestamp milliseconds
                    return True
        
        return False
    
    def _is_decimal_column(self, series: pd.Series, column_name: str) -> bool:
        """Check if column should be treated as decimal"""
        decimal_patterns = [
            'cost', 'price', 'amount', 'quantity', 'rate', 'committed'
        ]
        
        # Check column name patterns
        if any(pattern in column_name.lower() for pattern in decimal_patterns):
            return True
        
        # Check if series contains numeric data that should be decimal
        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_integer_dtype(series):
            return True
        
        return False
    
    def _is_boolean_column(self, series: pd.Series, column_name: str) -> bool:
        """Check if column should be treated as boolean"""
        boolean_patterns = [
            'is_', 'has_', 'can_', 'should_', 'eligible', 'enabled'
        ]
        
        # Check column name patterns
        if any(column_name.lower().startswith(pattern) for pattern in boolean_patterns):
            return True
        
        # Check if series contains boolean-like data
        if series.dtype == 'bool':
            return True
        
        # Check for string boolean values
        if series.dtype == 'object':
            unique_vals = set(str(v).lower() for v in series.dropna().unique())
            boolean_vals = {'true', 'false', '1', '0', 'yes', 'no'}
            if unique_vals.issubset(boolean_vals):
                return True
        
        return False
    
    def _is_json_column(self, column_name: str) -> bool:
        """Check if column should be treated as JSON"""
        json_patterns = [
            'tags', 'metadata', 'attributes', 'details', 'properties'
        ]
        
        return any(pattern in column_name.lower() for pattern in json_patterns)
    
    def _convert_to_datetime(self, series: pd.Series) -> pd.Series:
        """Convert series to datetime with proper timezone handling"""
        try:
            # Handle different datetime formats
            if pd.api.types.is_datetime64_any_dtype(series):
                # Already datetime, ensure UTC timezone
                if series.dt.tz is None:
                    return series.dt.tz_localize('UTC')
                else:
                    return series.dt.tz_convert('UTC')
            
            # Handle integer timestamps
            elif series.dtype in ['int64', 'int32']:
                # Try different timestamp formats
                try:
                    # Try Unix timestamp in seconds
                    return pd.to_datetime(series, unit='s', utc=True)
                except (ValueError, OSError):
                    try:
                        # Try Unix timestamp in milliseconds
                        return pd.to_datetime(series, unit='ms', utc=True)
                    except (ValueError, OSError):
                        # Try Unix timestamp in nanoseconds
                        return pd.to_datetime(series, unit='ns', utc=True)
            
            # Handle string datetime
            else:
                return pd.to_datetime(series, utc=True, errors='coerce')
                
        except Exception:
            # Return as-is if conversion fails
            return series
    
    def _convert_to_decimal(self, series: pd.Series) -> pd.Series:
        """Convert series to decimal with proper precision"""
        def safe_decimal_convert(value):
            if pd.isna(value):
                return None

            # Handle empty strings and whitespace
            if isinstance(value, str):
                value = value.strip()
                if value == '' or value.lower() == 'nan' or value.lower() == 'null':
                    return None

            try:
                # Convert to Decimal with appropriate precision
                decimal_val = Decimal(str(value))
                # Limit to ClickHouse Decimal(38,18) precision
                return decimal_val.quantize(Decimal('0.000000000000000001'))
            except (InvalidOperation, ValueError, TypeError):
                return None

        return series.apply(safe_decimal_convert)
    
    def _convert_to_boolean(self, series: pd.Series) -> pd.Series:
        """Convert series to boolean (UInt8 for ClickHouse)"""
        def safe_boolean_convert(value):
            if pd.isna(value):
                return None
            
            if isinstance(value, bool):
                return 1 if value else 0
            
            str_val = str(value).lower().strip()
            if str_val in ['true', '1', 'yes', 'y']:
                return 1
            elif str_val in ['false', '0', 'no', 'n']:
                return 0
            else:
                return None
        
        return series.apply(safe_boolean_convert)
    
    def _convert_to_json_string(self, series: pd.Series) -> pd.Series:
        """Convert series to JSON string format"""
        def safe_json_convert(value):
            if pd.isna(value):
                return None
            
            # If already a string, validate it's proper JSON
            if isinstance(value, str):
                try:
                    import json
                    json.loads(value)  # Validate JSON
                    return value
                except (json.JSONDecodeError, TypeError):
                    # If not valid JSON, wrap in quotes
                    return json.dumps(value)
            
            # Convert other types to JSON string
            try:
                import json
                return json.dumps(value)
            except (TypeError, ValueError):
                return str(value)
        
        return series.apply(safe_json_convert)
    
    def _convert_to_string(self, series: pd.Series) -> pd.Series:
        """Convert series to string with null handling"""
        return series.astype('string').where(series.notna(), None)
    
    def _add_computed_columns(self, df: pd.DataFrame, file_info: ParquetFileInfo) -> pd.DataFrame:
        """Add computed columns required for ClickHouse storage"""
        df = df.copy()
        
        # Add deterministic ID column
        df['id'] = self._generate_row_ids(df, file_info)
        
        # Add source system identifier
        df['source_system'] = self.source_system
        
        # Add audit timestamps
        current_time = datetime.now(timezone.utc)
        df['created_at'] = current_time
        df['updated_at'] = current_time
        
        return df
    
    def _generate_row_ids(self, df: pd.DataFrame, file_info: ParquetFileInfo) -> pd.Series:
        """Generate deterministic row IDs based on key columns"""
        
        # Key columns for ID generation (adjust based on dataset type)
        if file_info.dataset_type == 'cost_usage':
            key_columns = [
                'billing_account_id', 'usage_date', 'resource_id', 
                'sku_meter', 'charge_period_start'
            ]
        else:  # contract_commitment
            key_columns = [
                'contract_commitment_id', 'billing_account_id', 
                'commitment_discount_id'
            ]
        
        # Use available key columns
        available_key_columns = [col for col in key_columns if col in df.columns]
        
        if not available_key_columns:
            # Fallback: use row number with file info
            return [
                hashlib.sha256(f"{file_info.relative_path}:{i}".encode()).hexdigest()[:16]
                for i in range(len(df))
            ]
        
        # Generate IDs from key columns
        ids = []
        for idx, row in df.iterrows():
            key_parts = [str(row.get(col, '')) for col in available_key_columns]
            key_parts.append(str(idx))  # Add row index for uniqueness
            key_string = ':'.join(key_parts)
            row_id = hashlib.sha256(key_string.encode()).hexdigest()[:16]
            ids.append(row_id)
        
        return pd.Series(ids, index=df.index)
    
    def _validate_transformed_data(self, df: pd.DataFrame, dataset_type: str) -> Dict[str, Any]:
        """Validate transformed data meets requirements"""
        errors = []
        
        # Check required columns exist
        required_columns = self._get_required_columns(dataset_type)
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
        
        # Check for completely empty DataFrame
        if df.empty:
            return {'valid': True, 'warnings': ['Empty DataFrame']}
        
        # Check ID column uniqueness
        if 'id' in df.columns:
            duplicate_ids = df['id'].duplicated().sum()
            if duplicate_ids > 0:
                errors.append(f"Found {duplicate_ids} duplicate IDs")
        
        # Check for reasonable data ranges
        warnings = []
        
        # Check date columns are reasonable
        date_columns = [col for col in df.columns if 'date' in col.lower()]
        for col in date_columns:
            if col in df.columns and not df[col].isna().all():
                try:
                    min_date = df[col].min()
                    max_date = df[col].max()
                    if pd.notna(min_date) and pd.notna(max_date):
                        # Check if dates are in reasonable range (2000-2050)
                        if hasattr(min_date, 'year'):
                            if min_date.year < 2000 or max_date.year > 2050:
                                warnings.append(f"Date column {col} has unusual range: {min_date} to {max_date}")
                except Exception:
                    pass
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _get_required_columns(self, dataset_type: str) -> List[str]:
        """Get list of required columns for dataset type"""
        if dataset_type == 'cost_usage':
            return ['id', 'billing_account_id', 'billed_cost', 'source_system']
        elif dataset_type == 'contract_commitment':
            return ['id', 'contract_commitment_id', 'source_system']
        else:
            return ['id', 'source_system']
    
    def _generate_transformation_stats(self, df: pd.DataFrame, file_info: ParquetFileInfo) -> Dict[str, Any]:
        """Generate statistics about the transformation"""
        stats = {
            'rows_processed': len(df),
            'columns_processed': len(df.columns),
            'dataset_type': file_info.dataset_type,
            'file_size_bytes': file_info.file_path.stat().st_size,
            'null_counts': df.isnull().sum().to_dict(),
            'data_types': df.dtypes.astype(str).to_dict()
        }
        
        # Add memory usage info
        try:
            memory_usage = df.memory_usage(deep=True).sum()
            stats['memory_usage_bytes'] = int(memory_usage)
        except Exception:
            pass
        
        return stats


def transform_focus_data(file_info: ParquetFileInfo) -> TransformationResult:
    """
    Convenience function to transform FOCUS Parquet data.
    
    Args:
        file_info: Information about the Parquet file to transform
        
    Returns:
        TransformationResult with transformed data or error information
    """
    transformer = FocusDataTransformer()
    return transformer.transform_parquet_file(file_info)