#!/usr/bin/env bash

set -euo pipefail

IMAGE_NAME=${IMAGE_NAME:-minddock-backend}
CONTAINER_NAME=${CONTAINER_NAME:-minddock-backend}
HOST_PORT=${HOST_PORT:-8000}
ENV_FILE=${ENV_FILE:-}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

docker build -t "${IMAGE_NAME}" "${PROJECT_ROOT}"

RUN_ARGS=(
  --rm
  --name "${CONTAINER_NAME}"
  -p "${HOST_PORT}:8000"
  -v "${PROJECT_ROOT}/app/storage:/app/app/storage"
)

if [[ -n "${ENV_FILE}" ]]; then
  RUN_ARGS+=(--env-file "${ENV_FILE}")
fi

exec docker run "${RUN_ARGS[@]}" "${IMAGE_NAME}"
