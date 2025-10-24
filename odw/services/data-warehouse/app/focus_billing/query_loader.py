"""
FOCUS Query Loader and Parser

Loads and parses YAML query files from the FOCUS specification,
converting them into FocusQuery models with proper parameter extraction
and table reference normalization.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from pydantic import ValidationError

from .models import FocusQuery
from .config import FocusBillingConfig


class FocusQueryLoader:
    """
    Loads and parses FOCUS query YAML files into FocusQuery models.
    
    Handles:
    - Loading queries from YAML files
    - Merging base queries with adjustments
    - Extracting parameters from SQL
    - Replacing table references with ClickHouse view names
    """
    
    def __init__(self, config: Optional[FocusBillingConfig] = None):
        self.config = config or FocusBillingConfig()
        self._queries_cache: Optional[Dict[str, FocusQuery]] = None
        
    def load_queries(self, force_reload: bool = False) -> Dict[str, FocusQuery]:
        """
        Load all FOCUS queries from YAML files.
        
        Args:
            force_reload: If True, reload queries even if cached
            
        Returns:
            Dictionary mapping query slugs to FocusQuery objects
        """
        if self._queries_cache is not None and not force_reload:
            return self._queries_cache
            
        queries_dir = Path(self.config.focus_queries_root)
        
        if not queries_dir.exists():
            raise FileNotFoundError(f"Queries directory not found: {queries_dir}")
            
        # Load base queries
        base_queries = self._load_yaml_file(queries_dir / "focus_use_cases.yaml")
        
        # Load adjustments
        adjustments_file = queries_dir / "focus_use_cases_adjustments.yaml"
        adjustments = {}
        if adjustments_file.exists():
            adjustments = self._load_yaml_file(adjustments_file)
            
        # Merge queries with adjustments
        merged_queries = self._merge_queries(base_queries, adjustments)
        
        # Convert to FocusQuery models
        focus_queries = {}
        for slug, query_data in merged_queries.items():
            try:
                focus_query = self._convert_to_focus_query(slug, query_data)
                focus_queries[slug] = focus_query
            except Exception as e:
                print(f"Warning: Failed to parse query '{slug}': {e}")
                continue
                
        self._queries_cache = focus_queries
        return focus_queries
        
    def get_query(self, slug: str) -> Optional[FocusQuery]:
        """
        Get a specific query by slug.
        
        Args:
            slug: Query slug identifier
            
        Returns:
            FocusQuery object or None if not found
        """
        queries = self.load_queries()
        return queries.get(slug)
        
    def list_query_slugs(self) -> List[str]:
        """
        Get list of all available query slugs.
        
        Returns:
            List of query slug strings
        """
        queries = self.load_queries()
        return list(queries.keys())
        
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise RuntimeError(f"Failed to load YAML file {file_path}: {e}")
            
    def _merge_queries(self, base_queries: Dict[str, Any], adjustments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge base queries with adjustments.
        
        Adjustments can override any field from the base query.
        """
        merged = base_queries.copy()
        
        for slug, adjustment in adjustments.items():
            if slug in merged:
                # Merge adjustment into existing query
                merged[slug].update(adjustment)
            else:
                # New query from adjustments
                merged[slug] = adjustment
                
        return merged
        
    def _convert_to_focus_query(self, slug: str, query_data: Dict[str, Any]) -> FocusQuery:
        """
        Convert raw query data to FocusQuery model.
        
        Args:
            slug: Query slug identifier
            query_data: Raw query data from YAML
            
        Returns:
            FocusQuery object
        """
        # Extract basic fields
        name = query_data.get('title', slug.replace('_', ' ').title())
        description = query_data.get('description', '')
        sql = query_data.get('sql', '')
        
        if not sql:
            raise ValueError(f"Query '{slug}' has no SQL content")
            
        # Replace table references with ClickHouse view names
        normalized_sql = self._normalize_table_references(sql)
        
        # Extract parameters from SQL
        parameters = self._extract_parameters(normalized_sql)
        
        # Extract additional metadata
        category = query_data.get('category')
        tags = query_data.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
            
        return FocusQuery(
            slug=slug,
            name=name,
            description=description,
            sql=normalized_sql,
            parameters=parameters,
            category=category,
            tags=tags
        )
        
    def _normalize_table_references(self, sql: str) -> str:
        """
        Replace FOCUS table references with ClickHouse view names.
        
        Replaces:
        - focus_data_table -> focus_data_table (view)
        - Any other FOCUS table references as needed
        """
        # Replace focus_data_table with the actual view name
        # The view should already exist from the DDL generation step
        normalized_sql = sql.replace('focus_data_table', 'focus_data_table')
        
        # Add any other table reference replacements as needed
        # For example, if there are contract commitment references:
        normalized_sql = normalized_sql.replace('focus_contract_commitment_table', 'focus_contract_commitment_view')
        
        return normalized_sql
        
    def _extract_parameters(self, sql: str) -> List[str]:
        """
        Extract parameter names from SQL query.
        
        Handles both positional (?) and named (:param) parameters.
        For positional parameters, assumes standard order: start_date, end_date, ...
        
        Args:
            sql: SQL query string
            
        Returns:
            List of parameter names
        """
        parameters = []
        
        # Find positional parameters (?)
        positional_count = sql.count('?')
        
        # Find named parameters (:param_name)
        named_params = re.findall(r':(\w+)', sql)
        
        if positional_count > 0:
            # Standard parameter mapping for FOCUS queries
            # Most queries expect start_date and end_date as first two parameters
            param_names = ['start_date', 'end_date']
            
            # Add additional positional parameters if needed
            for i in range(2, positional_count):
                param_names.append(f'param_{i + 1}')
                
            parameters.extend(param_names[:positional_count])
            
        if named_params:
            parameters.extend(named_params)
            
        # Remove duplicates while preserving order
        seen = set()
        unique_parameters = []
        for param in parameters:
            if param not in seen:
                seen.add(param)
                unique_parameters.append(param)
                
        return unique_parameters


class FocusQueryParameterExtractor:
    """
    Utility class for extracting and analyzing query parameters.
    """
    
    @staticmethod
    def analyze_query_parameters(sql: str) -> Dict[str, Any]:
        """
        Analyze SQL query to extract parameter information.
        
        Returns:
            Dictionary with parameter analysis results
        """
        analysis = {
            'positional_count': sql.count('?'),
            'named_parameters': re.findall(r':(\w+)', sql),
            'has_date_filters': bool(re.search(r'(ChargePeriodStart|ChargePeriodEnd|BillingPeriodStart|BillingPeriodEnd)', sql, re.IGNORECASE)),
            'table_references': re.findall(r'FROM\s+(\w+)', sql, re.IGNORECASE),
            'json_extractions': re.findall(r'JSONExtractString\([^)]+\)', sql, re.IGNORECASE)
        }
        
        return analysis
        
    @staticmethod
    def suggest_parameter_types(parameters: List[str]) -> Dict[str, str]:
        """
        Suggest data types for query parameters based on naming conventions.
        
        Args:
            parameters: List of parameter names
            
        Returns:
            Dictionary mapping parameter names to suggested types
        """
        type_suggestions = {}
        
        for param in parameters:
            param_lower = param.lower()
            
            if 'date' in param_lower:
                type_suggestions[param] = 'date'
            elif 'time' in param_lower:
                type_suggestions[param] = 'datetime'
            elif param_lower in ['limit', 'offset', 'count']:
                type_suggestions[param] = 'int'
            elif param_lower in ['cost', 'amount', 'price'] or any(x in param_lower for x in ['cost', 'amount', 'price']):
                type_suggestions[param] = 'decimal'
            else:
                type_suggestions[param] = 'string'
                
        return type_suggestions