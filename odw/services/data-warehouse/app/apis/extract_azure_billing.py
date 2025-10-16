from moose_lib import ConsumptionApi, EgressConfig
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

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
        # Set default dates if not provided (last month)
        if not params.start_date or not params.end_date:
            today = datetime.now()
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            start_date = last_day_last_month.replace(day=1)
            end_date = last_day_last_month
            
            # Create new params with default dates
            params = AzureBillingExtractParams(
                batch_size=params.batch_size,
                fail_percentage=params.fail_percentage,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                azure_enrollment_number=params.azure_enrollment_number,
                azure_api_key=params.azure_api_key
            )
        
        # Trigger the actual Temporal workflow
        result = client.workflow.execute("azure-billing-workflow", params)
        
        return AzureBillingExtractResponse(
            message=f"Azure billing extraction triggered for period {params.start_date} to {params.end_date}",
            workflow_id=result.get("workflow_id", "azure-billing-workflow-" + datetime.now().strftime('%Y%m%d-%H%M%S')),
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