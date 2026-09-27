"""Target model representing the website being audited."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.audit import Audit


class Target(Base):
    """Represents the website being audited.

    At minimum stores:
    - UUID primary key
    - target URL
    - normalized/canonical representation if required by the architecture
    - creation timestamp

    Design note: One audit has a clearly defined target association.
    Target URLs are treated as untrusted data; no validation logic is implemented here.
    """

    __tablename__ = "targets"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
        comment="Unique identifier for the target",
    )
    url = Column(
        Text,
        nullable=False,
        comment="Original target URL provided by the user",
    )
    normalized_url = Column(
        Text,
        nullable=True,
        comment="Canonical/normalized representation of the URL (if computed)",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default="CURRENT_TIMESTAMP",
        comment="When the target was registered",
    )

    # Relationship back to Audit
    audits: Mapped[list["Audit"]] = relationship(
        "Audit",
        back_populates="target",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Target(id={self.id}, url={self.url!r})>"