import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";
import { config as dotenvConfig } from "dotenv";

// Load environment variables from .env.development
dotenvConfig({ path: ".env.development" });

// Use the pooler (Supavisor) for connection pooling
// The pooler runs on port 6543 in transaction mode
const connectionString =
  process.env.DATABASE_URL ||
  "postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:6543/postgres";

const pool = new Pool({
  connectionString,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

export const db = drizzle(pool, { schema });

export { pool };
