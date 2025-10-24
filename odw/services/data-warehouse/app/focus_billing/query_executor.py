"""
FOCUS Query Parameter Handler and Executor

Handles parameter validation, type coercion, and SQL execution
for FOCUS queries with proper ClickHouse parameter binding.
"""

import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any, Union, Optional, Tuple
from pydantic import BaseModel, ValidationError

from .models import FocusQuery, FocusQueryParameter, FocusQueryRequest, FocusQueryResponse
from .query_loader import FocusQueryLoader


class ParameterValidationError(Exception):
    """Raised when query parameter validation fails."""
    pass


class FocusQueryParameterHandler:
    """
    Handles parameter validation, type coercion, and SQL preparation
    for FOCUS query execution.
    """
    
    def __init__(self):
        self.query_loader = FocusQueryLoader()
        
    def validate_and_prepare_parameters(
        self, 
        query: FocusQuery, 
        raw_parameters: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Validate parameters and prepare SQL for execution.
        
        Args:
            query: FocusQuery object
            raw_parameters: Raw parameter values from request
            
        Returns:
            Tuple of (prepared_sql, validated_parameters)
            
        Raises:
            ParameterValidationError: If parameter validation fails
        """
        # Validate required parameters are provided
        missing_params = set(query.parameters) - set(raw_parameters.keys())
        if missing_params:
            raise ParameterValidationError(
                f"Missing required parameters: {', '.join(missing_params)}"
            )
            
        # Validate and coerce parameter types
        validated_params = {}
        for param_name in query.parameters:
            raw_value = raw_parameters[param_name]
            try:
                validated_value = self._coerce_parameter_type(param_name, raw_value)
                validated_params[param_name] = validated_value
            except Exception as e:
                raise ParameterValidationError(
                    f"Invalid value for parameter '{param_name}': {e}"
                )
                
        # Convert SQL from positional to named parameters
        prepared_sql = self._convert_to_named_parameters(query.sql, query.parameters)
        
        return prepared_sql, validated_params
        
    def _coerce_parameter_type(self, param_name: str, value: Any) -> Any:
        """
        Coerce parameter value to appropriate type based on naming conventions.
        
        Args:
            param_name: Parameter name
            value: Raw parameter value
            
        Returns:
            Coerced parameter value
            
        Raises:
            ValueError: If coercion fails
        """
        if value is None:
            return None
            
        param_lower = param_name.lower()
        
        # Date parameters
        if 'date' in param_lower:
            return self._coerce_to_date(value)
            
        # Datetime parameters  
        elif 'time' in param_lower and 'date' not in param_lower:
            return self._coerce_to_datetime(value)
            
        # Numeric parameters
        elif param_lower in ['limit', 'offset', 'count'] or 'count' in param_lower:
            return self._coerce_to_int(value)
            
        elif param_lower in ['cost', 'amount', 'price'] or any(x in param_lower for x in ['cost', 'amount', 'price']):
            return self._coerce_to_decimal(value)
            
        # String parameters (default)
        else:
            return str(value)
            
    def _coerce_to_date(self, value: Any) -> date:
        """Coerce value to date object."""
        if isinstance(value, datetime):
            return value.date()
        elif isinstance(value, date):
            return value
        elif isinstance(value, str):
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date: {value}")
        else:
            raise ValueError(f"Cannot convert {type(value)} to date")
            
    def _coerce_to_datetime(self, value: Any) -> datetime:
        """Coerce value to datetime object."""
        if isinstance(value, datetime):
            return value
        elif isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        elif isinstance(value, str):
            # Try common datetime formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse datetime: {value}")
        else:
            raise ValueError(f"Cannot convert {type(value)} to datetime")
            
    def _coerce_to_int(self, value: Any) -> int:
        """Coerce value to integer."""
        if isinstance(value, int):
            return value
        elif isinstance(value, float):
            if value.is_integer():
                return int(value)
            else:
                raise ValueError(f"Float value {value} is not a whole number")
        elif isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                raise ValueError(f"Unable to parse integer: {value}")
        else:
            raise ValueError(f"Cannot convert {type(value)} to integer")
            
    def _coerce_to_decimal(self, value: Any) -> Decimal:
        """Coerce value to Decimal."""
        if isinstance(value, Decimal):
            return value
        elif isinstance(value, (int, float)):
            return Decimal(str(value))
        elif isinstance(value, str):
            try:
                return Decimal(value)
            except InvalidOperation:
                raise ValueError(f"Unable to parse decimal: {value}")
        else:
            raise ValueError(f"Cannot convert {type(value)} to decimal")
            
    def _convert_to_named_parameters(self, sql: str, parameters: List[str]) -> str:
        """
        Convert SQL with positional parameters (?) to named parameters.
        
        Args:
            sql: SQL query with positional parameters
            parameters: List of parameter names in order
            
        Returns:
            SQL query with named parameters
        """
        # Replace positional parameters with named ones
        result_sql = sql
        param_index = 0
        
        # Find and replace each ? with the corresponding named parameter
        while '?' in result_sql and param_index < len(parameters):
            param_name = parameters[param_index]
            # Replace first occurrence of ? with named parameter
            result_sql = result_sql.replace('?', f':{param_name}', 1)
            param_index += 1
            
        return result_sql


class FocusQueryExecutor:
    """
    Executes FOCUS queries against ClickHouse with parameter binding.
    """
    
    def __init__(self):
        self.query_loader = FocusQueryLoader()
        self.parameter_handler = FocusQueryParameterHandler()
        
    def execute_query(
        self, 
        request: FocusQueryRequest,
        clickhouse_client = None  # Will be injected by the API layer
    ) -> FocusQueryResponse:
        """
        Execute a FOCUS query with the provided parameters.
        
        Args:
            request: Query execution request
            clickhouse_client: ClickHouse client instance
            
        Returns:
            Query execution response
            
        Raises:
            ValueError: If query not found or parameters invalid
            RuntimeError: If query execution fails
        """
        # Load the query
        query = self.query_loader.get_query(request.query_slug)
        if not query:
            raise ValueError(f"Query not found: {request.query_slug}")
            
        # Validate and prepare parameters
        try:
            prepared_sql, validated_params = self.parameter_handler.validate_and_prepare_parameters(
                query, request.parameters
            )
        except ParameterValidationError as e:
            raise ValueError(str(e))
            
        # Add pagination if specified
        if request.limit is not None:
            prepared_sql += f" LIMIT {request.limit}"
            if request.offset > 0:
                prepared_sql += f" OFFSET {request.offset}"
                
        # Execute query (this will be implemented by the API layer with actual ClickHouse client)
        if clickhouse_client is None:
            raise RuntimeError("ClickHouse client not provided")
            
        start_time = datetime.now()
        
        try:
            # Execute the query with named parameters
            result = clickhouse_client.query(prepared_sql, parameters=validated_params)
            rows = result.result_rows
            
            # Convert rows to list of dictionaries
            columns = result.column_names
            row_dicts = [dict(zip(columns, row)) for row in rows]
            
            # Get total count if pagination is used
            total_rows = len(row_dicts)
            if request.limit is not None:
                # Execute count query to get total
                count_sql = self._create_count_query(prepared_sql)
                count_result = clickhouse_client.query(count_sql, parameters=validated_params)
                total_rows = count_result.result_rows[0][0] if count_result.result_rows else 0
                
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}")
            
        end_time = datetime.now()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000
        
        return FocusQueryResponse(
            query_slug=request.query_slug,
            rows=row_dicts,
            total_rows=total_rows,
            execution_time_ms=execution_time_ms,
            parameters_used=validated_params
        )
        
    def _create_count_query(self, sql: str) -> str:
        """
        Create a COUNT query from the original SQL for pagination.
        
        Args:
            sql: Original SQL query
            
        Returns:
            COUNT query SQL
        """
        # Remove LIMIT and OFFSET clauses
        count_sql = re.sub(r'\s+LIMIT\s+\d+(\s+OFFSET\s+\d+)?$', '', sql, flags=re.IGNORECASE)
        
        # Wrap in COUNT query
        count_sql = f"SELECT COUNT(*) FROM ({count_sql}) AS count_subquery"
        
        return count_sql


class FocusQueryValidator:
    """
    Validates FOCUS queries for common issues and compatibility.
    """
    
    @staticmethod
    def validate_query_syntax(query: FocusQuery) -> List[str]:
        """
        Validate query syntax and return list of issues found.
        
        Args:
            query: FocusQuery to validate
            
        Returns:
            List of validation issues (empty if no issues)
        """
        issues = []
        sql = query.sql.upper()
        
        # Check for dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if keyword in sql:
                issues.append(f"Query contains potentially dangerous keyword: {keyword}")
                
        # Check for required table references
        if 'FOCUS_DATA_TABLE' not in sql and 'FOCUS_CONTRACT_COMMITMENT_VIEW' not in sql:
            issues.append("Query does not reference any FOCUS tables")
            
        # Check parameter count consistency
        positional_count = query.sql.count('?')
        if positional_count != len(query.parameters):
            issues.append(f"Parameter count mismatch: {positional_count} placeholders, {len(query.parameters)} parameters")
            
        return issues
        
    @staticmethod
    def validate_parameter_usage(query: FocusQuery, parameters: Dict[str, Any]) -> List[str]:
        """
        Validate parameter usage for a specific query execution.
        
        Args:
            query: FocusQuery to validate
            parameters: Parameters to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for missing parameters
        missing = set(query.parameters) - set(parameters.keys())
        if missing:
            issues.append(f"Missing required parameters: {', '.join(missing)}")
            
        # Check for extra parameters
        extra = set(parameters.keys()) - set(query.parameters)
        if extra:
            issues.append(f"Unexpected parameters provided: {', '.join(extra)}")
            
        # Validate date range parameters
        if 'start_date' in parameters and 'end_date' in parameters:
            try:
                start_date = parameters['start_date']
                end_date = parameters['end_date']
                
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    
                if start_date >= end_date:
                    issues.append("start_date must be before end_date")
                    
            except Exception as e:
                issues.append(f"Invalid date format: {e}")
                
        return issues