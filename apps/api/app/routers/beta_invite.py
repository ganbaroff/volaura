"""Beta invite code validation endpoint.

Validates codes server-side so the allowlist is never exposed to the client.
Valid codes are defined via INVITE_CODES env var (comma-separated) or the
legacy BETA_INVITE_CODE single-code setting.

Route: POST /api/invite/validate
Body:  { "code": "BETA_01" }
Response: { "valid": true } or { "valid": false }
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, field_validator

from app.middleware.rate_limit import limiter

router = APIRouter(prefix="/invite", tags=["Beta Invite"])

# Rate limit: 10/minute per IP — prevents brute-force enumeration of codes
RATE_VALIDATE = "10/minute"

# ── Default allowlist — override with INVITE_CODES env var (comma-separated) ──
# BETA_01..BETA_30 cover warm personal invites (30 slots)
# ORG_01..ORG_05 cover early org pilots
# OPEN is the public LinkedIn CTA code (no personal code required)
_DEFAULT_CODES: frozenset[str] = frozenset(
    [f"BETA_{i:02d}" for i in range(1, 31)]
    + [f"ORG_{i:02d}" for i in range(1, 6)]
    + ["OPEN"]
)


def _load_valid_codes() -> frozenset[str]:
    """Load valid codes from env at request time so Railway env changes are reflected
    without restart. Merges INVITE_CODES list with the legacy BETA_INVITE_CODE setting."""
    codes: set[str] = set()

    raw = os.environ.get("INVITE_CODES", "")
    if raw.strip():
        for part in raw.split(","):
            stripped = part.strip().upper()
            if stripped:
                codes.add(stripped)

    # Legacy single-code support (BETA_INVITE_CODE setting in config.py)
    legacy = os.environ.get("BETA_INVITE_CODE", "").strip().upper()
    if legacy:
        codes.add(legacy)

    # If neither env var is set, use the default allowlist
    return frozenset(codes) if codes else _DEFAULT_CODES


class ValidateCodeRequest(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def normalise(cls, v: str) -> str:
        return v.strip().upper()


class ValidateCodeResponse(BaseModel):
    valid: bool


@router.post("/validate", response_model=ValidateCodeResponse)
@limiter.limit(RATE_VALIDATE)
async def validate_invite_code(
    request: Request,
    body: ValidateCodeRequest,
) -> JSONResponse:
    """Check whether an invite code is valid.

    Returns { "valid": true/false } only — no error codes, no hints about
    which codes exist. Brute-force is rate-limited to 10/minute per IP.
    """
    valid_codes = _load_valid_codes()
    is_valid = body.code in valid_codes

    logger.info(
        "Invite code validation",
        code_prefix=body.code[:4] if body.code else "",
        valid=is_valid,
    )

    return JSONResponse(
        content={"data": {"valid": is_valid}, "meta": {}},
    )
