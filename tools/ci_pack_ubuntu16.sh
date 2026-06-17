#!/usr/bin/env bash
# CI entry for GitHub Release: run inside ubuntu:16.04 and build the Linux staticx artifact.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

rm -rf .venv build dist

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates \
  wget \
  bzip2 \
  binutils \
  patchelf
rm -rf /var/lib/apt/lists/*

MINICONDA=Miniconda3-py310_23.5.2-0-Linux-x86_64.sh
for attempt in 1 2 3 4 5; do
  if wget -O "/tmp/${MINICONDA}" "https://repo.anaconda.com/miniconda/${MINICONDA}"; then
    break
  fi
  if [[ "$attempt" == "5" ]]; then
    exit 1
  fi
  sleep 5
done

bash "/tmp/${MINICONDA}" -b -p /opt/conda
export PATH="/opt/conda/bin:$PATH"
python3 -V

export PACK_LINUX_SKIP_STATICX=1
bash tools/pack.sh src
