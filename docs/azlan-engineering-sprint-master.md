# AZLAN — MASTER ENGINEERING EXECUTION & SPRINT PLAN

**Team:** Solo developer
**Goal:** Production-grade, zero-cost-core V1

## Phase 0 — Foundation
- repository scaffold
- Docker Compose
- PostgreSQL
- FastAPI health
- worker
- frontend shell
- CI
- configuration
- migrations

**Gate:** services start, migrations work, CI green.

## Phase 1 — Audit Lifecycle
- audit model
- target validation
- configuration
- PostgreSQL-backed queue
- worker lifecycle
- state machine
- cancellation
- API
- history

**Gate:** create → queue → worker → complete works against a controlled target.

## Phase 2 — Discovery
- URL normalization
- scope engine
- HTTP client
- adaptive crawler
- HTML links/forms
- robots
- sitemap
- redirects
- JS endpoint extraction
- API discovery

**Gate:** controlled target surface is discovered with evidence and scope enforcement.

## Phase 3 — Passive Security
- TLS
- headers
- cookies
- disclosure
- misconfiguration
- finding/evidence model
- deduplication

**Gate:** controlled vulnerable fixtures produce deterministic findings.

## Phase 4 — Active Security
- safety policy
- request/concurrency budgets
- cancellation
- authentication checks
- authorization checks
- input checks
- API checks
- authenticated context

**Gate:** active checks remain scoped and non-destructive.

## Phase 5 — Verification/UI/Hardening
- finding UI
- remediation
- re-audit
- verification
- history
- observability
- benchmarks
- security regression suite
- documentation

**Gate:** Audit → Understand → Fix → Verify works on controlled applications.

## Phase 6 — Release Readiness
- final consistency audit
- threat-model review
- dependency review
- performance baseline
- Docker release
- demo dataset
- final README

**Gate:** reproducible build with docs matching code.

## Solo Rules

1. Do not expand scope without an ADR.
2. Every scanner check gets a fixture.
3. Every security boundary gets a bypass test.
4. Architecture changes require ADRs.
5. Core remains zero-cost.
6. Prefer simple correct components.
