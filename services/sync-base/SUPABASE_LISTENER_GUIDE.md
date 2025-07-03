# 🔥 Supabase Realtime Listener Guide

This guide will help you test the Supabase Realtime listener functionality in your sync-base service.

## 🚀 Quick Setup

### 1. Prerequisites
- Supabase project with a database
- Node.js and pnpm installed
- Database table(s) to monitor

### 2. Environment Variables

Set up the environment variables:

```bash
# Run the setup script
node setup-env.js

# Or manually set:
export SUPABASE_URL="http://localhost:3001"
export REALTIME_URL="ws://localhost:4002"
export ELASTICSEARCH_URL="http://localhost:9200"
```

Note: No authentication keys are needed anymore - the transactional-base service runs without auth!

### 3. Enable Realtime for Your Tables

In your Supabase dashboard:
1. Go to Database > Replication
2. Find your table (e.g., `todos`, `users`, etc.)
3. Toggle on the switch for `supabase_realtime`

## 🧪 Testing the Listener

### Option 1: Quick Test Script

```bash
cd services/sync-base
npx ts-node test-listener.ts
```

This will start a listener that monitors ALL tables in the `public` schema.

### Option 2: Moose Workflow Test

To test with the Moose workflow:

```bash
cd services/sync-base
pnpm dev
```

Then in another terminal, trigger the workflow with your configuration.

## 📝 Create Test Data

While the listener is running, create some test data in your Supabase database:

### Using Supabase SQL Editor

```sql
-- Create a test table
CREATE TABLE todos (
  id SERIAL PRIMARY KEY,
  task TEXT NOT NULL,
  completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS (optional, for security)
ALTER TABLE todos ENABLE ROW LEVEL SECURITY;

-- Allow anonymous access for testing (remove in production!)
CREATE POLICY "Allow anonymous access" ON todos FOR ALL TO anon USING (true);
```

### Insert Test Data

```sql
-- Insert a new todo
INSERT INTO todos (task) VALUES ('Test the Supabase listener!');

-- Update a todo
UPDATE todos SET completed = true WHERE id = 1;

-- Delete a todo
DELETE FROM todos WHERE id = 1;
```

## 📡 Expected Output

When you make database changes, you should see output like:

```
🧪 Testing Supabase Realtime Listener
=====================================
🔧 Configuration:
  URL: https://your-project.supabase.co
  Schema: public
  Table: ALL TABLES

💡 To test this listener:
  1. Make sure your table has replication enabled in Supabase
  2. Insert/Update/Delete records in your database
  3. Watch for change events in this console

🔥 Starting Supabase Realtime listener...
🔌 Subscription status: SUBSCRIBED
✅ Successfully subscribed to public-all-changes
🎧 Listening for database changes... (Press Ctrl+C to stop)

📡 Database change detected: {
  event: 'INSERT',
  table: 'todos',
  schema: 'public',
  old: null,
  new: {
    id: 1,
    task: 'Test the Supabase listener!',
    completed: false,
    created_at: '2024-01-15T10:30:00.000Z'
  },
  timestamp: '2024-01-15T10:30:00.123Z'
}
```

## 🔧 Configuration Options

### Listen to Specific Table

Edit the test script or workflow configuration:

```typescript
const config: SupabaseListenerConfig = {
  supabaseUrl: process.env.SUPABASE_URL || 'http://localhost:3001',
  supabaseKey: 'no-auth-needed', // No auth required anymore
  schema: 'public',
  table: 'todos', // Specify table name
};
```

### Listen to Specific Events

Modify the listener to only listen to specific events:

```typescript
.on(
  'postgres_changes',
  {
    event: 'INSERT', // Only listen to INSERT events
    schema: 'public',
    table: 'todos',
  },
  (payload) => {
    console.log("New record inserted:", payload);
  }
)
```

## 🚨 Troubleshooting

### Connection Issues
- ✅ Check your Supabase URL and API key
- ✅ Verify your network connection
- ✅ Ensure your Supabase project is active

### No Events Received
- ✅ Make sure replication is enabled for your table
- ✅ Check that your database changes are actually happening
- ✅ Verify you're listening to the correct schema/table

### Permission Errors
- ✅ Ensure your API key has the right permissions
- ✅ Check your Row Level Security (RLS) policies
- ✅ For testing, you can temporarily disable RLS

## 🔥 Next Steps

Once you've verified the listener works:

1. **Integrate with your sync logic** - Process the received events
2. **Add error handling** - Handle connection failures gracefully  
3. **Add filtering** - Only process relevant changes
4. **Scale considerations** - Handle high-frequency changes
5. **Security** - Remove test policies and secure your database

## 📚 Resources

- [Supabase Realtime Documentation](https://supabase.com/docs/guides/realtime/postgres-changes)
- [Supabase JS Client Documentation](https://supabase.com/docs/reference/javascript/introduction)
- [Moose Framework Documentation](https://docs.getmoose.dev/) 