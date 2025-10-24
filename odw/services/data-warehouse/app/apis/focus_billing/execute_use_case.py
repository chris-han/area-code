"""
FOCUS Billing API: Execute Use Case

Provides an API endpoint to execute FOCUS use case queries with runtime
parameters, returning paginated results and execution metrics.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import date, datetime
from decimal import Decimal
import time
import re
from pydantic import BaseModel, Field, validator
from moose_lib import ConsumptionApi, EgressConfig

from app.focus_billing.query_loader import FocusQueryLoader
from app.focus_billing.models import FocusQuery
from .exceptions import handle_focus_billing_error, QueryNotFoundError, QueryExecutionError, ParameterValidationError


class ExecuteFocusUseCaseQueryParams(BaseModel):
    """Query parameters for executing a FOCUS use case"""
    slug: str = Field(description="Use case slug identifier")
    start_date: Optional[date] = Field(None, description="Start date parameter")
    end_date: Optional[date] = Field(None, description="End date parameter")
    parameters: Dict[str, Union[str, int, float, date, datetime]] = Field(
        default_factory=dict, 
        description="Additional query parameters"
    )
    limit: Optional[int] = Field(None, ge=1, le=10000, description="Maximum number of rows to return")
    offset: int = Field(default=0, ge=0, description="Number of rows to skip")
    
    @validator('slug')
    def validate_slug(cls, v):
        if not v or not v.strip():
            raise ValueError("Slug cannot be empty")
        return v.strip()
    
    @validator('parameters', pre=True)
    def validate_parameters(cls, v):
        if v is None:
            return {}
        return v


class ExecuteFocusUseCaseResponse(BaseModel):
    """Response model for executing a FOCUS use case"""
    slug: str = Field(description="Executed query slug")
    rows: List[Dict[str, Any]] = Field(description="Query result rows")
    total_rows: int = Field(description="Total number of rows returned")
    execution_time_ms: float = Field(description="Query execution time in milliseconds")
    parameters_used: Dict[str, Any] = Field(description="Parameters used in execution")
    sql_executed: str = Field(description="Final SQL that was executed")
    has_more: bool = Field(description="Whether there are more rows available")


def execute_focus_use_case(client, params: ExecuteFocusUseCaseQueryParams) -> ExecuteFocusUseCaseResponse:
    """
    Execute a FOCUS use case query with runtime parameters.
    
    Args:
        client: ClickHouse client for query execution
        params: Query parameters including slug and runtime parameters
        
    Returns:
        ExecuteFocusUseCaseResponse with query results and metrics
        
    Raises:
        QueryNotFoundError: If the requested query is not found
        ParameterValidationError: If required parameters are missing or invalid
        QueryExecutionError: If query execution fails
        Exception: For other unexpected errors
    """
    start_time = time.time()
    
    try:
        # Load the query
        query_loader = FocusQueryLoader()
        query = query_loader.get_query(params.slug)
        
        if not query:
            raise QueryNotFoundError(params.slug)
        
        # Prepare parameters with validation
        query_params = _prepare_query_parameters(query, params)
        
        # Convert positional parameters to named parameters
        sql_with_named_params = _convert_to_named_parameters(query.sql, query_params)
        
        # Add pagination if specified
        final_sql = sql_with_named_params
        if params.limit is not None:
            final_sql += f" LIMIT {params.limit}"
            if params.offset > 0:
                final_sql += f" OFFSET {params.offset}"
        
        # Execute the query
        try:
            result = client.query.execute(final_sql, query_params)
            rows = [dict(row) for row in result] if result else []
        except Exception as e:
            raise QueryExecutionError(params.slug, str(e))
        
        # Calculate execution time
        execution_time = (time.time() - start_time) * 1000
        
        # Determine if there are more rows
        has_more = False
        if params.limit is not None and len(rows) == params.limit:
            # Check if there's a next page by running a count query
            try:
                count_sql = f"SELECT COUNT(*) as total FROM ({sql_with_named_params}) as subquery"
                count_result = client.query.execute(count_sql, query_params)
                total_available = count_result[0]['total'] if count_result else 0
                has_more = (params.offset + len(rows)) < total_available
            except:
                # If count fails, assume there might be more
                has_more = len(rows) == params.limit
        
        return ExecuteFocusUseCaseResponse(
            slug=params.slug,
            rows=rows,
            total_rows=len(rows),
            execution_time_ms=execution_time,
            parameters_used=query_params,
            sql_executed=final_sql,
            has_more=has_more
        )
        
    except (QueryNotFoundError, ParameterValidationError, QueryExecutionError):
        # Re-raise known FOCUS billing errors
        raise
    except Exception as e:
        # Log unexpected errors and re-raise
        print(f"Unexpected error in execute_focus_use_case: {str(e)}")
        raise


def _prepare_query_parameters(query: FocusQuery, params: ExecuteFocusUseCaseQueryParams) -> Dict[str, Any]:
    """
    Prepare query parameters by combining standard and custom parameters.
    
    Args:
        query: FocusQuery object with parameter definitions
        params: Request parameters
        
    Returns:
        Dictionary of prepared parameters for query execution
    """
    query_params = {}
    
    # Add standard date parameters if provided
    if params.start_date is not None:
        query_params['start_date'] = params.start_date
    if params.end_date is not None:
        query_params['end_date'] = params.end_date
    
    # Add custom parameters
    query_params.update(params.parameters)
    
    # Validate that all required parameters are provided
    missing_params = []
    for required_param in query.parameters:
        if required_param not in query_params:
            missing_params.append(required_param)
    
    if missing_params:
        raise ParameterValidationError(missing_params=missing_params)
    
    # Convert date objects to strings for ClickHouse
    for key, value in query_params.items():
        if isinstance(value, date):
            query_params[key] = value.strftime('%Y-%m-%d')
        elif isinstance(value, datetime):
            query_params[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, Decimal):
            query_params[key] = float(value)
    
    return query_params


def _convert_to_named_parameters(sql: str, parameters: Dict[str, Any]) -> str:
    """
    Convert positional parameters (?) to named parameters for ClickHouse.
    
    Args:
        sql: SQL query with positional parameters
        parameters: Dictionary of parameter values
        
    Returns:
        SQL query with named parameters
    """
    # Find all positional parameters
    positional_count = sql.count('?')
    
    if positional_count == 0:
        return sql
    
    # Replace positional parameters with named ones
    # Assume standard order: start_date, end_date, then additional parameters
    param_names = ['start_date', 'end_date']
    
    # Add additional parameter names if needed
    param_keys = list(parameters.keys())
    for i in range(2, positional_count):
        if i < len(param_keys):
            param_names.append(param_keys[i])
        else:
            param_names.append(f'param_{i + 1}')
    
    # Replace ? with {param_name} in order
    result_sql = sql
    for i, param_name in enumerate(param_names[:positional_count]):
        result_sql = result_sql.replace('?', f'{{{param_name}}}', 1)
    
    return result_sql


# Create the consumption API
execute_focus_use_case_api = ConsumptionApi[ExecuteFocusUseCaseQueryParams, ExecuteFocusUseCaseResponse](
    "executeFocusUseCase",
    query_function=execute_focus_use_case,
    source="focus_billing",  # Logical source name
    config=EgressConfig()
)