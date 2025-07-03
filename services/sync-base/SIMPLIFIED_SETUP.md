# 🎉 Simplified Sync-Base Setup

This document explains the changes made to sync-base to work with the simplified transactional-base service.

## 🔄 What Changed

### 1. **No More Authentication**
- ✅ Removed all JWT token generation
- ✅ No more `SUPABASE_ANON_KEY` needed
- ✅ Direct PostgreSQL access via PostgREST

### 2. **Simplified Environment Variables**
```bash
# Old setup (with auth)
SUPABASE_URL=http://localhost:3001
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# New setup (no auth)
SUPABASE_URL=http://localhost:3001
SUPABASE_REST_URL=http://localhost:3001
REALTIME_URL=ws://localhost:4002
ELASTICSEARCH_URL=http://localhost:9200
```

### 3. **Updated Setup Script**
The `setup-env.js` script now:
- Creates a simpler `.env` file
- No JWT token generation
- Clear comments explaining the simplified setup

## 🚀 Quick Start

### 1. Set up environment
```bash
node setup-env.js
```

### 2. Start the sync service
```bash
pnpm dev
```

### 3. Test the sync
```bash
# Test simplified sync
pnpm test:simplified

# Or test with manual operations
pnpm test:manual
```

## 🧪 Testing

### Available Test Scripts
- `pnpm test:listener` - Basic real-time listener test
- `pnpm test:simple` - Simple WebSocket connection test
- `pnpm test:manual` - Full CRUD sync test
- `pnpm test:simplified` - Test specifically for simplified setup
- `pnpm test:cdc` - Test CDC functionality

### Example: Testing Real-time Sync
```bash
# Terminal 1: Start the test listener
pnpm test:simplified

# Terminal 2: Create a record
curl -X POST http://localhost:8081/api/foo \
  -H "Content-Type: application/json" \
  -d '{"name": "No Auth Test", "description": "Works without authentication!"}'
```

## 🔍 How It Works

1. **PostgREST** (port 3001) provides REST API without authentication
2. **Real-time server** (port 4002) streams database changes
3. **Sync-base** listens to changes and syncs to Elasticsearch
4. **No authentication** required anywhere in the chain

## 📊 Benefits

- ✅ **Simpler setup** - No JWT configuration needed
- ✅ **Faster development** - No auth errors to debug
- ✅ **Direct access** - PostgreSQL via PostgREST
- ✅ **Same functionality** - Real-time sync still works

## ⚠️ Important Notes

1. **Development Only** - This simplified setup is for development
2. **No Security** - Add authentication for production use
3. **Direct Access** - All database operations are unrestricted

## 🔗 Related Services

- **transactional-base** - Source database (simplified, no auth)
- **retrieval-base** - Target Elasticsearch service
- **analytical-base** - Analytics service using Moose

## 🎯 Next Steps

1. Start all services:
   ```bash
   # Terminal 1
   cd services/transactional-base && pnpm dev
   
   # Terminal 2
   cd services/retrieval-base && pnpm dev
   
   # Terminal 3
   cd services/sync-base && pnpm dev
   ```

2. Test the sync with `pnpm test:manual`
3. Monitor real-time changes with `pnpm test:simplified`

The sync-base service is now properly configured to work with the simplified transactional-base setup! 🎉 