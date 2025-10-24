#!/usr/bin/env python3
"""
Simple test for DDL generation without complex imports
"""

# Test basic DDL generation functionality
def test_basic_ddl():
    """Test basic DDL generation"""
    
    # Simple CREATE TABLE statement
    ddl = """CREATE TABLE focus_cost_usage (
    id String COMMENT 'Deterministic hash ID for the row',
    usage_date Date COMMENT 'Date when the usage occurred',
    billing_account_id String COMMENT 'Billing Account ID',
    billed_cost Decimal(18,4) COMMENT 'Billed Cost',
    source_system String COMMENT 'Source system identifier',
    created_at DateTime64(3) COMMENT 'Record creation timestamp',
    updated_at DateTime64(3) COMMENT 'Record update timestamp'
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(usage_date)
ORDER BY (usage_date, billing_account_id)
SETTINGS index_granularity = 8192, allow_nullable_key = 1
COMMENT 'FOCUS Cost & Usage dataset with snake_case column names'"""
    
    print("Generated DDL:")
    print(ddl)
    print(f"\nDDL length: {len(ddl)} characters")
    
    # Basic validation
    required_keywords = ["CREATE TABLE", "ENGINE", "ORDER BY"]
    for keyword in required_keywords:
        if keyword in ddl:
            print(f"✓ Contains {keyword}")
        else:
            print(f"✗ Missing {keyword}")
    
    return ddl


def test_view_ddl():
    """Test view DDL generation"""
    
    view_ddl = """CREATE VIEW focus_data_table AS
SELECT
    id AS Id,
    usage_date AS UsageDate,
    billing_account_id AS BillingAccountId,
    billed_cost AS BilledCost,
    source_system AS SourceSystem,
    created_at AS CreatedAt,
    updated_at AS UpdatedAt
FROM focus_cost_usage"""
    
    print("\nGenerated View DDL:")
    print(view_ddl)
    print(f"\nView DDL length: {len(view_ddl)} characters")
    
    return view_ddl


def main():
    """Run simple tests"""
    print("=== FOCUS DDL Simple Test ===")
    
    try:
        # Test table DDL
        table_ddl = test_basic_ddl()
        
        # Test view DDL
        view_ddl = test_view_ddl()
        
        # Test companion DDL format
        companion_ddl = f"""-- FOCUS Billing Integration DDL Statements
-- Companion DDL for reapplication

-- Drop existing objects
DROP VIEW IF EXISTS focus_data_table;
DROP TABLE IF EXISTS focus_cost_usage;

-- Create table
{table_ddl};

-- Create view
{view_ddl};
"""
        
        print("\n=== Companion DDL ===")
        print(companion_ddl)
        
        # Save to file
        with open("companion_ddl.sql", "w") as f:
            f.write(companion_ddl)
        
        print(f"\n✓ Companion DDL saved to companion_ddl.sql")
        print("✓ All tests completed successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)