-- FOCUS Billing Integration DDL Statements
-- Companion DDL for reapplication
-- Generated from FOCUS specifications

-- Drop existing objects (in reverse dependency order)
DROP VIEW IF EXISTS focus_data_table;
DROP VIEW IF EXISTS focus_contract_commitment_view;
DROP TABLE IF EXISTS focus_cost_usage;
DROP TABLE IF EXISTS focus_contract_commitment;
DROP TABLE IF EXISTS focus_ingest_manifest;

-- Cost & Usage Table
CREATE TABLE focus_cost_usage (
    id String COMMENT 'Deterministic hash ID for the row',
    usage_date Date COMMENT 'Date when the usage occurred (derived from ChargePeriodStart)',
    availability_zone Nullable(String) COMMENT 'A provider-assigned identifier for a physically separated and isolated area within a Region that provides high availability and fault tolerance.',
    billed_cost Decimal(38, 18) COMMENT 'A *charge* serving as the basis for invoicing, inclusive of all reduced rates and discounts while excluding the *amortization* of upfront *charges* (one-time or recurring).',
    billing_account_id String COMMENT 'The identifier assigned to a *billing account* by the provider.',
    billing_account_name Nullable(String) COMMENT 'The display name assigned to a *billing account*.',
    billing_account_type String COMMENT 'A provider-assigned name to identify the type of *billing account*.',
    billing_currency String COMMENT 'Represents the currency that a *charge* was billed in.',
    billing_period_end DateTime64(3) COMMENT 'The *exclusive end bound* of a *billing period*.',
    billing_period_start DateTime64(3) COMMENT 'The *inclusive start bound* of a *billing period*.',
    capacity_reservation_id Nullable(String) COMMENT 'The identifier assigned to a *capacity reservation* by the provider.',
    capacity_reservation_status Nullable(String) COMMENT 'Indicates whether the *charge* represents either the consumption of a *capacity reservation* or when a *capacity reservation* is unused.',
    charge_category String COMMENT 'Represents the highest-level classification of a *charge* based on the nature of how it is billed.',
    charge_class Nullable(String) COMMENT 'Indicates whether the *row* represents a correction to a previously invoiced *billing period*.',
    charge_description Nullable(String) COMMENT 'Self-contained summary of the *charge\'s* purpose and price.',
    charge_frequency String COMMENT 'Indicates how often a *charge* will occur.',
    charge_period_end DateTime64(3) COMMENT 'The *exclusive end bound* of a *charge period*.',
    charge_period_start DateTime64(3) COMMENT 'The *inclusive start bound* of a *charge period*.',
    commitment_discount_category Nullable(String) COMMENT 'Indicates whether the *commitment discount* identified in the CommitmentDiscountId column is based on usage quantity or cost (aka "spend").',
    commitment_discount_id Nullable(String) COMMENT 'The identifier assigned to a *commitment discount* by the provider.',
    commitment_discount_name Nullable(String) COMMENT 'The display name assigned to a *commitment discount*.',
    commitment_discount_quantity Nullable(Decimal(38, 18)) COMMENT 'The amount of a *commitment discount* purchased or accounted for in *commitment discount* related *rows* that is denominated in Commitment Discount Units.',
    commitment_discount_status Nullable(String) COMMENT 'Indicates whether the *charge* corresponds with the consumption of a *commitment discount* or the unused portion of the committed amount.',
    commitment_discount_type Nullable(String) COMMENT 'A provider-assigned identifier for the type of *commitment discount* applied to the *row*.',
    commitment_discount_unit Nullable(String) COMMENT 'The provider-specified measurement unit indicating how a provider measures the Commitment Discount Quantity of a *commitment discount*.',
    consumed_quantity Nullable(Decimal(38, 18)) COMMENT 'The volume of a metered SKU associated with a *resource* or *service* used, based on the Consumed Unit.',
    consumed_unit Nullable(String) COMMENT 'Provider-specified measurement unit indicating how a provider measures usage of a metered SKU associated with a *resource* or *service*.',
    contracted_cost Decimal(38, 18) COMMENT 'Cost calculated by multiplying *contracted unit price* and the corresponding Pricing Quantity.',
    contracted_unit_price Nullable(Decimal(38, 18)) COMMENT 'The agreed-upon unit price for a single Pricing Unit of the associated SKU, inclusive of negotiated discounts, if present, while excluding negotiated commitment discounts or any other discounts.',
    effective_cost Decimal(38, 18) COMMENT 'The *amortized* cost of the *charge* after applying all reduced rates, discounts, and the applicable portion of relevant, prepaid purchases (one-time or recurring) that covered this *charge*.',
    invoice_id Nullable(String) COMMENT 'The provider-assigned identifier for an invoice encapsulating some or all *charges* in the corresponding billing period for a given billing account.',
    invoice_issuer_name String COMMENT 'The name of the entity responsible for invoicing for the *resources* or *services* consumed.',
    list_cost Decimal(38, 18) COMMENT 'Cost calculated by multiplying List Unit Price and the corresponding Pricing Quantity.',
    list_unit_price Nullable(Decimal(38, 18)) COMMENT 'The suggested provider-published unit price for a single Pricing Unit of the associated SKU, exclusive of any discounts.',
    pricing_category Nullable(String) COMMENT 'Describes the pricing model used for a *charge* at the time of use or purchase.',
    pricing_currency Nullable(String) COMMENT 'The national or virtual currency denomination that a *resource* or *service* was priced in.',
    pricing_currency_contracted_unit_price Nullable(Decimal(38, 18)) COMMENT 'The agreed-upon unit price for a single Pricing Unit of the associated SKU, inclusive of *negotiated discounts*, if present, while excluding negotiated *commitment discounts* or any other discounts, and expressed in Pricing Currency.',
    pricing_currency_effective_cost Nullable(Decimal(38, 18)) COMMENT 'The cost of the *charge* after applying all reduced rates, discounts, and the applicable portion of relevant, prepaid purchases (one-time or recurring) that covered this *charge*, as denominated in Pricing Currency.',
    pricing_currency_list_unit_price Nullable(Decimal(38, 18)) COMMENT 'The suggested provider-published unit price for a single Pricing Unit of the associated *SKU*, exclusive of any discounts and expressed in Pricing Currency.',
    pricing_quantity Nullable(Decimal(38, 18)) COMMENT 'The volume of a given *SKU* associated with a *resource* or *service* used or purchased, based on the Pricing Unit.',
    pricing_unit Nullable(String) COMMENT 'Provider-specified measurement unit for determining unit prices, indicating how the provider rates measured usage and purchase quantities after applying pricing rules like *block pricing*.',
    provider_name String COMMENT 'The name of the entity that made the *resources* or *services* available for purchase.',
    publisher_name String COMMENT 'The name of the entity that produced the *resources* or *services* that were purchased.',
    region_id Nullable(String) COMMENT 'Provider-assigned identifier for an isolated geographic area where a *resource* is provisioned or a *service* is provided.',
    region_name Nullable(String) COMMENT 'The name of an isolated geographic area where a *resource* is provisioned or a *service* is provided.',
    resource_id Nullable(String) COMMENT 'Identifier assigned to a *resource* by the provider.',
    resource_name Nullable(String) COMMENT 'Display name assigned to a *resource*.',
    resource_type Nullable(String) COMMENT 'The kind of *resource* the *charge* applies to.',
    service_category String COMMENT 'Highest-level classification of a *service* based on the core function of the *service*.',
    service_name String COMMENT 'An offering that can be purchased from a provider (e.g., cloud virtual machine, SaaS database, professional *services* from a systems integrator).',
    service_subcategory String COMMENT 'Secondary classification of the Service Category for a *service* based on its core function.',
    sku_id Nullable(String) COMMENT 'Provider-specified unique identifier that represents a specific *SKU* (e.g., a quantifiable good or service offering).',
    sku_meter Nullable(String) COMMENT 'Describes the functionality being metered or measured by a particular SKU in a *charge*.',
    sku_price_details Nullable(String) COMMENT 'A set of properties of a SKU Price ID which are meaningful and common to all instances of that SKU Price ID.',
    sku_price_id Nullable(String) COMMENT 'A provider-specified unique identifier that represents a specific *SKU Price* associated with a *resource* or *service* used or purchased.',
    sub_account_id Nullable(String) COMMENT 'An ID assigned to a grouping of [*resources*](#glossary:resource) or [*services*](#glossary:service), often used to manage access and/or cost.',
    sub_account_name Nullable(String) COMMENT 'A name assigned to a grouping of [*resources*](#glossary:resource) or [*services*](#glossary:service), often used to manage access and/or cost.',
    sub_account_type Nullable(String) COMMENT 'A provider-assigned name to identify the type of *sub account*.',
    tags Nullable(String) COMMENT 'The set of tags assigned to *tag sources* that account for potential provider-defined or user-defined tag evaluations.',
    source_system String COMMENT 'Source system identifier',
    created_at DateTime64(3) COMMENT 'Record creation timestamp',
    updated_at DateTime64(3) COMMENT 'Record update timestamp'
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(usage_date)
ORDER BY (usage_date, billing_account_id, service_category, service_name)
SETTINGS index_granularity = 8192, allow_nullable_key = 1
COMMENT 'FOCUS Cost & Usage dataset with snake_case column names and FOCUS metadata';

-- Contract Commitment Table
CREATE TABLE focus_contract_commitment (
    id String COMMENT 'Deterministic hash ID for the row',
    billing_currency String COMMENT 'Represents the currency that a *charge* was billed in.',
    source_system String COMMENT 'Source system identifier',
    created_at DateTime64(3) COMMENT 'Record creation timestamp',
    updated_at DateTime64(3) COMMENT 'Record update timestamp'
)
ENGINE = MergeTree()
ORDER BY (contract_commitment_id, billing_account_id)
SETTINGS index_granularity = 8192, allow_nullable_key = 1
COMMENT 'FOCUS Contract Commitment dataset with snake_case column names and FOCUS metadata';

-- Ingestion Manifest Table
CREATE TABLE focus_ingest_manifest (
    id String COMMENT 'Unique manifest entry ID',
    file_path String COMMENT 'Relative path to processed file',
    file_checksum String COMMENT 'File checksum for change detection',
    dataset_type String COMMENT 'Dataset type (cost_usage or contract_commitment)',
    rows_processed UInt64 COMMENT 'Number of rows processed',
    processing_status String COMMENT 'Processing status (success, failed, skipped)',
    error_message Nullable(String) COMMENT 'Error message if processing failed',
    processed_at DateTime64(3) COMMENT 'Processing timestamp',
    manifest_metadata Nullable(String) COMMENT 'Additional metadata from manifest.json as JSON string'
)
ENGINE = MergeTree()
ORDER BY (processed_at, dataset_type)
SETTINGS index_granularity = 8192
COMMENT 'Manifest table for tracking processed FOCUS Parquet files';

-- Cost & Usage View (PascalCase)
CREATE VIEW focus_data_table AS
SELECT
    id AS Id,
    usage_date AS UsageDate,
    availability_zone AS AvailabilityZone,
    billed_cost AS BilledCost,
    billing_account_id AS BillingAccountId,
    billing_account_name AS BillingAccountName,
    billing_account_type AS BillingAccountType,
    billing_currency AS BillingCurrency,
    billing_period_end AS BillingPeriodEnd,
    billing_period_start AS BillingPeriodStart,
    capacity_reservation_id AS CapacityReservationId,
    capacity_reservation_status AS CapacityReservationStatus,
    charge_category AS ChargeCategory,
    charge_class AS ChargeClass,
    charge_description AS ChargeDescription,
    charge_frequency AS ChargeFrequency,
    charge_period_end AS ChargePeriodEnd,
    charge_period_start AS ChargePeriodStart,
    commitment_discount_category AS CommitmentDiscountCategory,
    commitment_discount_id AS CommitmentDiscountId,
    commitment_discount_name AS CommitmentDiscountName,
    commitment_discount_quantity AS CommitmentDiscountQuantity,
    commitment_discount_status AS CommitmentDiscountStatus,
    commitment_discount_type AS CommitmentDiscountType,
    commitment_discount_unit AS CommitmentDiscountUnit,
    consumed_quantity AS ConsumedQuantity,
    consumed_unit AS ConsumedUnit,
    contracted_cost AS ContractedCost,
    contracted_unit_price AS ContractedUnitPrice,
    effective_cost AS EffectiveCost,
    invoice_id AS InvoiceId,
    invoice_issuer_name AS InvoiceIssuerName,
    list_cost AS ListCost,
    list_unit_price AS ListUnitPrice,
    pricing_category AS PricingCategory,
    pricing_currency AS PricingCurrency,
    pricing_currency_contracted_unit_price AS PricingCurrencyContractedUnitPrice,
    pricing_currency_effective_cost AS PricingCurrencyEffectiveCost,
    pricing_currency_list_unit_price AS PricingCurrencyListUnitPrice,
    pricing_quantity AS PricingQuantity,
    pricing_unit AS PricingUnit,
    provider_name AS ProviderName,
    publisher_name AS PublisherName,
    region_id AS RegionId,
    region_name AS RegionName,
    resource_id AS ResourceId,
    resource_name AS ResourceName,
    resource_type AS ResourceType,
    service_category AS ServiceCategory,
    service_name AS ServiceName,
    service_subcategory AS ServiceSubcategory,
    sku_id AS SkuId,
    sku_meter AS SkuMeter,
    sku_price_details AS SkuPriceDetails,
    sku_price_id AS SkuPriceId,
    sub_account_id AS SubAccountId,
    sub_account_name AS SubAccountName,
    sub_account_type AS SubAccountType,
    tags AS Tags,
    source_system AS SourceSystem,
    created_at AS CreatedAt,
    updated_at AS UpdatedAt
FROM focus_cost_usage;

-- Contract Commitment View (PascalCase)
CREATE VIEW focus_contract_commitment_view AS
SELECT
    id AS Id,
    billing_currency AS BillingCurrency,
    contract_commitment_id AS ContractCommitmentId,
    contract_id AS ContractId,
    contract_period_start AS ContractPeriodStart,
    contract_period_end AS ContractPeriodEnd,
    contract_commitment_period_start AS ContractCommitmentPeriodStart,
    contract_commitment_period_end AS ContractCommitmentPeriodEnd,
    contract_commitment_description AS ContractCommitmentDescription,
    contract_commitment_type AS ContractCommitmentType,
    contract_commitment_category AS ContractCommitmentCategory,
    contract_commitment_unit AS ContractCommitmentUnit,
    contract_commitment_quantity AS ContractCommitmentQuantity,
    contract_commitment_cost AS ContractCommitmentCost,
    source_system AS SourceSystem,
    created_at AS CreatedAt,
    updated_at AS UpdatedAt
FROM focus_contract_commitment;
