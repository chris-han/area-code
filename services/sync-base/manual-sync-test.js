#!/usr/bin/env node

/**
 * Manual Sync Test Script
 *
 * This script manually tests the sync functionality without Moose framework
 * to verify that Supabase real-time and Elasticsearch connections work.
 */

const { createClient } = require("@supabase/supabase-js");
const { Client } = require("@elastic/elasticsearch");

async function testManualSync() {
  console.log("🧪 Testing Manual Sync Functionality");
  console.log("===================================");

  // Configuration from .env
  const config = {
    supabaseRestUrl: process.env.SUPABASE_REST_URL || "http://localhost:3001", // PostgREST for queries
    supabaseRealtimeUrl: process.env.SUPABASE_URL || "http://localhost:4002", // Real-time server for subscriptions
    supabaseKey: process.env.SUPABASE_ANON_KEY || "your-anon-key",
    elasticsearchUrl: process.env.ELASTICSEARCH_URL || "http://localhost:9200",
  };

  console.log("🔧 Configuration:");
  console.log(`   Supabase REST: ${config.supabaseRestUrl}`);
  console.log(`   Supabase Real-time: ${config.supabaseRealtimeUrl}`);
  console.log(`   Elasticsearch: ${config.elasticsearchUrl}`);
  console.log("");

  try {
    // Test Elasticsearch connection
    console.log("1️⃣ Testing Elasticsearch connection...");
    const esClient = new Client({ node: config.elasticsearchUrl });

    try {
      await esClient.ping();
      console.log("✅ Elasticsearch connection successful");
    } catch (error) {
      console.error("❌ Elasticsearch connection failed:", error.message);
      return;
    }

    // Test Supabase connection
    console.log("2️⃣ Testing Supabase connection...");
    console.log(`   Using URL: ${config.supabaseRestUrl}`);
    console.log(`   Using Key: ${config.supabaseKey.substring(0, 20)}...`);
    const supabaseRest = createClient(
      config.supabaseRestUrl,
      config.supabaseKey
    );

    // Try to fetch data from foo table to test connection
    try {
      const { data, error } = await supabaseRest
        .from("foo")
        .select("*")
        .limit(1);

      if (error) {
        console.error("❌ Supabase query failed:", error.message);
        console.error("   Error details:", error);
        return;
      }

      console.log("✅ Supabase connection successful");
      console.log(`   Found ${data?.length || 0} records in foo table`);
    } catch (error) {
      console.error("❌ Supabase connection failed:", error.message);
      console.error("   Error details:", error);
      return;
    }

    // Test real-time subscription
    console.log("3️⃣ Testing Supabase real-time subscription...");
    const supabaseRealtime = createClient(
      config.supabaseRealtimeUrl,
      config.supabaseKey
    );

    const channel = supabaseRealtime
      .channel("manual-test-channel")
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "foo",
        },
        (payload) => {
          console.log("📡 Real-time event detected:", {
            event: payload.eventType,
            table: payload.table,
            id: payload.new?.id || payload.old?.id,
            timestamp: new Date().toISOString(),
          });

          // Sync to Elasticsearch
          syncToElasticsearch(esClient, payload);
        }
      )
      .subscribe((status) => {
        console.log(`🔌 Subscription status: ${status}`);
        if (status === "SUBSCRIBED") {
          console.log("✅ Real-time subscription active");
          console.log("");
          console.log(
            "💡 Now create/update/delete records in the foo table to test sync!"
          );
          console.log(
            '   Example: curl -X POST http://localhost:8081/api/foo -H "Content-Type: application/json" -d \'{"name": "Manual Test", "description": "Testing manual sync"}\''
          );
          console.log("");
        } else if (status === "CHANNEL_ERROR") {
          console.error("❌ Real-time subscription failed");
        }
      });

    // Keep running until interrupted
    console.log("🎧 Listening for real-time changes... (Press Ctrl+C to stop)");
    await new Promise((resolve) => {
      process.on("SIGINT", () => {
        console.log("\n🛑 Shutting down...");
        channel.unsubscribe();
        esClient.close();
        console.log("✅ Manual sync test stopped");
        resolve();
      });
    });
  } catch (error) {
    console.error("❌ Manual sync test failed:", error);
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

// Load environment variables
require("dotenv").config();

// Run the test
testManualSync().catch(console.error);
