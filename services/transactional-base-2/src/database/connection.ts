import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";
import { config as dotenvConfig } from "dotenv";

// Load environment variables from .env.development
dotenvConfig({ path: ".env.development" });

// According to Supabase docs:
// - Supavisor is the connection pooler used in the Supabase stack
// - Use postgres user with tenant ID for authentication
// - Format: postgres.{tenant-id}:password@host:port/database
const tenantId = process.env.POOLER_TENANT_ID || "dev";
const password =
  process.env.POSTGRES_PASSWORD ||
  "your-super-secret-and-long-postgres-password";

// Use session-based connection (port 5432) for migrations and direct operations
// Use pooled transactional connections (port 6543) for runtime application usage via Supavisor
const isMigrationScript = process.argv.some((arg) => arg.includes("migrate"));

const connectionString = isMigrationScript
  ? `postgresql://postgres.${tenantId}:${password}@localhost:5432/postgres`
  : `postgresql://postgres.${tenantId}:${password}@localhost:6543/postgres`;

const userType = "postgres";
const portType = isMigrationScript
  ? "session-based (5432)"
  : "pooled via Supavisor (6543)";

console.log(
  `🔗 Connecting as ${userType}.${tenantId} via ${portType} connection`
);

const pool = new Pool({
  connectionString,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

export const db = drizzle(pool, { schema });

export { pool };
