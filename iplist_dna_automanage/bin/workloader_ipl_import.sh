#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/workloader_common.sh"
IN_CSV="${1:?input csv required}"
retry_backoff "ipl-import" ipl-import "${IN_CSV}" --update-pce --no-prompt --provision
