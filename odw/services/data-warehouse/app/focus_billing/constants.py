"""
FOCUS Billing Constants

Constants and enumerations used throughout the FOCUS billing integration.
"""

from enum import Enum


class FocusDatasetType(str, Enum):
    """FOCUS dataset types"""
    COST_USAGE = "cost_and_usage"
    CONTRACT_COMMITMENT = "contract_commitment"


class FocusTableNames:
    """Standard table names for FOCUS datasets"""
    COST_USAGE = "focus_cost_usage"
    CONTRACT_COMMITMENT = "focus_contract_commitment"
    INGEST_MANIFEST = "focus_ingest_manifest"


class FocusViewNames:
    """Standard view names for FOCUS datasets"""
    COST_USAGE = "focus_data_table"
    CONTRACT_COMMITMENT = "focus_contract_commitment_view"


class FocusChargeCategory(str, Enum):
    """FOCUS charge categories"""
    USAGE = "Usage"
    PURCHASE = "Purchase"
    TAX = "Tax"
    CREDIT = "Credit"
    ADJUSTMENT = "Adjustment"


class FocusChargePeriod(str, Enum):
    """FOCUS charge periods"""
    MONTHLY = "Monthly"
    DAILY = "Daily"
    HOURLY = "Hourly"
    ONE_TIME = "OneTime"


class FocusPricingCategory(str, Enum):
    """FOCUS pricing categories"""
    ON_DEMAND = "On-Demand"
    COMMITTED_USE = "Committed Use"
    OTHER = "Other"


class FocusCommitmentDiscountCategory(str, Enum):
    """FOCUS commitment discount categories"""
    SPEND = "Spend"
    USAGE = "Usage"


class FocusCommitmentDiscountType(str, Enum):
    """FOCUS commitment discount types"""
    COMMITTED_USE_DISCOUNT = "Committed Use Discount"
    RESERVED_INSTANCE = "Reserved Instance"
    SAVINGS_PLAN = "Savings Plan"


class FocusProcessingStatus(str, Enum):
    """Processing status for manifest entries"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    IN_PROGRESS = "in_progress"


class FocusQueryCategories:
    """Categories for FOCUS queries"""
    COST_ANALYSIS = "Cost Analysis"
    USAGE_ANALYSIS = "Usage Analysis"
    COMMITMENT_ANALYSIS = "Commitment Analysis"
    BILLING_ANALYSIS = "Billing Analysis"
    RESOURCE_ANALYSIS = "Resource Analysis"


class FocusMetadataKeys:
    """Keys for FOCUS metadata"""
    COLUMN_TYPE = "column_type"
    FEATURE_LEVEL = "feature_level"
    ALLOWS_NULLS = "allows_nulls"
    DATA_TYPE = "data_type"
    DESCRIPTION = "description"


class FocusDefaultValues:
    """Default values for FOCUS fields"""
    CURRENCY = "USD"
    SOURCE_SYSTEM = "focus_parquet"
    BATCH_SIZE = 10000
    MAX_WORKERS = 4
    DECIMAL_PRECISION = 38
    DECIMAL_SCALE = 18


class FocusFilePatterns:
    """File patterns for FOCUS data discovery"""
    PARQUET_EXTENSION = ".parquet"
    MANIFEST_FILENAME = "manifest.json"
    COST_USAGE_PATTERN = "**/cost_and_usage/**/*.parquet"
    CONTRACT_COMMITMENT_PATTERN = "**/contract_commitment/**/*.parquet"


class FocusClickHouseTypes:
    """ClickHouse type mappings for FOCUS data types"""
    STRING = "String"
    NULLABLE_STRING = "Nullable(String)"
    DECIMAL = "Decimal(38, 18)"
    NULLABLE_DECIMAL = "Nullable(Decimal(38, 18))"
    DATE = "Date"
    NULLABLE_DATE = "Nullable(Date)"
    DATETIME = "DateTime64(3)"
    NULLABLE_DATETIME = "Nullable(DateTime64(3))"
    UINT8 = "UInt8"  # For boolean values
    INT32 = "Int32"
    INT64 = "Int64"
    FLOAT64 = "Float64"


class FocusPartitioningStrategy:
    """Partitioning strategies for FOCUS tables"""
    COST_USAGE_PARTITION = "toYYYYMM(usage_date)"
    CONTRACT_COMMITMENT_PARTITION = "toYYYYMM(contract_commitment_start_date)"


class FocusIndexingStrategy:
    """Indexing strategies for FOCUS tables"""
    COST_USAGE_ORDER_BY = "(usage_date, billing_account_id, service_category, service_name)"
    CONTRACT_COMMITMENT_ORDER_BY = "(contract_commitment_start_date, billing_account_id, contract_commitment_id)"
    
    # Min/max indexes
    MINMAX_INDEXES = ["billing_account_id", "usage_date"]
    
    # Set indexes for categorical data
    SET_INDEXES = ["service_category", "provider_name", "region_id"]


class FocusValidationRules:
    """Validation rules for FOCUS data"""
    MAX_STRING_LENGTH = 65535
    MAX_DECIMAL_PRECISION = 38
    MAX_DECIMAL_SCALE = 18
    MIN_DATE = "1900-01-01"
    MAX_DATE = "2100-12-31"
    
    # Required fields by dataset
    COST_USAGE_REQUIRED = ["billing_account_id", "usage_date", "billed_cost"]
    CONTRACT_COMMITMENT_REQUIRED = ["contract_commitment_id"]


class FocusErrorMessages:
    """Standard error messages"""
    MISSING_REQUIRED_FIELD = "Missing required field: {field}"
    INVALID_DATA_TYPE = "Invalid data type for field {field}: expected {expected}, got {actual}"
    INVALID_DATE_FORMAT = "Invalid date format for field {field}: expected YYYY-MM-DD"
    INVALID_DECIMAL_PRECISION = "Decimal precision exceeds maximum for field {field}"
    FILE_NOT_FOUND = "File not found: {file_path}"
    SCHEMA_MISMATCH = "Schema mismatch for dataset {dataset}: {details}"
    CLICKHOUSE_CONNECTION_ERROR = "Failed to connect to ClickHouse: {error}"
    QUERY_EXECUTION_ERROR = "Failed to execute query: {error}"