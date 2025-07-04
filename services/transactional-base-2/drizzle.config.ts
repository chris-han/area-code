import type { Config } from "drizzle-kit";
import { config as dotenvConfig } from "dotenv";

// Load environment variables from .env.development
dotenvConfig({ path: ".env.development" });

export default {
  schema: "./src/database/schema.ts",
  out: "./migrations",
  driver: "pg",
  dbCredentials: {
    connectionString:
      process.env.DATABASE_URL ||
      "postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:6543/postgres",
  },
} satisfies Config;
