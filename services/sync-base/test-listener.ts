#!/usr/bin/env ts-node

import { createClient } from "@supabase/supabase-js";

/**
 * Simple test script to run the Supabase Realtime listener for transactional-base
 *
 * Usage:
 * 1. Start transactional-base service first:
 *    cd services/transactional-base && pnpm db:setup && pnpm dev
 *
 * 2. Set environment variables (optional, defaults to local):
 *    export SUPABASE_URL="http://localhost:3001"
 *    export SUPABASE_ANON_KEY="your-anon-key"
 *
 * 3. Run this script:
 *    npx ts-node test-listener.ts
 *
 * 4. Make changes to foo, bar, or foo_bar tables to see events
 */

async function testSupabaseListener() {
  console.log("🧪 Testing Transactional-Base Supabase Listener");
  console.log("================================================");

  const config = {
    supabaseUrl: process.env.SUPABASE_URL || "http://localhost:3001",
    supabaseKey: process.env.SUPABASE_ANON_KEY || "your-anon-key",
    tables: ["foo", "bar", "foo_bar"],
  };

  console.log("🔧 Configuration:");
  console.log(`  URL: ${config.supabaseUrl}`);
  console.log(`  Tables: ${config.tables?.join(", ") || "ALL"}`);
  console.log("");

  console.log("💡 To test this listener:");
  console.log("  1. Make sure transactional-base service is running");
  console.log(
    "  2. Insert/Update/Delete records in foo, bar, or foo_bar tables"
  );
  console.log("  3. Watch for change events in this console");
  console.log("");

  console.log(
    "⚠️  Note: This requires Supabase Realtime service to be running"
  );
  console.log(
    "   The current transactional-base setup may need additional configuration"
  );
  console.log("");

  try {
    console.log("🔥 Starting Supabase Realtime listener...");

    // Create Supabase client
    const supabase = createClient(config.supabaseUrl, config.supabaseKey);

    // Set up listeners for each table
    const tables = config.tables || ["foo", "bar", "foo_bar"];
    const channels: any[] = [];

    for (const table of tables) {
      const channelName = `${table}-changes`;

      const channel = supabase
        .channel(channelName)
        .on(
          "postgres_changes",
          {
            event: "*", // Listen to all events (INSERT, UPDATE, DELETE)
            schema: "public",
            table: table,
          },
          (payload) => {
            console.log(`📡 [${table}] Database change:`, {
              event: payload.eventType,
              table: payload.table,
              old: payload.old,
              new: payload.new,
              timestamp: new Date().toISOString(),
            });
          }
        )
        .subscribe((status) => {
          console.log(`🔌 [${table}] Status: ${status}`);
          if (status === "SUBSCRIBED") {
            console.log(`✅ [${table}] Successfully subscribed`);
          } else if (status === "CHANNEL_ERROR") {
            console.error(`❌ [${table}] Subscription error`);
          }
        });

      channels.push(channel);
    }

    // Keep the listener running
    console.log("🎧 Listening for database changes... (Press Ctrl+C to stop)");

    // This keeps the listener active
    await new Promise<void>((resolve) => {
      process.on("SIGINT", () => {
        console.log("\n🛑 Shutting down listeners...");
        channels.forEach((channel) => channel.unsubscribe());
        resolve();
      });
    });
  } catch (error) {
    console.error("❌ Error running listener:", error);
    process.exit(1);
  }
}

// Run the test
testSupabaseListener().catch(console.error);
