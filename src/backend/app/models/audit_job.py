"""AuditJob model for the PostgreSQL-backed job queue."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from backend.app.db.base import Base
from backend.app.models.enums import JobStatus

if TYPE_CHECKING:
    from backend.app.models.audit import Audit


class AuditJob(Base):
    """Represents a job in the execution queue.

    The queue record represents execution scheduling.
    The Audit represents the product-level audit.
    Keep those responsibilities separate.
    """

    __tablename__ = "audit_jobs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
        comment="Unique identifier for the job",
    )
    audit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The audit this job belongs to",
    )
    status = Column(
        String(50),
        nullable=False,
        default=JobStatus.QUEUED.value,
        server_default=JobStatus.QUEUED.value,
        index=True,
        comment="Current job queue status",
    )
    available_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default="CURRENT_TIMESTAMP",
        index=True,
        comment="When the job becomes available for claiming",
    )
    claimed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the job was claimed by a worker",
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the job completed successfully",
    )
    failed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the job failed",
    )
    attempt_count = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of claim/attempt cycles",
    )
    worker_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Identity of the worker that claimed this job",
    )
    last_error = Column(
        Text,
        nullable=True,
        comment="Last error message if job failed",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default="CURRENT_TIMESTAMP",
        comment="When the job was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default="CURRENT_TIMESTAMP",
        onupdate=lambda: datetime.now(UTC),
        comment="Last timestamp update",
    )

    # Relationship back to Audit
    audit: Mapped["Audit"] = relationship(
        "Audit",
        back_populates="jobs",
    )

    def __repr__(self) -> str:
        return f"<AuditJob(id={self.id}, audit_id={self.audit_id}, status={self.status})>"