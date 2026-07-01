"""CV upload and claim extraction schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ClaimItem(BaseModel):
    """Single verifiable claim extracted from a CV."""

    id: str = Field(description="Unique claim identifier (claim_001, claim_002, ...)")
    type: str = Field(description="tool | role | project | employer | certification | skill")
    value: str = Field(description="The claimed thing (ClickUp, PMO Manager, COP29, etc.)")
    context: str = Field(description="Surrounding context from CV (role, project, team size)")
    source_line: str = Field(description="Verbatim line or phrase from the CV")
    suggested_competency: str = Field(description="Best-fit VOLAURA competency slug")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence 0-1")


class ExtractionMeta(BaseModel):
    """Metadata about the claim extraction process."""

    total_claims: int
    extraction_model: str
    extraction_time_ms: int


class ClaimExtractionResult(BaseModel):
    """Full result of claim extraction from a CV."""

    claims: list[ClaimItem]
    meta: ExtractionMeta


class CVUploadResponse(BaseModel):
    """Response from POST /api/cv/upload."""

    model_config = ConfigDict(from_attributes=True)

    cv_id: str
    filename: str
    text_length: int
    claims: list[ClaimItem]
    meta: ExtractionMeta
