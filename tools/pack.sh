#!/usr/bin/env bash
# 统一打包：使用仓库根 .venv，先 PyInstaller（各入口 spec），Linux 再 staticx 得到自解压静态包。
# Windows 仅 PyInstaller（无 staticx）。
#
# 用法（仓库根）：./tools/pack.sh [all|src|schema]
# Linux 另需系统包 patchelf（如 apt install patchelf）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TARGET="${1:-all}"

ensure_venv() {
  if [[ -f "$ROOT/.venv/Scripts/python.exe" ]]; then
    PYTHON_CMD=("$ROOT/.venv/Scripts/python.exe")
  elif [[ -f "$ROOT/.venv/bin/python" ]]; then
    PYTHON_CMD=("$ROOT/.venv/bin/python")
  else
    echo "未找到 .venv，正在创建 ..."
    case "$(uname -s 2>/dev/null || true)" in
      MINGW*|MSYS*|CYGWIN*|Windows_NT)
        if command -v py >/dev/null 2>&1; then
          py -3 -m venv "$ROOT/.venv"
        else
          python -m venv "$ROOT/.venv"
        fi
        PYTHON_CMD=("$ROOT/.venv/Scripts/python.exe")
        ;;
      *)
        if ! command -v python3 >/dev/null 2>&1; then
          echo "错误: 需要 python3 以创建 .venv。" >&2
          exit 1
        fi
        python3 -m venv "$ROOT/.venv"
        PYTHON_CMD=("$ROOT/.venv/bin/python")
        ;;
    esac
  fi
  echo "==> 使用虚拟环境: ${PYTHON_CMD[*]} ($("${PYTHON_CMD[@]}" -V 2>/dev/null || true))"
}

spec_for_target() {
  case "$1" in
    src) echo "$ROOT/jinja-build-cli.spec" ;;
    schema) echo "$ROOT/jinja-build-schema.spec" ;;
    *)
      echo "错误: 未知目标 $1（可用: all、src、schema）。" >&2
      exit 1
      ;;
  esac
}

dist_name_for_target() {
  case "$1" in
    src) echo "jinja-build" ;;
    schema) echo "jinja-build-schema" ;;
    *) exit 1 ;;
  esac
}

apply_staticx_linux() {
  local dist_name="$1"
  local pyi_out="$ROOT/dist/${dist_name}"
  if [[ ! -f "$pyi_out" ]]; then
    return 0
  fi
  if ! command -v patchelf >/dev/null 2>&1; then
    echo "错误: Linux 下 staticx 需要系统命令 patchelf（例如: sudo apt install patchelf）。" >&2
    exit 1
  fi
  "${PYTHON_CMD[@]}" -m pip install -q staticx
  local staticx="$ROOT/.venv/bin/staticx"
  if [[ ! -x "$staticx" ]]; then
    echo "错误: 未找到可执行的 .venv/bin/staticx。" >&2
    exit 1
  fi
  local tmp_out="$ROOT/dist/.${dist_name}-staticx.tmp"
  rm -f "$tmp_out"
  echo "==> staticx: $pyi_out -> $dist_name"
  "$staticx" "$pyi_out" "$tmp_out"
  mv -f "$tmp_out" "$pyi_out"
  chmod +x "$pyi_out"
  echo "完成: $pyi_out（staticx 自解压包；请在目标机实测）"
}

build_target() {
  local name="$1"
  local spec
  spec="$(spec_for_target "$name")"
  if [[ ! -f "$spec" ]]; then
    echo "错误: 未找到 $spec" >&2
    exit 1
  fi
  echo "==> PyInstaller: $spec"
  "${PYTHON_CMD[@]}" -m PyInstaller --clean --noconfirm "$spec"
  local dist_name
  dist_name="$(dist_name_for_target "$name")"
  if [[ -f "$ROOT/dist/${dist_name}.exe" ]]; then
    echo "完成: $ROOT/dist/${dist_name}.exe（Windows：无 staticx 步骤）"
    return 0
  fi
  if [[ ! -f "$ROOT/dist/${dist_name}" ]]; then
    echo "错误: 未在 dist 找到 ${dist_name} 或 ${dist_name}.exe。" >&2
    exit 1
  fi
  case "$(uname -s 2>/dev/null || true)" in
    Linux) apply_staticx_linux "$dist_name" ;;
    *) echo "完成: $ROOT/dist/${dist_name}（非 Linux，跳过 staticx）" ;;
  esac
}

ensure_venv

"${PYTHON_CMD[@]}" -m pip install -q -U pip setuptools wheel
"${PYTHON_CMD[@]}" -m pip install -q -e .
"${PYTHON_CMD[@]}" -m pip install -q "pyinstaller>=6.0"

rm -rf "$ROOT/build" "$ROOT/dist"

case "$TARGET" in
  all)
    build_target src
    rm -rf "$ROOT/build"
    build_target schema
    ;;
  src|schema)
    build_target "$TARGET"
    ;;
  *)
    echo "用法: ./tools/pack.sh [all|src|schema]" >&2
    exit 1
    ;;
esac

echo "PyInstaller 输出目录: $ROOT/dist"
