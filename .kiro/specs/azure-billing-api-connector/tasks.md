# Implementation Plan

- [x] 1. Create Azure billing data models and configuration classes
  - Create Pydantic models for AzureBillingDetail with all required fields from the design
  - Implement AzureBillingConnectorConfig class with Azure API credentials and processing parameters
  - Create AzureApiConfig and ProcessingConfig models for structured configuration management
  - _Requirements: 1.2, 2.1, 5.1, 5.3_

- [x] 2. Implement Azure EA API client with pagination and error handling
  - [x] 2.1 Create AzureEAApiClient class with authentication and request handling
    - Implement bearer token authentication for Azure EA API
    - Create methods for building API URLs and headers
    - _Requirements: 2.1, 5.1_

  - [x] 2.2 Implement API data fetching with pagination support
    - Create fetch_billing_data method that handles nextLink pagination
    - Implement automatic pagination traversal to retrieve complete datasets
    - Add proper JSON response parsing and error handling
    - _Requirements: 2.2, 4.3_

  - [x] 2.3 Add retry logic and error handling for API requests
    - Implement exponential backoff for rate limits and transient failures
    - Add specific handling for 503 Service Unavailable responses
    - Create timeout configuration and connection error recovery
    - _Requirements: 2.3, 4.1_

- [x] 3. Create resource tracking engine for cost allocation
  - [x] 3.1 Implement ResourceTrackingEngine class
    - Create class to load patterns from d_application_tag ClickHouse table
    - Implement pattern caching and refresh mechanisms
    - Add error handling for database connection issues
    - _Requirements: 3.1, 4.1_

  - [x] 3.2 Implement vectorized resource tracking with audit logging
    - Create apply_tracking method using Polars for efficient pattern matching
    - Implement priority-based matching (instance_id > resource_group > subscription_guid)
    - Generate audit logs for multiple matches and conflicts
    - _Requirements: 3.2, 4.2_

- [x] 4. Build data transformation pipeline
  - [x] 4.1 Create AzureBillingTransformer class
    - Implement transform_raw_data method for schema mapping
    - Add field type conversions (strings to dates, numbers to floats)
    - Create computed field derivation (month_date, newmonth, extended_cost_tax)
    - _Requirements: 3.3, 6.2_

  - [x] 4.2 Implement JSON field processing
    - Create clean_json_string function for tags and additional_info fields
    - Extract structured data from tags (app, ppm_billing_item, ppm_billing_owner, ppm_io_cc)
    - Handle malformed JSON with proper error logging and null fallbacks
    - _Requirements: 3.3, 4.3_

  - [x] 4.3 Add VM-specific business logic
    - Implement SKU derivation based on meter_category and product fields
    - Create resource_name extraction from instance_id and additional_info
    - Add vm_name logic for Virtual Machines with AKS handling
    - _Requirements: 3.4_

- [x] 5. Implement main AzureBillingConnector class
  - [x] 5.1 Create connector class following existing pattern
    - Implement AzureBillingConnector with Generic[T] type parameter
    - Create constructor that accepts AzureBillingConnectorConfig
    - Initialize API client and resource tracking engine
    - _Requirements: 1.1, 1.2_

  - [x] 5.2 Implement extract() method with batch processing
    - Create main extract method that returns List[AzureBillingDetail]
    - Implement date range iteration for monthly data fetching
    - Add chunked processing for memory management
    - Integrate API client, transformation, and resource tracking
    - _Requirements: 1.3, 2.4, 4.4_

  - [x] 5.3 Add memory monitoring and garbage collection
    - Implement memory usage tracking during processing
    - Add garbage collection at appropriate intervals
    - Create memory threshold alerts and cleanup mechanisms
    - _Requirements: 4.4_

- [x] 6. Extend ConnectorFactory for Azure billing support
  - Update ConnectorType enum to include AzureBilling
  - Modify ConnectorFactory.create() method to handle AzureBillingConnector
  - Add proper type hints and configuration validation
  - _Requirements: 1.2, 5.2_

- [x] 7. Create error handling and logging infrastructure
  - [x] 7.1 Implement ErrorHandler class
    - Create handle_api_error method for HTTP error classification
    - Implement handle_data_error for data processing exceptions
    - Add structured error logging with context information
    - _Requirements: 4.1, 4.3_

  - [x] 7.2 Add monitoring and observability features
    - Implement memory monitoring context manager
    - Create performance metrics logging (processing times, record counts)
    - Add data quality metrics tracking (validation failures, audit counts)
    - _Requirements: 4.4, 5.4_

- [x] 8. Create Temporal workflow integration
  - Create extract_azure_billing.py workflow following existing pattern
  - Implement workflow task that uses ConnectorFactory to create AzureBillingConnector
  - Add workflow configuration for batch_size, date_range, and failure simulation
  - Integrate with existing ingest API endpoints for data loading
  - _Requirements: 1.4, 6.1_

- [x] 9. Add data validation and quality checks
  - [x] 9.1 Implement data validation functions
    - Create validation for required fields (instance_id, date ranges)
    - Add data type validation and conversion error handling
    - Implement business rule validation (positive costs, valid dates)
    - _Requirements: 4.1, 6.4_

  - [ ]\* 9.2 Create data quality monitoring
    - Implement row count validation between API and database
    - Add duplicate detection and handling
    - Create data completeness checks for critical fields
    - _Requirements: 6.4_

- [x] 10. Integration with ClickHouse data warehouse
  - [x] 10.1 Verify compatibility with existing table schemas
    - Ensure AzureBillingDetail model matches stg_azure_billing_detail schema
    - Validate field mappings and data types
    - Test JSON field serialization for ClickHouse compatibility
    - _Requirements: 6.2, 6.3_

  - [x] 10.2 Implement database integration utilities
    - Create helper functions for ClickHouse client management
    - Add table existence validation and creation logic
    - Implement batch insertion with error handling
    - _Requirements: 6.1, 6.2_

- [x] 11. Configuration and deployment setup
  - [x] 11.1 Create configuration management
    - Implement environment variable support for Azure credentials
    - Add configuration validation at connector initialization
    - Create default configuration values and documentation
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 11.2 Add security and credential handling
    - Implement secure Azure API key management
    - Add configuration encryption for sensitive values
    - Create credential validation and error reporting
    - _Requirements: 5.1_

- [ ]\* 12. Create comprehensive test suite
  - [ ]\* 12.1 Write unit tests for core components
    - Test AzureBillingConnector extract() method with mock data
    - Test AzureEAApiClient with mocked API responses
    - Test data transformation functions with various input scenarios
    - Test resource tracking engine with sample patterns
    - _Requirements: 1.1, 2.1, 3.1, 3.2_

  - [ ]\* 12.2 Create integration tests
    - Test end-to-end workflow execution with Temporal
    - Test ClickHouse database integration with test data
    - Test error handling scenarios and recovery mechanisms
    - _Requirements: 1.4, 4.1, 6.1_

  - [ ]\* 12.3 Add performance and load testing
    - Test memory usage with large datasets
    - Benchmark processing performance with various batch sizes
    - Test API rate limiting and retry mechanisms
    - _Requirements: 2.3, 4.4_
