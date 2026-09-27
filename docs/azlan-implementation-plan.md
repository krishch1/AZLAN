# AZLAN — IMPLEMENTATION PLAN

## Mission

Build AZLAN from an empty repository to a production-grade V1 using the locked scope and architecture.

## Repository Layout

```text
azlan/
├── docs/
├── src/
│   ├── backend/app/
│   ├── worker/
│   └── frontend/
├── tests/
├── infra/
├── scripts/
├── docker-compose.yml
└── pyproject.toml
```

## Exact Build Order

### Step 1 — Foundation
Implement configuration, FastAPI app, PostgreSQL connection, migrations, health checks, frontend shell, and worker entrypoint.

### Step 2 — Data Model
Implement audits, targets, resources, evidence, findings, events, and verification records.

### Step 3 — Job Queue
Implement PostgreSQL-backed queue with transactional row locking, crash recovery, cancellation, and audit/queue consistency.

### Step 4 — Scope Engine
Implement target normalization, origin policy, redirect policy, destination validation, and out-of-scope classification. Write SSRF bypass tests before crawling.

### Step 5 — HTTP Discovery
Implement HTTP client, response normalization, HTML extraction, forms, redirects, robots, sitemap, and adaptive crawl.

### Step 6 — JS/API Discovery
Implement JS endpoint extraction, REST signals, OpenAPI signals, and GraphQL signals.

### Step 7 — Passive Checks
Implement each check as an independent catalog entry with evidence, finding, remediation, verification, and tests.

### Step 8 — Active Checks
Implement safety policy first, then budgets/cancellation, then authentication, authorization, input, REST, and GraphQL checks.

### Step 9 — Frontend
Implement create audit, progress, findings, evidence, re-audit, and history.

### Step 10 — Hardening
Run unit/integration/E2E/security/performance suites and final consistency audit.

## First Vertical Slice

```text
POST /api/v1/audits
 → persist
 → enqueue
 → worker claims
 → validate target
 → COMPLETED
 → GET /api/v1/audits/{id}
```

Do not implement crawling until this lifecycle is stable.

## Definition of Done

Code + tests + security review + documentation consistency.
