from moose_lib import ConsumptionApi
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
    status: int
    body: str



def trigger_azure_billing_extract(client, params: AzureBillingExtractParams):
    """
    Trigger Azure billing data extraction workflow.
    
    Args:
        client: Database client (not used for this endpoint)
        params: Contains extraction parameters
        
    Returns:
        Direct workflow execution result
    """
    
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
    
    # Trigger the actual Temporal workflow - return direct result like other workflows
    return client.workflow.execute("azure-billing-workflow", params)

# Create the consumption API - simplified like other extract APIs
extract_azure_billing_api = ConsumptionApi[AzureBillingExtractParams, AzureBillingExtractResponse](
    "extract-azure-billing",
    query_function=trigger_azure_billing_extract
)