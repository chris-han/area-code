#!/usr/bin/env node

/**
 * Generate a JWT token for testing Supabase Realtime
 */

const jwt = require("jsonwebtoken");

// The simplified JWT secret without hyphens
const JWT_SECRET = "supersecretjwttokenwithatleast32characterslong";

console.log("JWT Secret:", JWT_SECRET);

// Generate a token with appropriate claims
const payload = {
  role: "anon",
  iss: "supabase",
  iat: Math.floor(Date.now() / 1000),
  exp: Math.floor(Date.now() / 1000) + 365 * 24 * 60 * 60, // 1 year from now
};

const token = jwt.sign(payload, JWT_SECRET);

console.log("\nGenerated JWT Token:");
console.log(token);

// Verify the token
try {
  const decoded = jwt.verify(token, JWT_SECRET);
  console.log("\nDecoded token:");
  console.log(JSON.stringify(decoded, null, 2));
} catch (err) {
  console.error("\nToken verification failed:", err.message);
}
