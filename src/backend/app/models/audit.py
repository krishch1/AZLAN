"""Audit model representing one execution of an AZLAN audit."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from backend.app.db.base import Base
from backend.app.models.enums import AuditStatus

if TYPE_CHECKING:
    from backend.app.models.audit_configuration import AuditConfiguration
    from backend.app.models.audit_event import AuditEvent
    from backend.app.models.audit_job import AuditJob
    from backend.app.models.target import Target


class Audit(Base):
    """Represents one execution of an AZLAN audit.

    Attributes:
        id: UUID primary key
        target_id: Foreign key to Target
        status: Current lifecycle status (AuditStatus enum)
        created_at: When the audit was created
        started_at: When the audit started processing (nullable)
        completed_at: When the audit completed successfully (nullable)
        cancelled_at: When the audit was cancelled (nullable)
        failure_info: Structured failure information (nullable)
        updated_at: Last timestamp update for lifecycle tracking
    """

    __tablename__ = "audits"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
        comment="Unique identifier for the audit",
    )
    target_id = Column(
        UUID(as_uuid=True),
        ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The target being audited",
    )
    status = Column(
        String(50),
        nullable=False,
        default=AuditStatus.CREATED.value,
        server_default=AuditStatus.CREATED.value,
        index=True,
        comment="Current lifecycle status",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default="CURRENT_TIMESTAMP",
        comment="When the audit was created",
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the audit started processing",
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the audit completed successfully",
    )
    cancelled_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the audit was cancelled",
    )
    failure_info = Column(
        Text,
        nullable=True,
        comment="Structured failure information (JSON-encoded) if the audit failed",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default="CURRENT_TIMESTAMP",
        onupdate=lambda: datetime.now(UTC),
        comment="Last timestamp update for lifecycle tracking",
    )

    # Relationships
    target: Mapped["Target"] = relationship(
        "Target",
        back_populates="audits",
    )
    configuration: Mapped[Optional["AuditConfiguration"]] = relationship(
        "AuditConfiguration",
        back_populates="audit",
        uselist=False,
    )
    events: Mapped[list["AuditEvent"]] = relationship(
        "AuditEvent",
        back_populates="audit",
        cascade="all, delete-orphan",
        order_by="AuditEvent.timestamp",
    )
    jobs: Mapped[list["AuditJob"]] = relationship(
        "AuditJob",
        back_populates="audit",
        cascade="all, delete-orphan",
        order_by="AuditJob.created_at",
    )

    def __repr__(self) -> str:
        return f"<Audit(id={self.id}, status={self.status})>"