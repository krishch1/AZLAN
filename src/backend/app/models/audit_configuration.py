"""AuditConfiguration model for per-audit configuration."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from backend.app.db.base import Base
from backend.app.models.enums import AuditMode

if TYPE_CHECKING:
    from backend.app.models.audit import Audit


class AuditConfiguration(Base):
    """Per-audit configuration.

    Supports:
    - audit mode (quick, standard, deep, exhaustive)
    - crawl/discovery configuration
    - scope configuration (include/exclude patterns)
    - authentication configuration placeholder (SECURE: no plaintext credentials)
    - active testing configuration
    - resource/request limits

    SECURITY: Authentication/session information is sensitive.
    This model stores only a placeholder/reference structure for auth configuration.
    Actual credentials must be provided at runtime via a secure secret-handling mechanism
    (e.g., environment variables, secrets manager, or request headers) and NEVER persisted
    in plaintext in the database.
    """

    __tablename__ = "audit_configurations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
        comment="Unique identifier for the audit configuration",
    )
    audit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="The audit this configuration belongs to",
    )
    mode = Column(
        String(50),
        nullable=False,
        default=AuditMode.STANDARD.value,
        server_default=AuditMode.STANDARD.value,
        comment="Audit execution mode (quick, standard, deep, exhaustive)",
    )

    # Crawl/discovery configuration
    max_pages = Column(
        Text,
        nullable=True,
        comment="JSON-encoded crawl limits (e.g., max_pages, max_depth)",
    )
    crawl_config = Column(
        JSON,
        nullable=True,
        comment="Structured crawl/discovery configuration",
    )

    # Scope configuration
    scope_config = Column(
        JSON,
        nullable=True,
        comment="Scope configuration: include/exclude patterns, allowed_domains, etc.",
    )

    # Authentication configuration placeholder
    # SECURITY: This field stores ONLY a structural placeholder.
    # Actual credentials/secrets are NOT stored here.
    # Expected shape: {"type": "none" | "basic" | "bearer" | "cookie" | "custom",
    #                  "reference_id": "<secret-reference>"}  where reference_id
    # points to a secure secret store, not the secret itself.
    # The default is {"type": "none"} indicating no authentication.
    auth_config = Column(
        JSON,
        nullable=False,
        default=lambda: {"type": "none"},
        server_default='{"type": "none"}',
        comment="SAFE PLACEHOLDER for authentication configuration. "
        "Never store plaintext credentials. Use secret references.",
    )

    # Active testing configuration
    testing_config = Column(
        JSON,
        nullable=True,
        comment="Active testing configuration (which checks to run, etc.)",
    )

    # Resource/request limits
    limits_config = Column(
        JSON,
        nullable=True,
        comment="Resource and request limits (timeouts, concurrency, etc.)",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default="CURRENT_TIMESTAMP",
        comment="When the configuration was created",
    )

    # Relationship back to Audit - explicitly specify foreign_keys to resolve ambiguity
    audit: Mapped[Optional["Audit"]] = relationship(
        "Audit",
        back_populates="configuration",
        uselist=False,
        foreign_keys="AuditConfiguration.audit_id",
    )

    def __repr__(self) -> str:
        return f"<AuditConfiguration(id={self.id}, audit_id={self.audit_id}, mode={self.mode})>"