import polars as pl
import pandas as pd
from api_2_ck_stg_azure_billing_detail_daily_delta import get_columns_from_create_query, get_resource_tracking_str_vectorized

def test_get_resource_tracking_str_vectorized():
    """Test vectorized version with user-provided data."""
    data = {
        'instance_id': [
            "/subscriptions/d82eed84-007b-44fc-927c-e506ca851b21/resourceGroups/MC_CN-PRIMARY-DMZ-PRD-KUBERNET_CN-PRIMARY-DMZ-PRD-KUBERNET-20_CHINAEAST2/providers/Microsoft.Compute/virtualMachineScaleSets/aks-mlp203-16543136-vmss",
            "/subscriptions/d82eed84-007b-44fc-927c-e506ca851b21/resourceGroups/MC_CN-PRIMARY-DMZ-PRD-KUBERNET_CN-PRIMARY-DMZ-PRD-KUBERNET-20_CHINAEAST2/providers/Microsoft.Compute/virtualMachineScaleSets/another-vm"
        ],
        'resource_group': [
            "MC_CN-PRIMARY-DMZ-PRD-KUBERNET_CN-PRIMARY-DMZ-PRD-KUBERNET-20_CHINAEAST2",
            "MC_CN-PRIMARY-DMZ-PRD-KUBERNET_CN-PRIMARY-DMZ-PRD-KUBERNET-20_CHINAEAST2"
        ]
    }
    df = pl.from_pandas(pd.DataFrame(data))
    patterns = [
        ("aks-mlp203-16543136", "aks-mlp203-16543136", 1),
        ("CN-Primary-DMZ-PRD-Kubernet-20", "CN-Primary-DMZ-PRD-Kubernet-20", 1)
        
    ]
    ret, audit_df = get_resource_tracking_str_vectorized(df, patterns)
    ret = ret.to_pandas()
    expected = pd.Series(["AKS-MLP203-16543136", "CN-PRIMARY-DMZ-PRD-KUBERNET-20"], name="")
    pd.testing.assert_series_equal(ret, expected)
    assert not audit_df.is_empty()
    assert audit_df.height == 1
    audit_row = audit_df.to_dicts()[0]
    assert audit_row['last_segment_match'] == "AKS-MLP203-16543136"
    assert audit_row['resource_group_match'] == "CN-PRIMARY-DMZ-PRD-KUBERNET-20"
    assert audit_row['selected_match'] == "AKS-MLP203-16543136"
    
def test_get_resource_tracking_str_vectorized2():
    """Test vectorized version with user-provided data."""
    data = {
        'instance_id': [
            "/subscriptions/e341ef31-7f22-4288-bb95-2ecdbf096353/resourceGroups/Forensics/providers/Microsoft.Storage/storageAccounts/22beilh00380"
        ],
        'resource_group': [
            "Forensics"
        ]
    }
    df = pl.from_pandas(pd.DataFrame(data))
    patterns = [
        ("Forensics", "Forensics", 1)
    ]
    ret, audit_df = get_resource_tracking_str_vectorized(df, patterns)
    ret = ret.to_pandas()
    expected = pd.Series(["FORENSICS"], name="")
    pd.testing.assert_series_equal(ret, expected)
    assert audit_df.is_empty()
    
def test_get_resource_tracking_str_vectorized3():
    """Test vectorized version with user-provided data."""
    data = {
        'instance_id': [
            "/subscriptions/caa427cd-f315-41a2-a828-da3a82466e09/resourcegroups/rg-core-network-prod-cn3-01/providers/microsoft.network/publicipaddresses/nat-gw-public-ip"
        ],
        'resource_group': [
            "rg-core-network-prod-cn3-01"
        ],        
        'subscription_guid': [
            "caa427cd-f315-41a2-a828-da3a82466e09"
        ]
    }
    df = pl.from_pandas(pd.DataFrame(data))
    patterns = [
        ("cAa427cd-f315-41a2-a828-da3a82466e09", "caa427cd-f315-41a2-a828-da3a82466e09", 1),
        ("nat-gw-public-ip2", "nat-gw-public-ip2", 1)
        
    ]
    ret, audit_df = get_resource_tracking_str_vectorized(df, patterns)
    ret = ret.to_pandas()
    expected = pd.Series(["CAA427CD-F315-41A2-A828-DA3A82466E09"], name="")
    pd.testing.assert_series_equal(ret, expected)
    assert audit_df.is_empty()

def test_get_resource_tracking_str_vectorized4():
    """Test vectorized version with user-provided data."""
    data = {
        'instance_id': [
            "/subscriptions/0b6c4b9e-b613-494c-adf1-5851f6009ae2/resourceGroups/databricks-rg-azurechinapnoneviewdevadb-bb2ya6dcdekvs/providers/Microsoft.Storage/storageAccounts/dbstoragewtn3noxlofkne"
        ],
        'resource_group': [
            "databricks-rg-azurechinapnoneviewdevadb-bb2ya6dcdekvs"
        ],       
        'resource_name': [
            "dbstoragewtn3noxlofkne"
        ],        
        'subscription_guid': [
            "0b6c4b9e-b613-494c-adf1-5851f6009ae2"
        ]
    }
    df = pl.from_pandas(pd.DataFrame(data))
    patterns = [
        ("0b6c4b9e-b613-494c-adf1-5851f6009ae2", "0b6c4b9e-b613-494c-adf1-5851f6009ae2", 133),
        ("databricks-rg-azurechinapnoneviewdevadb-bb2ya6dcdekvs", "databricks-rg-azurechinapnoneviewdevadb-bb2ya6dcdekvs", 125)
        
    ]
    ret, audit_df = get_resource_tracking_str_vectorized(df, patterns)
    ret = ret.to_pandas()
    expected = pd.Series(["DATABRICKS-RG-AZURECHINAPNONEVIEWDEVADB-BB2YA6DCDEKVS"], name="")
    # expected = pd.Series(["0B6C4B9E-B613-494C-ADF1-5851F6009AE2"], name="")
    pd.testing.assert_series_equal(ret, expected)
    # assert audit_df.is_empty()

def test_get_resource_tracking_str_vectorized_with_audit():
    """Test vectorized version with audit log generation."""
    data = {
        'instance_id': [
            "/subscriptions/d82eed84-007b-44fc-927c-e506ca851b21/resourceGroups/MC_CN-PRIMARY-DMZ-PRD-KUBERNET_CN-PRIMARY-DMZ-PRD-KUBERNET-20_CHINAEAST2/providers/Microsoft.Compute/virtualMachineScaleSets/aks-mlp203-16543136-vmss"
        ],
        'resource_group': [
            "MC_CN-PRIMARY-DMZ-PRD-KUBERNET_CN-PRIMARY-DMZ-PRD-KUBERNET-20_CHINAEAST2"
        ],
        'subscription_guid': [
            "d82eed84-007b-44fc-927c-e506ca851b21"
        ]
    }
    df = pl.from_pandas(pd.DataFrame(data))
    patterns = [
        ("aks-mlp203-16543136".upper(), "aks-mlp203-16543136".upper(), 1),
        ("CN-PRIMARY-DMZ-PRD-KUBERNET-20".upper(), "CN-PRIMARY-DMZ-PRD-KUBERNET-20".upper(), 2)
    ]
    
    ret, audit_df = get_resource_tracking_str_vectorized(df, patterns)
    ret = ret.to_pandas()
    
    expected_ret = pd.Series(["AKS-MLP203-16543136"], name="")
    pd.testing.assert_series_equal(ret, expected_ret)
    
    assert not audit_df.is_empty()
    assert audit_df.height == 1
    audit_row = audit_df.to_dicts()[0]
    assert audit_row['last_segment_match'] == "AKS-MLP203-16543136"
    assert audit_row['resource_group_match'] == "CN-PRIMARY-DMZ-PRD-KUBERNET-20"
    assert audit_row['selected_match'] == "AKS-MLP203-16543136"
    
def test_get_columns_from_create_query():
    sample_query = '''
    CREATE TABLE IF NOT EXISTS dbo.test_table
    (
        id UInt64,
        name String,
        value Nullable(Float64),
        created_at DateTime DEFAULT now()
    )
    ENGINE = MergeTree()
    ORDER BY id
    '''
    expected_columns = ['id', 'name', 'value', 'created_at']
    result = get_columns_from_create_query(sample_query)
    assert result == expected_columns, f"Expected {expected_columns}, got {result}"