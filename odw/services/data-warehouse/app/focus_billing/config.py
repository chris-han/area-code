"""
FOCUS Billing Configuration Management

Handles configuration for FOCUS data paths, ClickHouse connections,
and workflow parameters with environment variable support and
moose.config.toml integration.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator

try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False


def _get_moose_config() -> Dict[str, Any]:
    """Load configuration from moose.config.toml"""
    if not TOML_AVAILABLE:
        # Fallback to hardcoded values from the moose.config.toml we saw
        return {
            'clickhouse_config': {
                'host': 'ck.mightytech.cn',
                'host_port': 8443,
                'user': 'finops',
                'password': 'cU2f947&9T{6d',
                'db_name': 'finops-odw',
                'use_ssl': True
            }
        }
    
    try:
        config_path = Path(__file__).parent.parent.parent / 'moose.config.toml'
        if config_path.exists():
            return toml.load(config_path)
        return {}
    except Exception:
        return {}


def _get_default_focus_data_root() -> str:
    """Get default FOCUS data root with fallback"""
    env_value = os.getenv('FOCUS_DATA_ROOT')
    if env_value:
        return env_value
    
    # Fallback path as specified in requirements
    fallback_path = '/home/chris/repo/area-code/odw/services/data-warehouse/app/focus_billing/data/focus'
    if Path(fallback_path).exists():
        return fallback_path
    
    # Alternative fallback relative to project structure
    relative_path = Path(__file__).parent.parent.parent.parent.parent.parent / 'focus-mcp-main' / 'data' / 'focus'
    return str(relative_path)


class FocusBillingConfig(BaseModel):
    """Configuration for FOCUS billing integration"""
    
    # Data source configuration
    focus_data_root: str = Field(
        default_factory=_get_default_focus_data_root,
        description="Root directory containing FOCUS Parquet exports"
    )
    
    focus_spec_root: str = Field(
        default_factory=lambda: os.getenv(
            'FOCUS_SPEC_ROOT',
            str(Path(__file__).parent.parent.parent.parent.parent.parent / 'FOCUS_Spec' / 'specification')
        ),
        description="Root directory containing FOCUS specification files"
    )
    
    focus_queries_root: str = Field(
        default_factory=lambda: os.getenv(
            'FOCUS_QUERIES_ROOT',
            str(Path(__file__).parent.parent.parent.parent.parent.parent / 'focus-mcp-main' / 'resources' / 'queries')
        ),
        description="Root directory containing FOCUS query YAML files"
    )
    
    focus_specifications_root: str = Field(
        default_factory=lambda: os.getenv(
            'FOCUS_SPECIFICATIONS_ROOT',
            str(Path(__file__).parent.parent.parent.parent.parent.parent / 'focus-mcp-main' / 'resources' / 'specifications')
        ),
        description="Root directory containing FOCUS specification YAML files"
    )
    
    # ClickHouse configuration (reused from moose.config.toml)
    clickhouse_host: str = Field(
        default='ck.mightytech.cn',
        description="ClickHouse host"
    )
    
    clickhouse_port: int = Field(
        default=8443,
        description="ClickHouse HTTP port"
    )
    
    clickhouse_user: str = Field(
        default='finops',
        description="ClickHouse username"
    )
    
    clickhouse_password: str = Field(
        default='cU2f947&9T{6d',
        description="ClickHouse password"
    )
    
    clickhouse_database: str = Field(
        default='finops-odw',
        description="ClickHouse database name"
    )
    
    clickhouse_use_ssl: bool = Field(
        default=True,
        description="Whether to use SSL for ClickHouse connections"
    )
    
    # Workflow configuration with environment variable support
    batch_size: int = Field(
        default_factory=lambda: int(os.getenv('FOCUS_BATCH_SIZE', '10000')),
        description="Batch size for ClickHouse insertions"
    )
    
    max_workers: int = Field(
        default_factory=lambda: int(os.getenv('FOCUS_MAX_WORKERS', '4')),
        description="Maximum number of concurrent workers for data processing"
    )
    
    connection_timeout: int = Field(
        default_factory=lambda: int(os.getenv('FOCUS_CONNECTION_TIMEOUT', '30')),
        description="ClickHouse connection timeout in seconds"
    )
    
    send_receive_timeout: int = Field(
        default_factory=lambda: int(os.getenv('FOCUS_SEND_RECEIVE_TIMEOUT', '300')),
        description="ClickHouse send/receive timeout in seconds"
    )
    
    dry_run: bool = Field(
        default_factory=lambda: os.getenv('FOCUS_DRY_RUN', 'false').lower() == 'true',
        description="Whether to run in dry-run mode (no actual insertions)"
    )
    
    # Table configuration
    cost_usage_table_name: str = Field(
        default="focus_cost_usage",
        description="Name of the Cost & Usage table in ClickHouse"
    )
    
    contract_commitment_table_name: str = Field(
        default="focus_contract_commitment", 
        description="Name of the Contract Commitment table in ClickHouse"
    )
    
    manifest_table_name: str = Field(
        default="focus_ingest_manifest",
        description="Name of the ingestion manifest table in ClickHouse"
    )
    
    cost_usage_view_name: str = Field(
        default="focus_data_table",
        description="Name of the Cost & Usage view with PascalCase columns"
    )
    
    contract_commitment_view_name: str = Field(
        default="focus_contract_commitment_view",
        description="Name of the Contract Commitment view with PascalCase columns"
    )

    @validator('batch_size')
    def validate_batch_size(cls, v):
        """Validate batch size is reasonable"""
        if v <= 0:
            raise ValueError("Batch size must be positive")
        if v > 100000:
            raise ValueError("Batch size too large (max 100,000)")
        return v
    
    @validator('max_workers')
    def validate_max_workers(cls, v):
        """Validate max workers is reasonable"""
        if v <= 0:
            raise ValueError("Max workers must be positive")
        if v > 32:
            raise ValueError("Max workers too large (max 32)")
        return v

    @classmethod
    def from_env_and_moose_config(cls) -> 'FocusBillingConfig':
        """Create configuration from environment variables and moose.config.toml"""
        moose_config = _get_moose_config()
        clickhouse_config = moose_config.get('clickhouse_config', {})
        
        # Override defaults with moose.config.toml values
        config_data = {}
        
        # ClickHouse configuration from moose.config.toml
        if 'host' in clickhouse_config:
            config_data['clickhouse_host'] = os.getenv('CLICKHOUSE_HOST', clickhouse_config['host'])
        if 'host_port' in clickhouse_config:
            config_data['clickhouse_port'] = int(os.getenv('CLICKHOUSE_PORT', str(clickhouse_config['host_port'])))
        if 'user' in clickhouse_config:
            config_data['clickhouse_user'] = os.getenv('CLICKHOUSE_USER', clickhouse_config['user'])
        if 'password' in clickhouse_config:
            config_data['clickhouse_password'] = os.getenv('CLICKHOUSE_PASSWORD', clickhouse_config['password'])
        if 'db_name' in clickhouse_config:
            config_data['clickhouse_database'] = os.getenv('CLICKHOUSE_DATABASE', clickhouse_config['db_name'])
        if 'use_ssl' in clickhouse_config:
            ssl_env = os.getenv('CLICKHOUSE_USE_SSL')
            if ssl_env:
                config_data['clickhouse_use_ssl'] = ssl_env.lower() == 'true'
            else:
                config_data['clickhouse_use_ssl'] = clickhouse_config['use_ssl']
        
        return cls(**config_data)
    
    def get_clickhouse_url(self) -> str:
        """Get ClickHouse connection URL"""
        protocol = "https" if self.clickhouse_use_ssl else "http"
        return f"{protocol}://{self.clickhouse_host}:{self.clickhouse_port}"
    
    def get_clickhouse_connection_params(self) -> Dict[str, Any]:
        """Get ClickHouse connection parameters for clickhouse_connect"""
        return {
            'host': self.clickhouse_host,
            'port': self.clickhouse_port,
            'username': self.clickhouse_user,
            'password': self.clickhouse_password,
            'database': self.clickhouse_database,
            'secure': self.clickhouse_use_ssl,
            'connect_timeout': self.connection_timeout,
            'send_receive_timeout': self.send_receive_timeout
        }
    
    def validate_paths(self) -> Dict[str, bool]:
        """
        Validate that required paths exist.
        
        Returns:
            Dict mapping path names to existence status
        """
        paths_to_check = {
            'focus_data_root': self.focus_data_root,
            'focus_spec_root': self.focus_spec_root,
            'focus_queries_root': self.focus_queries_root,
            'focus_specifications_root': self.focus_specifications_root
        }
        
        return {
            name: Path(path).exists()
            for name, path in paths_to_check.items()
        }
    
    def validate_clickhouse_connection(self) -> bool:
        """
        Test ClickHouse connection with current configuration.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            import clickhouse_connect
            client = clickhouse_connect.get_client(**self.get_clickhouse_connection_params())
            client.ping()
            client.close()
            return True
        except Exception:
            return False


# Lazy configuration instance (avoid module-level initialization for Temporal sandbox)
_focus_config_instance = None

def get_focus_config() -> FocusBillingConfig:
    """Get or create the global FOCUS configuration instance (lazy initialization)"""
    global _focus_config_instance
    if _focus_config_instance is None:
        _focus_config_instance = FocusBillingConfig.from_env_and_moose_config()
    return _focus_config_instance