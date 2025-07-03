import { Client } from "pg";

async function setupRealtimeWithTenant() {
  const client = new Client({
    user: "postgres",
    host: "localhost",
    database: "postgres",
    password: "your-super-secret-and-long-postgres-password",
    port: 5434,
  });

  try {
    await client.connect();
    console.log("🔄 Setting up Supabase real-time functionality...");

    // First, create the tenants table if it doesn't exist
    console.log("Creating tenants table...");
    await client.query(`
      CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
      
      CREATE TABLE IF NOT EXISTS tenants (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        name TEXT NOT NULL,
        external_id TEXT UNIQUE NOT NULL,
        jwt_secret TEXT NOT NULL,
        postgres_cdc_default TEXT DEFAULT 'postgres_cdc_rls',
        max_concurrent_users INTEGER DEFAULT 200,
        max_events_per_second INTEGER DEFAULT 100,
        max_bytes_per_second INTEGER DEFAULT 100000,
        max_channels_per_client INTEGER DEFAULT 100,
        max_joins_per_second INTEGER DEFAULT 100,
        suspend BOOLEAN DEFAULT FALSE,
        inserted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
    `);

    // Insert or update the localhost tenant
    console.log("Setting up localhost tenant...");
    await client.query(`
      INSERT INTO tenants (name, external_id, jwt_secret)
      VALUES ('localhost', 'localhost', 'your-super-secret-jwt-token-with-at-least-32-characters-long')
      ON CONFLICT (external_id) 
      DO UPDATE SET 
        jwt_secret = EXCLUDED.jwt_secret,
        updated_at = NOW();
    `);

    // Drop existing publication if it exists
    console.log("Dropping existing publication if it exists...");
    await client.query("DROP PUBLICATION IF EXISTS supabase_realtime;");

    // Create the publication
    console.log("Creating supabase_realtime publication...");
    await client.query("CREATE PUBLICATION supabase_realtime;");

    // Add tables to the publication
    console.log("Adding tables to publication...");
    await client.query("ALTER PUBLICATION supabase_realtime ADD TABLE foo;");
    await client.query("ALTER PUBLICATION supabase_realtime ADD TABLE bar;");
    await client.query(
      "ALTER PUBLICATION supabase_realtime ADD TABLE foo_bar;"
    );

    // Set replica identity for tables
    console.log("Setting replica identity for tables...");
    await client.query("ALTER TABLE foo REPLICA IDENTITY FULL;");
    await client.query("ALTER TABLE bar REPLICA IDENTITY FULL;");
    await client.query("ALTER TABLE foo_bar REPLICA IDENTITY FULL;");

    console.log("✅ Real-time publication and tenant configured successfully!");
    console.log("\n📋 Configuration summary:");
    console.log("   • Created tenants table");
    console.log("   • Added localhost tenant configuration");
    console.log("   • Created supabase_realtime publication");
    console.log("   • Added foo, bar, and foo_bar tables to publication");
    console.log("   • Set replica identity for real-time updates");
    console.log("\n🔗 Tables are now ready for real-time subscriptions!");
  } catch (error) {
    console.error("❌ Error setting up real-time:", error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

setupRealtimeWithTenant();
