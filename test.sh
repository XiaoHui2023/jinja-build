#!/usr/bin/env bash
# 在 .venv 中运行单元测试（对应 test.bat）；若无 venv 则先执行 update.sh。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ ! -x "$ROOT/.venv/Scripts/python.exe" && ! -x "$ROOT/.venv/bin/python" ]]; then
  bash "$ROOT/update.sh"
fi

if [[ -x "$ROOT/.venv/Scripts/python.exe" ]]; then
  PYTHON="$ROOT/.venv/Scripts/python.exe"
else
  PYTHON="$ROOT/.venv/bin/python"
fi

"$PYTHON" -m unittest discover -s tests "$@"
