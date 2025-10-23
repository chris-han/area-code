#!/usr/bin/env bash
#
# Terminates the ABI dev processes and frees their ports (3003 + 4300).

set -euo pipefail

SCRIPT_NAME="$(basename "$0")"
SELF_PID="$$"
PARENT_PID="${PPID:-}"
SKIP_PATTERN_KILL="${ABI_SKIP_PATTERN_KILL:-0}"

kill_process_group() {
  local pid="$1"
  local reason="$2"

  if ! kill -0 "$pid" 2>/dev/null; then
    return
  fi

  local pgid
  pgid="$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ')"

  if [[ -n "${pgid}" ]]; then
    echo "[${SCRIPT_NAME}] Sending SIGTERM to process group -${pgid} (${reason})"
    kill -- "-${pgid}" 2>/dev/null || true
    sleep 1

    if kill -0 "$pid" 2>/dev/null; then
      echo "[${SCRIPT_NAME}] Escalating to SIGKILL for process group -${pgid}"
      kill -9 -- "-${pgid}" 2>/dev/null || true
      sleep 0.3
    fi
  else
    echo "[${SCRIPT_NAME}] PGID unavailable for PID ${pid}; issuing direct signals"
    kill "$pid" 2>/dev/null || true
    sleep 1
    kill -9 "$pid" 2>/dev/null || true
  fi
}

terminate_port() {
  local port="$1"
  local attempts=0

  while true; do
    mapfile -t pids < <(lsof -t -iTCP:"${port}" 2>/dev/null | sort -u)
    if [[ "${#pids[@]}" -eq 0 ]]; then
      echo "[${SCRIPT_NAME}] Port ${port} is free"
      return 0
    fi

    ((attempts++))
    echo "[${SCRIPT_NAME}] Port ${port} occupied by PID(s): ${pids[*]} (attempt ${attempts})"

    for pid in "${pids[@]}"; do
      [[ -n "${pid}" ]] || continue
      kill_process_group "${pid}" "port ${port}"
    done

    if (( attempts >= 3 )); then
      break
    fi

    sleep 0.5
  done

  mapfile -t final_pids < <(lsof -t -iTCP:"${port}" 2>/dev/null | sort -u)
  if [[ "${#final_pids[@]}" -eq 0 ]]; then
    echo "[${SCRIPT_NAME}] Port ${port} cleared after retries"
    return 0
  fi

  echo "[${SCRIPT_NAME}] WARNING: Unable to free port ${port}. Remaining PID(s): ${final_pids[*]}"
  return 1
}

declare -a ports=("3003" "4300")
port_errors=0
for port in "${ports[@]}"; do
  if ! terminate_port "${port}"; then
    ((port_errors++))
  fi
done

# Also stop known ABI dev launchers so Turbo can't immediately respawn them.
declare -a patterns=(
  "bun run abi:dev"
  "turbo run abi:dev"
  "next dev --port 3003"
  "node .*next.* dev --port 3003"
  "uvicorn bia_backend.main:app"
  "odw/services/data-warehouse/scripts/abi-api.sh"
  "abi-dev.sh"
)

if [[ "${SKIP_PATTERN_KILL}" != "1" ]]; then
  for pattern in "${patterns[@]}"; do
    mapfile -t match_pids < <(pgrep -f "${pattern}" 2>/dev/null || true)
    if [[ "${#match_pids[@]}" -eq 0 ]]; then
      continue
    fi

    unique_pids=($(printf "%s\n" "${match_pids[@]}" | sort -u))
    echo "[${SCRIPT_NAME}] Pattern '${pattern}' matched PID(s): ${unique_pids[*]}"
    for pid in "${unique_pids[@]}"; do
      if [[ "${pid}" == "${SELF_PID}" ]]; then
        continue
      fi
      if [[ -n "${PARENT_PID}" && "${pid}" == "${PARENT_PID}" ]]; then
        continue
      fi
      kill_process_group "${pid}" "pattern '${pattern}'"
    done
  done
else
  echo "[${SCRIPT_NAME}] Skipping pattern-based process termination"
fi

if (( port_errors > 0 )); then
  echo "[${SCRIPT_NAME}] Completed with warnings (${port_errors} port(s) still busy)."
  exit 1
fi
