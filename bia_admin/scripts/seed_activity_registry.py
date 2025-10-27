#!/usr/bin/env python3
"""
Seed dynamic activity registry entries inside the plugin_registry database.

The script ensures the required metadata columns exist on
plugin_registry.plugin_configurations and performs idempotent upserts for the
activity definitions needed by the dynamic dispatcher.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

import psycopg2
import psycopg2.extras
import tomli


REPO_ROOT = Path(__file__).resolve().parents[2]
MOOSE_CONFIG_PATH = REPO_ROOT / "odw" / "services" / "data-warehouse" / "moose.config.toml"


@dataclass(frozen=True)
class ActivityDefinition:
    activity_name: str
    module: str
    qualname: str
    version: int = 1
    description: str | None = None

    @property
    def plugin_name(self) -> str:
        return f"activity.{self.activity_name}"


ACTIVITIES: Iterable[ActivityDefinition] = [
    ActivityDefinition(
        activity_name="execute_clickhouse_schema",
        module="bia_admin.bia_backend.workflows.focus_billing.schema_migration.activities",
        qualname="_execute_clickhouse_schema",
        description="Execute ClickHouse DDL generated from Parquet schema artifacts.",
    ),
]


def load_db_config() -> Mapping[str, str]:
    if not MOOSE_CONFIG_PATH.exists():
        raise SystemExit(f"Unable to locate moose.config.toml at {MOOSE_CONFIG_PATH}")
    with MOOSE_CONFIG_PATH.open("rb") as fh:
        cfg = tomli.load(fh)
    pg_cfg = cfg.get("plugin_registry_db")
    if not pg_cfg:
        raise SystemExit("plugin_registry_db section missing from moose.config.toml")
    return {
        "host": pg_cfg.get("host", "localhost"),
        "port": pg_cfg.get("port", 5432),
        "database": pg_cfg.get("database", "bia_config"),
        "user": pg_cfg.get("user", "temporal"),
        "password": pg_cfg.get("password", "temporal"),
    }


def ensure_columns(cur: psycopg2.extensions.cursor) -> None:
    cur.execute(
        """
        ALTER TABLE plugin_registry.plugin_configurations
        ADD COLUMN IF NOT EXISTS logic_module TEXT
        """
    )
    cur.execute(
        """
        ALTER TABLE plugin_registry.plugin_configurations
        ADD COLUMN IF NOT EXISTS logic_qualname TEXT
        """
    )
    cur.execute(
        """
        ALTER TABLE plugin_registry.plugin_configurations
        ADD COLUMN IF NOT EXISTS logic_activity TEXT
        """
    )
    cur.execute(
        """
        ALTER TABLE plugin_registry.plugin_configurations
        ADD COLUMN IF NOT EXISTS logic_version INTEGER DEFAULT 1
        """
    )


def upsert_activity(cur: psycopg2.extensions.cursor, activity: ActivityDefinition) -> None:
    configuration = {
        "logic_module": activity.module,
        "logic_qualname": activity.qualname,
        "logic_activity": activity.activity_name,
        "logic_version": activity.version,
        "description": activity.description,
    }
    payload = {
        "plugin_name": activity.plugin_name,
        "configuration": psycopg2.extras.Json(configuration),
        "logic_module": activity.module,
        "logic_qualname": activity.qualname,
        "logic_activity": activity.activity_name,
        "logic_version": activity.version,
        "updated_by": "activity-seed-script",
    }

    cur.execute(
        """
        SELECT id
        FROM plugin_registry.plugin_configurations
        WHERE plugin_name = %(plugin_name)s
        ORDER BY updated_at DESC NULLS LAST
        LIMIT 1
        """,
        payload,
    )
    row = cur.fetchone()

    if row:
        cur.execute(
            """
            UPDATE plugin_registry.plugin_configurations
            SET configuration = %(configuration)s,
                logic_module = %(logic_module)s,
                logic_qualname = %(logic_qualname)s,
                logic_activity = %(logic_activity)s,
                logic_version = %(logic_version)s,
                is_active = TRUE,
                updated_at = NOW(),
                updated_by = %(updated_by)s
            WHERE id = %(id)s
            """,
            {**payload, "id": row[0]},
        )
    else:
        cur.execute(
            """
            INSERT INTO plugin_registry.plugin_configurations (
                plugin_name,
                configuration,
                logic_module,
                logic_qualname,
                logic_activity,
                logic_version,
                is_active,
                updated_by
            ) VALUES (
                %(plugin_name)s,
                %(configuration)s,
                %(logic_module)s,
                %(logic_qualname)s,
                %(logic_activity)s,
                %(logic_version)s,
                TRUE,
                %(updated_by)s
            )
            """,
            payload,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed dynamic activity metadata into plugin_registry."
    )
    parser.parse_args()

    db_cfg = load_db_config()
    with psycopg2.connect(**db_cfg) as conn, conn.cursor() as cur:
        ensure_columns(cur)
        for activity in ACTIVITIES:
            upsert_activity(cur, activity)
        conn.commit()

    print("✔ Seeded activity registry entries:", ", ".join(a.activity_name for a in ACTIVITIES))


if __name__ == "__main__":
    try:
        main()
    except psycopg2.Error as exc:  # pragma: no cover - connection failures
        print(f"Database error: {exc}", file=sys.stderr)
        sys.exit(1)
