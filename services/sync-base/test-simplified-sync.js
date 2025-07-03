#!/usr/bin/env node

/**
 * Test script to verify sync-base works with simplified transactional-base setup
 */

const { createClient } = require("@supabase/supabase-js");
const { Client } = require("@elastic/elasticsearch");

// Load environment variables
require("dotenv").config();

async function testSimplifiedSync() {
  console.log("🧪 Testing Simplified Sync Setup");
  console.log("================================");
  console.log("");
  console.log("✅ Direct PostgreSQL access via PostgREST");
  console.log("✅ Real-time with JWT authentication");
  console.log("");

  const config = {
    supabaseUrl: process.env.SUPABASE_URL || "http://localhost:3001",
    // Use the generated JWT token (signed with the secret from docker-compose.yml)
    supabaseKey:
      "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzUxNTU0NDgyLCJleHAiOjE3ODMwOTA0ODJ9.74aZUGrZj6vJlBgUImfOAAO1BqE3Pd_j21fB36i1d3M",
    elasticsearchUrl: process.env.ELASTICSEARCH_URL || "http://localhost:9200",
  };

  console.log("🔧 Configuration:");
  console.log(`   PostgREST API: ${config.supabaseUrl}`);
  console.log(`   Elasticsearch: ${config.elasticsearchUrl}`);
  console.log(`   JWT Token: ${config.supabaseKey.substring(0, 20)}...`);
  console.log("");

  try {
    // Test Elasticsearch
    console.log("1️⃣ Testing Elasticsearch connection...");
    const esClient = new Client({ node: config.elasticsearchUrl });
    await esClient.ping();
    console.log("✅ Elasticsearch is running");

    // Create Supabase client with JWT authentication
    console.log("2️⃣ Creating Supabase client with JWT authentication...");
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
      global: {
        headers: {
          Authorization: `Bearer ${config.supabaseKey}`,
        },
      },
    });

    // Manually set the Realtime URL after client creation
    // This is needed because Realtime is on port 4002, not the default
    supabase.realtime.setAuth(config.supabaseKey);
    supabase.realtime.endPoint = "ws://localhost:4002/socket";
    supabase.realtime.reconnectTimer.reset();

    console.log("✅ Supabase client created with custom Realtime endpoint");

    // Subscribe to foo table changes
    console.log("3️⃣ Subscribing to real-time changes...");

    const channel = supabase
      .channel("db-changes")
      .on(
        "postgres_changes",
        {
          event: "*", // Listen to all events (INSERT, UPDATE, DELETE)
          schema: "public",
          table: "foo",
        },
        (payload) => {
          console.log(`\n📡 Real-time event received!`);
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
      )
      .subscribe((status) => {
        console.log(`📡 Subscription status: ${status}`);

        if (status === "SUBSCRIBED") {
          console.log("✅ Successfully subscribed to real-time changes");
          console.log("");
          console.log("🎯 Test Instructions:");
          console.log("   1. Open another terminal");
          console.log("   2. Create a record using one of these methods:");
          console.log("");
          console.log("   Method A - Using the API service (if running):");
          console.log("      curl -X POST http://localhost:8081/api/foo \\");
          console.log('        -H "Content-Type: application/json" \\');
          console.log(
            '        -d \'{"name": "Test Sync", "description": "Testing real-time"}\''
          );
          console.log("");
          console.log("   Method B - Using PostgREST directly:");
          console.log("      curl -X POST http://localhost:3001/foo \\");
          console.log('        -H "Content-Type: application/json" \\');
          console.log('        -H "Prefer: return=representation" \\');
          console.log(
            '        -d \'{"name": "Direct Test", "description": "Via PostgREST"}\''
          );
          console.log("");
          console.log("   Method C - Direct database insert:");
          console.log(
            "      docker exec -it transactional-base-db psql -U postgres -c \\"
          );
          console.log(
            "        \"INSERT INTO foo (name, description) VALUES ('DB Test', 'Direct insert') RETURNING *;\""
          );
          console.log("");
          console.log("   3. Watch for real-time events in this console");
          console.log("");
          console.log("🎧 Listening... (Press Ctrl+C to stop)");
        } else if (status === "CHANNEL_ERROR") {
          console.error("❌ Channel error occurred");
          console.error("   This may be due to:");
          console.error("   - JWT authentication failure");
          console.error("   - Realtime server not running");
          console.error("   - Database configuration issues");
        } else if (status === "TIMED_OUT") {
          console.error("❌ Connection timed out");
        } else if (status === "CLOSED") {
          console.log("📡 Channel closed");
        }
      });

    // Keep running
    await new Promise((resolve) => {
      process.on("SIGINT", () => {
        console.log("\n🛑 Shutting down...");
        channel.unsubscribe();
        esClient.close();
        resolve();
      });
    });
  } catch (error) {
    console.error("❌ Test failed:", error.message);
    console.error("");
    console.error("🔍 Troubleshooting:");
    console.error("");
    console.error("1. Verify Realtime server is running:");
    console.error("   docker ps | grep realtime");
    console.error("");
    console.error("2. Check Realtime server logs:");
    console.error("   docker logs transactional-base-realtime --tail 50");
    console.error("");
    console.error("3. Verify JWT configuration:");
    console.error(
      "   - JWT_SECRET in docker-compose.yml: your-super-secret-jwt-token-with-at-least-32-characters-long"
    );
    console.error("   - Check tenant configuration:");
    console.error(
      "     docker exec transactional-base-db psql -U postgres -c \"SELECT jwt_secret FROM tenants WHERE external_id = 'localhost';\""
    );
    console.error("");
    console.error("4. Ensure database is configured:");
    console.error("   cd services/sync-base && pnpm verify:realtime");
    console.error("");
    console.error("5. Try restarting the Realtime server:");
    console.error("   cd services/transactional-base");
    console.error("   docker-compose --profile manual restart realtime");
    console.error("");
    console.error("6. Check if tables are in publication:");
    console.error(
      "   docker exec transactional-base-db psql -U postgres -c \\"
    );
    console.error(
      "     \"SELECT * FROM pg_publication_tables WHERE pubname = 'supabase_realtime';\""
    );

    if (error.stack) {
      console.error("\n📋 Stack trace:");
      console.error(error.stack);
    }

    process.exit(1);
  }
}

// Run the test
testSimplifiedSync().catch(console.error);
