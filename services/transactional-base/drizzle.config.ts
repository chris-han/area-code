import type { Config } from "drizzle-kit";
import { config as dotenvConfig } from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

// Get current directory in ES module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from .env file in project root
dotenvConfig({ path: path.resolve(__dirname, ".env") });

export default {
  schema: "./src/database/schema.ts",
  out: "./migrations",
  driver: "pg",
  dbCredentials: {
    connectionString:
      process.env.DATABASE_URL ||
      `postgresql://postgres.${process.env.POOLER_TENANT_ID}:${process.env.POSTGRES_PASSWORD}@localhost:5432/postgres`, // Supavisor session mode for migrations
  },
} satisfies Config;
