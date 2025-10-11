#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATE_FILE="$SERVICE_DIR/moose.config.template.toml"
OUTPUT_FILE="$SERVICE_DIR/moose.config.toml"
ENV_FILE="$SERVICE_DIR/.env"

if [[ ! -f "$TEMPLATE_FILE" ]]; then
    echo "[render-config] Template not found: $TEMPLATE_FILE" >&2
    exit 1
fi

ensure_envsubst() {
    if command -v envsubst >/dev/null 2>&1; then
        return
    fi

    if command -v apt-get >/dev/null 2>&1; then
        echo "[render-config] 'envsubst' not found. Attempting to install via 'sudo apt-get install -y gettext-base'..."
        if sudo apt-get install -y gettext-base >/dev/null; then
            return
        fi
        echo "[render-config] Automatic installation failed. Please install gettext-base manually." >&2
    else
        echo "[render-config] 'envsubst' is required but not found. Install gettext-base (GNU gettext) and retry." >&2
    fi

    exit 1
}

ensure_envsubst

if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

# Default values
: "${MOOSE_CLICKHOUSE_DB_NAME:=dbo}"
: "${MOOSE_CLICKHOUSE_USER:=finops}"
: "${MOOSE_CLICKHOUSE_PASSWORD:=cU2f947&9T{6d}"
: "${MOOSE_CLICKHOUSE_USE_SSL:=true}"
: "${MOOSE_CLICKHOUSE_HOST:=ck.mightytech.cn}"
: "${MOOSE_CLICKHOUSE_HOST_PORT:=8443}"
: "${MOOSE_CLICKHOUSE_NATIVE_PORT:=8443}"

: "${MOOSE_TEMPORAL_DB_USER:=temporal}"
: "${MOOSE_TEMPORAL_DB_PASSWORD:=temporal}"
: "${MOOSE_TEMPORAL_DB_PORT:=5432}"
: "${MOOSE_TEMPORAL_HOST:=localhost}"
: "${MOOSE_TEMPORAL_PORT:=7233}"

: "${TEMPORAL_DB_HOST:=postgresql}"
: "${TEMPORAL_DB_PORT:=5432}"
: "${TEMPORAL_HOST:=temporal}"
: "${TEMPORAL_PORT:=7233}"

: "${MOOSE_S3_ENDPOINT_URL:=}"
: "${MOOSE_S3_ACCESS_KEY_ID:=}"
: "${MOOSE_S3_SECRET_ACCESS_KEY:=}"
: "${MOOSE_S3_REGION_NAME:=us-east-2}"
: "${MOOSE_S3_BUCKET_NAME:=yl-billing-data}"
: "${MOOSE_S3_SIGNATURE_VERSION:=s3v4}"

# Normalise boolean/string casing
MOOSE_CLICKHOUSE_USE_SSL=$(echo "$MOOSE_CLICKHOUSE_USE_SSL" | tr '[:upper:]' '[:lower:]')

VARS=(
    MOOSE_CLICKHOUSE_DB_NAME
    MOOSE_CLICKHOUSE_USER
    MOOSE_CLICKHOUSE_PASSWORD
    MOOSE_CLICKHOUSE_USE_SSL
    MOOSE_CLICKHOUSE_HOST
    MOOSE_CLICKHOUSE_HOST_PORT
    MOOSE_CLICKHOUSE_NATIVE_PORT
    MOOSE_TEMPORAL_DB_USER
    MOOSE_TEMPORAL_DB_PASSWORD
    MOOSE_TEMPORAL_DB_PORT
    MOOSE_TEMPORAL_HOST
    MOOSE_TEMPORAL_PORT
    TEMPORAL_DB_HOST
    TEMPORAL_DB_PORT
    TEMPORAL_HOST
    TEMPORAL_PORT
    MOOSE_S3_ENDPOINT_URL
    MOOSE_S3_ACCESS_KEY_ID
    MOOSE_S3_SECRET_ACCESS_KEY
    MOOSE_S3_REGION_NAME
    MOOSE_S3_BUCKET_NAME
    MOOSE_S3_SIGNATURE_VERSION
)

export "${VARS[@]}"

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

PATTERN="$(printf ' ${%s}' "${VARS[@]}")"
envsubst "$PATTERN" < "$TEMPLATE_FILE" > "$TMP_FILE"

if [[ ! -f "$OUTPUT_FILE" ]] || ! cmp -s "$TMP_FILE" "$OUTPUT_FILE"; then
    mv "$TMP_FILE" "$OUTPUT_FILE"
else
    rm -f "$TMP_FILE"
fi

echo "[render-config] Generated $OUTPUT_FILE from template"
