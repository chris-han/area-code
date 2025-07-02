import { db } from "../database/connection.js";
import { sql } from "drizzle-orm";

async function setupRealtime() {
  console.log("🔄 Setting up Supabase real-time functionality...");

  try {
    // Create the _realtime schema for the real-time server
    console.log("Creating _realtime schema...");
    await db.execute(sql`CREATE SCHEMA IF NOT EXISTS _realtime;`);

    // Create the tenants table required by Supabase real-time server in _realtime schema
    console.log("Creating tenants table in _realtime schema...");
    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS _realtime.tenants (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL,
        external_id TEXT NOT NULL UNIQUE,
        jwt_secret TEXT NOT NULL,
        postgres_cdc_default TEXT DEFAULT 'false',
        max_concurrent_users INTEGER DEFAULT 200,
        max_events_per_second INTEGER DEFAULT 100,
        max_bytes_per_second INTEGER DEFAULT 10485760,
        max_channels_per_client INTEGER DEFAULT 100,
        max_joins_per_second INTEGER DEFAULT 10,
        suspend BOOLEAN DEFAULT false,
        inserted_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
      );
    `);

    // Insert default tenant for localhost
    console.log("Inserting default tenant...");
    await db.execute(sql`
      INSERT INTO _realtime.tenants (name, external_id, jwt_secret)
      VALUES ('Default', 'localhost', 'your-super-secret-jwt-token-with-at-least-32-characters-long')
      ON CONFLICT (external_id) DO NOTHING;
    `);

    // Create extensions table required by Supabase real-time server
    console.log("Creating extensions table...");
    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS _realtime.extensions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        type TEXT NOT NULL,
        settings JSONB,
        tenant_external_id TEXT NOT NULL REFERENCES _realtime.tenants(external_id) ON DELETE CASCADE,
        inserted_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
      );
    `);

    // Insert default PostgresCdcRls extension
    console.log("Inserting default extension...");
    await db.execute(sql`
      INSERT INTO _realtime.extensions (type, settings, tenant_external_id)
      VALUES ('postgres_cdc_rls', '{}', 'localhost')
      ON CONFLICT DO NOTHING;
    `);

    // Create the realtime extension if it doesn't exist
    console.log("Creating supabase_realtime extension...");
    try {
      await db.execute(
        sql`CREATE EXTENSION IF NOT EXISTS supabase_realtime WITH SCHEMA _realtime;`
      );
    } catch (error) {
      console.log(
        "Note: supabase_realtime extension not available, using basic realtime setup"
      );
    }

    // Create publication for all tables
    console.log("Creating realtime publication...");
    try {
      await db.execute(sql`DROP PUBLICATION IF EXISTS supabase_realtime;`);
    } catch (error) {
      // Publication might not exist, that's OK
    }

    await db.execute(sql`CREATE PUBLICATION supabase_realtime FOR ALL TABLES;`);

    // Enable real-time for specific tables
    console.log("Configuring real-time for foo and bar tables...");

    // Add replica identity for tables (required for real-time)
    await db.execute(sql`ALTER TABLE public.foo REPLICA IDENTITY FULL;`);
    await db.execute(sql`ALTER TABLE public.bar REPLICA IDENTITY FULL;`);
    await db.execute(sql`ALTER TABLE public.foo_bar REPLICA IDENTITY FULL;`);

    // Grant permissions to publication
    await db.execute(sql`GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;`);
    await db.execute(
      sql`GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;`
    );

    // Create a basic real-time configuration table if needed
    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS _realtime.schema_migrations (
        version text PRIMARY KEY,
        inserted_at timestamp with time zone DEFAULT NOW()
      );
    `);

    // Insert initial schema version
    await db.execute(sql`
      INSERT INTO _realtime.schema_migrations (version) 
      VALUES ('20210101000000_initial') 
      ON CONFLICT (version) DO NOTHING;
    `);

    console.log("✅ Real-time functionality configured successfully!");
    console.log("");
    console.log("📋 Configuration summary:");
    console.log("   • Created _realtime schema");
    console.log("   • Set up publication for all tables");
    console.log(
      "   • Enabled replica identity for foo, bar, and foo_bar tables"
    );
    console.log("   • Granted necessary permissions");
    console.log("");
    console.log("🔗 Real-time server accessible at: http://localhost:4002");
  } catch (error) {
    console.error("❌ Real-time setup failed:", error);
    throw error;
  } finally {
    process.exit(0);
  }
}

// Run the setup
setupRealtime().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
