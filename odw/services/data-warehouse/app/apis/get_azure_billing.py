from moose_lib import ConsumptionApi, EgressConfig
from pydantic import BaseModel
from typing import Optional, List
# An API to retrieve Azure billing data from the moose-azure-billing ClickHouse table.
# For more information on consumption apis, see: https://docs.fiveonefour.com/moose/building/consumption-apis.

class AzureBillingQuery(BaseModel):
    subscription_id: Optional[int] = None
    subscription_guid: Optional[str] = None
    resource_group: Optional[str] = None
    consumed_service: Optional[str] = None
    start_date: Optional[str] = None  # YYYY-MM-DD format
    end_date: Optional[str] = None    # YYYY-MM-DD format
    limit: Optional[int] = 100

class AzureBillingRecord(BaseModel):
    id: str
    account_name: Optional[str] = None
    subscription_id: Optional[int] = None
    subscription_guid: Optional[str] = None
    subscription_name: Optional[str] = None
    date: Optional[str] = None  # Date as string in YYYY-MM-DD format
    product: Optional[str] = None
    meter_category: Optional[str] = None
    meter_sub_category: Optional[str] = None
    meter_name: Optional[str] = None
    consumed_quantity: Optional[float] = None
    resource_rate: Optional[float] = None
    extended_cost: Optional[float] = None
    resource_location: Optional[str] = None
    consumed_service: Optional[str] = None
    instance_id: str
    resource_group: Optional[str] = None
    extended_cost_tax: Optional[float] = None
    resource_name: Optional[str] = None
    transform_timestamp: str

class AzureBillingResponse(BaseModel):
    items: List[AzureBillingRecord] = []
    total: int = 0

def get_azure_billing_data(client, params: AzureBillingQuery) -> AzureBillingResponse:
    """
    Retrieve Azure billing data from the moose-azure-billing table.
    
    Args:
        client: Database client for executing queries
        params: Contains query parameters for filtering
        
    Returns:
        AzureBillingResponse object containing billing records
    """
    
    try:
        # Build the base query
        query = """
        SELECT 
            id,
            account_name,
            subscription_id,
            subscription_guid,
            subscription_name,
            date,
            product,
            meter_category,
            meter_sub_category,
            meter_name,
            consumed_quantity,
            resource_rate,
            extended_cost,
            resource_location,
            consumed_service,
            instance_id,
            resource_group,
            extended_cost_tax,
            resource_name,
            transform_timestamp
        FROM `moose-azure-billing`
        WHERE 1=1
        """
        
        query_params = {}
        
        # Add filters based on parameters
        if params.subscription_id:
            query += " AND subscription_id = {subscription_id}"
            query_params["subscription_id"] = params.subscription_id
            
        if params.subscription_guid:
            query += " AND subscription_guid = {subscription_guid}"
            query_params["subscription_guid"] = params.subscription_guid
            
        if params.resource_group:
            query += " AND resource_group = {resource_group}"
            query_params["resource_group"] = params.resource_group
            
        if params.consumed_service:
            query += " AND consumed_service = {consumed_service}"
            query_params["consumed_service"] = params.consumed_service
            
        if params.start_date:
            query += " AND date >= {start_date}"
            query_params["start_date"] = params.start_date
            
        if params.end_date:
            query += " AND date <= {end_date}"
            query_params["end_date"] = params.end_date
        
        # Add ordering and limit
        query += " ORDER BY date DESC, extended_cost DESC"
        
        if params.limit:
            query += " LIMIT {limit}"
            query_params["limit"] = params.limit
        
        # Execute the query
        result = client.query.execute(query, query_params)
        
        if not result:
            return AzureBillingResponse(items=[], total=0)
        
        # Convert results to response models
        items = []
        for row in result:
            items.append(AzureBillingRecord(**row))
        
        return AzureBillingResponse(
            items=items,
            total=len(items)
        )
        
    except Exception as e:
        # Return empty response on error
        return AzureBillingResponse(items=[], total=0)

# Create the consumption API
get_azure_billing_api = ConsumptionApi[AzureBillingQuery, AzureBillingResponse](
    "getAzureBilling",
    query_function=get_azure_billing_data,
    source="moose-azure-billing",
    config=EgressConfig()
)