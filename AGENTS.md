# Repository Guidelines

## Project Structure & Module Organization
Area Code is a turborepo-managed monorepo. `ufa/` hosts the user-facing analytics stack (React app in `apps/`, Fastify and worker services under `services/`, shared libraries in `packages/`). `odw/` contains the Moose data warehouse (`services/data-warehouse`) and Streamlit dashboards in `apps/`. `ufa-lite/` mirrors UFA for lightweight demos. `bia_admin/` bundles the admin Python API and React console. Shared docs and utilities live in `docs/`, `scripts/`, and `FOCUS_Spec/`.

## Build, Test, and Development Commands
Install dependencies with `bun install` (Bun ≥1.2, Node ≥18). `bun run ufa:dev` or `bun run ufa-lite:dev` spin up the analytics stack; ensure Docker is running for Temporal, ClickHouse, and related services. `bun run odw:dev` starts the warehouse, with `bun run odw:dev:seed` to load fixtures. Admin tooling comes up with `bun run bia:dev`. Use `turbo run lint` before pushing; root Python scripts under `scripts/` aid workflow debugging.

## Coding Style & Naming Conventions
TypeScript and React code follows the shared config in `ufa/packages/eslint-config`: two-space indentation, semicolons, camelCase utilities, PascalCase components, and consistent Tailwind ordering. Auto-format with Prettier or `bunx prettier --write`. Backend Python in `odw/services/data-warehouse` and `bia_admin/bia_backend` uses Black (100-character lines), Ruff, and strict type hints; prefer snake_case modules and descriptive test names.

## Testing Guidelines
Backend tests rely on `pytest`. From `odw/services/data-warehouse`, run `python -m pytest -m "not integration"` for fast suites and toggle marks such as `integration`, `focus`, or `slow` as needed. Document skips when external services (Temporal, ClickHouse, S3) are unavailable. Frontend changes should include component-level checks and, where applicable, update Playwright or Storybook coverage within the target app.

## Commit & Pull Request Guidelines
Commit messages should mirror existing Conventional Commit usage (`feat(focus-billing): ...`, `fix(worker): ...`) with imperative subjects under roughly 72 characters. Keep commits scoped so Turborepo caching stays effective. Pull requests need a concise summary, linked issues, screenshots or CLI captures for visible changes, and a checklist of commands run (`turbo run lint`, relevant `pytest` markers). Flag any new environment variables or infrastructure steps.

# Agent Notes

- Never hardcode IP addresses in the codebase; always read host values from `odw/services/data-warehouse/moose.config.toml` or the appropriate configuration source.