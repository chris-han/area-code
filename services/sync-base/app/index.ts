import { Task, Workflow } from "@514labs/moose-lib";
import { createClient } from "@supabase/supabase-js";
import { Client } from "@elastic/elasticsearch";
// import type { Foo, Bar } from "@workspace/models";

// export interface Foo {
//   name: string;
// }

// Elasticsearch client for retrieval-base
const createElasticsearchClient = () => {
  return new Client({
    node: process.env.ELASTICSEARCH_URL || "http://localhost:9200",
    maxRetries: 5,
    requestTimeout: 60000,
    sniffOnStart: false,
  });
};

// Index names (matching retrieval-base)
const FOO_INDEX = "foos";
const BAR_INDEX = "bars";

// Synchronization functions
async function syncFooToElasticsearch(
  esClient: Client,
  operation: "INSERT" | "UPDATE" | "DELETE",
  record: any
) {
  try {
    switch (operation) {
      case "INSERT":
      case "UPDATE":
        await esClient.index({
          index: FOO_INDEX,
          id: record.id,
          body: {
            id: record.id,
            name: record.name,
            description: record.description,
            status: record.status,
            priority: record.priority,
            isActive: record.is_active,
            createdAt: record.created_at,
            updatedAt: record.updated_at,
          },
          refresh: true,
        });
        console.log(`✅ Synced Foo ${operation}: ${record.id}`);
        break;

      case "DELETE":
        await esClient.delete({
          index: FOO_INDEX,
          id: record.id,
          refresh: true,
        });
        console.log(`✅ Deleted Foo from search: ${record.id}`);
        break;
    }
  } catch (error) {
    console.error(`❌ Failed to sync Foo ${operation}:`, error);
    throw error;
  }
}

async function syncBarToElasticsearch(
  esClient: Client,
  operation: "INSERT" | "UPDATE" | "DELETE",
  record: any
) {
  try {
    switch (operation) {
      case "INSERT":
      case "UPDATE":
        await esClient.index({
          index: BAR_INDEX,
          id: record.id,
          body: {
            id: record.id,
            fooId: record.foo_id,
            value: record.value,
            label: record.label,
            notes: record.notes,
            isEnabled: record.is_enabled,
            createdAt: record.created_at,
            updatedAt: record.updated_at,
          },
          refresh: true,
        });
        console.log(`✅ Synced Bar ${operation}: ${record.id}`);
        break;

      case "DELETE":
        await esClient.delete({
          index: BAR_INDEX,
          id: record.id,
          refresh: true,
        });
        console.log(`✅ Deleted Bar from search: ${record.id}`);
        break;
    }
  } catch (error) {
    console.error(`❌ Failed to sync Bar ${operation}:`, error);
    throw error;
  }
}

// Enhanced sync task that actually synchronizes data
export const supabaseToElasticsearchSync = new Task<null, void>(
  "transactional-to-retrieval-sync",
  {
    run: async () => {
      // Configuration
      const config = {
        supabaseUrl: process.env.SUPABASE_URL || "http://localhost:3001",
        supabaseKey: process.env.SUPABASE_ANON_KEY || "your-anon-key",
        tables: ["foo", "bar"], // Only sync these tables (foo_bar is junction table)
      };

      console.log("🔄 Starting transactional-base → retrieval-base sync...");
      console.log(`📍 Supabase: ${config.supabaseUrl}`);
      console.log(
        `🔍 Elasticsearch: ${process.env.ELASTICSEARCH_URL || "http://localhost:9200"}`
      );
      console.log(`📋 Syncing tables: ${config.tables.join(", ")}`);

      // Create clients
      const supabase = createClient(config.supabaseUrl, config.supabaseKey);
      const esClient = createElasticsearchClient();

      // Test Elasticsearch connection
      try {
        await esClient.ping();
        console.log("✅ Elasticsearch connection successful");
      } catch (error) {
        console.error("❌ Failed to connect to Elasticsearch:", error);
        throw error;
      }

      // Set up listeners for each table
      const channels: any[] = [];

      for (const table of config.tables) {
        const channelName = `${table}-sync-channel`;

        const channel = supabase
          .channel(channelName)
          .on(
            "postgres_changes",
            {
              event: "*", // Listen to all events (INSERT, UPDATE, DELETE)
              schema: "public",
              table: table,
            },
            async (payload) => {
              console.log(`📡 [${table}] Database change detected:`, {
                event: payload.eventType,
                table: payload.table,
                timestamp: new Date().toISOString(),
              });

              try {
                // Determine which record to use based on operation
                const record = payload.new || payload.old;

                if (!record) {
                  console.warn(
                    `⚠️ No record data available for ${payload.eventType} on ${table}`
                  );
                  return;
                }

                // Sync based on table type
                switch (table) {
                  case "foo":
                    await syncFooToElasticsearch(
                      esClient,
                      payload.eventType as any,
                      record
                    );
                    break;
                  case "bar":
                    await syncBarToElasticsearch(
                      esClient,
                      payload.eventType as any,
                      record
                    );
                    break;
                  default:
                    console.log(`⚠️ Skipping unsupported table: ${table}`);
                }
              } catch (error) {
                console.error(
                  `❌ Sync failed for ${table} ${payload.eventType}:`,
                  error
                );
              }
            }
          )
          .subscribe((status) => {
            console.log(`🔌 [${table}] Subscription status: ${status}`);
            if (status === "SUBSCRIBED") {
              console.log(`✅ [${table}] Successfully subscribed to changes`);
            } else if (status === "CHANNEL_ERROR") {
              console.error(`❌ [${table}] Subscription error`);
            }
          });

        channels.push(channel);
      }

      console.log("🎧 Real-time sync active! Monitoring for changes...");
      console.log(
        "   • Changes in transactional-base will be synced to retrieval-base"
      );
      console.log("   • Press Ctrl+C to stop");

      // Keep the sync active
      await new Promise<void>((resolve) => {
        process.on("SIGINT", () => {
          console.log("\n🛑 Shutting down sync...");
          channels.forEach((channel) => channel.unsubscribe());
          esClient.close();
          console.log("✅ Sync stopped gracefully");
          resolve();
        });
      });
    },
  }
);

export const syncWorkflow = new Workflow("transactional-retrieval-sync", {
  startingTask: supabaseToElasticsearchSync,
});
