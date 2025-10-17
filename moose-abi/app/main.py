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

class Level(Enum):
    INFO = "INFO"
    DEBUG = "DEBUG"
    ERROR = "ERROR"
    WARN = "WARN"

class Blob(BaseModel):
    id: Key[str]
    bucket_name: str
    file_path: str
    file_name: str
    file_size: Annotated[int, "int64"]
    permissions: list[str]
    content_type: Optional[str] = None
    ingested_at: str
    transform_timestamp: str

class Event(BaseModel):
    id: Key[str]
    event_name: str
    timestamp: str
    distinct_id: str
    session_id: Optional[str] = None
    project_id: str
    properties: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    transform_timestamp: str

class Log(BaseModel):
    id: Key[str]
    timestamp: str
    level: Level
    message: str
    source: Optional[str] = None
    trace_id: Optional[str] = None
    transform_timestamp: str

class Medical(BaseModel):
    id: Key[str]
    patient_name: str
    patient_age: str
    phone_number: str
    scheduled_appointment_date: str
    dental_procedure_name: str
    doctor: str
    transform_timestamp: str
    source_file_path: str

class UnstructuredData(BaseModel):
    id: Key[str]
    source_file_path: str
    extracted_data: Optional[str] = None
    processed_at: str
    processing_instructions: Optional[str] = None
    transform_timestamp: str

class moose_azure_billing(BaseModel):
    id: Key[str]
    account_owner_id: Optional[str] = None
    account_name: Optional[str] = None
    service_administrator_id: Optional[str] = None
    subscription_id: Optional[Annotated[int, "int64"]] = None
    subscription_guid: Optional[str] = None
    subscription_name: Optional[str] = None
    date: Optional[str] = None
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
    additional_info: Optional[str] = None
    tags: Optional[str] = None
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
    month_date: str
    sku: Optional[str] = None
    cmdb_mapped_application_service: Optional[str] = None
    ppm_billing_item: Optional[str] = None
    ppm_id_owner: Optional[str] = None
    ppm_io_cc: Optional[str] = None
    transform_timestamp: str

blob_table = OlapTable[Blob]("Blob", OlapConfig(
    order_by_fields=["id"],
    engine=MergeTreeEngine(),
    settings={"index_granularity_bytes": "10485760", "index_granularity": "8192", "enable_mixed_granularity_parts": "1"},
))

event_table = OlapTable[Event]("Event", OlapConfig(
    order_by_fields=["id"],
    engine=MergeTreeEngine(),
    settings={"enable_mixed_granularity_parts": "1", "index_granularity_bytes": "10485760", "index_granularity": "8192"},
))

log_table = OlapTable[Log]("Log", OlapConfig(
    order_by_fields=["id"],
    engine=MergeTreeEngine(),
    settings={"index_granularity_bytes": "10485760", "index_granularity": "8192", "enable_mixed_granularity_parts": "1"},
))

medical_table = OlapTable[Medical]("Medical", OlapConfig(
    order_by_fields=["id"],
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192", "enable_mixed_granularity_parts": "1", "index_granularity_bytes": "10485760"},
))

unstructured_data_table = OlapTable[UnstructuredData]("UnstructuredData", OlapConfig(
    order_by_fields=["id"],
    engine=MergeTreeEngine(),
    settings={"enable_mixed_granularity_parts": "1", "index_granularity": "8192", "index_granularity_bytes": "10485760"},
))

moose_azure_billing_table = OlapTable[moose_azure_billing]("moose_azure_billing", OlapConfig(
    order_by_fields=["id"],
    engine=MergeTreeEngine(),
    settings={"index_granularity": "8192", "enable_mixed_granularity_parts": "1", "index_granularity_bytes": "10485760"},
))


