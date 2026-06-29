"""CV upload and claim extraction endpoints.

Sprint 1 of the CV Truth Machine (ADR-017 Layer 1).

POST /api/cv/upload — upload PDF/DOCX, extract text, extract claims.
GET  /api/cv/{cv_id} — retrieve previously extracted claims.

Auth required (P0d invariant — anonymous JWTs rejected in deps.py).
Original file is NOT stored (GDPR data minimization — text only).
"""

from __future__ import annotations

import hashlib
import uuid

from fastapi import APIRouter, HTTPException, Request, UploadFile
from loguru import logger

from app.deps import CurrentUserId, SupabaseAdmin
from app.middleware.rate_limit import limiter
from app.schemas.cv import ClaimItem, CVUploadResponse, ExtractionMeta
from app.services.claim_extractor import extract_claims
from app.services.cv_parser import extract_text

router = APIRouter(prefix="/cv", tags=["CV Truth Verification"])

RATE_UPLOAD = "5/hour"
RATE_READ = "30/minute"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/upload", response_model=CVUploadResponse, status_code=201)
@limiter.limit(RATE_UPLOAD)
async def upload_cv(
    request: Request,
    file: UploadFile,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> CVUploadResponse:
    """Upload a CV (PDF/DOCX), extract text, extract verifiable claims.

    The original file is NOT stored — only extracted text and claims.
    Claims can later be used to generate experience interview questions.
    """
    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=422, detail={"code": "NO_FILENAME", "message": "File must have a name"})

    lower_name = file.filename.lower()
    if not (lower_name.endswith(".pdf") or lower_name.endswith(".docx")):
        raise HTTPException(
            status_code=422,
            detail={"code": "UNSUPPORTED_FORMAT", "message": "Only PDF and DOCX files are accepted"},
        )

    # Read and validate size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail={"code": "FILE_TOO_LARGE", "message": f"File exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit"},
        )
    if len(file_bytes) == 0:
        raise HTTPException(status_code=422, detail={"code": "EMPTY_FILE", "message": "File is empty"})

    # Extract text
    try:
        cv_text = extract_text(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail={"code": "PARSE_ERROR", "message": str(e)}) from e

    # Hash for dedup (text hash, not file hash — same text from different formats = same hash)
    text_hash = hashlib.sha256(cv_text.encode("utf-8")).hexdigest()[:16]

    # Check for existing upload with same text hash (dedup)
    existing = (
        await db_admin.table("cv_intake")
        .select("id, claims")
        .eq("user_id", user_id)
        .eq("file_hash", text_hash)
        .maybe_single()
        .execute()
    )
    if existing and existing.data:
        logger.info("CV dedup hit", user_id=user_id, hash=text_hash)
        claims_data = existing.data["claims"] or {"claims": [], "meta": {}}
        claims = [ClaimItem(**c) for c in claims_data.get("claims", [])]
        meta_raw = claims_data.get("meta", {})
        meta = ExtractionMeta(
            total_claims=meta_raw.get("total_claims", len(claims)),
            extraction_model=meta_raw.get("extraction_model", "cached"),
            extraction_time_ms=meta_raw.get("extraction_time_ms", 0),
        )
        return CVUploadResponse(
            cv_id=existing.data["id"],
            filename=file.filename,
            text_length=len(cv_text),
            claims=claims,
            meta=meta,
        )

    # Extract claims via LLM
    try:
        extraction = await extract_claims(cv_text)
    except ValueError as e:
        logger.error("Claim extraction failed", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=502,
            detail={"code": "EXTRACTION_FAILED", "message": "Could not extract claims from CV. Try again."},
        ) from e

    # Store in cv_intake (text + claims, NOT original file)
    cv_id = str(uuid.uuid4())
    insert_result = (
        await db_admin.table("cv_intake")
        .insert(
            {
                "id": cv_id,
                "user_id": user_id,
                "original_filename": file.filename[:255],
                "file_hash": text_hash,
                "cv_text": cv_text[:50000],  # cap at 50k chars
                "claims": extraction.model_dump(),
                "status": "extracted",
            }
        )
        .execute()
    )
    if not insert_result.data:
        raise HTTPException(status_code=500, detail={"code": "STORE_FAILED", "message": "Could not store CV data"})

    logger.info(
        "CV uploaded and claims extracted",
        cv_id=cv_id,
        user_id=user_id,
        claims=extraction.meta.total_claims,
        model=extraction.meta.extraction_model,
    )

    return CVUploadResponse(
        cv_id=cv_id,
        filename=file.filename,
        text_length=len(cv_text),
        claims=extraction.claims,
        meta=extraction.meta,
    )


@router.get("/{cv_id}", response_model=CVUploadResponse)
@limiter.limit(RATE_READ)
async def get_cv_claims(
    request: Request,
    cv_id: str,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> CVUploadResponse:
    """Retrieve previously extracted claims for a CV."""
    result = (
        await db_admin.table("cv_intake")
        .select("id, original_filename, cv_text, claims, user_id")
        .eq("id", cv_id)
        .eq("user_id", user_id)  # owner check
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(status_code=404, detail={"code": "CV_NOT_FOUND", "message": "CV not found"})

    row = result.data
    claims_data = row["claims"] or {"claims": [], "meta": {}}
    claims = [ClaimItem(**c) for c in claims_data.get("claims", [])]
    meta_raw = claims_data.get("meta", {})

    return CVUploadResponse(
        cv_id=row["id"],
        filename=row["original_filename"],
        text_length=len(row.get("cv_text", "")),
        claims=claims,
        meta=ExtractionMeta(
            total_claims=meta_raw.get("total_claims", len(claims)),
            extraction_model=meta_raw.get("extraction_model", "unknown"),
            extraction_time_ms=meta_raw.get("extraction_time_ms", 0),
        ),
    )
