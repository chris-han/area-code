import { Task, Workflow } from "@514labs/moose-lib";
import { createClient } from "@supabase/supabase-js";
import { Client } from "@elastic/elasticsearch";
import dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();

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

// Simplified sync task following Supabase docs approach
export const supabaseToElasticsearchSync = new Task<null, void>(
  "transactional-to-retrieval-sync",
  {
    run: async () => {
      console.log("🔄 Starting transactional-base → retrieval-base sync...");

      // Configuration - no auth key needed anymore
      const supabaseUrl = process.env.SUPABASE_URL || "http://localhost:3001";
      const realtimeUrl = process.env.REALTIME_URL || "ws://localhost:4002";
      const supabaseKey = "no-auth-needed"; // Dummy key since auth is removed

      console.log(`📍 Supabase URL: ${supabaseUrl}`);
      console.log(`📍 Realtime URL: ${realtimeUrl}`);
      console.log(
        `🔍 Elasticsearch: ${process.env.ELASTICSEARCH_URL || "http://localhost:9200"}`
      );
      console.log(
        "⚠️  Note: Running without authentication (simplified setup)"
      );

      // Test connections first
      console.log("\n🔧 Testing connections...");

      // Test PostgREST API
      try {
        const response = await fetch(`${supabaseUrl}/foo?limit=1`);
        if (!response.ok) {
          throw new Error(
            `PostgREST returned ${response.status}: ${response.statusText}`
          );
        }
        console.log("✅ PostgREST API is accessible");
      } catch (error: any) {
        console.error("❌ PostgREST API connection failed!");
        console.error(`   Error: ${error.message}`);
        console.error(`   URL: ${supabaseUrl}`);
        console.error("");
        console.error("🔍 Troubleshooting:");
        console.error(
          "   1. Is transactional-base running? (cd services/transactional-base && pnpm dev)"
        );
        console.error(
          "   2. Check if PostgREST is accessible: curl http://localhost:3001/foo"
        );
        console.error("   3. Verify SUPABASE_URL in .env file");
        throw new Error(
          "PostgREST connection failed - cannot proceed with sync"
        );
      }

      // Test Realtime WebSocket
      console.log("\n🔌 Testing Realtime WebSocket...");
      try {
        // Quick WebSocket test
        const ws = new (require("ws"))(realtimeUrl + "/socket/websocket", {
          timeout: 5000,
        });

        await new Promise((resolve, reject) => {
          ws.on("open", () => {
            console.log("✅ Realtime WebSocket is accessible");
            ws.close();
            resolve(true);
          });
          ws.on("error", (error: any) => {
            reject(error);
          });
          setTimeout(
            () => reject(new Error("WebSocket connection timeout")),
            5000
          );
        });
      } catch (error: any) {
        console.error("❌ Realtime WebSocket connection failed!");
        console.error(`   Error: ${error.message}`);
        console.error(`   URL: ${realtimeUrl}`);
        console.error("");
        console.error("🔍 Troubleshooting:");
        console.error("   1. Check if realtime server is running:");
        console.error("      - In transactional-base: docker compose ps");
        console.error(
          "      - Look for 'transactional-base-realtime' container"
        );
        console.error("   2. If not running, start it:");
        console.error("      - cd services/transactional-base");
        console.error("      - pnpm realtime:start");
        console.error("   3. Verify port 4002 is not blocked");
        console.error(
          "   4. Check docker logs: docker logs transactional-base-realtime"
        );
        console.error("");
        console.error(
          "⚠️  The sync service will continue but real-time updates won't work!"
        );
      }

      // Create clients
      const supabase = createClient(supabaseUrl, supabaseKey, {
        auth: {
          persistSession: false,
          autoRefreshToken: false,
        },
        realtime: {
          params: {
            eventsPerSecond: 10,
          },
        },
      });
      const esClient = createElasticsearchClient();

      // Test Elasticsearch connection
      try {
        await esClient.ping();
        console.log("✅ Elasticsearch connection successful");
      } catch (error: any) {
        console.error("❌ Failed to connect to Elasticsearch!");
        console.error(`   Error: ${error.message}`);
        console.error("");
        console.error("🔍 Troubleshooting:");
        console.error(
          "   1. Is retrieval-base running? (cd services/retrieval-base && pnpm dev)"
        );
        console.error(
          "   2. Check if Elasticsearch is accessible: curl http://localhost:9200"
        );
        console.error("   3. Verify ELASTICSEARCH_URL in .env file");
        throw new Error(
          "Elasticsearch connection failed - cannot proceed with sync"
        );
      }

      // Set up channel for all database changes following Supabase docs pattern
      console.log("\n📡 Setting up real-time subscriptions...");
      let retryCount = 0;
      const maxRetries = 3;

      const setupChannel = () => {
        const channel = supabase
          .channel("db-changes")
          .on(
            "postgres_changes",
            {
              event: "*", // Listen to INSERT, UPDATE, and DELETE
              schema: "public",
              table: "foo",
            },
            async (payload) => {
              console.log("📡 Foo change received:", payload.eventType);

              try {
                const record = payload.new || payload.old;
                if (record) {
                  await syncFooToElasticsearch(
                    esClient,
                    payload.eventType as any,
                    record
                  );
                }
              } catch (error) {
                console.error("❌ Error processing foo change:", error);
              }
            }
          )
          .on(
            "postgres_changes",
            {
              event: "*", // Listen to INSERT, UPDATE, and DELETE
              schema: "public",
              table: "bar",
            },
            async (payload) => {
              console.log("📡 Bar change received:", payload.eventType);

              try {
                const record = payload.new || payload.old;
                if (record) {
                  await syncBarToElasticsearch(
                    esClient,
                    payload.eventType as any,
                    record
                  );
                }
              } catch (error) {
                console.error("❌ Error processing bar change:", error);
              }
            }
          )
          .subscribe((status, error) => {
            console.log(`📡 Subscription status: ${status}`);

            if (status === "SUBSCRIBED") {
              console.log("✅ Successfully subscribed to database changes");
              console.log("   Using simplified Postgres Changes method");
              retryCount = 0; // Reset retry count on success
            } else if (status === "CHANNEL_ERROR") {
              console.error("❌ Channel error - subscription failed!");

              if (error) {
                console.error(`   Error details: ${JSON.stringify(error)}`);
              }

              console.error("");
              console.error("🔍 Common causes:");
              console.error("   1. Realtime server is not running");
              console.error(
                "   2. Publication 'supabase_realtime' not configured"
              );
              console.error("   3. Tables not added to publication");
              console.error("");
              console.error("📋 To fix:");
              console.error("   1. Start realtime server:");
              console.error(
                "      cd services/transactional-base && pnpm realtime:start"
              );
              console.error("   2. Set up publication:");
              console.error(
                "      cd services/transactional-base && pnpm db:setup-realtime"
              );
              console.error("");

              // Retry logic
              if (retryCount < maxRetries) {
                retryCount++;
                console.log(
                  `🔄 Retrying subscription (attempt ${retryCount}/${maxRetries})...`
                );
                setTimeout(() => {
                  channel.unsubscribe();
                  setupChannel();
                }, 5000 * retryCount); // Exponential backoff
              } else {
                console.error(
                  "❌ Max retries reached. Real-time sync will not work!"
                );
                console.error(
                  "   The service will continue running but won't receive updates."
                );
              }
            } else if (status === "TIMED_OUT") {
              console.error("⏰ Subscription timed out");
              console.error(
                "   This usually means the realtime server is not responding"
              );
            } else if (status === "CLOSED") {
              console.warn("🔒 Subscription closed");
            }
          });

        return channel;
      };

      const channel = setupChannel();

      console.log("\n🎧 Sync service is running!");
      console.log("   • Monitoring changes in transactional-base");
      console.log("   • Syncing to retrieval-base Elasticsearch");
      console.log("   • Press Ctrl+C to stop");

      // Keep the sync active
      await new Promise<void>((resolve) => {
        process.on("SIGINT", () => {
          console.log("\n🛑 Shutting down sync...");
          channel.unsubscribe();
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
