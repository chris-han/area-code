from moose_lib import ConsumptionApi, EgressConfig
from pydantic import BaseModel
from typing import Optional
import requests
import json

# An API to test Azure EA API connection with provided credentials.

class AzureConnectionTestParams(BaseModel):
    enrollment_number: Optional[str] = None
    api_key: Optional[str] = None
    api_base_url: Optional[str] = "https://ea.azure.cn/rest"

class AzureConnectionTestResponse(BaseModel):
    success: bool
    message: str
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None

def test_azure_connection_function(client, params: AzureConnectionTestParams) -> AzureConnectionTestResponse:
    """
    Test Azure EA API connection with provided credentials.
    
    Args:
        client: Database client (not used for this endpoint)
        params: Contains Azure credentials and connection parameters
        
    Returns:
        AzureConnectionTestResponse with connection test results
    """
    
    # Validate required parameters
    if not params.enrollment_number:
        return AzureConnectionTestResponse(
            success=False,
            message="Enrollment number is required"
        )
    
    if not params.api_key:
        return AzureConnectionTestResponse(
            success=False,
            message="API key is required"
        )
    
    try:
        import time
        start_time = time.time()
        
        # Build the test API URL
        # Test with a simple enrollment details endpoint (same as used in the connector)
        test_url = f"{params.api_base_url}/{params.enrollment_number}/usage-report/paginatedV3?month=2025-09&pageindex=0&fmt=json"
        
        # Prepare headers
        headers = {
            'Authorization': f'bearer {params.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Make the test request with timeout
        response = requests.get(
            test_url,
            headers=headers,
            timeout=120  # 120 second timeout for Azure API
        )
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            return AzureConnectionTestResponse(
                success=True,
                message="Azure EA API connection successful",
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
        elif response.status_code == 401:
            return AzureConnectionTestResponse(
                success=False,
                message="Authentication failed. Please check your API key.",
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
        elif response.status_code == 403:
            return AzureConnectionTestResponse(
                success=False,
                message="Access denied. Please verify your enrollment permissions.",
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
        elif response.status_code == 404:
            return AzureConnectionTestResponse(
                success=False,
                message="Enrollment not found. Please check your enrollment number.",
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
        else:
            return AzureConnectionTestResponse(
                success=False,
                message=f"Connection failed with status {response.status_code}: {response.text[:200]}",
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
            
    except requests.exceptions.Timeout:
        return AzureConnectionTestResponse(
            success=False,
            message="Connection timeout. Please check your network connection and try again."
        )
    except requests.exceptions.ConnectionError:
        return AzureConnectionTestResponse(
            success=False,
            message="Connection error. Please check your network connection and API base URL."
        )
    except Exception as e:
        return AzureConnectionTestResponse(
            success=False,
            message=f"Connection test failed: {str(e)}"
        )

# Create the consumption API
test_azure_connection_api = ConsumptionApi[AzureConnectionTestParams, AzureConnectionTestResponse](
    "test-azure-connection",
    query_function=test_azure_connection_function,
    source="azure_connection_test",  # Virtual source for connection testing
    config=EgressConfig()
)