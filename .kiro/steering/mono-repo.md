---
inclusion: always
---
NEVER USE NPM. ALWAYS USE PNPM.

DON'T EVER OVERRIDE THE .ENV FILE.

This is a mono repo. It leverages turbo repo.

If you need information refer to the official turborepo docs with the latest version: https://turborepo.com/docs

The mono repo is composed of three high level concepts:
1. Apps: core user facing functionality
2. Services: shared capabilities and infrastructure across apps
3. Packages: shared functionality across apps (like configs or component/design systems)

Some hygiene rules you should follow:
* Prefix package names for packages and services with @workspace


Until Moose Node Versions Issues are fixed in Moose you must use Node 20