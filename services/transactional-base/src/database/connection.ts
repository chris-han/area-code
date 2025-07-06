import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";
import { config as dotenvConfig } from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

// Get current directory in ES module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from .env file in project root
dotenvConfig({ path: path.resolve(__dirname, "../../.env") });

// Database connection configuration
const password =
  process.env.POSTGRES_PASSWORD ||
  "your-super-secret-and-long-postgres-password";

// Use session-based connection (port 5432) for migrations and direct operations
// Use pooled transactional connections (port 6543) for runtime application usage via Supavisor
const isMigrationScript = process.argv.some((arg) => arg.includes("migrate"));

// For migrations, use direct postgres connection
// For runtime, use Supavisor pooled connection with tenant format
const tenantId = process.env.POOLER_TENANT_ID || "dev";
const DIRECT_PORT = process.env.POSTGRES_PORT || "5432";
const POOLER_PORT = process.env.POSTGRES_PORT || "6542";

const connectionString = isMigrationScript
  ? `postgresql://postgres.${tenantId}:${password}@localhost:${DIRECT_PORT}/postgres`
  : `postgresql://postgres.${tenantId}:${password}@localhost:${POOLER_PORT}/postgres`;

const userType = `postgres.${tenantId}`;
const portType = isMigrationScript
  ? "Supavisor session mode (5432)"
  : "Supavisor transaction mode (6543)";

console.log(`🔗 Connecting as ${userType} via ${portType} connection`);

const pool = new Pool({
  connectionString,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

export const db = drizzle(pool, { schema });

export { pool };
