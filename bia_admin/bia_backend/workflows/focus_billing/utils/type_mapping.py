"""
Type Mapping Utilities

Functions for mapping between FOCUS data types and ClickHouse types,
and converting values between different formats.
"""

from decimal import Decimal
from datetime import datetime, date
from typing import Any, Optional, Union
import json


def map_focus_to_clickhouse_type(focus_type: str, allows_nulls: bool = True) -> str:
    """
    Map FOCUS data type to ClickHouse type
    
    Args:
        focus_type: FOCUS data type from specification
        allows_nulls: Whether the column allows null values
        
    Returns:
        ClickHouse type string
        
    Examples:
        >>> map_focus_to_clickhouse_type('String', True)
        'Nullable(String)'
        >>> map_focus_to_clickhouse_type('Decimal', False)
        'Decimal(38, 18)'
    """
    type_mapping = {
        'String': 'String',
        'Decimal': 'Decimal(38, 18)',
        'Date': 'Date',
        'DateTime': 'DateTime64(3)',
        'Date/Time': 'DateTime64(3)',  # Handle FOCUS Date/Time format
        'JSON': 'String',  # Store as String for compatibility
        'Boolean': 'UInt8'  # ClickHouse doesn't have native boolean
    }
    
    base_type = type_mapping.get(focus_type, 'String')
    
    if allows_nulls and focus_type != 'Boolean':
        return f'Nullable({base_type})'
    
    return base_type


def convert_parquet_value(value: Any, target_type: str) -> Any:
    """
    Convert Parquet value to appropriate type for ClickHouse
    
    Args:
        value: Value from Parquet file
        target_type: Target ClickHouse type
        
    Returns:
        Converted value
    """
    if value is None:
        return None
    
    # Handle Decimal types
    if 'Decimal' in target_type:
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        elif isinstance(value, str):
            try:
                return Decimal(value)
            except:
                return None
        return value
    
    # Handle Date types
    if target_type in ['Date', 'Nullable(Date)']:
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except:
                return None
        elif isinstance(value, datetime):
            return value.date()
        return value
    
    # Handle DateTime types
    if 'DateTime' in target_type:
        if isinstance(value, str):
            try:
                # Try common datetime formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                    try:
                        return datetime.strptime(value, fmt)
                    except:
                        continue
                return None
            except:
                return None
        return value
    
    # Handle Boolean (UInt8) types
    if target_type == 'UInt8':
        if isinstance(value, bool):
            return 1 if value else 0
        elif isinstance(value, str):
            return 1 if value.lower() in ['true', '1', 'yes'] else 0
        elif isinstance(value, (int, float)):
            return 1 if value else 0
        return 0
    
    # Handle JSON types (stored as String)
    if target_type in ['String', 'Nullable(String)'] and isinstance(value, (dict, list)):
        try:
            return json.dumps(value)
        except:
            return str(value)
    
    # Handle String types
    if 'String' in target_type:
        return str(value) if value is not None else None
    
    return value


def convert_int96_to_datetime(int96_value: Any) -> Optional[datetime]:
    """
    Convert Parquet INT96 timestamp to datetime
    
    Args:
        int96_value: INT96 timestamp value from Parquet
        
    Returns:
        Datetime object or None if conversion fails
    """
    if int96_value is None:
        return None
    
    try:
        # INT96 is nanoseconds since Julian epoch
        # This is a simplified conversion - may need adjustment based on actual data
        if isinstance(int96_value, int):
            # Convert nanoseconds to seconds
            seconds = int96_value / 1_000_000_000
            return datetime.fromtimestamp(seconds)
    except:
        pass
    
    return None


def normalize_decimal_precision(value: Decimal, max_precision: int = 18, max_scale: int = 6) -> Decimal:
    """
    Normalize decimal precision to fit ClickHouse constraints
    
    Args:
        value: Decimal value to normalize
        max_precision: Maximum precision allowed
        max_scale: Maximum scale allowed
        
    Returns:
        Normalized decimal value
    """
    if value is None:
        return None
    
    try:
        # Get the sign, digits, and exponent
        sign, digits, exponent = value.as_tuple()
        
        # Calculate current precision and scale
        precision = len(digits)
        scale = -exponent if exponent < 0 else 0
        
        # If precision exceeds limit, truncate
        if precision > max_precision:
            # Keep the most significant digits
            new_digits = digits[:max_precision]
            # Adjust exponent to maintain scale if possible
            new_exponent = exponent + (len(digits) - max_precision)
            value = Decimal((sign, new_digits, new_exponent))
        
        # If scale exceeds limit, round
        if scale > max_scale:
            return value.quantize(Decimal('0.' + '0' * max_scale))
        
        return value
    except:
        return value


def infer_clickhouse_type_from_value(value: Any) -> str:
    """
    Infer ClickHouse type from a sample value
    
    Args:
        value: Sample value to analyze
        
    Returns:
        Inferred ClickHouse type string
    """
    if value is None:
        return 'Nullable(String)'
    
    if isinstance(value, bool):
        return 'UInt8'
    elif isinstance(value, int):
        if -2147483648 <= value <= 2147483647:
            return 'Int32'
        else:
            return 'Int64'
    elif isinstance(value, float):
        return 'Float64'
    elif isinstance(value, Decimal):
        return 'Decimal(38, 18)'
    elif isinstance(value, date):
        return 'Date'
    elif isinstance(value, datetime):
        return 'DateTime64(3)'
    elif isinstance(value, (dict, list)):
        return 'String'  # Store JSON as string
    else:
        return 'String'