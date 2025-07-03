#!/usr/bin/env node

/**
 * Test script to connect directly to Realtime server using @supabase/realtime-js
 */

const { RealtimeClient } = require("@supabase/realtime-js");

async function testRealtimeDirect() {
  console.log("🧪 Testing Direct Realtime Connection");
  console.log("=====================================");
  console.log("");

  // JWT token generated from the secret in docker-compose.yml
  const JWT_TOKEN =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzUxNTU0NDgyLCJleHAiOjE3ODMwOTA0ODJ9.74aZUGrZj6vJlBgUImfOAAO1BqE3Pd_j21fB36i1d3M";

  console.log("🔧 Configuration:");
  console.log("   Realtime URL: ws://localhost:4002/socket");
  console.log(`   JWT Token: ${JWT_TOKEN.substring(0, 20)}...`);
  console.log("");

  try {
    console.log("1️⃣ Creating RealtimeClient...");

    // Create client with proper configuration based on the documentation
    // Note: RealtimeClient automatically appends /websocket to the URL
    const client = new RealtimeClient("ws://localhost:4002/socket", {
      params: {
        apikey: JWT_TOKEN,
      },
      timeout: 10000,
      logger: (kind, msg, data) => {
        console.log(`[${kind}] ${msg}`, data ? JSON.stringify(data) : "");
      },
      heartbeatIntervalMs: 30000,
      reconnectAfterMs: (tries) => {
        console.log(`Reconnect attempt ${tries}`);
        return [1000, 2000, 5000, 10000][tries - 1] || 10000;
      },
    });

    console.log("✅ RealtimeClient created");
    console.log("");

    console.log("2️⃣ Creating channel for database changes...");

    // Create a channel for database changes
    const channel = client.channel("db-changes");

    // Subscribe to postgres changes for the foo table
    channel.on(
      "postgres_changes",
      {
        event: "*",
        schema: "public",
        table: "foo",
      },
      (payload) => {
        console.log(`\n📡 Database change received!`);
        console.log(`   Event: ${payload.eventType}`);
        console.log(`   Table: ${payload.table}`);
        console.log(`   Schema: ${payload.schema}`);
        if (payload.new) {
          console.log(`   New data:`, payload.new);
        }
        if (payload.old) {
          console.log(`   Old data:`, payload.old);
        }
        console.log(`   Timestamp: ${new Date().toISOString()}`);
      }
    );

    console.log("3️⃣ Subscribing to channel...");

    // Subscribe to the channel
    channel.subscribe((status, err) => {
      console.log(`📡 Channel status: ${status}`);

      if (status === "SUBSCRIBED") {
        console.log("✅ Successfully subscribed to database changes!");
        console.log("");
        console.log("🎯 Test Instructions:");
        console.log("   1. Open another terminal");
        console.log("   2. Insert a record:");
        console.log(
          "      docker exec -it transactional-base-db psql -U postgres -c \\"
        );
        console.log(
          "        \"INSERT INTO foo (name, description) VALUES ('Realtime Test', 'Direct connection') RETURNING *;\""
        );
        console.log("");
        console.log("   3. Watch for real-time events in this console");
        console.log("");
        console.log("🎧 Listening... (Press Ctrl+C to stop)");
      }

      if (status === "CHANNEL_ERROR") {
        console.error(
          "❌ Channel subscription error:",
          err?.message || "Unknown error"
        );
      }

      if (status === "TIMED_OUT") {
        console.error("❌ Channel subscription timed out");
      }

      if (status === "CLOSED") {
        console.log("📡 Channel closed");
      }
    });

    // Keep the process running
    await new Promise((resolve) => {
      process.on("SIGINT", () => {
        console.log("\n🛑 Shutting down...");
        channel.unsubscribe();
        client.disconnect();
        resolve();
      });
    });
  } catch (error) {
    console.error("❌ Test failed:", error.message);
    console.error("");
    console.error("🔍 Troubleshooting:");
    console.error("1. Check if Realtime server is running:");
    console.error("   docker ps | grep realtime");
    console.error("");
    console.error("2. Check Realtime logs:");
    console.error("   docker logs transactional-base-realtime --tail 50");
    console.error("");
    console.error("3. Verify database configuration:");
    console.error("   cd services/sync-base && pnpm verify:realtime");
    console.error("");
    console.error("4. Check WebSocket endpoint:");
    console.error("   The URL should be ws://localhost:4002/socket");
    console.error("");
    console.error("5. Verify JWT token:");
    console.error(
      "   - Ensure the token is signed with the same secret as in docker-compose.yml"
    );
    console.error("   - Check the token expiration date");

    if (error.stack) {
      console.error("\n📋 Stack trace:");
      console.error(error.stack);
    }

    process.exit(1);
  }
}

// Run the test
testRealtimeDirect().catch(console.error);
