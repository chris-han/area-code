# Architecture Update Summary

## Overview

The service now distinguishes between:

- **Moose runtime** (`app/main.py`): registers ingestion pipelines, workflows, materialized views, and Moose-managed `ConsumptionApi` endpoints (including the bia analytics definitions). No general FastAPI routers are mounted here.
- **Billing Intelligence API (BIA) backend** (`bia_backend/main.py`): standalone FastAPI surface exposing REST endpoints (health, billing analytics, workflow management, plugins, storage, etc.) on port **4300**.

## Key Changes

| Area | Old State | New State |
|------|-----------|-----------|
| FastAPI entry point | `app.abi_app:abi_fastapi_app` | `bia_backend.main:app` |
| Moose entry point | `app/main.py` (Moose + bia) | `app/main.py` (Moose only) |
| Router location | `app/bia/routers/*` | `bia_backend/routers/*` |
| Scripts | Targeted `app.abi_app` | Target `bia_backend.main:app` |

## Files of Interest

- `app/main.py` – Moose CLI entry point (unchanged interface, now a bare FastAPI shell).
- `bia_backend/app.py` – Dependency loader and router registration for BIA.
- `bia_backend/main.py` – BIA FastAPI entry point.
- `../../../bia_admin/scripts/bia-api.sh`, `scripts/run-bia-standalone.sh`, `scripts/bia-dev.sh` – Updated to launch the new module.

## Launch Scenarios

```bash
# Moose stack only (ingest/consumption APIs via Moose CLI)
moose dev

# BIA backend at http://localhost:4300
../../../bia_admin/scripts/bia-api.sh
# or
uvicorn bia_backend.main:app --reload --port 4300

# Combined dev stack (Moose + BIA)
./scripts/bia-dev.sh
```

## Migration Notes

- Any tooling or documentation that referenced `app.abi_app:abi_fastapi_app` should now use `bia_backend.main:app`.
- Moose-specific automation continues to rely on `app/main.py`; no consumer changes required.
- bia business logic that must run inside Moose (e.g., `ConsumptionApi` definitions) still resides in `app/bia/`.

## Validation Checklist

- [x] `python -m compileall bia_backend app/main.py`
- [ ] `../../../bia_admin/scripts/bia-api.sh` → health endpoints respond on port 4300
- [ ] `moose dev` → Moose `/consumption/*` endpoints remain available
