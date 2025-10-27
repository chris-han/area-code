"""
Tests for FOCUS billing configuration
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch
from ..config import FocusBillingConfig


def test_focus_billing_config_creation():
    """Test that FocusBillingConfig can be created with defaults"""
    config = FocusBillingConfig()
    
    # Check that basic attributes exist
    assert hasattr(config, 'focus_data_root')
    assert hasattr(config, 'clickhouse_host')
    assert hasattr(config, 'batch_size')
    assert hasattr(config, 'cost_usage_table_name')
    
    # Check default values
    assert config.batch_size == 10000
    assert config.cost_usage_table_name == "focus_cost_usage"
    assert config.contract_commitment_table_name == "focus_contract_commitment"


def test_focus_billing_config_clickhouse_url():
    """Test ClickHouse URL generation"""
    config = FocusBillingConfig()
    
    url = config.get_clickhouse_url()
    assert isinstance(url, str)
    assert url.startswith(('http://', 'https://'))


def test_focus_billing_config_from_env():
    """Test configuration creation from environment"""
    config = FocusBillingConfig.from_env()
    
    assert isinstance(config, FocusBillingConfig)
    assert config.batch_size > 0


def test_environment_variable_handling():
    """Test that environment variables override defaults"""
    with patch.dict(os.environ, {
        'FOCUS_BATCH_SIZE': '5000',
        'FOCUS_MAX_WORKERS': '8',
        'FOCUS_CONNECTION_TIMEOUT': '60',
        'FOCUS_DRY_RUN': 'true'
    }):
        config = FocusBillingConfig()
        
        assert config.batch_size == 5000
        assert config.max_workers == 8
        assert config.connection_timeout == 60
        assert config.dry_run is True


def test_environment_variable_defaults():
    """Test default values when environment variables are not set"""
    # Clear any existing environment variables
    env_vars_to_clear = [
        'FOCUS_BATCH_SIZE', 'FOCUS_MAX_WORKERS', 'FOCUS_CONNECTION_TIMEOUT',
        'FOCUS_SEND_RECEIVE_TIMEOUT', 'FOCUS_DRY_RUN'
    ]
    
    with patch.dict(os.environ, {}, clear=False):
        # Remove the specific variables we're testing
        for var in env_vars_to_clear:
            os.environ.pop(var, None)
            
        config = FocusBillingConfig()
        
        # Test default values
        assert config.batch_size == 10000
        assert config.max_workers == 4
        assert config.connection_timeout == 30
        assert config.send_receive_timeout == 300
        assert config.dry_run is False


def test_clickhouse_credential_reuse():
    """Test that ClickHouse credentials are properly reused from moose config"""
    config = FocusBillingConfig.from_env_and_moose_config()
    
    # Verify that credentials match expected moose.config.toml values
    assert config.clickhouse_host == 'ck.mightytech.cn'
    assert config.clickhouse_port == 8443
    assert config.clickhouse_user == 'finops'
    assert config.clickhouse_password == 'cU2f947&9T{6d'
    assert config.clickhouse_database == 'finops-odw'
    assert config.clickhouse_use_ssl is True


def test_clickhouse_environment_override():
    """Test that environment variables can override ClickHouse credentials"""
    with patch.dict(os.environ, {
        'CLICKHOUSE_HOST': 'test-host',
        'CLICKHOUSE_PORT': '9000',
        'CLICKHOUSE_USER': 'test-user',
        'CLICKHOUSE_DATABASE': 'test-db',
        'CLICKHOUSE_USE_SSL': 'false'
    }):
        config = FocusBillingConfig.from_env_and_moose_config()
        
        assert config.clickhouse_host == 'test-host'
        assert config.clickhouse_port == 9000
        assert config.clickhouse_user == 'test-user'
        assert config.clickhouse_database == 'test-db'
        assert config.clickhouse_use_ssl is False


def test_clickhouse_connection_params():
    """Test ClickHouse connection parameters generation"""
    config = FocusBillingConfig()
    params = config.get_clickhouse_connection_params()
    
    required_keys = [
        'host', 'port', 'username', 'password', 'database',
        'secure', 'connect_timeout', 'send_receive_timeout'
    ]
    
    for key in required_keys:
        assert key in params
    
    assert params['host'] == config.clickhouse_host
    assert params['port'] == config.clickhouse_port
    assert params['username'] == config.clickhouse_user
    assert params['password'] == config.clickhouse_password
    assert params['database'] == config.clickhouse_database
    assert params['secure'] == config.clickhouse_use_ssl


def test_batch_size_validation():
    """Test batch size validation"""
    # Test valid batch size
    config = FocusBillingConfig(batch_size=5000)
    assert config.batch_size == 5000
    
    # Test invalid batch sizes
    with pytest.raises(ValueError, match="Batch size must be positive"):
        FocusBillingConfig(batch_size=0)
    
    with pytest.raises(ValueError, match="Batch size must be positive"):
        FocusBillingConfig(batch_size=-1)
    
    with pytest.raises(ValueError, match="Batch size too large"):
        FocusBillingConfig(batch_size=200000)


def test_max_workers_validation():
    """Test max workers validation"""
    # Test valid max workers
    config = FocusBillingConfig(max_workers=8)
    assert config.max_workers == 8
    
    # Test invalid max workers
    with pytest.raises(ValueError, match="Max workers must be positive"):
        FocusBillingConfig(max_workers=0)
    
    with pytest.raises(ValueError, match="Max workers must be positive"):
        FocusBillingConfig(max_workers=-1)
    
    with pytest.raises(ValueError, match="Max workers too large"):
        FocusBillingConfig(max_workers=50)


def test_path_validation():
    """Test path validation functionality"""
    config = FocusBillingConfig()
    path_status = config.validate_paths()
    
    # Should return a dict with path validation results
    assert isinstance(path_status, dict)
    expected_paths = [
        'focus_data_root', 'focus_spec_root', 
        'focus_queries_root', 'focus_specifications_root'
    ]
    
    for path_name in expected_paths:
        assert path_name in path_status
        assert isinstance(path_status[path_name], bool)


def test_clickhouse_url_generation():
    """Test ClickHouse URL generation with SSL and non-SSL"""
    # Test with SSL
    config_ssl = FocusBillingConfig(clickhouse_use_ssl=True)
    url_ssl = config_ssl.get_clickhouse_url()
    assert url_ssl.startswith('https://')
    assert config_ssl.clickhouse_host in url_ssl
    assert str(config_ssl.clickhouse_port) in url_ssl
    
    # Test without SSL
    config_no_ssl = FocusBillingConfig(clickhouse_use_ssl=False)
    url_no_ssl = config_no_ssl.get_clickhouse_url()
    assert url_no_ssl.startswith('http://')
    assert config_no_ssl.clickhouse_host in url_no_ssl
    assert str(config_no_ssl.clickhouse_port) in url_no_ssl