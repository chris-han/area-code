#!/usr/bin/env ts-node

import { createClient } from "@supabase/supabase-js";

/**
 * Simple test script to run the Supabase Realtime listener for transactional-base
 *
 * Usage:
 * 1. Start transactional-base service first:
 *    cd services/transactional-base && pnpm db:setup && pnpm dev
 *
 * 2. Run this script:
 *    npx ts-node test-listener.ts
 *
 * 3. Make changes to foo, bar, or foo_bar tables to see events
 */

async function testSupabaseListener() {
  console.log("🧪 Testing Transactional-Base Supabase Listener");
  console.log("================================================");

  const config = {
    supabaseUrl: process.env.SUPABASE_URL || "http://localhost:3001",
    supabaseKey: "no-auth-needed", // No auth required anymore
    tables: ["foo", "bar", "foo_bar"],
  };

  console.log("🔧 Configuration:");
  console.log(`  URL: ${config.supabaseUrl}`);
  console.log(`  Tables: ${config.tables?.join(", ") || "ALL"}`);
  console.log(`  Auth: Disabled (simplified setup)`);
  console.log("");

  console.log("💡 To test this listener:");
  console.log("  1. Make sure transactional-base service is running");
  console.log(
    "  2. Insert/Update/Delete records in foo, bar, or foo_bar tables"
  );
  console.log("  3. Watch for change events in this console");
  console.log("");

  console.log(
    "⚠️  Note: This uses the simplified real-time setup (Postgres Changes)"
  );
  console.log("");

  try {
    console.log("🔥 Starting Supabase Realtime listener...");

    // Create Supabase client without auth
    const supabase = createClient(config.supabaseUrl, config.supabaseKey, {
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
            console.error(`    Check that realtime is running on port 4002`);
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
