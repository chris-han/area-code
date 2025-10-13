from decimal import Decimal
import time
from util import get_xxhash64_uint64, get_clickhouse_client, setup_logging
from clickhouse_connect.driver.client import Client
from data_quality_check import check_row_counts
# Standard library import

import json
import re
import math

from json.decoder import JSONDecodeError
import sys
import gc
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Generator, Tuple

# Third-party imports
import requests
import psutil
#import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from ck_mem_purge import purge_memory
import polars as pl

# ClickHouse connection details from batch_load_f_azure_billing_detail.sh

STAGE_TABLE_NAME="stg_azure_billing_detail"
F_BILLING_DETAIL_TABLE_NAME="f_azure_billing_detail"

# Retry configuration for monthly data fetching
MAX_MONTH_FETCH_RETRIES = 5
MONTH_FETCH_RETRY_DELAY = 30 # seconds
# DATA_RETENTION_MONTHS = 3 # Typical EA data availability



logger = setup_logging()



@contextmanager
def monitor_memory(task_name: str) -> Generator[None, None, None]:
    """Context manager to monitor memory usage"""
    start_mem = psutil.Process().memory_info().rss / 1024 / 1024
    try:
        yield
    finally:
        end_mem = psutil.Process().memory_info().rss / 1024 / 1024
        delta_mem = end_mem - start_mem
        logger.info(f"Memory delta for {task_name}: {delta_mem:.2f} MB")
        if delta_mem > 500:  # Alert if memory increase is more than 500MB
            logger.warning(f"High memory increase detected in {task_name}")

def prepare_dq_tagging_audit_table(client: Client, table_name: str = "dq_tagging_audit", schema: str = "dbo") -> None:
    """Truncates the dq_tagging_audit table if it exists, otherwise creates it."""
    full_table_name = f"{schema}.{table_name}"
    try:
        result = client.command(f"EXISTS TABLE {full_table_name}")
        if result == 1:
            logger.info(f"Table {full_table_name} exists. Truncating it now...")
            client.command(f"TRUNCATE TABLE {full_table_name}")
            logger.info(f"Table {full_table_name} truncated successfully.")
        else:
            logger.warning(f"Table {full_table_name} does not exist. Creating it now...")
            
            create_query = f"""
            CREATE TABLE IF NOT EXISTS {full_table_name}
            (
                audit_id UInt64 DEFAULT xxHash64(instance_id, toString(audit_timestamp)),
                instance_id String,
                last_segment Nullable(String),
                resource_group Nullable(String),
                subscription_guid Nullable(String),
                last_segment_match Nullable(String),
                resource_group_match Nullable(String),
                subscription_match Nullable(String),
                selected_match Nullable(String),
                meter_category Nullable(String),
                audit_timestamp DateTime DEFAULT now()
            )
            ENGINE = MergeTree()
            ORDER BY (audit_timestamp, instance_id)
            PARTITION BY toYYYYMM(audit_timestamp)
            """
            
            client.command(create_query)
            logger.info(f"Table {full_table_name} created successfully.")
    except Exception as e:
        logger.error(f"Error ensuring table {full_table_name} exists or truncated: {e}")
        raise

def insert_dq_tagging_audit_logs(client: Client, audit_df: pl.DataFrame, table_name: str = "dq_tagging_audit", schema: str = "dbo") -> None:
    """Inserts tagging audit logs into the specified table."""
    full_table_name = f"{schema}.{table_name}"
    if audit_df.is_empty():
        logger.info("No audit logs to insert.")
        return

    try:
        logger.info(f"Inserting {audit_df.height} audit logs into {full_table_name}...")
        # Convert polars DataFrame to pandas DataFrame and ensure columns order matches table columns (excluding audit_id and audit_timestamp)
        expected_columns = [
            "instance_id", "last_segment", "resource_group",
            "subscription_guid", "last_segment_match", "resource_group_match",
            "subscription_match", "selected_match", "meter_category"
        ]
        # Filter columns present in audit_df to avoid KeyError if subscription_guid missing
        columns_to_insert = [col for col in expected_columns if col in audit_df.columns]
        pandas_df = audit_df.select(columns_to_insert).to_pandas()
        client.insert_df(full_table_name, pandas_df)
        logger.info("Audit logs inserted successfully.")
    except Exception as e:
        logger.error(f"Failed to insert audit logs into {full_table_name}: {e}")
        raise

CREATE_QUERY_STG_TABLE = """
CREATE TABLE IF NOT EXISTS {full_table_name}
(
    id UInt64 DEFAULT xxHash64(instance_id || toString(date)),
    account_owner_id Nullable(String),
    account_name Nullable(String),
    service_administrator_id Nullable(String),
    subscription_id Nullable(Int64),
    subscription_guid Nullable(String),
    subscription_name Nullable(String),
    date Nullable(Date),
    month Nullable(Int64),
    day Nullable(Int64),
    year Nullable(Int64),
    product Nullable(String),
    meter_id Nullable(String),
    meter_category Nullable(String),
    meter_sub_category Nullable(String),
    meter_region Nullable(String),
    meter_name Nullable(String),
    consumed_quantity Nullable(Float64),
    resource_rate Nullable(Float64),
    extended_cost Nullable(Float64),
    resource_location Nullable(String),
    consumed_service Nullable(String),
    instance_id String,
    service_info1 Nullable(String),
    service_info2 Nullable(String),
    additional_info JSON,
    tags JSON,
    store_service_identifier Nullable(String),
    department_name Nullable(String),
    cost_center Nullable(String),
    unit_of_measure Nullable(String),
    resource_group Nullable(String),
    extended_cost_tax Nullable(Float64),
    resource_tracking Nullable(String),
    -- resource_tracking_hash Nullable(UInt64),
    resource_name Nullable(String),
    vm_name Nullable(String),
    latest_resource_type Nullable(String),
    newmonth Nullable(String),
    month_date Date,
    sku Nullable(String),
    -- vmlookupkey Nullable(String),
    -- vmlookupkey_hash Nullable(UInt64),
    -- product_description_hash Nullable(UInt64),
    cmdb_mapped_application_service Nullable(String),
    ppm_billing_item Nullable(String),
    ppm_id_owner Nullable(String),
    ppm_io_cc Nullable(String),
    create_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (id)
PARTITION BY toYYYYMM(month_date)
"""

def get_columns_from_create_query(query: str) -> List[str]:
    """Parses column names from a CREATE TABLE query string."""
    # Isolate query part before ENGINE clause
    try:
        engine_pos = query.upper().index('ENGINE')
        query_before_engine = query[:engine_pos]
    except ValueError:
        query_before_engine = query

    # Find column definitions within parentheses
    start_pos = query_before_engine.find('(')
    end_pos = query_before_engine.rfind(')')

    if start_pos == -1 or end_pos == -1 or start_pos >= end_pos:
        return []

    columns_str = query_before_engine[start_pos + 1:end_pos]
    
    columns = []
    for line in columns_str.split(','):
        line = line.strip()
        if line and not line.startswith('--'):
            columns.append(line.split()[0].replace('`', ''))
    return columns

def create_stg_table(client: Client, table_name: str = STAGE_TABLE_NAME, schema: str = "dbo") -> None:
    """Checks if the table exists and creates it programmatically if it doesn't."""
    full_table_name = f"{schema}.{table_name}"
    try:
        result = client.command(f"EXISTS TABLE {full_table_name}")
        if result == 0:
            logger.warning(f"Table {full_table_name} does not exist. Creating it now...")
            
            create_query = CREATE_QUERY_STG_TABLE.format(full_table_name=full_table_name)
            
            client.command(create_query)
            logger.info(f"Table {full_table_name} created successfully.")
        else:
            logger.info(f"Table {full_table_name} already exists.")
    except Exception as e:
        logger.error(f"Error ensuring table {full_table_name} exists: {e}")
        raise

def truncate_target_table(client: Client, table_name: str = STAGE_TABLE_NAME, schema: str = "dbo") -> None:
    """Truncates the target table."""
    full_table_name = f"{schema}.{table_name}"
    logger.info(f"Truncating data from table {full_table_name}...")
    try:
        
        sql_query = f"Truncate TABLE {full_table_name}"
        client.command(sql_query)
        logger.info(f"Data from table {table_name} cleared successfully.")
    except Exception as e:
        logger.error(f"Failed to truncate data from table {table_name}: {e}")
        raise

def drop_target_table(client: Client, table_name: str = STAGE_TABLE_NAME, schema: str = "dbo") -> None:
    """Drops the target table."""
    full_table_name = f"{schema}.{table_name}"
    logger.info(f"Dropping table {full_table_name}...")
    try:
        
        client.command(f"DROP TABLE IF EXISTS {full_table_name}")
        logger.info(f"Table {full_table_name} dropped successfully.")
    except Exception as e:
        logger.error(f"Failed to drop table {full_table_name}: {e}")
        raise

def fetch_azure_data(billing_date: datetime, azure_config: Dict[str, str], api_url: str = None) -> tuple[pl.DataFrame, Optional[str]]:
    with monitor_memory("fetch_azure_data"):
        month = billing_date.strftime("%Y-%m")
        
        azure_data = pl.DataFrame()
        next_page_url = None
        
        if api_url:
            url = api_url
        else:
            url = f"https://ea.azure.cn/rest/{azure_config['azure_enrollment_number']}/usage-report/paginatedV3?month={month}&pageindex=0&fmt=json"
            
        headers = {
            'Authorization': f'bearer {azure_config["azure_api_key"]}'
        }
        
        try:
            for attempt in range(3):
                response = requests.get(url=url, headers=headers, timeout=800)
                logger.info(f"API request status code: {response.status_code}")

                if response.status_code == 200:
                    break
                elif response.status_code == 503:
                    logger.warning(f"Service unavailable, retrying... (Attempt {attempt + 1})")
                    time.sleep(5)
                else:
                    error_msg = f"Failed to fetch data: {response.text}"
                    logger.error(error_msg)
                    return pl.DataFrame(), None

            if response.status_code != 200:
                error_msg = f"Failed to fetch data after 3 attempts: {response.text}"
                logger.error(error_msg)
                return pl.DataFrame(), None
                
            response.encoding = 'utf-8-sig'
            
            try:
                data = response.json()
                next_page_url = data.get('nextLink')
                
                content = data.get('content', [])
                if not content:
                    logger.warning(f"No content in response for page {api_url}")
                    return pl.DataFrame(), None
                    
                # Convert content list of dicts to polars DataFrame
                azure_data = pl.DataFrame(content)

                # Debug: Log the first few rows and columns of azure_data to check 'Date' column presence and format
                # if not azure_data.is_empty() and 'Date' in azure_data.columns:
                #     logger.info(f"Debug: azure_data['Date'] sample values: {azure_data['Date'].head(5).to_list()}")
                # else:
                #     logger.warning("Debug: 'Date' column missing or azure_data is empty after fetching.")

                del response, content, data
                gc.collect()
                
                return azure_data, next_page_url
                
            except JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {e}")
                return pl.DataFrame(), None
            
        except Exception as e:
            logger.error(f"Error fetching Azure data: {e}")
            raise

def to_snake_case(column_name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', column_name).lower()
   
def get_resource_tracking_patterns(app_tag_tabel_name: str) ->list[tuple[str, str, int]]:
    """Get a list of resource tracking from application_tag table"""
    table_name = app_tag_tabel_name
    schema_name = 'dbo' # ClickHouse typically doesn't use 'dbo' schema, but keeping for consistency with other functions
    full_table_name = f"{schema_name}.{table_name}"
    logger.info(f"开始从表 {full_table_name} 加载资源跟踪模式...")

    try:
        client = get_clickhouse_client() # Obtain ClickHouse client
        # Check if table exists
        table_exists_result = client.command(f"EXISTS TABLE {full_table_name}")
        if table_exists_result == 1:
            # ClickHouse SELECT query
            # The result_rows will be a list of lists/tuples, e.g., [['pattern1', 1]]
            tag_rows = client.query(f'SELECT resource_tracking,id FROM {full_table_name}').result_rows
            # Store the compiled pattern, the original uppercase string and the id
            # We escape the strings to ensure literal matching. Polars' `str.contains`
            # will use the Rust regex engine internally.
            tag_patterns = [(re.escape(key[0].upper()), key[0].upper(), key[1]) for key in tag_rows]
            logger.info(f"加载了 {len(tag_patterns)} 条标签匹配规则")
            return tag_patterns
        else:
            logger.warning(f"表 {full_table_name} 不存在。")
            return []
    except Exception as e:
        logger.error(f"从表 {full_table_name} 加载失败: {str(e)}")
        raise

def get_resource_tracking_str_vectorized(df: pl.DataFrame, tag_patterns: List[Tuple[str, str, int]]) -> Tuple[pl.Series, pl.DataFrame]:
    """
    Optimized approach for resource tracking string vectorization.
    This version uses `polars.coalesce` to build expressions more efficiently,
    corrects the fallback logic, and returns audit logs for multiple matches.
    """
    if df.is_empty():
        return pl.Series([], dtype=pl.Utf8), pl.DataFrame()

    last_segment = pl.col('instance_id').str.split('/').list.last().str.to_uppercase()
    
    if not tag_patterns:
        return df.select(last_segment.alias("resource_tracking")).to_series(), pl.DataFrame()

    # Sort patterns by id to prioritize matches with smaller ids
    tag_patterns.sort(key=lambda x: x[2])

    # Uppercase the patterns and values internally to ensure case-insensitive matching
    patterns = [(p.upper(), v.upper()) for p, v, _ in tag_patterns]

    def get_match_expr(col_expr: pl.Expr) -> Tuple[pl.Expr, pl.Expr]:
        value_exprs = [pl.when(col_expr.str.contains(p, literal=False)).then(pl.lit(v)) for p, v in patterns]
        order_exprs = [pl.when(col_expr.str.contains(p, literal=False)).then(pl.lit(i)) for i, (p, _) in enumerate(patterns)]
        return pl.coalesce(value_exprs), pl.coalesce(order_exprs).fill_null(len(patterns))

    try:
        last_segment_val, last_segment_order = get_match_expr(last_segment)
        
        resource_group_val, resource_group_order = (
            get_match_expr(pl.col('resource_group').str.to_uppercase())
            if 'resource_group' in df.columns
            else (pl.lit(None, dtype=pl.Utf8), pl.lit(len(patterns), dtype=pl.Int32))
        )
        
        subscription_val, subscription_order = (
            get_match_expr(pl.col('subscription_guid').str.to_uppercase())
            if 'subscription_guid' in df.columns
            else (pl.lit(None, dtype=pl.Utf8), pl.lit(len(patterns), dtype=pl.Int32))
        )

        best_order = pl.min_horizontal(last_segment_order, resource_group_order, subscription_order)
        
        result_expr = pl.coalesce([
            pl.when(best_order.eq(last_segment_order)).then(last_segment_val),
            pl.when(best_order.eq(resource_group_order)).then(resource_group_val),
            pl.when(best_order.eq(subscription_order)).then(subscription_val),
            last_segment
        ])

        temp_df = df.with_columns(
            last_segment=last_segment,
            last_segment_match=last_segment_val,
            resource_group_match=resource_group_val,
            subscription_match=subscription_val,
            selected_match=result_expr
        )

        if 'subscription_guid' in df.columns:
            temp_df = temp_df.with_columns(
                pl.col('subscription_guid').str.to_uppercase().alias('subscription_guid')
            )

        audit_cols = [
            "instance_id", "last_segment", "resource_group",
            "last_segment_match", "resource_group_match", "subscription_match", "selected_match"
        ]
        if 'subscription_guid' in df.columns:
            audit_cols.insert(3, "subscription_guid")
        if 'meter_category' in df.columns:
            audit_cols.append("meter_category")

        audit_df = temp_df.filter(
            pl.sum_horizontal(
                pl.col("last_segment_match").is_not_null(),
                pl.col("resource_group_match").is_not_null(),
                pl.col("subscription_match").is_not_null()
            ) > 1
        ).select(audit_cols)

        result_series = temp_df.select(pl.col("selected_match").alias("resource_tracking")).to_series()
        
        return result_series.rename(""), audit_df

    except Exception as e:
        logger.error(f"Failed to get resource_tracking: {e}")
        raise



def clean_json_string(s: Any) -> Dict[str, Any]:
    """Cleans and converts a string to a list containing a JSON object (Python dictionary).
    Returns [None] if the input is null-like, or the string is empty or '{}'.
    """
    # If input is None or NaN, return None
    if s is None or (isinstance(s, float) and math.isnan(s)):
        return None
    
    if isinstance(s, str):
        s = s.strip()
        # If string is empty or represents an empty JSON object, return None
        if s == '':
            return None
        elif s == '{}': # Added '[]' for empty list case
            return None
        elif s == '[]':
            return None
        try:
            parsed_json = json.loads(s)
            return parsed_json

        except json.JSONDecodeError:
            # If not valid JSON, raise the error as per requirement
            raise ValueError(f"Invalid JSON string: '{s}'")
    # For other types like numbers, bools, etc., raise an error
    raise TypeError(f"Unsupported type for JSON cleaning: {type(s)}")

def transform_data(raw_data: pl.DataFrame, tag_patterns: List[tuple]) -> Tuple[pl.DataFrame, pl.DataFrame]:
    with monitor_memory("transform_data"):
        total_count = raw_data.height
        logger.info(f"开始转换 {total_count} 条原始记录...")

        if raw_data.is_empty():
            logger.warning("Raw data is empty, returning empty DataFrame")
            return pl.DataFrame(), pl.DataFrame()

        df = raw_data
        audit_df = pl.DataFrame()

        # Filter out rows where 'instance_id' is null or empty, as it's a non-nullable column in ClickHouse
        initial_rows = df.height
        if 'instance_id' in df.columns:
            df = df.filter(
                (pl.col('instance_id').is_not_null()) & (pl.col('instance_id') != '')
            )
            if df.height < initial_rows:
                logger.error(f"Filtered out {initial_rows - df.height} rows due to null or empty 'instance_id'.")

        if 'date' in df.columns and df.schema.get('date') == pl.Date:
            df = df.with_columns([
                pl.col('date').dt.strftime("%b %Y").alias('newmonth'),
                pl.col('date').dt.truncate('1mo').fill_null(date(1970, 1, 1)).alias('month_date')
            ])
        else:
            df = df.with_columns([
                pl.lit(None, dtype=pl.Utf8).alias('newmonth'),
                pl.lit(date(1970, 1, 1)).alias('month_date')
            ])

        if 'tags' in df.columns:
            df = df.with_columns(
                pl.col('tags').map_elements(clean_json_string, return_dtype=pl.Object).alias('tags')
            )
            df = df.with_columns([
                pl.col('tags').map_elements(lambda x: x.get('app') if isinstance(x, dict) else None, return_dtype=pl.Utf8).alias('cmdb_mapped_application_service'),
                pl.col('tags').map_elements(lambda x: x.get('ppm_billing_item') if isinstance(x, dict) else None, return_dtype=pl.Utf8).alias('ppm_billing_item'),
                pl.col('tags').map_elements(lambda x: x.get('ppm_billing_owner') if isinstance(x, dict) else None, return_dtype=pl.Utf8).alias('ppm_id_owner'),
                pl.col('tags').map_elements(lambda x: x.get('ppm_io_cc') if isinstance(x, dict) else None, return_dtype=pl.Utf8).alias('ppm_io_cc'),
            ])


        if 'additional_info' in df.columns:
            df = df.with_columns(
                pl.col('additional_info').map_elements(clean_json_string, return_dtype=pl.Object).alias('additional_info')
            )

        float_columns = ['consumed_quantity', 'resource_rate', 'extended_cost']
        for col in float_columns:
            if col in df.columns:
                df = df.with_columns(
                    pl.col(col).cast(pl.Float64).alias(col)
                )

        if 'extended_cost' in df.columns:
            df = df.with_columns(
                (pl.col('extended_cost') * 1.06).alias('extended_cost_tax')
            )

        if 'meter_category' in df.columns and 'product' in df.columns:
            df = df.with_columns([
                pl.lit(None, dtype=pl.Utf8).alias('sku'),
                pl.lit(None, dtype=pl.Utf8).alias('latest_resource_type'),
                pl.lit(None, dtype=pl.Utf8).alias('resource_name')
            ])

            # SKU and latest_resource_type logic
            df = df.with_columns(
                pl.when(pl.col('meter_category') == 'Virtual Machines')
                .then(
                    pl.when(pl.col('product').str.contains('(?i)Windows')).then(pl.lit('Windows'))
                    .otherwise(pl.lit('Linux'))
                )
                .when((pl.col('meter_name') == '100 DWUs') & (pl.col('meter_category') != 'Virtual Machines'))
                .then(pl.lit('SQL'))
                .otherwise(pl.col('sku'))
                .alias('sku')
            )

            df = df.with_columns(
                pl.when(pl.col('sku').is_in(['Windows', 'Linux']))
                .then(pl.col('sku') + '-' + pl.col('meter_name'))
                .otherwise(pl.col('latest_resource_type'))
                .alias('latest_resource_type')
            )

            # resource_name logic
            if 'instance_id' in df.columns and 'additional_info' in df.columns:
                vm_name_mask = (
                    (pl.col('meter_category') == 'Virtual Machines') &
                    (pl.col('additional_info').is_not_null()) &
                    (pl.col('additional_info').map_elements(
                        lambda x: isinstance(x, dict) and x.get('VMName') is not None,
                        return_dtype=pl.Boolean
                    ).fill_null(False)) &
                    (pl.col('instance_id').str.contains('(?i)aks-'))
                )
                df = df.with_columns(
                    pl.when(vm_name_mask)
                    .then(pl.col('additional_info').map_elements(lambda x: x.get('VMName'), return_dtype=pl.Utf8))
                    .otherwise(pl.col('resource_name'))
                    .alias('resource_name')
                )

            other_mask = (
                (pl.col('resource_name').is_null()) &
                (pl.col('instance_id').is_not_null())
            )
            # For rows where resource_name is null and instance_id not null, set resource_name = last segment of instance_id
            def get_last_segment(x):
                if isinstance(x, str) and '/' in x:
                    return x.split('/')[-1]
                return x
            df = df.with_columns(
                pl.when(other_mask)
                .then(pl.col('instance_id').map_elements(get_last_segment, return_dtype=pl.Utf8))
                .otherwise(pl.col('resource_name'))
                .alias('resource_name')
            )

            df = df.with_columns(pl.lit(None).alias('vm_name'))
            vm_name_mask = (
                (pl.col('meter_category') == 'Virtual Machines') &
                (pl.col('resource_name').is_not_null())
            )
            df = df.with_columns(
                pl.when(vm_name_mask)
                .then(pl.col('resource_name'))
                .otherwise(pl.col('vm_name'))
                .alias('vm_name')
            )



        if 'instance_id' in df.columns:
            logger.info("Starting get_resource_tracking_str_vectorized...")
            logger.info(f"DataFrame size: {df.height} rows, {len(df.columns)} columns")
            logger.info(f"Number of tag patterns: {len(tag_patterns)}")
            start_time = time.time()
            try:
                chunk_size = 10000
                results = []
                audits = []
                for start_idx in range(0, df.height, chunk_size):
                    end_idx = min(start_idx + chunk_size, df.height)
                    df_chunk = df.slice(start_idx, end_idx - start_idx)
                    pl_series_chunk, audit_df_chunk = get_resource_tracking_str_vectorized(df_chunk, tag_patterns)
                    results.append(pl_series_chunk)
                    audits.append(audit_df_chunk)
                pl_series = pl.concat(results)
                audit_df = pl.concat(audits) if audits else pl.DataFrame()
            except Exception as e:
                logger.error(f"Exception in get_resource_tracking_str_vectorized: {e}", exc_info=True)
                raise
            df = df.with_columns(
                pl_series.alias('resource_tracking')
            )
            end_time = time.time()
            logger.info(f"Finished get_resource_tracking_str_vectorized in {end_time - start_time:.2f} seconds.")



        for col in ['service_info1', 'service_info2']:
            if col in df.columns:
                df = df.with_columns(
                    pl.col(col).map_elements(lambda x: None if isinstance(x, str) and x.strip() == '' else x, return_dtype=pl.Utf8).alias(col)
                )

        gc.collect()
        return df, audit_df

def save_to_database(client: Client, records_df: pl.DataFrame, insert_columns: List[str], table_name: str = STAGE_TABLE_NAME, schema: str = "dbo") -> None:
    """
    Save transformed records to ClickHouse database using native Arrow format.

    Args:
        client (Client): ClickHouse client instance.
        records_df (pl.DataFrame): Polars DataFrame containing records to insert.
        table_name (str): Target table name.
        schema (str): Database schema name.

    Raises:
        Exception: Propagates exceptions after logging.
    """
    full_table_name = f"{schema}.{table_name}"

    if records_df.is_empty():
        logger.warning("No valid data to load into %s", full_table_name)
        return

    try:
        # Align DataFrame columns with table columns
        # aligned_df = records_df.select(insert_columns)
        
        # logger.info(f"Inserting {aligned_df.height} records into {full_table_name}...")
        
        # Convert polars DataFrame to pandas DataFrame with columns explicitly set
        logger.info("Convert polars DataFrame to pandas")
        records_to_insert = records_df.select(insert_columns).to_pandas()
        
        logger.info("Start inserting...")
        insert_start = time.perf_counter()
        # client.insert_arrow(full_table_name, records_to_insert)
        client.insert_df(full_table_name, records_to_insert)
        insert_end = time.perf_counter()

        elapsed = insert_end - insert_start
        logger.info(
            "Inserted %d records into %s in %.2f seconds.",
            len(records_to_insert),
            full_table_name,
            elapsed,
        )
        
    except Exception as e:
        logger.exception("Failed to insert data into %s: %s", full_table_name, e)
        
        # Added detailed error logging for debugging
        try:
            logger.error(f"DataFrame columns: {records_df.columns}")
            logger.error(f"Table columns: {insert_columns}")
        except Exception as desc_e:
            logger.error(f"Could not describe table {full_table_name}: {desc_e}")
            
        raise


def run_pipeline(prepare_stage_table: str = "drop", table_name: str = STAGE_TABLE_NAME, start_date: date = None, end_date: date = None) -> pl.DataFrame:
    """
    Complete ETL process for Azure EA data to ClickHouse.
    Returns a DataFrame with all audit logs.
    """
    all_audit_logs = []
    try:
        month_list = []
        current_date = start_date
        while current_date <= end_date:
            month_list.append(current_date.replace(day=1))
            current_date += relativedelta(months=1)
                
        client = get_clickhouse_client()

        # Fetch resource tracking patterns once before the main loop
        logger.info("Fetching resource tracking patterns...")
        resource_tracking_patterns = get_resource_tracking_patterns('d_application_tag')
        logger.info(f"Loaded {len(resource_tracking_patterns)} resource tracking patterns.")

        AZURE_CONFIG = {
            "azure_enrollment_number": "V5702303S0121",
            "azure_api_key": "eyJhbGciOiJSUzI1NiIsImtpZCI6IkY0QzA3NjhGOEJCOURBMjRGQzY5QUMzQjc5NTZDMDNDRjMxRjc3ODIiLCJ0eXAiOiJKV1QifQ.eyJFbnJvbGxtZW50TnVtYmVyIjoiVjU3MDIzMDNTMDEyMSIsIklkIjoiMzEwZTM1YmYtYmU2Yi00MDQwLThjYzUtYzY2YmY2N2RhZmI2IiwiUmVwb3J0VmlldyI6IlBhcnRuZXIiLCJQYXJ0bmVySWQiOiI1MDEwIiwiRGVwYXJ0bWVudElkIjoiIiwiQWNjb3VudElkIjoiIiwibmJmIjoxNzUxOTY5MzE1LCJleHAiOjE3Njc4NjY5MTUsImlhdCI6MTc1MTk2OTMxNSwiaXNzIjoiZWEubWljcm9zb2Z0YXp1cmUuY29tIiwiYXVkIjoiY2xpZW50LmVhLm1pY3Jvc29mdGF6dXJlLmNvbSJ9.KCooPKpK4zskNxCldzDK5A3oX-Z3Y1Jicl8SyVeixHT71cfRa2SgW3UZoT0g0c3vqtxtCQ-wn4vfkeBNuhSKwUNn76Eiqw-SU9hEXWw0ez62u-CraEfa15Wi5woUVKkZCSkkxqyGGCFX0bLXvSg5bPvRd0ENXGi0zfMG-DCh63GUVRhVvcX3kPACz5KkHZtxLvOGP9Q2hcS0HVFOt-d3DpL2x_ut6p0JBQ4ECWh_Lj4ph5FE0GtFXzsN2TGRW9zRM7JFI8WKgDlmLGQeH9e0HEU1AUj-5y4UwgShosYeQueShoHS3ejWsNdBrb83B7VD8kQp5mYs9ATZGuH7YO-Ucw"
        }
        
        # Validate API token expiration
        import jwt
        try:
            decoded = jwt.decode(AZURE_CONFIG["azure_api_key"], options={"verify_signature": False})
            exp_time = datetime.fromtimestamp(decoded["exp"])
            logger.info(f"API token expires at: {exp_time}")
            if datetime.now() > exp_time:
                logger.error("API token has expired!")
        except Exception as e:
            logger.error(f"Failed to decode API token: {e}")

        logger.info(f"Processing dates: {[d.strftime('%Y-%m') for d in month_list]}")
        
        if prepare_stage_table == "delete":
            logger.info("Step 1: Deleting target table")
            truncate_target_table(client, table_name=table_name)
            create_stg_table(client, table_name=table_name) # Ensure exists after truncate
        elif prepare_stage_table == "drop":
            logger.info("Step 1: Dropping target table")
            drop_target_table(client, table_name=table_name)
            create_stg_table(client, table_name=table_name) # Ensure exists after drop
        else:
            create_stg_table(client, table_name=table_name) # Ensure exists if no preparation

        insert_columns = get_columns_from_create_query(CREATE_QUERY_STG_TABLE)
        columns_to_exclude = {'id', 'create_at'}
        insert_columns = [col for col in insert_columns if col not in columns_to_exclude]
        total_months = len(month_list)
        for date_index, current_date in enumerate(month_list):
            month_str = current_date.strftime("%Y-%m")
            logger.info(f"-------------{month_str}-------------")
            logger.info(f"Step 2: Processing month {date_index+1}/{total_months}: {month_str}")
            
            month_data_fetched = False
            for attempt_month in range(1, MAX_MONTH_FETCH_RETRIES + 1):
                try:
                    page_number = 1
                    api_url = None
                    all_raw_data = []
                    response = None  # Ensure response is always defined
                    
                    while True:
                        logger.info(f"Step 2a: Fetching data for {month_str} - Page {page_number} (Month Attempt {attempt_month}/{MAX_MONTH_FETCH_RETRIES})")
                        raw_data, next_link = fetch_azure_data(current_date, AZURE_CONFIG, api_url=api_url)

                        if raw_data.is_empty():
                            status_msg = f"Status: {response.status_code}" if response is not None else "No response received"
                            logger.warning(f"Month {month_str}, Page {page_number}: No data retrieved from API. {status_msg}")
                            
                            if response is not None:
                                logger.debug(f"API Response: {response.text[:500]}...")  # Log first 500 chars of response
                                error_msg = f"No data retrieved for month: {month_str}. API Status: {response.status_code}"
                            else:
                                error_msg = f"No data retrieved for month: {month_str}. No API response received"
                                
                            if page_number == 1: # If first page is empty, this attempt for the month failed
                                logger.warning(f"Month {month_str}: First page empty. Retrying month fetch in {MONTH_FETCH_RETRY_DELAY} seconds...")
                                time.sleep(MONTH_FETCH_RETRY_DELAY)
                                all_raw_data = [] # Clear any partial data from this month attempt
                                break # Break from pagination loop to retry month
                            else: # If subsequent page is empty, just break pagination
                                logger.info(f"Month {month_str}, Page {page_number}: Subsequent page empty, stopping pagination for this month attempt.")
                                break
                        
                        if start_date and end_date and not raw_data.is_empty() and 'Date' in raw_data.columns:
                            # Convert 'Date' column to polars Date type for comparison
                            raw_data = raw_data.with_columns(
                                pl.col('Date').str.strptime(pl.Date, "%m/%d/%Y", strict=False).alias('Date')
                            )
                            # Filter records
                            initial_count = raw_data.height
                            # Add debug logs for filtering
                            # logger.info(f"Debug: start_date={start_date}, end_date={end_date}")
                            # if not raw_data.is_empty() and 'Date' in raw_data.columns:
                            #     logger.info(f"Debug: raw_data['Date'] min={raw_data['Date'].min()}, max={raw_data['Date'].max()}")
                            #     logger.info(f"Debug: raw_data['Date'] sample values: {raw_data['Date'].head(5).to_list()}")
                            raw_data = raw_data.filter(
                                (pl.col('Date') >= start_date) & (pl.col('Date') <= end_date)
                            )
                            filtered_count = raw_data.height
                            if initial_count > filtered_count:
                                logger.info(f"Filtered {initial_count - filtered_count} records from current page due to date range ({start_date} to {end_date}).")
                            
                            logger.info(f"{filtered_count} records will inserted date range ({start_date} to {end_date}).")
                        
                        all_raw_data.append(raw_data)
                        
                        if not raw_data.is_empty() and 'Date' in raw_data.columns and end_date:
                            # Convert 'date' column to datetime objects for comparison
                            # raw_data_dates = pd.to_datetime(raw_data['Date'], errors='coerce')
                            # max_date_in_raw_data = raw_data_dates.max().date()
                            
                            max_date_in_raw_data = raw_data.select(pl.col('Date').max()).item()
                            if max_date_in_raw_data > end_date:
                                logger.warning(f"Detected data beyond the last date. Breaking pagination loop.")
                                month_data_fetched = True # Mark as fetched to exit month retry loop
                                break # Break from pagination loop
                        
                        if next_link:
                            api_url = next_link
                            page_number += 1
                        else:
                            logger.info(f"Completed fetching all pages for month {month_str} on attempt {attempt_month}")
                            month_data_fetched = True
                            break # Break from pagination loop
                    
                    if month_data_fetched:
                        break # Break from month retry loop if data was successfully fetched
                
                except Exception as e:
                    logger.error(f"Error during month {month_str} fetch attempt {attempt_month}: {e}", exc_info=True)
                    if attempt_month < MAX_MONTH_FETCH_RETRIES:
                        logger.warning(f"Retrying month fetch in {MONTH_FETCH_RETRY_DELAY} seconds...")
                        time.sleep(MONTH_FETCH_RETRY_DELAY)
                    else:
                        raise # Re-raise if all attempts fail
            
            if not month_data_fetched:
                final_error_msg = f"Failed to retrieve any data for month: {month_str} after {MAX_MONTH_FETCH_RETRIES} attempts."
                logger.error(final_error_msg)
                from datetime import datetime
                current_month_str = datetime.now().strftime("%Y-%m")
                if month_str == current_month_str:
                    logger.warning(f"Current month {month_str} has no data yet. Skipping error raise.")
                else:
                    raise ValueError(final_error_msg)

            if all_raw_data:
                raw_data = pl.concat(all_raw_data)
            else:
                raw_data = pl.DataFrame()

            if not raw_data.is_empty():
                raw_data.columns = [to_snake_case(col) for col in raw_data.columns]
                
                initial_raw_data_len = raw_data.height
                logger.info(f"Step 2b: Transforming {initial_raw_data_len} records for {month_str}")
                transformed_records, audit_logs = transform_data(raw_data, resource_tracking_patterns)
                if not audit_logs.is_empty():
                    all_audit_logs.append(audit_logs)
                del raw_data
                gc.collect()

                if not transformed_records.is_empty():
                    transformed_records_len = transformed_records.height
                    if transformed_records_len < initial_raw_data_len:
                        logger.warning(f"Month {month_str}: Transformed records count ({transformed_records_len}) is less than raw data count ({initial_raw_data_len}).")
                    logger.info(f"Step 2c: Loading {transformed_records_len} records to database for {month_str}")
                    # Convert polars DataFrame to pandas DataFrame before saving
                    save_to_database(client, transformed_records, insert_columns, table_name=STAGE_TABLE_NAME)
                    del transformed_records
                    gc.collect()
                else:
                    logger.warning(f"Month {month_str}: No valid records after transformation.")
            else:
                logger.warning(f"No data to process for month {month_str}")
            
            logger.info(f"Step 2: Completed processing month {month_str}")
        
        logger.info("Azure EA data pipeline to ClickHouse completed successfully")
        
        if all_audit_logs:
            return pl.concat(all_audit_logs)
        return pl.DataFrame()

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        raise

def describe_table_schema(client: Client, table_name: str = STAGE_TABLE_NAME, schema: str = "dbo") -> None:
    full_table_name = f"{schema}.{table_name}"
    try:
        result = client.query(f"DESCRIBE TABLE {full_table_name}").result_rows
        logger.info(f"Schema for {full_table_name}:")
        for row in result:
            logger.info(f"  {row[0]}: {row[1]}")
    except Exception as e:
        logger.error(f"Error describing table {full_table_name}: {e}")
        raise

def exist_f_azure_billing_detail(client: Client, table_name: str = F_BILLING_DETAIL_TABLE_NAME, schema: str = "dbo") -> bool:
    """Checks if the f_azure_billing_detail table exists."""
    
    full_table_name = f"{schema}.{table_name}"
    try:
        result = client.command(f"EXISTS TABLE {full_table_name}")
        if result == 1:
            logger.info(f"Table {full_table_name} exists.")
            return True
        else:
            logger.warning(f"Table {full_table_name} does not exist.")
            return False
    except Exception as e:
        logger.error(f"Error checking if table {full_table_name} exists: {e}")
        raise

def get_last_date_f_billing_detail(client: Client, table_name: str = F_BILLING_DETAIL_TABLE_NAME, schema: str = "dbo") -> Optional[date]:
    """
    Retrieves the maximum 'date' from the specified ClickHouse table.

    Args:
        client: The ClickHouse client instance.
        table_name: The name of the table to query. Defaults to "f_azure_billing_detail".
        schema: The schema of the table. Defaults to "dbo".

    Returns:
        A datetime.date object representing the maximum date in the table,
        or None if the table does not exist or is empty.
    """
    full_table_name = f"{schema}.{table_name}"
    try:
        # Check if the table exists first to provide more specific logging
        table_exists_result = client.command(f"EXISTS TABLE {full_table_name}")
        if table_exists_result == 0:
            logger.warning(f"Table {full_table_name} does not exist. Cannot retrieve max date.")
            return None

        # If table exists, proceed to get max date
        result_str = client.command(f"SELECT MAX(date) FROM {full_table_name}")

        if result_str is not None and result_str.strip() != '1970-01-01':
            # ClickHouse returns date as 'YYYY-MM-DD' string for MAX(date)
            max_date = datetime.strptime(result_str.strip(), '%Y-%m-%d').date()
            logger.info(f"Successfully retrieved max date '{max_date}' from table {full_table_name}.")
            return max_date
        else:
            logger.info(f"Table {full_table_name} exists, but no data or max date found (table might be empty).")
            return None
    except Exception as e:
        logger.error(f"Error retrieving max date from table {full_table_name}: {e}", exc_info=True)
        raise

def create_f_azure_billing_detail():
    """
    Populates the f_azure_billing_detail table in ClickHouse by executing the SQL from ck_create_f_azure_billing_detail.sql.
    Each SQL statement is executed separately.
    """
    try:
        logger.info("Step 1: Initialize ClickHouse client for f_azure_billing_detail population")
        step_start = time.time()
        client = get_clickhouse_client()
        step_end = time.time()
        logger.info(f"Step 1 finished in {step_end - step_start:.2f} seconds")

        logger.info("Step 2: Reading SQL from ck_create_f_azure_billing_detail.sql")
        step_start = time.time()
        with open('clickhouse_sql/ck_create_f_azure_billing_detail.sql', 'r') as f:
            sql_script = f.read()
        step_end = time.time()
        logger.info(f"Step 2 finished in {step_end - step_start:.2f} seconds")

        logger.info("Step 3: Executing SQL commands to create f_azure_billing_detail")
        step_start = time.time()
        # Split SQL script into individual commands
        # Remove comments before splitting
        cleaned_sql_script = re.sub(r'/\*.*?\*/', '', sql_script, flags=re.DOTALL) # Remove multi-line comments
        cleaned_sql_script = re.sub(r'--.*$', '', cleaned_sql_script, flags=re.MULTILINE) # Remove single-line comments
        sql_commands = [cmd.strip() for cmd in cleaned_sql_script.split(';') if cmd.strip()]
        
        for i, command in enumerate(sql_commands):
            if command: # Ensure command is not empty
                logger.info(f"Executing command {i+1}/{len(sql_commands)}:\n{command[:100]}...") # Log first 100 chars
                client.command(command)
        
        step_end = time.time()
        logger.info(f"Step 3 finished in {step_end - step_start:.2f} seconds")
        logger.info("f_azure_billing_detail create completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to create f_azure_billing_detail: {e}", exc_info=True)
        raise


def insert_f_azure_billing_detail_batch(client: Client,start_date: date, end_date: date):
    """
    Populates the f_azure_billing_detail table in ClickHouse by executing the SQL from ck_insert_f_azure_billing_detail_batch.sql
    iteratively for each month within the specified date range.
    """
    try:
        logger.info("Step 1: Initialize ClickHouse client for f_azure_billing_detail population")
        step_start = time.time()
        # client = get_clickhouse_client()
        step_end = time.time()
        logger.info(f"Step 1 finished in {step_end - step_start:.2f} seconds")

        logger.info("Step 2: Reading SQL from clickhouse_sql/ck_insert_f_azure_billing_detail_batch.sql")
        step_start = time.time()
        with open('clickhouse_sql/ck_insert_f_azure_billing_detail_batch.sql', 'r') as f:
            sql_script = f.read()
        step_end = time.time()
        logger.info(f"Step 2 finished in {step_end - step_start:.2f} seconds")

        logger.info("Step 3: Executing SQL commands to populate f_azure_billing_detail in batches")
        step_start_total = time.time()

        current_date = start_date
        # end_date is already a date object

        while current_date <= end_date:
            batch_start_date = current_date.strftime("%Y-%m-01")
            # Calculate the last day of the current month
            # Add one month to the current date, then subtract one day
            batch_end_date_dt = current_date + relativedelta(months=1) - relativedelta(days=1)
            batch_end_date = batch_end_date_dt.strftime("%Y-%m-%d")

            logger.info(f"Loading data for month: {batch_start_date} to {batch_end_date}")

            # Execute the ClickHouse SQL script with parameters
            # The clickhouse-connect client.command method can take parameters directly
            # These parameters will be substituted into the SQL script.
            # Assuming the SQL script uses parameters like {param_batch_start_date} and {param_batch_end_date}
            try:
                client.command(
                    sql_script,
                    parameters={
                        'batch_start_date': batch_start_date,
                        'batch_end_date': batch_end_date
                    }
                )
                logger.info(f"Successfully loaded data for {batch_start_date} to {batch_end_date}")
            except Exception as e:
                logger.error(f"Failed to execute SQL for batch {batch_start_date} to {batch_end_date}: {e}", exc_info=True)
                raise

            # Move to the next month
            current_date += relativedelta(months=1)
        
        step_end_total = time.time()
        logger.info(f"Step 3 finished in {step_end_total - step_start_total:.2f} seconds")
        logger.info("f_azure_billing_detail batch population completed successfully.")
        
        # Perform data quality check
        source_table = f"dbo.{STAGE_TABLE_NAME}"
        target_table = f"dbo.{F_BILLING_DETAIL_TABLE_NAME}"
        check_row_counts(client, source_table, target_table, start_date, end_date)
        
        return True
    except Exception as e:
        logger.error(f"Failed to populate {F_BILLING_DETAIL_TABLE_NAME}: {e}", exc_info=True)
        raise

def get_processing_date_range(client: Client) -> tuple[date, date]:
    """
    Determines the start and end dates for processing billing data.
    The start date is typically the day after the last processed date in f_azure_billing_detail,
    or a default date if no previous data exists. The end date is the current date.
    Includes validation for future dates and warnings for old data.
    """
    current_date = datetime.now().date()
    
    last_date_f_billing_detail = get_last_date_f_billing_detail(client, table_name=F_BILLING_DETAIL_TABLE_NAME)
    
    if last_date_f_billing_detail:
        start_date = last_date_f_billing_detail + timedelta(days=1)
        logger.info(f"Last processed date found: {last_date_f_billing_detail}. Starting from: {start_date}")
    else:
        start_date = date(2023, 4, 1) # Default start date if no last date is found
        logger.info(f"No previous billing data found. Starting from default date: {start_date}")
    
    end_date = current_date
        
    logger.info(f"Determined processing period: {start_date} to {end_date}")
    
    # Validate date range
    if start_date > current_date:
        logger.error(f"Error: Start date {start_date} is in the future. Billing data not available.")
        raise ValueError(f"Cannot process future date: {start_date}")
    if end_date > current_date:
        logger.error(f"Error: End date {end_date} is in the future. Billing data not available.")
        raise ValueError(f"Cannot process future date: {end_date}")
    
    # Check if dates are within last DATA_RETENTION_MONTHS (typical EA data availability)
    # data_retention_threshold = current_date - relativedelta(months=DATA_RETENTION_MONTHS)
    # if start_date < data_retention_threshold:
    #     logger.warning(f"Warning: Start date {start_date} is older than {DATA_RETENTION_MONTHS} months. Data may be archived or incomplete.")
        
    return start_date, end_date

if __name__ == "__main__":
    try:
        client = get_clickhouse_client()
        logger.info("Starting daily delta billing data processing.")
        process_start_time = time.time()
        
        # START_DATE = date(2023, 4, 1)
        # END_DATE = date(2025, 7, 31)
        
        START_DATE, END_DATE = get_processing_date_range(client)
        
        prepare_dq_tagging_audit_table(client)
        audit_logs = run_pipeline(prepare_stage_table="drop", table_name=STAGE_TABLE_NAME, start_date=START_DATE, end_date=END_DATE)
        if not audit_logs.is_empty():
            insert_dq_tagging_audit_logs(client, audit_logs)

        if not exist_f_azure_billing_detail(client, table_name=F_BILLING_DETAIL_TABLE_NAME):
            logger.info(f"Table {F_BILLING_DETAIL_TABLE_NAME} does not exist. Creating it now.")
            create_f_azure_billing_detail()
        else:
            logger.info(f"Table {F_BILLING_DETAIL_TABLE_NAME} already exists.")

        insert_f_azure_billing_detail_batch(client, START_DATE, END_DATE)

        process_end_time = time.time()
        total_process_time = process_end_time - process_start_time
        logger.info(f"Total time for daily delta billing data processing: {total_process_time:.2f} seconds.")
        logger.info("Daily delta billing data processing completed successfully.")

    except Exception as e:
        logger.error(f"Main execution failed: {e}", exc_info=True)
        sys.exit(1)
