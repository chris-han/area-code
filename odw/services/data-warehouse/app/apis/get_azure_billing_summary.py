from moose_lib import ConsumptionApi, EgressConfig
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

# An API to retrieve Azure billing summary metrics from the moose-azure-billing ClickHouse table.

class AzureBillingSummaryQuery(BaseModel):
    start_date: Optional[str] = None  # YYYY-MM-DD format
    end_date: Optional[str] = None    # YYYY-MM-DD format

class AzureBillingSummaryResponse(BaseModel):
    total_cost: float = 0.0
    resource_count: int = 0
    subscription_count: int = 0
    last_updated: str = ""
    period_start: str = ""
    period_end: str = ""

def get_azure_billing_summary_data(client, params: AzureBillingSummaryQuery) -> AzureBillingSummaryResponse:
    """
    Retrieve Azure billing summary metrics from the moose-azure-billing table.
    
    Args:
        client: Database client for executing queries
        params: Contains query parameters for date filtering
        
    Returns:
        AzureBillingSummaryResponse object containing summary metrics
    """
    
    try:
        # Set default date range if not provided (last 30 days)
        if not params.start_date or not params.end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
        else:
            start_date_str = params.start_date
            end_date_str = params.end_date
        
        # Query for summary metrics
        summary_query = """
        SELECT 
            SUM(extended_cost) as total_cost,
            COUNT(DISTINCT instance_id) as resource_count,
            COUNT(DISTINCT subscription_guid) as subscription_count,
            MAX(transform_timestamp) as last_updated
        FROM `moose-azure-billing`
        WHERE date >= {start_date} AND date <= {end_date}
        """
        
        query_params = {
            "start_date": start_date_str,
            "end_date": end_date_str
        }
        
        # Execute the query
        result = client.query.execute(summary_query, query_params)
        
        if not result or len(result) == 0:
            return AzureBillingSummaryResponse(
                period_start=start_date_str,
                period_end=end_date_str
            )
        
        row = result[0]
        
        return AzureBillingSummaryResponse(
            total_cost=float(row.get('total_cost', 0) or 0),
            resource_count=int(row.get('resource_count', 0) or 0),
            subscription_count=int(row.get('subscription_count', 0) or 0),
            last_updated=str(row.get('last_updated', '')),
            period_start=start_date_str,
            period_end=end_date_str
        )
        
    except Exception as e:
        # Return default response on error
        return AzureBillingSummaryResponse(
            period_start=params.start_date or "",
            period_end=params.end_date or ""
        )

# Create the consumption API
get_azure_billing_summary_api = ConsumptionApi[AzureBillingSummaryQuery, AzureBillingSummaryResponse](
    "getAzureBillingSummary",
    query_function=get_azure_billing_summary_data,
    source="moose-azure-billing",
    config=EgressConfig()
)