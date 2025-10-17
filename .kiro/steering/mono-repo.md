---
inclusion: always
---

NEVER USE NPM. ALWAYS USE BUN.
NEVER USE PIP directly. ALWAYS USE UV.
DON'T EVER OVERRIDE THE .ENV FILE.

This is a mono repo. It leverages turbo repo.

If you need information refer to the official turborepo docs with the latest version: https://turborepo.com/docs

The mono repo is composed of three high level concepts:

1. Apps: core user facing functionality
2. Services: shared capabilities and infrastructure across apps
3. Packages: shared functionality across apps (like configs or component/design systems)

Some hygiene rules you should follow:

- Prefix package names for packages and services with @workspace

Until Moose Node Versions Issues are fixed in Moose you must use Node 20
## Docker Port Configuration

NEVER allow Docker to auto-assign ports when there are conflicts. Always use fixed port numbers in Docker Compose configurations. If there's a port conflict, it should raise an error for investigation rather than silently using a different port.

This prevents:
- Silent port conflicts that are hard to debug
- Services running on unexpected ports
- Configuration drift between environments
- Hard-to-trace connectivity issues

Always explicitly set ports in docker-compose.yml without fallback auto-assignment.