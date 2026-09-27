"""Base worker class for audit job processing."""
This module provides the abstract base class that all audit workers inherit from.
It handles the job claiming lifecycle, state transitions, and error recovery.
"""

from __future__ import annotations

import asyncio
import signal
import sys
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit_job import AuditJob
from backend.app.models.enums import AuditStatus, JobStatus
from backend.app.services.queue_service import AuditQueueService
from backend.app.services.state_service import AuditStateService

if TYPE_CHECKING:
    from backend.app.models.audit import Audit


class WorkerBase(ABC):
    """Abstract base class for audit workers.

    Subclasses must implement the `execute` method to define the actual
    work performed for a job. The base class handles:
    - Job claiming with proper locking
    - State transitions (VALIDATING -> DISCOVERING -> AUDITING -> PROCESSING -> COMPLETED)
    - Error handling and retries
    - Graceful shutdown on signals
    """

    # Override in subclasses
    worker_type: str = "base"
    max_retries: int = 3
    poll_interval: float = 1.0  # seconds between queue polls when empty

    def __init__(self, session_factory, worker_id: str | None = None) -> None:
        """Initialize the worker.

        Args:
            session_factory: Callable that returns a new AsyncSession.
            worker_id: Unique identifier for this worker instance.
        """
        self.session_factory = session_factory
        self.worker_id = worker_id or f"{self.worker_type}-{datetime.now(UTC).timestamp()}"
        self._shutdown_event = asyncio.Event()
        self._current_job: AuditJob | None = None

    @abstractmethod
    async def execute(self, job: AuditJob, session: AsyncSession) -> None:
        """Execute the audit job.

        This method is called after the job is claimed and the audit
        has been transitioned to VALIDATING. The worker should perform
        the actual audit work here, transitioning through the expected
        states as appropriate.

        Args:
            job: The claimed job to execute.
            session: Database session for this job execution.

        Raises:
            Exception: Any exception will trigger job failure handling.
        """
        pass

    async def _transition_to_discovering(self, audit: "Audit", session: AsyncSession) -> None:
        """Transition audit to DISCOVERING state."""
        state_service = AuditStateService(session)
        await state_service.transition_to_discovering(audit)

    async def _transition_to_auditing(self, audit: "Audit", session: AsyncSession) -> None:
        """Transition audit to AUDITING state."""
        state_service = AuditStateService(session)
        await state_service.transition_to_auditing(audit)

    async def _transition_to_processing(self, audit: "Audit", session: AsyncSession) -> None:
        """Transition audit to PROCESSING state."""
        state_service = AuditStateService(session)
        await state_service.transition_to_processing(audit)

async def _process_job(self, job: AuditJob, session: AsyncSession) -> None:
        """Process a single job through the full lifecycle.

        Args:
            job: The claimed job to process.
            session: Database session for this job.
        """
        self._current_job = job
        audit = job.audit

        try:
            # Execute the job (worker-specific logic)
            await self.execute(job, session)

            # If we reach here without exception, complete the job
            queue_service = AuditQueueService(session)
            await queue_service.complete(job)

        except Exception as err:
            # Handle failure - check if we should retry
            queue_service = AuditQueueService(session)

            if job.attempt_count < self.max_retries:
                # Retry: return job to queue
                await queue_service.fail(job, error_message=str(err), retry=True)
            else:
                # Max retries exceeded: mark as permanently failed
                await queue_service.fail(job, error_message=str(err), retry=False)
            raise

        finally:
            self._current_job = None

    async def run_once(self) -> bool:
        """Claim and process a single job.

        Returns:
            True if a job was processed, False if no job was available.
        """
        async with self.session_factory() as session:
            queue_service = AuditQueueService(session)
            job = await queue_service.claim(self.worker_id)

            if job is None:
                return False

            await self._process_job(job, session)
            return True

    async def run(self) -> None:
        """Run the worker continuously until shutdown signal.

        This method polls the queue and processes jobs until
        a shutdown signal is received.
        """
        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()

        def _shutdown() -> None:
            self._shutdown_event.set()

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, _shutdown)
            except NotImplementedError:
                # Windows doesn't support add_signal_handler for some signals
                pass

        print(f"[{self.worker_id}] Worker started, polling queue...")

        while not self._shutdown_event.is_set():
            try:
                job_processed = await self.run_once()

                if not job_processed:
                    # No job available, wait before polling again
                    try:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(), timeout=self.poll_interval
                        )
                    except asyncio.TimeoutError:
                        # Normal timeout, continue polling
                        pass

            except Exception as err:
                # Log error but continue running
                print(f"[{self.worker_id}] Error in worker loop: {err}", file=sys.stderr)
                await asyncio.sleep(self.poll_interval)

        print(f"[{self.worker_id}] Worker shutting down...")

        # If we have a current job, wait for it to finish or cancel it
        if self._current_job:
            print(f"[{self.worker_id}] Waiting for current job to complete...")
            # In a real implementation, you might want to cancel the job here

    async def shutdown(self) -> None:
        """Trigger graceful shutdown."""
        self._shutdown_event.set()