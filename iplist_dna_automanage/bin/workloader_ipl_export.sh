#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/workloader_common.sh"
OUT_CSV="${1:?output csv required}"
retry_backoff "ipl-export" ipl-export --output-file "${OUT_CSV}"
