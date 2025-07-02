import { db } from "../database/connection.js";
import { sql } from "drizzle-orm";

async function setupAuth() {
  console.log("🔐 Setting up authentication roles...");

  try {
    // Create anon role if it doesn't exist
    await db.execute(sql`
      DO $$
      BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anon') THEN
          CREATE ROLE anon NOLOGIN;
        END IF;
      END
      $$;
    `);
    console.log("✅ anon role created/verified");

    // Create authenticated role if it doesn't exist
    await db.execute(sql`
      DO $$
      BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticated') THEN
          CREATE ROLE authenticated NOLOGIN;
        END IF;
      END
      $$;
    `);
    console.log("✅ authenticated role created/verified");

    // Create service_role if it doesn't exist
    await db.execute(sql`
      DO $$
      BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'service_role') THEN
          CREATE ROLE service_role NOLOGIN BYPASSRLS;
        END IF;
      END
      $$;
    `);
    console.log("✅ service_role created/verified");

    // Grant necessary permissions to anon role
    await db.execute(sql`GRANT USAGE ON SCHEMA public TO anon;`);
    await db.execute(
      sql`GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO anon;`
    );
    await db.execute(
      sql`GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;`
    );
    console.log("✅ anon role permissions granted");

    // Grant necessary permissions to authenticated role
    await db.execute(sql`GRANT USAGE ON SCHEMA public TO authenticated;`);
    await db.execute(
      sql`GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;`
    );
    await db.execute(
      sql`GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;`
    );
    console.log("✅ authenticated role permissions granted");

    // Grant all permissions to service_role
    await db.execute(sql`GRANT ALL ON SCHEMA public TO service_role;`);
    await db.execute(
      sql`GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;`
    );
    await db.execute(
      sql`GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;`
    );
    console.log("✅ service_role permissions granted");

    console.log("🎉 Authentication setup completed successfully!");
  } catch (error) {
    console.error("❌ Auth setup failed:", error);
    throw error;
  } finally {
    process.exit(0);
  }
}

setupAuth().catch(console.error);
