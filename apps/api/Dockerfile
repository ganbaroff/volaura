FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# 2026-04-19: NOTE — the telegram_gate (packages/swarm/telegram_gate.py) and
# silence-file (memory/atlas/telegram-silenced-until.txt) are NOT copied in
# this Dockerfile because its build context is `apps/api/`, which cannot
# reach sibling directories via Docker COPY. The repo-root Dockerfile.railway
# is the one active on Railway per root railway.toml, and it DOES ship them.
# If this Dockerfile ever becomes the active one, move the build to repo root
# (or inline a trimmed telegram_gate under apps/api/app/shared/).

# Railway injects PORT at runtime
ENV PORT=8000
EXPOSE $PORT

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
# cache-bust: Fri Apr 04 15:52:00 AST 2026 — trimmed deps (crewai/fal removed)
