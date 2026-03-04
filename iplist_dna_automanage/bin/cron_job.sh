#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONF_FILE="${1:-${ROOT_DIR}/conf/global.conf}"

export GLOBAL_CONF_PATH="${CONF_FILE}"
python3 "${ROOT_DIR}/modules/dna_automanage.py" --config "${CONF_FILE}"
