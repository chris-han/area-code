-- FOCUS Data Model ClickHouse Schema
-- Creates optimized tables for FOCUS-compliant billing analytics

-- Main FOCUS billing data fact table
CREATE TABLE IF NOT EXISTS focus_billing_data (
    id String,
    billing_account_id String,
    billing_account_name Nullable(String),
    billing_currency String,
    billing_period_start_date Date,
    billing_period_end_date Date,
    billed_cost Decimal64(4),
    effective_cost Nullable(Decimal64(4)),
    list_cost Nullable(Decimal64(4)),
    list_unit_price Nullable(Decimal64(4)),
    usage_date Date,
    usage_quantity Nullable(Decimal64(4)),
    usage_unit Nullable(String),
    resource_id Nullable(String),
    resource_name Nullable(String),
    resource_type Nullable(String),
    service_category Nullable(String),
    service_name Nullable(String),
    availability_zone Nullable(String),
    region Nullable(String),
    provider String DEFAULT 'Azure',
    created_at DateTime64(3),
    updated_at DateTime64(3),
    source_system String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(usage_date)
ORDER BY (usage_date, billing_account_id, service_category, provider)
SETTINGS index_granularity = 8192;

-- Service category dimension table
CREATE TABLE IF NOT EXISTS focus_service_category (
    id String,
    category_name String,
    category_description Nullable(String),
    provider String,
    created_at DateTime64(3)
) ENGINE = MergeTree()
ORDER BY (provider, category_name)
SETTINGS index_granularity = 8192;

-- Resource type dimension table
CREATE TABLE IF NOT EXISTS focus_resource_type (
    id String,
    resource_type_name String,
    resource_type_description Nullable(String),
    service_category_id String,
    provider String,
    created_at DateTime64(3)
) ENGINE = MergeTree()
ORDER BY (provider, service_category_id, resource_type_name)
SETTINGS index_granularity = 8192;

-- Geography dimension table
CREATE TABLE IF NOT EXISTS focus_geography (
    id String,
    region_name String,
    availability_zone Nullable(String),
    country Nullable(String),
    provider String,
    created_at DateTime64(3)
) ENGINE = MergeTree()
ORDER BY (provider, country, region_name)
SETTINGS index_granularity = 8192;

-- Billing account dimension table
CREATE TABLE IF NOT EXISTS focus_billing_account (
    id String,
    account_name String,
    account_type Nullable(String),
    parent_account_id Nullable(String),
    provider String,
    created_at DateTime64(3),
    updated_at DateTime64(3)
) ENGINE = MergeTree()
ORDER BY (provider, id)
SETTINGS index_granularity = 8192;

-- Materialized view for monthly cost aggregations
CREATE MATERIALIZED VIEW IF NOT EXISTS focus_monthly_costs
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(usage_date)
ORDER BY (toYYYYMM(usage_date), billing_account_id, service_category, provider)
AS SELECT
    toYYYYMM(usage_date) as month,
    billing_account_id,
    billing_account_name,
    service_category,
    service_name,
    provider,
    region,
    billing_currency,
    sum(billed_cost) as total_billed_cost,
    sum(effective_cost) as total_effective_cost,
    sum(usage_quantity) as total_usage_quantity,
    count() as record_count,
    usage_date
FROM focus_billing_data
GROUP BY 
    month,
    billing_account_id,
    billing_account_name,
    service_category,
    service_name,
    provider,
    region,
    billing_currency,
    usage_date;

-- Materialized view for daily service category costs
CREATE MATERIALIZED VIEW IF NOT EXISTS focus_daily_service_costs
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(usage_date)
ORDER BY (usage_date, service_category, provider)
AS SELECT
    usage_date,
    service_category,
    service_name,
    provider,
    billing_currency,
    sum(billed_cost) as daily_billed_cost,
    sum(effective_cost) as daily_effective_cost,
    sum(usage_quantity) as daily_usage_quantity,
    count() as daily_record_count
FROM focus_billing_data
GROUP BY 
    usage_date,
    service_category,
    service_name,
    provider,
    billing_currency;

-- Index for fast cost queries by account and date range
CREATE INDEX IF NOT EXISTS idx_account_date ON focus_billing_data (billing_account_id, usage_date) TYPE minmax GRANULARITY 1;

-- Index for service category filtering
CREATE INDEX IF NOT EXISTS idx_service_category ON focus_billing_data (service_category) TYPE set(100) GRANULARITY 1;

-- Index for provider filtering
CREATE INDEX IF NOT EXISTS idx_provider ON focus_billing_data (provider) TYPE set(10) GRANULARITY 1;

-- Index for region filtering
CREATE INDEX IF NOT EXISTS idx_region ON focus_billing_data (region) TYPE set(100) GRANULARITY 1;

-- Insert default service categories for Azure
INSERT INTO focus_service_category (id, category_name, category_description, provider, created_at) VALUES
('azure_compute', 'Compute', 'Virtual machines, containers, and compute services', 'Azure', now()),
('azure_storage', 'Storage', 'Blob storage, file storage, and data services', 'Azure', now()),
('azure_networking', 'Networking', 'Virtual networks, load balancers, and network services', 'Azure', now()),
('azure_database', 'Database', 'SQL databases, NoSQL databases, and data services', 'Azure', now()),
('azure_analytics', 'Analytics', 'Data analytics, machine learning, and AI services', 'Azure', now()),
('azure_security', 'Security', 'Identity, security, and compliance services', 'Azure', now()),
('azure_management', 'Management', 'Monitoring, management, and governance services', 'Azure', now()),
('azure_other', 'Other', 'Other Azure services not categorized above', 'Azure', now());

-- Insert common Azure regions
INSERT INTO focus_geography (id, region_name, availability_zone, country, provider, created_at) VALUES
('azure_eastus', 'East US', NULL, 'United States', 'Azure', now()),
('azure_eastus2', 'East US 2', NULL, 'United States', 'Azure', now()),
('azure_westus', 'West US', NULL, 'United States', 'Azure', now()),
('azure_westus2', 'West US 2', NULL, 'United States', 'Azure', now()),
('azure_centralus', 'Central US', NULL, 'United States', 'Azure', now()),
('azure_northcentralus', 'North Central US', NULL, 'United States', 'Azure', now()),
('azure_southcentralus', 'South Central US', NULL, 'United States', 'Azure', now()),
('azure_westcentralus', 'West Central US', NULL, 'United States', 'Azure', now()),
('azure_westeurope', 'West Europe', NULL, 'Netherlands', 'Azure', now()),
('azure_northeurope', 'North Europe', NULL, 'Ireland', 'Azure', now()),
('azure_eastasia', 'East Asia', NULL, 'Hong Kong', 'Azure', now()),
('azure_southeastasia', 'Southeast Asia', NULL, 'Singapore', 'Azure', now()),
('azure_japaneast', 'Japan East', NULL, 'Japan', 'Azure', now()),
('azure_japanwest', 'Japan West', NULL, 'Japan', 'Azure', now()),
('azure_australiaeast', 'Australia East', NULL, 'Australia', 'Azure', now()),
('azure_australiasoutheast', 'Australia Southeast', NULL, 'Australia', 'Azure', now());