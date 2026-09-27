"""Centralized domain enums for AZLAN audit lifecycle."""

from enum import Enum


class AuditStatus(str, Enum):
    """Lifecycle states for an Audit entity.

    The state model supports the currently defined lifecycle:
    CREATED -> QUEUED -> VALIDATING -> DISCOVERING -> AUDITING -> PROCESSING -> COMPLETED
    plus terminal failure/cancellation states.
    """

    CREATED = "created"
    QUEUED = "queued"
    VALIDATING = "validating"
    DISCOVERING = "discovering"
    AUDITING = "auditing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def is_terminal(cls, status: "AuditStatus") -> bool:
        """Return True if the status is a terminal state (no further transitions expected)."""
        return status in (cls.COMPLETED, cls.FAILED, cls.CANCELLED)

    @classmethod
    def is_active(cls, status: "AuditStatus") -> bool:
        """Return True if the status represents an in-progress audit."""
        return not cls.is_terminal(status)


class AuditMode(str, Enum):
    """High-level audit execution modes."""

    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    EXHAUSTIVE = "exhaustive"


class JobStatus(str, Enum):
    """Lifecycle states for an AuditJob (execution queue item).

    The job queue represents scheduling/execution tracking.
    Separate from AuditStatus which represents the product-level audit.
    """

    QUEUED = "queued"
    CLAIMED = "claimed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def is_terminal(cls, status: "JobStatus") -> bool:
        """Return True if the status is a terminal state."""
        return status in (cls.COMPLETED, cls.FAILED, cls.CANCELLED)


class EventType(str, Enum):
    """Types of lifecycle events that can be recorded for an audit."""

    AUDIT_CREATED = "audit.created"
    AUDIT_QUEUED = "audit.queued"
    VALIDATION_STARTED = "validation.started"
    VALIDATION_COMPLETED = "validation.completed"
    DISCOVERY_STARTED = "discovery.started"
    DISCOVERY_COMPLETED = "discovery.completed"
    AUDITING_STARTED = "auditing.started"
    AUDITING_COMPLETED = "auditing.completed"
    PROCESSING_STARTED = "processing.started"
    PROCESSING_COMPLETED = "processing.completed"
    AUDIT_COMPLETED = "audit.completed"
    AUDIT_FAILED = "audit.failed"
    AUDIT_CANCELLED = "audit.cancelled"
    WORKER_CLAIMED = "worker.claimed"
    ERROR = "audit.error"
    WARNING = "audit.warning"
    INFO = "audit.info"