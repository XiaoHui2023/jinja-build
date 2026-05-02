#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
WHEEL_DIR="${1:-${PROJECT_ROOT}/packaging/wheels}"
PYTHON_BIN="${PYTHON:-python3}"

mkdir -p "${WHEEL_DIR}"

"${PYTHON_BIN}" -m pip download \
  --dest "${WHEEL_DIR}" \
  -r "${PROJECT_ROOT}/packaging/requirements-pyinstaller.txt"

echo "Downloaded PyInstaller dependencies to: ${WHEEL_DIR}"
