# Azure Blob Data Lineage

```mermaid
flowchart TD
    subgraph AzureStorage[Azure Blob Storage]
        A1[Parquet Blobs]
    end

    subgraph ConnectorLayer[Azure Blob Connector\n`connectors/src/azure_blob_connector.py`]
        B1[Discover Containers & Parquet]
        B2[Normalise Arrow Rows]
    end

    subgraph WorkflowLayer[Moose Workflow\n`app/azure_billing/workflows/azure_blob_ingest_workflow.py`]
        W1[Validate Plugin Metadata]
        W2[Build Ingest Payload]
    end

    subgraph MooseIngest[Moose Ingest]
        C1[`AzureBlobStaging` Pipeline\n`app/ingest/models.py`]
        C2[ClickHouse Staging Table]
    end

    subgraph Downstream[Downstream Processing]
        D1[FOCUS Transformations\n`app/azure_billing/transformations/*`]
        D2[Analytics Views\n`app/views/*`]
        D3[bia Consumption APIs\n`bia_backend/*`]
    end

    A1 -->|Plugin metadata config| B1
    B1 --> B2
    B2 -->|Connector output| W1
    W1 --> W2
    W2 -->|POST /ingest/AzureBlobStaging| C1
    C1 --> C2
    C2 --> D1
    D1 --> D2
    D2 --> D3
```

## Sequence Overview

```mermaid
sequenceDiagram
    participant Azure as Azure Blob Storage
    participant Workflow as Moose Workflow\n`azure_blob_ingest_workflow`
    participant Connector as Azure Blob Connector
    participant Ingest as Moose Ingest API
    participant ClickHouse as ClickHouse Staging
    participant Transform as FOCUS Transformations
    participant API as bia Consumption APIs

    Azure->>Workflow: Plugin metadata (containers, prefix, SAS)
    Workflow->>Connector: Instantiate with resolved config
    Connector->>Azure: Enumerate parquet blobs
    Connector-->>Workflow: Stream normalised rows
    Workflow->>Ingest: POST /ingest/AzureBlobStaging
    Ingest->>ClickHouse: Persist staging rows
    ClickHouse->>Transform: Provide staging dataset
    Transform->>API: Serve analytics + bia routes
```

## Stages

- **Azure Blob Storage** – Containers hold FOCUS-compliant parquet files published by cloud billing teams.
- **Azure Blob Connector** – Implemented in `odw/services/connectors/src/azure_blob_connector.py`; uses plugin metadata to resolve containers, enumerates parquet files, normalizes Arrow rows, and prepares JSON payloads.
- **Moose Workflow** – Defined in `odw/services/data-warehouse/app/azure_billing/workflows/azure_blob_ingest_workflow.py`; validates config, orchestrates the connector, and posts to Moose ingest.
- **Moose Ingest** – `AzureBlobStaging` pipeline in `odw/services/data-warehouse/app/ingest/models.py` that persists rows to a ClickHouse staging table exposed via Moose CLI.
- **Downstream Processing** – Transformation engines convert staging data into FOCUS models, expose analytical views, and serve bia APIs.
- **Trigger Surface** – Available via the bia admin UI (`Create New Workflow → Azure Blob Parquet Ingest`) and through the `/api/v1/workflows/trigger` endpoint using `workflow_type="azure_blob_ingest"`.

## Components & Paths

- Connector: `odw/services/connectors/src/azure_blob_connector.py`
- Workflow: `odw/services/data-warehouse/app/azure_billing/workflows/azure_blob_ingest_workflow.py`
- Ingest pipeline: `odw/services/data-warehouse/app/ingest/models.py`
- Plugin metadata: `odw/services/data-warehouse/app/azure_billing/plugins/marketplace_api.py`
- Sample parquet assets: `odw/services/data-warehouse/app/blobs/part_*.snappy.parquet`
- Downstream transforms: `odw/services/data-warehouse/app/azure_billing/transformations/`
