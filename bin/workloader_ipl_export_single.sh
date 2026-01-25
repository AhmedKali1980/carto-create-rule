#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$0")/workloader_common.sh"

OUT_CSV="${1:?output csv required}"
IPLIST_NAME="${2:?iplist name required}"

OUT_DIR="$(dirname "${OUT_CSV}")"
OUT_BASE="$(basename "${OUT_CSV}" .csv)"
OUT_IP_ENTRIES="${OUT_DIR}/${OUT_BASE}-ip_entries.csv"

mkdir -p "${OUT_DIR}"

(
  cd "${OUT_DIR}"
  retry_backoff "ipl-export-single" -- ipl-export "${IPLIST_NAME}" --output-file "${OUT_BASE}.csv"
)

if [[ -f "${OUT_IP_ENTRIES}" ]]; then
  mv -f "${OUT_IP_ENTRIES}" "${OUT_CSV}"
else
  echo "[ERROR] iplist export did not produce ${OUT_IP_ENTRIES}" >&2
  exit 1
fi
