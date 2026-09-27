"""AZLAN domain/application exceptions.

A small, focused exception hierarchy for audit lifecycle service failures.
"""

from __future__ import annotations


class AuditError(Exception):
    """Base exception for audit lifecycle errors."""


class AuditNotFoundError(AuditError):
    """Raised when an audit cannot be located by ID."""


class AuditTargetError(AuditError):
    """Raised when a target URL is syntactically invalid."""


class AuditConfigurationError(AuditError):
    """Raised when audit configuration is invalid."""


class AuditPersistenceError(AuditError):
    """Raised when persistence of an audit fails."""


class AuditStateError(AuditError):
    """Raised when an invalid state transition is attempted."""


class AuditJobError(AuditError):
    """Base exception for audit job queue errors."""


class AuditJobNotFoundError(AuditJobError):
    """Raised when a job cannot be located by ID."""


class AuditJobAlreadyExistsError(AuditJobError):
    """Raised when attempting to enqueue an audit that already has a job."""


class AuditJobClaimError(AuditJobError):
    """Raised when a job cannot be claimed (already claimed, not in queued state, etc.)."""


class AuditJobTransitionError(AuditJobError):
    """Raised when an invalid job state transition is attempted."""


__all__ = [
    "AuditConfigurationError",
    "AuditError",
    "AuditJobAlreadyExistsError",
    "AuditJobClaimError",
    "AuditJobError",
    "AuditJobNotFoundError",
    "AuditJobTransitionError",
    "AuditNotFoundError",
    "AuditPersistenceError",
    "AuditStateError",
    "AuditTargetError",
]