"""ZEUS Gateway router — inbound bridge for Python swarm proposals.

Receives HIGH/CRITICAL findings from autonomous_run.py (_notify_zeus_gateway)
and appends them to memory/swarm/proposals.json for CTO review.

Auth: X-Gateway-Secret header must match settings.gateway_secret.
Endpoints:
  GET  /api/zeus/health   — healthcheck
  POST /api/zeus/proposal — receive proposal from Python swarm
"""

import json
import pathlib

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import settings

router = APIRouter(prefix="/api/atlas", tags=["atlas-gateway"])

# Resolve relative to repo root (works on Railway — cwd is /app)
_PROPOSALS_PATH = pathlib.Path("memory/swarm/proposals.json")


@router.get("/health")
async def gateway_health() -> dict:
    return {"status": "ok", "service": "atlas-gateway"}


@router.post("/proposal")
async def receive_proposal(
    request: Request,
    x_gateway_secret: str = Header(None),
) -> dict:
    if not settings.gateway_secret:
        raise HTTPException(status_code=503, detail="Gateway secret not configured")
    if x_gateway_secret != settings.gateway_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    body = await request.json()

    proposals: list = []
    if _PROPOSALS_PATH.exists():
        try:
            proposals = json.loads(_PROPOSALS_PATH.read_text(encoding="utf-8"))
            if not isinstance(proposals, list):
                proposals = []
        except (json.JSONDecodeError, OSError):
            proposals = []

    proposals.append(body)

    try:
        _PROPOSALS_PATH.write_text(
            json.dumps(proposals, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        # Railway read-only filesystem — log and continue (non-blocking)
        pass

    return {"status": "queued", "total": len(proposals)}
