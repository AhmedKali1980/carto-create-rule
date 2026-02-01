#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/workloader_common.sh"
INCLUDE="${1:?include file required}"
START="${2:?start YYYY-mm-dd}"
END="${3:?end YYYY-mm-dd}"
OUT="${4:?output csv}"
retry_backoff "traffic-out-dst" -- traffic -a "${INCLUDE}" -s "${START}" -e "${END}" --output-file "${OUT}"
