"""Tests for the audit state machine and queue service."""

import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.app.models.enums import AuditStatus, JobStatus, EventType
from backend.app.services.queue_service import AuditQueueService
from backend.app.services.state_service import (
    AuditStateService,
    AUDIT_STATUS_TRANSITIONS,
    get_allowed_next_statuses,
    is_legal_transition,
)
from backend.app.exceptions import (
    AuditJobAlreadyExistsError,
    AuditJobNotFoundError,
    AuditJobTransitionError,
    AuditStateError,
)


# Patch path for AuditStateService - it's defined in state_service but imported in queue_service
STATE_SERVICE_PATCH = 'backend.app.services.state_service.AuditStateService'


class TestStateMachine:
    """Tests for the audit state machine."""

    def test_allowed_transitions_from_created(self):
        """CREATED can only go to QUEUED."""
        allowed = get_allowed_next_statuses(AuditStatus.CREATED)
        assert allowed == {AuditStatus.QUEUED}

    def test_allowed_transitions_from_queued(self):
        """QUEUED can go to VALIDATING or CANCELLED."""
        allowed = get_allowed_next_statuses(AuditStatus.QUEUED)
        assert allowed == {AuditStatus.VALIDATING, AuditStatus.CANCELLED}

    def test_allowed_transitions_from_validating(self):
        """VALIDATING can go to DISCOVERING, FAILED, or CANCELLED."""
        allowed = get_allowed_next_statuses(AuditStatus.VALIDATING)
        assert allowed == {AuditStatus.DISCOVERING, AuditStatus.FAILED, AuditStatus.CANCELLED}

    def test_allowed_transitions_from_discovering(self):
        """DISCOVERING can go to AUDITING, FAILED, or CANCELLED."""
        allowed = get_allowed_next_statuses(AuditStatus.DISCOVERING)
        assert allowed == {AuditStatus.AUDITING, AuditStatus.FAILED, AuditStatus.CANCELLED}

    def test_allowed_transitions_from_auditing(self):
        """AUDITING can go to PROCESSING, FAILED, or CANCELLED."""
        allowed = get_allowed_next_statuses(AuditStatus.AUDITING)
        assert allowed == {AuditStatus.PROCESSING, AuditStatus.FAILED, AuditStatus.CANCELLED}

    def test_allowed_transitions_from_processing(self):
        """PROCESSING can go to COMPLETED, FAILED, or CANCELLED."""
        allowed = get_allowed_next_statuses(AuditStatus.PROCESSING)
        assert allowed == {AuditStatus.COMPLETED, AuditStatus.FAILED, AuditStatus.CANCELLED}

    def test_terminal_states_have_no_transitions(self):
        """Terminal states (COMPLETED, FAILED, CANCELLED) have no outgoing transitions."""
        for status in [AuditStatus.COMPLETED, AuditStatus.FAILED, AuditStatus.CANCELLED]:
            allowed = get_allowed_next_statuses(status)
            assert allowed == set()

    def test_legal_transition_check(self):
        """is_legal_transition correctly validates transitions."""
        assert is_legal_transition(AuditStatus.CREATED, AuditStatus.QUEUED) is True
        assert is_legal_transition(AuditStatus.QUEUED, AuditStatus.VALIDATING) is True
        assert is_legal_transition(AuditStatus.CREATED, AuditStatus.VALIDATING) is False
        assert is_legal_transition(AuditStatus.COMPLETED, AuditStatus.FAILED) is False

    def test_transition_map_completeness(self):
        """Every non-terminal status has at least one allowed transition."""
        for status in AuditStatus:
            if status not in (AuditStatus.COMPLETED, AuditStatus.FAILED, AuditStatus.CANCELLED):
                allowed = get_allowed_next_statuses(status)
                assert len(allowed) > 0, f"Status {status} has no allowed transitions"


class MockAudit:
    """Mock audit object for testing."""
    def __init__(self, id=None, status=AuditStatus.CREATED.value):
        self.id = id or uuid4()
        self.status = status
        self.started_at = None
        self.completed_at = None
        self.cancelled_at = None
        self.updated_at = None
        self.audit_metadata = {}
        # SQLAlchemy relationship support
        self._sa_instance_state = MagicMock()


class MockAuditEvent:
    """Mock audit event."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockAuditJob:
    """Mock audit job."""
    def __init__(self, audit_id=None, status=JobStatus.QUEUED.value, **kwargs):
        self.id = uuid4()
        self.audit = kwargs.get('audit')
        self.audit_id = audit_id or (self.audit.id if self.audit else None) or uuid4()
        self.status = status
        self.worker_id = None
        self.attempt_count = 0
        self.available_at = datetime.now(UTC)
        self.claimed_at = None
        self.completed_at = None
        self.failed_at = None
        self.last_error = None
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        for k, v in kwargs.items():
            setattr(self, k, v)
        if self.audit and not self.audit_id:
            self.audit_id = self.audit.id


class TestAuditStateService:
    """Tests for the AuditStateService."""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def state_service(self, mock_session):
        return AuditStateService(mock_session)

    @pytest.fixture
    def audit(self):
        return MockAudit(status=AuditStatus.CREATED.value)

    @pytest.mark.asyncio
    async def test_transition_legal(self, state_service, audit):
        """Test legal transition CREATED -> QUEUED."""
        with patch('backend.app.services.audit_service._sanitize_metadata', return_value={}):
            with patch('backend.app.models.audit_event.AuditEvent') as mock_event_class:
                mock_event = MockAuditEvent()
                mock_event_class.return_value = mock_event

                event = await state_service.transition(audit, AuditStatus.QUEUED)

                assert audit.status == AuditStatus.QUEUED.value
                assert audit.started_at is not None
                assert event is not None

    @pytest.mark.asyncio
    async def test_transition_illegal(self, state_service, audit):
        """Test illegal transition raises AuditStateError."""
        audit.status = AuditStatus.COMPLETED.value

        with pytest.raises(AuditStateError) as exc_info:
            await state_service.transition(audit, AuditStatus.QUEUED)

        assert "Illegal transition" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_transition_idempotent(self, state_service, audit):
        """Test idempotent transition (same status) returns latest event."""
        audit.status = AuditStatus.QUEUED.value

        mock_event = MockAuditEvent()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_event
        state_service.session.execute = AsyncMock(return_value=mock_result)

        event = await state_service.transition(audit, AuditStatus.QUEUED)

        assert event == mock_event

    @pytest.mark.asyncio
    async def test_transition_sets_completed_at(self, state_service, audit):
        """Test transition to COMPLETED sets completed_at."""
        audit.status = AuditStatus.PROCESSING.value

        with patch('backend.app.services.audit_service._sanitize_metadata', return_value={}):
            with patch('backend.app.models.audit_event.AuditEvent') as mock_event_class:
                mock_event_class.return_value = MockAuditEvent()

                await state_service.transition(audit, AuditStatus.COMPLETED)

                assert audit.completed_at is not None

    @pytest.mark.asyncio
    async def test_transition_sets_cancelled_at(self, state_service, audit):
        """Test transition to CANCELLED sets cancelled_at."""
        audit.status = AuditStatus.QUEUED.value

        with patch('backend.app.services.audit_service._sanitize_metadata', return_value={}):
            with patch('backend.app.models.audit_event.AuditEvent') as mock_event_class:
                mock_event_class.return_value = MockAuditEvent()

                await state_service.transition(audit, AuditStatus.CANCELLED)

                assert audit.cancelled_at is not None

    @pytest.mark.asyncio
    async def test_transition_to_failed_includes_error(self, state_service, audit):
        """Test transition_to_failed includes error message in metadata."""
        audit.status = AuditStatus.AUDITING.value

        with patch('backend.app.services.audit_service._sanitize_metadata', return_value={}) as mock_sanitize:
            with patch('backend.app.models.audit_event.AuditEvent') as mock_event_class:
                mock_event_class.return_value = MockAuditEvent()

                await state_service.transition_to_failed(
                    audit, error_message="Something went wrong"
                )

                # Check that sanitize_metadata was called with error in metadata
                call_args = mock_sanitize.call_args[0][0]
                assert call_args.get("error") == "Something went wrong"


class TestAuditQueueService:
    """Tests for the AuditQueueService."""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.rollback = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def queue_service(self, mock_session):
        return AuditQueueService(mock_session, claim_lease_seconds=300)

    @pytest.fixture
    def audit(self):
        return MockAudit(status=AuditStatus.CREATED.value)

    @pytest.mark.asyncio
    async def test_enqueue_creates_job(self, queue_service, audit, mock_session):
        """Test enqueue creates a job and transitions audit to QUEUED."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch(STATE_SERVICE_PATCH) as mock_state:
            mock_state_instance = AsyncMock()
            mock_state.return_value = mock_state_instance
            mock_state_instance.transition_to_queued = AsyncMock()

            job = await queue_service.enqueue(audit)

            assert job is not None
            assert job.audit_id == audit.id
            assert job.status == JobStatus.QUEUED.value
            assert job.attempt_count == 0
            mock_state_instance.transition_to_queued.assert_called_once_with(audit)

    @pytest.mark.asyncio
    async def test_enqueue_existing_job_raises(self, queue_service, audit, mock_session):
        """Test enqueue raises if audit already has a job."""
        existing_job = MockAuditJob(audit_id=audit.id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_job
        mock_session.execute.return_value = mock_result

        with pytest.raises(AuditJobAlreadyExistsError):
            await queue_service.enqueue(audit)

    @pytest.mark.asyncio
    async def test_enqueue_wrong_status_raises(self, queue_service, audit, mock_session):
        """Test enqueue raises if audit not in CREATED state."""
        audit.status = AuditStatus.QUEUED.value
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(AuditStateError):
            await queue_service.enqueue(audit)

    @pytest.mark.asyncio
    async def test_claim_returns_job(self, queue_service, mock_session):
        """Test claim returns a job when available."""
        job = MockAuditJob(status=JobStatus.QUEUED.value)
        job.audit = MockAudit(status=AuditStatus.QUEUED.value)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = job
        mock_session.execute.return_value = mock_result

        with patch(STATE_SERVICE_PATCH) as mock_state:
            mock_state_instance = AsyncMock()
            mock_state.return_value = mock_state_instance
            mock_state_instance.transition_to_validating = AsyncMock()

            claimed_job = await queue_service.claim("worker-1")

            assert claimed_job is not None
            assert claimed_job.status == JobStatus.CLAIMED.value
            assert claimed_job.worker_id == "worker-1"
            assert claimed_job.attempt_count == 1

    @pytest.mark.asyncio
    async def test_claim_returns_none_when_empty(self, queue_service, mock_session):
        """Test claim returns None when no jobs available."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        job = await queue_service.claim("worker-1")
        assert job is None

    @pytest.mark.asyncio
    async def test_complete_job(self, queue_service, mock_session):
        """Test complete transitions job and audit to COMPLETED."""
        job = MockAuditJob(status=JobStatus.CLAIMED.value)
        job.audit = MockAudit(status=AuditStatus.PROCESSING.value)

        with patch(STATE_SERVICE_PATCH) as mock_state:
            mock_state_instance = AsyncMock()
            mock_state.return_value = mock_state_instance
            mock_state_instance.transition_to_completed = AsyncMock()

            completed_job = await queue_service.complete(job)

            assert completed_job.status == JobStatus.COMPLETED.value
            assert completed_job.completed_at is not None
            mock_state_instance.transition_to_completed.assert_called_once_with(job.audit)

    @pytest.mark.asyncio
    async def test_complete_wrong_status_raises(self, queue_service):
        """Test complete raises if job not in CLAIMED state."""
        job = MockAuditJob(status=JobStatus.QUEUED.value)

        with pytest.raises(AuditJobTransitionError):
            await queue_service.complete(job)

    @pytest.mark.asyncio
    async def test_fail_job_permanent(self, queue_service, mock_session):
        """Test fail marks job as FAILED (no retry)."""
        job = MockAuditJob(status=JobStatus.CLAIMED.value)
        job.audit = MockAudit(status=AuditStatus.AUDITING.value)

        with patch(STATE_SERVICE_PATCH) as mock_state:
            mock_state_instance = AsyncMock()
            mock_state.return_value = mock_state_instance
            mock_state_instance.transition_to_failed = AsyncMock()

            failed_job = await queue_service.fail(job, error_message="Error!", retry=False)

            assert failed_job.status == JobStatus.FAILED.value
            assert failed_job.last_error == "Error!"
            mock_state_instance.transition_to_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_fail_job_retry(self, queue_service, mock_session):
        """Test fail returns job to QUEUED for retry."""
        job = MockAuditJob(status=JobStatus.CLAIMED.value, attempt_count=1)
        job.audit = MockAudit(status=AuditStatus.AUDITING.value)

        with patch(STATE_SERVICE_PATCH) as mock_state:
            mock_state_instance = AsyncMock()
            mock_state.return_value = mock_state_instance
            mock_state_instance.transition_to_failed = AsyncMock()

            failed_job = await queue_service.fail(job, error_message="Retryable error", retry=True)

            assert failed_job.status == JobStatus.QUEUED.value
            assert failed_job.claimed_at is None
            assert failed_job.worker_id is None
            mock_state_instance.transition_to_failed.assert_not_called()

    @pytest.mark.asyncio
    async def test_cancel_queued_job(self, queue_service, mock_session):
        """Test cancel a QUEUED job."""
        job = MockAuditJob(status=JobStatus.QUEUED.value)
        job.audit = MockAudit(status=AuditStatus.QUEUED.value)

        with patch(STATE_SERVICE_PATCH) as mock_state:
            mock_state_instance = AsyncMock()
            mock_state.return_value = mock_state_instance
            mock_state_instance.transition_to_cancelled = AsyncMock()

            cancelled_job = await queue_service.cancel(job, reason="User requested")

            assert cancelled_job.status == JobStatus.CANCELLED.value
            mock_state_instance.transition_to_cancelled.assert_called_once_with(job.audit, reason="User requested")

    @pytest.mark.asyncio
    async def test_cancel_claimed_job(self, queue_service, mock_session):
        """Test cancel a CLAIMED job."""
        job = MockAuditJob(status=JobStatus.CLAIMED.value)
        job.audit = MockAudit(status=AuditStatus.VALIDATING.value)

        with patch(STATE_SERVICE_PATCH) as mock_state:
            mock_state_instance = AsyncMock()
            mock_state.return_value = mock_state_instance
            mock_state_instance.transition_to_cancelled = AsyncMock()

            cancelled_job = await queue_service.cancel(job)

            assert cancelled_job.status == JobStatus.CANCELLED.value

    @pytest.mark.asyncio
    async def test_cancel_terminal_job_raises(self, queue_service):
        """Test cancel raises if job in terminal state."""
        job = MockAuditJob(status=JobStatus.COMPLETED.value)

        with pytest.raises(AuditJobTransitionError):
            await queue_service.cancel(job)

    @pytest.mark.asyncio
    async def test_recover_stale_jobs(self, queue_service, mock_session):
        """Test recover_stale_jobs returns stale jobs to QUEUED."""
        old_time = datetime.now(UTC) - timedelta(seconds=600)  # 10 minutes ago
        stale_job = MockAuditJob(status=JobStatus.CLAIMED.value, claimed_at=old_time)
        stale_job.audit = MockAudit(status=AuditStatus.VALIDATING.value)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [stale_job]
        mock_session.execute.return_value = mock_result

        recovered = await queue_service.recover_stale_jobs(max_stale=10)

        assert len(recovered) == 1
        assert recovered[0].status == JobStatus.QUEUED.value
        assert recovered[0].claimed_at is None
        assert recovered[0].worker_id is None

    @pytest.mark.asyncio
    async def test_get_job(self, queue_service, mock_session):
        """Test get_job retrieves job by ID."""
        job_id = uuid4()
        job = MockAuditJob(id=job_id)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = job
        mock_session.execute.return_value = mock_result

        retrieved = await queue_service.get_job(job_id)
        assert retrieved == job

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, queue_service, mock_session):
        """Test get_job raises if not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(AuditJobNotFoundError):
            await queue_service.get_job(uuid4())