#!/usr/bin/env bash
# run-ui-behave.sh — Start the Vite dev server (mock mode) then run Behave UI tests.
#
# Usage:
#   scripts/uat/run-ui-behave.sh                     # mock mode (default)
#   E2E_MODE=integration scripts/uat/run-ui-behave.sh
#
# Environment variables:
#   E2E_MODE  "mock" (default) or "integration"
#   BASE_URL  Frontend origin (default: http://localhost:5173)
#   HEADLESS  "true" (default) / "false" to watch the browser
#   BEHAVE_ARGS  Extra arguments forwarded to behave (e.g. "--tags @wip")

set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
E2E_MODE="${E2E_MODE:-mock}"
BASE_URL="${BASE_URL:-http://localhost:5173}"
HEADLESS="${HEADLESS:-true}"
SERVER_PID=""

# ── Helper: wait for server ────────────────────────────────────────────────────
wait_for_server() {
    local url="$1"
    local retries=60
    echo "⏳  Waiting for $url ..."
    for i in $(seq 1 "$retries"); do
        if curl -sf --max-time 2 "$url" > /dev/null 2>&1; then
            echo "✅  Server ready at $url"
            return 0
        fi
        sleep 2
    done
    echo "❌  Server did not start within $((retries * 2)) seconds" >&2
    return 1
}

# ── Start Vite dev server in mock mode if not already running ──────────────────
if [ "$E2E_MODE" = "mock" ]; then
    if curl -sf --max-time 1 "$BASE_URL" > /dev/null 2>&1; then
        echo "ℹ️   Reusing existing dev server at $BASE_URL"
    else
        echo "🚀  Starting Vite dev server with MSW enabled..."
        cd "$WORKSPACE_ROOT"
        VITE_MSW_ENABLED=true pnpm exec nx run app-web:serve &
        SERVER_PID=$!
        wait_for_server "$BASE_URL"
    fi
fi

# ── Run Behave UI tests ────────────────────────────────────────────────────────
cd "$WORKSPACE_ROOT"
echo "🎭  Running Behave UI tests (E2E_MODE=$E2E_MODE, BASE_URL=$BASE_URL)..."

EXIT_CODE=0
E2E_MODE="$E2E_MODE" BASE_URL="$BASE_URL" HEADLESS="$HEADLESS" \
    uv run --project fastapi-clean-example \
    behave features/ui \
    --no-capture \
    --format progress2 \
    ${BEHAVE_ARGS:-} \
    || EXIT_CODE=$?

# ── Stop the server if we started it ──────────────────────────────────────────
if [ -n "$SERVER_PID" ]; then
    echo "🛑  Stopping dev server (PID $SERVER_PID)..."
    kill "$SERVER_PID" 2>/dev/null || true
fi

exit "$EXIT_CODE"
