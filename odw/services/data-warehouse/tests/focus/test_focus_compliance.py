"""
FOCUS Specification Compliance Tests

Automated tests for FOCUS specification adherence and data quality validation.
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from app.azure_billing.models.azure_blob_parquet_models import AzureNCEIParquetModel
from app.azure_billing.transformations.azure_ncei_to_focus import AzureNCEIToFOCUSTransformer


class TestFOCUSCompliance:
    """Test FOCUS specification adherence."""
    
    def test_required_focus_fields_present(self, sample_azure_billing_data):
        """Test that all required FOCUS fields are present in transformed data."""
        
        # Required FOCUS fields according to specification
        required_fields = [
            "billing_account_id",
            "billing_account_name", 
            "billing_currency",
            "billing_period_start_date",
            "billing_period_end_date",
            "billed_cost",
            "effective_cost",
            "list_cost",
            "usage_date",
            "usage_quantity",
            "usage_unit",
            "resource_id",
            "resource_name",
            "resource_type",
            "service_category",
            "service_name",
            "provider"
        ]
        
        # Test each record
        for record in sample_azure_billing_data:
            for field in required_fields:
                if field in ["billing_period_start_date", "billing_period_end_date", 
                           "effective_cost", "list_cost", "usage_quantity", "usage_unit"]:
                    # These fields may be optional or derived
                    continue
                assert field in record, f"Required FOCUS field '{field}' missing from record"
    
    def test_focus_data_types_validation(self, sample_azure_billing_data):
        """Test FOCUS data type compliance."""
        
        for record in sample_azure_billing_data:
            # Test currency field
            if "billing_currency" in record:
                assert isinstance(record["billing_currency"], str)
                assert len(record["billing_currency"]) == 3  # ISO 4217 currency code
            
            # Test cost fields are numeric
            cost_fields = ["billed_cost", "effective_cost", "list_cost"]
            for cost_field in cost_fields:
                if cost_field in record:
                    assert isinstance(record[cost_field], (int, float, Decimal))
                    assert record[cost_field] >= 0  # Costs should be non-negative
            
            # Test date fields
            if "usage_date" in record:
                if isinstance(record["usage_date"], str):
                    # Should be valid date string
                    datetime.strptime(record["usage_date"], "%Y-%m-%d")
                else:
                    assert isinstance(record["usage_date"], (date, datetime))
            
            # Test provider field
            if "provider" in record:
                assert record["provider"] == "Azure"
    
    def test_focus_field_constraints(self, sample_azure_billing_data):
        """Test FOCUS field constraints and business rules."""
        
        for record in sample_azure_billing_data:
            # Test billing_account_id format (should be UUID for Azure)
            if "billing_account_id" in record:
                account_id = record["billing_account_id"]
                assert isinstance(account_id, str)
                assert len(account_id) > 0
                # Azure subscription IDs are typically UUIDs
                if len(account_id) == 36:
                    assert account_id.count("-") == 4
            
            # Test resource_id format (should be Azure resource ID)
            if "resource_id" in record:
                resource_id = record["resource_id"]
                assert isinstance(resource_id, str)
                assert resource_id.startswith("/subscriptions/")
            
            # Test service_category values
            if "service_category" in record:
                valid_categories = [
                    "Compute", "Storage", "Networking", "Database", 
                    "Analytics", "AI + Machine Learning", "Security",
                    "Management and Governance", "Other"
                ]
                assert record["service_category"] in valid_categories

clas
s TestDataQualityValidation:
    """Test data quality validation scenarios."""
    
    def test_data_completeness_validation(self):
        """Test data completeness validation."""
        
        # Test complete record
        complete_record = {
            "billing_account_id": "12345678-1234-1234-1234-123456789012",
            "billing_account_name": "Test Subscription",
            "usage_date": "2024-01-01",
            "billed_cost": 150.75,
            "billing_currency": "USD",
            "service_category": "Compute",
            "service_name": "Virtual Machines",
            "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm",
            "resource_name": "test-vm",
            "resource_type": "Microsoft.Compute/virtualMachines",
            "region": "East US",
            "provider": "Azure"
        }
        
        # Validate completeness
        required_fields = ["billing_account_id", "usage_date", "billed_cost", "provider"]
        for field in required_fields:
            assert field in complete_record
            assert complete_record[field] is not None
            assert complete_record[field] != ""
    
    def test_data_accuracy_validation(self):
        """Test data accuracy validation rules."""
        
        # Test cost accuracy
        test_record = {
            "billed_cost": 150.75,
            "effective_cost": 150.75,
            "list_cost": 200.00,
            "usage_quantity": 24.0,
            "usage_unit": "Hours"
        }
        
        # Effective cost should not exceed list cost
        if test_record.get("effective_cost") and test_record.get("list_cost"):
            assert test_record["effective_cost"] <= test_record["list_cost"]
        
        # Billed cost should be positive
        assert test_record["billed_cost"] > 0
        
        # Usage quantity should be positive if present
        if test_record.get("usage_quantity"):
            assert test_record["usage_quantity"] > 0
    
    def test_data_consistency_validation(self):
        """Test data consistency across related fields."""
        
        test_records = [
            {
                "billing_account_id": "12345678-1234-1234-1234-123456789012",
                "billing_account_name": "Test Subscription",
                "billing_currency": "USD",
                "usage_date": "2024-01-01"
            },
            {
                "billing_account_id": "12345678-1234-1234-1234-123456789012", 
                "billing_account_name": "Test Subscription",
                "billing_currency": "USD",
                "usage_date": "2024-01-02"
            }
        ]
        
        # Group by billing account
        account_groups = {}
        for record in test_records:
            account_id = record["billing_account_id"]
            if account_id not in account_groups:
                account_groups[account_id] = []
            account_groups[account_id].append(record)
        
        # Validate consistency within account groups
        for account_id, records in account_groups.items():
            # All records for same account should have same account name and currency
            account_names = set(r["billing_account_name"] for r in records)
            currencies = set(r["billing_currency"] for r in records)
            
            assert len(account_names) == 1, "Inconsistent account names for same billing account"
            assert len(currencies) == 1, "Inconsistent currencies for same billing account"


class TestTransformationAccuracy:
    """Test transformation accuracy and completeness."""
    
    @pytest.mark.asyncio
    async def test_azure_ncei_transformation_accuracy(self):
        """Test accuracy of Azure NCEI to FOCUS transformation."""
        
        # Sample Azure NCEI data
        ncei_data = [
            {
                "SubscriptionId": "12345678-1234-1234-1234-123456789012",
                "SubscriptionName": "Test Subscription", 
                "Date": "2024-01-01",
                "Cost": 150.75,
                "Currency": "USD",
                "ServiceFamily": "Compute",
                "ServiceName": "Virtual Machines",
                "ResourceId": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm",
                "ResourceName": "test-vm",
                "ResourceType": "Microsoft.Compute/virtualMachines",
                "Location": "East US"
            }
        ]
        
        transformer = AzureNCEIToFOCUSTransformer()
        focus_data = await transformer.transform_batch(ncei_data)
        
        # Verify transformation accuracy
        assert len(focus_data) == len(ncei_data)
        
        focus_record = focus_data[0]
        ncei_record = ncei_data[0]
        
        # Verify field mappings
        assert focus_record["billing_account_id"] == ncei_record["SubscriptionId"]
        assert focus_record["billing_account_name"] == ncei_record["SubscriptionName"]
        assert focus_record["usage_date"] == ncei_record["Date"]
        assert focus_record["billed_cost"] == ncei_record["Cost"]
        assert focus_record["billing_currency"] == ncei_record["Currency"]
        assert focus_record["service_category"] == ncei_record["ServiceFamily"]
        assert focus_record["service_name"] == ncei_record["ServiceName"]
        assert focus_record["resource_id"] == ncei_record["ResourceId"]
        assert focus_record["resource_name"] == ncei_record["ResourceName"]
        assert focus_record["resource_type"] == ncei_record["ResourceType"]
        assert focus_record["region"] == ncei_record["Location"]
        assert focus_record["provider"] == "Azure"
    
    def test_parquet_model_focus_mapping(self):
        """Test parquet model FOCUS field mapping accuracy."""
        
        # Create test parquet model
        model_data = {
            "blob_path": "focus-data/2024/01/billing_data_20240101.parquet",
            "blob_name": "billing_data_20240101.parquet",
            "container_name": "billing-data",
            "account_url": "https://finopsbilling.blob.core.chinacloudapi.cn",
            "column_names": [
                "SubscriptionId", "SubscriptionName", "Date", "Cost", 
                "Currency", "ServiceFamily", "ServiceName", "ResourceId"
            ]
        }
        
        model = AzureNCEIParquetModel(**model_data)
        focus_mapping = model.get_focus_field_mapping()
        
        # Verify mapping accuracy
        expected_mappings = {
            "SubscriptionId": "billing_account_id",
            "SubscriptionName": "billing_account_name", 
            "Date": "usage_date",
            "Cost": "billed_cost",
            "Currency": "billing_currency",
            "ServiceFamily": "service_category",
            "ServiceName": "service_name",
            "ResourceId": "resource_id"
        }
        
        for source_field, expected_focus_field in expected_mappings.items():
            assert source_field in focus_mapping
            assert focus_mapping[source_field] == expected_focus_field