"""Pydantic v2 schemas for BrandedBy — AI Twin video platform.

Sprint B1: Foundation CRUD for AI Twins + generation jobs.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# --- AI Twin ---

TwinStatus = Literal["draft", "active", "suspended"]
GenerationType = Literal["video", "audio", "text_chat"]
GenerationStatus = Literal["queued", "processing", "completed", "failed"]


class AITwinCreate(BaseModel):
    """POST /api/brandedby/twins — create user's AI Twin."""

    model_config = ConfigDict(str_strip_whitespace=True)

    display_name: str = Field(min_length=1, max_length=100)
    tagline: str | None = Field(default=None, max_length=200)
    photo_url: str | None = None

    @field_validator("display_name")
    @classmethod
    def clean_display_name(cls, v: str) -> str:
        return " ".join(v.split())  # collapse whitespace


class AITwinUpdate(BaseModel):
    """PATCH /api/brandedby/twins/{id} — update AI Twin."""

    model_config = ConfigDict(str_strip_whitespace=True)

    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    tagline: str | None = Field(default=None, max_length=200)
    photo_url: str | None = None
    status: TwinStatus | None = None


class AITwinOut(BaseModel):
    """Response model for an AI Twin."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    display_name: str
    tagline: str | None = None
    photo_url: str | None = None
    voice_id: str | None = None
    personality_prompt: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


# --- Generation ---


class GenerationCreate(BaseModel):
    """POST /api/brandedby/generations — request a new generation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    twin_id: UUID
    gen_type: GenerationType = "video"
    input_text: str = Field(min_length=1, max_length=2000)
    skip_queue: bool = Field(
        default=False,
        description="If true, spend crystals to skip the queue",
    )

    @field_validator("input_text")
    @classmethod
    def validate_script(cls, v: str) -> str:
        if len(v.split()) < 3:
            msg = "Script must be at least 3 words"
            raise ValueError(msg)
        return v


class GenerationOut(BaseModel):
    """Response model for a generation job."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    twin_id: UUID
    user_id: UUID
    gen_type: str
    input_text: str
    output_url: str | None = None
    thumbnail_url: str | None = None
    status: str
    error_message: str | None = None
    queue_position: int | None = None
    crystal_cost: int
    duration_seconds: int | None = None
    processing_started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
