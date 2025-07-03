#!/usr/bin/env node

/**
 * Manual Sync Test Script
 *
 * This script tests the synchronization functionality by making direct API calls
 * to insert/update/delete records and observing the sync behavior.
 */

const { createClient } = require("@supabase/supabase-js");
const { Client } = require("@elastic/elasticsearch");
const axios = require("axios");

// Load environment variables
require("dotenv").config();

async function manualSyncTest() {
  console.log("🧪 Manual Sync Test");
  console.log("===================");

  const config = {
    supabaseUrl: process.env.SUPABASE_URL || "http://localhost:3001",
    supabaseKey: "no-auth-needed", // No auth required
    postgrestUrl: process.env.SUPABASE_REST_URL || "http://localhost:3001",
    elasticsearchUrl: process.env.ELASTICSEARCH_URL || "http://localhost:9200",
  };

  console.log("🔧 Configuration:");
  console.log(`   Supabase URL: ${config.supabaseUrl}`);
  console.log(`   PostgREST URL: ${config.postgrestUrl}`);
  console.log(`   Elasticsearch: ${config.elasticsearchUrl}`);
  console.log(`   Auth: Disabled (simplified setup)`);
  console.log("");

  try {
    // 1. Test Elasticsearch connection
    console.log("1️⃣ Testing Elasticsearch connection...");
    const esClient = new Client({ node: config.elasticsearchUrl });
    await esClient.ping();
    console.log("✅ Elasticsearch connection successful");

    // 2. Test PostgREST API connection
    console.log("2️⃣ Testing PostgREST API...");
    try {
      const response = await axios.get(`${config.postgrestUrl}/foo?limit=1`);
      console.log("✅ PostgREST connection successful");
    } catch (error) {
      console.error("❌ PostgREST connection failed:", error.message);
      return;
    }

    // 3. Create Supabase client for real-time
    console.log("3️⃣ Setting up Supabase real-time client...");
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

    // 4. Subscribe to changes
    let changesReceived = [];
    const channel = supabase
      .channel("test-changes")
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "foo",
        },
        (payload) => {
          console.log("📡 Change detected:", payload.eventType);
          changesReceived.push(payload);
        }
      )
      .subscribe();

    console.log("✅ Subscribed to real-time changes");

    // Wait a bit for subscription to be ready
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // 5. Create a test record
    console.log("\n4️⃣ Creating test record...");
    const testRecord = {
      name: `Sync Test ${Date.now()}`,
      description: "Testing real-time sync",
      status: "active",
      priority: 1,
    };

    const createResponse = await axios.post(
      `${config.postgrestUrl}/foo`,
      testRecord,
      { headers: { "Content-Type": "application/json" } }
    );

    const createdId = createResponse.data[0].id;
    console.log(`✅ Created record with ID: ${createdId}`);

    // Wait for sync
    await new Promise((resolve) => setTimeout(resolve, 3000));

    // 6. Check if synced to Elasticsearch
    console.log("\n5️⃣ Checking Elasticsearch...");
    try {
      const esDoc = await esClient.get({
        index: "foos",
        id: createdId,
      });
      console.log("✅ Document found in Elasticsearch!");
      console.log(
        `   Name: ${esDoc._source.name}, Status: ${esDoc._source.status}`
      );
    } catch (error) {
      console.error("❌ Document not found in Elasticsearch");
    }

    // 7. Update the record
    console.log("\n6️⃣ Updating test record...");
    const updateResponse = await axios.patch(
      `${config.postgrestUrl}/foo?id=eq.${createdId}`,
      { status: "updated", priority: 2 },
      { headers: { "Content-Type": "application/json" } }
    );
    console.log("✅ Record updated");

    // Wait for sync
    await new Promise((resolve) => setTimeout(resolve, 3000));

    // 8. Check if update synced
    console.log("\n7️⃣ Checking updated document in Elasticsearch...");
    try {
      const esDoc = await esClient.get({
        index: "foos",
        id: createdId,
      });
      console.log("✅ Updated document found!");
      console.log(
        `   Status: ${esDoc._source.status}, Priority: ${esDoc._source.priority}`
      );
    } catch (error) {
      console.error("❌ Updated document not found");
    }

    // 9. Delete the record
    console.log("\n8️⃣ Deleting test record...");
    await axios.delete(`${config.postgrestUrl}/foo?id=eq.${createdId}`);
    console.log("✅ Record deleted");

    // Wait for sync
    await new Promise((resolve) => setTimeout(resolve, 3000));

    // 10. Check if deleted from Elasticsearch
    console.log("\n9️⃣ Checking deletion in Elasticsearch...");
    try {
      await esClient.get({
        index: "foos",
        id: createdId,
      });
      console.error("❌ Document still exists in Elasticsearch!");
    } catch (error) {
      if (error.meta?.statusCode === 404) {
        console.log("✅ Document successfully deleted from Elasticsearch!");
      } else {
        console.error("❌ Error checking document:", error.message);
      }
    }

    // Summary
    console.log("\n📊 Test Summary:");
    console.log(`   Real-time changes received: ${changesReceived.length}`);
    changesReceived.forEach((change, i) => {
      console.log(`   ${i + 1}. ${change.eventType} event`);
    });

    // Cleanup
    channel.unsubscribe();
    await esClient.close();

    console.log("\n✅ Manual sync test completed!");
  } catch (error) {
    console.error("❌ Test failed:", error);
  }
}

// Run the test
manualSyncTest().catch(console.error);
