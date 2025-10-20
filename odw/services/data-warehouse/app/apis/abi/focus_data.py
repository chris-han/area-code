"""
FOCUS Data API

Provides FOCUS-compliant billing data query endpoints with filtering,
aggregation, and analytics capabilities.
"""

from moose_lib import ConsumptionApi, EgressConfig
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class FOCUSBillingRecord(BaseModel):
    """FOCUS billing record response model"""
    id: str
    billing_account_id: str
    billing_account_name: Optional[str]
    billing_currency: str
    billing_period_start_date: date
    billing_period_end_date: date
    billed_cost: Decimal
    effective_cost: Optional[Decimal]
    list_cost: Optional[Decimal]
    list_unit_price: Optional[Decimal]
    usage_date: date
    usage_quantity: Optional[Decimal]
    usage_unit: Optional[str]
    resource_id: Optional[str]
    resource_name: Optional[str]
    resource_type: Optional[str]
    service_category: Optional[str]
    service_name: Optional[str]
    availability_zone: Optional[str]
    region: Optional[str]
    provider: str
    created_at: datetime
    updated_at: datetime
    source_system: str


class FOCUSDataQuery(BaseModel):
    """FOCUS data query parameters"""
    # Pagination
    limit: Optional[int] = Field(default=100, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)
    
    # Date filtering
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Account filtering
    billing_account_ids: Optional[List[str]] = None
    
    # Service filtering
    service_categories: Optional[List[str]] = None
    service_names: Optional[List[str]] = None
    
    # Resource filtering
    resource_types: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    
    # Cost filtering
    min_cost: Optional[Decimal] = Field(default=None, ge=0)
    max_cost: Optional[Decimal] = Field(default=None, ge=0)
    
    # Provider filtering
    providers: Optional[List[str]] = None
    
    # Sorting
    sort_by: Optional[str] = Field(default="usage_date", pattern="^(usage_date|billed_cost|created_at)$")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v
    
    @validator('max_cost')
    def validate_cost_range(cls, v, values):
        if v and 'min_cost' in values and values['min_cost']:
            if v < values['min_cost']:
                raise ValueError('max_cost must be greater than min_cost')
        return v


class FOCUSDataResponse(BaseModel):
    """FOCUS data response model"""
    items: List[FOCUSBillingRecord]
    total: int
    page_info: Dict[str, Any]
    filters_applied: Dict[str, Any]


class FOCUSAggregationQuery(BaseModel):
    """FOCUS data aggregation query parameters"""
    # Date filtering
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Grouping dimensions
    group_by: List[str] = Field(
        default=["service_category"],
        pattern="^(service_category|service_name|region|billing_account_id|usage_date|provider)$",
    )
    
    # Aggregation metrics
    metrics: List[str] = Field(
        default=["total_cost", "record_count"],
        pattern="^(total_cost|avg_cost|min_cost|max_cost|total_usage|record_count)$",
    )
    
    # Filtering (same as FOCUSDataQuery)
    billing_account_ids: Optional[List[str]] = None
    service_categories: Optional[List[str]] = None
    service_names: Optional[List[str]] = None
    resource_types: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    providers: Optional[List[str]] = None
    
    # Result limiting
    limit: Optional[int] = Field(default=100, ge=1, le=1000)


class FOCUSAggregationResult(BaseModel):
    """FOCUS aggregation result model"""
    dimensions: Dict[str, Any]
    metrics: Dict[str, Decimal]


class FOCUSAggregationResponse(BaseModel):
    """FOCUS aggregation response model"""
    results: List[FOCUSAggregationResult]
    total_results: int
    query_info: Dict[str, Any]


def get_focus_billing_data(client, params: FOCUSDataQuery) -> FOCUSDataResponse:
    """
    Retrieve FOCUS-compliant billing data with filtering and pagination.
    
    Args:
        client: Database client for executing queries
        params: Query parameters for filtering and pagination
        
    Returns:
        FOCUSDataResponse with billing records
    """
    
    # Build base query
    query = """
        SELECT
            id,
            billing_account_id,
            billing_account_name,
            billing_currency,
            billing_period_start_date,
            billing_period_end_date,
            billed_cost,
            effective_cost,
            list_cost,
            list_unit_price,
            usage_date,
            usage_quantity,
            usage_unit,
            resource_id,
            resource_name,
            resource_type,
            service_category,
            service_name,
            availability_zone,
            region,
            provider,
            created_at,
            updated_at,
            source_system
        FROM focus_billing_data
    """
    
    # Build WHERE conditions
    where_conditions = []
    query_params = {}
    
    if params.start_date:
        where_conditions.append("usage_date >= {start_date}")
        query_params["start_date"] = params.start_date
    
    if params.end_date:
        where_conditions.append("usage_date <= {end_date}")
        query_params["end_date"] = params.end_date
    
    if params.billing_account_ids:
        where_conditions.append("billing_account_id IN {billing_account_ids}")
        query_params["billing_account_ids"] = params.billing_account_ids
    
    if params.service_categories:
        where_conditions.append("service_category IN {service_categories}")
        query_params["service_categories"] = params.service_categories
    
    if params.service_names:
        where_conditions.append("service_name IN {service_names}")
        query_params["service_names"] = params.service_names
    
    if params.resource_types:
        where_conditions.append("resource_type IN {resource_types}")
        query_params["resource_types"] = params.resource_types
    
    if params.regions:
        where_conditions.append("region IN {regions}")
        query_params["regions"] = params.regions
    
    if params.min_cost is not None:
        where_conditions.append("billed_cost >= {min_cost}")
        query_params["min_cost"] = params.min_cost
    
    if params.max_cost is not None:
        where_conditions.append("billed_cost <= {max_cost}")
        query_params["max_cost"] = params.max_cost
    
    if params.providers:
        where_conditions.append("provider IN {providers}")
        query_params["providers"] = params.providers
    
    # Add WHERE clause if conditions exist
    if where_conditions:
        query += " WHERE " + " AND ".join(where_conditions)
    
    # Add ORDER BY
    query += f" ORDER BY {params.sort_by} {params.sort_order.upper()}"
    
    # Add LIMIT and OFFSET
    query += " LIMIT {limit} OFFSET {offset}"
    query_params["limit"] = params.limit
    query_params["offset"] = params.offset
    
    # Execute query
    try:
        result = client.query.execute(query, query_params)
        
        # Convert results to FOCUSBillingRecord objects
        items = []
        for item in result:
            # Convert Decimal fields
            record_data = dict(item)
            for field in ['billed_cost', 'effective_cost', 'list_cost', 'list_unit_price', 'usage_quantity']:
                if record_data.get(field) is not None:
                    record_data[field] = Decimal(str(record_data[field]))
            
            items.append(FOCUSBillingRecord(**record_data))
        
        # Get total count (simplified - in production you'd use a separate count query)
        total = len(items)
        
        # Create page info
        page_info = {
            "current_page": (params.offset // params.limit) + 1 if params.limit else 1,
            "page_size": params.limit,
            "total_pages": (total + params.limit - 1) // params.limit if params.limit else 1,
            "has_next": params.offset + params.limit < total if params.limit else False,
            "has_previous": params.offset > 0
        }
        
        # Create filters applied info
        filters_applied = {
            "date_range": {
                "start_date": params.start_date,
                "end_date": params.end_date
            } if params.start_date or params.end_date else None,
            "accounts": params.billing_account_ids,
            "services": {
                "categories": params.service_categories,
                "names": params.service_names
            } if params.service_categories or params.service_names else None,
            "resources": {
                "types": params.resource_types,
                "regions": params.regions
            } if params.resource_types or params.regions else None,
            "cost_range": {
                "min": params.min_cost,
                "max": params.max_cost
            } if params.min_cost is not None or params.max_cost is not None else None,
            "providers": params.providers
        }
        
        return FOCUSDataResponse(
            items=items,
            total=total,
            page_info=page_info,
            filters_applied=filters_applied
        )
        
    except Exception as e:
        logger.error(f"Error executing FOCUS data query: {e}")
        raise


def get_focus_aggregation(client, params: FOCUSAggregationQuery) -> FOCUSAggregationResponse:
    """
    Get aggregated FOCUS billing data with grouping and metrics.
    
    Args:
        client: Database client for executing queries
        params: Aggregation query parameters
        
    Returns:
        FOCUSAggregationResponse with aggregated results
    """
    
    # Build SELECT clause with grouping and metrics
    select_fields = []
    
    # Add grouping dimensions
    for dimension in params.group_by:
        select_fields.append(dimension)
    
    # Add metric calculations
    metric_calculations = {
        "total_cost": "sum(billed_cost)",
        "avg_cost": "avg(billed_cost)",
        "min_cost": "min(billed_cost)",
        "max_cost": "max(billed_cost)",
        "total_usage": "sum(usage_quantity)",
        "record_count": "count(*)"
    }
    
    for metric in params.metrics:
        if metric in metric_calculations:
            select_fields.append(f"{metric_calculations[metric]} as {metric}")
    
    query = f"SELECT {', '.join(select_fields)} FROM focus_billing_data"
    
    # Build WHERE conditions (similar to get_focus_billing_data)
    where_conditions = []
    query_params = {}
    
    if params.start_date:
        where_conditions.append("usage_date >= {start_date}")
        query_params["start_date"] = params.start_date
    
    if params.end_date:
        where_conditions.append("usage_date <= {end_date}")
        query_params["end_date"] = params.end_date
    
    # Add other filters...
    if params.billing_account_ids:
        where_conditions.append("billing_account_id IN {billing_account_ids}")
        query_params["billing_account_ids"] = params.billing_account_ids
    
    if params.service_categories:
        where_conditions.append("service_category IN {service_categories}")
        query_params["service_categories"] = params.service_categories
    
    # Add WHERE clause
    if where_conditions:
        query += " WHERE " + " AND ".join(where_conditions)
    
    # Add GROUP BY
    if params.group_by:
        query += f" GROUP BY {', '.join(params.group_by)}"
    
    # Add ORDER BY (order by first metric)
    if params.metrics:
        query += f" ORDER BY {params.metrics[0]} DESC"
    
    # Add LIMIT
    if params.limit:
        query += f" LIMIT {params.limit}"
        query_params["limit"] = params.limit
    
    # Execute query
    try:
        result = client.query.execute(query, query_params)
        
        # Convert results to FOCUSAggregationResult objects
        results = []
        for item in result:
            item_dict = dict(item)
            
            # Separate dimensions and metrics
            dimensions = {}
            metrics = {}
            
            for key, value in item_dict.items():
                if key in params.group_by:
                    dimensions[key] = value
                elif key in params.metrics:
                    metrics[key] = Decimal(str(value)) if value is not None else Decimal('0')
            
            results.append(FOCUSAggregationResult(
                dimensions=dimensions,
                metrics=metrics
            ))
        
        # Create query info
        query_info = {
            "group_by": params.group_by,
            "metrics": params.metrics,
            "date_range": {
                "start_date": params.start_date,
                "end_date": params.end_date
            } if params.start_date or params.end_date else None,
            "filters_count": len([f for f in [
                params.billing_account_ids,
                params.service_categories,
                params.service_names,
                params.resource_types,
                params.regions,
                params.providers
            ] if f])
        }
        
        return FOCUSAggregationResponse(
            results=results,
            total_results=len(results),
            query_info=query_info
        )
        
    except Exception as e:
        logger.error(f"Error executing FOCUS aggregation query: {e}")
        raise


# Create the consumption APIs
focus_data_api = ConsumptionApi[FOCUSDataQuery, FOCUSDataResponse](
    "getFocusBillingData",
    query_function=get_focus_billing_data,
    source="focus_billing_data",
    config=EgressConfig()
)

focus_aggregation_api = ConsumptionApi[FOCUSAggregationQuery, FOCUSAggregationResponse](
    "getFocusAggregation", 
    query_function=get_focus_aggregation,
    source="focus_billing_data",
    config=EgressConfig()
)
