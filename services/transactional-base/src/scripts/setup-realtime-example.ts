/**
 * Example script showing how to configure PostgreSQL for realtime functionality
 * This creates the necessary database structures for realtime features
 */

import { pool } from "../database/connection";

async function setupRealtimeExample() {
  const client = await pool.connect();

  try {
    console.log("Setting up realtime example configuration...");

    // Create a sample table with realtime enabled
    await client.query(`
      CREATE TABLE IF NOT EXISTS realtime_messages (
        id SERIAL PRIMARY KEY,
        channel TEXT NOT NULL,
        user_id TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Grant permissions for realtime access
    await client.query(`
      GRANT ALL ON TABLE realtime_messages TO anon;
      GRANT USAGE, SELECT ON SEQUENCE realtime_messages_id_seq TO anon;
    `);

    // Create a publication for realtime if it doesn't exist
    await client.query(`
      DO $$ 
      BEGIN
        IF NOT EXISTS (
          SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime'
        ) THEN
          CREATE PUBLICATION supabase_realtime FOR ALL TABLES;
        END IF;
      END $$;
    `);

    // Add the table to the publication
    await client.query(`
      ALTER PUBLICATION supabase_realtime ADD TABLE realtime_messages;
    `);

    console.log("✅ Realtime example setup complete!");
    console.log("\nYou can now:");
    console.log(
      "1. Insert messages: POST to http://localhost:3001/realtime_messages"
    );
    console.log(
      "2. Query messages: GET http://localhost:3001/realtime_messages"
    );
    console.log("\nExample insert:");
    console.log(`curl -X POST http://localhost:3001/realtime_messages \\
  -H "Content-Type: application/json" \\
  -H "Prefer: return=representation" \\
  -d '{"channel": "general", "user_id": "user123", "message": "Hello, World!"}'`);
  } catch (error) {
    console.error("❌ Error setting up realtime example:", error);
  } finally {
    client.release();
  }
}

setupRealtimeExample();
