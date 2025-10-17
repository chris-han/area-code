# Welcome to your new Moose analytical backend! 🦌

# Getting Started Guide:

# 1. Data Modeling
# First, plan your data structure and create your data models
# → See: docs.fiveonefour.com/moose/building/data-modeling
#   Learn about type definitions and data validation

# 2. Set Up Ingestion
# Create ingestion pipelines to receive your data via REST APIs
# → See: docs.fiveonefour.com/moose/building/ingestion
#   Learn about IngestPipeline, data formats, and validation

# 3. Create Workflows
# Build data processing pipelines to transform and analyze your data
# → See: docs.fiveonefour.com/moose/building/workflows
#   Learn about task scheduling and data processing

# 4. Configure Consumption APIs
# Set up queries and real-time analytics for your data
# → See: docs.fiveonefour.com/moose/building/consumption-apis

# Need help? Check out the quickstart guide:
# → docs.fiveonefour.com/moose/getting-started/quickstart


from pydantic import BaseModel, Field
from typing import Optional, Any, Annotated
import datetime
import ipaddress
from uuid import UUID
from enum import IntEnum, Enum
from moose_lib import Key, IngestPipeline, IngestPipelineConfig, OlapTable, OlapConfig, clickhouse_datetime64, clickhouse_decimal, ClickhouseSize, StringToEnumMixin
from moose_lib import Point, Ring, LineString, MultiLineString, Polygon, MultiPolygon
from moose_lib import clickhouse_default, LifeCycle
from moose_lib.blocks import MergeTreeEngine, ReplacingMergeTreeEngine, AggregatingMergeTreeEngine, SummingMergeTreeEngine, S3QueueEngine, ReplicatedMergeTreeEngine, ReplicatedReplacingMergeTreeEngine, ReplicatedAggregatingMergeTreeEngine, ReplicatedSummingMergeTreeEngine

class d_application_tag(BaseModel):
    id: Annotated[int, "int32"]
    resource_tracking_hash: Annotated[int, "uint64"]
    cappm: Optional[str] = None
    project_name: Optional[str] = None
    billing_item: Optional[str] = None
    application_owner: Optional[str] = None
    server_build: Optional[str] = None
    resource_tracking: Optional[str] = None
    initial_resource_type: Optional[str] = None
    go_live: Optional[str] = None
    segment: Optional[str] = None
    unit: Optional[str] = None
    branch: Optional[str] = None
    masterteam: Optional[str] = None
    team: Optional[str] = None
    function: Optional[str] = None
    cpp_plan: Optional[str] = None
    cpp_order: Optional[str] = None
    region: Optional[str] = None
    scope: Optional[str] = None
    cost_center: Optional[str] = None
    is_new_billing_item_mom: bool
    name_source: Optional[str] = None
    xls_file_path: Optional[str] = None
    create_at: Annotated[datetime.datetime, clickhouse_default("now()")]
    update_at: Annotated[datetime.datetime, clickhouse_default("now()")]

class d_azure_retail_prices(BaseModel):
    id: Annotated[int, "uint64"]
    currency_code: str
    tier_minimum_units: float
    retail_price: float
    unit_price: float
    arm_region_name: str
    location: str
    effective_start_date: datetime.datetime
    meter_id: str
    meter_name: str
    product_id: str
    sku_id: str
    product_name: str
    sku_name: str
    service_name: str
    service_family: str
    unit_of_measure: str
    type: str
    is_primary_meter: Optional[str] = None
    arm_sku_name: str
    reservation_term: str
    created_at: datetime.datetime
    meter_id_location: str
    duplicate_count: Annotated[int, "uint64"]
    rn_eff_date: Annotated[int, "uint64"]

class d_exchange_rate(BaseModel):
    id: Annotated[int, "int32"]
    year: Annotated[int, "int32"]
    exchange_rate: Optional[float] = None
    xls_file_path: Optional[str] = None
    create_at: Annotated[datetime.datetime, clickhouse_default("now()")]

class d_managed_disks(BaseModel):
    Type: str
    Disk_Size: str = Field(alias="Disk Size")
    Price_per_month(untax): str = Field(alias="Price per month(untax)")
    IOPS_per_disk: str = Field(alias="IOPS per disk")
    Throughput_per_disk: str = Field(alias="Throughput per disk")
    Shared_Disk(untax): str = Field(alias="Shared Disk(untax)")
    Disks_MeterName: str = Field(alias="Disks MeterName")

class d_monthly_budget(BaseModel):
    billing_item: Key[str]
    year: Key[Annotated[int, "uint16"]]
    budget_values: list[clickhouse_decimal(18, 2)]
    created_date: Annotated[datetime.datetime, clickhouse_default("now()")]
    updated_date: Annotated[datetime.datetime, clickhouse_default("now()")]

class dq_tagging_audit(BaseModel):
    audit_id: Annotated[Annotated[int, "uint64"], clickhouse_default("xxHash64(instance_id, toString(audit_timestamp))")]
    instance_id: str
    last_segment: Optional[str] = None
    resource_group: Optional[str] = None
    subscription_guid: Optional[str] = None
    last_segment_match: Optional[str] = None
    resource_group_match: Optional[str] = None
    subscription_match: Optional[str] = None
    selected_match: Optional[str] = None
    meter_category: Optional[str] = None
    audit_timestamp: Annotated[datetime.datetime, clickhouse_default("now()")]

class f_azure_billing_detail(BaseModel):
    id: Annotated[int, "uint64"]
    account_owner_id: Optional[str] = None
    account_name: Optional[str] = None
    service_administrator_id: Optional[str] = None
    subscription_id: Annotated[int, "int64"]
    subscription_guid: Optional[str] = None
    subscription_name: Optional[str] = None
    date: Annotated[datetime.date, ClickhouseSize(2)]
    month: Annotated[int, "int64"]
    day: Annotated[int, "int64"]
    year: Annotated[int, "int64"]
    product: Optional[str] = None
    meter_id: Optional[str] = None
    meter_category: Optional[str] = None
    meter_sub_category: Optional[str] = None
    meter_region: Optional[str] = None
    meter_name: Optional[str] = None
    consumed_quantity: float
    resource_rate: float
    extended_cost: float
    resource_location: Optional[str] = None
    consumed_service: Optional[str] = None
    instance_id: str
    service_info1: Optional[str] = None
    service_info2: Optional[str] = None
    additional_info: Optional[Any] = None
    tags: Optional[Any] = None
    store_service_identifier: Optional[str] = None
    department_name: Optional[str] = None
    cost_center: Optional[str] = None
    unit_of_measure: Optional[str] = None
    resource_group: Optional[str] = None
    extended_cost_tax: float
    resource_tracking: Optional[str] = None
    resource_tracking_hash: Annotated[int, "uint64"]
    resource_name: Optional[str] = None
    vm_name: Optional[str] = None
    latest_resource_type: Optional[str] = None
    newmonth: Optional[str] = None
    month_date: Annotated[datetime.date, ClickhouseSize(2)]
    sku: Optional[str] = None
    vmlookupkey: Optional[str] = None
    cpp_pkey_hash: Annotated[int, "uint64"]
    discount_pkey_hash: Annotated[int, "uint64"]
    cmdb_mapped_application_service: Optional[str] = None
    ppm_billing_item: Optional[str] = None
    ppm_id_owner: Optional[str] = None
    ppm_io_cc: Optional[str] = None
    is_new_billing_item_mom: bool
    create_at: Annotated[datetime.datetime, clickhouse_default("now()")]

class f_azure_billing_resource_tracking(BaseModel):
    id: Annotated[int, "uint64"]
    resource_tracking: str
    resource_tracking_hash: Annotated[int, "uint64"]
    create_at: Annotated[datetime.datetime, clickhouse_default("now()")]
    update_at: Annotated[datetime.datetime, clickhouse_default("now()")]

class f_budget(BaseModel):
    id: Annotated[int, "int64"]
    Charge_Model: str
    Application: str
    Scope: str
    Jan: float
    Feb: float
    Mar: float
    Apr: float
    May: float
    Jun: float
    Jul: float
    Aug: float
    Sep: float
    Oct: float
    Nov: float
    Dec: float

class f_budget_plan(BaseModel):
    id: Annotated[int, "uint32"]
    AppName: str
    month_date: Annotated[datetime.date, ClickhouseSize(2)]
    budget: float
    xls_file_path: str
    create_at: datetime.datetime
    update_at: datetime.datetime

class f_cpp_detail(BaseModel):
    cpp_pkey_hash: Annotated[int, "uint64"]
    vmlookupkey: str
    cpp_contract_date: Annotated[datetime.date, ClickhouseSize(2)]
    description: str
    sku_os: str
    meter_name: str
    meter_region: str
    cpp_count: Annotated[int, "int32"]
    cpp_monthly_cost_tax: Annotated[float, "float32"]
    cpp_monthly_unit_price_tax: Annotated[float, "float32"]
    cpp_hourly_unit_price_tax: Annotated[float, "float32"]
    official_monthly_cost_tax: Annotated[float, "float32"]
    official_monthly_unit_price_tax: Annotated[float, "float32"]
    official_hourly_unit_price_tax: Annotated[float, "float32"]
    VCPU: Annotated[float, "float32"]
    Memory: Annotated[float, "float32"]
    cpp_coverage_hours: Annotated[int, "int32"]

class f_cpp_detail_dbt(BaseModel):
    cpp_pkey_hash: Annotated[int, "uint64"]
    vmlookupkey: str
    cpp_contract_date: Annotated[datetime.date, ClickhouseSize(2)]
    description: str
    sku_os: str
    meter_name: str
    meter_region: str
    cpp_count: Annotated[int, "int8"]
    cpp_monthly_cost_tax: Annotated[float, "float32"]
    cpp_monthly_unit_price_tax: Annotated[float, "float32"]
    cpp_hourly_unit_price_tax: Annotated[float, "float32"]
    official_monthly_cost_tax: Annotated[float, "float32"]
    official_monthly_unit_price_tax: Annotated[float, "float32"]
    official_hourly_unit_price_tax: Annotated[float, "float32"]
    cpp_coverage_hours: Annotated[int, "int8"]

class f_est_cumulative_saving(BaseModel):
    id: Annotated[int, "int32"]
    month_date: Annotated[datetime.date, ClickhouseSize(2)]
    estimated_saving_usd: Optional[float] = None
    xls_file_path: Optional[str] = None
    create_at: Annotated[datetime.datetime, clickhouse_default("now()")]

class f_mars_bugdet_each_application_by_month(BaseModel):
    Month: Annotated[datetime.date, ClickhouseSize(2)]
    billing_item: str
    cost_center: str
    Cost: float
    chargeback_status: bool

class f_mars_bugdet_each_application_by_week(BaseModel):
    Month: Annotated[datetime.date, ClickhouseSize(2)]
    billing_item: str
    cost_center: str
    Cost: float
    chargeback_status: bool

class f_mars_bugdet_result_re(BaseModel):
    billing_item: str
    cost_center: str
    chargeback_status: Annotated[int, "uint8"]
    Month: str
    formula: str
    cgmr: float
    value: float
    calc_date: str
    update_date: Annotated[datetime.date, ClickhouseSize(2)]
    created_at: Annotated[datetime.datetime, clickhouse_default("now()")]

class f_opt_saving(BaseModel):
    id: Annotated[int, "int32"]
    month_date: Annotated[datetime.date, ClickhouseSize(2)]
    opt_saving_usd: Optional[float] = None
    xls_file_path: Optional[str] = None
    create_at: Annotated[datetime.datetime, clickhouse_default("now()")]

class f_sku_discount(BaseModel):
    discount_pkey_hash: Annotated[int, "uint64"]
    product_description: str
    month_date: Annotated[datetime.date, ClickhouseSize(2)]
    rate: clickhouse_decimal(9, 4)
    is_new: bool

class f_sku_discount_dbt(BaseModel):
    discount_pkey_hash: Annotated[int, "uint64"]
    product_description: str
    month_date: Annotated[datetime.date, ClickhouseSize(2)]
    rate: clickhouse_decimal(9, 4)
    is_new: bool

class f_unused_cpp(BaseModel):
    month_date: Annotated[datetime.date, ClickhouseSize(2)]
    start_date: Annotated[datetime.date, ClickhouseSize(2)]
    end_date: Annotated[datetime.date, ClickhouseSize(2)]
    description: str
    sku_os: str
    meter_name: str
    meter_region: str
    cpp_monthly_cost_tax: Annotated[float, "float32"]
    official_monthly_cost_tax: Annotated[float, "float32"]
    cpp_count: Annotated[int, "int32"]
    vmlookupkey: str

class stg_azure_billing_detail(BaseModel):
    id: Annotated[Annotated[int, "uint64"], clickhouse_default("xxHash64(concat(instance_id, toString(date)))")]
    account_owner_id: Optional[str] = None
    account_name: Optional[str] = None
    service_administrator_id: Optional[str] = None
    subscription_id: Optional[Annotated[int, "int64"]] = None
    subscription_guid: Optional[str] = None
    subscription_name: Optional[str] = None
    date: Optional[Annotated[datetime.date, ClickhouseSize(2)]] = None
    month: Optional[Annotated[int, "int64"]] = None
    day: Optional[Annotated[int, "int64"]] = None
    year: Optional[Annotated[int, "int64"]] = None
    product: Optional[str] = None
    meter_id: Optional[str] = None
    meter_category: Optional[str] = None
    meter_sub_category: Optional[str] = None
    meter_region: Optional[str] = None
    meter_name: Optional[str] = None
    consumed_quantity: Optional[float] = None
    resource_rate: Optional[float] = None
    extended_cost: Optional[float] = None
    resource_location: Optional[str] = None
    consumed_service: Optional[str] = None
    instance_id: str
    service_info1: Optional[str] = None
    service_info2: Optional[str] = None
    additional_info: Any
    tags: Any
    store_service_identifier: Optional[str] = None
    department_name: Optional[str] = None
    cost_center: Optional[str] = None
    unit_of_measure: Optional[str] = None
    resource_group: Optional[str] = None
    extended_cost_tax: Optional[float] = None
    resource_tracking: Optional[str] = None
    resource_name: Optional[str] = None
    vm_name: Optional[str] = None
    latest_resource_type: Optional[str] = None
    newmonth: Optional[str] = None
    month_date: Annotated[datetime.date, ClickhouseSize(2)]
    sku: Optional[str] = None
    cmdb_mapped_application_service: Optional[str] = None
    ppm_billing_item: Optional[str] = None
    ppm_id_owner: Optional[str] = None
    ppm_io_cc: Optional[str] = None
    create_at: Annotated[datetime.datetime, clickhouse_default("now()")]

class stg_azure_retail_prices(BaseModel):
    id: Annotated[Annotated[int, "uint64"], clickhouse_default("xxHash64(concat(coalesce(toString(meter_id), ''), coalesce(toString(location), ''), coalesce(toString(effective_start_date), '')))")]
    currency_code: Optional[str] = None
    tier_minimum_units: Optional[float] = None
    retail_price: Optional[float] = None
    unit_price: Optional[float] = None
    arm_region_name: Optional[str] = None
    location: Optional[str] = None
    effective_start_date: Optional[datetime.datetime] = None
    meter_id: Optional[str] = None
    meter_name: Optional[str] = None
    product_id: Optional[str] = None
    sku_id: Optional[str] = None
    product_name: Optional[str] = None
    sku_name: Optional[str] = None
    service_name: Optional[str] = None
    service_family: Optional[str] = None
    unit_of_measure: Optional[str] = None
    type: Optional[str] = None
    is_primary_meter: Optional[Annotated[int, "uint8"]] = None
    arm_sku_name: Optional[str] = None
    reservation_term: Optional[str] = None
    created_at: Annotated[datetime.datetime, clickhouse_default("now()")]

class stg_cpp_detail(BaseModel):
    id: Annotated[int, "uint64"]
    identifier: str
    description: str
    sku_os: str
    meter_name: str
    meter_region: str
    start_date: Annotated[datetime.date, ClickhouseSize(2)]
    end_date: Annotated[datetime.date, ClickhouseSize(2)]
    batch: str
    cpp_monthly_cost_tax: Annotated[float, "float32"]
    official_monthly_cost_tax: Annotated[float, "float32"]
    cpp_count: Annotated[int, "int8"]
    VCPU: Annotated[float, "float32"]
    Memory: Annotated[float, "float32"]
    xls_file_path: str
    create_at: Annotated[datetime.datetime, clickhouse_default("now()")]

class stg_cpp_detail_dbt(BaseModel):
    id: Annotated[int, "uint64"]
    identifier: str
    description: str
    sku_os: str
    meter_name: str
    meter_region: str
    start_date: Annotated[datetime.date, ClickhouseSize(2)]
    end_date: Annotated[datetime.date, ClickhouseSize(2)]
    batch: str
    cpp_monthly_cost_tax: Annotated[float, "float32"]
    official_monthly_cost_tax: Annotated[float, "float32"]
    cpp_count: Annotated[int, "int8"]
    xls_file_path: str
    create_at: datetime.datetime

class stg_sku_discount_dbt(BaseModel):
    id: Annotated[int, "uint64"]
    sku_identifier: Optional[str] = None
    product_description: str
    rate: Annotated[float, "float32"]
    start_date: Annotated[datetime.date, ClickhouseSize(2)]
    end_date: Annotated[datetime.date, ClickhouseSize(2)]
    create_at: datetime.datetime

class stg_special_sku_discount(BaseModel):
    id: Annotated[int, "uint64"]
    sku_identifier: Optional[str] = None
    product_description: str
    rate: clickhouse_decimal(9, 4)
    start_date: Annotated[datetime.date, ClickhouseSize(2)]
    end_date: Annotated[datetime.date, ClickhouseSize(2)]
    create_at: Annotated[datetime.datetime, clickhouse_default("now()")]

d_application_tag_table = OlapTable[d_application_tag]("d_application_tag", OlapConfig(
    order_by_fields=["id"],
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

d_azure_retail_prices_table = OlapTable[d_azure_retail_prices]("d_azure_retail_prices", OlapConfig(
    order_by_fields=["meter_id", "location", "effective_start_date"],
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

d_exchange_rate_table = OlapTable[d_exchange_rate]("d_exchange_rate", OlapConfig(
    order_by_fields=["id"],
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

d_managed_disks_table = OlapTable[d_managed_disks]("d_managed_disks", OlapConfig(
    order_by_expression="tuple()",
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

d_monthly_budget_table = OlapTable[d_monthly_budget]("d_monthly_budget", OlapConfig(
    order_by_fields=["billing_item", "year"],
    partition_by="year",
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

dq_tagging_audit_table = OlapTable[dq_tagging_audit]("dq_tagging_audit", OlapConfig(
    order_by_fields=["audit_timestamp", "instance_id"],
    partition_by="toYYYYMM(audit_timestamp)",
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

f_azure_billing_detail_table = OlapTable[f_azure_billing_detail]("f_azure_billing_detail", OlapConfig(
    order_by_fields=["id", "resource_tracking_hash"],
    partition_by="toYYYYMM(month_date)",
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

f_azure_billing_resource_tracking_table = OlapTable[f_azure_billing_resource_tracking]("f_azure_billing_resource_tracking", OlapConfig(
    order_by_fields=["id", "resource_tracking_hash"],
    partition_by="tuple()",
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

f_budget_table = OlapTable[f_budget]("f_budget", OlapConfig(
    order_by_expression="tuple()",
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

f_budget_plan_table = OlapTable[f_budget_plan]("f_budget_plan", OlapConfig(
    order_by_fields=["month_date", "id"],
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

f_cpp_detail_table = OlapTable[f_cpp_detail]("f_cpp_detail", OlapConfig(
    order_by_fields=["cpp_pkey_hash"],
    engine=ReplacingMergeTreeEngine(ver="cpp_contract_date"),
    settings={"index_granularity": "8192"},
))

f_cpp_detail_dbt_table = OlapTable[f_cpp_detail_dbt]("f_cpp_detail_dbt", OlapConfig(
    order_by_expression="tuple()",
    engine=MergeTreeEngine(),
    settings={"replicated_deduplication_window": "0", "index_granularity": "8192"},
))

f_est_cumulative_saving_table = OlapTable[f_est_cumulative_saving]("f_est_cumulative_saving", OlapConfig(
    order_by_fields=["id"],
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

f_mars_bugdet_each_application_by_month_table = OlapTable[f_mars_bugdet_each_application_by_month]("f_mars_bugdet_each_application_by_month", OlapConfig(
    order_by_fields=["Month", "billing_item"],
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

f_mars_bugdet_each_application_by_week_table = OlapTable[f_mars_bugdet_each_application_by_week]("f_mars_bugdet_each_application_by_week", OlapConfig(
    order_by_fields=["Month", "billing_item"],
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

f_mars_bugdet_result_re_table = OlapTable[f_mars_bugdet_result_re]("f_mars_bugdet_result_re", OlapConfig(
    order_by_fields=["billing_item", "cost_center", "Month", "formula"],
    partition_by="toYYYYMM(update_date)",
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

f_opt_saving_table = OlapTable[f_opt_saving]("f_opt_saving", OlapConfig(
    order_by_fields=["id"],
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

f_sku_discount_table = OlapTable[f_sku_discount]("f_sku_discount", OlapConfig(
    order_by_fields=["discount_pkey_hash"],
    engine=ReplacingMergeTreeEngine(ver="discount_pkey_hash"),
    settings={"index_granularity": "8192"},
))

f_sku_discount_dbt_table = OlapTable[f_sku_discount_dbt]("f_sku_discount_dbt", OlapConfig(
    order_by_expression="tuple()",
    engine=MergeTreeEngine(),
    settings={"replicated_deduplication_window": "0", "index_granularity": "8192"},
))

f_unused_cpp_table = OlapTable[f_unused_cpp]("f_unused_cpp", OlapConfig(
    order_by_fields=["month_date", "vmlookupkey"],
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

stg_azure_billing_detail_table = OlapTable[stg_azure_billing_detail]("stg_azure_billing_detail", OlapConfig(
    order_by_fields=["id"],
    partition_by="toYYYYMM(month_date)",
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

stg_azure_retail_prices_table = OlapTable[stg_azure_retail_prices]("stg_azure_retail_prices", OlapConfig(
    order_by_fields=["id"],
    partition_by="toYYYYMM(created_at)",
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

stg_cpp_detail_table = OlapTable[stg_cpp_detail]("stg_cpp_detail", OlapConfig(
    order_by_fields=["start_date", "end_date"],
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))

stg_cpp_detail_dbt_table = OlapTable[stg_cpp_detail_dbt]("stg_cpp_detail_dbt", OlapConfig(
    order_by_expression="tuple()",
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192", "replicated_deduplication_window": "0"},
))

stg_sku_discount_dbt_table = OlapTable[stg_sku_discount_dbt]("stg_sku_discount_dbt", OlapConfig(
    order_by_expression="tuple()",
    engine=MergeTreeEngine(),
    settings={"replicated_deduplication_window": "0", "index_granularity": "8192"},
))

stg_special_sku_discount_table = OlapTable[stg_special_sku_discount]("stg_special_sku_discount", OlapConfig(
    order_by_fields=["id"],
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192"},
))


