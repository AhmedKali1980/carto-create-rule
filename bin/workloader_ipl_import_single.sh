#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/workloader_common.sh"

OUT_CSV="${1:?output csv required}"
IPLIST_NAME="${2:?iplist name required}"
retry_backoff "ipl-export-single" -- ipl-export "${IPLIST_NAME}" --output-file "${OUT_CSV}"
