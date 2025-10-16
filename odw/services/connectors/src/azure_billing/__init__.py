"""
Azure Billing Connector Package

This package contains all components for the Azure Enterprise Agreement (EA) 
billing data connector, including API client, data transformation, resource 
tracking, and error handling.
"""

# Lazy imports to avoid circular import issues
def _get_connector_classes():
    from .azure_billing_connector import (
        AzureBillingConnector,
        AzureBillingConnectorConfig,
        AzureBillingDetail,
        AzureApiConfig,
        ProcessingConfig,
        MemoryMonitor
    )
    return (
        AzureBillingConnector,
        AzureBillingConnectorConfig,
        AzureBillingDetail,
        AzureApiConfig,
        ProcessingConfig,
        MemoryMonitor
    )

def _get_api_client():
    from .azure_ea_api_client import AzureEAApiClient
    return AzureEAApiClient

def _get_transformer():
    from .azure_billing_transformer import AzureBillingTransformer
    return AzureBillingTransformer

def _get_tracking_engine():
    from .resource_tracking_engine import ResourceTrackingEngine
    return ResourceTrackingEngine

def _get_error_handler():
    from .error_handler import ErrorHandler, ErrorType, ErrorSeverity
    return ErrorHandler, ErrorType, ErrorSeverity

def _get_workflow_classes():
    from .extract_azure_billing import (
        AzureBillingWorkflowConfig,
        extract_azure_billing_task,
        extract_azure_billing_monthly
    )
    return (
        AzureBillingWorkflowConfig,
        extract_azure_billing_task,
        extract_azure_billing_monthly
    )

# Make classes available at package level through lazy loading
def __getattr__(name):
    if name == 'AzureBillingConnector':
        return _get_connector_classes()[0]
    elif name == 'AzureBillingConnectorConfig':
        return _get_connector_classes()[1]
    elif name == 'AzureBillingDetail':
        return _get_connector_classes()[2]
    elif name == 'AzureApiConfig':
        return _get_connector_classes()[3]
    elif name == 'ProcessingConfig':
        return _get_connector_classes()[4]
    elif name == 'MemoryMonitor':
        return _get_connector_classes()[5]
    elif name == 'AzureEAApiClient':
        return _get_api_client()
    elif name == 'AzureBillingTransformer':
        return _get_transformer()
    elif name == 'ResourceTrackingEngine':
        return _get_tracking_engine()
    elif name == 'ErrorHandler':
        return _get_error_handler()[0]
    elif name == 'ErrorType':
        return _get_error_handler()[1]
    elif name == 'ErrorSeverity':
        return _get_error_handler()[2]
    elif name == 'AzureBillingWorkflowConfig':
        return _get_workflow_classes()[0]
    elif name == 'extract_azure_billing_task':
        return _get_workflow_classes()[1]
    elif name == 'extract_azure_billing_monthly':
        return _get_workflow_classes()[2]
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    # Main connector classes
    'AzureBillingConnector',
    'AzureBillingConnectorConfig',
    'AzureBillingDetail',
    'AzureApiConfig',
    'ProcessingConfig',
    'MemoryMonitor',
    
    # API client
    'AzureEAApiClient',
    
    # Data processing
    'AzureBillingTransformer',
    'ResourceTrackingEngine',
    
    # Error handling
    'ErrorHandler',
    'ErrorType',
    'ErrorSeverity',
    
    # Workflow integration
    'AzureBillingWorkflowConfig',
    'extract_azure_billing_task',
    'extract_azure_billing_monthly'
]