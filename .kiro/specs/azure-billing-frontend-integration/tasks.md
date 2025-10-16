# Implementation Plan

- [x] 1. Set up Azure billing page structure and navigation
  - Create new page file `pages/azure_billing_view.py` following existing page patterns
  - Add Azure billing page to navigation menu in `main.py` with icon and URL path
  - Implement basic page layout with header, configuration section, and data display areas
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 2. Implement credential management system with multiple persistence levels
  - [x] 2.1 Create CredentialManager class with encryption capabilities
    - Implement session-based credential encryption for temporary storage
    - Add browser localStorage encryption with stronger security for persistent storage
    - Create credential retrieval methods that check multiple storage sources
    - _Requirements: 7.1, 7.2, 7.6_

  - [x] 2.2 Implement WorkflowParameterManager for configuration persistence
    - Create methods to save/load configuration to session state
    - Add browser localStorage integration for cross-session persistence
    - Implement file export/import functionality for configuration backup
    - Add environment variable support for system defaults
    - _Requirements: 7.3, 7.7_

- [ ] 3. Build configuration form with persistence options
  - [x] 3.1 Create configuration form UI components
    - Implement Azure credentials input fields with masking
    - Add date range pickers with validation
    - Create batch size input with reasonable limits
    - Add persistence level selection (session/browser/export)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.2 Add configuration validation and error handling
    - Implement client-side validation for all form fields
    - Add enrollment number format validation
    - Create date range validation (start before end, reasonable limits)
    - Display clear error messages for invalid configurations
    - _Requirements: 2.5, 7.4_

  - [x] 3.3 Implement configuration persistence actions
    - Add save configuration button with persistence level handling
    - Create import/export functionality for configuration files
    - Implement test connection functionality
    - Add clear saved data options with level selection
    - _Requirements: 7.3, 7.6_

- [ ] 4. Create API integration functions for Azure billing
  - [x] 4.1 Extend api_functions.py with Azure billing methods
    - Implement `fetch_azure_billing_data()` function with filtering support
    - Create `trigger_azure_billing_extract()` function for workflow execution
    - Add `test_azure_connection()` function for credential validation
    - Implement `fetch_azure_billing_summary()` for metrics data
    - _Requirements: 3.1, 3.2, 3.3, 6.2_

  - [x] 4.2 Add error handling for API interactions
    - Implement specific error handling for authentication failures (401/403)
    - Add rate limiting detection and user-friendly messages (429)
    - Create server error handling with retry suggestions (5xx)
    - Ensure error messages don't expose sensitive credential information
    - _Requirements: 3.4, 3.5, 7.4_

- [ ] 5. Implement workflow trigger and monitoring functionality
  - [x] 5.1 Create workflow execution interface
    - Add "Run Azure Billing Extract" button with configuration validation
    - Implement loading states and progress indicators during execution
    - Create success/failure message handling using existing status system
    - Add automatic data refresh after successful workflow completion
    - _Requirements: 3.1, 3.2, 3.3, 3.6_

  - [x] 5.2 Integrate workflow status monitoring
    - Use existing `render_workflows_table()` function for Azure billing workflows
    - Add workflow execution metrics (processing time, record counts)
    - Implement error detection and troubleshooting recommendations
    - Create links to detailed logs and audit information
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 6. Build data visualization and table components
  - [x] 6.1 Create summary metrics dashboard
    - Implement metric cards for total cost, resource count, subscription count
    - Add last updated timestamp display
    - Create responsive layout using existing UI patterns
    - Integrate with `fetch_azure_billing_summary()` API function
    - _Requirements: 4.3, 5.3_

  - [x] 6.2 Implement interactive data table
    - Create `prepare_azure_billing_display_data()` function for data transformation
    - Add sortable columns for key billing fields (date, cost, subscription, resource)
    - Implement pagination or virtual scrolling for large datasets
    - Add search and filter capabilities within the table
    - _Requirements: 4.1, 4.2, 4.4_

  - [x] 6.3 Add filtering and analysis controls
    - Create filter controls for date range, subscription, resource group, cost center
    - Implement dynamic filter application with real-time table updates
    - Add export functionality (CSV and Excel) for filtered data
    - Create "no data" state with helpful instructions for new users
    - _Requirements: 4.5, 5.1, 5.2, 4.6_

- [ ] 7. Create cost analysis and visualization charts
  - [x] 7.1 Implement cost trend analysis
    - Create line chart showing cost trends over time using billing data
    - Add bar chart for cost breakdown by subscription
    - Implement responsive chart layout using existing patterns
    - Add chart interaction capabilities (zoom, filter, export)
    - _Requirements: 5.4_

  - [x] 7.2 Add resource tracking analysis
    - Create pie chart showing tracked vs untracked resource costs
    - Add metrics for resource tracking coverage and unmapped resources
    - Implement drill-down capabilities for resource tracking details
    - Create recommendations for improving resource tracking coverage
    - _Requirements: 5.5, 6.3_

- [ ] 8. Implement security and data protection measures
  - [x] 8.1 Add credential security features
    - Implement secure credential masking in all input fields
    - Add session timeout handling with automatic credential clearing
    - Create secure credential storage with proper encryption keys
    - Implement credential validation without exposing values in errors
    - _Requirements: 7.1, 7.4, 7.5, 7.7_

  - [x] 8.2 Add data security and privacy controls
    - Implement input sanitization for all user inputs
    - Add HTTPS enforcement for production API communications
    - Create audit logging for all configuration changes and workflow triggers
    - Implement data retention policies for cached billing data
    - _Requirements: 7.4, 6.4_

- [x] 9. Integrate with existing application architecture
  - [x] 9.1 Follow existing design patterns and styling
    - Use `streamlit_shadcn_ui` components consistently with other pages
    - Apply existing CSS styling and layout patterns
    - Implement consistent navigation and page structure
    - Use existing tooltip and help text patterns
    - _Requirements: 8.1, 8.2_

  - [x] 9.2 Integrate with existing status and error handling systems
    - Use existing `status_handler.py` for user feedback messages
    - Implement consistent error display patterns
    - Add integration with existing logging and monitoring systems
    - Ensure consistent performance and responsiveness with other pages
    - _Requirements: 8.3, 8.4, 8.5_

- [ ] 10. Implement backend API endpoints for Azure billing
  - [x] 10.1 Create Azure billing consumption API endpoints
    - Add `/getAzureBilling` endpoint to fetch billing data from moose_f_azure_billing_detail table
    - Implement `/getAzureBillingSummary` endpoint for summary metrics
    - Add `/getAzureSubscriptions` and `/getAzureResourceGroups` endpoints for filter options
    - Create proper error handling and response formatting for all endpoints
    - _Requirements: 4.1, 4.2, 5.1_

  - [x] 10.2 Create Azure workflow trigger endpoints
    - Implement `/extract-azure-billing` POST endpoint to trigger Temporal workflows
    - Add `/test-azure-connection` POST endpoint for credential validation
    - Create proper request validation and error responses
    - Integrate with existing Azure billing connector from the backend spec
    - _Requirements: 3.1, 3.2, 3.3, 6.1_

- [ ] 11. Add browser localStorage integration for persistence
  - [x] 11.1 Implement JavaScript integration for localStorage
    - Create JavaScript functions for reading/writing to localStorage
    - Add proper error handling for browsers with disabled localStorage
    - Implement data validation for localStorage content
    - Create fallback mechanisms when localStorage is unavailable
    - _Requirements: 7.2, 7.3_

  - [x] 11.2 Add cross-session configuration management
    - Implement automatic configuration loading from localStorage on page load
    - Add configuration migration handling for version updates
    - Create localStorage cleanup for expired or invalid configurations
    - Implement user notification for localStorage usage and privacy
    - _Requirements: 7.3, 7.6_

- [ ] 12. Create comprehensive error handling and user feedback
  - [x] 12.1 Implement validation error display
    - Create user-friendly validation error messages for all form fields
    - Add inline validation feedback with clear correction instructions
    - Implement progressive validation (validate as user types)
    - Create validation summary with all errors listed clearly
    - _Requirements: 2.5, 7.4_

  - [x] 12.2 Add API error handling and recovery
    - Implement specific error messages for different API failure scenarios
    - Add retry mechanisms for transient failures
    - Create troubleshooting guides for common configuration issues
    - Implement graceful degradation when backend services are unavailable
    - _Requirements: 3.4, 3.5, 6.4_

- [ ] 13. Implement data export and import functionality
  - [x] 13.1 Add configuration file export/import
    - Create JSON export functionality for configuration backup
    - Implement secure configuration import with validation
    - Add file format validation and error handling for imports
    - Create configuration versioning for backward compatibility
    - _Requirements: 7.3_

  - [x] 13.2 Add billing data export capabilities
    - Implement CSV export for filtered billing data
    - Add Excel export with formatted columns and charts
    - Create export progress indicators for large datasets
    - Add export customization options (date ranges, columns, formats)
    - _Requirements: 4.4, 5.2_

- [ ]\* 14. Create comprehensive test suite
  - [ ]\* 14.1 Write unit tests for core components
    - Test CredentialManager encryption/decryption functionality
    - Test WorkflowParameterManager persistence operations
    - Test configuration validation logic
    - Test data transformation functions
    - _Requirements: 2.1, 2.5, 7.1, 7.2_

  - [ ]\* 14.2 Create integration tests for API functions
    - Test Azure billing API integration with mock responses
    - Test workflow trigger functionality
    - Test error handling scenarios
    - Test data export/import functionality
    - _Requirements: 3.1, 3.2, 3.4, 6.1_

  - [ ]\* 14.3 Add end-to-end testing for user workflows
    - Test complete configuration and workflow execution flow
    - Test persistence across browser sessions
    - Test error recovery and user feedback scenarios
    - Test data visualization and export functionality
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 15. Add performance optimization and monitoring
  - [x] 15.1 Implement data loading optimization
    - Add pagination for large billing datasets
    - Implement lazy loading for data tables and charts
    - Create data caching strategies to reduce API calls
    - Add loading states and progress indicators for all async operations
    - _Requirements: 4.4, 8.5_

  - [x] 15.2 Add user activity monitoring and analytics
    - Implement user action logging for configuration changes
    - Add performance metrics tracking for page load times
    - Create error tracking and monitoring for debugging
    - Add usage analytics for feature adoption and optimization
    - _Requirements: 6.1, 6.4_

- [ ] 16. Create documentation and help system
  - [x] 16.1 Add inline help and tooltips
    - Create comprehensive tooltips for all form fields and options
    - Add contextual help text for complex configuration options
    - Implement help icons with detailed explanations
    - Create quick start guide for new users
    - _Requirements: 2.1, 2.2, 4.6_

  - [x] 16.2 Add troubleshooting and FAQ section
    - Create common error scenarios and solutions
    - Add Azure credential setup instructions
    - Implement diagnostic tools for connection testing
    - Create performance optimization recommendations
    - _Requirements: 6.4, 3.4_
