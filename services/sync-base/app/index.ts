import { Task, Workflow } from "@514labs/moose-lib";
import { createClient } from "@supabase/supabase-js";

// export interface Foo {
//   name: string;
// }

// Simple listener task for transactional-base Supabase instance
export const supabaseListenerTask = new Task<null, void>(
  "transactional-listener",
  {
    run: async () => {
      // Configuration for local transactional-base Supabase
      const config = {
        supabaseUrl: process.env.SUPABASE_URL || "http://localhost:3001",
        supabaseKey: process.env.SUPABASE_ANON_KEY || "your-anon-key",
        tables: ["foo", "bar", "foo_bar"],
      };
      console.log("🔥 Starting transactional-base Supabase listener...");
      console.log(`📍 Connecting to: ${config.supabaseUrl}`);
      console.log(
        `📋 Monitoring tables: ${config.tables?.join(", ") || "ALL"}`
      );

      // Create Supabase client
      const supabase = createClient(config.supabaseUrl, config.supabaseKey);

      // Set up listeners for each table
      const tables = config.tables || ["foo", "bar", "foo_bar"];
      const channels: any[] = [];

      for (const table of tables) {
        const channelName = `${table}-changes`;

        const channel = supabase
          .channel(channelName)
          .on(
            "postgres_changes",
            {
              event: "*", // Listen to all events (INSERT, UPDATE, DELETE)
              schema: "public",
              table: table,
            },
            (payload) => {
              console.log(`📡 [${table}] Database change:`, {
                event: payload.eventType,
                table: payload.table,
                old: payload.old,
                new: payload.new,
                timestamp: new Date().toISOString(),
              });
            }
          )
          .subscribe((status) => {
            console.log(`🔌 [${table}] Status: ${status}`);
            if (status === "SUBSCRIBED") {
              console.log(`✅ [${table}] Successfully subscribed`);
            } else if (status === "CHANNEL_ERROR") {
              console.error(`❌ [${table}] Subscription error`);
            }
          });

        channels.push(channel);
      }

      console.log(
        "🎧 Listening for database changes... (Press Ctrl+C to stop)"
      );

      // Keep the listener active
      await new Promise<void>((resolve) => {
        process.on("SIGINT", () => {
          console.log("\n🛑 Shutting down listeners...");
          channels.forEach((channel) => channel.unsubscribe());
          resolve();
        });
      });
    },
  }
);

export const myworkflow = new Workflow("transactional-sync-workflow", {
  startingTask: supabaseListenerTask,
});
