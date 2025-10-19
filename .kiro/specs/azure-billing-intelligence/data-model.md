# Azure Billing Intelligence Data Model

## Overview

The Azure Billing Intelligence (ABI) system implements a dual data model architecture based on the FinOps Open Cost and Usage Specification (FOCUS). This approach separates source data models from the canonical target data model, enabling flexible data ingestion from multiple sources while maintaining standardized analytics and reporting.

## FOCUS Specification Implementation

### Core FOCUS Dimensions

Based on the FinOps Open Cost and Usage Specification (FOCUS), the canonical data model includes:

#### 1. Billing Dimensions
```sql
-- Core billing fact table following FOCUS specification
CREATE TABLE focus_billing_data (
    -- FOCUS Required Dimensions
    billing_account_id VARCHAR(255) NOT NULL,
    billing_account_name VARCHAR(255),
    billing_currency VARCHAR(3) NOT NULL,
    billing_period_start_date DATE NOT NULL,
    billing_period_end_date DATE NOT NULL,
    
    -- FOCUS Cost Dimensions
    billed_cost DECIMAL(18,4) NOT NULL,
    effective_cost DECIMAL(18,4),
    list_cost DECIMAL(18,4),
    list_unit_price DECIMAL(18,4),
    
    -- FOCUS Usage Dimensions
    usage_date DATE NOT NULL,
    usage_quantity DECIMAL(18,4),
    usage_unit VARCHAR(50),
    
    -- FOCUS Resource Dimensions
    resource_id VARCHAR(500),
    resource_name VARCHAR(255),
    resource_type VARCHAR(100),
    
    -- FOCUS Service Dimensions
    service_category VARCHAR(100),
    service_name VARCHAR(255),
    
    -- FOCUS Geographic Dimensions
    availability_zone VARCHAR(50),
    region VARCHAR(100),
    
    -- FOCUS Pricing Dimensions
    pricing_category VARCHAR(50),
    pricing_unit VARCHAR(50),
    
    -- FOCUS Provider Dimensions
    provider VARCHAR(50) NOT NULL DEFAULT 'Azure',
    
    -- FOCUS Metadata
    invoice_issuer VARCHAR(255),
    
    -- Partitioning and Indexing
    partition_date DATE GENERATED ALWAYS AS (usage_date) STORED,
    
    PRIMARY KEY (billing_account_id, usage_date, resource_id, service_name)
) 
PARTITION BY RANGE (partition_date)
ORDER BY (usage_date, billing_account_id, service_name);
```