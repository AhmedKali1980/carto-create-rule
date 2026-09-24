#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/workloader_common.sh"

INCLUDE="${1:?include file required}"
START="${2:?start YYYY-mm-dd}"
END="${3:?end YYYY-mm-dd}"
OUT="${4:?output csv}"
EXCLUDE_LABELS="${5:-}"
EXCLUDE_IPLISTS="${6:-}"

FILTERS=(--incl-dst-file "${INCLUDE}")
EXCLUDE_SRC=""
TEMP_EXCLUDE=""
if [[ -n "${EXCLUDE_LABELS}" && -n "${EXCLUDE_IPLISTS}" ]]; then
  EXCLUDE_SRC=$(mktemp "${OUT}.exclude_src.XXXXXX")
  TEMP_EXCLUDE="${EXCLUDE_SRC}"
  awk '1' "${EXCLUDE_LABELS}" "${EXCLUDE_IPLISTS}" > "${EXCLUDE_SRC}"
elif [[ -n "${EXCLUDE_LABELS}" ]]; then
  EXCLUDE_SRC="${EXCLUDE_LABELS}"
elif [[ -n "${EXCLUDE_IPLISTS}" ]]; then
  EXCLUDE_SRC="${EXCLUDE_IPLISTS}"
fi
[[ -n "${EXCLUDE_SRC}" ]] && FILTERS+=(--excl-src-file "${EXCLUDE_SRC}")

NOT_ALLOWED=$(mktemp "${OUT}.not_allowed.XXXXXX")
ALLOWED=$(mktemp "${OUT}.allowed.XXXXXX")
trap 'rm -f -- "$NOT_ALLOWED" "$ALLOWED"; [[ -z "$TEMP_EXCLUDE" ]] || rm -f -- "$TEMP_EXCLUDE"' EXIT

retry_backoff "traffic-in-not-allowed" -- traffic "${FILTERS[@]}" -s "${START}" -e "${END}" \
  --excl-allowed --output-file "${NOT_ALLOWED}"
retry_backoff "traffic-in-allowed" -- traffic "${FILTERS[@]}" -s "${START}" -e "${END}" \
  --excl-potentially-blocked --excl-blocked --excl-unknown --output-file "${ALLOWED}"

merge_traffic_csv "${NOT_ALLOWED}" "${ALLOWED}" "${OUT}"
