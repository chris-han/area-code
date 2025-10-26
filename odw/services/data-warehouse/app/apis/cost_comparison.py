from moose_lib import ConsumptionApi, ConsumptionApiConfig
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

class CostComparisonRequest(BaseModel):
    billing_period_start: str
    billing_period_end: str
    provider_name: Optional[str] = None
    billing_account_id: Optional[str] = None

class CostComparisonRow(BaseModel):
    provider_name: str
    billing_account_id: str
    service_name: str
    total_effective_cost: Decimal
    total_billed_cost: Decimal
    total_list_cost: Decimal
    effective_discount: Decimal

def get_cost_comparison(client, request: CostComparisonRequest) -> List[CostComparisonRow]:
    provider_filter = f"AND provider_name = '{request.provider_name}'" if request.provider_name else ""
    account_filter = f"AND billing_account_id = '{request.billing_account_id}'" if request.billing_account_id else ""

    query = f"""
        WITH AggregatedData AS (
            SELECT provider_name, billing_account_id, service_name,
                   SUM(effective_cost) AS total_effective_cost,
                   SUM(billed_cost) AS total_billed_cost,
                   SUM(list_cost) AS total_list_cost
            FROM focus_data_table
            WHERE billing_period_start >= '{request.billing_period_start}'
              AND billing_period_end < '{request.billing_period_end}'
              {provider_filter}
              {account_filter}
            GROUP BY provider_name, billing_account_id, service_name
        )
        SELECT *,
               (1 - (total_effective_cost / NULLIF(total_list_cost, 0))) * 100 AS effective_discount
        FROM AggregatedData
        ORDER BY total_effective_cost DESC
        LIMIT 100
    """

    result = client.query(query)
    return [CostComparisonRow(**row) for row in result.named_results()]

cost_comparison = ConsumptionApi[CostComparisonRequest, List[CostComparisonRow]](
    name="CostComparison",
    query_function=get_cost_comparison,
    config=ConsumptionApiConfig()
)
