"""
Azure Billing Connector Package

This package contains all components for the Azure Enterprise Agreement (EA) 
billing data connector, including API client, data transformation, resource 
tracking, and error handling.
"""

# Lazy imports to avoid circular import issues
def _get_connector_classes():
    import azure_billing.azure_billing_connector as connector_module
    return (
        connector_module.AzureBillingConnector,
        connector_module.AzureBillingConnectorConfig,
        connector_module.AzureBillingDetail,
        connector_module.AzureApiConfig,
        connector_module.ProcessingConfig,
        connector_module.MemoryMonitor
    )

def _get_api_client():
    import azure_billing.azure_ea_api_client as api_module
    return api_module.AzureEAApiClient

def _get_transformer():
    import azure_billing.azure_billing_transformer as transformer_module
    return transformer_module.AzureBillingTransformer

def _get_tracking_engine():
    import azure_billing.resource_tracking_engine as tracking_module
    return tracking_module.ResourceTrackingEngine

def _get_error_handler():
    import azure_billing.error_handler as error_module
    return error_module.ErrorHandler, error_module.ErrorType, error_module.ErrorSeverity

def _get_workflow_classes():
    import azure_billing.extract_azure_billing as workflow_module
    return (
        workflow_module.AzureBillingWorkflowConfig,
        workflow_module.extract_azure_billing_task,
        workflow_module.extract_azure_billing_monthly
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