# This is a [MooseJs](https://www.moosejs.com/) project bootstrapped with the [`Moose CLI`](https://github.com/514-labs/moose/tree/main/apps/framework-cli).

<a href="https://www.getmoose.dev/"><img src="https://raw.githubusercontent.com/514-labs/moose/main/logo-m-light.png" alt="moose logo" height="100px"></a>

[![NPM Version](https://img.shields.io/npm/v/%40514labs%2Fmoose-cli?logo=npm)](https://www.npmjs.com/package/@514labs/moose-cli?activeTab=readme)
[![Moose Community](https://img.shields.io/badge/slack-moose_community-purple.svg?logo=slack)](https://join.slack.com/t/moose-community/shared_invite/zt-2fjh5n3wz-cnOmM9Xe9DYAgQrNu8xKxg)
[![Docs](https://img.shields.io/badge/quick_start-docs-blue.svg)](https://docs.moosejs.com/)
[![MIT license](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

[Moose](https://www.getmoose.dev/) is an open-source data engineering framework designed to drastically accellerate AI-enabled software developers, as you prototype and scale data-intensive features and applications.

# Get started with Moose

Get up and running with your own Moose project in minutes by using our [Quick Start Tutorial](https://docs.getmoose.dev/quickstart). We also have our [Docs](https://docs.getmoose.dev/) where you can pick your path, learn more about Moose, and learn what types of applications can be built with Moose.

# Beta release

Moose is beta software and is in active development. Multiple public companies across the globe are using Moose in production. We'd love for you to [get your hands on it and try it out](https://docs.getmoose.dev/quickstart). If you're interested in using Moose in production, or if you just want to chat, you can reach us at [hello@moosejs.dev](mailto:hello@moosejs.dev) or in the Moose developer community below.

# Community

You can join the Moose community [on Slack](https://join.slack.com/t/moose-community/shared_invite/zt-2fjh5n3wz-cnOmM9Xe9DYAgQrNu8xKxg).

Here you can get together with other Moose developers, ask questions, give feedback, make feature requests, and interact directly with Moose maintainers.

# Contributing

We welcome contributions to Moose! Please check out the [contribution guidelines](https://github.com/514-labs/moose/blob/main/CONTRIBUTING.md).

# Made by 514

Our mission at [fiveonefour](https://www.fiveonefour.com/) is to bring incredible developer experiences to the data stack. If you're interested in enterprise solutions, commercial support, or design partnerships, then we'd love to chat with you: [hello@moosejs.dev](mailto:hello@moosejs.dev)

# Sync Base Service

This service provides a Moose workflow for real-time synchronization with the transactional-base database using Supabase realtime subscriptions.

## Overview

The sync-base service implements a long-running Moose workflow that listens to changes in the transactional-base database tables:
- `foo` table
- `bar` table  
- `foo_bar` junction table

## Environment Setup

**Important**: This workflow uses environment variables for configuration, not input parameters.

Create a `.env` file in the sync-base directory with the following configuration:

```bash
# Copy these values from your transactional-base service's .env file

# Supabase Configuration for Sync Service
SUPABASE_PUBLIC_URL=http://localhost:8000

# CRITICAL: Copy this from transactional-base/.env
ANON_KEY=your_actual_anon_key_from_transactional_base

# Optional: Service Role Key (copy from transactional-base/.env)
SERVICE_ROLE_KEY=your_service_role_key_here

# Database Schema (usually 'public')
DB_SCHEMA=public

# Realtime WebSocket URL
REALTIME_URL=ws://localhost:8000/realtime/v1
```

### Getting the Keys

1. **ANON_KEY**: Copy the exact value from `services/transactional-base/.env`
2. **SERVICE_ROLE_KEY**: Copy the exact value from `services/transactional-base/.env`  
3. **SUPABASE_PUBLIC_URL**: Should match your transactional-base service URL

## Running the Workflow

### Prerequisites

1. Ensure the transactional-base service is running
2. Database tables must be set up with realtime enabled
3. Environment variables must be configured in `.env` file

### Start the Workflow

```bash
# Start the Moose development server
pnpm dev

# In another terminal, run the workflow (NO INPUT NEEDED)
moose workflow run supabase-listener
```

**Note**: The workflow now reads configuration from environment variables automatically. No input parameters are required.

### Testing the Workflow

Once running, the workflow will listen for changes on the database tables. You can test by:

1. Creating records in the transactional-base service
2. Updating existing records
3. Deleting records

The workflow will log all changes and execute business logic handlers.

## Workflow Features

- **Environment-based configuration**: All settings from .env file
- **Long-running task**: Runs indefinitely until manually stopped
- **Real-time listening**: Responds to database changes immediately
- **Graceful shutdown**: Properly cleans up subscriptions
- **Business logic handlers**: Separate handlers for each table
- **Comprehensive logging**: Detailed event logging with timestamps
- **No input required**: All configuration from environment variables

## Customization

Add your sync logic in the handler functions:
- `handleFooChange()` - Process foo table changes
- `handleBarChange()` - Process bar table changes  
- `handleFooBarChange()` - Process foo_bar junction table changes

## Architecture

The workflow uses:
- **Environment Variables**: For all configuration (no runtime input)
- **Moose Workflows**: For task orchestration and lifecycle management
- **Supabase Realtime**: For real-time database change notifications
- **PostgreSQL Change Streams**: For capturing database events
- **WebSocket connections**: For real-time communication

## Monitoring

The workflow provides detailed logging for:
- Environment variable validation
- Connection status
- Subscription events
- Database changes
- Business logic execution
- Error conditions

## Troubleshooting

Common issues:
1. **"ANON_KEY environment variable is empty"**: Copy the exact ANON_KEY from transactional-base/.env
2. **Connection errors**: Check SUPABASE_PUBLIC_URL and network connectivity
3. **Authentication errors**: Verify ANON_KEY is correct and matches transactional-base
4. **No events received**: Ensure realtime is enabled on database tables
5. **Subscription failures**: Check database permissions and RLS policies

## Environment Variable Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_PUBLIC_URL` | Yes | URL of your transactional-base service |
| `ANON_KEY` | Yes | Supabase anonymous key from transactional-base |
| `DB_SCHEMA` | Yes | Database schema (usually 'public') |
| `SERVICE_ROLE_KEY` | Optional | Service role key for admin operations |
| `REALTIME_URL` | Optional | WebSocket URL for realtime connections |
