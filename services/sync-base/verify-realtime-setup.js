#!/usr/bin/env node

/**
 * Verification script to ensure database is properly configured for Supabase Realtime
 * Based on: https://github.com/supabase/realtime#server-setup
 */

const { Client } = require("pg");

async function verifyRealtimeSetup() {
  console.log("🔍 Verifying Realtime Database Setup");
  console.log("====================================");
  console.log("");

  const client = new Client({
    user: "postgres",
    host: "localhost",
    database: "postgres",
    password: "your-super-secret-and-long-postgres-password",
    port: 5434,
  });

  const issues = [];
  const warnings = [];

  try {
    await client.connect();
    console.log("✅ Connected to database");

    // 1. Check WAL level
    console.log("\n📋 Checking WAL level...");
    const walResult = await client.query("SHOW wal_level;");
    const walLevel = walResult.rows[0].wal_level;
    if (walLevel === "logical") {
      console.log(`✅ WAL level is set to: ${walLevel}`);
    } else {
      issues.push(`WAL level is '${walLevel}' but should be 'logical'`);
      console.log(`❌ WAL level is '${walLevel}' but should be 'logical'`);
    }

    // 2. Check max_replication_slots
    console.log("\n📋 Checking replication slots...");
    const slotsResult = await client.query("SHOW max_replication_slots;");
    const maxSlots = parseInt(slotsResult.rows[0].max_replication_slots);
    if (maxSlots >= 5) {
      console.log(`✅ max_replication_slots: ${maxSlots}`);
    } else {
      issues.push(
        `max_replication_slots is ${maxSlots} but should be at least 5`
      );
      console.log(
        `❌ max_replication_slots is ${maxSlots} but should be at least 5`
      );
    }

    // 3. Check max_wal_senders
    console.log("\n📋 Checking WAL senders...");
    const sendersResult = await client.query("SHOW max_wal_senders;");
    const maxSenders = parseInt(sendersResult.rows[0].max_wal_senders);
    if (maxSenders >= 5) {
      console.log(`✅ max_wal_senders: ${maxSenders}`);
    } else {
      issues.push(`max_wal_senders is ${maxSenders} but should be at least 5`);
      console.log(
        `❌ max_wal_senders is ${maxSenders} but should be at least 5`
      );
    }

    // 4. Check if publication exists
    console.log("\n📋 Checking publications...");
    const pubResult = await client.query(
      "SELECT pubname FROM pg_publication WHERE pubname = 'supabase_realtime';"
    );
    if (pubResult.rows.length > 0) {
      console.log("✅ Publication 'supabase_realtime' exists");

      // Check tables in publication
      const tablesResult = await client.query(`
        SELECT schemaname, tablename 
        FROM pg_publication_tables 
        WHERE pubname = 'supabase_realtime'
        ORDER BY schemaname, tablename;
      `);

      if (tablesResult.rows.length > 0) {
        console.log("📊 Tables in publication:");
        tablesResult.rows.forEach((row) => {
          console.log(`   • ${row.schemaname}.${row.tablename}`);
        });
      } else {
        warnings.push("No tables found in supabase_realtime publication");
        console.log("⚠️  No tables found in publication");
      }
    } else {
      issues.push("Publication 'supabase_realtime' does not exist");
      console.log("❌ Publication 'supabase_realtime' does not exist");
    }

    // 5. Check if tenants table exists
    console.log("\n📋 Checking tenants table...");
    const tenantsResult = await client.query(
      "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tenants');"
    );
    if (tenantsResult.rows[0].exists) {
      console.log("✅ Tenants table exists");

      // Check localhost tenant
      const tenantResult = await client.query(
        "SELECT external_id, jwt_secret FROM tenants WHERE external_id = 'localhost';"
      );
      if (tenantResult.rows.length > 0) {
        console.log("✅ Localhost tenant configured");
        const jwtLength = tenantResult.rows[0].jwt_secret.length;
        if (jwtLength >= 32) {
          console.log(`✅ JWT secret length: ${jwtLength} characters`);
        } else {
          issues.push(
            `JWT secret is only ${jwtLength} characters (minimum 32 required)`
          );
          console.log(
            `❌ JWT secret is only ${jwtLength} characters (minimum 32 required)`
          );
        }
      } else {
        issues.push("Localhost tenant not found in tenants table");
        console.log("❌ Localhost tenant not found");
      }
    } else {
      issues.push("Tenants table does not exist");
      console.log("❌ Tenants table does not exist");
    }

    // 6. Check replica identity on tables
    console.log("\n📋 Checking replica identity...");
    const replicaResult = await client.query(`
      SELECT 
        c.relname as table_name,
        CASE c.relreplident
          WHEN 'd' THEN 'default'
          WHEN 'n' THEN 'nothing'
          WHEN 'f' THEN 'full'
          WHEN 'i' THEN 'index'
        END as replica_identity
      FROM pg_class c
      JOIN pg_namespace n ON c.relnamespace = n.oid
      WHERE n.nspname = 'public'
        AND c.relkind = 'r'
        AND c.relname IN ('foo', 'bar', 'foo_bar')
      ORDER BY c.relname;
    `);

    replicaResult.rows.forEach((row) => {
      if (row.replica_identity === "full") {
        console.log(`✅ Table '${row.table_name}' has REPLICA IDENTITY FULL`);
      } else {
        warnings.push(
          `Table '${row.table_name}' has REPLICA IDENTITY ${row.replica_identity.toUpperCase()} (FULL recommended for real-time)`
        );
        console.log(
          `⚠️  Table '${row.table_name}' has REPLICA IDENTITY ${row.replica_identity.toUpperCase()}`
        );
      }
    });

    // 7. Check for active replication slots
    console.log("\n📋 Checking replication slots...");
    const activeSlots = await client.query(`
      SELECT slot_name, active, restart_lsn, confirmed_flush_lsn 
      FROM pg_replication_slots 
      WHERE slot_name LIKE '%realtime%';
    `);

    if (activeSlots.rows.length > 0) {
      console.log("📊 Realtime replication slots:");
      activeSlots.rows.forEach((slot) => {
        const status = slot.active ? "✅ ACTIVE" : "⚠️  INACTIVE";
        console.log(`   ${status} ${slot.slot_name}`);
      });
    } else {
      console.log(
        "ℹ️  No realtime replication slots found (will be created on first connection)"
      );
    }

    // Summary
    console.log("\n========================================");
    console.log("📊 VERIFICATION SUMMARY");
    console.log("========================================");

    if (issues.length === 0) {
      console.log("✅ All critical checks passed!");
    } else {
      console.log(`❌ Found ${issues.length} critical issue(s):`);
      issues.forEach((issue, i) => {
        console.log(`   ${i + 1}. ${issue}`);
      });
    }

    if (warnings.length > 0) {
      console.log(`\n⚠️  Found ${warnings.length} warning(s):`);
      warnings.forEach((warning, i) => {
        console.log(`   ${i + 1}. ${warning}`);
      });
    }

    if (issues.length > 0) {
      console.log("\n🔧 TO FIX:");
      console.log("1. Run the setup script:");
      console.log("   cd services/transactional-base && pnpm setup:realtime");
      console.log("");
      console.log("2. Ensure PostgreSQL is configured with:");
      console.log("   - wal_level=logical");
      console.log("   - max_replication_slots>=5");
      console.log("   - max_wal_senders>=5");
      console.log("");
      console.log("3. Restart the database container if needed:");
      console.log(
        "   cd services/transactional-base && docker-compose restart db"
      );
    }

    console.log("\n✨ Done!");
  } catch (error) {
    console.error("\n❌ Verification failed:", error.message);
    console.error("\n🔍 Make sure the database is running:");
    console.error(
      "   cd services/transactional-base && docker-compose up -d db"
    );
  } finally {
    await client.end();
  }
}

// Run verification
verifyRealtimeSetup().catch(console.error);
