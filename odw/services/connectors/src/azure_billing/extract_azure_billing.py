"""
Temporal Workflow for Azure Billing Data Extraction

This module provides the Temporal workflow task for extracting Azure billing data
using the AzureBillingConnector and integrating with the existing ingest pipeline.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import connector_factory
import azure_billing.azure_billing_connector as connector_module

ConnectorFactory = connector_factory.ConnectorFactory
ConnectorType = connector_factory.ConnectorType
AzureBillingConnectorConfig = connector_module.AzureBillingConnectorConfig
AzureBillingDetail = connector_module.AzureBillingDetail

logger = logging.getLogger(__name__)


class AzureBillingWorkflowConfig:
    """Configuration for Azure billing extraction workflow"""
    
    def __init__(
        self,
        azure_enrollment_number: str,
        azure_api_key: str,
        start_date: date,
        end_date: date,
        batch_size: int = 1000,
        api_base_url: str = "https://ea.azure.cn/rest",
        enable_failure_simulation: bool = False
    ):
        self.azure_enrollment_number = azure_enrollment_number
        self.azure_api_key = azure_api_key
        self.start_date = start_date
        self.end_date = end_date
        self.batch_size = batch_size
        self.api_base_url = api_base_url
        self.enable_failure_simulation = enable_failure_simulation


def extract_azure_billing_task(config: AzureBillingWorkflowConfig) -> Dict[str, Any]:
    """
    Temporal task for extracting Azure billing data
    
    Args:
        config: Workflow configuration
        
    Returns:
        Dictionary with extraction results and statistics
    """
    try:
        logger.info(f"Starting Azure billing extraction for period: {config.start_date} to {config.end_date}")
        
        # Create connector configuration
        connector_config = AzureBillingConnectorConfig(
            batch_size=config.batch_size,
            start_date=datetime.combine(config.start_date, datetime.min.time()),
            end_date=datetime.combine(config.end_date, datetime.min.time()),
            azure_enrollment_number=config.azure_enrollment_number,
            azure_api_key=config.azure_api_key,
            api_base_url=config.api_base_url
        )
        
        # Create connector using factory
        connector = ConnectorFactory.create(
            ConnectorType.AzureBilling,
            connector_config
        )
        
        # Extract data
        start_time = datetime.now()
        billing_records = connector.extract()
        end_time = datetime.now()
        
        # Calculate statistics
        processing_time = (end_time - start_time).total_seconds()
        record_count = len(billing_records)
        
        logger.info(f"Extraction completed: {record_count} records in {processing_time:.2f} seconds")
        
        # Prepare data for ingest API
        ingest_data = [record.dict() for record in billing_records]
        
        # Simulate ingest API call (replace with actual API call)
        ingest_result = simulate_ingest_api_call(ingest_data, "AzureBillingDetail")
        
        # Return results
        return {
            'success': True,
            'record_count': record_count,
            'processing_time_seconds': processing_time,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'date_range': {
                'start_date': config.start_date.isoformat(),
                'end_date': config.end_date.isoformat()
            },
            'ingest_result': ingest_result,
            'connector_config': {
                'batch_size': config.batch_size,
                'api_base_url': config.api_base_url
            }
        }
        
    except Exception as e:
        logger.error(f"Azure billing extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'date_range': {
                'start_date': config.start_date.isoformat(),
                'end_date': config.end_date.isoformat()
            }
        }


def simulate_ingest_api_call(data: List[Dict[str, Any]], data_type: str) -> Dict[str, Any]:
    """
    Simulate ingest API call (replace with actual implementation)
    
    Args:
        data: List of records to ingest
        data_type: Type of data being ingested
        
    Returns:
        Ingest result dictionary
    """
    try:
        logger.info(f"Simulating ingest API call for {len(data)} {data_type} records")
        
        # Simulate processing time
        import time
        time.sleep(0.1)  # Simulate API call delay
        
        # Simulate success
        return {
            'success': True,
            'records_ingested': len(data),
            'data_type': data_type,
            'ingest_time': datetime.now().isoformat(),
            'message': f'Successfully ingested {len(data)} records'
        }
        
    except Exception as e:
        logger.error(f"Ingest API simulation failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'data_type': data_type,
            'records_attempted': len(data)
        }


def extract_azure_billing_monthly(
    azure_enrollment_number: str,
    azure_api_key: str,
    year: int,
    month: int,
    batch_size: int = 1000
) -> Dict[str, Any]:
    """
    Extract Azure billing data for a specific month
    
    Args:
        azure_enrollment_number: Azure enrollment number
        azure_api_key: Azure EA API key
        year: Year to extract
        month: Month to extract (1-12)
        batch_size: Batch size for processing
        
    Returns:
        Extraction result dictionary
    """
    try:
        # Calculate date range for the month
        start_date = date(year, month, 1)
        
        # Calculate last day of month
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        # Adjust to last day of current month
        from datetime import timedelta
        end_date = date(end_date.year, end_date.month, 1) - timedelta(days=1)
        
        # Create workflow config
        config = AzureBillingWorkflowConfig(
            azure_enrollment_number=azure_enrollment_number,
            azure_api_key=azure_api_key,
            start_date=start_date,
            end_date=end_date,
            batch_size=batch_size
        )
        
        # Execute extraction
        return extract_azure_billing_task(config)
        
    except Exception as e:
        logger.error(f"Monthly extraction failed for {year}-{month:02d}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'year': year,
            'month': month
        }


# Example usage for testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Example configuration (use environment variables in production)
    config = AzureBillingWorkflowConfig(
        azure_enrollment_number="123456789",
        azure_api_key="your-api-key-here",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        batch_size=500
    )
    
    # Run extraction
    result = extract_azure_billing_task(config)
    print(f"Extraction result: {result}")