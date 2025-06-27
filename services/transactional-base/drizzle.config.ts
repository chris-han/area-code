import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./src/database/schema.ts",
  out: "./migrations",
  driver: "pg",
  dbCredentials: {
    connectionString:
      process.env.DATABASE_URL ||
      "postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:5433/postgres",
  },
  verbose: true,
  strict: true,
}); 