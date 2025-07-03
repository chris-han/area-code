#!/usr/bin/env node

/**
 * Simple Sync Test Script
 *
 * This script tests sync functionality using direct HTTP calls and WebSocket connections
 * instead of the Supabase client library to isolate configuration issues.
 */

const { Client } = require("@elastic/elasticsearch");
const WebSocket = require("ws");
const axios = require("axios");

// Load environment variables
require("dotenv").config();

async function simpleSync() {
  console.log("🧪 Simple Sync Test");
  console.log("==================");

  const config = {
    postgrestUrl: process.env.SUPABASE_REST_URL || "http://localhost:3001",
    realtimeUrl: process.env.REALTIME_URL || "ws://localhost:4002",
    elasticsearchUrl: process.env.ELASTICSEARCH_URL || "http://localhost:9200",
  };

  console.log("🔧 Configuration:");
  console.log(`   PostgREST: ${config.postgrestUrl}`);
  console.log(`   Real-time: ${config.realtimeUrl}`);
  console.log(`   Elasticsearch: ${config.elasticsearchUrl}`);
  console.log(`   Auth: Disabled (simplified setup)`);
  console.log("");

  try {
    // Test Elasticsearch
    console.log("1️⃣ Testing Elasticsearch...");
    const esClient = new Client({ node: config.elasticsearchUrl });
    await esClient.ping();
    console.log("✅ Elasticsearch connection successful");

    // Test PostgREST directly
    console.log("2️⃣ Testing PostgREST...");
    try {
      const response = await axios.get(`${config.postgrestUrl}/foo?limit=1`);
      console.log("✅ PostgREST connection successful");
      console.log(`   Found ${response.data.length} records`);
    } catch (error) {
      console.error("❌ PostgREST connection failed:", error.message);
      return;
    }

    // Test WebSocket real-time connection
    console.log("3️⃣ Testing WebSocket real-time connection...");

    const wsUrl = config.realtimeUrl + "/socket/websocket";
    console.log(`   Connecting to: ${wsUrl}`);

    // Connect without authentication
    const ws = new WebSocket(wsUrl);

    ws.on("open", () => {
      console.log("✅ WebSocket connection opened");

      // Subscribe to foo table changes
      const subscribeMessage = {
        topic: "realtime:public:foo",
        event: "phx_join",
        payload: {},
        ref: "1",
      };

      ws.send(JSON.stringify(subscribeMessage));
      console.log("📡 Subscribed to foo table changes");

      console.log("🎧 Listening for real-time changes...");
      console.log(
        '   Create a foo item to test: curl -X POST http://localhost:8081/api/foo -H "Content-Type: application/json" -d \'{"name": "WebSocket Test", "description": "Testing direct WebSocket"}\''
      );
    });

    ws.on("message", (data) => {
      try {
        const message = JSON.parse(data.toString());
        console.log("📡 WebSocket message received:", {
          topic: message.topic,
          event: message.event,
          timestamp: new Date().toISOString(),
        });

        if (message.event === "postgres_changes") {
          console.log("🔥 Database change detected!", message.payload);

          // Sync to Elasticsearch
          syncToElasticsearch(esClient, message.payload);
        }
      } catch (error) {
        console.error("❌ Error parsing WebSocket message:", error);
      }
    });

    ws.on("error", (error) => {
      console.error("❌ WebSocket error:", error.message);
    });

    ws.on("close", (code, reason) => {
      console.log(`🔌 WebSocket closed: ${code} - ${reason}`);
    });

    // Keep running
    process.on("SIGINT", () => {
      console.log("\n🛑 Shutting down...");
      ws.close();
      esClient.close();
      process.exit(0);
    });

    // Keep alive
    await new Promise(() => {});
  } catch (error) {
    console.error("❌ Simple sync test failed:", error);
  }
}

async function syncToElasticsearch(esClient, payload) {
  try {
    const { eventType, new: newRecord, old: oldRecord } = payload;
    const record = newRecord || oldRecord;

    if (!record) {
      console.warn("⚠️ No record data available");
      return;
    }

    console.log(`🔄 Syncing ${eventType} to Elasticsearch...`);

    switch (eventType) {
      case "INSERT":
      case "UPDATE":
        await esClient.index({
          index: "foos",
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
        console.log(`✅ Synced ${eventType} to Elasticsearch: ${record.id}`);
        break;

      case "DELETE":
        await esClient.delete({
          index: "foos",
          id: record.id,
          refresh: true,
        });
        console.log(`✅ Deleted from Elasticsearch: ${record.id}`);
        break;

      default:
        console.log(`⚠️ Unknown event type: ${eventType}`);
    }
  } catch (error) {
    console.error(`❌ Failed to sync to Elasticsearch:`, error);
  }
}

// Run the test
simpleSync().catch(console.error);
