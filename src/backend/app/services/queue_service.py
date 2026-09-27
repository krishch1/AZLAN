"""Audit Queue Service for PostgreSQL-backed job queue.

This module implements the job queue operations:
- enqueue: Create a job for an audit (transactional with audit status transition)
- claim: Atomically claim a queued job using SELECT FOR UPDATE SKIP LOCKED
- complete: Mark job as completed and transition audit to COMPLETED
- fail: Mark job as failed and transition audit to FAILED
- cancel: Cancel a queued/claimed job
- recover_stale: Recover jobs that have been claimed but not completed for too long
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.exceptions import (
    AuditJobAlreadyExistsError,
    AuditJobClaimError,
    AuditJobNotFoundError,
    AuditJobTransitionError,
    AuditNotFoundError,
    AuditPersistenceError,
    AuditStateError,
)
from backend.app.models.audit import Audit
from backend.app.models.audit_job import AuditJob
from backend.app.models.enums import AuditStatus, JobStatus

if TYPE_CHECKING:
    from backend.app.models.audit_event import AuditEvent


class AuditQueueService:
    """Service for managing the PostgreSQL-backed audit job queue.

    Uses SELECT FOR UPDATE SKIP LOCKED for safe concurrent job claiming.
    All operations are transactional and update both job and audit state.
    """

    def __init__(self, session: AsyncSession, *, claim_lease_seconds: int = 300) -> None:
        """Initialize with an AsyncSession.

        Args:
            session: Database session.
            claim_lease_seconds: How long a job stays claimed before being
                considered stale and eligible for recovery. Default 5 minutes.
        """
        self.session = session
        self.claim_lease_seconds = claim_lease_seconds

    async def enqueue(self, audit: Audit, *, available_at: datetime | None = None) -> AuditJob:
        """Create a job for an audit and transition audit to QUEUED.

        This operation is transactional: both the job creation and the
        audit status transition succeed or fail together.

        Args:
            audit: The audit to enqueue. Must be in CREATED state.
            available_at: When the job becomes available for claiming.
                Defaults to now.

        Returns:
            The created AuditJob.

        Raises:
            AuditJobAlreadyExistsError: If audit already has a job.
            AuditStateError: If audit is not in CREATED state.
            AuditPersistenceError: If database persistence fails.
        """
        # Check if audit already has a job
        from sqlalchemy import select
        stmt = select(AuditJob).where(AuditJob.audit_id == audit.id)
        result = await self.session.execute(stmt)
        existing_job = result.scalar_one_or_none()
        if existing_job:
            raise AuditJobAlreadyExistsError(
                f"Audit {audit.id} already has job {existing_job.id} with status {existing_job.status}"
            )

        # Verify audit is in enqueueable state (CREATED)
        if AuditStatus(audit.status) != AuditStatus.CREATED:
            raise AuditStateError(
                f"Cannot enqueue audit {audit.id}: current status is {audit.status}, expected CREATED"
            )

        # Create the job
        now = datetime.now(UTC)
        job = AuditJob(
            audit=audit,
            audit_id=audit.id,
            status=JobStatus.QUEUED.value,
            available_at=available_at or now,
            attempt_count=0,
        )
        self.session.add(job)

        # Transition audit to QUEUED
        from backend.app.services.state_service import AuditStateService
        state_service = AuditStateService(self.session)
        await state_service.transition_to_queued(audit)

        try:
            await self.session.flush()
            await self.session.refresh(job)
        except Exception as err:
            await self.session.rollback()
            raise AuditPersistenceError(f"Failed to enqueue audit: {err}") from err

        return job

    async def claim(self, worker_id: str) -> AuditJob | None:
        """Atomically claim an available queued job.

        Uses SELECT FOR UPDATE SKIP LOCKED to prevent multiple workers
        from claiming the same job.

        The database lock is released immediately after claiming.
        The caller should NOT perform long-running work while holding the session.

        Args:
            worker_id: Identity of the worker claiming the job.

        Returns:
            The claimed AuditJob, or None if no jobs available.

        Raises:
            AuditPersistenceError: If database persistence fails.
        """
        now = datetime.now(UTC)

        # Select one available queued job, lock it, skip locked rows
        stmt = (
            select(AuditJob)
            .where(
                AuditJob.status == JobStatus.QUEUED.value,
                AuditJob.available_at <= now,
            )
            .order_by(AuditJob.available_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        job = result.scalar_one_or_none()

        if job is None:
            return None

        # Update job state
        job.status = JobStatus.CLAIMED.value
        job.claimed_at = now
        job.attempt_count += 1
        job.worker_id = worker_id
        job.updated_at = now

        # Update audit state to VALIDATING (first execution step)
        from backend.app.services.state_service import AuditStateService
        state_service = AuditStateService(self.session)
        await state_service.transition_to_validating(job.audit)

        try:
            await self.session.flush()
            await self.session.refresh(job)
            await self.session.refresh(job.audit)
        except Exception as err:
            await self.session.rollback()
            raise AuditPersistenceError(f"Failed to claim job: {err}") from err

        return job

    async def complete(self, job: AuditJob) -> AuditJob:
        """Mark a job as completed and transition audit to COMPLETED.

        Args:
            job: The job to complete. Must be in CLAIMED state.

        Returns:
            The updated AuditJob.

        Raises:
            AuditJobTransitionError: If job is not in a completable state.
            AuditPersistenceError: If database persistence fails.
        """
        if JobStatus(job.status) != JobStatus.CLAIMED:
            raise AuditJobTransitionError(
                f"Cannot complete job {job.id}: current status is {job.status}, expected CLAIMED"
            )

        now = datetime.now(UTC)
        job.status = JobStatus.COMPLETED.value
        job.completed_at = now
        job.updated_at = now

        # Transition audit to COMPLETED
        from backend.app.services.state_service import AuditStateService
        state_service = AuditStateService(self.session)
        await state_service.transition_to_completed(job.audit)

        try:
            await self.session.flush()
            await self.session.refresh(job)
            await self.session.refresh(job.audit)
        except Exception as err:
            await self.session.rollback()
            raise AuditPersistenceError(f"Failed to complete job: {err}") from err

        return job

    async def fail(
        self, job: AuditJob, *, error_message: str, retry: bool = False
    ) -> AuditJob:
        """Mark a job as failed and transition audit to FAILED.

        If retry is True, the job is returned to QUEUED state for another attempt.
        Otherwise, it's marked FAILED and audit transitions to FAILED.

        Args:
            job: The job to fail. Must be in CLAIMED state.
            error_message: Error description.
            retry: Whether to re-queue the job for retry.

        Returns:
            The updated AuditJob.

        Raises:
            AuditJobTransitionError: If job is not in a fail-able state.
            AuditPersistenceError: If database persistence fails.
        """
        if JobStatus(job.status) != JobStatus.CLAIMED:
            raise AuditJobTransitionError(
                f"Cannot fail job {job.id}: current status is {job.status}, expected CLAIMED"
            )

        now = datetime.now(UTC)
        job.last_error = error_message
        job.failed_at = now
        job.updated_at = now

        if retry:
            # Re-queue for another attempt
            job.status = JobStatus.QUEUED.value
            job.claimed_at = None
            job.worker_id = None
            job.available_at = now
            # Audit stays in VALIDATING (or whatever state it was in)
        else:
            # Mark as permanently failed
            job.status = JobStatus.FAILED.value
            # Transition audit to FAILED
            from backend.app.services.state_service import AuditStateService
            state_service = AuditStateService(self.session)
            await state_service.transition_to_failed(job.audit, error_message=error_message)

        try:
            await self.session.flush()
            await self.session.refresh(job)
            await self.session.refresh(job.audit)
        except Exception as err:
            await self.session.rollback()
            raise AuditPersistenceError(f"Failed to fail job: {err}") from err

        return job

    async def cancel(self, job: AuditJob, *, reason: str | None = None) -> AuditJob:
        """Cancel a queued or claimed job.

        Args:
            job: The job to cancel. Must be in QUEUED or CLAIMED state.
            reason: Optional cancellation reason.

        Returns:
            The updated AuditJob.

        Raises:
            AuditJobTransitionError: If job cannot be cancelled from current state.
            AuditPersistenceError: If database persistence fails.
        """
        current_status = JobStatus(job.status)
        if current_status not in (JobStatus.QUEUED, JobStatus.CLAIMED):
            raise AuditJobTransitionError(
                f"Cannot cancel job {job.id}: current status is {job.status}, "
                f"only QUEUED or CLAIMED jobs can be cancelled"
            )

        now = datetime.now(UTC)
        job.status = JobStatus.CANCELLED.value
        job.updated_at = now

        # Transition audit to CANCELLED
        from backend.app.services.state_service import AuditStateService
        state_service = AuditStateService(self.session)
        await state_service.transition_to_cancelled(job.audit, reason=reason)

        try:
            await self.session.flush()
            await self.session.refresh(job)
            await self.session.refresh(job.audit)
        except Exception as err:
            await self.session.rollback()
            raise AuditPersistenceError(f"Failed to cancel job: {err}") from err

        return job

    async def recover_stale_jobs(self, *, max_stale: int | None = None) -> list[AuditJob]:
        """Recover jobs that have been claimed but not completed for too long.

        Jobs in CLAIMED state where claimed_at is older than the lease duration
        are returned to QUEUED state for another worker to pick up.

        Args:
            max_stale: Maximum number of stale jobs to recover in one call.
                Defaults to all.

        Returns:
            List of recovered AuditJobs.

        Raises:
            AuditPersistenceError: If database persistence fails.
        """
        lease_threshold = datetime.now(UTC) - timedelta(seconds=self.claim_lease_seconds)

        stmt = (
            select(AuditJob)
            .where(
                AuditJob.status == JobStatus.CLAIMED.value,
                AuditJob.claimed_at < lease_threshold,
            )
            .order_by(AuditJob.claimed_at)
        )
        if max_stale:
            stmt = stmt.limit(max_stale)

        result = await self.session.execute(stmt)
        stale_jobs = result.scalars().all()

        recovered = []
        for job in stale_jobs:
            now = datetime.now(UTC)
            job.status = JobStatus.QUEUED.value
            job.claimed_at = None
            job.worker_id = None
            job.available_at = now
            job.updated_at = now

            # Keep audit in its current state (VALIDATING, DISCOVERING, etc.)
            # The worker will re-transition when it claims the job

            recovered.append(job)

        if recovered:
            try:
                await self.session.flush()
                for job in recovered:
                    await self.session.refresh(job)
                    await self.session.refresh(job.audit)
            except Exception as err:
                await self.session.rollback()
                raise AuditPersistenceError(f"Failed to recover stale jobs: {err}") from err

        return recovered

    async def get_job(self, job_id: UUID) -> AuditJob:
        """Get a job by ID.

        Args:
            job_id: The job UUID.

        Returns:
            The AuditJob.

        Raises:
            AuditJobNotFoundError: If job not found.
        """
        stmt = select(AuditJob).where(AuditJob.id == job_id)
        result = await self.session.execute(stmt)
        job = result.scalar_one_or_none()
        if job is None:
            raise AuditJobNotFoundError(f"Job {job_id} not found")
        return job

    async def get_jobs_for_audit(self, audit_id: UUID) -> list[AuditJob]:
        """Get all jobs for an audit.

        Args:
            audit_id: The audit UUID.

        Returns:
            List of AuditJobs ordered by creation time.
        """
        stmt = select(AuditJob).where(AuditJob.audit_id == audit_id).order_by(AuditJob.created_at)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())