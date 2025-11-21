#!/usr/bin/env bash
set -euo pipefail

# Simple launcher: start a browser with CDP, activate venv, run cli.py with sensible defaults.
# Env overrides:
# - PORT: CDP port (default 9222)
# - REGION: cn/us/i18n; selects default login URL unless LOGIN_URL overrides
# - LOGIN_URL: SSO login URL (optional; otherwise picked by REGION)
# - WAIT_URL: glob to detect login completion; leave empty to press Enter manually
# - BROWSER_BIN: explicit browser executable; otherwise auto-detect Chrome/Edge
# - START_BROWSER: set to 0 to skip launching browser (if already running with CDP)
# - PYTHON: python executable (default "python")

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-9222}"
REGION="${REGION:-cn}"
LOGIN_URL="${LOGIN_URL:-}"
WAIT_URL="${WAIT_URL:-}"
START_BROWSER="${START_BROWSER:-1}"
PYTHON_BIN="${PYTHON:-python}"
CDP_ENDPOINT="http://127.0.0.1:${PORT}"

detect_browser() {
  if [[ -n "${BROWSER_BIN:-}" ]]; then
    echo "${BROWSER_BIN}"
    return
  fi
  local uname_out
  uname_out="$(uname -s)"
  if [[ "$uname_out" == "Darwin" ]]; then
    if [[ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]]; then
      echo "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
      return
    fi
    if [[ -x "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" ]]; then
      echo "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
      return
    fi
  fi
  if command -v google-chrome >/dev/null 2>&1; then
    echo "google-chrome"
    return
  fi
  if command -v chromium >/dev/null 2>&1; then
    echo "chromium"
    return
  fi
  if command -v microsoft-edge >/dev/null 2>&1; then
    echo "microsoft-edge"
    return
  fi
  echo "Browser executable not found. Set BROWSER_BIN to your Chrome/Edge path." >&2
  exit 1
}

BROWSER_CMD="$(detect_browser)"
BROWSER_PID=""

start_browser() {
  if [[ "${START_BROWSER}" != "1" ]]; then
    echo "Skipping browser launch; expecting browser already on ${CDP_ENDPOINT}"
    return
  fi
  echo "Starting browser: ${BROWSER_CMD} (CDP port ${PORT})"
  "${BROWSER_CMD}" \
    --remote-debugging-port="${PORT}" \
    --user-data-dir="${ROOT_DIR}/.chrome-profile" \
    --no-first-run \
    --no-default-browser-check \
    about:blank >/dev/null 2>&1 &
  BROWSER_PID=$!
  echo "Browser PID: ${BROWSER_PID} (will be terminated when this script exits)"
}

cleanup() {
  if [[ -n "${BROWSER_PID}" ]] && kill -0 "${BROWSER_PID}" >/dev/null 2>&1; then
    kill "${BROWSER_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

activate_venv() {
  local venv_path="${ROOT_DIR}/.venv/bin/activate"
  if [[ -f "${venv_path}" ]]; then
    # shellcheck source=/dev/null
    source "${venv_path}"
    echo "Activated venv at ${ROOT_DIR}/.venv"
  else
    echo "Warning: venv not found at ${ROOT_DIR}/.venv. Using system Python (${PYTHON_BIN})." >&2
  fi
}

main() {
  start_browser
  activate_venv

  CLI_ARGS=(--cdp-endpoint "${CDP_ENDPOINT}" --region "${REGION}")
  if [[ -n "${LOGIN_URL}" ]]; then
    CLI_ARGS+=(--login-url "${LOGIN_URL}")
  fi
  if [[ -n "${WAIT_URL}" ]]; then
    CLI_ARGS+=(--wait-url "${WAIT_URL}")
  fi
  CLI_ARGS+=("$@")

  echo "Running: ${PYTHON_BIN} ${ROOT_DIR}/cli.py ${CLI_ARGS[*]}"
  "${PYTHON_BIN}" "${ROOT_DIR}/cli.py" "${CLI_ARGS[@]}"
}

main "$@"
