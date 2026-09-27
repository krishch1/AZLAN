# AZLAN — MASTER TECHNICAL & PRODUCT DOCUMENTATION

**System:** Production-grade Web Application Security Auditing Platform
**Primary User:** Individual developer
**Development Model:** Solo developer
**Core Cost Constraint:** Zero monetary cost for the core system
**Status:** Pre-Implementation Baseline

## Document Series

| Part | Title |
|---|---|
| Part 1 | Foundations, Requirements & Architecture |
| Part 2 | Audit Engine & Application Discovery |
| Part 3 | Security, Threat Model & Data Architecture |
| Part 4 | Performance, Observability & Frontend |
| Part 5 | Testing, Deployment & Development Standards |
| Part 6 | Risks, Decisions & Readiness |

Supporting execution artifacts:
- `azlan-engineering-sprint-master.md`
- `azlan-implementation-plan.md`
- `azlan-final-preimplementation-audit.md`

## Architectural baseline

AZLAN V1 is a modular monolith plus dedicated worker:

```text
Browser
  |
  v
React + TypeScript
  |
  v
FastAPI API
  |
  +---- PostgreSQL
  |
  +---- PostgreSQL-backed Job Queue
              |
              v
        Scan Worker
              |
       +------+------+
       |             |
   HTTP Engine   Browser Adapter
       |
   Audit Checks
       |
   Evidence/Findings
       |
       v
    PostgreSQL
```

## Locked technology baseline

| Area | Decision | Status |
|---|---|---|
| Backend | Python 3.12 + FastAPI | `[LOCKED]` |
| Validation | Pydantic v2 | `[LOCKED]` |
| Data layer | SQLAlchemy 2 async | `[LOCKED]` |
| Database | PostgreSQL | `[LOCKED]` |
| DB driver | asyncpg | `[LOCKED]` |
| Migrations | Alembic | `[LOCKED]` |
| HTTP client | httpx | `[LOCKED]` |
| HTML parser | selectolax | `[RECOMMENDED]` |
| Browser adapter | Playwright | `[RECOMMENDED]` |
| GraphQL parser | graphql-core | `[RECOMMENDED]` |
| Job queue | PostgreSQL-backed | `[LOCKED]` |
| Frontend | React + TypeScript + Vite | `[LOCKED]` |
| Local orchestration | Docker Compose | `[LOCKED]` |
| CI | GitHub Actions | `[RECOMMENDED]` |
| AI/LLM | Not required for V1 core | `[LOCKED]` |

The architecture deliberately avoids mandatory Redis, Kafka, cloud queues, hosted scanners, and paid AI services.

## Principles

1. Evidence before conclusions.
2. Authorized auditing only.
3. Passive and active auditing are separate capabilities.
4. Active checks are bounded and non-destructive by default.
5. Discovery never automatically grants authorization.
6. Findings must be traceable to evidence.
7. Partial audits must never appear complete.
8. Security controls are cross-cutting.
9. No paid dependency is required for the core workflow.
10. Prefer the smallest production-grade system that satisfies the locked scope.

## Core pipeline

```text
Target Configuration
      ↓
Target Validation
      ↓
Scope Policy
      ↓
Discovery
      ↓
Evidence Collection
      ↓
Passive Checks
      ↓
Controlled Active Checks
      ↓
Finding Correlation
      ↓
Remediation Guidance
      ↓
Report
      ↓
Re-Audit / Verification
```
