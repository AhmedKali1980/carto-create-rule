#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/workloader_common.sh"
OUT="${1:?output csv}"
HEADERS='href,hostname,name,external_data_set,created_at,interfaces,public_ip,app,env,loc,role,managed,enforcement,external_data_reference,OS'
retry_backoff "wkld-export-m" -- wkld-export -m --headers "$HEADERS" --output-file "$OUT"
