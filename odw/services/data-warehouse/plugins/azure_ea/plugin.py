"""
Azure Enterprise Agreement Plugin

Data source plugin for Azure EA API integration with FOCUS transformation.
Enhanced with BasePlugin interface and comprehensive error handling.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import os

from ...app.azure_billing.plugins.manager import BasePlugin

logger = logging.getLogger(__name__)


class PluginMetadata(BaseModel):
    """Plugin metadata model"""
    name: str
    version: str
    description: str
    author: str
    category: str
    tags: List[str]
    requirements: List[str]
    config_schema: Dict[str, Any]
    icon_url: Optional[str] = None
    documentation_url: Optional[str] = None


class AzureEAPlugin(BasePlugin):
    """
    Azure Enterprise Agreement API plugin for billing data extraction.
    
    This plugin provides integration with Azure EA APIs to extract
    billing and usage data for FOCUS transformation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "https://consumption.azure.com")
        self.api_version = config.get("api_version", "2019-10-01")
        self.session: Optional[aiohttp.ClientSession] = None
        self.enrollment_number = config.get("enrollment_number")
        self.api_key = config.get("api_key")
        self.timeout = config.get("timeout", 30)
        self.rate_limit_delay = config.get("rate_limit_delay", 1.0)
    
    async def initialize(self) -> bool:
        """Initialize the Azure EA plugin"""
        try:
            # Validate required configuration
            if not self.enrollment_number or not self.api_key:
                logger.error("Missing required configuration: enrollment_number or api_key")
                return False
            
            # Initialize HTTP session
            await self._init_session()
            
            # Test connection
            connection_test = await self.test_connection(self.config)
            if not connection_test:
                logger.error("Azure EA API connection test failed")
                return False
            
            self._initialized = True
            logger.info("Azure EA plugin initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure EA plugin: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Azure EA API connection"""
        health_result = {
            "healthy": False,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        try:
            # Check session status
            if not self.session or self.session.closed:
                health_result["checks"]["session"] = {"status": "failed", "message": "Session not available"}
                return health_result
            
            health_result["checks"]["session"] = {"status": "ok", "message": "Session active"}
            
            # Test API connectivity
            url = f"{self.base_url}/v3/enrollments/{self.enrollment_number}/billingperiods"
            headers = self._get_headers(self.api_key)
            
            start_time = datetime.utcnow()
            async with self.session.get(url, headers=headers, timeout=10) as response:
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                if response.status == 200:
                    health_result["checks"]["api_connectivity"] = {
                        "status": "ok", 
                        "response_time_seconds": response_time,
                        "message": "API accessible"
                    }
                    health_result["healthy"] = True
                else:
                    health_result["checks"]["api_connectivity"] = {
                        "status": "failed",
                        "response_code": response.status,
                        "message": f"API returned status {response.status}"
                    }
            
        except asyncio.TimeoutError:
            health_result["checks"]["api_connectivity"] = {
                "status": "failed",
                "message": "API request timed out"
            }
        except Exception as e:
            health_result["checks"]["api_connectivity"] = {
                "status": "failed",
                "message": f"API check failed: {str(e)}"
            }
        
        return health_result
    
    async def cleanup(self):
        """Clean up plugin resources"""
        if self.session and not self.session.closed:
            await self.session.close()
        logger.info("Azure EA plugin cleanup completed")
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Return plugin metadata"""
        return {
            "name": "azure-ea-api",
            "version": "1.0.0",
            "description": "Azure Enterprise Agreement API connector for billing data extraction",
            "author": "ABI Team",
            "category": "data_source",
            "plugin_type": "data_source",
            "tags": ["azure", "billing", "enterprise", "ea"],
            "requirements": ["aiohttp>=3.8.0", "azure-identity>=1.12.0"],
            "config_schema": {
                "type": "object",
                "properties": {
                    "enrollment_number": {
                        "type": "string",
                        "description": "Azure EA enrollment number",
                        "pattern": "^[0-9]+$"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "Azure EA API key",
                        "format": "password"
                    },
                    "base_url": {
                        "type": "string",
                        "default": "https://consumption.azure.com",
                        "description": "Azure EA API base URL"
                    },
                    "timeout": {
                        "type": "integer",
                        "default": 30,
                        "minimum": 5,
                        "maximum": 300,
                        "description": "Request timeout in seconds"
                    },
                    "rate_limit_delay": {
                        "type": "number",
                        "default": 1.0,
                        "minimum": 0.1,
                        "maximum": 10.0,
                        "description": "Delay between API requests in seconds"
                    }
                },
                "required": ["enrollment_number", "api_key"]
            },
            "icon_url": "https://azure.microsoft.com/favicon.ico",
            "documentation_url": "https://docs.microsoft.com/en-us/rest/api/consumption/"
        }
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration.
        
        Args:
            config: Plugin configuration dictionary
            
        Returns:
            True if configuration is valid
        """
        required_fields = ["enrollment_number", "api_key"]
        
        for field in required_fields:
            if field not in config or not config[field]:
                logger.error(f"Missing required configuration field: {field}")
                return False
        
        # Validate enrollment number format
        enrollment_number = config["enrollment_number"]
        if not enrollment_number.isdigit():
            logger.error("Enrollment number must contain only digits")
            return False
        
        return True
    
    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """
        Test connection with Azure EA API.
        
        Args:
            config: Plugin configuration dictionary
            
        Returns:
            True if connection is successful
        """
        try:
            if not await self.validate_config(config):
                return False
            
            # Ensure session is initialized
            if not self.session:
                await self._init_session()
            
            # Test API connectivity with a simple request
            enrollment_number = config["enrollment_number"]
            url = f"{self.base_url}/v3/enrollments/{enrollment_number}/billingperiods"
            
            headers = self._get_headers(config["api_key"])
            
            async with self.session.get(url, headers=headers, timeout=config.get("timeout", 30)) as response:
                if response.status == 200:
                    logger.info("Azure EA API connection test successful")
                    return True
                elif response.status == 401:
                    logger.error("Azure EA API authentication failed - check API key")
                    return False
                elif response.status == 403:
                    logger.error("Azure EA API access forbidden - check permissions")
                    return False
                else:
                    logger.error(f"Azure EA API connection test failed with status: {response.status}")
                    return False
                    
        except asyncio.TimeoutError:
            logger.error("Azure EA API connection test timed out")
            return False
        except Exception as e:
            logger.error(f"Azure EA API connection test failed: {e}")
            return False
    
    async def extract_data(self, config: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract billing data from Azure EA API.
        
        Args:
            config: Plugin configuration
            params: Extraction parameters (start_date, end_date, etc.)
            
        Returns:
            List of billing records
        """
        try:
            if not await self.validate_config(config):
                raise ValueError("Invalid plugin configuration")
            
            await self._init_session(config)
            
            start_date = params.get("start_date")
            end_date = params.get("end_date")
            batch_size = params.get("batch_size", 1000)
            
            if not start_date or not end_date:
                raise ValueError("start_date and end_date are required parameters")
            
            enrollment_number = config["enrollment_number"]
            api_key = config["api_key"]
            
            # Extract usage details
            usage_data = await self._extract_usage_details(
                enrollment_number, api_key, start_date, end_date, batch_size
            )
            
            logger.info(f"Extracted {len(usage_data)} records from Azure EA API")
            return usage_data
            
        except Exception as e:
            logger.error(f"Error extracting data from Azure EA API: {e}")
            raise
        finally:
            await self._close_session()
    
    async def get_schema(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get data schema from Azure EA API.
        
        Args:
            config: Plugin configuration
            
        Returns:
            Schema definition
        """
        return {
            "type": "object",
            "properties": {
                "account_owner_id": {"type": "string"},
                "account_name": {"type": "string"},
                "subscription_id": {"type": "string"},
                "subscription_name": {"type": "string"},
                "date": {"type": "string", "format": "date"},
                "product": {"type": "string"},
                "meter_category": {"type": "string"},
                "meter_sub_category": {"type": "string"},
                "consumed_quantity": {"type": "number"},
                "resource_rate": {"type": "number"},
                "extended_cost": {"type": "number"},
                "resource_location": {"type": "string"},
                "consumed_service": {"type": "string"},
                "instance_id": {"type": "string"},
                "resource_group": {"type": "string"},
                "department_name": {"type": "string"},
                "cost_center": {"type": "string"},
                "tags": {"type": "string"}
            }
        }
    
    async def _init_session(self):
        """Initialize HTTP session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def _close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_headers(self, api_key: str) -> Dict[str, str]:
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _extract_usage_details(self, 
                                   enrollment_number: str, 
                                   api_key: str, 
                                   start_date: str, 
                                   end_date: str, 
                                   batch_size: int) -> List[Dict[str, Any]]:
        """
        Extract usage details from Azure EA API.
        
        Args:
            enrollment_number: Azure EA enrollment number
            api_key: API authentication key
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            batch_size: Number of records per batch
            
        Returns:
            List of usage detail records
        """
        all_records = []
        headers = self._get_headers(api_key)
        
        # Get billing periods in the date range
        billing_periods = await self._get_billing_periods(enrollment_number, headers, start_date, end_date)
        
        for period in billing_periods:
            period_start = period["billingPeriodId"]
            
            # Extract usage details for this billing period
            url = f"{self.base_url}/v3/enrollments/{enrollment_number}/usagedetails"
            params = {
                "billingPeriod": period_start,
                "$top": batch_size
            }
            
            page_records = await self._get_paginated_data(url, headers, params)
            all_records.extend(page_records)
            
            # Rate limiting
            await asyncio.sleep(1.0)  # 1 second delay between requests
        
        return all_records
    
    async def _get_billing_periods(self, 
                                 enrollment_number: str, 
                                 headers: Dict[str, str], 
                                 start_date: str, 
                                 end_date: str) -> List[Dict[str, Any]]:
        """Get billing periods within date range"""
        url = f"{self.base_url}/v3/enrollments/{enrollment_number}/billingperiods"
        
        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Failed to get billing periods: {response.status}")
            
            data = await response.json()
            periods = data.get("value", [])
            
            # Filter periods by date range
            filtered_periods = []
            for period in periods:
                period_start = period.get("billingPeriodId", "")
                if start_date <= period_start <= end_date:
                    filtered_periods.append(period)
            
            return filtered_periods
    
    async def _get_paginated_data(self, 
                                url: str, 
                                headers: Dict[str, str], 
                                params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get paginated data from API"""
        all_records = []
        next_url = url
        
        while next_url:
            async with self.session.get(next_url, headers=headers, params=params if next_url == url else None) as response:
                if response.status != 200:
                    logger.error(f"API request failed with status: {response.status}")
                    break
                
                data = await response.json()
                records = data.get("value", [])
                all_records.extend(records)
                
                # Get next page URL
                next_url = data.get("nextLink")
                
                # Rate limiting
                await asyncio.sleep(0.5)
        
        return all_records


# Plugin factory function
def create_plugin(config: Dict[str, Any]) -> AzureEAPlugin:
    """Create and return plugin instance"""
    return AzureEAPlugin(config)

# Plugin class for direct instantiation
Plugin = AzureEAPlugin