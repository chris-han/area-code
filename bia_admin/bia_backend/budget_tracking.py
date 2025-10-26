"""
Budget Tracking API

Provides budget vs actual cost analysis endpoints with
FOCUS-compliant data and variance calculations.
"""

from datetime import date, datetime
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from bia_backend.dependencies import get_clickhouse_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/focus", tags=["budget-tracking"])


class BudgetTrackingRequest(BaseModel):
    """Budget tracking request parameters"""
    start_date: date
    end_date: date
    billing_account_ids: Optional[List[str]] = None
    service_categories: Optional[List[str]] = None


class BudgetItem(BaseModel):
    """Budget item with actual and forecasted costs"""
    budget_name: str
    budget_amount: Decimal
    actual_spend: Decimal
    forecasted_spend: Decimal
    variance_percentage: float
    period: str
    billing_account_id: Optional[str] = None
    service_category: Optional[str] = None


class BudgetTrackingResponse(BaseModel):
    """Budget tracking response"""
    budgets: List[BudgetItem]
    total_budget: Decimal
    total_actual: Decimal
    total_forecasted: Decimal
    overall_variance: float
    period: str


@router.post("/budget-tracking", response_model=BudgetTrackingResponse)
async def get_budget_tracking(
    request: BudgetTrackingRequest,
    client: Any = Depends(get_clickhouse_client),
) -> BudgetTrackingResponse:
    """
    Get budget tracking data with actual vs forecasted costs.
    
    This endpoint calculates:
    - Actual spend for the period
    - Forecasted spend based on current trends
    - Variance percentage
    - Budget status
    """
    
    try:
        # Query actual costs
        actual_query = """
            SELECT 
                billing_account_id,
                billing_account_name,
                service_category,
                sum(billed_cost) as actual_spend,
                count(*) as record_count
            FROM focus_billing_data
            WHERE usage_date >= {start_date:Date}
              AND usage_date <= {end_date:Date}
        """
        
        where_conditions = []
        params = {
            "start_date": request.start_date,
            "end_date": request.end_date
        }
        
        if request.billing_account_ids:
            where_conditions.append("billing_account_id IN {billing_account_ids:Array(String)}")
            params["billing_account_ids"] = request.billing_account_ids
        
        if request.service_categories:
            where_conditions.append("service_category IN {service_categories:Array(String)}")
            params["service_categories"] = request.service_categories
        
        if where_conditions:
            actual_query += " AND " + " AND ".join(where_conditions)
        
        actual_query += """
            GROUP BY billing_account_id, billing_account_name, service_category
            ORDER BY actual_spend DESC
        """
        
        # Execute query
        result = client.query(actual_query, params)
        
        # Process results
        budgets = []
        total_budget = Decimal('0')
        total_actual = Decimal('0')
        total_forecasted = Decimal('0')
        
        for row in result.result_rows:
            billing_account_id = row[0]
            billing_account_name = row[1]
            service_category = row[2]
            actual_spend = Decimal(str(row[3]))
            
            # Calculate budget (simplified - in production this would come from a budget table)
            # For now, assume budget is 120% of actual spend
            budget_amount = actual_spend * Decimal('1.2')
            
            # Calculate forecast (simplified - in production this would use trend analysis)
            # For now, assume forecast is 110% of actual spend
            forecasted_spend = actual_spend * Decimal('1.1')
            
            # Calculate variance
            variance_percentage = float(
                ((actual_spend - budget_amount) / budget_amount * 100) 
                if budget_amount > 0 else 0
            )
            
            budget_name = f"{billing_account_name or billing_account_id}"
            if service_category:
                budget_name += f" - {service_category}"
            
            budgets.append(BudgetItem(
                budget_name=budget_name,
                budget_amount=budget_amount,
                actual_spend=actual_spend,
                forecasted_spend=forecasted_spend,
                variance_percentage=variance_percentage,
                period=f"{request.start_date} to {request.end_date}",
                billing_account_id=billing_account_id,
                service_category=service_category
            ))
            
            total_budget += budget_amount
            total_actual += actual_spend
            total_forecasted += forecasted_spend
        
        # Calculate overall variance
        overall_variance = float(
            ((total_actual - total_budget) / total_budget * 100)
            if total_budget > 0 else 0
        )
        
        return BudgetTrackingResponse(
            budgets=budgets,
            total_budget=total_budget,
            total_actual=total_actual,
            total_forecasted=total_forecasted,
            overall_variance=overall_variance,
            period=f"{request.start_date} to {request.end_date}"
        )
        
    except Exception as e:
        logger.error(f"Error fetching budget tracking data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/budget-summary")
async def get_budget_summary(
    billing_account_id: Optional[str] = None,
    client = Depends(get_clickhouse_client)
) -> Dict[str, Any]:
    """
    Get high-level budget summary metrics.
    """
    
    try:
        query = """
            SELECT 
                sum(billed_cost) as total_cost,
                count(DISTINCT billing_account_id) as account_count,
                count(DISTINCT service_category) as service_count,
                min(usage_date) as earliest_date,
                max(usage_date) as latest_date
            FROM focus_billing_data
            WHERE 1=1
        """
        
        params = {}
        
        if billing_account_id:
            query += " AND billing_account_id = {billing_account_id:String}"
            params["billing_account_id"] = billing_account_id
        
        result = client.query(query, params)
        row = result.result_rows[0]
        
        return {
            "total_cost": float(row[0]) if row[0] else 0,
            "account_count": row[1],
            "service_count": row[2],
            "earliest_date": str(row[3]) if row[3] else None,
            "latest_date": str(row[4]) if row[4] else None
        }
        
    except Exception as e:
        logger.error(f"Error fetching budget summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
