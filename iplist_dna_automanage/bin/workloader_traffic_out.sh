#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/workloader_common.sh"

INCL_SRC_FILE="${1:?include src file required}"
EXCL_DST_FILE="${2:?exclude dst file required}"
EXCL_SVC_FILE="${3:?exclude service file required}"
START_DATE="${4:?start date YYYY-mm-dd required}"
END_DATE="${5:?end date YYYY-mm-dd required}"
OUT_CSV="${6:?output csv required}"

retry_backoff "traffic-out" traffic \
  --incl-src-file "${INCL_SRC_FILE}" \
  --excl-dst-file "${EXCL_DST_FILE}" \
  --excl-svc-file "${EXCL_SVC_FILE}" \
  --start "${START_DATE}" \
  --end "${END_DATE}" \
  --max-results 200000 \
  --output-file "${OUT_CSV}"
