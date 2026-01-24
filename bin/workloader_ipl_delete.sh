#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/workloader_common.sh"

HREF_FILE="${1:?href csv required}"
retry_backoff "ipl-delete" -- delete "${HREF_FILE}" --update-pce --no-prompt --provision
