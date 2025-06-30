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

# 🔄 Sync-Base Service

A **Moose-powered data synchronization service** that provides real-time CDC (Change Data Capture) from transactional databases to analytical stores using **Supabase Postgres Changes** and **dual-workflow architecture**.

## 🏗️ **Architecture Overview**

This service uses a **two-workflow approach** for optimal separation of concerns:

### **1. 🔥 CDC Manager Workflow** (Long-Running)
- **Purpose**: Manages the CDC handler lifecycle
- **Execution**: Manually triggered, runs continuously (24-72 hours)
- **Responsibilities**:
  - Initialize and start CDC handler
  - Perform initial historical sync
  - Maintain persistent CDC connections
  - Handle CDC restarts and recovery

### **2. 🔍 Sync Monitor Workflow** (Scheduled)
- **Purpose**: Monitors CDC health and generates reports
- **Execution**: Automatically runs every 2 minutes
- **Responsibilities**:
  - Check CDC handler status
  - Generate monitoring reports
  - Alert if CDC is down
  - Provide observability data

```mermaid
graph TD
    A[Manual Trigger] --> B[CDC Manager Workflow]
    B --> C[Initialize CDC Handler]
    C --> D[Initial Historical Sync]
    D --> E[Maintain CDC Connection - LONG RUNNING]
    
    F[Every 2 Minutes] --> G[Sync Monitor Workflow]
    G --> H[Check CDC Status]
    H --> I[Generate Report]
    
    E -.->|Status Check| H
    
    J[Database Changes] --> K[Supabase Realtime]
    K --> L[CDC Handler]
    L --> M[Event Buffer]
    M --> N[Batch Processing]
    N --> O[Data Validation]
    O --> P[Moose Ingestion]
```

## 🚀 **Getting Started**

### **Prerequisites**
- Node.js 18+
- PostgreSQL database (transactional-base)
- Supabase project configured
- Moose CLI installed

### **1. Install Dependencies**
```bash
cd services/sync-base
pnpm install
```

### **2. Configure Environment**
```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
TRANSACTIONAL_DB_URL=postgresql://postgres:password@localhost:5433/postgres
```

### **3. Start the Service**
```bash
pnpm dev
```

### **4. Start CDC Data Sync**
```bash
# In another terminal, start the CDC manager (long-running)
moose workflow run cdcManagerWorkflow

# The monitor workflow runs automatically every 2 minutes
```

## 🎯 **Workflow Management**

### **Starting CDC**
```bash
# Start the CDC manager workflow (this runs continuously)
moose workflow run cdcManagerWorkflow
```

### **Checking Status**
```bash
# View CDC manager workflow status
moose workflow status cdcManagerWorkflow

# View scheduled monitor workflow status
moose workflow status syncMonitorWorkflow

# View all workflow runs
moose workflow list
```

### **Stopping CDC**
```bash
# Cancel the CDC manager workflow
moose workflow cancel cdcManagerWorkflow
```

### **Manual Status Check**
```bash
# Run monitor workflow manually
moose workflow run syncMonitorWorkflow
```

## 📊 **Data Flow**

### **Tables Synchronized**
- `foo` → `FooSync`
- `bar` → `BarSync` 
- `foo_bar` → `FooBarSync`

### **Event Processing**
1. **Real-time Events**: Database changes trigger Supabase realtime notifications
2. **Event Buffering**: Events are batched (default: 50 events)
3. **Dual Triggers**: Process when buffer is full OR every 30 seconds
4. **Data Validation**: Zod schema validation before ingestion
5. **Moose Ingestion**: Validated data sent to analytical store

### **CDC Operations Supported**
- ✅ **INSERT**: New records
- ✅ **UPDATE**: Modified records  
- ✅ **DELETE**: Removed records
- ✅ **Historical Sync**: Initial data catch-up

## 🔧 **Configuration**

### **Workflow Configuration**
```typescript
export const initialSyncConfig: SyncWorkflowConfig = {
  supabaseUrl: process.env.SUPABASE_URL || 'http://localhost:54321',
  supabaseKey: process.env.SUPABASE_ANON_KEY || '',
  transactionalDbUrl: process.env.TRANSACTIONAL_DB_URL || 'postgresql://...',
  batchSize: 50,              // Events per batch
  syncInterval: '@every 2m',  // Monitor frequency
  tables: ['foo', 'bar', 'foo_bar'],
};
```

### **CDC Handler Configuration**
```typescript
const cdcConfig: CDCConfig = {
  supabaseUrl: config.supabaseUrl,
  supabaseKey: config.supabaseKey,
  transactionalDbUrl: config.transactionalDbUrl,
  tables: config.tables,
  batchSize: config.batchSize,
  onBatch: processCDCEvents,    // Batch processor function
};
```

## 🔍 **Monitoring & Observability**

### **Temporal Dashboard**
- View both workflows in Temporal UI
- Monitor workflow execution history
- Track failures and retries
- Analyze performance metrics

### **Logs & Metrics**
```bash
# View real-time logs
moose logs

# Check workflow-specific logs
moose workflow logs cdcManagerWorkflow
moose workflow logs syncMonitorWorkflow
```

### **Status Indicators**
- **🔥 CDC Manager**: Long-running workflow status
- **🔍 Monitor**: Scheduled health checks
- **💓 Heartbeat**: CDC connection health (every minute)
- **📊 Metrics**: Events processed, buffer status, uptime

## 🛠️ **Development & Testing**

### **Test CDC Connection**
```bash
node test-cdc.js
```

### **Manual Status Check**
```javascript
// In Node.js REPL or script
const { getCDCStatus } = require('./app/index.ts');
console.log(getCDCStatus());
```

### **Debug Mode**
```bash
# Enable verbose logging
DEBUG=moose:* pnpm dev
```

## 🏥 **Error Handling & Recovery**

### **Automatic Recovery**
- **Connection Drops**: Auto-reconnect with exponential backoff
- **Batch Failures**: Individual event retry with dead letter queue
- **Workflow Failures**: Temporal retry policies with proper timeouts
- **CDC Handler Restart**: Monitor workflow detects and alerts

### **Manual Recovery**
```bash
# Restart CDC if stuck
moose workflow cancel cdcManagerWorkflow
moose workflow run cdcManagerWorkflow

# Check what went wrong
moose workflow logs cdcManagerWorkflow --tail 100
```

## 🚀 **Production Deployment**

### **Scaling Considerations**
- **CDC Manager**: One instance per database
- **Monitor Workflow**: Can run multiple instances safely
- **Event Volume**: Adjust `batchSize` based on throughput
- **Resources**: Long-running workflows need persistent containers

### **High Availability**
```bash
# Deploy with process manager
pm2 start pnpm --name "sync-base" -- dev

# Or with Docker
docker-compose up -d
```

### **Monitoring Setup**
- Configure Temporal alerts
- Set up log aggregation
- Monitor CDC lag metrics
- Track sync completion rates

## 🤔 **Why Two Workflows?**

### **Traditional Single Workflow Issues**
- ❌ Bootstrap dependency (need scheduled workflow to start CDC)
- ❌ Poor observability for long-running operations  
- ❌ Mixed concerns (CDC management + monitoring)
- ❌ Difficult to control independently

### **Dual Workflow Benefits**
- ✅ **Clear Separation**: CDC management vs. monitoring
- ✅ **Independent Control**: Start/stop CDC without affecting monitoring
- ✅ **Better Observability**: Each workflow visible in Temporal
- ✅ **Fault Isolation**: CDC failure doesn't break monitoring
- ✅ **Scalability**: Each workflow can scale independently

## 📚 **API Reference**

### **Exported Functions**
```typescript
// Get current CDC status
getCDCStatus(): CDCStatus

// Graceful shutdown
shutdownCDC(): Promise<void>
```

### **Workflow Names**
- `cdcManagerWorkflow` - Long-running CDC manager
- `syncMonitorWorkflow` - Scheduled monitoring

### **Data Schemas**
- `FooSync` - Zod schema for foo table sync
- `BarSync` - Zod schema for bar table sync  
- `FooBarSync` - Zod schema for foo_bar table sync

## 🔗 **Related Services**

- **[transactional-base](../transactional-base)**: Source database service
- **[analytical-base](../analytical-base)**: Target analytical store
- **[Supabase Realtime](https://supabase.com/docs/guides/realtime)**: CDC source

## 🆘 **Troubleshooting**

### **Common Issues**

**CDC Not Starting**
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# Verify database connection
psql $TRANSACTIONAL_DB_URL -c "SELECT 1;"
```

**No Events Being Processed**
```bash
# Check Supabase realtime configuration
# Verify table has realtime enabled
# Check CDC handler status
```

**Workflow Stuck**
```bash
# Cancel and restart
moose workflow cancel cdcManagerWorkflow
moose workflow run cdcManagerWorkflow
```

**High Memory Usage**
```bash
# Reduce batch size
# Check for event processing bottlenecks
# Monitor buffer sizes
```

### **Getting Help**
- Check Moose documentation: https://moosejs.dev
- Review Temporal workflow patterns
- Analyze workflow execution history
- Enable debug logging for detailed traces

---

🎉 **Ready to sync data in real-time with robust, observable, and scalable CDC workflows!**
