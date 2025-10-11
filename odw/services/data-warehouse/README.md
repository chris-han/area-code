# Data Warehouse Service

**Learn to build operational data warehouses with Moose** - from real-time ingestion to analytics APIs. This hands-on demonstration showcases how to create a complete data pipeline using Moose primitives, with mocked data sources for easy experimentation and clear examples using simple data models.

<a href="dw-logo.png"><img src="dw-logo.png" alt="Data Warehouse Logo" width="512"></a>

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker 2.23.1+

## Quick Start

(If you haven't already, navigate to odw root directory `cd ../..`, and make sure Docker Desktop is running)

**Full Setup**:

```bash
bun add -g turbo
bun install
bun odw:dev
```

This will:

- Install all dependencies
- Start the data warehouse service (moose app)
- Start the data warehouse frontend (streamlit in apps/dw-frontend)

## Presenter - walkthrough docs

[Presenter - walkthrough docs](./docs/README.md)

## Project Overview

<a href="./docs/ODW-architecture.jpg"><img src="./docs/ODW-architecture.jpg" alt="Data Warehouse Architecture" width="800"></a>

This project is your **practical guide** to understanding how Moose can power modern operational data warehouses. Rather than implementing every feature in the reference architecture above, we've created a focused, working example that you can run immediately and extend based on your specific needs.

The codebase is **commented** to help you understand each component and pattern. Feel free to explore the code with your favorite LLM - it can provide detailed explanations of how the various Moose primitives work together and help you understand the data flow from ingestion to consumption.

### Purpose and Scope

This project is **intentionally focused** on demonstrating key concepts rather than implementing the full reference architecture shown above. It provides enough practical insights and working examples to help developers understand how to:

- Build data ingestion pipelines with Moose
- Implement stream processing workflows
- Create analytical APIs and consumption endpoints
- Integrate multiple data sources into a unified warehouse

### Current Implementation

The current state represents a **simplified but functional** implementation that:

- **Uses mocked data sources**: Logs, Blob (storage), and Events integrations are mocked to make this demo self-contained. Developers can easily adapt these patterns for real data sources by configuring appropriate API keys and endpoints for services they want to integrate.

- **Demonstrates Moose primitives**: The project showcases core Moose concepts including data models, ingestion pipelines, stream functions, materialized views, and consumption APIs.

- **Keeps data models simple**: Uses representative data models to make the data flow easy to follow and understand. Moose makes it straightforward to create much richer and more complex data models as your use case requires.

- **Provides a complete workflow**: From data ingestion through processing to consumption, giving developers a full picture of an operational data warehouse built with Moose.

### Key Technical Capabilities

- **Real-time Data Ingestion**: Stream data processing with RedPanda
- **Multi-Source Data Extraction**: Configurable connectors for various data sources
- **REST API**: Query interface for accessing processed data
- **Scalable Storage**: ClickHouse backend optimized for analytical workloads
- **Stream Processing**: Real-time data transformation and enrichment

### Demo presentation walkthrough

See: [Presenter - walkthrough docs](./docs/README.md)

## Project Structure

```
odw/
├── services/
│   ├── data-warehouse/         # Main Moose data warehouse service
│   │   ├── app/
│   │   │   ├── apis/           # REST API endpoints for data consumption
│   │   │   ├── blobs/          # Blob data extraction workflows
│   │   │   ├── events/         # Events data extraction workflows
│   │   │   ├── ingest/         # Data models and stream transformations
│   │   │   ├── logs/           # Log data extraction workflows
│   │   │   ├── views/          # Materialized views for analytics
│   │   │   └── main.py         # Main Moose application entry point
│   │   ├── docs/               # Documentation and walkthrough guides
│   │   ├── scripts/            # Setup and management scripts
│   │   ├── moose.config.toml   # Moose framework configuration
│   │   └── requirements.txt    # Python dependencies
│   └── connectors/             # External data source connectors
│       └── src/
│           ├── blob_connector.py    # Blob storage data connector
│           ├── events_connector.py  # Events data connector
│           ├── logs_connector.py    # Logs data connector
│           └── connector_factory.py # Connector factory pattern
└── apps/
    └── dw-frontend/            # Streamlit web application
        ├── pages/              # Frontend page components
        ├── utils/              # Frontend utility functions
        └── main.py             # Streamlit application entry point
```

## Detailed high-level overview

For a high-level architectural overview of the system, see [high-level-overview.md](./docs/high-level-overview.md).

## Other Commands

| Command              | Description        |
| -------------------- | ------------------ |
| `bun run odw:dev:clean` | Clean all services |

## Installing Aurora AI Support

Aurora AI is an optional enhancement that extends your copilot's AI capabilities an MCP with specialized tools for Moose workflows, ClickHouse queries, and RedPanda integration. This provides intelligent assistance for the creation and maintenance of data warehouse operations.

For setup instructions, see [Aurora docs](https://docs.fiveonefour.com/aurora).

## LLM Configuration

This project includes **LLM-powered unstructured data extraction** using Anthropic's Claude API. To enable this feature:

### Required Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude LLM integration

### Setup Instructions

1. **Get an Anthropic API key**: Sign up at [console.anthropic.com](https://console.anthropic.com) and create an API key

2. **Configure LLM settings**: Copy the example configuration and customize as needed:

   ```bash
   cp env.example .env
   ```

   Then edit `.env` to set your API key and configure LLM parameters. See `env.example` for detailed configuration options including batch processing, model selection, and validation settings.

3. **Verify setup**: The LLM service will be automatically initialized when processing unstructured data

### LLM Features

- **Extraction**: Convert unstructured documents (text, PDFs, images) to structured JSON using natural language instructions
- **Validation**: Validate extracted data against business rules specified in plain English
- **Transformation**: Modify and enrich extracted data using natural language transformations
- **Routing**: Intelligently route data based on content analysis
- **Batch Processing**: Process multiple files efficiently with configurable batch sizes for improved performance

#### Configuration Options

The LLM service supports extensive configuration through the `.env` file:

- **Model Selection**: Choose from available Claude models (default: `claude-sonnet-4-20250514`)
- **Processing Parameters**: Configure temperature, token limits, and content size limits
- **Batch Processing**: Enable/disable batch processing and set optimal batch sizes
- **Field Validation**: Enable strict field validation for cleaner data extraction
- **Performance Tuning**: Adjust settings to balance speed vs. accuracy for your use case

#### Fallback Behavior

**Note**: LLM features are optional. When the API key is not configured, the system will:

- Return structured metadata about the content (file type, content preview, processing timestamps)
- Preserve original data with informational notes about the disabled LLM service
- Continue processing without intelligent extraction, validation, or transformation
- Provide clear guidance on enabling LLM features through logging messages

This ensures the system remains functional while providing a clear upgrade path to intelligent processing.

## S3/MinIO Configuration

This project now supports **S3-compatible storage** for unstructured data files, allowing you to read documents, images, and other files directly from S3 buckets or MinIO instances instead of local filesystem paths.

### Configuration in `moose.config.toml`

The S3 configuration section has been added to `moose.config.toml`:

```toml
[s3_config]
# S3/MinIO configuration for unstructured data storage
endpoint_url = ""  # MinIO endpoint, set to empty string for AWS S3
access_key_id = { from_env = "MOOSE_S3_ACCESS_KEY_ID" }
secret_access_key = { from_env = "MOOSE_S3_SECRET_ACCESS_KEY" }
region_name = { from_env = "MOOSE_S3_REGION_NAME", default = "us-east-2" }
bucket_name = { from_env = "MOOSE_S3_BUCKET_NAME", default = "unstructured-data" }
signature_version = "s3v4"
```

> ℹ️ **Environment-backed values**  
> Sensitive credentials now live in `.env`. Populate the following variables (a template is provided in `env.example`):
> 
> ```bash
> MOOSE_S3_ACCESS_KEY_ID=...
> MOOSE_S3_SECRET_ACCESS_KEY=...
> MOOSE_S3_REGION_NAME=...
> MOOSE_S3_BUCKET_NAME=...
> ```

### ClickHouse Connection Settings

ClickHouse credentials are also sourced from environment variables:

```toml
[clickhouse_config]
db_name = "dbo"
user = { from_env = "MOOSE_CLICKHOUSE_USER" }
password = { from_env = "MOOSE_CLICKHOUSE_PASSWORD" }
use_ssl = { from_env = "MOOSE_CLICKHOUSE_USE_SSL", default = true }
host = { from_env = "MOOSE_CLICKHOUSE_HOST" }
host_port = { from_env = "MOOSE_CLICKHOUSE_HOST_PORT", default = 8443 }
native_port = { from_env = "MOOSE_CLICKHOUSE_NATIVE_PORT", default = 8443 }
```

Populate the corresponding variables in `.env` (see `env.example` for placeholders). Boolean variables such as `MOOSE_CLICKHOUSE_USE_SSL` accept values like `true/false`, `1/0`, or `yes/no`.

### Setup for Different Storage Types

**For MinIO (Development/Testing):**

- Set `endpoint_url` to your MinIO server (e.g., `http://localhost:9500`)
- Use MinIO admin credentials or create specific access keys
- Ensure the bucket exists in MinIO

**For AWS S3 (Production):**

- Set `endpoint_url` to an empty string `""`
- Use your AWS access key and secret key
- Set the appropriate AWS region
- Ensure the S3 bucket exists and your credentials have read access

### Supported Path Formats

The system now accepts multiple path formats for unstructured data:

```bash
# S3 paths
s3://bucket-name/path/to/file.txt

# MinIO paths
minio://bucket-name/path/to/file.txt
```

### File Type Support

The S3 integration supports multiple file types, all processed using Claude's advanced vision and text processing capabilities:

- **Text files**: `.txt`, `.md`, `.csv`, `.json`, `.xml`, `.html` - Processed using standard LLM text extraction
- **PDF files**: `.pdf` - Processed using Claude's vision capabilities for text extraction and OCR
- **Images**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp` - Processed using Claude's vision capabilities for OCR and content analysis
- **Word documents**: `.doc`, `.docx` - Processed using Claude's document processing capabilities

**Note**: All file processing is handled natively through Claude's API without requiring external OCR libraries, PDF parsers, or document processing tools. This provides a unified, simplified architecture where all unstructured data processing flows through the LLM service.

### Usage in APIs

When submitting unstructured data via the `submitUnstructuredData` API, you can now use S3 paths:

```json
{
  "source_file_path": "minio://unstructured-data/memo_001.txt",
  "extracted_data": "{\"extracted\": \"data\"}"
}
```
