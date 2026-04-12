"""Shared Pydantic response schemas."""

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class MessageResponse(BaseModel):
    message: str


class PaginatedMeta(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
