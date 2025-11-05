#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

if [[ ! -d "${FRONTEND_DIR}/node_modules" ]]; then
  echo "[setup] Installing frontend dependencies..."
  (cd "${FRONTEND_DIR}" && npm install)
fi

echo "[dev] Starting Vite dev server..."
exec npm run dev --prefix "${FRONTEND_DIR}"
