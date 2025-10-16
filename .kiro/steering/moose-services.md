---
inclusion: manual
---
# Moose Services Rules

These rules apply to Moose-based services in the `services/` directory (analytical-base and sync-base).

## Workflow Testing Guidelines

When testing workflows in these services:

- **Always use the command:** `moose workflow run <workflow-name>` to test if a workflow is running correctly
- **Assume the Moose instance is already running** - no need to start it separately. Inspect the existing terminal
- **Code changes will hot reload automatically** - any modifications to the Moose code will be picked up by the running server without manual restart

## Development Workflow

1. Make changes to your workflow code
2. Save the file (hot reload will handle the rest)
3. Test using: `moose workflow run <workflow-name>`
4. Check logs and output to verify behavior

## Example Usage

```bash
# Testing a specific workflow
moose workflow run eventsPipeline

# The Moose instance will already be running, so this command
# will execute against the current running instance
```

## Port Configuration Rules

**CRITICAL: Always use the configured ports, never fallback to alternative ports**

- **Port 4200**: Main Moose HTTP server (consumption APIs)
- **Port 4201**: Proxy port (internal use only)
- **If port 4200 is not available**: Issue a warning and investigate the problem
- **NEVER automatically switch to port 4201** - this breaks the expected API contract
- **Frontend constants should always point to port 4200** with `/consumption` path

### API Endpoint Format
```
CONSUMPTION_API_BASE = "http://localhost:4200/consumption"
WORKFLOW_API_BASE = "http://localhost:4200/consumption"  
INGEST_API_BASE = "http://localhost:4200/ingest"
```

### Troubleshooting Port Issues
1. Check if moose service is running: `lsof -i :4200`
2. If not running, restart the moose service
3. If running but not responding, check moose logs
4. **Do NOT change port configuration as a workaround**

## Important Notes

- Do not restart the Moose server unnecessarily - it supports hot reload
- Focus on the workflow logic rather than server management
- Use the workflow run command for quick iteration and testing
- **Always verify port 4200 is working before suggesting alternatives** 