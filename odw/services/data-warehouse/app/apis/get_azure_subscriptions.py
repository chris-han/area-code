from moose_lib import ConsumptionApi, EgressConfig
from pydantic import BaseModel
from typing import List, Optional

# An API to retrieve unique Azure subscriptions from the moose_azure_billing ClickHouse table.

class AzureSubscriptionsQuery(BaseModel):
    limit: Optional[int] = 100

class AzureSubscription(BaseModel):
    subscription_id: Optional[int] = None
    subscription_guid: Optional[str] = None
    subscription_name: Optional[str] = None

class AzureSubscriptionsResponse(BaseModel):
    items: List[AzureSubscription] = []
    total: int = 0

def get_azure_subscriptions_data(client, params: AzureSubscriptionsQuery) -> AzureSubscriptionsResponse:
    """
    Retrieve unique Azure subscriptions from the moose_azure_billing table.
    
    Args:
        client: Database client for executing queries
        params: Contains query parameters for limiting results
        
    Returns:
        AzureSubscriptionsResponse object containing subscription list
    """
    
    try:
        # Query for unique subscriptions
        query = """
        SELECT DISTINCT
            subscription_id,
            subscription_guid,
            subscription_name
        FROM `moose_azure_billing`
        WHERE subscription_name IS NOT NULL 
        AND subscription_name != ''
        ORDER BY subscription_name
        """
        
        query_params = {}
        
        if params.limit:
            query += " LIMIT {limit}"
            query_params["limit"] = params.limit
        
        # Execute the query
        result = client.query.execute(query, query_params)
        
        if not result:
            return AzureSubscriptionsResponse(items=[], total=0)
        
        # Convert results to response models
        items = []
        for row in result:
            items.append(AzureSubscription(
                subscription_id=row.get('subscription_id'),
                subscription_guid=row.get('subscription_guid'),
                subscription_name=row.get('subscription_name')
            ))
        
        return AzureSubscriptionsResponse(
            items=items,
            total=len(items)
        )
        
    except Exception as e:
        # Return empty response on error
        return AzureSubscriptionsResponse(items=[], total=0)

# Create the consumption API
get_azure_subscriptions_api = ConsumptionApi[AzureSubscriptionsQuery, AzureSubscriptionsResponse](
    "getAzureSubscriptions",
    query_function=get_azure_subscriptions_data,
    source="moose_azure_billing",
    config=EgressConfig()
)