"""
Automated Report Generation System

Comprehensive report generation system for Azure billing intelligence
with scheduled report creation, distribution, and analytics.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import json
import asyncio
from pathlib import Path

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

from ..models.focus_models import FOCUSBillingRecord
from ..transformations.transformation_engine import TransformationEngine
from ..validation.focus_validator import FOCUSValidator

logger = logging.getLogger(__name__)


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    report_id: str
    report_name: str
    report_type: str  # 'cost_analysis', 'usage_summary', 'budget_variance', 'custom'
    output_format: str  # 'pdf', 'excel', 'csv', 'json'
    schedule: str  # cron expression
    recipients: List[str]
    filters: Dict[str, Any]
    template_id: Optional[str] = None
    custom_queries: Optional[List[str]] = None
    enabled: bool = True


@dataclass
class ReportData:
    """Container for report data and metadata"""
    report_id: str
    generated_at: datetime
    data_period_start: datetime
    data_period_end: datetime
    total_records: int
    total_cost: float
    currency: str
    summary_metrics: Dict[str, Any]
    detailed_data: List[Dict[str, Any]]
    charts_data: Optional[Dict[str, Any]] = None


@dataclass
class ReportOutput:
    """Report output container"""
    report_id: str
    file_path: str
    file_size: int
    format: str
    generated_at: datetime
    metadata: Dict[str, Any]


# Temporal Activities
@activity.defn
async def generate_cost_analysis_report(config: ReportConfig, 
                                      start_date: str, 
                                      end_date: str) -> ReportData:
    """
    Generate cost analysis report with detailed breakdowns
    
    Args:
        config: Report configuration
        start_date: Start date for analysis (YYYY-MM-DD)
        end_date: End date for analysis (YYYY-MM-DD)
        
    Returns:
        ReportData with cost analysis results
    """
    logger.info(f"Generating cost analysis report: {config.report_id}")
    
    try:
        # Initialize transformation engine
        engine = TransformationEngine()
        
        # Build query based on filters
        query = _build_cost_analysis_query(config.filters, start_date, end_date)
        
        # Execute query and get results
        raw_data = await engine.execute_query(query)
        
        # Process and aggregate data
        summary_metrics = _calculate_cost_metrics(raw_data)
        detailed_data = _format_cost_breakdown(raw_data)
        charts_data = _generate_cost_charts_data(raw_data)
        
        return ReportData(
            report_id=config.report_id,
            generated_at=datetime.utcnow(),
            data_period_start=datetime.fromisoformat(start_date),
            data_period_end=datetime.fromisoformat(end_date),
            total_records=len(raw_data),
            total_cost=summary_metrics.get('total_cost', 0.0),
            currency=summary_metrics.get('currency', 'USD'),
            summary_metrics=summary_metrics,
            detailed_data=detailed_data,
            charts_data=charts_data
        )
        
    except Exception as e:
        logger.error(f"Error generating cost analysis report: {e}")
        raise


@activity.defn
async def generate_usage_summary_report(config: ReportConfig,
                                      start_date: str,
                                      end_date: str) -> ReportData:
    """
    Generate usage summary report with resource utilization metrics
    
    Args:
        config: Report configuration
        start_date: Start date for analysis
        end_date: End date for analysis
        
    Returns:
        ReportData with usage summary
    """
    logger.info(f"Generating usage summary report: {config.report_id}")
    
    try:
        engine = TransformationEngine()
        
        # Build usage analysis query
        query = _build_usage_summary_query(config.filters, start_date, end_date)
        raw_data = await engine.execute_query(query)
        
        # Calculate usage metrics
        summary_metrics = _calculate_usage_metrics(raw_data)
        detailed_data = _format_usage_breakdown(raw_data)
        charts_data = _generate_usage_charts_data(raw_data)
        
        return ReportData(
            report_id=config.report_id,
            generated_at=datetime.utcnow(),
            data_period_start=datetime.fromisoformat(start_date),
            data_period_end=datetime.fromisoformat(end_date),
            total_records=len(raw_data),
            total_cost=summary_metrics.get('total_cost', 0.0),
            currency=summary_metrics.get('currency', 'USD'),
            summary_metrics=summary_metrics,
            detailed_data=detailed_data,
            charts_data=charts_data
        )
        
    except Exception as e:
        logger.error(f"Error generating usage summary report: {e}")
        raise


@activity.defn
async def generate_budget_variance_report(config: ReportConfig,
                                        start_date: str,
                                        end_date: str) -> ReportData:
    """
    Generate budget variance report comparing actual vs budgeted costs
    
    Args:
        config: Report configuration
        start_date: Start date for analysis
        end_date: End date for analysis
        
    Returns:
        ReportData with budget variance analysis
    """
    logger.info(f"Generating budget variance report: {config.report_id}")
    
    try:
        engine = TransformationEngine()
        
        # Get actual costs
        actual_query = _build_cost_analysis_query(config.filters, start_date, end_date)
        actual_data = await engine.execute_query(actual_query)
        
        # Get budget data (this would come from budget management system)
        budget_data = await _get_budget_data(config.filters, start_date, end_date)
        
        # Calculate variance metrics
        summary_metrics = _calculate_budget_variance_metrics(actual_data, budget_data)
        detailed_data = _format_budget_variance_breakdown(actual_data, budget_data)
        charts_data = _generate_budget_variance_charts_data(actual_data, budget_data)
        
        return ReportData(
            report_id=config.report_id,
            generated_at=datetime.utcnow(),
            data_period_start=datetime.fromisoformat(start_date),
            data_period_end=datetime.fromisoformat(end_date),
            total_records=len(actual_data),
            total_cost=summary_metrics.get('actual_cost', 0.0),
            currency=summary_metrics.get('currency', 'USD'),
            summary_metrics=summary_metrics,
            detailed_data=detailed_data,
            charts_data=charts_data
        )
        
    except Exception as e:
        logger.error(f"Error generating budget variance report: {e}")
        raise


@activity.defn
async def generate_custom_report(config: ReportConfig,
                               start_date: str,
                               end_date: str) -> ReportData:
    """
    Generate custom report based on user-defined queries and templates
    
    Args:
        config: Report configuration with custom queries
        start_date: Start date for analysis
        end_date: End date for analysis
        
    Returns:
        ReportData with custom analysis results
    """
    logger.info(f"Generating custom report: {config.report_id}")
    
    try:
        engine = TransformationEngine()
        
        if not config.custom_queries:
            raise ValueError("Custom queries not provided for custom report")
        
        all_data = []
        summary_metrics = {}
        
        # Execute each custom query
        for i, query in enumerate(config.custom_queries):
            # Replace date placeholders in query
            formatted_query = query.replace('{start_date}', start_date)
            formatted_query = formatted_query.replace('{end_date}', end_date)
            
            # Apply filters to query
            filtered_query = _apply_filters_to_query(formatted_query, config.filters)
            
            # Execute query
            query_data = await engine.execute_query(filtered_query)
            all_data.extend(query_data)
            
            # Calculate metrics for this query
            query_metrics = _calculate_custom_metrics(query_data, f"query_{i}")
            summary_metrics.update(query_metrics)
        
        # Format results
        detailed_data = _format_custom_breakdown(all_data)
        charts_data = _generate_custom_charts_data(all_data, config.template_id)
        
        return ReportData(
            report_id=config.report_id,
            generated_at=datetime.utcnow(),
            data_period_start=datetime.fromisoformat(start_date),
            data_period_end=datetime.fromisoformat(end_date),
            total_records=len(all_data),
            total_cost=summary_metrics.get('total_cost', 0.0),
            currency=summary_metrics.get('currency', 'USD'),
            summary_metrics=summary_metrics,
            detailed_data=detailed_data,
            charts_data=charts_data
        )
        
    except Exception as e:
        logger.error(f"Error generating custom report: {e}")
        raise


@activity.defn
async def format_report_output(report_data: ReportData, 
                             output_format: str,
                             template_id: Optional[str] = None) -> ReportOutput:
    """
    Format report data into specified output format
    
    Args:
        report_data: Report data to format
        output_format: Target format ('pdf', 'excel', 'csv', 'json')
        template_id: Optional template identifier
        
    Returns:
        ReportOutput with formatted file information
    """
    logger.info(f"Formatting report {report_data.report_id} as {output_format}")
    
    try:
        if output_format.lower() == 'pdf':
            return await _format_pdf_report(report_data, template_id)
        elif output_format.lower() == 'excel':
            return await _format_excel_report(report_data, template_id)
        elif output_format.lower() == 'csv':
            return await _format_csv_report(report_data)
        elif output_format.lower() == 'json':
            return await _format_json_report(report_data)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
            
    except Exception as e:
        logger.error(f"Error formatting report output: {e}")
        raise


@activity.defn
async def distribute_report(report_output: ReportOutput, 
                          recipients: List[str],
                          config: ReportConfig) -> Dict[str, Any]:
    """
    Distribute generated report to specified recipients
    
    Args:
        report_output: Generated report output
        recipients: List of recipient email addresses
        config: Report configuration
        
    Returns:
        Distribution results
    """
    logger.info(f"Distributing report {report_output.report_id} to {len(recipients)} recipients")
    
    try:
        distribution_results = {
            "report_id": report_output.report_id,
            "distributed_at": datetime.utcnow().isoformat(),
            "recipients": recipients,
            "success_count": 0,
            "failure_count": 0,
            "errors": []
        }
        
        for recipient in recipients:
            try:
                # Send email with report attachment
                await _send_report_email(
                    recipient=recipient,
                    report_output=report_output,
                    config=config
                )
                distribution_results["success_count"] += 1
                logger.info(f"Successfully sent report to {recipient}")
                
            except Exception as e:
                distribution_results["failure_count"] += 1
                distribution_results["errors"].append(f"{recipient}: {str(e)}")
                logger.error(f"Failed to send report to {recipient}: {e}")
        
        return distribution_results
        
    except Exception as e:
        logger.error(f"Error distributing report: {e}")
        raise


# Temporal Workflow
@workflow.defn
class ReportGenerationWorkflow:
    """
    Main workflow for automated report generation
    """
    
    def __init__(self):
        self.retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3
        )
    
    @workflow.run
    async def run(self, config: ReportConfig, 
                  start_date: Optional[str] = None,
                  end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute report generation workflow
        
        Args:
            config: Report configuration
            start_date: Optional start date override
            end_date: Optional end date override
            
        Returns:
            Workflow execution results
        """
        workflow.logger.info(f"Starting report generation workflow: {config.report_id}")
        
        try:
            # Determine date range
            if not start_date or not end_date:
                start_date, end_date = _calculate_default_date_range(config.schedule)
            
            # Generate report data based on type
            if config.report_type == 'cost_analysis':
                report_data = await workflow.execute_activity(
                    generate_cost_analysis_report,
                    args=[config, start_date, end_date],
                    retry_policy=self.retry_policy,
                    start_to_close_timeout=timedelta(minutes=30)
                )
            elif config.report_type == 'usage_summary':
                report_data = await workflow.execute_activity(
                    generate_usage_summary_report,
                    args=[config, start_date, end_date],
                    retry_policy=self.retry_policy,
                    start_to_close_timeout=timedelta(minutes=30)
                )
            elif config.report_type == 'budget_variance':
                report_data = await workflow.execute_activity(
                    generate_budget_variance_report,
                    args=[config, start_date, end_date],
                    retry_policy=self.retry_policy,
                    start_to_close_timeout=timedelta(minutes=30)
                )
            elif config.report_type == 'custom':
                report_data = await workflow.execute_activity(
                    generate_custom_report,
                    args=[config, start_date, end_date],
                    retry_policy=self.retry_policy,
                    start_to_close_timeout=timedelta(minutes=30)
                )
            else:
                raise ValueError(f"Unsupported report type: {config.report_type}")
            
            # Format report output
            report_output = await workflow.execute_activity(
                format_report_output,
                args=[report_data, config.output_format, config.template_id],
                retry_policy=self.retry_policy,
                start_to_close_timeout=timedelta(minutes=15)
            )
            
            # Distribute report
            distribution_results = await workflow.execute_activity(
                distribute_report,
                args=[report_output, config.recipients, config],
                retry_policy=self.retry_policy,
                start_to_close_timeout=timedelta(minutes=10)
            )
            
            # Return workflow results
            return {
                "workflow_id": workflow.info().workflow_id,
                "report_id": config.report_id,
                "status": "completed",
                "report_data": {
                    "total_records": report_data.total_records,
                    "total_cost": report_data.total_cost,
                    "currency": report_data.currency,
                    "data_period": f"{start_date} to {end_date}"
                },
                "output": {
                    "file_path": report_output.file_path,
                    "file_size": report_output.file_size,
                    "format": report_output.format
                },
                "distribution": distribution_results,
                "completed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            workflow.logger.error(f"Report generation workflow failed: {e}")
            return {
                "workflow_id": workflow.info().workflow_id,
                "report_id": config.report_id,
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            }


# Helper Functions
def _build_cost_analysis_query(filters: Dict[str, Any], 
                             start_date: str, 
                             end_date: str) -> str:
    """Build SQL query for cost analysis"""
    base_query = """
    SELECT 
        billing_account_id,
        service_category,
        service_name,
        region,
        resource_type,
        usage_date,
        SUM(billed_cost) as total_cost,
        SUM(usage_quantity) as total_usage,
        COUNT(*) as record_count,
        billing_currency
    FROM focus_billing_data
    WHERE usage_date >= '{start_date}'
      AND usage_date <= '{end_date}'
    """.format(start_date=start_date, end_date=end_date)
    
    # Apply filters
    if 'subscription_ids' in filters:
        subscription_list = "', '".join(filters['subscription_ids'])
        base_query += f" AND billing_account_id IN ('{subscription_list}')"
    
    if 'service_categories' in filters:
        category_list = "', '".join(filters['service_categories'])
        base_query += f" AND service_category IN ('{category_list}')"
    
    if 'regions' in filters:
        region_list = "', '".join(filters['regions'])
        base_query += f" AND region IN ('{region_list}')"
    
    base_query += """
    GROUP BY billing_account_id, service_category, service_name, 
             region, resource_type, usage_date, billing_currency
    ORDER BY usage_date DESC, total_cost DESC
    """
    
    return base_query


def _build_usage_summary_query(filters: Dict[str, Any],
                             start_date: str,
                             end_date: str) -> str:
    """Build SQL query for usage summary"""
    base_query = """
    SELECT 
        resource_type,
        service_name,
        region,
        COUNT(DISTINCT resource_id) as unique_resources,
        SUM(usage_quantity) as total_usage,
        AVG(usage_quantity) as avg_usage,
        SUM(billed_cost) as total_cost,
        usage_unit,
        billing_currency
    FROM focus_billing_data
    WHERE usage_date >= '{start_date}'
      AND usage_date <= '{end_date}'
    """.format(start_date=start_date, end_date=end_date)
    
    # Apply filters (similar to cost analysis)
    if 'subscription_ids' in filters:
        subscription_list = "', '".join(filters['subscription_ids'])
        base_query += f" AND billing_account_id IN ('{subscription_list}')"
    
    base_query += """
    GROUP BY resource_type, service_name, region, usage_unit, billing_currency
    ORDER BY total_cost DESC
    """
    
    return base_query


def _calculate_cost_metrics(raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate cost analysis metrics"""
    if not raw_data:
        return {"total_cost": 0.0, "currency": "USD"}
    
    total_cost = sum(float(record.get('total_cost', 0)) for record in raw_data)
    currency = raw_data[0].get('billing_currency', 'USD')
    
    # Group by service category
    service_costs = {}
    region_costs = {}
    
    for record in raw_data:
        service = record.get('service_category', 'Unknown')
        region = record.get('region', 'Unknown')
        cost = float(record.get('total_cost', 0))
        
        service_costs[service] = service_costs.get(service, 0) + cost
        region_costs[region] = region_costs.get(region, 0) + cost
    
    return {
        "total_cost": total_cost,
        "currency": currency,
        "service_breakdown": service_costs,
        "region_breakdown": region_costs,
        "top_service": max(service_costs, key=service_costs.get) if service_costs else None,
        "top_region": max(region_costs, key=region_costs.get) if region_costs else None,
        "record_count": len(raw_data)
    }


def _format_cost_breakdown(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format cost data for detailed breakdown"""
    return [
        {
            "account_id": record.get('billing_account_id'),
            "service_category": record.get('service_category'),
            "service_name": record.get('service_name'),
            "region": record.get('region'),
            "resource_type": record.get('resource_type'),
            "date": record.get('usage_date'),
            "cost": float(record.get('total_cost', 0)),
            "usage": float(record.get('total_usage', 0)),
            "currency": record.get('billing_currency')
        }
        for record in raw_data
    ]


def _generate_cost_charts_data(raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate chart data for cost visualization"""
    # This would generate data structures suitable for charting libraries
    return {
        "cost_trend": _prepare_trend_data(raw_data),
        "service_pie": _prepare_pie_data(raw_data, 'service_category'),
        "region_bar": _prepare_bar_data(raw_data, 'region')
    }


def _calculate_default_date_range(schedule: str) -> tuple[str, str]:
    """Calculate default date range based on schedule"""
    today = datetime.utcnow().date()
    
    if 'daily' in schedule.lower():
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif 'weekly' in schedule.lower():
        start_date = today - timedelta(days=7)
        end_date = today - timedelta(days=1)
    elif 'monthly' in schedule.lower():
        start_date = today.replace(day=1) - timedelta(days=1)
        start_date = start_date.replace(day=1)
        end_date = today.replace(day=1) - timedelta(days=1)
    else:
        # Default to last 30 days
        start_date = today - timedelta(days=30)
        end_date = today - timedelta(days=1)
    
    return start_date.isoformat(), end_date.isoformat()


# Additional helper functions would be implemented here for:
# - _calculate_usage_metrics()
# - _format_usage_breakdown()
# - _generate_usage_charts_data()
# - _get_budget_data()
# - _calculate_budget_variance_metrics()
# - _format_budget_variance_breakdown()
# - _generate_budget_variance_charts_data()
# - _calculate_custom_metrics()
# - _format_custom_breakdown()
# - _generate_custom_charts_data()
# - _apply_filters_to_query()
# - _format_pdf_report()
# - _format_excel_report()
# - _format_csv_report()
# - _format_json_report()
# - _send_report_email()
# - _prepare_trend_data()
# - _prepare_pie_data()
# - _prepare_bar_data()


# Report Management Functions
class ReportManager:
    """Manager class for report configurations and scheduling"""
    
    def __init__(self):
        self.reports: Dict[str, ReportConfig] = {}
    
    def register_report(self, config: ReportConfig) -> None:
        """Register a new report configuration"""
        self.reports[config.report_id] = config
        logger.info(f"Registered report: {config.report_id}")
    
    def get_report_config(self, report_id: str) -> Optional[ReportConfig]:
        """Get report configuration by ID"""
        return self.reports.get(report_id)
    
    def list_reports(self) -> List[ReportConfig]:
        """List all registered reports"""
        return list(self.reports.values())
    
    def update_report(self, report_id: str, updates: Dict[str, Any]) -> bool:
        """Update report configuration"""
        if report_id not in self.reports:
            return False
        
        config = self.reports[report_id]
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        logger.info(f"Updated report configuration: {report_id}")
        return True
    
    def delete_report(self, report_id: str) -> bool:
        """Delete report configuration"""
        if report_id in self.reports:
            del self.reports[report_id]
            logger.info(f"Deleted report: {report_id}")
            return True
        return False