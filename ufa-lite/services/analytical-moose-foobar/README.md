# Analytical Backend

A MooseStack-powered analytical service that provides consumption APIs for Foo and Bar analytics with ClickHouse integration.

## Available Scripts

```bash
bun run ufa-lite:devx ## start the analytical service
bun run seed-foo ## copy data from remote ClickHouse to local foo table
bun run seed-bar ## copy data from remote ClickHouse to local bar table
bun run generate-sdk ## Runs the Kubb CLI to generate the SDK for the analytical service
```
