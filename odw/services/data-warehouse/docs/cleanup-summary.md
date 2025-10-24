# Cleanup Summary (Moose vs BIA separation)

## Scope

- `app/main.py` – trimmed to Moose-only responsibilities.
- `bia_backend/app.py` – new home for dependency management and router registration.
- `bia_backend/routers/*` – relocated general FastAPI routers.
- Scripts updated to launch the new BIA backend.

## Highlights

### app/main.py
- Provides a bare FastAPI instance for Moose tooling.
- Keeps the import side effects that register Moose ingestion/consumption APIs.
- No longer mounts bia routers or mixes lifecycle logic.

### bia_backend/app.py
- Hosts the `ABIApplication` class, dependency initialization, and FastAPI factory.
- Mounts all routers from `bia_backend/routers/`.
- Exposes `abi_fastapi_app`/`bia_fastapi_app` for consumers and compatibility.

### Routers
- Moved from `app/bia/routers` to `bia_backend/routers`.
- Imports updated to use `bia_backend.app` for dependencies.

### Scripts
- `../../../bia_admin/scripts/bia-api.sh`, `scripts/run-bia-standalone.sh`, and `scripts/bia-dev.sh` now point to `bia_backend.main:app` (port 4300).

## Follow-up Checks

1. `python -m compileall bia_backend app/main.py`
2. `../../../bia_admin/scripts/bia-api.sh` → check `http://localhost:4300/api/v1/health/ping`
3. `moose dev` → verify `/consumption/*` endpoints
