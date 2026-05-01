#!/usr/bin/env bash
set -euo pipefail

archive="${1:-}"

if [ -z "${archive}" ]; then
  archive="$(ls jinja-build-*-image.tar.gz 2>/dev/null | head -n 1 || true)"
fi

if [ -z "${archive}" ]; then
  echo "No image archive found. Pass the archive path or place jinja-build-*-image.tar.gz here." >&2
  exit 1
fi

mkdir -p template doc-output log

loaded_image="$(docker load -i "${archive}" | sed -n 's/^Loaded image: //p' | tail -n 1)"
if [ -n "${loaded_image}" ]; then
  export IMAGE_NAME="${loaded_image}"
fi

docker compose -f docker-compose.yml up -d
