"""Audit State Machine and Transition Service.

This module defines the legal state transitions for AuditStatus and provides
a controlled service for performing transitions. It ensures that all state
changes are validated, transactional, and produce appropriate AuditEvents.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.exceptions import AuditPersistenceError, AuditStateError
from backend.app.models.enums import AuditStatus, EventType

if TYPE_CHECKING:
    from backend.app.models.audit import Audit
    from backend.app.models.audit_event import AuditEvent


# Legal AuditStatus transitions
# Format: current_status -> set of allowed next statuses
AUDIT_STATUS_TRANSITIONS: dict[AuditStatus, set[AuditStatus]] = {
    AuditStatus.CREATED: {AuditStatus.QUEUED},
    AuditStatus.QUEUED: {AuditStatus.VALIDATING, AuditStatus.CANCELLED},
    AuditStatus.VALIDATING: {AuditStatus.DISCOVERING, AuditStatus.FAILED, AuditStatus.CANCELLED},
    AuditStatus.DISCOVERING: {AuditStatus.AUDITING, AuditStatus.FAILED, AuditStatus.CANCELLED},
    AuditStatus.AUDITING: {AuditStatus.PROCESSING, AuditStatus.FAILED, AuditStatus.CANCELLED},
    AuditStatus.PROCESSING: {AuditStatus.COMPLETED, AuditStatus.FAILED, AuditStatus.CANCELLED},
    # Terminal states - no transitions allowed
    AuditStatus.COMPLETED: set(),
    AuditStatus.FAILED: set(),
    AuditStatus.CANCELLED: set(),
}


# Map AuditStatus to corresponding EventType for the transition
AUDIT_STATUS_TO_EVENT_TYPE: dict[AuditStatus, EventType] = {
    AuditStatus.CREATED: EventType.AUDIT_CREATED,
    AuditStatus.QUEUED: EventType.AUDIT_QUEUED,
    AuditStatus.VALIDATING: EventType.VALIDATION_STARTED,
    AuditStatus.DISCOVERING: EventType.DISCOVERY_STARTED,
    AuditStatus.AUDITING: EventType.AUDITING_STARTED,
    AuditStatus.PROCESSING: EventType.PROCESSING_STARTED,
    AuditStatus.COMPLETED: EventType.AUDIT_COMPLETED,
    AuditStatus.FAILED: EventType.AUDIT_FAILED,
    AuditStatus.CANCELLED: EventType.AUDIT_CANCELLED,
}


def get_allowed_next_statuses(current: AuditStatus) -> set[AuditStatus]:
    """Return the set of legal next statuses for the given current status."""
    return AUDIT_STATUS_TRANSITIONS.get(current, set())


def is_legal_transition(current: AuditStatus, next_status: AuditStatus) -> bool:
    """Check if a transition from current to next_status is legal."""
    return next_status in get_allowed_next_statuses(current)


class AuditStateService:
    """Service for controlled audit state transitions.

    This is the authoritative mechanism for changing audit status.
    Callers should not directly assign audit.status = ...
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an AsyncSession."""
        self.session = session

    async def transition(
        self,
        audit: "Audit",
        new_status: AuditStatus,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> "AuditEvent":
        """Perform a controlled state transition on an audit.

        Args:
            audit: The audit to transition.
            new_status: The target status.
            metadata: Optional additional metadata for the AuditEvent.

        Returns:
            The created AuditEvent recording the transition.

        Raises:
            AuditStateError: If the transition is not legal.
            AuditPersistenceError: If database persistence fails.
        """
        current_status = AuditStatus(audit.status)

        # Check if transition is legal (unless idempotent)
        if current_status != new_status and not is_legal_transition(current_status, new_status):
            raise AuditStateError(
                f"Illegal transition from {current_status.value} to {new_status.value}"
            )

        # Idempotent: if already in target status, return the latest event
        if current_status == new_status:
            from sqlalchemy import select
            from backend.app.models.audit_event import AuditEvent

            stmt = (
                select(AuditEvent)
                .where(AuditEvent.audit_id == audit.id)
                .order_by(AuditEvent.timestamp.desc())
                .limit(1)
            )
            result = await self.session.execute(stmt)
            latest_event = result.scalar_one_or_none()
            return latest_event

        # Update audit status and timestamps
        audit.status = new_status.value
        audit.updated_at = datetime.now(UTC)

        if new_status == AuditStatus.QUEUED:
            audit.started_at = datetime.now(UTC)
        elif new_status == AuditStatus.COMPLETED:
            audit.completed_at = datetime.now(UTC)
        elif new_status == AuditStatus.CANCELLED:
            audit.cancelled_at = datetime.now(UTC)

        # Determine event type
        event_type = AUDIT_STATUS_TO_EVENT_TYPE.get(new_status, EventType.AUDIT_QUEUED)

        # Prepare metadata
        event_metadata = metadata or {}
        event_metadata.setdefault("previous_status", current_status.value)
        event_metadata.setdefault("new_status", new_status.value)

        from backend.app.services.audit_service import _sanitize_metadata
        from backend.app.models.audit_event import AuditEvent

        event = AuditEvent(
            audit=audit,
            event_type=event_type.value,
            metadata_=_sanitize_metadata(event_metadata),
        )
        self.session.add(event)

        try:
            await self.session.flush()
            await self.session.refresh(audit)
            await self.session.refresh(event)
        except Exception as err:
            await self.session.rollback()
            raise AuditPersistenceError(f"Failed to persist state transition: {err}") from err

        return event

    async def transition_to_queued(
        self, audit: "Audit", *, metadata: dict[str, Any] | None = None
    ) -> "AuditEvent":
        """Convenience method to transition CREATED -> QUEUED."""
        return await self.transition(audit, AuditStatus.QUEUED, metadata=metadata)

    async def transition_to_validating(
        self, audit: "Audit", *, metadata: dict[str, Any] | None = None
    ) -> "AuditEvent":
        """Convenience method to transition QUEUED -> VALIDATING."""
        return await self.transition(audit, AuditStatus.VALIDATING, metadata=metadata)

    async def transition_to_discovering(
        self, audit: "Audit", *, metadata: dict[str, Any] | None = None
    ) -> "AuditEvent":
        """Convenience method to transition VALIDATING -> DISCOVERING."""
        return await self.transition(audit, AuditStatus.DISCOVERING, metadata=metadata)

    async def transition_to_auditing(
        self, audit: "Audit", *, metadata: dict[str, Any] | None = None
    ) -> "AuditEvent":
        """Convenience method to transition DISCOVERING -> AUDITING."""
        return await self.transition(audit, AuditStatus.AUDITING, metadata=metadata)

    async def transition_to_processing(
        self, audit: "Audit", *, metadata: dict[str, Any] | None = None
    ) -> "AuditEvent":
        """Convenience method to transition AUDITING -> PROCESSING."""
        return await self.transition(audit, AuditStatus.PROCESSING, metadata=metadata)

    async def transition_to_completed(
        self, audit: "Audit", *, metadata: dict[str, Any] | None = None
    ) -> "AuditEvent":
        """Convenience method to transition PROCESSING -> COMPLETED."""
        return await self.transition(audit, AuditStatus.COMPLETED, metadata=metadata)

    async def transition_to_failed(
        self,
        audit: "Audit",
        *,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "AuditEvent":
        """Convenience method to transition to FAILED with error info."""
        meta = metadata or {}
        if error_message:
            meta["error"] = error_message
        return await self.transition(audit, AuditStatus.FAILED, metadata=meta)

    async def transition_to_cancelled(
        self, audit: "Audit", *, reason: str | None = None, metadata: dict[str, Any] | None = None
    ) -> "AuditEvent":
        """Convenience method to transition to CANCELLED with reason."""
        meta = metadata or {}
        if reason:
            meta["reason"] = reason
        return await self.transition(audit, AuditStatus.CANCELLED, metadata=meta)