"""
Billing Analytics API

Advanced analytics endpoints for cost optimization, resource utilization,
and billing insights with FOCUS-compliant data.
"""

from moose_lib import ConsumptionApi, EgressConfig
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from .clickhouse_client import ClickHouseClient, FOCUSQueryBuilder

logger = logging.getLogger(__name__)


class CostTrendPoint(BaseModel):
    """Cost trend data point"""
    date: date
    total_cost: Decimal
    record_count: int
    avg_cost_per_record: Decimal


class CostTrendQuery(BaseModel):
    """Cost trend analysis query parameters"""
    start_date: date
    end_date: date
    granularity: str = Field(default="daily", pattern="^(daily|weekly|monthly)$")
    billing_account_ids: Optional[List[str]] = None
    service_categories: Optional[List[str]] = None
    regions: Optional[List[str]] = None


class CostTrendResponse(BaseModel):
    """Cost trend analysis response"""
    trend_data: List[CostTrendPoint]
    summary: Dict[str, Any]
    period_comparison: Optional[Dict[str, Any]] = None


class ResourceUtilizationMetric(BaseModel):
    """Resource utilization metric"""
    resource_type: str
    service_category: str
    region: str
    total_cost: Decimal
    total_usage: Optional[Decimal]
    usage_unit: Optional[str]
    cost_per_unit: Optional[Decimal]
    efficiency_score: Optional[float]


class ResourceUtilizationQuery(BaseModel):
    """Resource utilization query parameters"""
    start_date: date
    end_date: date
    resource_types: Optional[List[str]] = None
    service_categories: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    min_cost_threshold: Optional[Decimal] = Field(default=Decimal('1.0'), ge=0)
    limit: Optional[int] = Field(default=100, ge=1, le=1000)


class ResourceUtilizationResponse(BaseModel):
    """Resource utilization response"""
    utilization_metrics: List[ResourceUtilizationMetric]
    summary: Dict[str, Any]
    recommendations: List[str]


class CostOptimizationOpportunity(BaseModel):
    """Cost optimization opportunity"""
    opportunity_type: str
    resource_id: Optional[str]
    resource_name: Optional[str]
    service_category: str
    current_cost: Decimal
    potential_savings: Decimal
    savings_percentage: float
    recommendation: str
    confidence_score: float


class CostOptimizationQuery(BaseModel):
    """Cost optimization analysis query parameters"""
    start_date: date
    end_date: date
    billing_account_ids: Optional[List[str]] = None
    service_categories: Optional[List[str]] = None
    min_savings_threshold: Optional[Decimal] = Field(default=Decimal('10.0'), ge=0)
    limit: Optional[int] = Field(default=50, ge=1, le=200)


class CostOptimizationResponse(BaseModel):
    """Cost optimization response"""
    opportunities: List[CostOptimizationOpportunity]
    total_potential_savings: Decimal
    summary: Dict[str, Any]


class ServiceCostBreakdown(BaseModel):
    """Service cost breakdown"""
    service_category: str
    service_name: str
    total_cost: Decimal
    percentage_of_total: float
    record_count: int
    avg_cost_per_record: Decimal
    trend: str  # increasing, decreasing, stable


class ServiceAnalysisQuery(BaseModel):
    """Service cost analysis query parameters"""
    start_date: date
    end_date: date
    billing_account_ids: Optional[List[str]] = None
    top_n: Optional[int] = Field(default=20, ge=1, le=100)
    include_trend: bool = True


class ServiceAnalysisResponse(BaseModel):
    """Service cost analysis response"""
    service_breakdown: List[ServiceCostBreakdown]
    total_cost: Decimal
    summary: Dict[str, Any]


async def get_cost_trends(client, params: CostTrendQuery) -> CostTrendResponse:
    """
    Analyze cost trends over time with configurable granularity.
    
    Args:
        client: Enhanced ClickHouse client for executing queries
        params: Cost trend query parameters
        
    Returns:
        CostTrendResponse with trend analysis
    """
    
    # Determine date grouping based on granularity
    date_group_expr = {
        "daily": "usage_date",
        "weekly": "toMonday(usage_date)",
        "monthly": "toStartOfMonth(usage_date)"
    }
    
    group_expr = date_group_expr[params.granularity]
    
    # Build optimized query with ClickHouse-specific functions
    select_fields = [
        f"{group_expr} as period_date",
        "sum(billed_cost) as total_cost",
        "count(*) as record_count",
        "avg(billed_cost) as avg_cost_per_record"
    ]
    
    where_conditions = [
        "usage_date >= {start_date}",
        "usage_date <= {end_date}"
    ]
    
    query_params = {
        "start_date": params.start_date,
        "end_date": params.end_date
    }
    
    # Add filters
    if params.billing_account_ids:
        where_conditions.append("billing_account_id IN {billing_account_ids}")
        query_params["billing_account_ids"] = params.billing_account_ids
    
    if params.service_categories:
        where_conditions.append("service_category IN {service_categories}")
        query_params["service_categories"] = params.service_categories
    
    if params.regions:
        where_conditions.append("region IN {regions}")
        query_params["regions"] = params.regions
    
    try:
        # Use enhanced ClickHouse client for optimized execution
        result = await client.execute_aggregation_query(
            table="focus_billing_data",
            select_fields=select_fields,
            where_conditions=where_conditions,
            group_by=[group_expr],
            order_by="period_date",
            parameters=query_params
        )
        
        # Convert results to trend points
        trend_data = []
        total_cost = Decimal('0')
        total_records = 0
        
        for item in result:
            cost = Decimal(str(item['total_cost']))
            records = int(item['record_count'])
            avg_cost = Decimal(str(item['avg_cost_per_record']))
            
            trend_data.append(CostTrendPoint(
                date=item['period_date'],
                total_cost=cost,
                record_count=records,
                avg_cost_per_record=avg_cost
            ))
            
            total_cost += cost
            total_records += records
        
        # Calculate summary
        summary = {
            "total_cost": total_cost,
            "total_records": total_records,
            "avg_cost_per_period": total_cost / len(trend_data) if trend_data else Decimal('0'),
            "period_count": len(trend_data),
            "granularity": params.granularity
        }
        
        # Calculate period comparison (current vs previous period)
        period_comparison = None
        if len(trend_data) >= 2:
            current_period_cost = trend_data[-1].total_cost
            previous_period_cost = trend_data[-2].total_cost
            
            if previous_period_cost > 0:
                change_percentage = float((current_period_cost - previous_period_cost) / previous_period_cost * 100)
                period_comparison = {
                    "current_period_cost": current_period_cost,
                    "previous_period_cost": previous_period_cost,
                    "change_amount": current_period_cost - previous_period_cost,
                    "change_percentage": change_percentage,
                    "trend_direction": "increasing" if change_percentage > 0 else "decreasing" if change_percentage < 0 else "stable"
                }
        
        return CostTrendResponse(
            trend_data=trend_data,
            summary=summary,
            period_comparison=period_comparison
        )
        
    except Exception as e:
        logger.error(f"Error executing cost trend query: {e}")
        raise


def get_resource_utilization(client, params: ResourceUtilizationQuery) -> ResourceUtilizationResponse:
    """
    Analyze resource utilization and efficiency metrics.
    
    Args:
        client: Database client for executing queries
        params: Resource utilization query parameters
        
    Returns:
        ResourceUtilizationResponse with utilization analysis
    """
    
    query = """
        SELECT
            resource_type,
            service_category,
            region,
            sum(billed_cost) as total_cost,
            sum(usage_quantity) as total_usage,
            any(usage_unit) as usage_unit,
            avg(billed_cost / nullIf(usage_quantity, 0)) as cost_per_unit
        FROM focus_billing_data
        WHERE usage_date >= {start_date}
          AND usage_date <= {end_date}
          AND billed_cost >= {min_cost_threshold}
    """
    
    query_params = {
        "start_date": params.start_date,
        "end_date": params.end_date,
        "min_cost_threshold": params.min_cost_threshold
    }
    
    # Add filters
    if params.resource_types:
        query += " AND resource_type IN {resource_types}"
        query_params["resource_types"] = params.resource_types
    
    if params.service_categories:
        query += " AND service_category IN {service_categories}"
        query_params["service_categories"] = params.service_categories
    
    if params.regions:
        query += " AND region IN {regions}"
        query_params["regions"] = params.regions
    
    query += " GROUP BY resource_type, service_category, region"
    query += " ORDER BY total_cost DESC"
    
    if params.limit:
        query += f" LIMIT {params.limit}"
    
    try:
        result = client.query.execute(query, query_params)
        
        # Convert results to utilization metrics
        utilization_metrics = []
        total_cost = Decimal('0')
        
        for item in result:
            cost = Decimal(str(item['total_cost']))
            usage = Decimal(str(item['total_usage'])) if item['total_usage'] else None
            cost_per_unit = Decimal(str(item['cost_per_unit'])) if item['cost_per_unit'] else None
            
            # Calculate efficiency score (simplified)
            efficiency_score = None
            if usage and cost_per_unit:
                # Higher usage with lower cost per unit = higher efficiency
                efficiency_score = min(float(usage / (cost_per_unit + 1)), 10.0)
            
            utilization_metrics.append(ResourceUtilizationMetric(
                resource_type=item['resource_type'] or 'Unknown',
                service_category=item['service_category'] or 'Other',
                region=item['region'] or 'Unknown',
                total_cost=cost,
                total_usage=usage,
                usage_unit=item['usage_unit'],
                cost_per_unit=cost_per_unit,
                efficiency_score=efficiency_score
            ))
            
            total_cost += cost
        
        # Generate recommendations
        recommendations = []
        
        # Find high-cost, low-efficiency resources
        high_cost_low_efficiency = [
            m for m in utilization_metrics 
            if m.total_cost > total_cost * Decimal('0.1') and 
               m.efficiency_score and m.efficiency_score < 3.0
        ]
        
        if high_cost_low_efficiency:
            recommendations.append(
                f"Consider optimizing {len(high_cost_low_efficiency)} high-cost, low-efficiency resources"
            )
        
        # Find unused resources
        unused_resources = [m for m in utilization_metrics if m.total_usage == 0]
        if unused_resources:
            recommendations.append(
                f"Review {len(unused_resources)} resources with zero usage for potential decommissioning"
            )
        
        summary = {
            "total_cost": total_cost,
            "resource_count": len(utilization_metrics),
            "avg_efficiency_score": sum(m.efficiency_score for m in utilization_metrics if m.efficiency_score) / len([m for m in utilization_metrics if m.efficiency_score]) if utilization_metrics else 0,
            "top_cost_resource_type": utilization_metrics[0].resource_type if utilization_metrics else None
        }
        
        return ResourceUtilizationResponse(
            utilization_metrics=utilization_metrics,
            summary=summary,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error executing resource utilization query: {e}")
        raise


def get_cost_optimization_opportunities(client, params: CostOptimizationQuery) -> CostOptimizationResponse:
    """
    Identify cost optimization opportunities and potential savings.
    
    Args:
        client: Database client for executing queries
        params: Cost optimization query parameters
        
    Returns:
        CostOptimizationResponse with optimization opportunities
    """
    
    # This is a simplified implementation - in practice, you'd have more sophisticated
    # algorithms to identify optimization opportunities
    
    query = """
        SELECT
            resource_id,
            resource_name,
            service_category,
            sum(billed_cost) as total_cost,
            avg(billed_cost) as avg_cost,
            count(*) as usage_days,
            sum(usage_quantity) as total_usage
        FROM focus_billing_data
        WHERE usage_date >= {start_date}
          AND usage_date <= {end_date}
    """
    
    query_params = {
        "start_date": params.start_date,
        "end_date": params.end_date
    }
    
    # Add filters
    if params.billing_account_ids:
        query += " AND billing_account_id IN {billing_account_ids}"
        query_params["billing_account_ids"] = params.billing_account_ids
    
    if params.service_categories:
        query += " AND service_category IN {service_categories}"
        query_params["service_categories"] = params.service_categories
    
    query += " GROUP BY resource_id, resource_name, service_category"
    query += " HAVING total_cost > {min_savings_threshold}"
    query_params["min_savings_threshold"] = params.min_savings_threshold
    
    query += " ORDER BY total_cost DESC"
    
    if params.limit:
        query += f" LIMIT {params.limit}"
    
    try:
        result = client.query.execute(query, query_params)
        
        opportunities = []
        total_potential_savings = Decimal('0')
        
        for item in result:
            total_cost = Decimal(str(item['total_cost']))
            usage_days = int(item['usage_days'])
            total_usage = Decimal(str(item['total_usage'])) if item['total_usage'] else Decimal('0')
            
            # Identify optimization opportunities (simplified logic)
            
            # 1. Underutilized resources (low usage days relative to period)
            period_days = (params.end_date - params.start_date).days + 1
            utilization_rate = usage_days / period_days
            
            if utilization_rate < 0.3:  # Less than 30% utilization
                potential_savings = total_cost * Decimal('0.7')  # Assume 70% savings possible
                opportunities.append(CostOptimizationOpportunity(
                    opportunity_type="underutilized_resource",
                    resource_id=item['resource_id'],
                    resource_name=item['resource_name'],
                    service_category=item['service_category'],
                    current_cost=total_cost,
                    potential_savings=potential_savings,
                    savings_percentage=70.0,
                    recommendation=f"Resource used only {utilization_rate:.1%} of the time. Consider rightsizing or scheduling.",
                    confidence_score=0.8
                ))
                total_potential_savings += potential_savings
            
            # 2. High-cost resources (potential for reserved instances or committed use)
            elif total_cost > Decimal('1000'):  # High cost threshold
                potential_savings = total_cost * Decimal('0.2')  # Assume 20% savings with reservations
                opportunities.append(CostOptimizationOpportunity(
                    opportunity_type="reservation_opportunity",
                    resource_id=item['resource_id'],
                    resource_name=item['resource_name'],
                    service_category=item['service_category'],
                    current_cost=total_cost,
                    potential_savings=potential_savings,
                    savings_percentage=20.0,
                    recommendation="High-cost resource suitable for reserved instances or committed use discounts.",
                    confidence_score=0.6
                ))
                total_potential_savings += potential_savings
        
        # Sort opportunities by potential savings
        opportunities.sort(key=lambda x: x.potential_savings, reverse=True)
        
        summary = {
            "total_opportunities": len(opportunities),
            "total_potential_savings": total_potential_savings,
            "avg_savings_per_opportunity": total_potential_savings / len(opportunities) if opportunities else Decimal('0'),
            "opportunity_types": {
                "underutilized_resource": len([o for o in opportunities if o.opportunity_type == "underutilized_resource"]),
                "reservation_opportunity": len([o for o in opportunities if o.opportunity_type == "reservation_opportunity"])
            }
        }
        
        return CostOptimizationResponse(
            opportunities=opportunities,
            total_potential_savings=total_potential_savings,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error executing cost optimization query: {e}")
        raise


def get_service_analysis(client, params: ServiceAnalysisQuery) -> ServiceAnalysisResponse:
    """
    Analyze service cost breakdown and trends.
    
    Args:
        client: Database client for executing queries
        params: Service analysis query parameters
        
    Returns:
        ServiceAnalysisResponse with service breakdown
    """
    
    query = """
        SELECT
            service_category,
            service_name,
            sum(billed_cost) as total_cost,
            count(*) as record_count,
            avg(billed_cost) as avg_cost_per_record
        FROM focus_billing_data
        WHERE usage_date >= {start_date}
          AND usage_date <= {end_date}
    """
    
    query_params = {
        "start_date": params.start_date,
        "end_date": params.end_date
    }
    
    if params.billing_account_ids:
        query += " AND billing_account_id IN {billing_account_ids}"
        query_params["billing_account_ids"] = params.billing_account_ids
    
    query += " GROUP BY service_category, service_name"
    query += " ORDER BY total_cost DESC"
    
    if params.top_n:
        query += f" LIMIT {params.top_n}"
    
    try:
        result = client.query.execute(query, query_params)
        
        # Calculate total cost for percentage calculations
        total_cost = sum(Decimal(str(item['total_cost'])) for item in result)
        
        service_breakdown = []
        
        for item in result:
            cost = Decimal(str(item['total_cost']))
            records = int(item['record_count'])
            avg_cost = Decimal(str(item['avg_cost_per_record']))
            
            percentage = float(cost / total_cost * 100) if total_cost > 0 else 0.0
            
            # Calculate trend (simplified - would need historical data for real trend)
            trend = "stable"  # Default
            
            service_breakdown.append(ServiceCostBreakdown(
                service_category=item['service_category'] or 'Other',
                service_name=item['service_name'] or 'Unknown',
                total_cost=cost,
                percentage_of_total=percentage,
                record_count=records,
                avg_cost_per_record=avg_cost,
                trend=trend
            ))
        
        summary = {
            "total_cost": total_cost,
            "service_count": len(service_breakdown),
            "top_service_category": service_breakdown[0].service_category if service_breakdown else None,
            "top_service_cost": service_breakdown[0].total_cost if service_breakdown else Decimal('0'),
            "cost_concentration": service_breakdown[0].percentage_of_total if service_breakdown else 0.0
        }
        
        return ServiceAnalysisResponse(
            service_breakdown=service_breakdown,
            total_cost=total_cost,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error executing service analysis query: {e}")
        raise


# Create the consumption APIs
cost_trends_api = ConsumptionApi[CostTrendQuery, CostTrendResponse](
    "getCostTrends",
    query_function=get_cost_trends,
    source="focus_billing_data",
    config=EgressConfig()
)

resource_utilization_api = ConsumptionApi[ResourceUtilizationQuery, ResourceUtilizationResponse](
    "getResourceUtilization",
    query_function=get_resource_utilization,
    source="focus_billing_data", 
    config=EgressConfig()
)

cost_optimization_api = ConsumptionApi[CostOptimizationQuery, CostOptimizationResponse](
    "getCostOptimizationOpportunities",
    query_function=get_cost_optimization_opportunities,
    source="focus_billing_data",
    config=EgressConfig()
)

service_analysis_api = ConsumptionApi[ServiceAnalysisQuery, ServiceAnalysisResponse](
    "getServiceAnalysis",
    query_function=get_service_analysis,
    source="focus_billing_data",
    config=EgressConfig()
)
