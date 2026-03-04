#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONF_FILE="${GLOBAL_CONF_PATH:-${ROOT_DIR}/conf/global.conf}"

if [[ ! -f "${CONF_FILE}" ]]; then
  echo "ERROR: global config not found at ${CONF_FILE}" >&2
  exit 2
fi

# shellcheck disable=SC1090
source "${CONF_FILE}"

: "${EXECUTABLE:?Missing EXECUTABLE in global.conf}"
: "${EXECUTABLE_CONFIG_FILE:?Missing EXECUTABLE_CONFIG_FILE in global.conf}"

RETRY_MAX_ATTEMPTS="${RETRY_MAX_ATTEMPTS:-3}"
RETRY_BASE_SLEEP="${RETRY_BASE_SLEEP:-3}"
RETRY_BACKOFF_FACTOR="${RETRY_BACKOFF_FACTOR:-2}"
RETRY_MAX_SLEEP="${RETRY_MAX_SLEEP:-60}"
RETRY_JITTER_PCT="${RETRY_JITTER_PCT:-20}"
TIMEOUT_SEC="${TIMEOUT_SEC:-2700}"

run_workloader() {
  local args=("$@")
  local base=("${EXECUTABLE}" --config "${EXECUTABLE_CONFIG_FILE}")
  if [[ -n "${PCE_NAME:-}" ]]; then
    base+=(--pce "${PCE_NAME}")
  fi
  if command -v timeout >/dev/null 2>&1; then
    timeout "${TIMEOUT_SEC}" "${base[@]}" "${args[@]}"
  else
    "${base[@]}" "${args[@]}"
  fi
}

retry_backoff() {
  local name="$1"; shift
  local attempt=1
  while (( attempt <= RETRY_MAX_ATTEMPTS )); do
    echo "[$(date '+%F %T')] ${name}: attempt ${attempt}/${RETRY_MAX_ATTEMPTS}" >&2
    if run_workloader "$@"; then
      return 0
    fi

    local rc=$?
    if (( attempt == RETRY_MAX_ATTEMPTS )); then
      echo "[$(date '+%F %T')] ${name}: failed with rc=${rc}" >&2
      return "${rc}"
    fi

    local wait=$(( RETRY_BASE_SLEEP * (RETRY_BACKOFF_FACTOR ** (attempt - 1)) ))
    if (( wait > RETRY_MAX_SLEEP )); then
      wait=${RETRY_MAX_SLEEP}
    fi

    local jitter=$(( (wait * RETRY_JITTER_PCT) / 100 ))
    local extra=0
    if (( jitter > 0 )); then
      extra=$(( RANDOM % (jitter + 1) ))
    fi
    sleep $((wait + extra))
    ((attempt++))
  done
}
