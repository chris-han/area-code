# BIA Deployment Notes

The Billing Intelligence API (BIA) now runs as an independent FastAPI application under `bia_backend/`, so Moose availability no longer affects the REST surface.

## Key Points

- `bia_backend/app.py` initializes ClickHouse, Temporal, Redis, and plugin dependencies. Failures in one service are logged and do not block startup of the others.
- Moose is **not** required to serve the BIA endpoints. Moose-specific features continue to run through `app/main.py` and Moose CLI commands.
- The legacy Moose status endpoints (`/api/v1/moose/status`, etc.) can be reintroduced inside `bia_backend` if needed, but the default behaviour is simply to expose health information about the BIA stack.

## Recommended Deployment

```bash
# Run BIA only
uvicorn bia_backend.main:app --host 0.0.0.0 --port 4300

# Or via helper script
../../../bia_admin/scripts/bia-api.sh
```

Moose ingestion/consumption endpoints remain available through `moose dev` (port 4200) and are unaffected by the BIA process.
