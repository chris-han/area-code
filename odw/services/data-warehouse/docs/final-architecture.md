# Final Architecture After BIA Separation

## Overview

The data-warehouse service now exposes two complementary FastAPI applications:

- `app/main.py` → Moose-managed surface that only registers ingestion pipelines, workflows, materialized views, and Moose `ConsumptionApi` endpoints. This remains the entry point the Moose CLI expects.
- `bia_backend/main.py` → Billing Intelligence API (BIA) FastAPI application served on port **4300**, providing the general-purpose REST endpoints (health, billing analytics, workflow management, etc.).

This separation keeps the Moose runtime focused on Moose-native contracts while allowing the BIA surface to evolve independently.

## Directory Layout

```
app/
├── main.py                # Moose CLI entry point (Moose-only FastAPI shell)
├── abi/                   # ABI analytics registered as Moose Consumption APIs
├── moose_apis/            # Moose ingestion & consumption endpoints
└── …

bia_backend/
├── app.py                 # Dependency management + router registration
├── main.py                # FastAPI entry point served on port 4300
├── budget_tracking.py     # Non-Moose FastAPI handlers
└── routers/               # BIA FastAPI routers (billing, health, plugins, …)
```

## Entry Points

| Use Case                       | Command/Module                                | Port |
|--------------------------------|-----------------------------------------------|------|
| Moose CLI (ingest/consume)     | `moose dev` → `app/main.py`                   | 4200 |
| Run BIA-only HTTP API          | `uvicorn bia_backend.main:app --port 4300`    | 4300 |
| Dev helper script              | `./scripts/abi-api.sh`                        | 4300 |
| Combined Moose + BIA dev stack | `./scripts/abi-dev.sh`                        | 4200 + 4300 |

> Note: `./scripts/run-abi-standalone.sh` now targets `bia_backend.main:app` as well.

## Moose Surface (`app/main.py`)

- Provides a bare FastAPI instance—no general routers mounted.
- Moose automatically wires `/ingest/*` and `/consumption/*` routes based on the registered pipelines and `ConsumptionApi` definitions (including the ABI analytics APIs under `app/abi/`).
- Safe to import in any Moose tooling or CLI flows.

## BIA Backend (`bia_backend/app.py`)

- Handles dependency initialization (ClickHouse, Temporal, Redis, plugin registry/manager).
- Mounts routers from `bia_backend/routers/` for:
  - Billing analytics
  - Workflow management
  - Plugin management
  - FOCUS data & budget tracking
  - Health/readiness probes
  - Storage management
- Exposes documentation under `/docs` and `/redoc` on port 4300.

## Updated Scripts

| Script                                    | Purpose                                      | Target |
|-------------------------------------------|----------------------------------------------|--------|
| `scripts/abi-api.sh`                      | Run only the BIA FastAPI app                 | `bia_backend.main:app`
| `scripts/run-abi-standalone.sh`           | Manual launch of the BIA FastAPI app        | `bia_backend.main:app`
| `scripts/abi-dev.sh`                      | Concurrent Moose stack + BIA backend dev     | `app/main.py` + `bia_backend/main.py`

## Verification Tips

1. **Moose APIs** – Execute `moose dev` and confirm `/consumption/*` endpoints continue to resolve (via Moose CLI or curl).
2. **BIA Backend** – Run `./scripts/abi-api.sh` and hit `http://localhost:4300/api/v1/health/ping`.
3. **Import checks** – `python -m compileall bia_backend app/main.py` ensures the new modules compile.

## Why This Matters

- **Clear Separation**: Moose-managed APIs live under Moose tooling; FastAPI routes that don’t need Moose are isolated in their own app.
- **Operational Flexibility**: You can deploy/scale the BIA backend separately while keeping Moose ingestion pipelines intact.
- **Future Extensibility**: New FastAPI features or middlewares can be added to `bia_backend` without affecting Moose internals.
