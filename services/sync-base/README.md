# This is a [MooseJs](https://www.moosejs.com/) project bootstrapped with the [`Moose CLI`](https://github.com/514-labs/moose/tree/main/apps/framework-cli).

<a href="https://www.getmoose.dev/"><img src="https://raw.githubusercontent.com/514-labs/moose/main/logo-m-light.png" alt="moose logo" height="100px"></a>

[![NPM Version](https://img.shields.io/npm/v/%40514labs%2Fmoose-cli?logo=npm)](https://www.npmjs.com/package/@514labs/moose-cli?activeTab=readme)
[![Moose Community](https://img.shields.io/badge/slack-moose_community-purple.svg?logo=slack)](https://join.slack.com/t/moose-community/shared_invite/zt-2fjh5n3wz-cnOmM9Xe9DYAgQrNu8xKxg)
[![Docs](https://img.shields.io/badge/quick_start-docs-blue.svg)](https://docs.moosejs.com/)
[![MIT license](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

[Moose](https://www.getmoose.dev/) is an open-source data engineering framework designed to drastically accellerate AI-enabled software developers, as you prototype and scale data-intensive features and applications.

# Get started with Moose

Get up and running with your own Moose project in minutes by using our [Quick Start Tutorial](https://docs.getmoose.dev/quickstart). We also have our [Docs](https://docs.getmoose.dev/) where you can pick your path, learn more about Moose, and learn what types of applications can be built with Moose.

# Beta release

Moose is beta software and is in active development. Multiple public companies across the globe are using Moose in production. We'd love for you to [get your hands on it and try it out](https://docs.getmoose.dev/quickstart). If you're interested in using Moose in production, or if you just want to chat, you can reach us at [hello@moosejs.dev](mailto:hello@moosejs.dev) or in the Moose developer community below.

# Community

You can join the Moose community [on Slack](https://join.slack.com/t/moose-community/shared_invite/zt-2fjh5n3wz-cnOmM9Xe9DYAgQrNu8xKxg).

Here you can get together with other Moose developers, ask questions, give feedback, make feature requests, and interact directly with Moose maintainers.

# Contributing

We welcome contributions to Moose! Please check out the [contribution guidelines](https://github.com/514-labs/moose/blob/main/CONTRIBUTING.md).

# Made by 514

Our mission at [fiveonefour](https://www.fiveonefour.com/) is to bring incredible developer experiences to the data stack. If you're interested in enterprise solutions, commercial support, or design partnerships, then we'd love to chat with you: [hello@moosejs.dev](mailto:hello@moosejs.dev)

# Sync Base Service - CDC Data Sync Workflow

This service implements a sophisticated Change Data Capture (CDC) workflow that syncs data from the transactional-base service to an analytical data store using Supabase's realtime features and Moose workflows.

## Architecture Overview

The sync service consists of:

1. **CDC Handler** (`supabase-cdc/cdc-handler.ts`) - Manages realtime subscriptions to PostgreSQL changes via Supabase
2. **Moose Workflow** (`index.ts`) - Orchestrates the sync process with scheduling, retries, and monitoring
3. **Data Validation** - Uses Zod schemas to ensure data integrity during sync

## Features

- 🔄 **Real-time Change Data Capture** using Supabase realtime subscriptions
- ⏰ **Scheduled Workflow** runs every 2 minutes to monitor and maintain CDC connections
- 🔁 **Initial Sync** for historical data when first starting
- 🛡️ **Error Handling** with retries at both task and workflow levels
- 📊 **Monitoring** with status reporting and health checks
- 🧩 **Batch Processing** to efficiently handle multiple changes
- ✅ **Data Validation** using Zod schemas before ingestion

## Setup Instructions

### 1. Prerequisites

Ensure you have the following running:
- **Transactional Base Service** (source database on port 5433)
- **Supabase-compatible PostgreSQL** with realtime enabled
- **Node.js 18+** and **pnpm**

### 2. Environment Configuration

Set these environment variables in your `.env` file or environment:

```env
# Supabase Configuration
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=your-supabase-anon-key

# Source Database (Transactional Base)
TRANSACTIONAL_DB_URL=postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:5433/postgres
```

### 3. Install Dependencies

```bash
cd services/sync-base
pnpm install
```

### 4. Start the Development Server

```bash
pnpm dev
```

This will start the Moose development server with the CDC workflow enabled.

## Workflow Operation

### Workflow Schedule

The `dataSyncWorkflow` runs every 2 minutes (`@every 2m`) and performs:

1. **Initialize CDC** - Sets up or verifies Supabase realtime subscriptions
2. **Initial Sync** - Processes historical data on first run
3. **Monitor Status** - Checks CDC handler health and buffered events
4. **Update Status** - Logs workflow completion and statistics

### CDC Handler Operation

The CDC handler operates continuously in the background:

- **Realtime Subscriptions** to `foo`, `bar`, and `foo_bar` tables
- **Event Buffering** with configurable batch sizes (default: 50 events)
- **Automatic Processing** of batched events every 30 seconds
- **Error Recovery** with automatic reconnection on failures

### Data Flow

```
PostgreSQL (Transactional DB)
    ↓ (Realtime CDC)
Supabase CDC Handler
    ↓ (Batch Processing)
Data Validation (Zod)
    ↓ (Ingestion)
Analytical Store (ClickHouse)
```

## Usage Examples

### Running the Workflow Manually

```bash
# Run the workflow once
moose workflow run dataSyncWorkflow

# Run with custom input
moose workflow run dataSyncWorkflow --input '{"batchSize": 100}'
```

### Monitoring Workflow Status

```bash
# Check workflow status
moose workflow status dataSyncWorkflow

# Get detailed status with logs
moose workflow status dataSyncWorkflow --verbose
```

### Viewing Workflow in Temporal Dashboard

When the workflow runs, it provides a URL to view execution in the Temporal dashboard:
```
View it in the Temporal dashboard: http://localhost:8080/namespaces/default/workflows/dataSyncWorkflow/...
```

## Configuration Options

You can customize the sync behavior by modifying `initialSyncConfig`:

```typescript
export const initialSyncConfig: SyncWorkflowConfig = {
  supabaseUrl: process.env.SUPABASE_URL || 'http://localhost:54321',
  supabaseKey: process.env.SUPABASE_ANON_KEY || '',
  transactionalDbUrl: process.env.TRANSACTIONAL_DB_URL || '...',
  batchSize: 50,                    // Events per batch
  syncInterval: '@every 2m',        // Workflow frequency
  tables: ['foo', 'bar', 'foo_bar'], // Tables to sync
};
```

## Monitoring and Debugging

### CDC Handler Status

The workflow logs CDC handler status including:
- Running state
- Number of buffered events
- Subscribed tables
- Total events synced

### Error Handling

The system includes multiple layers of error protection:

- **Workflow Level**: 1 retry with 20-minute timeout
- **Task Level**: Individual retry policies (1-3 retries each)
- **CDC Handler Level**: Automatic reconnection and batch retry

### Common Issues

1. **Connection Failures**
   - Check that transactional-base service is running on port 5433
   - Verify Supabase URL and key are correct

2. **No Events Received**
   - Ensure Supabase realtime is enabled for the tables
   - Check that the transactional database allows CDC connections

3. **High Buffer Counts**
   - The workflow will warn if buffered events exceed 2x batch size
   - Consider increasing batch size or processing frequency

## Development

### Adding New Tables

To sync additional tables:

1. Add the table name to the `tables` array in config
2. Create a corresponding Zod schema for validation
3. Add a case in the `processCDCEvents` function

### Customizing Processing

The `processCDCEvents` function can be modified to:
- Transform data before ingestion
- Add custom validation logic
- Route different data types to different destinations

### Testing

```bash
# Test CDC connectivity
moose workflow run dataSyncWorkflow --input '{"batchSize": 1}'

# Monitor realtime events
# (Check the terminal output for CDC event logs)
```

## Production Considerations

- **Scaling**: The CDC handler maintains persistent connections - consider connection pooling for multiple instances
- **Monitoring**: Implement proper logging and alerting for production deployments
- **Security**: Use proper authentication and network security for database connections
- **Data Validation**: The Zod schemas provide runtime validation - ensure they match your analytical store requirements

## Troubleshooting

For debugging CDC issues:

1. Check the Temporal dashboard for workflow execution details
2. Monitor the terminal output for CDC event logs
3. Verify database connectivity using the health check endpoints
4. Use `moose workflow status` for detailed execution information

For additional help, refer to the [Moose documentation](https://docs.fiveonefour.com/moose/) and [Supabase realtime documentation](https://supabase.com/docs/guides/realtime).
