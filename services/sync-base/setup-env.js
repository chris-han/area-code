#!/usr/bin/env node

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

function base64UrlEncode(str) {
  return Buffer.from(str)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
}

function generateJWT(secret, payload) {
  const header = { alg: "HS256", typ: "JWT" };

  const encodedHeader = base64UrlEncode(JSON.stringify(header));
  const encodedPayload = base64UrlEncode(JSON.stringify(payload));

  const signature = crypto
    .createHmac("sha256", secret)
    .update(`${encodedHeader}.${encodedPayload}`)
    .digest("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");

  return `${encodedHeader}.${encodedPayload}.${signature}`;
}

function setupEnvironment() {
  console.log("🔧 Setting up sync-base environment...");

  // JWT secret from transactional-base docker-compose
  const jwtSecret =
    "your-super-secret-jwt-token-with-at-least-32-characters-long";

  // Generate anon key
  const anonPayload = {
    iss: "postgrest",
    role: "anon",
    exp: Math.floor(Date.now() / 1000) + 365 * 24 * 60 * 60, // 1 year from now
  };
  const anonKey = generateJWT(jwtSecret, anonPayload);

  // Create .env content
  const envContent = `# Supabase connection (from transactional-base service)
# Real-time server runs on port 4002, PostgREST on port 3001
SUPABASE_URL=http://localhost:4002
SUPABASE_REST_URL=http://localhost:3001

# Generated anon key that matches the JWT secret in transactional-base docker-compose
SUPABASE_ANON_KEY=${anonKey}

# Elasticsearch connection (from retrieval-base service)  
# When running retrieval-base locally with docker-compose, Elasticsearch runs on port 9200
ELASTICSEARCH_URL=http://localhost:9200
`;

  // Write .env file
  const envPath = path.join(__dirname, ".env");
  fs.writeFileSync(envPath, envContent);

  console.log("✅ .env file created with correct JWT tokens");
  console.log("📍 Supabase URL: http://localhost:3001");
  console.log("🔍 Elasticsearch URL: http://localhost:9200");
  console.log("🎉 Sync-base environment setup complete!");
}

setupEnvironment();
