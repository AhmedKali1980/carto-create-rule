#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/workloader_common.sh"
INCLUDE="${1:?include file required}"
START="${2:?start YYYY-mm-dd}"
END="${3:?end YYYY-mm-dd}"
OUT="${4:?output csv}"

NOT_ALLOWED=$(mktemp "${OUT}.not_allowed.XXXXXX")
ALLOWED=$(mktemp "${OUT}.allowed.XXXXXX")
trap 'rm -f -- "$NOT_ALLOWED" "$ALLOWED"' EXIT

retry_backoff "traffic-out-not-allowed" -- traffic -c "${INCLUDE}" -s "${START}" -e "${END}" \
  --excl-allowed --output-file "${NOT_ALLOWED}"
retry_backoff "traffic-out-allowed" -- traffic -c "${INCLUDE}" -s "${START}" -e "${END}" \
  --excl-potentially-blocked --excl-blocked --excl-unknown --output-file "${ALLOWED}"

merge_traffic_csv "${NOT_ALLOWED}" "${ALLOWED}" "${OUT}"
