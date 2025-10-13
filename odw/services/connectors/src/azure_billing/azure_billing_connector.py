from typing import List, TypeVar, Generic, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import date, datetime
from enum import Enum

T = TypeVar('T')

class AzureApiConfig(BaseModel):
    """Configuration for Azure EA API connection"""
    enrollment_number: str = Field(..., description="Azure enrollment number")
    api_key: str = Field(..., description="Azure EA API key")
    base_url: str = Field(default="https://ea.azure.cn/rest", description="Azure EA API base URL")
    timeout: int = Field(default=800, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    retry_delay: int = Field(default=5, description="Delay between retries in seconds")

class ProcessingConfig(BaseModel):
    """Configuration for data processing parameters"""
    batch_size: int = Field(default=1000, description="Number of records to process in each batch")
    chunk_size: int = Field(default=10000, description="Size of data chunks for memory management")
    memory_threshold_mb: int = Field(default=500, description="Memory threshold in MB for garbage collection")
    enable_audit_logging: bool = Field(default=True, description="Enable audit logging for resource tracking")

class AzureBillingConnectorConfig(BaseModel):
    """Main configuration class for Azure Billing Connector"""
    batch_size: Optional[int] = Field(default=None, description="Override batch size for connector")
    start_date: Optional[datetime] = Field(default=None, description="Start date for data extraction")
    end_date: Optional[datetime] = Field(default=None, description="End date for data extraction")
    azure_enrollment_number: Optional[str] = Field(default=None, description="Azure enrollment number")
    azure_api_key: Optional[str] = Field(default=None, description="Azure EA API key")
    api_base_url: Optional[str] = Field(default=None, description="Azure EA API base URL")
    azure_api_config: Optional[AzureApiConfig] = Field(default=None, description="Detailed Azure API configuration")
    processing_config: Optional[ProcessingConfig] = Field(default=None, description="Data processing configuration")

    def get_effective_batch_size(self) -> int:
        """Get the effective batch size from various configuration sources"""
        if self.batch_size is not None:
            return self.batch_size
        if self.processing_config and self.processing_config.batch_size:
            return self.processing_config.batch_size
        return 1000

    def get_azure_api_config(self) -> AzureApiConfig:
        """Get the effective Azure API configuration"""
        if self.azure_api_config:
            return self.azure_api_config
        
        # Build from individual fields if azure_api_config not provided
        enrollment_number = self.azure_enrollment_number
        api_key = self.azure_api_key
        base_url = self.api_base_url or "https://ea.azure.cn/rest"
        
        if not enrollment_number or not api_key:
            raise ValueError("Azure enrollment number and API key must be provided")
        
        return AzureApiConfig(
            enrollment_number=enrollment_number,
            api_key=api_key,
            base_url=base_url
        )

    def get_processing_config(self) -> ProcessingConfig:
        """Get the effective processing configuration"""
        if self.processing_config:
            return self.processing_config
        return ProcessingConfig()

class AzureBillingDetail(BaseModel):
    """Pydantic model for Azure billing detail records"""
    id: Optional[str] = Field(default=None, description="Unique identifier for the billing record")
    account_owner_id: Optional[str] = Field(default=None, description="Account owner identifier")
    account_name: Optional[str] = Field(default=None, description="Account name")
    service_administrator_id: Optional[str] = Field(default=None, description="Service administrator identifier")
    subscription_id: Optional[int] = Field(default=None, description="Subscription ID")
    subscription_guid: Optional[str] = Field(default=None, description="Subscription GUID")
    subscription_name: Optional[str] = Field(default=None, description="Subscription name")
    date: Optional[datetime] = Field(default=None, description="Billing date")
    month: Optional[int] = Field(default=None, description="Billing month")
    day: Optional[int] = Field(default=None, description="Billing day")
    year: Optional[int] = Field(default=None, description="Billing year")
    product: Optional[str] = Field(default=None, description="Product name")
    meter_id: Optional[str] = Field(default=None, description="Meter identifier")
    meter_category: Optional[str] = Field(default=None, description="Meter category")
    meter_sub_category: Optional[str] = Field(default=None, description="Meter sub-category")
    meter_region: Optional[str] = Field(default=None, description="Meter region")
    meter_name: Optional[str] = Field(default=None, description="Meter name")
    consumed_quantity: Optional[float] = Field(default=None, description="Consumed quantity")
    resource_rate: Optional[float] = Field(default=None, description="Resource rate")
    extended_cost: Optional[float] = Field(default=None, description="Extended cost")
    resource_location: Optional[str] = Field(default=None, description="Resource location")
    consumed_service: Optional[str] = Field(default=None, description="Consumed service")
    instance_id: str = Field(..., description="Instance ID (required field)")
    service_info1: Optional[str] = Field(default=None, description="Service info 1")
    service_info2: Optional[str] = Field(default=None, description="Service info 2")
    additional_info: Optional[Dict[str, Any]] = Field(default=None, description="Additional information as JSON")
    tags: Optional[Dict[str, Any]] = Field(default=None, description="Resource tags as JSON")
    store_service_identifier: Optional[str] = Field(default=None, description="Store service identifier")
    department_name: Optional[str] = Field(default=None, description="Department name")
    cost_center: Optional[str] = Field(default=None, description="Cost center")
    unit_of_measure: Optional[str] = Field(default=None, description="Unit of measure")
    resource_group: Optional[str] = Field(default=None, description="Resource group")
    extended_cost_tax: Optional[float] = Field(default=None, description="Extended cost including tax")
    resource_tracking: Optional[str] = Field(default=None, description="Resource tracking information")
    resource_name: Optional[str] = Field(default=None, description="Resource name")
    vm_name: Optional[str] = Field(default=None, description="Virtual machine name")
    latest_resource_type: Optional[str] = Field(default=None, description="Latest resource type")
    newmonth: Optional[str] = Field(default=None, description="New month identifier")
    month_date: datetime = Field(..., description="Month date (required field)")
    sku: Optional[str] = Field(default=None, description="SKU identifier")
    cmdb_mapped_application_service: Optional[str] = Field(default=None, description="CMDB mapped application service")
    ppm_billing_item: Optional[str] = Field(default=None, description="PPM billing item")
    ppm_id_owner: Optional[str] = Field(default=None, description="PPM ID owner")
    ppm_io_cc: Optional[str] = Field(default=None, description="PPM IO cost center")

class AzureBillingConnector(Generic[T]):
    """Azure Billing Connector following the established connector pattern"""
    
    def __init__(self, config: AzureBillingConnectorConfig):
        self._config = config
        self._azure_api_config = config.get_azure_api_config()
        self._processing_config = config.get_processing_config()
        self._batch_size = config.get_effective_batch_size()
        
        # Initialize components
        self._api_client = None
        self._resource_tracking_engine = None
        self._transformer = None
        
        # Initialize logging
        import logging
        self._logger = logging.getLogger(__name__)
        
    def _initialize_components(self):
        """Initialize API client and processing components"""
        if self._api_client is None:
            import azure_billing.azure_ea_api_client as api_client_module
            self._api_client = api_client_module.AzureEAApiClient(self._azure_api_config)
            
        if self._resource_tracking_engine is None:
            import azure_billing.resource_tracking_engine as tracking_module
            self._resource_tracking_engine = tracking_module.ResourceTrackingEngine()
            
        if self._transformer is None:
            import azure_billing.azure_billing_transformer as transformer_module
            self._transformer = transformer_module.AzureBillingTransformer()
        
    def extract(self) -> List[AzureBillingDetail]:
        """
        Main extraction method following connector pattern
        Extracts, transforms, and returns Azure billing data
        """
        try:
            self._logger.info("Starting Azure billing data extraction")
            
            # Initialize components
            self._initialize_components()
            
            # Validate configuration
            if not self._config.start_date or not self._config.end_date:
                raise ValueError("start_date and end_date must be provided in configuration")
            
            # Extract data for date range
            all_records = []
            current_date = self._config.start_date
            
            while current_date <= self._config.end_date:
                month_str = current_date.strftime('%Y-%m')
                self._logger.info(f"Processing month: {month_str}")
                
                # Extract raw data for month
                month_records = self._extract_month_data(month_str)
                all_records.extend(month_records)
                
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            self._logger.info(f"Extraction complete: {len(all_records)} total records")
            return all_records
            
        except Exception as e:
            self._logger.error(f"Failed to extract Azure billing data: {str(e)}")
            raise
    
    def _extract_month_data(self, month: str) -> List[AzureBillingDetail]:
        """
        Extract and process data for a specific month with batch processing
        
        Args:
            month: Month in YYYY-MM format
            
        Returns:
            List of processed AzureBillingDetail records
        """
        try:
            # Fetch raw data from API
            raw_data = self._api_client.fetch_all_billing_data(month)
            
            if not raw_data:
                self._logger.warning(f"No data returned for month {month}")
                return []
            
            self._logger.info(f"Processing {len(raw_data)} raw records for month {month}")
            
            # Process data in chunks for memory management
            chunk_size = self._processing_config.chunk_size
            all_processed_records = []
            
            for i in range(0, len(raw_data), chunk_size):
                chunk_end = min(i + chunk_size, len(raw_data))
                chunk_data = raw_data[i:chunk_end]
                
                self._logger.debug(f"Processing chunk {i//chunk_size + 1}: records {i+1}-{chunk_end}")
                
                # Process chunk
                chunk_records = self._process_data_chunk(chunk_data, month, i//chunk_size + 1)
                all_processed_records.extend(chunk_records)
                
                # Memory management
                if self._should_trigger_gc(i//chunk_size + 1):
                    self._perform_memory_cleanup()
            
            self._logger.info(f"Completed processing {len(all_processed_records)} records for month {month}")
            return all_processed_records
            
        except Exception as e:
            self._logger.error(f"Failed to extract data for month {month}: {str(e)}")
            raise
    
    def _process_data_chunk(self, chunk_data: List[Dict], month: str, chunk_num: int) -> List[AzureBillingDetail]:
        """
        Process a chunk of raw data
        
        Args:
            chunk_data: List of raw billing records
            month: Month being processed
            chunk_num: Chunk number for logging
            
        Returns:
            List of processed AzureBillingDetail records
        """
        try:
            # Convert to Polars DataFrame for processing
            import polars as pl
            df = pl.DataFrame(chunk_data)
            
            # Transform the data
            transformed_df = self._transformer.transform_raw_data(df)
            
            # Apply resource tracking
            tracking_series, audit_df = self._resource_tracking_engine.apply_tracking(transformed_df)
            
            # Add resource tracking to main DataFrame
            transformed_df = transformed_df.with_columns(tracking_series)
            
            # Apply business rules
            final_df = self._transformer.apply_business_rules(transformed_df)
            
            # Convert to Pydantic models in batches
            records = []
            batch_size = self._batch_size
            
            for batch_start in range(0, len(final_df), batch_size):
                batch_end = min(batch_start + batch_size, len(final_df))
                batch_rows = final_df.slice(batch_start, batch_end - batch_start)
                
                for row in batch_rows.iter_rows(named=True):
                    try:
                        # Clean row data for Pydantic model
                        cleaned_row = self._clean_row_for_model(row)
                        record = AzureBillingDetail(**cleaned_row)
                        records.append(record)
                    except Exception as e:
                        self._logger.warning(f"Failed to create record from row: {str(e)}")
                        continue
            
            # Log audit information if conflicts found
            if len(audit_df) > 0:
                audit_summary = self._resource_tracking_engine.generate_audit_summary(audit_df)
                self._logger.debug(f"Chunk {chunk_num} audit summary: {audit_summary}")
            
            return records
            
        except Exception as e:
            self._logger.error(f"Failed to process chunk {chunk_num} for month {month}: {str(e)}")
            raise
    
    def _clean_row_for_model(self, row: Dict) -> Dict:
        """
        Clean row data to ensure compatibility with Pydantic model
        
        Args:
            row: Raw row dictionary
            
        Returns:
            Cleaned row dictionary
        """
        cleaned = {}
        
        for key, value in row.items():
            # Handle None values
            if value is None:
                cleaned[key] = None
                continue
            
            # Handle date fields
            if key in ['date', 'month_date'] and value is not None:
                if isinstance(value, str):
                    try:
                        from datetime import datetime
                        cleaned[key] = datetime.strptime(value, '%Y-%m-%d').date()
                    except:
                        cleaned[key] = None
                else:
                    cleaned[key] = value
            else:
                cleaned[key] = value
        
        return cleaned
    
    def _should_trigger_gc(self, chunk_num: int) -> bool:
        """
        Determine if garbage collection should be triggered
        
        Args:
            chunk_num: Current chunk number
            
        Returns:
            True if GC should be triggered
        """
        # Trigger GC every 10 chunks or based on memory threshold
        return chunk_num % 10 == 0
    
    def _perform_memory_cleanup(self):
        """Perform memory cleanup and garbage collection"""
        try:
            import gc
            import psutil
            import os
            
            # Get current memory usage
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # Trigger garbage collection
            collected = gc.collect()
            
            # Log memory info
            new_memory_mb = process.memory_info().rss / 1024 / 1024
            self._logger.debug(f"Memory cleanup: {memory_mb:.1f}MB -> {new_memory_mb:.1f}MB, "
                             f"collected {collected} objects")
            
            # Check if memory usage is too high
            if new_memory_mb > self._processing_config.memory_threshold_mb:
                self._logger.warning(f"Memory usage ({new_memory_mb:.1f}MB) exceeds threshold "
                                   f"({self._processing_config.memory_threshold_mb}MB)")
                
        except Exception as e:
            self._logger.warning(f"Failed to perform memory cleanup: {str(e)}")
    
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get current memory usage statistics
        
        Returns:
            Dictionary with memory usage information
        """
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
                'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
                'percent': process.memory_percent(),       # Percentage of system memory
                'available_mb': psutil.virtual_memory().available / 1024 / 1024
            }
            
        except Exception as e:
            self._logger.warning(f"Failed to get memory usage: {str(e)}")
            return {'error': str(e)}


class MemoryMonitor:
    """Context manager for monitoring memory usage during operations"""
    
    def __init__(self, operation_name: str, logger=None):
        import logging
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_memory = None
        self.end_memory = None
    
    def __enter__(self):
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            self.start_memory = process.memory_info().rss / 1024 / 1024
            self.logger.debug(f"Starting {self.operation_name} - Memory: {self.start_memory:.1f}MB")
        except Exception as e:
            self.logger.warning(f"Failed to get start memory for {self.operation_name}: {str(e)}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            self.end_memory = process.memory_info().rss / 1024 / 1024
            
            if self.start_memory:
                memory_delta = self.end_memory - self.start_memory
                self.logger.info(f"Completed {self.operation_name} - "
                               f"Memory: {self.end_memory:.1f}MB "
                               f"(Δ{memory_delta:+.1f}MB)")
            else:
                self.logger.info(f"Completed {self.operation_name} - Memory: {self.end_memory:.1f}MB")
                
        except Exception as e:
            self.logger.warning(f"Failed to get end memory for {self.operation_name}: {str(e)}")