"""Bulk invite endpoints for organizations.

Allows org owners to upload a CSV of volunteer emails to invite.
Max 500 rows per upload, processed in batches of 50.
Returns per-row audit log with created/duplicate/error status.

Security mitigations (from agent review):
- File size limit: 1 MB max
- Formula injection: sanitized in Pydantic validators
- Auth boundary: org owner verified BEFORE file parsing
- Rate limit: 2/minute (RATE_BULK_INVITE)
- Info disclosure: generic errors, no existing user details leaked
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
from loguru import logger

from app.deps import CurrentUserId, SupabaseAdmin
from app.middleware.rate_limit import limiter
from app.schemas.invite import (
    BulkInviteResponse,
    InviteListResponse,
    InviteRowInput,
    InviteRowResult,
)

router = APIRouter(prefix="/organizations", tags=["Organization Invites"])

# Strict rate limit for bulk operations
RATE_BULK_INVITE = "2/minute"

# Limits
MAX_FILE_SIZE = 1_048_576  # 1 MB
MAX_ROWS = 500
BATCH_SIZE = 50


@router.post("/{org_id}/invites/bulk", response_model=BulkInviteResponse, status_code=207)
@limiter.limit(RATE_BULK_INVITE)
async def bulk_invite_volunteers(
    request: Request,
    org_id: str,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    file: UploadFile = File(...),
) -> JSONResponse:
    """Upload a CSV of volunteers to invite to the platform.

    CSV format: email (required), display_name, phone, skills (pipe-delimited)
    Max 500 rows. Duplicates within file and against existing invites are skipped.
    Returns HTTP 207 with per-row audit log.
    """
    # ── Auth: verify org ownership BEFORE parsing file ──
    _validate_uuid(org_id, "org_id")

    org_result = await db_admin.table("organizations").select("id, owner_id, name").eq("id", org_id).single().execute()
    if not org_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "ORG_NOT_FOUND", "message": "Organization not found"},
        )
    if org_result.data["owner_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_ORG_OWNER", "message": "Only the organization owner can send invites"},
        )

    org_name = org_result.data["name"]

    # ── File size guard ──
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail={"code": "FILE_TOO_LARGE", "message": f"CSV file must be under {MAX_FILE_SIZE // 1024}KB"},
        )

    # ── Parse CSV ──
    try:
        text = content.decode("utf-8-sig")  # Handle BOM from Excel
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_ENCODING", "message": "CSV must be UTF-8 encoded"},
        )

    reader = csv.DictReader(io.StringIO(text))

    # Validate required column
    if not reader.fieldnames or "email" not in [f.strip().lower() for f in reader.fieldnames]:
        raise HTTPException(
            status_code=422,
            detail={"code": "MISSING_COLUMN", "message": "CSV must have an 'email' column"},
        )

    # ── Validate rows ──
    rows: list[tuple[int, InviteRowInput]] = []
    results: list[InviteRowResult] = []
    seen_emails: set[str] = set()

    for i, raw_row in enumerate(reader, start=2):  # row 1 = header
        if i - 1 > MAX_ROWS:
            results.append(InviteRowResult(
                row=i, email=raw_row.get("email", "?"), status="error",
                error=f"Exceeds max {MAX_ROWS} rows",
            ))
            break

        # Normalize column names (strip whitespace, lowercase)
        normalized = {k.strip().lower(): v for k, v in raw_row.items() if k}

        try:
            row = InviteRowInput(
                email=normalized.get("email", ""),
                display_name=normalized.get("display_name") or normalized.get("name"),
                phone=normalized.get("phone"),
                skills=normalized.get("skills"),
            )
        except Exception as e:
            results.append(InviteRowResult(
                row=i, email=normalized.get("email", "?"), status="error",
                error=str(e).split("\n")[0][:200],  # Truncate, don't leak internals
            ))
            continue

        # In-file duplicate check
        if row.email in seen_emails:
            results.append(InviteRowResult(
                row=i, email=row.email, status="duplicate",
                error="Duplicate within this file",
            ))
            continue

        seen_emails.add(row.email)
        rows.append((i, row))

    if not rows and not results:
        raise HTTPException(
            status_code=422,
            detail={"code": "EMPTY_CSV", "message": "CSV has no data rows"},
        )

    # ── Check existing invites in DB (manual dedup instead of upsert) ──
    emails_to_check = [row.email for _, row in rows]

    existing_invites: set[str] = set()
    # Query in chunks to avoid URL length limits
    for chunk_start in range(0, len(emails_to_check), BATCH_SIZE):
        chunk = emails_to_check[chunk_start:chunk_start + BATCH_SIZE]
        existing_result = await db_admin.table("organization_invites").select("email").eq(
            "org_id", org_id
        ).neq("status", "expired").in_("email", chunk).execute()
        for inv in (existing_result.data or []):
            existing_invites.add(inv["email"])

    # ── Batch insert new invites ──
    batch_id = str(uuid.uuid4())
    created_count = 0
    duplicate_count = 0
    error_count = len([r for r in results if r.status == "error"])

    # Split into new vs duplicate
    new_rows: list[tuple[int, InviteRowInput]] = []
    for row_num, row in rows:
        if row.email in existing_invites:
            results.append(InviteRowResult(
                row=row_num, email=row.email, status="duplicate",
                error="Already invited by this organization",
            ))
            duplicate_count += 1
        else:
            new_rows.append((row_num, row))

    # Insert in batches of BATCH_SIZE
    for batch_start in range(0, len(new_rows), BATCH_SIZE):
        batch = new_rows[batch_start:batch_start + BATCH_SIZE]
        insert_data = []
        for row_num, row in batch:
            insert_data.append({
                "id": str(uuid.uuid4()),
                "org_id": org_id,
                "invited_by": user_id,
                "email": row.email,
                "display_name": row.display_name,
                "phone": row.phone,
                "skills": row.to_skills_list(),
                "status": "pending",
                "batch_id": batch_id,
            })

        try:
            await db_admin.table("organization_invites").insert(insert_data).execute()
            for row_num, row in batch:
                results.append(InviteRowResult(
                    row=row_num, email=row.email, status="created",
                ))
                created_count += 1
        except Exception as e:
            logger.error(
                "Batch insert failed",
                batch_start=batch_start,
                batch_size=len(batch),
                org_id=org_id,
                error=str(e),
            )
            # If batch fails, mark all rows in batch as error
            for row_num, row in batch:
                results.append(InviteRowResult(
                    row=row_num, email=row.email, status="error",
                    error="Database insert failed",
                ))
                error_count += 1

    # Sort results by row number for readability
    results.sort(key=lambda r: r.row)

    # Count in-file duplicates
    duplicate_count += len([r for r in results if r.status == "duplicate"])
    # Avoid double-counting: recalculate from results
    created_count = len([r for r in results if r.status == "created"])
    duplicate_count = len([r for r in results if r.status == "duplicate"])
    error_count = len([r for r in results if r.status == "error"])

    logger.info(
        "Bulk invite completed",
        org_id=org_id,
        org_name=org_name,
        batch_id=batch_id,
        total=len(results),
        created=created_count,
        duplicates=duplicate_count,
        errors=error_count,
    )

    response = BulkInviteResponse(
        batch_id=batch_id,
        total=len(results),
        created=created_count,
        duplicates=duplicate_count,
        errors=error_count,
        results=results,
    )

    return JSONResponse(
        status_code=207,
        content={"data": response.model_dump(), "meta": {}},
    )


@router.get("/{org_id}/invites", response_model=list[InviteListResponse])
@limiter.limit("30/minute")
async def list_invites(
    request: Request,
    org_id: str,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    status: str | None = None,
    batch_id: str | None = None,
) -> list[InviteListResponse]:
    """List invites for an organization, optionally filtered by status or batch."""
    _validate_uuid(org_id, "org_id")

    # Verify ownership
    org_result = await db_admin.table("organizations").select("id, owner_id").eq("id", org_id).single().execute()
    if not org_result.data or org_result.data["owner_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_ORG_OWNER", "message": "Only the organization owner can view invites"},
        )

    query = db_admin.table("organization_invites").select("*").eq("org_id", org_id).order("created_at", desc=True).limit(200)

    if status:
        if status not in ("pending", "accepted", "declined", "expired"):
            raise HTTPException(status_code=422, detail={"code": "INVALID_STATUS", "message": "Invalid status filter"})
        query = query.eq("status", status)

    if batch_id:
        _validate_uuid(batch_id, "batch_id")
        query = query.eq("batch_id", batch_id)

    result = await query.execute()
    return result.data or []


@router.get("/{org_id}/invites/template")
async def download_invite_template() -> JSONResponse:
    """Return the expected CSV template for bulk invite."""
    return JSONResponse(
        content={
            "data": {
                "columns": ["email", "display_name", "phone", "skills"],
                "required": ["email"],
                "example_row": {
                    "email": "ahmed@example.com",
                    "display_name": "Ahmed Mammadov",
                    "phone": "+994501234567",
                    "skills": "leadership|event_coordination|english",
                },
                "notes": [
                    "email is required, all other columns are optional",
                    "skills should be pipe-delimited (|)",
                    "max 500 rows per upload",
                    "file must be UTF-8 encoded CSV",
                ],
            },
            "meta": {},
        }
    )


def _validate_uuid(value: str, field_name: str) -> None:
    """Validate UUID format to prevent injection."""
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_UUID", "message": f"Invalid {field_name} format"},
        )
