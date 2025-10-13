-- DROP TABLE IF EXISTS dbo.f_azure_billing_detail;

CREATE TABLE IF NOT EXISTS dbo.f_azure_billing_detail
(
    -- Unique identifier for the billing detail
    id UInt64,

    -- Text fields mapped to ClickHouse String type
    account_owner_id Nullable(String),
    account_name Nullable(String),
    service_administrator_id Nullable(String),

    -- Bigint mapped to Int64
    subscription_id Int64,
    subscription_guid Nullable(String),
    subscription_name Nullable(String),

    -- Date mapped to Date for a wider date range support
    date Date,

    -- Bigint mapped to Int64
    month Int64,
    day Int64,
    year Int64,

    -- Text fields mapped to String
    product Nullable(String),
    meter_id Nullable(String),
    meter_category Nullable(String),
    meter_sub_category Nullable(String),
    meter_region Nullable(String),
    meter_name Nullable(String),

    -- Double precision mapped to Float64
    consumed_quantity Float64,
    resource_rate Float64,
    extended_cost Float64,

    -- Text fields mapped to String
    resource_location Nullable(String),
    consumed_service Nullable(String),
    instance_id String,
    service_info1 Nullable(String),
    service_info2 Nullable(String),

    -- JSONB mapped to String/JSON
    additional_info Nullable(JSON),
    tags Nullable(JSON),

    -- Text fields mapped to String
    store_service_identifier Nullable(String),
    department_name Nullable(String),
    cost_center Nullable(String),
    unit_of_measure Nullable(String),
    resource_group Nullable(String),

    -- Numeric mapped to Float64
    extended_cost_tax Float64,

    -- Character varying mapped to String
    resource_tracking Nullable(String),

    -- Bytea mapped to FixedString
    resource_tracking_hash UInt64,

    -- Character varying mapped to String
    resource_name Nullable(String),
    vm_name Nullable(String),
    latest_resource_type Nullable(String),
    newmonth Nullable(String),

    -- Date mapped to Date
    month_date Date,

    -- Character varying mapped to String
    sku Nullable(String),
    vmlookupkey Nullable(String),

    -- Bytea mapped to FixedString
    -- vmlookupkey_hash FixedString(18),
    cpp_pkey_hash UInt64, 

    discount_pkey_hash UInt64,

    -- Character varying mapped to String
    cmdb_mapped_application_service Nullable(String),
    ppm_billing_item Nullable(String),
    ppm_id_owner Nullable(String),
    ppm_io_cc Nullable(String),

    is_new_billing_item_mom Bool,
    -- billing_item Nullable(String),
    -- segment Nullable(String),
    -- cpp_plan Nullable(String),
    -- cpp_order Nullable(String),
    -- cost_center Nullable(String),
    -- Timestamp with default value
    create_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
-- KEY OPTIMIZATION: Order by the columns used in your window function
ORDER BY (id,resource_tracking_hash)
-- Keep the same partitioning strategy
PARTITION BY toYYYYMM(month_date);
;

