#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"

function usage() {
  cat <<'USAGE'
MindDock development helper

Usage: ./scripts/minddock.sh <command> [args]

Commands:
  setup            Create the Python virtual environment and install backend deps
  backend          Start the FastAPI app with uvicorn (reload enabled)
  backend-prod     Start the FastAPI app without reload (production mode)
  frontend         Start the Vite development server
  docker           Build and run the backend container (delegates to run_docker.sh)
  test             Run pytest within the virtual environment
  format           Format backend code with ruff (if installed)
  rag-reindex      Regenerate embeddings for all memories (RAG index)
  help             Show this help message

Environment variables:
  HOST             Address for uvicorn to bind (default: 0.0.0.0)
  PORT             Port for uvicorn to use (default: 8000)
  UVICORN_ARGS     Extra arguments passed to uvicorn commands
USAGE
}

function log() {
  echo "[minddock] $*"
}

function ensure_venv() {
  if [[ ! -d "${VENV_DIR}" ]]; then
    log "Creating virtual environment at ${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
  fi

  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"

  local requirements_file="${PROJECT_ROOT}/requirements.txt"
  if [[ ! -f "${requirements_file}" ]]; then
    log "requirements.txt not found at ${requirements_file}"
    return 1
  fi

  if [[ ! -f "${VENV_DIR}/.deps-installed" ]] || [[ ${requirements_file} -nt "${VENV_DIR}/.deps-installed" ]]; then
    log "Installing backend dependencies from requirements.txt"
    pip install --upgrade pip >/dev/null
    pip install -r "${requirements_file}"
    touch "${VENV_DIR}/.deps-installed"
  fi
}

function cmd_setup() {
  ensure_venv
  log "Virtual environment ready"
}

function cmd_backend() {
  ensure_venv
  local host="${HOST:-0.0.0.0}"
  local port="${PORT:-8000}"
  log "Starting uvicorn on ${host}:${port} (reload)"
  exec uvicorn app.main:app --reload --host "${host}" --port "${port}" ${UVICORN_ARGS:-}
}

function cmd_backend_prod() {
  ensure_venv
  local host="${HOST:-0.0.0.0}"
  local port="${PORT:-8000}"
  log "Starting uvicorn on ${host}:${port} (production mode)"
  exec uvicorn app.main:app --host "${host}" --port "${port}" ${UVICORN_ARGS:-}
}

function cmd_frontend() {
  log "Delegating to scripts/run_frontend.sh"
  exec "${SCRIPT_DIR}/run_frontend.sh"
}

function cmd_docker() {
  log "Delegating to scripts/run_docker.sh"
  exec "${SCRIPT_DIR}/run_docker.sh"
}

function cmd_test() {
  ensure_venv
  log "Running pytest"
  exec pytest "$@"
}

function cmd_format() {
  ensure_venv
  if ! command -v ruff >/dev/null 2>&1; then
    log "ruff not found in PATH; installing into virtual environment"
    pip install ruff
  fi
  log "Formatting backend with ruff"
  exec ruff format "${PROJECT_ROOT}/app" "$@"
}

function cmd_rag_reindex() {
  ensure_venv
  log "Rebuilding RAG embeddings for all memories"
  python <<'PYCODE'
from app.database import SessionLocal
from app.repositories import MemoryRepository
from app.services.rag_service import RAGService

session = SessionLocal()
try:
    repo = MemoryRepository(session)
    rag = RAGService(session)
    memories = repo.list_all()
    for memory in memories:
        rag.index_memory(memory)
    print(f"[minddock] Re-indexed {len(memories)} memories")
finally:
    session.close()
PYCODE
}

COMMAND="${1:-help}"
shift || true

case "${COMMAND}" in
  setup)
    cmd_setup "$@"
    ;;
  backend)
    cmd_backend "$@"
    ;;
  backend-prod)
    cmd_backend_prod "$@"
    ;;
  frontend)
    cmd_frontend "$@"
    ;;
  docker)
    cmd_docker "$@"
    ;;
  test)
    cmd_test "$@"
    ;;
  format)
    cmd_format "$@"
    ;;
  rag-reindex)
    cmd_rag_reindex "$@"
    ;;
  help|--help|-h)
    usage
    ;;
  *)
    usage
    log "Unknown command: ${COMMAND}"
    exit 1
    ;;
esac
