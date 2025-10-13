"""
Azure Enterprise Agreement (EA) API Client

This module provides the AzureEAApiClient class for interacting with the Azure EA API
to fetch billing data with proper authentication, pagination, and error handling.
"""

import requests
import time
import logging
import random
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin
import azure_billing.azure_billing_connector as connector_module
AzureApiConfig = connector_module.AzureApiConfig

logger = logging.getLogger(__name__)


class AzureEAApiClient:
    """
    Client for Azure Enterprise Agreement API
    
    Handles authentication, request building, and basic error handling
    for Azure EA API interactions.
    """
    
    def __init__(self, config: AzureApiConfig):
        """
        Initialize the Azure EA API client
        
        Args:
            config: AzureApiConfig containing API credentials and settings
        """
        self.config = config
        self.enrollment_number = config.enrollment_number
        self.api_key = config.api_key
        self.base_url = config.base_url.rstrip('/')
        self.timeout = config.timeout
        self.max_retries = config.max_retries
        self.retry_delay = config.retry_delay
        
        # Create a session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self._build_headers())
        
        logger.info(f"Initialized Azure EA API client for enrollment: {self.enrollment_number}")
    
    def _build_headers(self) -> Dict[str, str]:
        """
        Build HTTP headers for Azure EA API requests
        
        Returns:
            Dictionary containing required headers including authorization
        """
        return {
            'Authorization': f'bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ODW-AzureBillingConnector/1.0'
        }
    
    def _build_api_url(self, endpoint: str) -> str:
        """
        Build complete API URL for a given endpoint
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Complete URL for the API request
        """
        # Remove leading slash if present to avoid double slashes
        endpoint = endpoint.lstrip('/')
        return urljoin(f"{self.base_url}/", endpoint)
    
    def _is_retryable_error(self, response: Optional[requests.Response], exception: Optional[Exception]) -> bool:
        """
        Determine if an error is retryable
        
        Args:
            response: HTTP response object (if available)
            exception: Exception that occurred (if any)
            
        Returns:
            True if the error should be retried, False otherwise
        """
        # Retry on connection errors, timeouts
        if isinstance(exception, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
            return True
        
        # Retry on specific HTTP status codes
        if response is not None:
            # 503 Service Unavailable - Azure EA API specific
            if response.status_code == 503:
                return True
            # 429 Too Many Requests - Rate limiting
            if response.status_code == 429:
                return True
            # 502 Bad Gateway, 504 Gateway Timeout
            if response.status_code in [502, 504]:
                return True
            # 500 Internal Server Error (sometimes transient)
            if response.status_code == 500:
                return True
        
        return False
    
    def _calculate_retry_delay(self, attempt: int, base_delay: Optional[float] = None) -> float:
        """
        Calculate retry delay with exponential backoff and jitter
        
        Args:
            attempt: Current attempt number (1-based)
            base_delay: Base delay in seconds (uses config default if None)
            
        Returns:
            Delay in seconds before next retry
        """
        if base_delay is None:
            base_delay = self.retry_delay
        
        # Exponential backoff: base_delay * (2 ^ (attempt - 1))
        delay = base_delay * (2 ** (attempt - 1))
        
        # Add jitter to avoid thundering herd (±25% random variation)
        jitter = delay * 0.25 * (random.random() * 2 - 1)  # -25% to +25%
        delay += jitter
        
        # Cap maximum delay at 60 seconds
        delay = min(delay, 60.0)
        
        return max(delay, 0.1)  # Minimum 0.1 seconds
    
    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make HTTP request with retry logic and error handling
        
        Args:
            url: Complete URL for the request
            params: Optional query parameters
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: For HTTP errors after all retries exhausted
        """
        last_exception = None
        last_response = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Making request to: {url} (attempt {attempt}/{self.max_retries})")
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                
                # Log response details
                logger.debug(f"Response status: {response.status_code}")
                
                # Check for success
                response.raise_for_status()
                
                # Success - log and return
                if attempt > 1:
                    logger.info(f"Request succeeded on attempt {attempt}")
                
                return response
                
            except requests.exceptions.HTTPError as e:
                last_response = e.response
                last_exception = e
                
                logger.warning(f"HTTP error {last_response.status_code} on attempt {attempt}: {str(e)}")
                
                # Check if we should retry
                if attempt < self.max_retries and self._is_retryable_error(last_response, None):
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    # Log final failure details
                    logger.error(f"HTTP error {last_response.status_code} for URL: {url}")
                    logger.error(f"Response content: {last_response.text[:500]}")
                    raise
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_exception = e
                
                logger.warning(f"Connection/timeout error on attempt {attempt}: {str(e)}")
                
                # Check if we should retry
                if attempt < self.max_retries and self._is_retryable_error(None, e):
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Connection/timeout error for URL: {url}")
                    raise
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error making request to {url}: {str(e)}")
                raise
        
        # If we get here, all retries were exhausted
        if last_exception:
            logger.error(f"All {self.max_retries} retry attempts exhausted for URL: {url}")
            raise last_exception
        else:
            raise requests.exceptions.RequestException(f"Request failed after {self.max_retries} attempts")
    
    def get_billing_data_url(self, month: str) -> str:
        """
        Build URL for billing data endpoint for a specific month
        
        Args:
            month: Month in YYYY-MM format
            
        Returns:
            Complete URL for billing data endpoint
        """
        endpoint = f"{self.enrollment_number}/billingPeriods/{month}/usagedetails"
        return self._build_api_url(endpoint)
    
    def validate_connection(self) -> bool:
        """
        Validate API connection and credentials
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to get enrollment details as a connection test
            test_url = self._build_api_url(f"{self.enrollment_number}")
            response = self._make_request(test_url)
            
            logger.info("Azure EA API connection validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate Azure EA API connection: {str(e)}")
            return False
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def fetch_billing_data(self, month: str, page_url: Optional[str] = None) -> Tuple[List[Dict], Optional[str]]:
        """
        Fetch billing data for a specific month with pagination support
        
        Args:
            month: Month in YYYY-MM format (e.g., "2024-01")
            page_url: Optional URL for pagination (nextLink from previous response)
            
        Returns:
            Tuple containing:
            - List of billing records as dictionaries
            - Next page URL if more data available, None otherwise
            
        Raises:
            requests.RequestException: For API errors
            ValueError: For invalid response format
        """
        try:
            # Use provided page URL or build initial URL
            if page_url:
                url = page_url
                logger.debug(f"Fetching paginated data from: {page_url}")
            else:
                url = self.get_billing_data_url(month)
                logger.info(f"Fetching billing data for month: {month}")
            
            # Make the API request
            response = self._make_request(url)
            
            # Parse JSON response
            try:
                data = response.json()
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Response content: {response.text[:1000]}")
                raise ValueError(f"Invalid JSON response from Azure EA API: {str(e)}")
            
            # Extract billing records
            billing_records = []
            if isinstance(data, dict):
                # Standard Azure EA API response format
                if 'value' in data:
                    billing_records = data['value']
                    logger.info(f"Retrieved {len(billing_records)} billing records")
                else:
                    logger.warning("No 'value' field found in API response")
                    logger.debug(f"Response structure: {list(data.keys())}")
                
                # Check for pagination
                next_link = data.get('nextLink') or data.get('@odata.nextLink')
                if next_link:
                    logger.debug(f"Next page available: {next_link}")
                else:
                    logger.debug("No more pages available")
                
                return billing_records, next_link
                
            elif isinstance(data, list):
                # Direct list response (less common)
                logger.info(f"Retrieved {len(data)} billing records (direct list)")
                return data, None
            else:
                logger.error(f"Unexpected response format: {type(data)}")
                raise ValueError(f"Unexpected response format from Azure EA API: {type(data)}")
                
        except requests.exceptions.RequestException:
            # Re-raise request exceptions as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching billing data: {str(e)}")
            raise
    
    def fetch_all_billing_data(self, month: str) -> List[Dict]:
        """
        Fetch all billing data for a month, handling pagination automatically
        
        Args:
            month: Month in YYYY-MM format (e.g., "2024-01")
            
        Returns:
            Complete list of billing records for the month
            
        Raises:
            requests.RequestException: For API errors
        """
        all_records = []
        next_url = None
        page_count = 0
        
        logger.info(f"Starting complete data fetch for month: {month}")
        
        try:
            while True:
                page_count += 1
                logger.debug(f"Fetching page {page_count}")
                
                # Fetch current page
                records, next_url = self.fetch_billing_data(month, next_url)
                
                # Add records to collection
                all_records.extend(records)
                logger.debug(f"Page {page_count}: {len(records)} records, Total: {len(all_records)}")
                
                # Check if more pages available
                if not next_url:
                    break
                    
                # Small delay between requests to be respectful to the API
                time.sleep(0.1)
            
            logger.info(f"Completed data fetch for {month}: {len(all_records)} total records across {page_count} pages")
            return all_records
            
        except Exception as e:
            logger.error(f"Failed to fetch complete billing data for {month}: {str(e)}")
            logger.info(f"Partial data retrieved: {len(all_records)} records from {page_count} pages")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session"""
        if hasattr(self, 'session'):
            self.session.close()