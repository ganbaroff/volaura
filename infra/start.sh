#!/bin/bash
# =============================================================================
# VOLAURA Organism — Single-command VPS startup
# =============================================================================
# Adapted from Perplexity's template for our ACTUAL project structure.
#
# What runs:
# 1. Ollama with Gemma4 + qwen3:8b
# 2. Gemma4 brain (reads project, creates tasks every 5min)
# 3. 17-agent swarm daemon (executes tasks, polls every 20s)
# 4. Health monitor (auto-restarts crashed processes, Telegram alerts)
#
# Usage:
#   ssh user@VM_IP
#   cd /opt/volaura
#   ./infra/start.sh
#
# Prerequisites:
#   - Ubuntu 22.04+ with NVIDIA GPU drivers
#   - Python 3.10+
#   - Ollama installed: curl -fsSL https://ollama.ai/install.sh | sh
#   - VOLAURA repo cloned: git clone ... /opt/volaura
#   - .env file at apps/api/.env with API keys
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_PATH="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${VOLAURA_LOGS:-/var/log/volaura}"

echo "=========================================="
echo "VOLAURA Organism — Starting"
echo "Project: $PROJECT_PATH"
echo "Logs:    $LOG_DIR"
echo "=========================================="

mkdir -p "$LOG_DIR"
mkdir -p "$PROJECT_PATH/memory/atlas/work-queue/pending"
mkdir -p "$PROJECT_PATH/memory/atlas/work-queue/done"
mkdir -p "$PROJECT_PATH/memory/atlas/episodes"
mkdir -p "$PROJECT_PATH/memory/atlas/semantic"

# ── Step 1: Ollama ──────────────────────────────────────────────────────────
if ! pgrep -x "ollama" > /dev/null; then
    echo "[1/4] Starting Ollama..."
    nohup ollama serve > "$LOG_DIR/ollama.log" 2>&1 &
    sleep 5
    ollama list | grep -q "gemma4" || { echo "Pulling Gemma4..."; ollama pull gemma4; }
    ollama list | grep -q "qwen3:8b" || { echo "Pulling qwen3:8b..."; ollama pull qwen3:8b; }
    echo "[1/4] Ollama ready"
else
    echo "[1/4] Ollama already running"
fi

# ── Step 2: Install Python deps ─────────────────────────────────────────────
echo "[2/4] Checking Python deps..."
cd "$PROJECT_PATH"
pip3 install --quiet openai google-genai groq posthog 2>/dev/null || true

# ── Step 3: Start Brain + Daemon ─────────────────────────────────────────────
echo "[3/4] Starting Brain + Daemon..."

pkill -f "gemma4_brain.py" 2>/dev/null || true
pkill -f "atlas_swarm_daemon.py" 2>/dev/null || true
sleep 1

cd "$PROJECT_PATH"
nohup python3 scripts/gemma4_brain.py >> "$LOG_DIR/brain.log" 2>&1 &
BRAIN_PID=$!
echo "  Brain PID: $BRAIN_PID"

nohup python3 scripts/atlas_swarm_daemon.py >> "$LOG_DIR/daemon.log" 2>&1 &
DAEMON_PID=$!
echo "  Daemon PID: $DAEMON_PID"

echo "$BRAIN_PID" > "$LOG_DIR/brain.pid"
echo "$DAEMON_PID" > "$LOG_DIR/daemon.pid"

# ── Step 4: Health monitor loop ──────────────────────────────────────────────
echo "[4/4] Health monitor active"
echo ""
echo "=========================================="
echo "VOLAURA running!"
echo "  Brain:  tail -f $LOG_DIR/brain.log"
echo "  Daemon: tail -f $LOG_DIR/daemon.log"
echo "=========================================="

# Load Telegram credentials from .env
TELEGRAM_BOT_TOKEN=""
CEO_CHAT_ID=""
ENV_FILE="$PROJECT_PATH/apps/api/.env"
if [ -f "$ENV_FILE" ]; then
    TELEGRAM_BOT_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" "$ENV_FILE" | cut -d= -f2 | tr -d "'" | tr -d '"')
    CEO_CHAT_ID=$(grep "^TELEGRAM_CEO_CHAT_ID=" "$ENV_FILE" | cut -d= -f2 | tr -d "'" | tr -d '"')
fi

HEALTH_INTERVAL=300  # 5 minutes

while true; do
    BRAIN_ALIVE=$(pgrep -f "gemma4_brain" | wc -l)
    DAEMON_ALIVE=$(pgrep -f "atlas_swarm_daemon" | wc -l)

    # Auto-restart crashed processes
    if [ "$BRAIN_ALIVE" -eq 0 ]; then
        echo "[$(date '+%H:%M')] Brain crashed, restarting..."
        cd "$PROJECT_PATH"
        nohup python3 scripts/gemma4_brain.py >> "$LOG_DIR/brain.log" 2>&1 &
    fi

    if [ "$DAEMON_ALIVE" -eq 0 ]; then
        echo "[$(date '+%H:%M')] Daemon crashed, restarting..."
        cd "$PROJECT_PATH"
        nohup python3 scripts/atlas_swarm_daemon.py >> "$LOG_DIR/daemon.log" 2>&1 &
    fi

    # Telegram heartbeat (if configured)
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$CEO_CHAT_ID" ]; then
        PENDING=$(find "$PROJECT_PATH/memory/atlas/work-queue/pending" -name "*.md" 2>/dev/null | wc -l)
        DONE=$(find "$PROJECT_PATH/memory/atlas/work-queue/done" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)

        # Only send heartbeat every 30 minutes (6 cycles)
        CYCLE_COUNT=$((${CYCLE_COUNT:-0} + 1))
        if [ $((CYCLE_COUNT % 6)) -eq 0 ]; then
            MSG="VOLAURA $(date '+%H:%M') — Brain: $([ $BRAIN_ALIVE -gt 0 ] && echo OK || echo DOWN), Daemon: $([ $DAEMON_ALIVE -gt 0 ] && echo OK || echo DOWN), Queue: ${PENDING}p/${DONE}d"
            curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
                -d "chat_id=${CEO_CHAT_ID}" -d "text=${MSG}" > /dev/null 2>&1 || true
        fi
    fi

    sleep $HEALTH_INTERVAL
done
