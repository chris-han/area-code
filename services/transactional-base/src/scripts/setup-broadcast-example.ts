import { db } from "../database/connection.js";
import { sql } from "drizzle-orm";

/**
 * Example script showing how to set up broadcast changes with triggers
 * This follows the Supabase documentation approach for real-time
 * Run this if you want to use the broadcast method instead of Postgres Changes
 */
async function setupBroadcastExample() {
  console.log("🔄 Setting up broadcast changes example...");

  try {
    // Create a function that broadcasts changes
    console.log("Creating broadcast function...");
    await db.execute(sql`
      CREATE OR REPLACE FUNCTION public.broadcast_table_changes()
      RETURNS trigger
      SECURITY DEFINER
      LANGUAGE plpgsql
      AS $$
      BEGIN
        -- Using table name as topic prefix
        PERFORM realtime.broadcast_changes(
          TG_TABLE_NAME || ':' || COALESCE(NEW.id, OLD.id)::text,
          TG_OP,
          TG_OP,
          TG_TABLE_NAME,
          TG_TABLE_SCHEMA,
          NEW,
          OLD
        );
        RETURN NULL;
      END;
      $$;
    `);

    // Create triggers for each table
    console.log("Creating triggers for broadcast...");

    // Trigger for foo table
    await db.execute(sql`
      DROP TRIGGER IF EXISTS broadcast_foo_changes ON public.foo;
      CREATE TRIGGER broadcast_foo_changes
      AFTER INSERT OR UPDATE OR DELETE
      ON public.foo
      FOR EACH ROW
      EXECUTE FUNCTION broadcast_table_changes();
    `);

    // Trigger for bar table
    await db.execute(sql`
      DROP TRIGGER IF EXISTS broadcast_bar_changes ON public.bar;
      CREATE TRIGGER broadcast_bar_changes
      AFTER INSERT OR UPDATE OR DELETE
      ON public.bar
      FOR EACH ROW
      EXECUTE FUNCTION broadcast_table_changes();
    `);

    console.log("✅ Broadcast changes configured successfully!");
    console.log("");
    console.log("📋 How to use on the client side:");
    console.log("");
    console.log("// Listen to changes for a specific record");
    console.log("const recordId = 'some-uuid';");
    console.log("const channel = supabase");
    console.log(
      "  .channel(`foo:\${recordId}`, { config: { private: true } })"
    );
    console.log(
      "  .on('broadcast', { event: 'INSERT' }, (payload) => console.log('New record:', payload))"
    );
    console.log(
      "  .on('broadcast', { event: 'UPDATE' }, (payload) => console.log('Updated:', payload))"
    );
    console.log(
      "  .on('broadcast', { event: 'DELETE' }, (payload) => console.log('Deleted:', payload))"
    );
    console.log("  .subscribe();");
  } catch (error) {
    console.error("❌ Broadcast setup failed:", error);
    throw error;
  } finally {
    process.exit(0);
  }
}

// Run the setup
setupBroadcastExample().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
