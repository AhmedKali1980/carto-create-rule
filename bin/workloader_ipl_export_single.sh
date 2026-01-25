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
  WL_SKIP_OUTPUT_CHECK=1 retry_backoff "ipl-export-single" -- ipl-export "${IPLIST_NAME}" --output-file "${OUT_BASE}.csv"
)

found_file=""
for candidate in \
  "${OUT_IP_ENTRIES}" \
  "${OUT_DIR}/.${OUT_BASE}single-ip_entries.csv" \
  "${OUT_DIR}/.${OUT_BASE}-ip_entries.csv" \
  "${OUT_DIR}/${OUT_BASE}single-ip_entries.csv" \
  "${OUT_DIR}/${OUT_BASE}"*-ip_entries.csv; do
  if [[ -f "${candidate}" ]]; then
    found_file="${candidate}"
    break
  fi
done

if [[ -n "${found_file}" ]]; then
  mv -f "${found_file}" "${OUT_CSV}"
else
  echo "[ERROR] iplist export did not produce an ip_entries file in ${OUT_DIR}" >&2
  exit 1
fi
