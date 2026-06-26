#!/usr/bin/env bash
# 生成单个 examples 示范产物（对应 example.bat）。
# 用法：./example.sh <示范目录名>
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ $# -lt 1 ]]; then
  echo "用法: $0 <示范目录名>" >&2
  echo "例如: $0 jinja-basics" >&2
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

NAME="$1"
shift
exec "$PYTHON" "$ROOT/src/__main__.py" \
  -t "$ROOT/examples/$NAME" \
  -i "$ROOT/examples/$NAME/config.yaml" \
  -o "$ROOT/examples/$NAME/generated" \
  "$@"
