"""EventShift Pydantic schemas (v2).

People-first domain: Event → Department → Area → Unit → People + Metrics.
Each entity is tenant-scoped via org_id (injected by router, not request body).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

# ── Events ────────────────────────────────────────────────────────────────────


EVENT_STATUSES = {"planning", "staffing", "live", "closed", "cancelled"}
UNIT_STATUSES = {"open", "staffed", "live", "closed"}
ASSIGNMENT_ROLES = {"lead", "staff", "backup", "volunteer"}
ASSIGNMENT_STATUSES = {"assigned", "accepted", "declined", "checked_in", "completed", "no_show"}
METRIC_TYPES = {
    "attendance",
    "handover_integrity",
    "incident",
    "incident_closure",
    "reliability_proof",
}


class EventShiftEventCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None
    start_at: datetime
    end_at: datetime
    timezone: str = "Asia/Baku"
    location: dict[str, Any] | None = None
    status: str = "planning"

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in EVENT_STATUSES:
            raise ValueError(f"status must be one of {sorted(EVENT_STATUSES)}")
        return v

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not v or len(v) > 64:
            raise ValueError("slug must be 1-64 chars")
        return v


class EventShiftEventUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    timezone: str | None = None
    location: dict[str, Any] | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in EVENT_STATUSES:
            raise ValueError(f"status must be one of {sorted(EVENT_STATUSES)}")
        return v


class EventShiftEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    org_id: str
    slug: str
    name: str
    description: str | None = None
    start_at: datetime
    end_at: datetime
    timezone: str
    location: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    status: str
    created_at: datetime
    updated_at: datetime


# ── Departments ───────────────────────────────────────────────────────────────


class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None
    color_hex: str | None = None
    lead_user_id: str | None = None
    sort_order: int = 0


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color_hex: str | None = None
    lead_user_id: str | None = None
    sort_order: int | None = None


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    org_id: str
    event_id: str
    name: str
    description: str | None = None
    color_hex: str | None = None
    lead_user_id: str | None = None
    sort_order: int
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


# ── Areas ─────────────────────────────────────────────────────────────────────


class AreaCreate(BaseModel):
    name: str
    description: str | None = None
    location: dict[str, Any] | None = None
    coordinator_user_id: str | None = None


class AreaUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location: dict[str, Any] | None = None
    coordinator_user_id: str | None = None


class AreaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    org_id: str
    department_id: str
    name: str
    description: str | None = None
    location: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    coordinator_user_id: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Units (shifts) ────────────────────────────────────────────────────────────


class UnitCreate(BaseModel):
    name: str
    description: str | None = None
    shift_start: datetime
    shift_end: datetime
    required_headcount: int = 1
    required_skills: list[str] = []
    status: str = "open"

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in UNIT_STATUSES:
            raise ValueError(f"status must be one of {sorted(UNIT_STATUSES)}")
        return v

    @field_validator("required_headcount")
    @classmethod
    def validate_headcount(cls, v: int) -> int:
        if v < 1 or v > 1000:
            raise ValueError("required_headcount must be 1..1000")
        return v


class UnitUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    shift_start: datetime | None = None
    shift_end: datetime | None = None
    required_headcount: int | None = None
    required_skills: list[str] | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in UNIT_STATUSES:
            raise ValueError(f"status must be one of {sorted(UNIT_STATUSES)}")
        return v


class UnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    org_id: str
    area_id: str
    name: str
    description: str | None = None
    shift_start: datetime
    shift_end: datetime
    required_headcount: int
    required_skills: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


# ── Unit assignments (the People) ─────────────────────────────────────────────


class UnitAssignmentCreate(BaseModel):
    user_id: str
    role: str = "staff"
    notes: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ASSIGNMENT_ROLES:
            raise ValueError(f"role must be one of {sorted(ASSIGNMENT_ROLES)}")
        return v


class UnitAssignmentUpdate(BaseModel):
    role: str | None = None
    status: str | None = None
    notes: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is not None and v not in ASSIGNMENT_ROLES:
            raise ValueError(f"role must be one of {sorted(ASSIGNMENT_ROLES)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in ASSIGNMENT_STATUSES:
            raise ValueError(f"status must be one of {sorted(ASSIGNMENT_STATUSES)}")
        return v


class UnitAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    org_id: str
    unit_id: str
    user_id: str
    role: str
    status: str
    notes: str | None = None
    assigned_at: datetime
    updated_at: datetime


# ── Unit metrics (reliability_proof, incident, handover_integrity, …) ─────────


class UnitMetricCreate(BaseModel):
    metric_type: str
    value: float | None = None
    payload: dict[str, Any] | None = None
    recorded_at: datetime | None = None

    @field_validator("metric_type")
    @classmethod
    def validate_metric_type(cls, v: str) -> str:
        if v not in METRIC_TYPES:
            raise ValueError(f"metric_type must be one of {sorted(METRIC_TYPES)}")
        return v


class UnitMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    org_id: str
    unit_id: str
    metric_type: str
    value: float | None = None
    payload: dict[str, Any] | None = None
    recorded_at: datetime
    recorded_by: str | None = None
    created_at: datetime
