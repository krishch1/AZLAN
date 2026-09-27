"""AuditEvent model for lifecycle/event history."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship

from backend.app.db.base import Base


class AuditEvent(Base):
    """Records lifecycle and informational events for an audit.

    Attributes:
        id: UUID primary key
        audit_id: Foreign key to Audit
        event_type: Type of event (EventType enum)
        timestamp: When the event occurred
        metadata: Structured event metadata (JSONB)

    SECURITY: No secrets are stored in event metadata.
    Event metadata is stored in PostgreSQL JSONB for structured querying.
    """

    __tablename__ = "audit_events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
        comment="Unique identifier for the event",
    )
    audit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The audit this event belongs to",
    )
    event_type = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of event (from EventType enum)",
    )
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default="CURRENT_TIMESTAMP",
        index=True,
        comment="When the event occurred",
    )
    metadata_ = Column(
        "metadata",
        JSONB,
        nullable=True,
        comment="Structured event metadata (JSONB). Never store secrets here.",
    )

    # Composite index for retrieving events for a specific audit in chronological order
    __table_args__ = (
        Index("ix_audit_events_audit_created", "audit_id", "timestamp"),
    )

    # Relationship back to Audit
    audit: Mapped["Audit"] = relationship(  # noqa: F821
        "Audit",
        back_populates="events",
    )

    def __repr__(self) -> str:
        return f"<AuditEvent(id={self.id}, audit_id={self.audit_id}, event_type={self.event_type})>"