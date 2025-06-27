import {
  createClient,
  SupabaseClient,
  RealtimeChannel,
  RealtimePostgresChangesPayload,
} from "@supabase/supabase-js";
import { Pool } from "pg";

export interface CDCEvent {
  table: string;
  operation: "INSERT" | "UPDATE" | "DELETE";
  record: any;
  old_record?: any;
  timestamp: Date;
  commit_timestamp?: string;
}

export interface CDCConfig {
  supabaseUrl: string;
  supabaseKey: string;
  transactionalDbUrl: string;
  tables: string[];
  batchSize: number;
  onBatch: (events: CDCEvent[]) => Promise<void>;
}

export class SupabaseCDCHandler {
  private supabase: SupabaseClient;
  private pool: Pool;
  private channels: Map<string, RealtimeChannel> = new Map();
  private eventBuffer: CDCEvent[] = [];
  private config: CDCConfig;
  private isRunning: boolean = false;
  private batchTimer?: ReturnType<typeof setInterval>;

  constructor(config: CDCConfig) {
    this.config = config;
    this.supabase = createClient(config.supabaseUrl, config.supabaseKey);
    this.pool = new Pool({ connectionString: config.transactionalDbUrl });
  }

  async start(): Promise<void> {
    if (this.isRunning) {
      console.log("🔄 CDC handler is already running");
      return;
    }

    console.log("🚀 Starting Supabase CDC handler...");

    try {
      // Test connections
      await this.testConnections();

      // Set up realtime subscriptions for each table
      for (const table of this.config.tables) {
        await this.subscribeToTable(table);
      }

      // Start batch processing timer
      this.startBatchTimer();

      this.isRunning = true;
      console.log("✅ CDC handler started successfully");
    } catch (error) {
      console.error("❌ Failed to start CDC handler:", error);
      throw error;
    }
  }

  async stop(): Promise<void> {
    if (!this.isRunning) {
      return;
    }

    console.log("🛑 Stopping Supabase CDC handler...");

    // Unsubscribe from all channels
    for (const [tableName, channel] of this.channels) {
      await this.supabase.removeChannel(channel);
      console.log(`📤 Unsubscribed from ${tableName}`);
    }

    this.channels.clear();

    // Clear batch timer
    if (this.batchTimer) {
      clearInterval(this.batchTimer);
      this.batchTimer = undefined;
    }

    // Process any remaining events
    if (this.eventBuffer.length > 0) {
      console.log(
        `📦 Processing ${this.eventBuffer.length} remaining events...`
      );
      await this.processBatch();
    }

    // Close database pool
    await this.pool.end();

    this.isRunning = false;
    console.log("✅ CDC handler stopped");
  }

  private async testConnections(): Promise<void> {
    // Test Supabase connection
    const { data, error } = await this.supabase
      .from("foo")
      .select("count")
      .limit(1);
    if (error && error.code !== "PGRST116") {
      // PGRST116 is "table not found" which is ok for testing
      throw new Error(`Supabase connection failed: ${error.message}`);
    }

    // Test PostgreSQL connection
    const client = await this.pool.connect();
    try {
      await client.query("SELECT NOW()");
    } finally {
      client.release();
    }

    console.log("✅ Database connections verified");
  }

  private async subscribeToTable(tableName: string): Promise<void> {
    console.log(`📡 Setting up realtime subscription for table: ${tableName}`);

    const channel = this.supabase
      .channel(`${tableName}-changes`)
      .on(
        "postgres_changes",
        {
          event: "*", // Listen to all events (INSERT, UPDATE, DELETE)
          schema: "public",
          table: tableName,
        },
        (payload) => {
          this.handleRealtimeEvent(tableName, payload);
        }
      )
      .subscribe((status) => {
        if (status === "SUBSCRIBED") {
          console.log(`✅ Subscribed to ${tableName} changes`);
        } else if (status === "CHANNEL_ERROR") {
          console.error(`❌ Error subscribing to ${tableName}:`, status);
        }
      });

    this.channels.set(tableName, channel);
  }

  private handleRealtimeEvent(
    tableName: string,
    payload: RealtimePostgresChangesPayload<any>
  ): void {
    const event: CDCEvent = {
      table: tableName,
      operation: payload.eventType as "INSERT" | "UPDATE" | "DELETE",
      record: payload.new || payload.old,
      old_record: payload.old,
      timestamp: new Date(),
      commit_timestamp: payload.commit_timestamp,
    };

    console.log(
      `📥 Received ${event.operation} event for ${tableName}:`,
      event.record?.id || "unknown"
    );

    this.eventBuffer.push(event);

    // Process batch immediately if buffer is full
    if (this.eventBuffer.length >= this.config.batchSize) {
      this.processBatch();
    }
  }

  private startBatchTimer(): void {
    // Process batches every 30 seconds even if not full
    this.batchTimer = setInterval(() => {
      if (this.eventBuffer.length > 0) {
        this.processBatch();
      }
    }, 30000);
  }

  private async processBatch(): Promise<void> {
    if (this.eventBuffer.length === 0) {
      return;
    }

    const batch = this.eventBuffer.splice(0, this.config.batchSize);
    console.log(`📦 Processing batch of ${batch.length} events`);

    try {
      await this.config.onBatch(batch);
      console.log(`✅ Successfully processed batch of ${batch.length} events`);
    } catch (error) {
      console.error(`❌ Error processing batch:`, error);

      // Re-add events to buffer for retry (simple retry strategy)
      this.eventBuffer.unshift(...batch);

      // Could implement more sophisticated retry logic here
      throw error;
    }
  }

  // Method to get historical changes (for initial sync or catch-up)
  async getHistoricalChanges(
    tableName: string,
    since: Date,
    limit: number = 1000
  ): Promise<CDCEvent[]> {
    console.log(
      `📚 Fetching historical changes for ${tableName} since ${since.toISOString()}`
    );

    const client = await this.pool.connect();
    try {
      // Query for records created/updated since the given timestamp
      const query = `
        SELECT *, 'UPDATE' as operation_type 
        FROM ${tableName} 
        WHERE updated_at > $1 OR created_at > $1
        ORDER BY COALESCE(updated_at, created_at) ASC 
        LIMIT $2
      `;

      const result = await client.query(query, [since, limit]);

      const events: CDCEvent[] = result.rows.map((row) => ({
        table: tableName,
        operation: new Date(row.created_at) > since ? "INSERT" : "UPDATE",
        record: row,
        timestamp: new Date(row.updated_at || row.created_at),
      }));

      console.log(
        `📚 Found ${events.length} historical changes for ${tableName}`
      );
      return events;
    } finally {
      client.release();
    }
  }

  // Method to perform initial sync for a table
  async performInitialSync(
    tableName: string,
    lastSyncTime?: Date
  ): Promise<CDCEvent[]> {
    const sinceTime =
      lastSyncTime || new Date(Date.now() - 24 * 60 * 60 * 1000); // Default to 24 hours ago
    return this.getHistoricalChanges(tableName, sinceTime);
  }

  // Get current status
  getStatus(): {
    isRunning: boolean;
    bufferedEvents: number;
    subscribedTables: string[];
  } {
    return {
      isRunning: this.isRunning,
      bufferedEvents: this.eventBuffer.length,
      subscribedTables: Array.from(this.channels.keys()),
    };
  }
}
