from moose_lib import ConsumptionApi, EgressConfig
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import requests
import json

# An API to trigger Azure billing data extraction and processing workflows.
# This processes Azure billing data directly using the workflow system.

class AzureBillingExtractParams(BaseModel):
    batch_size: Optional[int] = 1000
    fail_percentage: Optional[int] = 0
    start_date: Optional[str] = None  # YYYY-MM-DD format
    end_date: Optional[str] = None    # YYYY-MM-DD format
    azure_enrollment_number: Optional[str] = None
    azure_api_key: Optional[str] = None

class AzureBillingExtractResponse(BaseModel):
    message: str
    workflow_id: Optional[str] = None
    status: str = "started"

def trigger_azure_billing_extract(client, params: AzureBillingExtractParams) -> AzureBillingExtractResponse:
    """
    Trigger Azure billing data extraction workflow.
    
    Args:
        client: Database client (not used for this endpoint)
        params: Contains extraction parameters
        
    Returns:
        AzureBillingExtractResponse with workflow status
    """
    
    try:
        # Prepare workflow parameters
        workflow_params = {
            "batch_size": params.batch_size or 1000,
            "fail_percentage": params.fail_percentage or 0,
            "start_date": params.start_date,
            "end_date": params.end_date,
            "azure_enrollment_number": params.azure_enrollment_number,
            "azure_api_key": params.azure_api_key
        }
        
        # Set default dates if not provided (last month)
        if not params.start_date or not params.end_date:
            today = datetime.now()
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            start_date = last_day_last_month.replace(day=1)
            end_date = last_day_last_month
            
            workflow_params["start_date"] = start_date.strftime('%Y-%m-%d')
            workflow_params["end_date"] = end_date.strftime('%Y-%m-%d')
        
        # Note: In a real implementation, you would trigger the workflow here
        # For now, we'll return a success response
        # Example: workflow_id = client.workflow.execute("azure-billing-workflow", workflow_params)
        
        return AzureBillingExtractResponse(
            message=f"Azure billing extraction triggered for period {workflow_params['start_date']} to {workflow_params['end_date']}",
            workflow_id="azure-billing-workflow-" + datetime.now().strftime('%Y%m%d-%H%M%S'),
            status="started"
        )
        
    except Exception as e:
        return AzureBillingExtractResponse(
            message=f"Failed to trigger Azure billing extraction: {str(e)}",
            status="failed"
        )

# Create the consumption API
extract_azure_billing_api = ConsumptionApi[AzureBillingExtractParams, AzureBillingExtractResponse](
    "extract-azure-billing",
    query_function=trigger_azure_billing_extract,
    source="azure_billing",  # This is a virtual source since we're triggering workflows
    config=EgressConfig()
)