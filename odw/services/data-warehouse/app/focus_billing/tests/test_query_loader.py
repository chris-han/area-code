"""
Tests for FOCUS Query Loader and Parameter Handler

Tests the query loading, parsing, and parameter handling functionality.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

from ..query_loader import FocusQueryLoader, FocusQueryParameterExtractor
from ..query_executor import FocusQueryParameterHandler, ParameterValidationError
from ..models import FocusQuery
from ..config import FocusBillingConfig


class TestFocusQueryLoader:
    """Test FOCUS query loading and parsing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.queries_dir = Path(self.temp_dir) / "resources" / "queries"
        self.queries_dir.mkdir(parents=True)
        
        # Create test query files
        self.base_queries = {
            'test_query_1': {
                'title': 'Test Query 1',
                'slug': 'test-query-1',
                'description': 'A test query',
                'sql': 'SELECT * FROM focus_data_table WHERE ChargePeriodStart >= ? AND ChargePeriodEnd < ?'
            },
            'test_query_2': {
                'title': 'Test Query 2',
                'slug': 'test-query-2',
                'description': 'Another test query',
                'sql': 'SELECT ServiceName, SUM(BilledCost) FROM focus_data_table WHERE ServiceName = ? GROUP BY ServiceName'
            }
        }
        
        self.adjustments = {
            'test_query_1': {
                'fix_comment': 'Updated for ClickHouse compatibility',
                'sql': 'SELECT * FROM focus_data_table WHERE ChargePeriodStart >= ? AND ChargePeriodEnd < ? ORDER BY ChargePeriodStart'
            }
        }
        
        # Write test files
        with open(self.queries_dir / "focus_use_cases.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(self.base_queries, f)
            
        with open(self.queries_dir / "focus_use_cases_adjustments.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(self.adjustments, f)
            
        # Create config pointing to temp directory
        self.config = FocusBillingConfig(
            focus_data_root=self.temp_dir,
            focus_queries_root=str(self.queries_dir)
        )
        self.loader = FocusQueryLoader(self.config)
        
    def test_load_queries_success(self):
        """Test successful query loading."""
        queries = self.loader.load_queries()
        
        assert len(queries) == 2
        assert 'test_query_1' in queries
        assert 'test_query_2' in queries
        
        # Check that adjustment was applied
        query1 = queries['test_query_1']
        assert 'ORDER BY ChargePeriodStart' in query1.sql
        
    def test_query_parameter_extraction(self):
        """Test parameter extraction from SQL."""
        queries = self.loader.load_queries()
        
        query1 = queries['test_query_1']
        assert query1.parameters == ['start_date', 'end_date']
        
        query2 = queries['test_query_2']
        assert query2.parameters == ['start_date']  # First positional parameter
        
    def test_get_query_by_slug(self):
        """Test retrieving specific query by slug."""
        query = self.loader.get_query('test_query_1')
        
        assert query is not None
        assert query.slug == 'test_query_1'
        assert query.name == 'Test Query 1'
        
    def test_get_nonexistent_query(self):
        """Test retrieving non-existent query."""
        query = self.loader.get_query('nonexistent')
        assert query is None
        
    def test_list_query_slugs(self):
        """Test listing all query slugs."""
        slugs = self.loader.list_query_slugs()
        
        assert len(slugs) == 2
        assert 'test_query_1' in slugs
        assert 'test_query_2' in slugs

    def test_yaml_parsing_success(self):
        """Test successful YAML parsing."""
        # Test loading base queries file
        base_file = self.queries_dir / "focus_use_cases.yaml"
        result = self.loader._load_yaml_file(base_file)
        
        assert isinstance(result, dict)
        assert 'test_query_1' in result
        assert result['test_query_1']['title'] == 'Test Query 1'
        
    def test_yaml_parsing_empty_file(self):
        """Test parsing empty YAML file."""
        empty_file = self.queries_dir / "empty.yaml"
        with open(empty_file, 'w', encoding='utf-8') as f:
            f.write('')
            
        result = self.loader._load_yaml_file(empty_file)
        assert result == {}
        
    def test_yaml_parsing_invalid_file(self):
        """Test parsing invalid YAML file."""
        invalid_file = self.queries_dir / "invalid.yaml"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write('invalid: yaml: content: [')
            
        with pytest.raises(RuntimeError) as exc_info:
            self.loader._load_yaml_file(invalid_file)
        assert 'Failed to load YAML file' in str(exc_info.value)
        
    def test_model_conversion_success(self):
        """Test successful conversion to FocusQuery model."""
        query_data = {
            'title': 'Test Query',
            'description': 'A test query for validation',
            'sql': 'SELECT * FROM focus_data_table WHERE ChargePeriodStart >= ?',
            'category': 'billing',
            'tags': ['test', 'validation']
        }
        
        result = self.loader._convert_to_focus_query('test_slug', query_data)
        
        assert result.slug == 'test_slug'
        assert result.name == 'Test Query'
        assert result.description == 'A test query for validation'
        assert result.category == 'billing'
        assert result.tags == ['test', 'validation']
        assert result.parameters == ['start_date']
        
    def test_model_conversion_missing_sql(self):
        """Test model conversion with missing SQL."""
        query_data = {
            'title': 'Test Query',
            'description': 'A test query'
        }
        
        with pytest.raises(ValueError) as exc_info:
            self.loader._convert_to_focus_query('test_slug', query_data)
        assert 'has no SQL content' in str(exc_info.value)
        
    def test_model_conversion_string_tags(self):
        """Test model conversion with string tags (should convert to list)."""
        query_data = {
            'title': 'Test Query',
            'sql': 'SELECT * FROM focus_data_table',
            'tags': 'single_tag'
        }
        
        result = self.loader._convert_to_focus_query('test_slug', query_data)
        assert result.tags == ['single_tag']


class TestFocusQueryParameterExtractor:
    """Test parameter extraction utilities."""
    
    def test_analyze_query_parameters(self):
        """Test query parameter analysis."""
        sql = """
        SELECT * FROM focus_data_table 
        WHERE ChargePeriodStart >= ? 
        AND ChargePeriodEnd < ?
        AND JSONExtractString(Tags, '$.Application') = ?
        """
        
        analysis = FocusQueryParameterExtractor.analyze_query_parameters(sql)
        
        assert analysis['positional_count'] == 3
        assert analysis['has_date_filters'] is True
        assert 'focus_data_table' in analysis['table_references']
        assert len(analysis['json_extractions']) == 1
        
    def test_analyze_query_parameters_named_params(self):
        """Test analysis with named parameters."""
        sql = """
        SELECT ServiceName, SUM(BilledCost) 
        FROM focus_data_table 
        WHERE ChargePeriodStart >= :start_date 
        AND ServiceName = :service_name
        """
        
        analysis = FocusQueryParameterExtractor.analyze_query_parameters(sql)
        
        assert analysis['positional_count'] == 0
        assert analysis['named_parameters'] == ['start_date', 'service_name']
        assert analysis['has_date_filters'] is True
        
    def test_analyze_query_parameters_no_params(self):
        """Test analysis with no parameters."""
        sql = "SELECT COUNT(*) FROM focus_data_table"
        
        analysis = FocusQueryParameterExtractor.analyze_query_parameters(sql)
        
        assert analysis['positional_count'] == 0
        assert analysis['named_parameters'] == []
        assert analysis['has_date_filters'] is False
        
    def test_suggest_parameter_types(self):
        """Test parameter type suggestions."""
        parameters = ['start_date', 'end_date', 'service_name', 'limit', 'total_cost']
        
        suggestions = FocusQueryParameterExtractor.suggest_parameter_types(parameters)
        
        assert suggestions['start_date'] == 'date'
        assert suggestions['end_date'] == 'date'
        assert suggestions['service_name'] == 'string'
        assert suggestions['limit'] == 'int'
        assert suggestions['total_cost'] == 'decimal'
        
    def test_suggest_parameter_types_edge_cases(self):
        """Test parameter type suggestions for edge cases."""
        parameters = ['created_time', 'count', 'unit_price', 'description']
        
        suggestions = FocusQueryParameterExtractor.suggest_parameter_types(parameters)
        
        assert suggestions['created_time'] == 'datetime'
        assert suggestions['count'] == 'int'
        assert suggestions['unit_price'] == 'decimal'
        assert suggestions['description'] == 'string'


class TestFocusQueryParameterHandler:
    """Test query parameter validation and handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = FocusQueryParameterHandler()
        
        self.test_query = FocusQuery(
            slug='test_query',
            name='Test Query',
            description='A test query',
            sql='SELECT * FROM focus_data_table WHERE ChargePeriodStart >= ? AND ChargePeriodEnd < ?',
            parameters=['start_date', 'end_date']
        )
        
    def test_validate_parameters_success(self):
        """Test successful parameter validation."""
        raw_params = {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }
        
        prepared_sql, validated_params = self.handler.validate_and_prepare_parameters(
            self.test_query, raw_params
        )
        
        assert ':start_date' in prepared_sql
        assert ':end_date' in prepared_sql
        assert '?' not in prepared_sql
        
        assert isinstance(validated_params['start_date'], date)
        assert isinstance(validated_params['end_date'], date)
        
    def test_validate_parameters_missing(self):
        """Test validation with missing parameters."""
        raw_params = {'start_date': '2024-01-01'}  # Missing end_date
        
        with pytest.raises(ParameterValidationError) as exc_info:
            self.handler.validate_and_prepare_parameters(self.test_query, raw_params)
            
        assert 'Missing required parameters' in str(exc_info.value)
        assert 'end_date' in str(exc_info.value)
        
    def test_coerce_date_types(self):
        """Test date type coercion."""
        # String date
        result = self.handler._coerce_to_date('2024-01-01')
        assert result == date(2024, 1, 1)
        
        # Date object
        input_date = date(2024, 1, 1)
        result = self.handler._coerce_to_date(input_date)
        assert result == input_date
        
        # Datetime object
        input_datetime = datetime(2024, 1, 1, 12, 0, 0)
        result = self.handler._coerce_to_date(input_datetime)
        assert result == date(2024, 1, 1)
        
    def test_coerce_invalid_date(self):
        """Test invalid date coercion."""
        with pytest.raises(ValueError):
            self.handler._coerce_to_date('invalid-date')
            
    def test_coerce_numeric_types(self):
        """Test numeric type coercion."""
        # Integer
        assert self.handler._coerce_to_int('123') == 123
        assert self.handler._coerce_to_int(123.0) == 123
        
        # Decimal
        result = self.handler._coerce_to_decimal('123.45')
        assert result == Decimal('123.45')
        
        result = self.handler._coerce_to_decimal(123.45)
        assert result == Decimal('123.45')
        
    def test_convert_positional_to_named_parameters(self):
        """Test conversion from positional to named parameters."""
        sql = "SELECT * FROM table WHERE col1 = ? AND col2 = ?"
        parameters = ['param1', 'param2']
        
        result = self.handler._convert_to_named_parameters(sql, parameters)
        
        expected = "SELECT * FROM table WHERE col1 = :param1 AND col2 = :param2"
        assert result == expected
        
    def test_parameter_validation_edge_cases(self):
        """Test parameter validation edge cases."""
        # None values
        result = self.handler._coerce_parameter_type('test_param', None)
        assert result is None
        
        # Different parameter naming patterns
        assert isinstance(self.handler._coerce_parameter_type('created_date', '2024-01-01'), date)
        assert isinstance(self.handler._coerce_parameter_type('row_count', '100'), int)
        assert isinstance(self.handler._coerce_parameter_type('unit_cost', '12.34'), Decimal)
        assert isinstance(self.handler._coerce_parameter_type('service_name', 'compute'), str)


class TestFocusQueryNormalization:
    """Test query normalization and table reference replacement."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = FocusQueryLoader()
        
    def test_normalize_table_references_basic(self):
        """Test basic table reference normalization."""
        sql = "SELECT * FROM focus_data_table WHERE BilledCost > 0"
        
        result = self.loader._normalize_table_references(sql)
        
        # Should remain the same as focus_data_table is the correct view name
        assert result == sql
        
    def test_normalize_table_references_contract_commitment(self):
        """Test contract commitment table reference normalization."""
        sql = "SELECT * FROM focus_contract_commitment_table WHERE CommittedCost > 0"
        
        result = self.loader._normalize_table_references(sql)
        
        expected = "SELECT * FROM focus_contract_commitment_view WHERE CommittedCost > 0"
        assert result == expected
        
    def test_normalize_table_references_multiple(self):
        """Test normalization with multiple table references."""
        sql = """
        SELECT c.*, d.BilledCost 
        FROM focus_contract_commitment_table c
        JOIN focus_data_table d ON c.BillingAccountID = d.BillingAccountID
        """
        
        result = self.loader._normalize_table_references(sql)
        
        assert 'focus_contract_commitment_view' in result
        assert 'focus_data_table' in result
        
    def test_extract_parameters_positional(self):
        """Test parameter extraction from positional parameters."""
        sql = "SELECT * FROM focus_data_table WHERE ChargePeriodStart >= ? AND ChargePeriodEnd < ?"
        
        result = self.loader._extract_parameters(sql)
        
        assert result == ['start_date', 'end_date']
        
    def test_extract_parameters_named(self):
        """Test parameter extraction from named parameters."""
        sql = "SELECT * FROM focus_data_table WHERE ServiceName = :service AND RegionName = :region"
        
        result = self.loader._extract_parameters(sql)
        
        assert result == ['service', 'region']
        
    def test_extract_parameters_mixed(self):
        """Test parameter extraction with mixed parameter types."""
        sql = "SELECT * FROM focus_data_table WHERE ChargePeriodStart >= ? AND ServiceName = :service"
        
        result = self.loader._extract_parameters(sql)
        
        assert 'start_date' in result
        assert 'service' in result
        assert len(result) == 2
        
    def test_extract_parameters_duplicates(self):
        """Test parameter extraction removes duplicates."""
        sql = "SELECT * FROM focus_data_table WHERE ServiceName = :service OR ServiceName = :service"
        
        result = self.loader._extract_parameters(sql)
        
        assert result == ['service']
        
    def test_extract_parameters_many_positional(self):
        """Test parameter extraction with many positional parameters."""
        sql = "SELECT * FROM focus_data_table WHERE col1 = ? AND col2 = ? AND col3 = ? AND col4 = ?"
        
        result = self.loader._extract_parameters(sql)
        
        expected = ['start_date', 'end_date', 'param_3', 'param_4']
        assert result == expected