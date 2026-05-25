#!/usr/bin/env bash
# 创建/使用仓库根 .venv，并 editable 安装本项目（对应 update.bat）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/Scripts/python.exe" ]]; then
  PYTHON="$ROOT/.venv/Scripts/python.exe"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv "$ROOT/.venv"
  elif command -v python >/dev/null 2>&1; then
    python -m venv "$ROOT/.venv"
  else
    echo "错误: 未找到 python3 或 python，无法创建虚拟环境。" >&2
    exit 1
  fi
  if [[ -x "$ROOT/.venv/Scripts/python.exe" ]]; then
    PYTHON="$ROOT/.venv/Scripts/python.exe"
  else
    PYTHON="$ROOT/.venv/bin/python"
  fi
fi

"$PYTHON" -m pip install -U pip setuptools wheel
"$PYTHON" -m pip install -e .
