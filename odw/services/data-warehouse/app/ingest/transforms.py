from app.ingest.models import (
    blobSourceModel,
    logSourceModel,
    eventSourceModel,
    unstructuredDataSourceModel,
    azureBillingDetailSourceModel,
    blobModel,
    logModel,
    eventModel,
    unstructuredDataModel,
    medicalModel,
    azureBillingDetailModel,
    BlobSource,
    LogSource,
    EventSource,
    UnstructuredDataSource,
    AzureBillingDetailSource,
    Blob,
    Log,
    Event,
    UnstructuredData,
    Medical,
    AzureBillingDetail,
)
from moose_lib import DeadLetterModel, TransformConfig
from datetime import datetime
from typing import Optional
import json

# This defines how data can be transformed from one model to another.
# For more information on transformations, see: https://docs.fiveonefour.com/moose/building/streams.


# Transform BlobSource to Blob, adding timestamp and handling failures
def blob_source_to_blob(blob_source: BlobSource) -> Blob:
    # Check for failure simulation
    if blob_source.file_name.startswith("[DLQ]"):
        raise ValueError(
            f"Transform failed for blob {blob_source.id}: File marked as failed"
        )

    return Blob(
        id=blob_source.id,
        bucket_name=blob_source.bucket_name,
        file_path=blob_source.file_path,
        file_name=blob_source.file_name,
        file_size=blob_source.file_size,
        permissions=blob_source.permissions,
        content_type=blob_source.content_type,
        ingested_at=blob_source.ingested_at,
        transform_timestamp=datetime.now().isoformat(),
    )


# Transform LogSource to Log, adding timestamp and handling failures
def log_source_to_log(log_source: LogSource) -> Log:
    # Check for failure simulation
    if log_source.message.startswith("[DLQ]"):
        raise ValueError(
            f"Transform failed for log {log_source.id}: Log marked as failed"
        )

    return Log(
        id=log_source.id,
        timestamp=log_source.timestamp,
        level=log_source.level,
        message=log_source.message,
        source=log_source.source,
        trace_id=log_source.trace_id,
        transform_timestamp=datetime.now().isoformat(),
    )


# Transform EventSource to Event, adding timestamp and handling failures
def event_source_to_event(event_source: EventSource) -> Event:
    # Check for failure simulation (events with [DLQ] in distinct_id)
    if event_source.distinct_id.startswith("[DLQ]"):
        raise ValueError(
            f"Transform failed for event {event_source.id}: Event marked as failed"
        )

    return Event(
        id=event_source.id,
        event_name=event_source.event_name,
        timestamp=event_source.timestamp,
        distinct_id=event_source.distinct_id,
        session_id=event_source.session_id,
        project_id=event_source.project_id,
        properties=event_source.properties,
        ip_address=event_source.ip_address,
        user_agent=event_source.user_agent,
        transform_timestamp=datetime.now().isoformat(),
    )


# Set up the transformations
blobSourceModel.get_stream().add_transform(
    destination=blobModel.get_stream(),
    transformation=blob_source_to_blob,
    config=TransformConfig(dead_letter_queue=blobSourceModel.get_dead_letter_queue()),
)

logSourceModel.get_stream().add_transform(
    destination=logModel.get_stream(),
    transformation=log_source_to_log,
    config=TransformConfig(dead_letter_queue=logSourceModel.get_dead_letter_queue()),
)

eventSourceModel.get_stream().add_transform(
    destination=eventModel.get_stream(),
    transformation=event_source_to_event,
    config=TransformConfig(dead_letter_queue=eventSourceModel.get_dead_letter_queue()),
)


# Transform UnstructuredDataSource to UnstructuredData, adding timestamp
def unstructured_data_source_to_unstructured_data(
    source: UnstructuredDataSource,
) -> UnstructuredData:
    # Check for failure simulation
    if source.source_file_path.startswith("[DLQ]"):
        raise ValueError(
            f"Transform failed for unstructured data {source.id}: File marked as failed"
        )

    return UnstructuredData(
        id=source.id,
        source_file_path=source.source_file_path,
        extracted_data=source.extracted_data,
        processed_at=source.processed_at,
        processing_instructions=source.processing_instructions,
        transform_timestamp=datetime.now().isoformat(),
    )


unstructuredDataSourceModel.get_stream().add_transform(
    destination=unstructuredDataModel.get_stream(),
    transformation=unstructured_data_source_to_unstructured_data,
    config=TransformConfig(
        dead_letter_queue=unstructuredDataSourceModel.get_dead_letter_queue()
    ),
)


# Transform AzureBillingDetailSource to AzureBillingDetail, adding timestamp and additional processing
def azure_billing_source_to_azure_billing(
    source: AzureBillingDetailSource,
) -> AzureBillingDetail:
    # Check for failure simulation
    if source.instance_id.startswith("[DLQ]"):
        raise ValueError(
            f"Transform failed for Azure billing record {source.id}: Record marked as failed"
        )

    return AzureBillingDetail(
        id=source.id,
        account_owner_id=source.account_owner_id,
        account_name=source.account_name,
        service_administrator_id=source.service_administrator_id,
        subscription_id=source.subscription_id,
        subscription_guid=source.subscription_guid,
        subscription_name=source.subscription_name,
        date=source.date,
        month=source.month,
        day=source.day,
        year=source.year,
        product=source.product,
        meter_id=source.meter_id,
        meter_category=source.meter_category,
        meter_sub_category=source.meter_sub_category,
        meter_region=source.meter_region,
        meter_name=source.meter_name,
        consumed_quantity=source.consumed_quantity,
        resource_rate=source.resource_rate,
        extended_cost=source.extended_cost,
        resource_location=source.resource_location,
        consumed_service=source.consumed_service,
        instance_id=source.instance_id,
        service_info1=source.service_info1,
        service_info2=source.service_info2,
        additional_info=source.additional_info,
        tags=source.tags,
        store_service_identifier=source.store_service_identifier,
        department_name=source.department_name,
        cost_center=source.cost_center,
        unit_of_measure=source.unit_of_measure,
        resource_group=source.resource_group,
        # Additional fields for the final model
        extended_cost_tax=(
            source.extended_cost * 1.1 if source.extended_cost else None
        ),  # Example: add 10% tax
        resource_tracking=(
            f"tracked_{source.instance_id}" if source.instance_id else None
        ),
        resource_name=(
            source.instance_id.split("/")[-1]
            if source.instance_id and "/" in source.instance_id
            else source.instance_id
        ),
        vm_name=(
            source.instance_id.split("/")[-1]
            if source.instance_id and "virtualMachines" in source.instance_id
            else None
        ),
        latest_resource_type=source.consumed_service,
        newmonth=(
            f"{source.year}-{source.month:02d}"
            if source.year and source.month
            else None
        ),
        month_date=source.month_date,
        sku=source.meter_id,
        cmdb_mapped_application_service=None,  # To be populated by business logic
        ppm_billing_item=None,  # To be populated by business logic
        ppm_id_owner=None,  # To be populated by business logic
        ppm_io_cc=source.cost_center,
        transform_timestamp=datetime.now().isoformat(),
    )


azureBillingDetailSourceModel.get_stream().add_transform(
    destination=azureBillingDetailModel.get_stream(),
    transformation=azure_billing_source_to_azure_billing,
    config=TransformConfig(
        dead_letter_queue=azureBillingDetailSourceModel.get_dead_letter_queue()
    ),
)


# Dead letter queue recovery for BlobSource
def invalid_blob_source_to_blob(
    dead_letter: DeadLetterModel[BlobSource],
) -> Optional[Blob]:
    try:
        original_blob_source = dead_letter.as_typed()

        # Fix the failure condition - change [DLQ] to [RECOVERED]
        corrected_file_name = original_blob_source.file_name
        if corrected_file_name.startswith("[DLQ]"):
            corrected_file_name = corrected_file_name.replace("[DLQ]", "[RECOVERED]", 1)

        return Blob(
            id=original_blob_source.id,
            bucket_name=original_blob_source.bucket_name,
            file_path=original_blob_source.file_path,
            file_name=corrected_file_name,
            file_size=original_blob_source.file_size,
            permissions=original_blob_source.permissions,
            content_type=original_blob_source.content_type,
            ingested_at=original_blob_source.ingested_at,
            transform_timestamp=datetime.now().isoformat(),
        )
    except Exception as error:
        print(f"Blob recovery failed: {error}")
        return None


# Dead letter queue recovery for LogSource
def invalid_log_source_to_log(dead_letter: DeadLetterModel[LogSource]) -> Optional[Log]:
    try:
        original_log_source = dead_letter.as_typed()

        # Fix the failure condition - change [DLQ] to [RECOVERED]
        corrected_message = original_log_source.message
        if corrected_message.startswith("[DLQ]"):
            corrected_message = corrected_message.replace("[DLQ]", "[RECOVERED]", 1)

        return Log(
            id=original_log_source.id,
            timestamp=original_log_source.timestamp,
            level=original_log_source.level,
            message=corrected_message,
            source=original_log_source.source,
            trace_id=original_log_source.trace_id,
            transform_timestamp=datetime.now().isoformat(),
        )
    except Exception as error:
        print(f"Log recovery failed: {error}")
        return None


# Dead letter queue recovery for EventSource
def invalid_event_source_to_event(
    dead_letter: DeadLetterModel[EventSource],
) -> Optional[Event]:
    try:
        original_event_source = dead_letter.as_typed()

        # Fix the failure condition - change [DLQ] to [RECOVERED]
        corrected_distinct_id = original_event_source.distinct_id
        if corrected_distinct_id.startswith("[DLQ]"):
            corrected_distinct_id = corrected_distinct_id.replace(
                "[DLQ]", "[RECOVERED]", 1
            )

        return Event(
            id=original_event_source.id,
            event_name=original_event_source.event_name,
            timestamp=original_event_source.timestamp,
            distinct_id=corrected_distinct_id,
            session_id=original_event_source.session_id,
            project_id=original_event_source.project_id,
            properties=original_event_source.properties,
            ip_address=original_event_source.ip_address,
            user_agent=original_event_source.user_agent,
            ingested_at=original_event_source.ingested_at,
            transform_timestamp=datetime.now().isoformat(),
        )
    except Exception as error:
        print(f"Event recovery failed: {error}")
        return None


# Dead letter queue recovery for UnstructuredDataSource
def invalid_unstructured_data_source_to_unstructured_data(
    dead_letter: DeadLetterModel[UnstructuredDataSource],
) -> Optional[UnstructuredData]:
    try:
        original_source = dead_letter.as_typed()

        # Fix the failure condition - change [DLQ] to [RECOVERED]
        corrected_file_path = original_source.source_file_path
        if corrected_file_path.startswith("[DLQ]"):
            corrected_file_path = corrected_file_path.replace("[DLQ]", "[RECOVERED]", 1)

        return UnstructuredData(
            id=original_source.id,
            source_file_path=corrected_file_path,
            extracted_data=original_source.extracted_data,
            processed_at=original_source.processed_at,
            processing_instructions=original_source.processing_instructions,
            transform_timestamp=datetime.now().isoformat(),
        )
    except Exception as error:
        print(f"UnstructuredData recovery failed: {error}")
        return None


# Set up dead letter queue transforms
blobSourceModel.get_dead_letter_queue().add_transform(
    destination=blobModel.get_stream(),
    transformation=invalid_blob_source_to_blob,
)

logSourceModel.get_dead_letter_queue().add_transform(
    destination=logModel.get_stream(),
    transformation=invalid_log_source_to_log,
)

eventSourceModel.get_dead_letter_queue().add_transform(
    destination=eventModel.get_stream(),
    transformation=invalid_event_source_to_event,
)

unstructuredDataSourceModel.get_dead_letter_queue().add_transform(
    destination=unstructuredDataModel.get_stream(),
    transformation=invalid_unstructured_data_source_to_unstructured_data,
)


# Dead letter queue recovery for AzureBillingDetailSource
def invalid_azure_billing_source_to_azure_billing(
    dead_letter: DeadLetterModel[AzureBillingDetailSource],
) -> Optional[AzureBillingDetail]:
    try:
        original_source = dead_letter.as_typed()

        # Fix the failure condition - change [DLQ] to [RECOVERED]
        corrected_instance_id = original_source.instance_id
        if corrected_instance_id.startswith("[DLQ]"):
            corrected_instance_id = corrected_instance_id.replace(
                "[DLQ]", "[RECOVERED]", 1
            )

        return AzureBillingDetail(
            id=original_source.id,
            account_owner_id=original_source.account_owner_id,
            account_name=original_source.account_name,
            service_administrator_id=original_source.service_administrator_id,
            subscription_id=original_source.subscription_id,
            subscription_guid=original_source.subscription_guid,
            subscription_name=original_source.subscription_name,
            date=original_source.date,
            month=original_source.month,
            day=original_source.day,
            year=original_source.year,
            product=original_source.product,
            meter_id=original_source.meter_id,
            meter_category=original_source.meter_category,
            meter_sub_category=original_source.meter_sub_category,
            meter_region=original_source.meter_region,
            meter_name=original_source.meter_name,
            consumed_quantity=original_source.consumed_quantity,
            resource_rate=original_source.resource_rate,
            extended_cost=original_source.extended_cost,
            resource_location=original_source.resource_location,
            consumed_service=original_source.consumed_service,
            instance_id=corrected_instance_id,
            service_info1=original_source.service_info1,
            service_info2=original_source.service_info2,
            additional_info=original_source.additional_info,
            tags=original_source.tags,
            store_service_identifier=original_source.store_service_identifier,
            department_name=original_source.department_name,
            cost_center=original_source.cost_center,
            unit_of_measure=original_source.unit_of_measure,
            resource_group=original_source.resource_group,
            # Additional fields for the final model
            extended_cost_tax=(
                original_source.extended_cost * 1.1
                if original_source.extended_cost
                else None
            ),
            resource_tracking=f"recovered_{corrected_instance_id}",
            resource_name=(
                corrected_instance_id.split("/")[-1]
                if "/" in corrected_instance_id
                else corrected_instance_id
            ),
            vm_name=(
                corrected_instance_id.split("/")[-1]
                if "virtualMachines" in corrected_instance_id
                else None
            ),
            latest_resource_type=original_source.consumed_service,
            newmonth=(
                f"{original_source.year}-{original_source.month:02d}"
                if original_source.year and original_source.month
                else None
            ),
            month_date=original_source.month_date,
            sku=original_source.meter_id,
            cmdb_mapped_application_service=None,
            ppm_billing_item=None,
            ppm_id_owner=None,
            ppm_io_cc=original_source.cost_center,
            transform_timestamp=datetime.now().isoformat(),
        )
    except Exception as error:
        print(f"Azure billing recovery failed: {error}")
        return None


azureBillingDetailSourceModel.get_dead_letter_queue().add_transform(
    destination=azureBillingDetailModel.get_stream(),
    transformation=invalid_azure_billing_source_to_azure_billing,
)
