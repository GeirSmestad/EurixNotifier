#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment if present (kept out of git via .gitignore in most setups).
if [[ -f "${APP_DIR}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a
  source "${APP_DIR}/.env"
  set +a
fi

cd "${APP_DIR}"

VENV_PY="${APP_DIR}/.venv/bin/python"
if [[ ! -x "${VENV_PY}" ]]; then
  echo "Missing venv python at ${VENV_PY}. Run bootstrap.sh first." >&2
  exit 1
fi

exec "${VENV_PY}" -m eurixnotifier "$@"

