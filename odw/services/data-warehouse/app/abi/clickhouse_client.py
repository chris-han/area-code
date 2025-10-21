"""
ClickHouse Client Integration

Enhanced ClickHouse client with connection pooling, query optimization,
and FOCUS-specific query builders for ABI analytics.
"""

import clickhouse_connect
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
import logging
from contextlib import asynccontextmanager
import asyncio
from decimal import Decimal

logger = logging.getLogger(__name__)


class ClickHouseClient:
    """Enhanced ClickHouse client for ABI analytics"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._client = None
        self._connection_pool = None
        
    def connect(self):
        """Establish ClickHouse connection"""
        try:
            self._client = clickhouse_connect.get_client(
                host=self.config.get('host', 'ck.mightytech.cn'),
                port=self.config.get('port', 8443),
                username=self.config.get('username', 'finops'),
                password=self.config.get('password'),
                database=self.config.get('database', 'finops-odw'),
                secure=self.config.get('secure', True),
                connect_timeout=self.config.get('connect_timeout', 30),
                send_receive_timeout=self.config.get('send_receive_timeout', 300)
            )
            logger.info("ClickHouse client connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            raise
    
    def disconnect(self):
        """Close ClickHouse connection"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("ClickHouse client disconnected")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get ClickHouse connection with context management"""
        if not self._client:
            self.connect()
        
        try:
            yield self._client
        except Exception as e:
            logger.error(f"ClickHouse query error: {e}")
            raise
    
    async def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute ClickHouse query with parameters and return results.
        
        Args:
            query: SQL query string
            parameters: Query parameters
            
        Returns:
            List of result dictionaries
        """
        async with self.get_connection() as client:
            try:
                # Format parameters for ClickHouse
                formatted_params = self._format_parameters(parameters or {})
                
                # Execute query
                result = client.query(query, parameters=formatted_params)
                
                # Convert to list of dictionaries
                if result.result_rows:
                    columns = result.column_names
                    return [
                        dict(zip(columns, row))
                        for row in result.result_rows
                    ]
                else:
                    return []
                    
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Parameters: {parameters}")
                raise
    
    def _format_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Format parameters for ClickHouse query execution"""
        formatted = {}
        
        for key, value in parameters.items():
            if isinstance(value, (date, datetime)):
                formatted[key] = value.strftime('%Y-%m-%d')
            elif isinstance(value, list):
                # Format list parameters for IN clauses
                if all(isinstance(item, str) for item in value):
                    formatted[key] = value
                else:
                    formatted[key] = [str(item) for item in value]
            elif isinstance(value, Decimal):
                formatted[key] = float(value)
            else:
                formatted[key] = value
        
        return formatted
    
    async def execute_aggregation_query(
        self,
        table: str,
        select_fields: List[str],
        where_conditions: List[str],
        group_by: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute optimized aggregation query with ClickHouse-specific optimizations.
        
        Args:
            table: Table name
            select_fields: List of SELECT fields
            where_conditions: List of WHERE conditions
            group_by: Optional GROUP BY fields
            order_by: Optional ORDER BY clause
            limit: Optional LIMIT
            parameters: Query parameters
            
        Returns:
            List of result dictionaries
        """
        
        # Build optimized query
        query_parts = [f"SELECT {', '.join(select_fields)}"]
        query_parts.append(f"FROM {table}")
        
        if where_conditions:
            query_parts.append(f"WHERE {' AND '.join(where_conditions)}")
        
        if group_by:
            query_parts.append(f"GROUP BY {', '.join(group_by)}")
        
        if order_by:
            query_parts.append(f"ORDER BY {order_by}")
        
        if limit:
            query_parts.append(f"LIMIT {limit}")
        
        query = " ".join(query_parts)
        
        return await self.execute_query(query, parameters)
    
    async def get_table_stats(self, table: str) -> Dict[str, Any]:
        """Get table statistics for query optimization"""
        try:
            stats_query = f"""
                SELECT
                    count() as total_rows,
                    min(usage_date) as min_date,
                    max(usage_date) as max_date,
                    sum(billed_cost) as total_cost,
                    uniq(billing_account_id) as unique_accounts,
                    uniq(service_category) as unique_services
                FROM {table}
            """
            
            result = await self.execute_query(stats_query)
            return result[0] if result else {}
            
        except Exception as e:
            logger.error(f"Failed to get table stats for {table}: {e}")
            return {}
    
    async def optimize_table(self, table: str):
        """Optimize table for better query performance"""
        try:
            optimize_query = f"OPTIMIZE TABLE {table} FINAL"
            await self.execute_query(optimize_query)
            logger.info(f"Table {table} optimized successfully")
            
        except Exception as e:
            logger.error(f"Failed to optimize table {table}: {e}")
    
    async def check_connection(self) -> bool:
        """Check if ClickHouse connection is healthy"""
        try:
            result = await self.execute_query("SELECT 1 as health_check")
            return len(result) > 0 and result[0].get('health_check') == 1
            
        except Exception as e:
            logger.error(f"ClickHouse health check failed: {e}")
            return False


class FOCUSQueryBuilder:
    """Query builder for FOCUS-compliant billing data queries"""
    
    def __init__(self, client: ClickHouseClient):
        self.client = client
        self.base_table = "focus_billing_data"
    
    def build_billing_data_query(
        self,
        filters: Dict[str, Any],
        pagination: Dict[str, Any],
        sorting: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """Build optimized billing data query with filters"""
        
        select_fields = [
            "id", "billing_account_id", "billing_account_name",
            "billing_currency", "billing_period_start_date", "billing_period_end_date",
            "billed_cost", "effective_cost", "list_cost", "list_unit_price",
            "usage_date", "usage_quantity", "usage_unit",
            "resource_id", "resource_name", "resource_type",
            "service_category", "service_name",
            "availability_zone", "region", "provider",
            "created_at", "updated_at", "source_system"
        ]
        
        where_conditions = []
        parameters = {}
        
        # Date filters (optimized for partitioning)
        if filters.get('start_date'):
            where_conditions.append("usage_date >= {start_date}")
            parameters['start_date'] = filters['start_date']
        
        if filters.get('end_date'):
            where_conditions.append("usage_date <= {end_date}")
            parameters['end_date'] = filters['end_date']
        
        # Account filters
        if filters.get('billing_account_ids'):
            where_conditions.append("billing_account_id IN {billing_account_ids}")
            parameters['billing_account_ids'] = filters['billing_account_ids']
        
        # Service filters
        if filters.get('service_categories'):
            where_conditions.append("service_category IN {service_categories}")
            parameters['service_categories'] = filters['service_categories']
        
        if filters.get('service_names'):
            where_conditions.append("service_name IN {service_names}")
            parameters['service_names'] = filters['service_names']
        
        # Resource filters
        if filters.get('resource_types'):
            where_conditions.append("resource_type IN {resource_types}")
            parameters['resource_types'] = filters['resource_types']
        
        if filters.get('regions'):
            where_conditions.append("region IN {regions}")
            parameters['regions'] = filters['regions']
        
        # Cost filters
        if filters.get('min_cost') is not None:
            where_conditions.append("billed_cost >= {min_cost}")
            parameters['min_cost'] = filters['min_cost']
        
        if filters.get('max_cost') is not None:
            where_conditions.append("billed_cost <= {max_cost}")
            parameters['max_cost'] = filters['max_cost']
        
        # Provider filters
        if filters.get('providers'):
            where_conditions.append("provider IN {providers}")
            parameters['providers'] = filters['providers']
        
        # Build query
        query = f"SELECT {', '.join(select_fields)} FROM {self.base_table}"
        
        if where_conditions:
            query += f" WHERE {' AND '.join(where_conditions)}"
        
        # Add sorting
        sort_field = sorting.get('sort_by', 'usage_date')
        sort_order = sorting.get('sort_order', 'desc').upper()
        query += f" ORDER BY {sort_field} {sort_order}"
        
        # Add pagination
        limit = pagination.get('limit', 100)
        offset = pagination.get('offset', 0)
        query += f" LIMIT {limit} OFFSET {offset}"
        
        parameters['limit'] = limit
        parameters['offset'] = offset
        
        return query, parameters
    
    def build_aggregation_query(
        self,
        group_by: List[str],
        metrics: List[str],
        filters: Dict[str, Any],
        limit: Optional[int] = None
    ) -> tuple[str, Dict[str, Any]]:
        """Build optimized aggregation query"""
        
        # Build SELECT clause
        select_fields = group_by.copy()
        
        # Add metric calculations
        metric_calculations = {
            "total_cost": "sum(billed_cost)",
            "avg_cost": "avg(billed_cost)",
            "min_cost": "min(billed_cost)",
            "max_cost": "max(billed_cost)",
            "total_usage": "sum(usage_quantity)",
            "record_count": "count(*)"
        }
        
        for metric in metrics:
            if metric in metric_calculations:
                select_fields.append(f"{metric_calculations[metric]} as {metric}")
        
        # Build WHERE conditions (same as billing data query)
        where_conditions = []
        parameters = {}
        
        if filters.get('start_date'):
            where_conditions.append("usage_date >= {start_date}")
            parameters['start_date'] = filters['start_date']
        
        if filters.get('end_date'):
            where_conditions.append("usage_date <= {end_date}")
            parameters['end_date'] = filters['end_date']
        
        # Add other filters...
        for filter_key, condition_template in [
            ('billing_account_ids', 'billing_account_id IN {billing_account_ids}'),
            ('service_categories', 'service_category IN {service_categories}'),
            ('service_names', 'service_name IN {service_names}'),
            ('resource_types', 'resource_type IN {resource_types}'),
            ('regions', 'region IN {regions}'),
            ('providers', 'provider IN {providers}')
        ]:
            if filters.get(filter_key):
                where_conditions.append(condition_template)
                parameters[filter_key] = filters[filter_key]
        
        # Build query
        query = f"SELECT {', '.join(select_fields)} FROM {self.base_table}"
        
        if where_conditions:
            query += f" WHERE {' AND '.join(where_conditions)}"
        
        if group_by:
            query += f" GROUP BY {', '.join(group_by)}"
        
        # Order by first metric
        if metrics:
            query += f" ORDER BY {metrics[0]} DESC"
        
        if limit:
            query += f" LIMIT {limit}"
            parameters['limit'] = limit
        
        return query, parameters