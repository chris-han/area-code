"""
FOCUS Billing API Exceptions

Common exception classes and error handling utilities for FOCUS billing APIs.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel


class FocusBillingError(Exception):
    """Base exception for FOCUS billing operations"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code or "FOCUS_BILLING_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class QueryNotFoundError(FocusBillingError):
    """Raised when a requested query is not found"""
    
    def __init__(self, slug: str):
        super().__init__(
            message=f"FOCUS use case query '{slug}' not found",
            error_code="QUERY_NOT_FOUND",
            details={"slug": slug}
        )


class FeatureNotFoundError(FocusBillingError):
    """Raised when a requested feature is not found"""
    
    def __init__(self, name: str):
        super().__init__(
            message=f"FOCUS supported feature '{name}' not found",
            error_code="FEATURE_NOT_FOUND",
            details={"name": name}
        )


class QueryExecutionError(FocusBillingError):
    """Raised when query execution fails"""
    
    def __init__(self, slug: str, original_error: str):
        super().__init__(
            message=f"Failed to execute FOCUS query '{slug}': {original_error}",
            error_code="QUERY_EXECUTION_ERROR",
            details={"slug": slug, "original_error": original_error}
        )


class ParameterValidationError(FocusBillingError):
    """Raised when query parameters are invalid"""
    
    def __init__(self, missing_params: list = None, invalid_params: dict = None):
        missing_params = missing_params or []
        invalid_params = invalid_params or {}
        
        message_parts = []
        if missing_params:
            message_parts.append(f"Missing required parameters: {', '.join(missing_params)}")
        if invalid_params:
            invalid_details = [f"{k}: {v}" for k, v in invalid_params.items()]
            message_parts.append(f"Invalid parameters: {'; '.join(invalid_details)}")
        
        message = "; ".join(message_parts) if message_parts else "Parameter validation failed"
        
        super().__init__(
            message=message,
            error_code="PARAMETER_VALIDATION_ERROR",
            details={
                "missing_parameters": missing_params,
                "invalid_parameters": invalid_params
            }
        )


class ConfigurationError(FocusBillingError):
    """Raised when FOCUS billing configuration is invalid"""
    
    def __init__(self, config_issue: str):
        super().__init__(
            message=f"FOCUS billing configuration error: {config_issue}",
            error_code="CONFIGURATION_ERROR",
            details={"config_issue": config_issue}
        )


class ErrorResponse(BaseModel):
    """Standard error response model for FOCUS billing APIs"""
    error: bool = True
    error_code: str
    message: str
    details: Dict[str, Any] = {}


def handle_focus_billing_error(error: Exception) -> ErrorResponse:
    """
    Convert exceptions to standardized error responses.
    
    Args:
        error: Exception to convert
        
    Returns:
        ErrorResponse object
    """
    if isinstance(error, FocusBillingError):
        return ErrorResponse(
            error_code=error.error_code,
            message=error.message,
            details=error.details
        )
    else:
        # Handle unexpected errors
        return ErrorResponse(
            error_code="INTERNAL_ERROR",
            message=f"An unexpected error occurred: {str(error)}",
            details={"exception_type": type(error).__name__}
        )