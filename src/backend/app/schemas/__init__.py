"""Pydantic schemas for the audit lifecycle service.

These schemas are intentionally decoupled from FastAPI request/response objects
so that the domain service layer can be tested and reused independently.
"""

from __future__ import annotations

from backend.app.schemas.audit_schemas import (
    AuditConfigurationResponse,
    AuditCreateRequest,
    AuditEventResponse,
    AuditResponse,
    TargetResponse,
)

__all__ = [
    "AuditConfigurationResponse",
    "AuditCreateRequest",
    "AuditEventResponse",
    "AuditResponse",
    "TargetResponse",
]