#!/usr/bin/env bash
set -euo pipefail

version="${1:-manual}"
image="jinja-build:${version}"
package_dir="artifacts/jinja-build-docker-${version}"
archive="jinja-build-${version}-image.tar.gz"

docker build -f docker/Dockerfile -t "${image}" .

rm -rf "${package_dir}"
mkdir -p "${package_dir}/template" "${package_dir}/doc-output" "${package_dir}/log"

docker save "${image}" | gzip > "${package_dir}/${archive}"
cp docker/docker-compose.offline.yml "${package_dir}/docker-compose.yml"
cp docker/load-and-run.sh "${package_dir}/load-and-run.sh"
cp docker/OFFLINE-README.md "${package_dir}/README.md"
chmod +x "${package_dir}/load-and-run.sh"

tar -czf "artifacts/jinja-build-docker-${version}.tar.gz" -C artifacts "jinja-build-docker-${version}"
