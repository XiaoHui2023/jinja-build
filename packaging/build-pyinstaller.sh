#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
WHEEL_DIR="${WHEEL_DIR:-${PROJECT_ROOT}/packaging/wheels}"
VENV_DIR="${VENV_DIR:-${PROJECT_ROOT}/.venv-pyinstaller}"
PYTHON_BIN="${PYTHON:-python3}"
TARGET="${1:-all}"

if [ ! -d "${WHEEL_DIR}" ]; then
  echo "Missing wheel directory: ${WHEEL_DIR}" >&2
  echo "Run packaging/download-pyinstaller-deps.sh on an online machine first." >&2
  exit 1
fi

cd "${PROJECT_ROOT}"

if [ ! -x "${VENV_DIR}/bin/python" ]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

# shellcheck source=/dev/null
. "${VENV_DIR}/bin/activate"

python -m pip install \
  --no-index \
  --find-links "${WHEEL_DIR}" \
  -r "${PROJECT_ROOT}/packaging/requirements-pyinstaller.txt"

rm -rf "${PROJECT_ROOT}/build" "${PROJECT_ROOT}/dist"

build_one() {
  local name="$1"
  pyinstaller --clean --noconfirm "${PROJECT_ROOT}/packaging/specs/${name}.spec"
}

case "${TARGET}" in
  all)
    build_one jinja-build-cli
    build_one jinja-build-server
    build_one jinja-build-doc
    ;;
  cli)
    build_one jinja-build-cli
    ;;
  server)
    build_one jinja-build-server
    ;;
  doc)
    build_one jinja-build-doc
    ;;
  *)
    echo "Usage: $0 [all|cli|server|doc]" >&2
    exit 1
    ;;
esac

echo "PyInstaller output directory: ${PROJECT_ROOT}/dist"
