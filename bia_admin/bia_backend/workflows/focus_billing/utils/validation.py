"""
Validation Utilities

Functions for validating FOCUS data and query parameters.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
import re


def validate_focus_data(data: Dict[str, Any], dataset_type: str) -> List[str]:
    """
    Validate FOCUS data against specification requirements
    
    Args:
        data: Data dictionary to validate
        dataset_type: Type of dataset (cost_usage or contract_commitment)
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if dataset_type == 'cost_usage':
        errors.extend(_validate_cost_usage_data(data))
    elif dataset_type == 'contract_commitment':
        errors.extend(_validate_contract_commitment_data(data))
    else:
        errors.append(f"Unknown dataset type: {dataset_type}")
    
    return errors


def _validate_cost_usage_data(data: Dict[str, Any]) -> List[str]:
    """Validate Cost & Usage dataset data"""
    errors = []
    
    # Check mandatory fields
    mandatory_fields = ['billing_account_id', 'usage_date', 'billed_cost']
    for field in mandatory_fields:
        if field not in data or data[field] is None:
            errors.append(f"Missing mandatory field: {field}")
    
    # Validate data types
    if 'usage_date' in data and data['usage_date'] is not None:
        if not isinstance(data['usage_date'], (date, datetime, str)):
            errors.append("usage_date must be a date, datetime, or date string")
    
    if 'billed_cost' in data and data['billed_cost'] is not None:
        if not isinstance(data['billed_cost'], (Decimal, float, int)):
            errors.append("billed_cost must be a numeric value")
    
    # Validate billing_account_id format
    if 'billing_account_id' in data and data['billing_account_id'] is not None:
        if not isinstance(data['billing_account_id'], str) or len(data['billing_account_id']) == 0:
            errors.append("billing_account_id must be a non-empty string")
    
    return errors


def _validate_contract_commitment_data(data: Dict[str, Any]) -> List[str]:
    """Validate Contract Commitment dataset data"""
    errors = []
    
    # Check mandatory fields
    mandatory_fields = ['contract_commitment_id']
    for field in mandatory_fields:
        if field not in data or data[field] is None:
            errors.append(f"Missing mandatory field: {field}")
    
    # Validate contract_commitment_id format
    if 'contract_commitment_id' in data and data['contract_commitment_id'] is not None:
        if not isinstance(data['contract_commitment_id'], str) or len(data['contract_commitment_id']) == 0:
            errors.append("contract_commitment_id must be a non-empty string")
    
    return errors


def validate_query_parameters(parameters: Dict[str, Any], required_params: List[str]) -> List[str]:
    """
    Validate query parameters
    
    Args:
        parameters: Parameters to validate
        required_params: List of required parameter names
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Check for missing required parameters
    for param in required_params:
        if param not in parameters:
            errors.append(f"Missing required parameter: {param}")
    
    # Validate parameter types and formats
    for param_name, param_value in parameters.items():
        if param_name in ['start_date', 'end_date'] and param_value is not None:
            if not _is_valid_date(param_value):
                errors.append(f"Parameter {param_name} must be a valid date (YYYY-MM-DD)")
        
        if param_name in ['limit', 'offset'] and param_value is not None:
            if not isinstance(param_value, int) or param_value < 0:
                errors.append(f"Parameter {param_name} must be a non-negative integer")
    
    # Validate date ranges
    if 'start_date' in parameters and 'end_date' in parameters:
        start_date = _parse_date(parameters['start_date'])
        end_date = _parse_date(parameters['end_date'])
        
        if start_date and end_date and start_date > end_date:
            errors.append("start_date must be less than or equal to end_date")
    
    return errors


def _is_valid_date(value: Any) -> bool:
    """Check if value is a valid date"""
    if isinstance(value, (date, datetime)):
        return True
    
    if isinstance(value, str):
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    return False


def _parse_date(value: Any) -> Optional[date]:
    """Parse date value to date object"""
    if isinstance(value, date):
        return value
    elif isinstance(value, datetime):
        return value.date()
    elif isinstance(value, str):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return None
    
    return None


def validate_billing_account_id(account_id: str) -> bool:
    """
    Validate billing account ID format
    
    Args:
        account_id: Billing account ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(account_id, str):
        return False
    
    # Basic validation - non-empty string with reasonable length
    if len(account_id) == 0 or len(account_id) > 255:
        return False
    
    # Check for valid characters (alphanumeric, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9_-]+$', account_id):
        return False
    
    return True


def validate_currency_code(currency: str) -> bool:
    """
    Validate currency code format (ISO 4217)
    
    Args:
        currency: Currency code to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(currency, str):
        return False
    
    # ISO 4217 currency codes are 3 uppercase letters
    return bool(re.match(r'^[A-Z]{3}$', currency))


def validate_decimal_precision(value: Decimal, max_precision: int = 38, max_scale: int = 18) -> bool:
    """
    Validate decimal precision and scale
    
    Args:
        value: Decimal value to validate
        max_precision: Maximum allowed precision
        max_scale: Maximum allowed scale
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(value, Decimal):
        return False
    
    try:
        sign, digits, exponent = value.as_tuple()
        precision = len(digits)
        scale = -exponent if exponent < 0 else 0
        
        return precision <= max_precision and scale <= max_scale
    except:
        return False