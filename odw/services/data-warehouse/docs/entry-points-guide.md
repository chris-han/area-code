# Entry Point Guide

## Quick Reference

| Use Case | Entry Point | Command | Default Port |
|----------|-------------|---------|--------------|
| Moose CLI / ingestion & consumption APIs | `app/main.py` | `moose dev` | 4200 |
| Billing Intelligence API (BIA) | `bia_backend/main.py` | `uvicorn bia_backend.main:app --reload --port 4300` | 4300 |
| Combined dev stack | scripts | `./scripts/abi-dev.sh` | 4200 & 4300 |

## 1. Moose Runtime (`app/main.py`)

- **Purpose:** Registers Moose models, ingestion pipelines, workflows, materialized views, and Moose `ConsumptionApi` endpoints (including the ABI analytics APIs implemented inside Moose).
- **Characteristics:** Bare FastAPI instance—Moose injects routes automatically. Required by the Moose CLI (file name cannot change).
- **Typical commands:**
  ```bash
  moose dev
  moose build
  ```
- **When to use:** Any Moose CLI workflow, ingestion testing, or data pipeline debugging.

## 2. Billing Intelligence API (`bia_backend/main.py`)

- **Purpose:** Hosts the general FastAPI surface (health, billing analytics, workflow management, plugin management, storage, etc.).
- **Ports:** Defaults to **4300** via scripts.
- **Typical commands:**
  ```bash
  uvicorn bia_backend.main:app --reload --port 4300
  ./scripts/abi-api.sh             # wrapper with virtualenv detection
  ./scripts/abi-dev.sh             # runs Moose + BIA together
  ```
- **When to use:** Serving REST endpoints to frontends or external consumers, local feature development on BIA routes, readiness/health probes.

## Why Two Entry Points?

- The Moose CLI is hard-coded to load `app/main.py`, so we keep Moose-specific registration there.
- BIA routes are pure FastAPI and do not require Moose; they now live in `bia_backend/` to avoid loading Moose when unnecessary.

## Common Scenarios

### Local Moose Development
```bash
moose dev
# Visit http://localhost:4200 for Moose-managed routes
```

### Local BIA Development
```bash
./scripts/abi-api.sh
# Visit http://localhost:4300/api/v1/health/ping
```

### Combined Stack
```bash
./scripts/abi-dev.sh
# Moose → 4200, BIA → 4300
```

### Production-style BIA Deployment
```bash
gunicorn bia_backend.main:app \
    --bind 0.0.0.0:4300 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker
```

## Checklist When Adding New Endpoints

1. **Moose `ConsumptionApi`?** → Keep it under `app/` so Moose can load it.
2. **General FastAPI route?** → Create it under `bia_backend/` and register it via the appropriate router.
3. **Update scripts/docs** if new ports or commands are required.
