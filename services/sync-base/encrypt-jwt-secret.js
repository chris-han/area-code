#!/usr/bin/env node

/**
 * Encrypt JWT secret for storage in tenants table
 * The Realtime server expects the JWT secret to be AES encrypted with DB_ENC_KEY
 */

const crypto = require("crypto");

const JWT_SECRET =
  "your-super-secret-jwt-token-with-at-least-32-characters-long";
const DB_ENC_KEY = "supabaserealtime"; // 16 characters for AES-128

function encrypt(text, key) {
  // Create a cipher using AES-128-CBC
  const algorithm = "aes-128-cbc";
  const keyBuffer = Buffer.from(key, "utf8");

  // Generate a random IV (initialization vector)
  const iv = crypto.randomBytes(16);

  // Create cipher
  const cipher = crypto.createCipheriv(algorithm, keyBuffer, iv);

  // Encrypt the text
  let encrypted = cipher.update(text, "utf8");
  encrypted = Buffer.concat([encrypted, cipher.final()]);

  // Combine IV and encrypted data, then base64 encode with proper padding
  const combined = Buffer.concat([iv, encrypted]);
  const base64 = combined.toString("base64");

  // Ensure proper base64 padding
  const paddingNeeded = (4 - (base64.length % 4)) % 4;
  const padded = base64 + "=".repeat(paddingNeeded);

  return padded;
}

console.log("JWT Secret:", JWT_SECRET);
console.log("DB_ENC_KEY:", DB_ENC_KEY);
console.log("");

try {
  const encryptedSecret = encrypt(JWT_SECRET, DB_ENC_KEY);
  console.log("Encrypted JWT Secret (base64 with padding):");
  console.log(encryptedSecret);
  console.log("Length:", encryptedSecret.length);
  console.log("");
  console.log("SQL Update Command:");
  console.log(
    `UPDATE public.tenants SET jwt_secret = '${encryptedSecret}' WHERE external_id = 'localhost';`
  );
} catch (error) {
  console.error("Encryption failed:", error.message);
}
