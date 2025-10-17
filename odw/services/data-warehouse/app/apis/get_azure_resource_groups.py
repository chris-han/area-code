from moose_lib import ConsumptionApi, EgressConfig
from pydantic import BaseModel
from typing import List, Optional

# An API to retrieve unique Azure resource groups from the moose_azure_billing ClickHouse table.

class AzureResourceGroupsQuery(BaseModel):
    subscription_guid: Optional[str] = None
    limit: Optional[int] = 100

class AzureResourceGroup(BaseModel):
    resource_group: str
    subscription_guid: Optional[str] = None
    subscription_name: Optional[str] = None

class AzureResourceGroupsResponse(BaseModel):
    items: List[AzureResourceGroup] = []
    total: int = 0

def get_azure_resource_groups_data(client, params: AzureResourceGroupsQuery) -> AzureResourceGroupsResponse:
    """
    Retrieve unique Azure resource groups from the moose_azure_billing table.
    
    Args:
        client: Database client for executing queries
        params: Contains query parameters for filtering and limiting results
        
    Returns:
        AzureResourceGroupsResponse object containing resource group list
    """
    
    try:
        # Query for unique resource groups
        query = """
        SELECT DISTINCT
            resource_group,
            subscription_guid,
            subscription_name
        FROM `moose_azure_billing`
        WHERE resource_group IS NOT NULL 
        AND resource_group != ''
        """
        
        query_params = {}
        
        # Add subscription filter if provided
        if params.subscription_guid:
            query += " AND subscription_guid = {subscription_guid}"
            query_params["subscription_guid"] = params.subscription_guid
        
        query += " ORDER BY resource_group"
        
        if params.limit:
            query += " LIMIT {limit}"
            query_params["limit"] = params.limit
        
        # Execute the query
        result = client.query.execute(query, query_params)
        
        if not result:
            return AzureResourceGroupsResponse(items=[], total=0)
        
        # Convert results to response models
        items = []
        for row in result:
            items.append(AzureResourceGroup(
                resource_group=row.get('resource_group', ''),
                subscription_guid=row.get('subscription_guid'),
                subscription_name=row.get('subscription_name')
            ))
        
        return AzureResourceGroupsResponse(
            items=items,
            total=len(items)
        )
        
    except Exception as e:
        # Return empty response on error
        return AzureResourceGroupsResponse(items=[], total=0)

# Create the consumption API
get_azure_resource_groups_api = ConsumptionApi[AzureResourceGroupsQuery, AzureResourceGroupsResponse](
    "getAzureResourceGroups",
    query_function=get_azure_resource_groups_data,
    source="moose_azure_billing",
    config=EgressConfig()
)