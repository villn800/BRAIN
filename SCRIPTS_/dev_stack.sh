#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
APP_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
REPO_ROOT=$(cd "$APP_ROOT/.." && pwd)
PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
NODE_BIN=$(command -v node || true)
BACKEND_DIR="$APP_ROOT/backend"
FRONTEND_DIR="$APP_ROOT/frontend"
BACKEND_PID_FILE="/tmp/backend.pid"
FRONTEND_PID_FILE="/tmp/frontend.pid"
STORAGE_ROOT="/tmp/brain_manual_storage"
BACKEND_LOG="/tmp/backend.log"
FRONTEND_LOG="/tmp/frontend.log"

if [[ ! -x $PYTHON_BIN ]]; then
  echo "Python virtualenv not found at $PYTHON_BIN" >&2
  exit 1
fi

if [[ -z $NODE_BIN ]]; then
  echo "Node.js is not installed (required for Vite dev server)." >&2
  exit 1
fi

NODE_VERSION_RAW=$($NODE_BIN -v | sed 's/^v//')
IFS='.' read -r NODE_MAJOR NODE_MINOR NODE_PATCH <<<"$NODE_VERSION_RAW"
if (( NODE_MAJOR < 20 )) || { (( NODE_MAJOR == 20 )) && (( NODE_MINOR < 19 )); }; then
  echo "Node.js $NODE_VERSION_RAW detected. Vite requires Node 20.19+ or 22.12+. Please upgrade Node.js." >&2
  exit 1
fi

stop_service() {
  local pid_file=$1
  if [[ -f $pid_file ]]; then
    local pid
    pid=$(cat "$pid_file")
    if [[ -n $pid ]] && kill -0 "$pid" 2>/dev/null; then
      echo "Stopping process $pid (from $pid_file)"
      kill "$pid" && wait "$pid" 2>/dev/null || true
    fi
    rm -f "$pid_file"
  fi
}

echo "Ensuring previous dev processes are stopped"
stop_service "$FRONTEND_PID_FILE"
stop_service "$BACKEND_PID_FILE"

mkdir -p "$STORAGE_ROOT"

echo "Starting FastAPI backend on port 4000"
(
  cd "$BACKEND_DIR"
  nohup env PYTHONPATH=app "$PYTHON_BIN" -m uvicorn app.main:app --host 0.0.0.0 --port 4000 >"$BACKEND_LOG" 2>&1 &
  echo $! > "$BACKEND_PID_FILE"
)

printf 'Waiting for backend health check...'
for attempt in {1..10}; do
  if curl -fsS http://localhost:4000/health >/dev/null; then
    printf ' done\n'
    break
  fi
  if [[ $attempt -eq 10 ]]; then
    echo " backend did not become healthy (see $BACKEND_LOG)" >&2
    exit 1
  fi
  printf '.'
  sleep 1
done

echo "Starting Vite dev server on port 5173"
(
  cd "$FRONTEND_DIR"
  nohup env \
    VITE_API_BASE_URL=http://localhost:4000/api \
    VITE_ASSET_BASE_URL=http://localhost:4000/assets \
    npm run dev -- --host 0.0.0.0 --port 5173 --strictPort >"$FRONTEND_LOG" 2>&1 &
  echo $! > "$FRONTEND_PID_FILE"
)

printf 'Waiting for frontend to respond...'
for attempt in {1..10}; do
  if curl -fsS http://localhost:5173/ >/dev/null; then
    printf ' done\n'
    break
  fi
  if [[ $attempt -eq 10 ]]; then
    echo " frontend failed to start (see $FRONTEND_LOG)" >&2
    exit 1
  fi
  printf '.'
  sleep 1
done

echo "Dev stack is running!"
echo "  Backend PID: $(cat "$BACKEND_PID_FILE") (logs: $BACKEND_LOG)"
echo "  Frontend PID: $(cat "$FRONTEND_PID_FILE") (logs: $FRONTEND_LOG)"
echo "Visit http://localhost:5173/login to start using the app."
