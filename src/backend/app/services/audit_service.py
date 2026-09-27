"""Audit Lifecycle Domain Service.

Responsible for transactionally creating and retrieving AZLAN audits.
Ensures:
- Target, Audit, AuditConfiguration, and initial AuditEvent are created together
  within a single database transaction.
- New audits start in CREATED state.
- No sensitive credentials are written to AuditEvent metadata or persisted in plaintext.
- Clean domain error handling via domain exceptions.
- Target URL is preserved as untrusted input (no network activity).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.exceptions import (
    AuditConfigurationError,
    AuditNotFoundError,
    AuditPersistenceError,
    AuditTargetError,
)
from backend.app.models.audit import Audit
from backend.app.models.audit_configuration import AuditConfiguration
from backend.app.models.audit_event import AuditEvent
from backend.app.models.enums import AuditStatus, EventType
from backend.app.models.target import Target
from backend.app.schemas.audit_schemas import AuditCreateRequest, AuditResponse

logger = logging.getLogger(__name__)

# Sensitive keys filter to ensure event metadata never exposes credentials
SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "credential",
    "authorization",
    "cookie",
    "session_id",
    "auth",
}


def _sanitize_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """Sanitize metadata dictionary to ensure no sensitive credentials are present."""
    sanitized: dict[str, Any] = {}
    for k, v in meta.items():
        if k.lower() in SENSITIVE_KEYS:
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = _sanitize_metadata(v)
        else:
            sanitized[k] = v
    return sanitized


class AuditLifecycleService:
    """Domain service for managing audit lifecycles.

    Controls the transaction boundary for audit creation and retrieval.
    Decoupled from FastAPI request/response lifecycle.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an AsyncSession.

        The service manages operations within this session.
        """
        self.session = session

    async def create_audit(self, request: AuditCreateRequest) -> AuditResponse:
        """Transactionally create an Audit with its Target, AuditConfiguration, and initial AuditEvent.

        Args:
            request: Structured AuditCreateRequest model.

        Returns:
            AuditResponse: Clean domain representation of the created Audit.

        Raises:
            AuditTargetError: If the target URL is invalid.
            AuditConfigurationError: If the configuration shape or values are invalid.
            AuditPersistenceError: If database persistence fails.
        """
        try:
            # 1. Create Target (untrusted input, no network calls)
            target = Target(
                url=request.target_url,
                normalized_url=request.target_url.lower(),
            )
            self.session.add(target)

            # 2. Create Audit starting in CREATED state
            audit = Audit(
                target=target,
                status=AuditStatus.CREATED.value,
            )
            self.session.add(audit)

            # 3. Create AuditConfiguration
            config = AuditConfiguration(
                audit=audit,
                mode=request.mode.value,
                crawl_config=request.crawl_config,
                scope_config=request.scope_config,
                auth_config=request.auth_config,
                testing_config=request.testing_config,
                limits_config=request.limits_config,
            )
            self.session.add(config)

            # 4. Create Initial AuditEvent (audit.created)
            event_metadata = _sanitize_metadata(
                {
                    "target_url": request.target_url,
                    "mode": request.mode.value,
                    "auth_type": request.auth_config.get("type", "none"),
                }
            )

            event = AuditEvent(
                audit=audit,
                event_type=EventType.AUDIT_CREATED.value,
                metadata_=event_metadata,
            )
            self.session.add(event)

            # Flush to assign IDs within the ongoing transaction
            await self.session.flush()
            # Commit the transaction atomically
            await self.session.commit()

            # Refresh to load relationships and generated timestamps
            await self.session.refresh(audit, ["target", "configuration", "events"])

            return AuditResponse.model_validate(audit)

        except (AuditTargetError, AuditConfigurationError):
            await self.session.rollback()
            raise
        except ValidationError as val_err:
            await self.session.rollback()
            raise AuditConfigurationError(f"Invalid audit configuration: {val_err}") from val_err
        except Exception as err:
            await self.session.rollback()
            logger.exception("Failed to transactionally create audit")
            raise AuditPersistenceError(f"Failed to persist audit: {err}") from err

    async def get_audit_by_id(self, audit_id: UUID) -> AuditResponse:
        """Retrieve an audit by its UUID along with target, configuration, and events.

        Args:
            audit_id: UUID of the audit to retrieve.

        Returns:
            AuditResponse: Domain representation of the audit.

        Raises:
            AuditNotFoundError: If no audit with the given ID exists.
        """
        try:
            stmt = (
                select(Audit)
                .where(Audit.id == audit_id)
                .options(
                    selectinload(Audit.target),
                    selectinload(Audit.configuration),
                    selectinload(Audit.events),
                )
            )
            result = await self.session.execute(stmt)
            audit = result.scalar_one_or_none()

            if audit is None:
                raise AuditNotFoundError(f"Audit with ID '{audit_id}' was not found.")

            return AuditResponse.model_validate(audit)

        except AuditNotFoundError:
            raise
        except Exception as err:
            logger.exception("Error retrieving audit %s", audit_id)
            raise AuditPersistenceError(f"Error reading audit from database: {err}") from err
