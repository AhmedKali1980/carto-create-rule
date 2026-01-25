#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# workloader_common.sh
# Common helpers to wrap Illumio PCE "workloader" commands with:
#  - retry with exponential backoff + jitter
#  - per-attempt timeout (if 'timeout' binary is available)
#  - post-attempt throttling (orange) and post-success pause (yellow)
#  - consistent logging: START / END / RETRY WAIT / INTER-ATTEMPT SLEEP / OUTPUT FILE
#
# Environment variables (provided by the Python orchestrator via carto.conf):
#   EXECUTABLE        : absolute path to 'workloader' binary (required)
#   CFG               : absolute path to 'pce.yaml' (required)
#   PCE_NAME          : optional PCE logical name; if set, '--pce $PCE_NAME' is injected
#   BASE_SLEEP        : base sleep (seconds) before computing backoff            [default: 3]
#   BACKOFF           : backoff factor (e.g., 2 -> 3,6,12,24,48...)              [default: 2]
#   MAX_SLEEP         : maximum sleep between retries (seconds)                  [default: 60]
#   JITTER            : jitter percentage (+/-) applied to computed wait time    [default: 20]
#   TIMEOUT_SEC       : per-attempt timeout (seconds) if 'timeout' is available  [default: 2700]
#   MAX_ATTEMPTS      : maximum number of attempts before giving up              [default: 5]
#
# Notes:
#  - If 'timeout' is not available on the system, attempts will run without timeout.
#  - This file is designed to be 'bash -n' clean and portable across typical Linux distros.
# ------------------------------------------------------------------------------

set -Eeuo pipefail

: "${EXECUTABLE:?path to workloader required}"
: "${CFG:?path to pce.yaml required}"

BASE_SLEEP="${BASE_SLEEP:-3}"
BACKOFF="${BACKOFF:-2}"
MAX_SLEEP="${MAX_SLEEP:-60}"
JITTER="${JITTER:-20}"

TIMEOUT_SEC="${TIMEOUT_SEC:-2700}"   # 45 minutes
MAX_ATTEMPTS="${MAX_ATTEMPTS:-5}"

YELLOW=$'\033[33m'
ORANGE=$'\033[38;5;214m'
RESET=$'\033[0m'

run_workloader() {
  "${EXECUTABLE}" --config-file "${CFG}" "$@"
}

progress_bar() {
  local color="$1" secs="${2:-60}"
  (( secs <= 0 )) && return 0
  local i total=30 filled bar pct
  for (( i=0; i<secs; i++ )); do
    filled=$(( total * i / secs ))
    bar=$(printf '%*s' "$filled" '' | tr ' ' '#')
    pct=$(( 100 * i / secs ))
    printf "\r%s[%-30s] %3d%%%s" "$color" "$bar" "$pct" "$RESET"
    sleep 1
  done
  bar=$(printf '%*s' 30 '' | tr ' ' '#')
  printf "\r%s[%-30s] %3d%%%s\n" "$color" "$bar" 100 "$RESET"
}

pause_yellow() {
  local label="$1" secs="${2:-60}"
  printf "%sPAUSE %ds after [%s]...%s\n" "$YELLOW" "$secs" "$label" "$RESET"
  progress_bar "$YELLOW" "$secs"
}

pause_orange() {
  local label="$1" secs="${2:-60}"
  printf "%sINTER-ATTEMPT SLEEP %ds after [%s]...%s\n" "$ORANGE" "$secs" "$label" "$RESET"
  progress_bar "$ORANGE" "$secs"
}

retry_backoff() {
  # Usage: retry_backoff <tag> -- <args to workloader ... --output-file <OUT>>
  local tag="$1"; shift
  [[ "${1:-}" == "--" ]] && shift
  local args=( "$@" )

  local cmd_args
  if [[ -n "${PCE_NAME:-}" ]]; then
    cmd_args=( --pce "$PCE_NAME" "${args[@]}" )
  else
    cmd_args=( "${args[@]}" )
  fi

  local out_file=""
  for i in "${!cmd_args[@]}"; do
    if [[ "${cmd_args[$i]}" == "--output-file" ]]; then
      out_file="${cmd_args[$((i+1))]}"
      break
    fi
  done

  local attempt=1 rc=1
  while :; do
    echo "$(date '+%F %T') START [${tag}] attempt=${attempt} CMD=${EXECUTABLE} --config-file ${CFG} ${cmd_args[*]}"
    set +e
    if command -v timeout >/dev/null 2>&1; then
      export -f run_workloader
      timeout --preserve-status "${TIMEOUT_SEC}s" bash -c 'run_workloader "$@"' -- "${cmd_args[@]}"
      rc=$?
      [[ $rc -eq 124 ]] && echo "$(date '+%F %T') [WARN] ${tag} timed out after ${TIMEOUT_SEC}s"
    else
      run_workloader "${cmd_args[@]}"
      rc=$?
    fi
    set -e

    if [[ $rc -eq 0 ]]; then
      if [[ -n "${WL_SKIP_OUTPUT_CHECK:-}" ]]; then
        echo "$(date '+%F %T') END [${tag}] status=OK rc=$rc (output check skipped)"
        pause_yellow "$tag" 60
        return 0
      fi
      if [[ -n "$out_file" ]]; then
        if [[ -s "$out_file" ]]; then
          echo "$(date '+%F %T') END [${tag}] status=OK rc=$rc out=$out_file"
          pause_yellow "$tag" 60
          return 0
        fi
        echo "$(date '+%F %T') END [${tag}] status=FAIL rc=$rc out=$out_file (empty or missing)"
      else
        echo "$(date '+%F %T') END [${tag}] status=OK rc=$rc"
        pause_yellow "$tag" 60
        return 0
      fi
    fi

    echo "$(date '+%F %T') END [${tag}] status=FAIL rc=$rc"
    pause_orange "$tag attempt=${attempt}" 60

    if (( attempt >= MAX_ATTEMPTS )); then
      echo "RETRY STOP [${tag}] max attempts reached=${MAX_ATTEMPTS}"
      return 1
    fi

    local wait="$BASE_SLEEP"
    local j
    for (( j=1; j<attempt; j++ )); do
      wait=$(( wait * BACKOFF ))
      (( wait > MAX_SLEEP )) && { wait="$MAX_SLEEP"; break; }
    done
    local jitter=$(( wait * JITTER / 100 ))
    local delta=0
    (( jitter > 0 )) && delta=$(( RANDOM % (2*jitter + 1) - jitter ))
    wait=$(( wait + delta ))
    (( wait < 1 )) && wait=1

    echo "RETRY WAIT [${tag}] sleeping=${wait}s"
    sleep "$wait"
    (( attempt++ ))
  done
}
