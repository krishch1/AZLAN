# AZLAN — PART 3: SECURITY, THREAT MODEL & DATA ARCHITECTURE

## Trust Boundaries

1. User input → validation and scope policy.
2. Target network → SSRF protection, redirect revalidation, bounded access.
3. Audit engine → strict interfaces, bounded payloads, exception isolation.
4. Persistence → parameterized queries, constraints, transactions.
5. Presentation → safe rendering, secret redaction.

## Threat Model

| ID | Threat | Required Control |
|---|---|---|
| THR-001 | SSRF | Network destination policy |
| THR-002 | Scope bypass | Central scope engine |
| THR-003 | Credential leakage | Secret classification/redaction |
| THR-004 | Audit data crossover | Audit isolation |
| THR-005 | Resource exhaustion | Bounded concurrency/time/request limits |
| THR-006 | Malicious target content | Treat target content as untrusted |
| THR-007 | Finding tampering | Evidence linkage/integrity |
| THR-008 | SQL injection into AZLAN | Parameterized persistence |
| THR-009 | XSS in findings | Safe output rendering |
| THR-010 | Dependency compromise | Reproducible dependency process |
| THR-011 | Worker failure | Persistent state/recovery |
| THR-012 | Unauthorized active testing | Authorization + scope gate |

## Data Classification

| Data | Classification | Handling |
|---|---|---|
| Target URL | Operational | Persisted |
| Crawl metadata | Operational | Persisted |
| HTTP evidence | Sensitive | Minimized/redacted |
| Session cookies | Secret | Never normal UI/logs |
| Credentials | Secret | Minimized |
| Findings | Sensitive | Protected |
| Audit history | Sensitive | Retained by policy |
| Logs | Operational/Sensitive | Secret-free |

## Core Entities

```text
Audit
Target
AuditConfiguration
AuditResource
Evidence
Finding
FindingEvidence
AuditEvent
VerificationResult
```

## Audit State Machine

```text
CREATED → VALIDATING → QUEUED → DISCOVERING → AUDITING → PROCESSING → COMPLETED

Failure/cancel paths:
VALIDATING → FAILED
QUEUED → CANCELLED
DISCOVERING → FAILED/CANCELLED
AUDITING → FAILED/CANCELLED/PARTIAL
PROCESSING → FAILED/PARTIAL
```

## Initial API

```text
POST /api/v1/audits
GET  /api/v1/audits/{audit_id}
POST /api/v1/audits/{audit_id}/cancel
POST /api/v1/audits/{audit_id}/rerun
GET  /api/v1/audits/{audit_id}/findings
GET  /api/v1/audits/{audit_id}/findings/{finding_id}
GET  /api/v1/audits/{audit_id}/resources
GET  /api/v1/audits/{audit_id}/events
GET  /api/v1/health
```
