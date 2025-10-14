"""
Error Handler for Azure Billing Connector

This module provides comprehensive error handling and logging infrastructure
for the Azure billing data extraction and processing pipeline.
"""

import logging
import traceback
from typing import Dict, Any, Optional, List
from enum import Enum
import requests
from datetime import datetime


class ErrorType(Enum):
    """Classification of error types"""
    API_ERROR = "api_error"
    DATA_ERROR = "data_error"
    VALIDATION_ERROR = "validation_error"
    TRANSFORMATION_ERROR = "transformation_error"
    RESOURCE_TRACKING_ERROR = "resource_tracking_error"
    MEMORY_ERROR = "memory_error"
    CONFIGURATION_ERROR = "configuration_error"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorHandler:
    """
    Centralized error handling for Azure billing connector
    
    Provides structured error classification, logging, and recovery strategies
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_counts = {}
        self.error_history = []
    
    def handle_api_error(self, response: requests.Response, context: Dict[str, Any]) -> bool:
        """
        Handle HTTP API errors with classification and recovery suggestions
        
        Args:
            response: HTTP response object
            context: Additional context information
            
        Returns:
            True if error is retryable, False otherwise
        """
        try:
            error_info = {
                'error_type': ErrorType.API_ERROR.value,
                'status_code': response.status_code,
                'url': response.url,
                'context': context,
                'timestamp': datetime.now(),
                'response_headers': dict(response.headers),
                'response_content': response.text[:1000] if response.text else None
            }
            
            # Classify error and determine severity
            severity, is_retryable = self._classify_api_error(response.status_code)
            error_info['severity'] = severity.value
            error_info['is_retryable'] = is_retryable
            
            # Log error with appropriate level
            self._log_error(error_info, severity)
            
            # Track error statistics
            self._track_error(ErrorType.API_ERROR, severity)
            
            return is_retryable
            
        except Exception as e:
            self.logger.error(f"Failed to handle API error: {str(e)}")
            return False
    
    def handle_data_error(self, error: Exception, record: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle data processing errors with recovery attempts
        
        Args:
            error: Exception that occurred
            record: Data record being processed
            context: Processing context
            
        Returns:
            Cleaned record if recoverable, None if unrecoverable
        """
        try:
            error_info = {
                'error_type': ErrorType.DATA_ERROR.value,
                'exception_type': type(error).__name__,
                'exception_message': str(error),
                'record_sample': {k: str(v)[:100] for k, v in record.items()},
                'context': context,
                'timestamp': datetime.now(),
                'traceback': traceback.format_exc()
            }
            
            # Determine severity based on error type
            severity = self._classify_data_error(error)
            error_info['severity'] = severity.value
            
            # Attempt recovery
            recovered_record = self._attempt_data_recovery(error, record)
            error_info['recovery_attempted'] = recovered_record is not None
            
            # Log error
            self._log_error(error_info, severity)
            
            # Track error
            self._track_error(ErrorType.DATA_ERROR, severity)
            
            return recovered_record
            
        except Exception as e:
            self.logger.error(f"Failed to handle data error: {str(e)}")
            return None
    
    def handle_validation_error(self, error: Exception, data: Any, context: Dict[str, Any]) -> bool:
        """
        Handle validation errors
        
        Args:
            error: Validation exception
            data: Data that failed validation
            context: Validation context
            
        Returns:
            True if processing should continue, False if it should stop
        """
        try:
            error_info = {
                'error_type': ErrorType.VALIDATION_ERROR.value,
                'exception_type': type(error).__name__,
                'exception_message': str(error),
                'data_type': type(data).__name__,
                'context': context,
                'timestamp': datetime.now()
            }
            
            # Validation errors are typically medium severity
            severity = ErrorSeverity.MEDIUM
            error_info['severity'] = severity.value
            
            # Log error
            self._log_error(error_info, severity)
            
            # Track error
            self._track_error(ErrorType.VALIDATION_ERROR, severity)
            
            # Continue processing for validation errors (skip invalid records)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to handle validation error: {str(e)}")
            return False
    
    def _classify_api_error(self, status_code: int) -> tuple[ErrorSeverity, bool]:
        """
        Classify API error by status code
        
        Args:
            status_code: HTTP status code
            
        Returns:
            Tuple of (severity, is_retryable)
        """
        if status_code == 401:
            return ErrorSeverity.CRITICAL, False  # Authentication failure
        elif status_code == 403:
            return ErrorSeverity.HIGH, False      # Authorization failure
        elif status_code == 404:
            return ErrorSeverity.MEDIUM, False    # Resource not found
        elif status_code == 429:
            return ErrorSeverity.MEDIUM, True     # Rate limiting
        elif status_code == 500:
            return ErrorSeverity.HIGH, True       # Server error (retryable)
        elif status_code == 502:
            return ErrorSeverity.MEDIUM, True     # Bad gateway
        elif status_code == 503:
            return ErrorSeverity.MEDIUM, True     # Service unavailable
        elif status_code == 504:
            return ErrorSeverity.MEDIUM, True     # Gateway timeout
        elif 400 <= status_code < 500:
            return ErrorSeverity.HIGH, False      # Client error
        elif 500 <= status_code < 600:
            return ErrorSeverity.HIGH, True       # Server error
        else:
            return ErrorSeverity.MEDIUM, False    # Unknown
    
    def _classify_data_error(self, error: Exception) -> ErrorSeverity:
        """
        Classify data processing error by exception type
        
        Args:
            error: Exception that occurred
            
        Returns:
            Error severity level
        """
        error_type = type(error).__name__
        
        if error_type in ['KeyError', 'AttributeError']:
            return ErrorSeverity.MEDIUM  # Missing fields
        elif error_type in ['ValueError', 'TypeError']:
            return ErrorSeverity.MEDIUM  # Data type issues
        elif error_type in ['JSONDecodeError']:
            return ErrorSeverity.LOW     # JSON parsing issues
        elif error_type in ['MemoryError']:
            return ErrorSeverity.CRITICAL  # Memory issues
        else:
            return ErrorSeverity.MEDIUM  # Default
    
    def _attempt_data_recovery(self, error: Exception, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Attempt to recover from data processing errors
        
        Args:
            error: Exception that occurred
            record: Original record
            
        Returns:
            Recovered record or None if unrecoverable
        """
        try:
            error_type = type(error).__name__
            
            if error_type == 'KeyError':
                # Handle missing keys by setting defaults
                recovered = record.copy()
                missing_key = str(error).strip("'\"")
                recovered[missing_key] = None
                return recovered
            
            elif error_type == 'ValueError' and 'date' in str(error).lower():
                # Handle date parsing errors
                recovered = record.copy()
                for key, value in recovered.items():
                    if 'date' in key.lower() and isinstance(value, str):
                        recovered[key] = None  # Set invalid dates to None
                return recovered
            
            elif error_type == 'JSONDecodeError':
                # Handle JSON parsing errors
                recovered = record.copy()
                for key, value in recovered.items():
                    if isinstance(value, str) and ('{' in value or '[' in value):
                        recovered[key] = None  # Set invalid JSON to None
                return recovered
            
            # No recovery strategy available
            return None
            
        except Exception:
            return None
    
    def _log_error(self, error_info: Dict[str, Any], severity: ErrorSeverity):
        """
        Log error with appropriate level based on severity
        
        Args:
            error_info: Error information dictionary
            severity: Error severity level
        """
        message = f"{error_info['error_type']}: {error_info.get('exception_message', 'Unknown error')}"
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(message, extra={'error_info': error_info})
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(message, extra={'error_info': error_info})
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(message, extra={'error_info': error_info})
        else:  # LOW
            self.logger.info(message, extra={'error_info': error_info})
    
    def _track_error(self, error_type: ErrorType, severity: ErrorSeverity):
        """
        Track error statistics
        
        Args:
            error_type: Type of error
            severity: Error severity
        """
        key = f"{error_type.value}_{severity.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        
        # Keep recent error history (last 100 errors)
        self.error_history.append({
            'type': error_type.value,
            'severity': severity.value,
            'timestamp': datetime.now()
        })
        
        if len(self.error_history) > 100:
            self.error_history.pop(0)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of errors encountered
        
        Returns:
            Dictionary with error statistics and summary
        """
        return {
            'error_counts': self.error_counts.copy(),
            'total_errors': sum(self.error_counts.values()),
            'recent_errors': len(self.error_history),
            'error_history': self.error_history[-10:]  # Last 10 errors
        }
    
    def reset_error_tracking(self):
        """Reset error tracking statistics"""
        self.error_counts.clear()
        self.error_history.clear()