-- FOCUS Billing Integration DDL Statements
-- Companion DDL for reapplication

-- Drop existing objects
DROP VIEW IF EXISTS focus_data_table;
DROP TABLE IF EXISTS focus_cost_usage;

-- Create table
CREATE TABLE focus_cost_usage (
    id String COMMENT 'Deterministic hash ID for the row',
    usage_date Date COMMENT 'Date when the usage occurred',
    billing_account_id String COMMENT 'Billing Account ID',
    billed_cost Decimal(18,4) COMMENT 'Billed Cost',
    source_system String COMMENT 'Source system identifier',
    created_at DateTime64(3) COMMENT 'Record creation timestamp',
    updated_at DateTime64(3) COMMENT 'Record update timestamp'
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(usage_date)
ORDER BY (usage_date, billing_account_id)
SETTINGS index_granularity = 8192, allow_nullable_key = 1
COMMENT 'FOCUS Cost & Usage dataset with snake_case column names';

-- Create view
CREATE VIEW focus_data_table AS
SELECT
    id AS Id,
    usage_date AS UsageDate,
    billing_account_id AS BillingAccountId,
    billed_cost AS BilledCost,
    source_system AS SourceSystem,
    created_at AS CreatedAt,
    updated_at AS UpdatedAt
FROM focus_cost_usage;
