#!/usr/bin/env bash
# 在 .venv 中运行 jinja-build（对应 run.bat）。
# 用法：./run.sh <template> <input> <output> [额外参数...]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ $# -lt 3 ]]; then
  echo "用法: $0 <template> <input> <output> [额外参数...]" >&2
  echo "例如: $0 examples/01-jinja-basics examples/01-jinja-basics/config.yaml examples/01-jinja-basics/generated" >&2
  exit 1
fi

if [[ ! -x "$ROOT/.venv/Scripts/python.exe" && ! -x "$ROOT/.venv/bin/python" ]]; then
  bash "$ROOT/update.sh"
fi

if [[ -x "$ROOT/.venv/Scripts/python.exe" ]]; then
  PYTHON="$ROOT/.venv/Scripts/python.exe"
else
  PYTHON="$ROOT/.venv/bin/python"
fi

TEMPLATE="$1"
INPUT="$2"
OUTPUT="$3"
shift 3
exec "$PYTHON" "$ROOT/src/__main__.py" -t "$TEMPLATE" -i "$INPUT" -o "$OUTPUT" "$@"
