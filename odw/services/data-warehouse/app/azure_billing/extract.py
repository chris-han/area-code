from app.ingest.models import AzureBillingDetailSource
from app.utils.simulator import simulate_failures
from connectors.connector_factory import ConnectorFactory, ConnectorType
from connectors.azure_billing.azure_billing_connector import AzureBillingConnectorConfig
from moose_lib import Task, TaskConfig, Workflow, WorkflowConfig, cli_log, CliLogData, TaskContext
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import requests
import json
import uuid
import os

# This workflow extracts Azure billing data and sends it to the ingest API.
# For more information on workflows, see: https://docs.fiveonefour.com/moose/building/workflows.
#
# The data flows through the following pipeline:
# 1. Azure EA API -> AzureBillingDetailSource (raw data)
# 2. Stream transformation -> AzureBillingDetail (processed data)
# 3. Final storage -> moose_azure_billing ClickHouse table

class AzureBillingExtractParams(BaseModel):
    batch_size: Optional[int] = 1000
    fail_percentage: Optional[int] = 0
    start_date: Optional[str] = None  # YYYY-MM-DD format
    end_date: Optional[str] = None    # YYYY-MM-DD format
    azure_enrollment_number: Optional[str] = None
    azure_api_key: Optional[str] = None

def run_task(context: TaskContext[AzureBillingExtractParams]) -> None:
    cli_log(CliLogData(action="AzureBillingWorkflow", message="Starting Azure billing data extraction...", message_type="Info"))
    
    # Log workflow execution start time for timeout debugging
    import time
    start_time = time.time()
    cli_log(CliLogData(action="AzureBillingWorkflow", message=f"Workflow started at: {time.ctime(start_time)}", message_type="Info"))

    try:
        # Parse date parameters or use defaults (last month)
        if context.input.start_date and context.input.end_date:
            start_date = datetime.strptime(context.input.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(context.input.end_date, '%Y-%m-%d')
        else:
            # Default to last month
            today = datetime.now()
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            start_date = last_day_last_month.replace(day=1)
            end_date = last_day_last_month

        cli_log(CliLogData(
            action="AzureBillingWorkflow", 
            message=f"Extracting data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", 
            message_type="Info"
        ))

        # Get Azure credentials from environment variables or input parameters
        azure_enrollment_number = (
            context.input.azure_enrollment_number or 
            os.getenv('AZURE_ENROLLMENT_NUMBER')
        )
        azure_api_key = (
            context.input.azure_api_key or 
            os.getenv('AZURE_API_KEY')
        )
        
        if not azure_enrollment_number or not azure_api_key:
            raise ValueError(
                "Azure credentials not provided. Set AZURE_ENROLLMENT_NUMBER and AZURE_API_KEY "
                "environment variables or pass them as workflow parameters."
            )

        cli_log(CliLogData(
            action="AzureBillingWorkflow", 
            message=f"Using Azure enrollment: {azure_enrollment_number}", 
            message_type="Info"
        ))

        # Create Azure billing connector configuration
        connector_config = AzureBillingConnectorConfig(
            batch_size=context.input.batch_size,
            start_date=start_date,
            end_date=end_date,
            azure_enrollment_number=azure_enrollment_number,
            azure_api_key=azure_api_key
        )

        # Create connector to extract data from Azure billing API
        connector = ConnectorFactory[AzureBillingDetailSource].create(
            ConnectorType.AzureBilling,
            connector_config
        )

        # Extract data from Azure billing API
        cli_log(CliLogData(action="AzureBillingWorkflow", message="Calling Azure EA API...", message_type="Info"))
        raw_data = connector.extract()

        cli_log(CliLogData(
            action="AzureBillingWorkflow",
            message=f"Extracted {len(raw_data)} billing records from Azure API",
            message_type="Info"
        ))

        if not raw_data:
            cli_log(CliLogData(
                action="AzureBillingWorkflow",
                message="No data extracted from Azure API",
                message_type="Warning"
            ))
            return

        # Convert Azure billing records to source model format
        source_records = []
        for record in raw_data:
            try:
                # Convert the connector's AzureBillingDetail to our AzureBillingDetailSource
                source_record = AzureBillingDetailSource(
                    id=record.id or str(uuid.uuid4()),
                    account_owner_id=record.account_owner_id,
                    account_name=record.account_name,
                    service_administrator_id=record.service_administrator_id,
                    subscription_id=record.subscription_id,
                    subscription_guid=record.subscription_guid,
                    subscription_name=record.subscription_name,
                    date=record.date.strftime('%Y-%m-%d') if record.date else None,
                    month=record.month,
                    day=record.day,
                    year=record.year,
                    product=record.product,
                    meter_id=record.meter_id,
                    meter_category=record.meter_category,
                    meter_sub_category=record.meter_sub_category,
                    meter_region=record.meter_region,
                    meter_name=record.meter_name,
                    consumed_quantity=record.consumed_quantity,
                    resource_rate=record.resource_rate,
                    extended_cost=record.extended_cost,
                    resource_location=record.resource_location,
                    consumed_service=record.consumed_service,
                    instance_id=record.instance_id,
                    service_info1=record.service_info1,
                    service_info2=record.service_info2,
                    additional_info=json.dumps(record.additional_info) if record.additional_info else None,
                    tags=json.dumps(record.tags) if record.tags else None,
                    store_service_identifier=record.store_service_identifier,
                    department_name=record.department_name,
                    cost_center=record.cost_center,
                    unit_of_measure=record.unit_of_measure,
                    resource_group=record.resource_group,
                    month_date=record.month_date.strftime('%Y-%m-%d') if record.month_date else None
                )
                source_records.append(source_record)
            except Exception as e:
                cli_log(CliLogData(
                    action="AzureBillingWorkflow",
                    message=f"Failed to convert record to source format: {str(e)}",
                    message_type="Warning"
                ))
                continue

        cli_log(CliLogData(
            action="AzureBillingWorkflow",
            message=f"Converted {len(source_records)} records to source format",
            message_type="Info"
        ))

        # Simulate failures for testing if requested
        failed_count = simulate_failures(source_records, context.input.fail_percentage)
        if failed_count > 0:
            cli_log(CliLogData(
                action="AzureBillingWorkflow",
                message=f"Marked {failed_count} items ({context.input.fail_percentage}%) as failed for testing",
                message_type="Info"
            ))

        # Convert to dictionaries for JSON serialization
        data_dicts = [record.model_dump() for record in source_records]
        
        # Send data to ingest API in batches
        batch_size = context.input.batch_size or 1000
        total_sent = 0
        
        for i in range(0, len(data_dicts), batch_size):
            batch = data_dicts[i:i + batch_size]
            
            try:
                response = requests.post(
                    "http://localhost:4200/ingest/AzureBillingDetailSource",
                    json=batch,
                    headers={"Content-Type": "application/json"},
                    timeout=300  # 5 minute timeout for large batches
                )
                response.raise_for_status()
                total_sent += len(batch)
                
                cli_log(CliLogData(
                    action="AzureBillingWorkflow",
                    message=f"Successfully sent batch {i//batch_size + 1}: {len(batch)} records",
                    message_type="Info"
                ))
                
            except Exception as e:
                cli_log(CliLogData(
                    action="AzureBillingWorkflow",
                    message=f"Failed to send batch {i//batch_size + 1} to ingest API: {str(e)}",
                    message_type="Error"
                ))
                # Continue with next batch rather than failing completely
                continue

        # Log completion time for timeout debugging
        end_time = time.time()
        execution_time = end_time - start_time
        cli_log(CliLogData(
            action="AzureBillingWorkflow",
            message=f"Azure billing extraction completed. Total records sent: {total_sent}/{len(source_records)}. Execution time: {execution_time:.2f} seconds",
            message_type="Info"
        ))

    except Exception as e:
        cli_log(CliLogData(
            action="AzureBillingWorkflow",
            message=f"Azure billing workflow failed: {str(e)}",
            message_type="Error"
        ))
        raise

azure_billing_task = Task[AzureBillingExtractParams, None](
    name="azure-billing-task",
    config=TaskConfig(run=run_task)
)

azure_billing_workflow = Workflow(
    name="azure-billing-workflow",
    config=WorkflowConfig(starting_task=azure_billing_task)
)