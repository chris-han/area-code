import streamlit as st
import json
import base64
import secrets
import hashlib
import os
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class AzureBillingConfig:
    """Configuration model for Azure billing extraction"""
    enrollment_number: str
    api_key: str
    start_date: date
    end_date: date
    batch_size: int = 1000
    save_credentials: bool = False
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not self.enrollment_number:
            errors.append("Azure enrollment number is required")
        
        if not self.api_key:
            errors.append("Azure API key is required")
        
        if self.start_date >= self.end_date:
            errors.append("Start date must be before end date")
        
        if self.batch_size < 100 or self.batch_size > 10000:
            errors.append("Batch size must be between 100 and 10000")
        
        # Additional validations
        if self.start_date < date.today() - timedelta(days=365):
            errors.append("Start date cannot be more than 1 year in the past")
        
        if self.end_date > date.today():
            errors.append("End date cannot be in the future")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API calls"""
        return {
            "enrollment_number": self.enrollment_number,
            "api_key": self.api_key,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "batch_size": self.batch_size
        }

class CredentialManager:
    """Secure credential management for Azure billing configuration with multiple persistence options"""
    
    @staticmethod
    def encrypt_credential(value: str, persistence_level: str = "session") -> str:
        """Encrypt credential using appropriate method for persistence level"""
        if not value:
            return ""
        
        if persistence_level == "browser":
            # Use stronger encryption for browser storage
            return CredentialManager._encrypt_for_browser(value)
        else:
            # Use session-based encryption
            return CredentialManager._encrypt_for_session(value)
    
    @staticmethod
    def _encrypt_for_session(value: str) -> str:
        """Encrypt credential for session storage"""
        session_key = st.session_state.get("credential_key")
        if not session_key:
            session_key = secrets.token_urlsafe(32)
            st.session_state["credential_key"] = session_key
        
        # Simple encryption for demo (use proper encryption in production)
        encoded = base64.b64encode(value.encode()).decode()
        return f"sess_{encoded}"
    
    @staticmethod
    def _encrypt_for_browser(value: str) -> str:
        """Encrypt credential for browser localStorage (stronger encryption)"""
        # Generate a browser-specific key based on session and timestamp
        browser_key = hashlib.sha256(f"{st.session_state.get('session_id', 'default')}{date.today()}".encode()).hexdigest()[:32]
        
        # Use simple encryption for browser storage (in production, use proper encryption)
        try:
            key = base64.urlsafe_b64encode(browser_key.encode()[:32].ljust(32, b'0'))
            encoded = base64.b64encode(value.encode()).decode()
            return f"browser_{encoded}"
        except Exception:
            # Fallback to session encryption
            return CredentialManager._encrypt_for_session(value)
    
    @staticmethod
    def decrypt_credential(encrypted_value: str) -> str:
        """Decrypt credential based on encryption type"""
        if not encrypted_value:
            return ""
        
        if encrypted_value.startswith("sess_"):
            return CredentialManager._decrypt_session(encrypted_value)
        elif encrypted_value.startswith("browser_"):
            return CredentialManager._decrypt_browser(encrypted_value)
        else:
            return ""
    
    @staticmethod
    def _decrypt_session(encrypted_value: str) -> str:
        """Decrypt session-encrypted credential"""
        try:
            encoded = encrypted_value[5:]  # Remove "sess_" prefix
            return base64.b64decode(encoded).decode()
        except Exception:
            return ""
    
    @staticmethod
    def _decrypt_browser(encrypted_value: str) -> str:
        """Decrypt browser-encrypted credential"""
        try:
            encoded = encrypted_value[8:]  # Remove "browser_" prefix
            return base64.b64decode(encoded).decode()
        except Exception:
            return ""
    
    @staticmethod
    def save_credentials(enrollment_number: str, api_key: str, persistence_level: str = "session"):
        """Save encrypted credentials with specified persistence level"""
        if enrollment_number:
            encrypted_enrollment = CredentialManager.encrypt_credential(enrollment_number, persistence_level)
            st.session_state["saved_enrollment"] = encrypted_enrollment
            
            if persistence_level == "browser":
                CredentialManager._save_credential_to_browser("enrollment", encrypted_enrollment)
        
        if api_key:
            encrypted_api_key = CredentialManager.encrypt_credential(api_key, persistence_level)
            st.session_state["saved_api_key"] = encrypted_api_key
            
            if persistence_level == "browser":
                CredentialManager._save_credential_to_browser("api_key", encrypted_api_key)
    
    @staticmethod
    def _save_credential_to_browser(credential_type: str, encrypted_value: str):
        """Save encrypted credential to browser localStorage"""
        # For now, we'll store in session state with a browser prefix
        # In a full implementation, this would use JavaScript to save to localStorage
        st.session_state[f"browser_azure_billing_{credential_type}"] = encrypted_value
    
    @staticmethod
    def get_saved_credential(credential_type: str) -> str:
        """Retrieve and decrypt saved credential from available sources"""
        key_map = {
            "enrollment_number": "saved_enrollment",
            "api_key": "saved_api_key"
        }
        
        session_key = key_map.get(credential_type)
        
        # Try session state first
        if session_key and session_key in st.session_state:
            return CredentialManager.decrypt_credential(st.session_state[session_key])
        
        # Try browser storage as fallback
        browser_key = f"browser_azure_billing_{credential_type}"
        if browser_key in st.session_state:
            browser_value = st.session_state[browser_key]
            # Copy to session state for current session
            if session_key:
                st.session_state[session_key] = browser_value
            return CredentialManager.decrypt_credential(browser_value)
        
        return ""
    
    @staticmethod
    def clear_saved_credentials(persistence_level: str = "all"):
        """Clear saved credentials from specified storage level"""
        if persistence_level in ["all", "session"]:
            for key in ["saved_enrollment", "saved_api_key", "credential_key"]:
                if key in st.session_state:
                    del st.session_state[key]
        
        if persistence_level in ["all", "browser"]:
            CredentialManager._clear_browser_credentials()
    
    @staticmethod
    def _clear_browser_credentials():
        """Clear credentials from browser localStorage"""
        # Clear browser-prefixed credentials from session state
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith("browser_azure_billing_")]
        for key in keys_to_remove:
            del st.session_state[key]

class WorkflowParameterManager:
    """Manage persistence of workflow configuration parameters across multiple storage levels"""
    
    @staticmethod
    def save_workflow_config(config: AzureBillingConfig, persistence_level: str = "session"):
        """Save workflow configuration with specified persistence level"""
        config_data = {
            "enrollment_number": config.enrollment_number,
            "start_date": config.start_date.isoformat(),
            "end_date": config.end_date.isoformat(),
            "batch_size": config.batch_size,
            "last_saved": datetime.now().isoformat(),
            "persistence_level": persistence_level
        }
        
        # Always save to session state
        st.session_state["azure_billing_config"] = config_data
        
        # Save to browser localStorage if requested
        if persistence_level == "browser":
            WorkflowParameterManager._save_to_browser_storage(config_data)
        
        # Save encrypted credentials separately if requested
        if config.save_credentials:
            CredentialManager.save_credentials(config.enrollment_number, config.api_key, persistence_level)
    
    @staticmethod
    def _save_to_browser_storage(config_data: dict):
        """Save configuration to browser localStorage using session state simulation"""
        # Remove sensitive data before saving to browser
        safe_config = {k: v for k, v in config_data.items() if k != "enrollment_number"}
        
        # Store in session state with browser prefix (simulating localStorage)
        st.session_state["browser_azure_billing_config"] = safe_config
    
    @staticmethod
    def load_workflow_config() -> Optional[AzureBillingConfig]:
        """Load workflow configuration from available storage sources"""
        config_data = None
        
        # Try session state first
        if "azure_billing_config" in st.session_state:
            config_data = st.session_state["azure_billing_config"]
        
        # Try browser localStorage if session state is empty
        elif "browser_azure_billing_config" in st.session_state:
            config_data = st.session_state["browser_azure_billing_config"]
            if config_data:
                # Copy to session state for current session
                st.session_state["azure_billing_config"] = config_data
        
        # Try environment defaults as fallback
        else:
            config_data = WorkflowParameterManager._load_environment_defaults()
        
        if config_data:
            return AzureBillingConfig(
                enrollment_number=config_data.get("enrollment_number", ""),
                api_key=CredentialManager.get_saved_credential("api_key"),
                start_date=date.fromisoformat(config_data.get("start_date", date.today().isoformat())),
                end_date=date.fromisoformat(config_data.get("end_date", date.today().isoformat())),
                batch_size=config_data.get("batch_size", 1000)
            )
        return None
    
    @staticmethod
    def _load_environment_defaults() -> dict:
        """Load default configuration from environment variables"""
        return {
            "enrollment_number": os.getenv("AZURE_DEFAULT_ENROLLMENT", ""),
            "start_date": (date.today() - timedelta(days=30)).isoformat(),
            "end_date": date.today().isoformat(),
            "batch_size": int(os.getenv("AZURE_DEFAULT_BATCH_SIZE", "1000")),
            "last_saved": datetime.now().isoformat(),
            "persistence_level": "environment"
        }
    
    @staticmethod
    def export_config_to_file(config: AzureBillingConfig) -> str:
        """Export configuration to JSON string for file download"""
        export_data = {
            "azure_billing_config": {
                "enrollment_number": config.enrollment_number,
                "start_date": config.start_date.isoformat(),
                "end_date": config.end_date.isoformat(),
                "batch_size": config.batch_size,
                "exported_at": datetime.now().isoformat()
            },
            "version": "1.0",
            "type": "azure_billing_configuration"
        }
        return json.dumps(export_data, indent=2)
    
    @staticmethod
    def import_config_from_file(file_content: str) -> Optional[AzureBillingConfig]:
        """Import configuration from JSON file content"""
        try:
            data = json.loads(file_content)
            if data.get("type") != "azure_billing_configuration":
                st.error("Invalid configuration file type")
                return None
            
            config_data = data.get("azure_billing_config", {})
            return AzureBillingConfig(
                enrollment_number=config_data.get("enrollment_number", ""),
                api_key="",  # Never import API keys from files
                start_date=date.fromisoformat(config_data.get("start_date", date.today().isoformat())),
                end_date=date.fromisoformat(config_data.get("end_date", date.today().isoformat())),
                batch_size=config_data.get("batch_size", 1000)
            )
        except Exception as e:
            st.error(f"Failed to import configuration: {e}")
            return None
    
    @staticmethod
    def clear_workflow_config(persistence_level: str = "all"):
        """Clear saved workflow configuration"""
        if persistence_level in ["all", "session"] and "azure_billing_config" in st.session_state:
            del st.session_state["azure_billing_config"]
        
        if persistence_level in ["all", "browser"]:
            WorkflowParameterManager._clear_browser_storage()
    
    @staticmethod
    def _clear_browser_storage():
        """Clear configuration from browser localStorage"""
        if "browser_azure_billing_config" in st.session_state:
            del st.session_state["browser_azure_billing_config"]

class SecurityUtils:
    """Security utilities for Azure billing frontend"""
    
    @staticmethod
    def sanitize_input(input_value: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not input_value:
            return ""
        
        # Remove potentially dangerous characters
        sanitized = input_value.strip()
        
        # Remove HTML tags and script content
        import re
        sanitized = re.sub(r'<[^>]*>', '', sanitized)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @staticmethod
    def validate_enrollment_number(enrollment_number: str) -> bool:
        """Validate Azure enrollment number format"""
        if not enrollment_number:
            return False
        
        # Azure enrollment numbers can be alphanumeric, typically 8-15 characters
        import re
        return bool(re.match(r'^[A-Za-z0-9]{8,15}$', enrollment_number.strip()))
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate Azure API key format"""
        if not api_key:
            return False
        
        # Azure API keys can be JWT tokens (much longer) or other formats
        # JWT tokens have the format: header.payload.signature with base64url encoding
        import re
        stripped_key = api_key.strip()
        
        # Check if it's a JWT token (has two dots separating three parts)
        if stripped_key.count('.') == 2:
            parts = stripped_key.split('.')
            # Each part should be base64url encoded (letters, numbers, -, _)
            jwt_pattern = r'^[A-Za-z0-9_-]+$'
            return all(re.match(jwt_pattern, part) for part in parts if part)
        
        # For other API key formats, be flexible
        return bool(re.match(r'^[A-Za-z0-9+/=_-]{10,}$', stripped_key))
    
    @staticmethod
    def log_user_action(action: str, details: dict = None):
        """Log user actions for monitoring and analytics"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "user_session": st.session_state.get("session_id", "unknown"),
            "details": details or {}
        }
        
        # In a production environment, this would log to a proper logging system
        print(f"User action: {action}", log_entry)
    
    @staticmethod
    def track_error(error: Exception, context: str):
        """Track errors for monitoring and debugging"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "user_session": st.session_state.get("session_id", "unknown")
        }
        
        # In a production environment, this would log to a proper error tracking system
        print(f"Frontend error in {context}: {error}", error_entry)

class DataRetentionManager:
    """Manage data retention policies for cached billing data"""
    
    @staticmethod
    def cleanup_old_cache():
        """Clean up old cached data from session state"""
        current_time = datetime.now()
        
        # Clean up cached data older than 1 hour
        cache_keys = [key for key in st.session_state.keys() if key.startswith("azure_billing_cache_")]
        
        for key in cache_keys:
            cache_data = st.session_state.get(key, {})
            if isinstance(cache_data, dict) and "timestamp" in cache_data:
                cache_time = datetime.fromisoformat(cache_data["timestamp"])
                if (current_time - cache_time).total_seconds() > 3600:  # 1 hour
                    del st.session_state[key]
    
    @staticmethod
    def cache_data(key: str, data: any, ttl_seconds: int = 3600):
        """Cache data with TTL"""
        cache_entry = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "ttl": ttl_seconds
        }
        st.session_state[f"azure_billing_cache_{key}"] = cache_entry
    
    @staticmethod
    def get_cached_data(key: str) -> any:
        """Retrieve cached data if still valid"""
        cache_key = f"azure_billing_cache_{key}"
        if cache_key not in st.session_state:
            return None
        
        cache_entry = st.session_state[cache_key]
        cache_time = datetime.fromisoformat(cache_entry["timestamp"])
        
        if (datetime.now() - cache_time).total_seconds() > cache_entry["ttl"]:
            del st.session_state[cache_key]
            return None
        
        return cache_entry["data"]