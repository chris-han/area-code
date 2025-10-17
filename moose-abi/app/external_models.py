# AUTO-GENERATED FILE. DO NOT EDIT.
# This file will be replaced when you run `moose db pull`.

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


