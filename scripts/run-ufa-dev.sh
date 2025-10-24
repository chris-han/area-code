#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REQUIRED_NODE_MAJOR=20
REQUIRED_NODE_RANGE="20"

ensure_nvm() {
    # shellcheck disable=SC1090
    if [[ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]]; then
        # shellcheck disable=SC1090
        source "${NVM_DIR:-$HOME/.nvm}/nvm.sh"
        return 0
    fi
    return 1
}

current_node_major() {
    local version
    if ! version="$(node -v 2>/dev/null)"; then
        echo ""
        return
    fi
    version="${version#v}"
    echo "${version%%.*}"
}

if ensure_nvm; then
    if ! nvm use "${REQUIRED_NODE_RANGE}" >/dev/null 2>&1; then
        echo "Node ${REQUIRED_NODE_RANGE}.x not installed via nvm; installing..." >&2
        nvm install "${REQUIRED_NODE_RANGE}"
        nvm use "${REQUIRED_NODE_RANGE}" >/dev/null
    fi
else
    current_major="$(current_node_major)"
    if [[ -z "${current_major}" || "${current_major}" != "${REQUIRED_NODE_MAJOR}" ]]; then
        echo "Node ${REQUIRED_NODE_MAJOR}.x is required but nvm is not available to install it automatically." >&2
        echo "Please install nvm or switch to Node ${REQUIRED_NODE_MAJOR}.x manually." >&2
        exit 1
    fi
fi

# Re-check version after nvm adjustments.
active_major="$(current_node_major)"
if [[ "${active_major}" != "${REQUIRED_NODE_MAJOR}" ]]; then
    echo "Failed to activate Node ${REQUIRED_NODE_MAJOR}.x (current: ${active_major:-unknown})." >&2
    exit 1
fi

export NODE_ENV="${NODE_ENV:-development}"
export PATH="${REPO_ROOT}/node_modules/.bin:${PATH}"

TURBO_BIN="${REPO_ROOT}/node_modules/.bin/turbo"
if [[ ! -x "${TURBO_BIN}" ]]; then
    echo "Turbo CLI not found at ${TURBO_BIN}. Run 'bun install' before starting ufa:dev." >&2
    exit 1
fi

exec "${TURBO_BIN}" run ufa:dev --ui=tui
