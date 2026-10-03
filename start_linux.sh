#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

command -v python3 >/dev/null || { echo "Python 3 est requis."; exit 1; }
command -v php >/dev/null || { echo "PHP est requis."; exit 1; }

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r backend/requirements.txt

cleanup() {
  kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(
  cd backend
  ../.venv/bin/python -m uvicorn app.main:app --reload --port 8000
) &
BACKEND_PID=$!

(
  cd frontend/public
  php -S localhost:8080
) &
FRONTEND_PID=$!

echo "Interface : http://localhost:8080"
echo "API       : http://localhost:8000/docs"
wait
