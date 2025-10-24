"""
Plugin Configuration Validator

Validates plugin configurations against JSON schemas and performs
testing framework integration for plugin validation.
"""

from typing import Dict, Any, List, Optional, Union
import json
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a configuration validation issue"""
    severity: ValidationSeverity
    field_path: str
    message: str
    actual_value: Any = None
    expected_type: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Configuration validation result"""
    is_valid: bool
    issues: List[ValidationIssue]
    normalized_config: Optional[Dict[str, Any]] = None
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]


class PluginConfigValidator:
    """
    Comprehensive plugin configuration validator with JSON schema validation,
    type checking, and business rule validation.
    """
    
    def __init__(self):
        self.custom_validators = {}
        self.type_converters = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict
        }
    
    def validate_config(self, 
                       config: Dict[str, Any], 
                       schema: Dict[str, Any],
                       normalize: bool = True) -> ValidationResult:
        """
        Validate plugin configuration against JSON schema.
        
        Args:
            config: Configuration to validate
            schema: JSON schema for validation
            normalize: Whether to normalize/convert types
            
        Returns:
            Validation result with issues and normalized config
        """
        issues = []
        normalized_config = config.copy() if normalize else None
        
        try:
            # Perform JSON schema validation
            validator = Draft7Validator(schema)
            
            # Collect all validation errors
            for error in validator.iter_errors(config):
                issues.append(self._convert_jsonschema_error(error))
            
            # Normalize configuration if requested and no errors
            if normalize and not any(issue.severity == ValidationSeverity.ERROR for issue in issues):
                normalized_config = self._normalize_config(config, schema)
                
                # Validate normalized config
                additional_issues = self._validate_business_rules(normalized_config, schema)
                issues.extend(additional_issues)
            
        except Exception as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field_path="root",
                message=f"Schema validation failed: {str(e)}"
            ))
        
        # Determine overall validity
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            normalized_config=normalized_config if is_valid else None
        )
    
    def register_custom_validator(self, 
                                field_name: str, 
                                validator_func: callable):
        """
        Register a custom validator for specific fields.
        
        Args:
            field_name: Field name to validate
            validator_func: Function that takes (value, config) and returns ValidationIssue list
        """
        self.custom_validators[field_name] = validator_func
    
    def validate_connection_config(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Validate connection-specific configuration.
        
        Args:
            config: Connection configuration
            
        Returns:
            Validation result
        """
        issues = []
        
        # Common connection validation
        if "host" in config:
            host_issues = self._validate_host(config["host"])
            issues.extend(host_issues)
        
        if "port" in config:
            port_issues = self._validate_port(config["port"])
            issues.extend(port_issues)
        
        if "timeout" in config:
            timeout_issues = self._validate_timeout(config["timeout"])
            issues.extend(timeout_issues)
        
        # SSL/TLS validation
        if config.get("use_ssl", False):
            ssl_issues = self._validate_ssl_config(config)
            issues.extend(ssl_issues)
        
        # Authentication validation
        auth_issues = self._validate_auth_config(config)
        issues.extend(auth_issues)
        
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            normalized_config=config
        )
    
    def validate_data_source_config(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Validate data source specific configuration.
        
        Args:
            config: Data source configuration
            
        Returns:
            Validation result
        """
        issues = []
        
        # Validate required data source fields
        required_fields = ["source_type", "connection"]
        for field in required_fields:
            if field not in config:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field_path=field,
                    message=f"Required field '{field}' is missing"
                ))
        
        # Validate source type
        if "source_type" in config:
            valid_types = ["api", "file", "database", "stream"]
            if config["source_type"] not in valid_types:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field_path="source_type",
                    message=f"Invalid source type. Must be one of: {valid_types}",
                    actual_value=config["source_type"]
                ))
        
        # Validate batch configuration
        if "batch_config" in config:
            batch_issues = self._validate_batch_config(config["batch_config"])
            issues.extend(batch_issues)
        
        # Validate retry configuration
        if "retry_config" in config:
            retry_issues = self._validate_retry_config(config["retry_config"])
            issues.extend(retry_issues)
        
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            normalized_config=config
        )
    
    def _convert_jsonschema_error(self, error: ValidationError) -> ValidationIssue:
        """Convert JSON schema validation error to ValidationIssue"""
        field_path = ".".join(str(p) for p in error.absolute_path) or "root"
        
        # Determine severity based on error type
        severity = ValidationSeverity.ERROR
        if error.validator in ["format", "pattern"]:
            severity = ValidationSeverity.WARNING
        
        # Create user-friendly message
        message = self._create_user_friendly_message(error)
        
        return ValidationIssue(
            severity=severity,
            field_path=field_path,
            message=message,
            actual_value=error.instance if hasattr(error, 'instance') else None
        )
    
    def _create_user_friendly_message(self, error: ValidationError) -> str:
        """Create user-friendly error message from JSON schema error"""
        if error.validator == "required":
            missing_field = error.message.split("'")[1]
            return f"Required field '{missing_field}' is missing"
        elif error.validator == "type":
            expected_type = error.validator_value
            return f"Expected {expected_type}, got {type(error.instance).__name__}"
        elif error.validator == "enum":
            valid_values = error.validator_value
            return f"Value must be one of: {valid_values}"
        elif error.validator == "minimum":
            return f"Value must be at least {error.validator_value}"
        elif error.validator == "maximum":
            return f"Value must be at most {error.validator_value}"
        elif error.validator == "minLength":
            return f"String must be at least {error.validator_value} characters long"
        elif error.validator == "maxLength":
            return f"String must be at most {error.validator_value} characters long"
        elif error.validator == "pattern":
            return f"String does not match required pattern: {error.validator_value}"
        else:
            return error.message
    
    def _normalize_config(self, config: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize configuration by converting types and applying defaults"""
        normalized = config.copy()
        
        # Apply default values
        if "properties" in schema:
            for field_name, field_schema in schema["properties"].items():
                if field_name not in normalized and "default" in field_schema:
                    normalized[field_name] = field_schema["default"]
        
        # Convert types
        normalized = self._convert_types(normalized, schema)
        
        return normalized
    
    def _convert_types(self, config: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert configuration values to expected types"""
        converted = config.copy()
        
        if "properties" in schema:
            for field_name, field_schema in schema["properties"].items():
                if field_name in converted and "type" in field_schema:
                    expected_type = field_schema["type"]
                    current_value = converted[field_name]
                    
                    try:
                        if expected_type in self.type_converters:
                            converter = self.type_converters[expected_type]
                            converted[field_name] = converter(current_value)
                    except (ValueError, TypeError):
                        # Keep original value if conversion fails
                        pass
        
        return converted
    
    def _validate_business_rules(self, config: Dict[str, Any], schema: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate business-specific rules"""
        issues = []
        
        # Apply custom validators
        for field_name, validator_func in self.custom_validators.items():
            if field_name in config:
                try:
                    field_issues = validator_func(config[field_name], config)
                    issues.extend(field_issues)
                except Exception as e:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field_path=field_name,
                        message=f"Custom validation failed: {str(e)}"
                    ))
        
        return issues
    
    def _validate_host(self, host: str) -> List[ValidationIssue]:
        """Validate host configuration"""
        issues = []
        
        if not isinstance(host, str) or not host.strip():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field_path="host",
                message="Host must be a non-empty string"
            ))
        elif host in ["localhost", "localhost"]:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                field_path="host",
                message="Using localhost may not work in containerized environments",
                suggestion="Consider using service names or external IPs"
            ))
        
        return issues
    
    def _validate_port(self, port: Union[int, str]) -> List[ValidationIssue]:
        """Validate port configuration"""
        issues = []
        
        try:
            port_num = int(port)
            if port_num < 1 or port_num > 65535:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field_path="port",
                    message="Port must be between 1 and 65535",
                    actual_value=port_num
                ))
            elif port_num < 1024:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field_path="port",
                    message="Using privileged port (< 1024) may require special permissions",
                    actual_value=port_num
                ))
        except (ValueError, TypeError):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field_path="port",
                message="Port must be a valid integer",
                actual_value=port
            ))
        
        return issues
    
    def _validate_timeout(self, timeout: Union[int, float]) -> List[ValidationIssue]:
        """Validate timeout configuration"""
        issues = []
        
        try:
            timeout_val = float(timeout)
            if timeout_val <= 0:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field_path="timeout",
                    message="Timeout must be greater than 0",
                    actual_value=timeout_val
                ))
            elif timeout_val > 300:  # 5 minutes
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field_path="timeout",
                    message="Very long timeout may cause performance issues",
                    actual_value=timeout_val,
                    suggestion="Consider using a shorter timeout with retry logic"
                ))
        except (ValueError, TypeError):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field_path="timeout",
                message="Timeout must be a valid number",
                actual_value=timeout
            ))
        
        return issues
    
    def _validate_ssl_config(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate SSL/TLS configuration"""
        issues = []
        
        if config.get("use_ssl", False):
            # Check for SSL-related fields
            ssl_fields = ["ssl_cert", "ssl_key", "ssl_ca"]
            missing_ssl_fields = [field for field in ssl_fields if field in config and not config[field]]
            
            if missing_ssl_fields:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field_path="ssl_config",
                    message=f"SSL enabled but missing: {missing_ssl_fields}",
                    suggestion="Provide SSL certificate files or disable SSL"
                ))
        
        return issues
    
    def _validate_auth_config(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate authentication configuration"""
        issues = []
        
        # Check for authentication fields
        auth_fields = ["username", "password", "api_key", "token"]
        auth_provided = any(field in config and config[field] for field in auth_fields)
        
        if not auth_provided:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                field_path="authentication",
                message="No authentication credentials provided",
                suggestion="Consider providing authentication for secure connections"
            ))
        
        # Validate specific auth types
        if "password" in config and config["password"]:
            if len(config["password"]) < 8:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field_path="password",
                    message="Password is shorter than 8 characters",
                    suggestion="Use a stronger password for better security"
                ))
        
        return issues
    
    def _validate_batch_config(self, batch_config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate batch processing configuration"""
        issues = []
        
        if "batch_size" in batch_config:
            try:
                batch_size = int(batch_config["batch_size"])
                if batch_size <= 0:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field_path="batch_config.batch_size",
                        message="Batch size must be greater than 0"
                    ))
                elif batch_size > 10000:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field_path="batch_config.batch_size",
                        message="Large batch size may cause memory issues",
                        suggestion="Consider using smaller batch sizes for better performance"
                    ))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field_path="batch_config.batch_size",
                    message="Batch size must be a valid integer"
                ))
        
        return issues
    
    def _validate_retry_config(self, retry_config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate retry configuration"""
        issues = []
        
        if "max_retries" in retry_config:
            try:
                max_retries = int(retry_config["max_retries"])
                if max_retries < 0:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field_path="retry_config.max_retries",
                        message="Max retries cannot be negative"
                    ))
                elif max_retries > 10:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field_path="retry_config.max_retries",
                        message="High retry count may cause delays",
                        suggestion="Consider using exponential backoff with lower retry count"
                    ))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field_path="retry_config.max_retries",
                    message="Max retries must be a valid integer"
                ))
        
        return issues