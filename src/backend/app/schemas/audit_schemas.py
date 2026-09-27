"""Pydantic schemas for Audit Creation and Retrieval input/output."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from backend.app.models.enums import AuditMode, AuditStatus


class AuditCreateRequest(BaseModel):
    """Structured input request for creating an audit."""

    target_url: str = Field(..., description="Target URL for auditing", min_length=1)
    mode: AuditMode = Field(default=AuditMode.STANDARD, description="Audit execution mode")
    crawl_config: dict[str, Any] | None = Field(
        default=None, description="Crawl and discovery configuration"
    )
    scope_config: dict[str, Any] | None = Field(
        default=None, description="Scope configuration (include/exclude rules)"
    )
    auth_config: dict[str, Any] = Field(
        default_factory=lambda: {"type": "none"},
        description="Authentication configuration placeholder. Never include secrets.",
    )
    testing_config: dict[str, Any] | None = Field(
        default=None, description="Active testing configuration"
    )
    limits_config: dict[str, Any] | None = Field(
        default=None, description="Resource and request limits"
    )

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, v: str) -> str:
        """Basic syntactic URL validation.

        Preserves the target URL as untrusted input.
        Does NOT perform DNS resolution or HTTP requests.
        """
        v = v.strip()
        if not v:
            raise ValueError("target_url must not be empty")
        
        # Check scheme exists and is http/https
        if not v.startswith(("http://", "https://")):
            raise ValueError("target_url must start with http:// or https://")

        # Validate with HttpUrl
        try:
            HttpUrl(v)
        except Exception as err:
            raise ValueError(f"Invalid target URL syntax: {err}") from err

        return v

    @field_validator("auth_config")
    @classmethod
    def validate_auth_config_no_secrets(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure auth_config does not contain sensitive authentication material in plaintext."""
        forbidden_keys = {
            "password",
            "secret",
            "token",
            "api_key",
            "apikey",
            "private_key",
            "credential",
            "authorization",
            "cookie",
            "session_id",
        }
        lowercased_keys = {str(k).lower() for k in v}
        found_sensitive = forbidden_keys.intersection(lowercased_keys)
        if found_sensitive:
            raise ValueError(
                f"auth_config contains forbidden key(s): {', '.join(found_sensitive)}. "
                "Do not store sensitive authentication material in plaintext. "
                "Use reference_id pointers instead."
            )
        return v


class TargetResponse(BaseModel):
    """Target presentation schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    normalized_url: str | None
    created_at: datetime


class AuditConfigurationResponse(BaseModel):
    """AuditConfiguration presentation schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mode: str
    max_pages: str | None
    crawl_config: dict[str, Any] | None
    scope_config: dict[str, Any] | None
    auth_config: dict[str, Any]
    testing_config: dict[str, Any] | None
    limits_config: dict[str, Any] | None
    created_at: datetime


class AuditEventResponse(BaseModel):
    """AuditEvent presentation schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audit_id: UUID
    event_type: str
    timestamp: datetime
    metadata: dict[str, Any] | None = Field(None, alias="metadata_")


class AuditResponse(BaseModel):
    """Clean domain representation of an Audit suitable for future API response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    target_id: UUID
    status: AuditStatus
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    failure_info: str | None
    updated_at: datetime
    target: TargetResponse | None = None
    configuration: AuditConfigurationResponse | None = None
    events: list[AuditEventResponse] = Field(default_factory=list)
