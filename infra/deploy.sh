#!/bin/bash
# =============================================================================
# VOLAURA — One-command brain deploy on VM
# =============================================================================
# What it does:
#   1. cd to repo root (/opt/volaura by default).
#   2. git fetch origin + checkout codex/swarm-queue-bridge + git pull.
#   3. pkill old gemma4_brain.py process (if running).
#   4. Start fresh brain in background with .env loaded.
#   5. Tail brain.log so you see proof of life before exit.
#
# Daemon (atlas_swarm_daemon.py) is NOT touched — Patch 2 is brain-only and
# backward-compatible with the daemon already running.
#
# Usage on VM:
#   curl -fsSL https://raw.githubusercontent.com/ganbaroff/volaura/codex/swarm-queue-bridge/infra/deploy.sh | bash
#   OR
#   cd /opt/volaura && git fetch && git checkout codex/swarm-queue-bridge -- infra/deploy.sh && bash infra/deploy.sh
# =============================================================================

set -euo pipefail

REPO="${VOLAURA_REPO:-/opt/volaura}"
BRANCH="${VOLAURA_BRANCH:-codex/swarm-queue-bridge}"
LOG_DIR="${VOLAURA_LOGS:-/var/log/volaura}"
BRAIN_LOG="${LOG_DIR}/brain.log"

echo "[deploy] repo=${REPO} branch=${BRANCH}"

if [[ ! -d "${REPO}/.git" ]]; then
    echo "[deploy] FATAL: ${REPO} is not a git repo" >&2
    exit 1
fi

cd "${REPO}"

echo "[deploy] git fetch origin..."
git fetch origin

echo "[deploy] git checkout ${BRANCH}..."
git checkout "${BRANCH}"

echo "[deploy] git pull..."
git pull --ff-only origin "${BRANCH}"

NEW_HEAD="$(git log --oneline -1)"
echo "[deploy] HEAD now: ${NEW_HEAD}"

mkdir -p "${LOG_DIR}"

# Stop the old brain process (if any). Match exactly gemma4_brain.py to avoid
# touching the daemon.
if pgrep -f "gemma4_brain.py" > /dev/null; then
    echo "[deploy] stopping old brain process..."
    pkill -f "gemma4_brain.py" || true
    sleep 2
fi

# Source .env so brain has provider keys
if [[ -f "${REPO}/apps/api/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${REPO}/apps/api/.env"
    set +a
    echo "[deploy] .env loaded"
else
    echo "[deploy] WARNING: ${REPO}/apps/api/.env not found — brain will rely on shell env only" >&2
fi

# Start fresh brain in background, redirected to brain.log
PYTHON_BIN="${PYTHON_BIN:-python3}"
echo "[deploy] starting brain via ${PYTHON_BIN}..."
nohup "${PYTHON_BIN}" "${REPO}/scripts/gemma4_brain.py" > "${BRAIN_LOG}" 2>&1 &
NEW_PID=$!
disown
echo "[deploy] new brain PID: ${NEW_PID}"

# Verify brain process is alive
sleep 3
if ! kill -0 "${NEW_PID}" 2>/dev/null; then
    echo "[deploy] FATAL: brain died within 3s. Check ${BRAIN_LOG}" >&2
    tail -30 "${BRAIN_LOG}" >&2 || true
    exit 2
fi

echo "[deploy] brain alive after 3s"
echo "[deploy] tailing ${BRAIN_LOG} (Ctrl+C to stop tail; brain keeps running)..."
echo "================================================================"
tail -f "${BRAIN_LOG}" &
TAIL_PID=$!
sleep 30
kill "${TAIL_PID}" 2>/dev/null || true
echo "================================================================"
echo "[deploy] DONE. brain PID=${NEW_PID}, branch=${BRANCH}, head=${NEW_HEAD}"
echo "[deploy] To see live brain: tail -f ${BRAIN_LOG}"
