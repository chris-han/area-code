// Welcome to your new Moose analytical backend! 🦌

// Getting Started Guide:

// 1. Data Modeling
// First, plan your data structure and create your data models
// → See: docs.fiveonefour.com/moose/building/data-modeling
//   Learn about type definitions and data validation

// 2. Set Up Ingestion
// Create ingestion pipelines to receive your data via REST APIs
// → See: docs.fiveonefour.com/moose/building/ingestion
//   Learn about IngestPipeline, data formats, and validation

// 3. Create Workflows
// Build data processing pipelines to transform and analyze your data
// → See: docs.fiveonefour.com/moose/building/workflows
//   Learn about task scheduling and data processing

// 4. Configure Consumption APIs
// Set up queries and real-time analytics for your data
// → See: docs.fiveonefour.com/moose/building/consumption-apis

// Need help? Check out the quickstart guide:
// → docs.fiveonefour.com/moose/getting-started/quickstart

import { Task, Workflow } from "@514labs/moose-lib";
import { z } from "zod";
import {
  SupabaseCDCHandler,
  CDCEvent,
  CDCConfig,
} from "./supabase-cdc/cdc-handler";

// Data schemas for validation (these will be used to validate data before ingestion)
export const FooSync = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().optional(),
  status: z.string(),
  priority: z.number().optional(),
  isActive: z.boolean().optional(),
  createdAt: z.date(),
  updatedAt: z.date(),
  syncedAt: z.date(),
  operation: z.enum(["INSERT", "UPDATE", "DELETE"]),
});

export const BarSync = z.object({
  id: z.string(),
  fooId: z.string(),
  value: z.number(),
  label: z.string().optional(),
  notes: z.string().optional(),
  isEnabled: z.boolean().optional(),
  createdAt: z.date(),
  updatedAt: z.date(),
  syncedAt: z.date(),
  operation: z.enum(["INSERT", "UPDATE", "DELETE"]),
});

export const FooBarSync = z.object({
  id: z.string(),
  fooId: z.string(),
  barId: z.string(),
  relationshipType: z.string().optional(),
  metadata: z.string().optional(),
  createdAt: z.date(),
  syncedAt: z.date(),
  operation: z.enum(["INSERT", "UPDATE", "DELETE"]),
});

// Configuration for the sync workflow
export interface SyncWorkflowConfig {
  supabaseUrl: string;
  supabaseKey: string;
  transactionalDbUrl: string;
  batchSize: number;
  syncInterval: string;
  tables: string[];
}

export interface SyncContext {
  config: SyncWorkflowConfig;
  cdcHandler?: SupabaseCDCHandler;
  lastSyncTimestamp: Date;
  totalEventsSynced: number;
  isInitialSync: boolean;
}

// Global CDC handler instance (shared across workflow runs)
let globalCDCHandler: SupabaseCDCHandler | null = null;

// Initial sync configuration
export const initialSyncConfig: SyncWorkflowConfig = {
  supabaseUrl: process.env.SUPABASE_URL || "http://localhost:54321",
  supabaseKey: process.env.SUPABASE_ANON_KEY || "",
  transactionalDbUrl:
    process.env.TRANSACTIONAL_DB_URL ||
    "postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:5433/postgres",
  batchSize: 50,
  syncInterval: "@every 2m",
  tables: ["foo", "bar", "foo_bar"],
};

// Function to process CDC events and ingest into analytical store
async function processCDCEvents(events: CDCEvent[]): Promise<void> {
  console.log(`🔄 Processing ${events.length} CDC events for ingestion`);

  const syncTimestamp = new Date();

  for (const event of events) {
    try {
      let syncData: any;

      switch (event.table) {
        case "foo":
          syncData = {
            ...event.record,
            syncedAt: syncTimestamp,
            operation: event.operation,
            createdAt: new Date(event.record.created_at),
            updatedAt: new Date(event.record.updated_at),
          };

          // Validate the data using Zod schema
          const validatedFoo = FooSync.parse(syncData);

          // Here you would use Moose's ingestion API
          console.log(
            `📝 Would ingest Foo record: ${syncData.id} (${event.operation})`
          );
          break;

        case "bar":
          syncData = {
            ...event.record,
            syncedAt: syncTimestamp,
            operation: event.operation,
            createdAt: new Date(event.record.created_at),
            updatedAt: new Date(event.record.updated_at),
          };

          const validatedBar = BarSync.parse(syncData);
          console.log(
            `📝 Would ingest Bar record: ${syncData.id} (${event.operation})`
          );
          break;

        case "foo_bar":
          syncData = {
            ...event.record,
            syncedAt: syncTimestamp,
            operation: event.operation,
            createdAt: new Date(event.record.created_at),
          };

          const validatedFooBar = FooBarSync.parse(syncData);
          console.log(
            `📝 Would ingest FooBar record: ${syncData.id} (${event.operation})`
          );
          break;

        default:
          console.warn(`⚠️  Unknown table: ${event.table}`);
      }
    } catch (error) {
      console.error(`❌ Error processing event for ${event.table}:`, error);
      throw error;
    }
  }
}

// Task 1: Initialize or check CDC handler
export const initializeCDC = new Task<SyncWorkflowConfig, SyncContext>(
  "initializeCDC",
  {
    run: async (config: SyncWorkflowConfig) => {
      console.log("🚀 Initializing CDC workflow...");

      // Check if global CDC handler exists and is running
      if (globalCDCHandler && globalCDCHandler.getStatus().isRunning) {
        console.log("✅ CDC handler already running, using existing instance");

        return {
          config,
          cdcHandler: globalCDCHandler,
          lastSyncTimestamp: new Date(),
          totalEventsSynced: 0,
          isInitialSync: false,
        };
      }

      // Create new CDC handler
      const cdcConfig: CDCConfig = {
        supabaseUrl: config.supabaseUrl,
        supabaseKey: config.supabaseKey,
        transactionalDbUrl: config.transactionalDbUrl,
        tables: config.tables,
        batchSize: config.batchSize,
        onBatch: processCDCEvents,
      };

      globalCDCHandler = new SupabaseCDCHandler(cdcConfig);

      // Start the CDC handler
      await globalCDCHandler.start();

      console.log("✅ CDC handler initialized and started");

      return {
        config,
        cdcHandler: globalCDCHandler,
        lastSyncTimestamp: new Date(),
        totalEventsSynced: 0,
        isInitialSync: true,
      };
    },
    retries: 3,
    timeout: "5m",
  }
);

// Task 2: Perform initial sync if needed
export const performInitialSync = new Task<SyncContext, SyncContext>(
  "performInitialSync",
  {
    run: async (context: SyncContext) => {
      if (!context.isInitialSync || !context.cdcHandler) {
        console.log("ℹ️  Skipping initial sync - not required");
        return context;
      }

      console.log("📚 Performing initial sync for historical data...");

      let totalHistoricalEvents = 0;

      for (const table of context.config.tables) {
        try {
          const historicalEvents =
            await context.cdcHandler.performInitialSync(table);

          if (historicalEvents.length > 0) {
            console.log(
              `📊 Processing ${historicalEvents.length} historical events for ${table}`
            );
            await processCDCEvents(historicalEvents);
            totalHistoricalEvents += historicalEvents.length;
          }
        } catch (error) {
          console.error(`❌ Error during initial sync for ${table}:`, error);
          throw error;
        }
      }

      console.log(
        `✅ Initial sync completed - processed ${totalHistoricalEvents} historical events`
      );

      context.totalEventsSynced += totalHistoricalEvents;
      context.isInitialSync = false;

      return context;
    },
    retries: 2,
    timeout: "10m",
  }
);

// Task 3: Monitor CDC handler status
export const monitorCDCStatus = new Task<SyncContext, SyncContext>(
  "monitorCDCStatus",
  {
    run: async (context: SyncContext) => {
      if (!context.cdcHandler) {
        throw new Error("CDC handler not initialized");
      }

      const status = context.cdcHandler.getStatus();

      console.log("📊 CDC Handler Status:", {
        isRunning: status.isRunning,
        bufferedEvents: status.bufferedEvents,
        subscribedTables: status.subscribedTables,
        totalEventsSynced: context.totalEventsSynced,
      });

      if (!status.isRunning) {
        console.warn("⚠️  CDC handler is not running - attempting restart");
        await context.cdcHandler.start();
      }

      if (status.bufferedEvents > context.config.batchSize * 2) {
        console.warn(
          `⚠️  High number of buffered events: ${status.bufferedEvents}`
        );
      }

      return context;
    },
    retries: 1,
    timeout: "2m",
  }
);

// Task 4: Cleanup and status update
export const updateSyncStatus = new Task<SyncContext, void>(
  "updateSyncStatus",
  {
    run: async (context: SyncContext) => {
      console.log("📈 Updating sync workflow status...");

      const status = context.cdcHandler?.getStatus();

      const summary = {
        timestamp: new Date().toISOString(),
        totalEventsSynced: context.totalEventsSynced,
        cdcStatus: status,
        lastSyncTimestamp: context.lastSyncTimestamp.toISOString(),
        workflowStatus: "completed",
      };

      console.log("✅ Sync workflow cycle completed:", summary);

      // Here you could store sync status in a database or monitoring system
      // The CDC handler continues running in the background between workflow runs
    },
    retries: 1,
    timeout: "1m",
  }
);

// Create the main sync workflow using proper task chaining
export const dataSyncWorkflow = new Workflow("dataSyncWorkflow", {
  startingTask: new Task<SyncWorkflowConfig, void>("syncWorkflowChain", {
    run: async (config: SyncWorkflowConfig) => {
      // Execute tasks in sequence
      console.log("🚀 Starting data sync workflow...");

      // Task 1: Initialize CDC
      const context1 = await initializeCDC.config.run(config);

      // Task 2: Perform initial sync
      const context2 = await performInitialSync.config.run(context1);

      // Task 3: Monitor CDC status
      const context3 = await monitorCDCStatus.config.run(context2);

      // Task 4: Update sync status
      await updateSyncStatus.config.run(context3);

      console.log("✅ Data sync workflow completed successfully");
    },
    retries: 1,
    timeout: "15m",
  }),
  schedule: initialSyncConfig.syncInterval, // Run every 2 minutes for monitoring
  retries: 1,
  timeout: "20m",
});

console.log(
  "🚀 Advanced CDC-based data sync workflow configured and ready to run!"
);

// Export cleanup function for graceful shutdown
export async function shutdownCDC(): Promise<void> {
  if (globalCDCHandler) {
    console.log("🛑 Shutting down CDC handler...");
    await globalCDCHandler.stop();
    globalCDCHandler = null;
    console.log("✅ CDC handler shutdown complete");
  }
}
