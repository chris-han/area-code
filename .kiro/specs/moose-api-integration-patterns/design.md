# Design Document

## Overview

This document defines the architectural patterns and implementation guidelines for integrating frontend applications with Moose backend services. It establishes standard practices to prevent common integration issues and ensure consistent, reliable API communication.

## Architecture

### API Integration Layer Architecture

```
Frontend Application
    ├── UI Components
    ├── API Integration Layer
    │   ├── HTTP Client Configuration
    │   ├── Request/Response Handlers
    │   ├── Error Management
    │   └── Timeout Management
    └── Configuration Management
        ├── Port Configuration
        ├── Endpoint Mapping
        └── Environment Settings
```

### Moose Service Architecture

```
Moose Service (Port 4200)
    ├── Consumption APIs (/consumption/*)
    ├── Ingest APIs (/ingest/*)
    ├── Workflow APIs (/consumption/*)
    └── Health Check Endpoints
```

## Components and Interfaces

### 1. HTTP Method Conventions

**GET Endpoints (Data Retrieval & Workflow Triggering)**

- All Moose consumption APIs use GET requests with query parameters
- Examples: `/consumption/getBlobs`, `/consumption/extract-azure-billing`
- Parameters passed as URL query string
- Timeout: 30 seconds for standard operations, 180 seconds for long-running workflows

**POST Endpoints (Data Ingestion)**

- Ingest APIs use POST requests with JSON payloads
- Examples: `/ingest/BlobSource`, `/ingest/AzureBillingDetailSource`
- Data passed as JSON in request body
- Timeout: 300 seconds for large batch operations

### 2. Port Configuration Standards

**Primary Configuration**

```python
CONSUMPTION_API_BASE = "http://localhost:4200/consumption"
WORKFLOW_API_BASE = "http://localhost:4200/consumption"
INGEST_API_BASE = "http://localhost:4200/ingest"
```

**Port Validation Logic**

```python
def validate_moose_service():
    try:
        response = requests.get("http://localhost:4200/health", timeout=5)
        return response.status_code == 200
    except:
        raise MooseServiceUnavailableError("Port 4200 not available")
```

### 3. Request Handler Patterns

**Standard GET Request Pattern**

```python
def make_moose_get_request(endpoint, params=None, timeout=30):
    url = f"{CONSUMPTION_API_BASE}/{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        raise APITimeoutError(f"Request to {endpoint} timed out")
    except requests.RequestException as e:
        raise APIError(f"Request failed: {str(e)}")
```

**Standard POST Request Pattern**

```python
def make_moose_post_request(endpoint, data, timeout=300):
    url = f"{INGEST_API_BASE}/{endpoint}"
    try:
        response = requests.post(url, json=data, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        raise APITimeoutError(f"Request to {endpoint} timed out")
    except requests.RequestException as e:
        raise APIError(f"Request failed: {str(e)}")
```

## Data Models

### API Configuration Model

```python
@dataclass
class MooseAPIConfig:
    base_url: str = "http://localhost:4200"
    consumption_path: str = "/consumption"
    ingest_path: str = "/ingest"
    default_timeout: int = 30
    long_operation_timeout: int = 180
    batch_operation_timeout: int = 300

    def get_consumption_url(self) -> str:
        return f"{self.base_url}{self.consumption_path}"

    def get_ingest_url(self) -> str:
        return f"{self.base_url}{self.ingest_path}"
```

### Error Response Model

```python
@dataclass
class APIErrorResponse:
    error_type: str
    message: str
    user_message: str
    retry_after: Optional[int] = None

    @classmethod
    def from_exception(cls, error: Exception) -> 'APIErrorResponse':
        if isinstance(error, requests.Timeout):
            return cls(
                error_type="timeout",
                message=str(error),
                user_message="Request timed out. Please try again.",
                retry_after=30
            )
        elif isinstance(error, requests.ConnectionError):
            return cls(
                error_type="connection",
                message=str(error),
                user_message="Unable to connect to service. Please check if the service is running."
            )
        # ... other error types
```

## Error Handling

### Error Classification and Handling

**Connection Errors**

- Cause: Service not running on port 4200 or failed to bind to port
- Action: Display service unavailable message, suggest checking service status and restarting if needed
- User Message: "Data service is unavailable. The service may need to be restarted."
- Recovery: Implement automatic service health checks and restart recommendations

**Timeout Errors**

- Cause: Request exceeds configured timeout
- Action: Allow retry with exponential backoff
- User Message: "Request is taking longer than expected. Please try again."

**Authentication Errors (401/403)**

- Cause: Invalid credentials or insufficient permissions
- Action: Prompt for credential verification
- User Message: "Authentication failed. Please check your credentials."

**Rate Limiting (429)**

- Cause: Too many requests in short period
- Action: Implement automatic retry with delay
- User Message: "Service is busy. Retrying automatically..."

**Server Errors (5xx)**

- Cause: Internal service errors
- Action: Log error details, show generic message
- User Message: "Service error occurred. Please try again later."

**Infrastructure Dependency Errors**

- Cause: External dependencies (Temporal, ClickHouse, PostgreSQL) unavailable
- Action: Check service logs, restart infrastructure stack
- User Message: "Service dependencies are unavailable. Please restart the development environment."
- Recovery: Run `bun run odw:dev` to restart all services with dependency cleanup

### Error Recovery Patterns

**Automatic Retry Logic**

```python
def retry_with_backoff(func, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            return func()
        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
```

## Testing Strategy

### Integration Testing Patterns

**API Connectivity Tests**

- Verify service is running on correct port
- Test basic endpoint availability
- Validate response format consistency

**HTTP Method Validation Tests**

- Ensure GET endpoints reject POST requests appropriately
- Verify POST endpoints handle JSON payloads correctly
- Test parameter passing for both methods

**Timeout and Error Handling Tests**

- Simulate network delays to test timeout behavior
- Mock service unavailability scenarios
- Verify error message clarity and actionability

**Configuration Validation Tests**

- Test port configuration validation
- Verify fallback behavior when service unavailable
- Validate environment-specific configuration loading

### Test Implementation Examples

**Port Availability Test**

```python
def test_moose_service_availability():
    """Test that Moose service is running on expected port"""
    try:
        response = requests.get("http://localhost:4200/health", timeout=5)
        assert response.status_code == 200
    except requests.RequestException:
        pytest.fail("Moose service not available on port 4200")
```

**HTTP Method Validation Test**

```python
def test_consumption_api_http_methods():
    """Test that consumption APIs use correct HTTP methods"""
    # Test GET request works
    response = requests.get(
        "http://localhost:4200/consumption/getBlobs",
        params={"limit": 10}
    )
    assert response.status_code == 200

    # Test POST request is rejected (if applicable)
    response = requests.post(
        "http://localhost:4200/consumption/getBlobs",
        json={"limit": 10}
    )
    assert response.status_code in [405, 400]  # Method not allowed or bad request
```

## Service Startup Patterns

### Port Cleanup on Service Start

Service startup scripts should automatically clean up stale processes to prevent port conflicts:

```bash
kill_processes_on_port() {
    local port=$1
    local pids

    # Get PIDs of processes using the port
    pids=$(lsof -ti ":$port" 2>/dev/null || true)

    if [ -n "$pids" ]; then
        echo "Found processes using port $port: $pids"
        echo "Killing existing processes on port $port..."

        # Kill processes gracefully first (TERM signal)
        echo "$pids" | xargs -r kill -TERM 2>/dev/null || true
        sleep 2

        # Force kill if still running
        pids=$(lsof -ti ":$port" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "Force killing remaining processes: $pids"
            echo "$pids" | xargs -r kill -KILL 2>/dev/null || true
            sleep 1
        fi

        echo "Cleared port $port"
    fi
}

# Use before starting service
kill_processes_on_port 4200
```

## Implementation Guidelines

### Frontend Integration Checklist

1. **HTTP Method Selection**
   - ✅ Use GET for all consumption API endpoints
   - ✅ Use POST for all ingest API endpoints
   - ✅ Pass parameters as query string for GET requests
   - ✅ Pass data as JSON payload for POST requests

2. **Timeout Configuration**
   - ✅ Set 30-second timeout for standard operations
   - ✅ Set 180-second timeout for workflow operations
   - ✅ Set 300-second timeout for batch operations
   - ✅ Handle timeout exceptions gracefully

3. **Port Configuration**
   - ✅ Always use port 4200 for Moose services
   - ✅ Never automatically fallback to port 4201
   - ✅ Validate port availability before making requests
   - ✅ Provide clear error messages for port issues

4. **Error Handling**
   - ✅ Implement user-friendly error messages
   - ✅ Log detailed error information for debugging
   - ✅ Provide retry mechanisms for transient errors
   - ✅ Handle authentication and authorization errors

5. **Testing Coverage**
   - ✅ Test API connectivity and availability
   - ✅ Validate HTTP method usage
   - ✅ Test timeout and error scenarios
   - ✅ Verify configuration validation

### Common Anti-Patterns to Avoid

❌ **Using POST for consumption APIs**

```python
# WRONG
response = requests.post(f"{API_BASE}/extract-azure-billing", json=params)

# CORRECT
response = requests.get(f"{API_BASE}/extract-azure-billing", params=params)
```

❌ **Missing timeout configuration**

```python
# WRONG
response = requests.get(url, params=params)

# CORRECT
response = requests.get(url, params=params, timeout=30)
```

❌ **Automatic port fallback**

```python
# WRONG
try:
    response = requests.get("http://localhost:4200/api")
except:
    response = requests.get("http://localhost:4201/api")  # Don't do this

# CORRECT
try:
    response = requests.get("http://localhost:4200/api")
except:
    raise ServiceUnavailableError("Moose service not available on port 4200")
```

❌ **Generic error handling**

```python
# WRONG
except Exception as e:
    st.error(f"Error: {e}")

# CORRECT
except requests.Timeout:
    st.error("Request timed out. Please try again.")
except requests.ConnectionError:
    st.error("Unable to connect to service. Please check if the service is running.")
```
