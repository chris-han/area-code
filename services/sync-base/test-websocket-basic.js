#!/usr/bin/env node

/**
 * Basic WebSocket test to verify connectivity
 */

const WebSocket = require("ws");

async function testBasicWebSocket() {
  console.log("🧪 Testing Basic WebSocket Connection");
  console.log("=====================================");
  console.log("");

  // Use the JWT token that the user specified
  const JWT_TOKEN =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzUxNTU0NDgyLCJleHAiOjE3ODMwOTA0ODJ9.74aZUGrZj6vJlBgUImfOAAO1BqE3Pd_j21fB36i1d3M";

  // Try with apikey parameter (what the server expects)
  const wsUrl = `ws://localhost:4002/socket/websocket?apikey=${JWT_TOKEN}&vsn=1.0.0`;

  console.log("🔧 Connecting to:", wsUrl.substring(0, 60) + "...");
  console.log("   (With JWT token signed with original secret)");
  console.log("   (SECURE_CHANNELS=false)");
  console.log("");

  const ws = new WebSocket(wsUrl);

  ws.on("open", () => {
    console.log("✅ WebSocket connection opened!");
    console.log("");
    console.log("📤 Sending heartbeat...");

    // Send a Phoenix-style heartbeat
    const heartbeat = JSON.stringify({
      topic: "phoenix",
      event: "heartbeat",
      payload: {},
      ref: "1",
    });

    ws.send(heartbeat);
  });

  ws.on("message", (data) => {
    console.log("📥 Received:", data.toString());

    // Try to parse as JSON
    try {
      const msg = JSON.parse(data.toString());
      console.log("   Parsed:", JSON.stringify(msg, null, 2));
    } catch (e) {
      // Not JSON, that's okay
    }
  });

  ws.on("error", (error) => {
    console.error("❌ WebSocket error:", error.message);
    console.error("   Error code:", error.code);
    console.error("   Error type:", error.name);
  });

  ws.on("close", (code, reason) => {
    console.log("📡 WebSocket connection closed");
    console.log("   Code:", code);
    console.log("   Reason:", reason.toString());
  });

  // Keep the script running
  await new Promise((resolve) => {
    process.on("SIGINT", () => {
      console.log("\n🛑 Shutting down...");
      ws.close();
      resolve();
    });
  });
}

// Run the test
testBasicWebSocket().catch(console.error);
