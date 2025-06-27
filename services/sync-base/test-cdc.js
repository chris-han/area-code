#!/usr/bin/env node

/**
 * CDC Workflow Test Script
 *
 * This script tests the CDC setup by:
 * 1. Checking database connectivity
 * 2. Creating test data in the transactional database
 * 3. Monitoring for CDC events
 */

const { Pool } = require("pg");

async function testCDCSetup() {
  console.log("🧪 Testing CDC Workflow Setup...\n");

  // Configuration
  const transactionalDbUrl =
    process.env.TRANSACTIONAL_DB_URL ||
    "postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:5433/postgres";

  const pool = new Pool({ connectionString: transactionalDbUrl });

  try {
    // Test 1: Database Connectivity
    console.log("1️⃣ Testing database connectivity...");
    const client = await pool.connect();
    const result = await client.query(
      "SELECT NOW() as current_time, version() as pg_version"
    );
    console.log(`✅ Connected to PostgreSQL: ${result.rows[0].current_time}`);
    console.log(`   Version: ${result.rows[0].pg_version.split(" ")[0]}\n`);

    // Test 2: Check if tables exist
    console.log("2️⃣ Checking if required tables exist...");
    const tables = ["foo", "bar", "foo_bar"];
    for (const table of tables) {
      const tableCheck = await client.query(
        `SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)`,
        [table]
      );
      if (tableCheck.rows[0].exists) {
        console.log(`✅ Table '${table}' exists`);
      } else {
        console.log(`❌ Table '${table}' not found`);
      }
    }
    console.log();

    // Test 3: Create test data
    console.log("3️⃣ Creating test data...");

    // Insert a test foo record
    const fooResult = await client.query(`
      INSERT INTO foo (name, description, status, priority) 
      VALUES ('CDC Test Foo', 'Created by CDC test script', 'active', 1) 
      RETURNING id, name, created_at
    `);
    const fooId = fooResult.rows[0].id;
    console.log(
      `✅ Created test foo record: ${fooId} - ${fooResult.rows[0].name}`
    );

    // Insert a test bar record
    const barResult = await client.query(
      `
      INSERT INTO bar (foo_id, value, label, notes) 
      VALUES ($1, 42, 'CDC Test Bar', 'Created by CDC test script') 
      RETURNING id, label, created_at
    `,
      [fooId]
    );
    const barId = barResult.rows[0].id;
    console.log(
      `✅ Created test bar record: ${barId} - ${barResult.rows[0].label}`
    );

    // Insert a test foo_bar relationship
    const fooBarResult = await client.query(
      `
      INSERT INTO foo_bar (foo_id, bar_id, relationship_type, metadata) 
      VALUES ($1, $2, 'test_relationship', '{"created_by": "cdc_test"}') 
      RETURNING id, relationship_type, created_at
    `,
      [fooId, barId]
    );
    console.log(
      `✅ Created test foo_bar record: ${fooBarResult.rows[0].id} - ${fooBarResult.rows[0].relationship_type}`
    );
    console.log();

    // Test 4: Update records to trigger CDC
    console.log("4️⃣ Updating records to trigger CDC events...");

    await client.query(
      `
      UPDATE foo SET description = 'Updated by CDC test script', updated_at = NOW() 
      WHERE id = $1
    `,
      [fooId]
    );
    console.log(`✅ Updated foo record: ${fooId}`);

    await client.query(
      `
      UPDATE bar SET notes = 'Updated by CDC test script', updated_at = NOW() 
      WHERE id = $1
    `,
      [barId]
    );
    console.log(`✅ Updated bar record: ${barId}`);
    console.log();

    // Test 5: Display current data
    console.log("5️⃣ Current data in database:");

    const fooData = await client.query("SELECT * FROM foo WHERE id = $1", [
      fooId,
    ]);
    console.log("📊 Foo record:", {
      id: fooData.rows[0].id,
      name: fooData.rows[0].name,
      status: fooData.rows[0].status,
      updated_at: fooData.rows[0].updated_at,
    });

    const barData = await client.query("SELECT * FROM bar WHERE id = $1", [
      barId,
    ]);
    console.log("📊 Bar record:", {
      id: barData.rows[0].id,
      foo_id: barData.rows[0].foo_id,
      value: barData.rows[0].value,
      updated_at: barData.rows[0].updated_at,
    });

    const fooBarData = await client.query(
      "SELECT * FROM foo_bar WHERE id = $1",
      [fooBarResult.rows[0].id]
    );
    console.log("📊 FooBar record:", {
      id: fooBarData.rows[0].id,
      foo_id: fooBarData.rows[0].foo_id,
      bar_id: fooBarData.rows[0].bar_id,
      relationship_type: fooBarData.rows[0].relationship_type,
    });
    console.log();

    console.log("✅ CDC Test Setup Complete!");
    console.log("\n📋 Next Steps:");
    console.log("1. Start the sync-base service: `pnpm dev`");
    console.log(
      "2. The CDC workflow should detect and process these test records"
    );
    console.log("3. Check the terminal output for CDC event logs");
    console.log(
      "4. Monitor the workflow with: `moose workflow status dataSyncWorkflow`"
    );
    console.log("\n🔍 Test Data IDs for monitoring:");
    console.log(`   Foo ID: ${fooId}`);
    console.log(`   Bar ID: ${barId}`);
    console.log(`   FooBar ID: ${fooBarResult.rows[0].id}`);

    client.release();
  } catch (error) {
    console.error("❌ CDC Test Failed:", error.message);
    console.error("\n🔧 Troubleshooting:");
    console.error("1. Ensure the transactional-base service is running");
    console.error("2. Check the database connection string");
    console.error("3. Verify the database migrations have been run");
    console.error("4. Make sure PostgreSQL is accessible on port 5433");
  } finally {
    await pool.end();
  }
}

// Run the test
testCDCSetup().catch(console.error);
