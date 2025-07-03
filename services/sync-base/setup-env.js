#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

function setupEnvironment() {
  console.log("🔧 Setting up sync-base environment...");

  // Create .env content - simplified without auth
  const envContent = `# Transactional-base connection (simplified - no auth)
# PostgREST API runs on port 3001
SUPABASE_URL=http://localhost:3001
SUPABASE_REST_URL=http://localhost:3001

# Real-time WebSocket URL (port 4002)
REALTIME_URL=ws://localhost:4002

# No authentication keys needed anymore!
# The transactional-base now runs without auth

# Elasticsearch connection (from retrieval-base service)  
# When running retrieval-base locally with docker-compose, Elasticsearch runs on port 9200
ELASTICSEARCH_URL=http://localhost:9200
`;

  // Write .env file
  const envPath = path.join(__dirname, ".env");
  fs.writeFileSync(envPath, envContent);

  console.log("✅ .env file created for simplified setup");
  console.log("📍 PostgREST URL: http://localhost:3001");
  console.log("📍 Real-time URL: ws://localhost:4002");
  console.log("🔍 Elasticsearch URL: http://localhost:9200");
  console.log("");
  console.log(
    "⚠️  Note: Authentication has been removed from transactional-base"
  );
  console.log("    The services now run with direct postgres access");
  console.log("");
  console.log("🎉 Sync-base environment setup complete!");
}

setupEnvironment();
