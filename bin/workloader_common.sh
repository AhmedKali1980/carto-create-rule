#!/usr/bin/env bash
set -Eeuo pipefail

WORKLOADER_BIN="${EXECUTABLE:-workloader}"
WORKLOADER_CFG="${CFG:-${EXECUTABLE_CONFIG_FILE:-}}"
PCE_NAME="${PCE_NAME:-}"

run_workloader() {
  local args=("$@")
  local cmd=("${WORKLOADER_BIN}")
  if [[ -n "${WORKLOADER_CFG}" ]]; then
    cmd+=(--cfg "${WORKLOADER_CFG}")
  fi
  if [[ -n "${PCE_NAME}" ]]; then
    cmd+=(--pce "${PCE_NAME}")
  fi
  cmd+=("${args[@]}")
  "${cmd[@]}"
}

retry_backoff() {
  local label="${1:?label required}"
  shift
  if [[ "${1:-}" == "--" ]]; then
    shift
  fi

  local attempt=1
  local max_attempts="${MAX_ATTEMPTS:-${RETRY_MAX_ATTEMPTS:-3}}"
  local base_sleep="${BASE_SLEEP:-${RETRY_BASE_SLEEP:-3}}"
  local backoff_factor="${BACKOFF:-${RETRY_BACKOFF_FACTOR:-2}}"
  local max_sleep="${MAX_SLEEP:-${RETRY_MAX_SLEEP:-60}}"
  local jitter_pct="${JITTER:-${RETRY_JITTER_PCT:-20}}"
  local timeout_sec="${TIMEOUT_SEC:-}"

  while (( attempt <= max_attempts )); do
    echo "[INFO] ${label}: attempt ${attempt}/${max_attempts}"
    if command -v timeout >/dev/null 2>&1 && [[ -n "${timeout_sec}" ]]; then
      if timeout "${timeout_sec}"s run_workloader "$@"; then
        return 0
      fi
    else
      if run_workloader "$@"; then
        return 0
      fi
    fi

    local sleep_s
    sleep_s=$(awk -v base="${base_sleep}" -v factor="${backoff_factor}" -v n="${attempt}" 'BEGIN {printf "%.0f", base * (factor ** (n-1))}')
    if (( sleep_s > max_sleep )); then
      sleep_s=${max_sleep}
    fi

    if (( jitter_pct > 0 )); then
      local jitter
      jitter=$(awk -v pct="${jitter_pct}" -v s="${sleep_s}" 'BEGIN {printf "%.0f", (rand()*2-1) * s * pct / 100}')
      sleep_s=$(( sleep_s + jitter ))
      if (( sleep_s < 1 )); then
        sleep_s=1
      fi
    fi

    echo "[WARN] ${label}: retrying in ${sleep_s}s"
    sleep "${sleep_s}"
    attempt=$(( attempt + 1 ))
  done

  echo "[ERROR] ${label}: failed after ${max_attempts} attempts" >&2
  return 1
}
