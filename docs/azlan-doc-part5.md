# AZLAN — PART 5: TESTING, DEPLOYMENT & DEVELOPMENT STANDARDS

## Testing Philosophy

Testing covers correctness, security assurance, and regression prevention.

## Testing Pyramid

```text
        E2E
   Integration
      Unit
```

## Unit Tests

Cover:
- URL normalization;
- scope decisions;
- SSRF policy;
- crawler prioritization;
- HTML/JS extraction;
- every audit check;
- finding correlation;
- redaction;
- state transitions.

## Integration Tests

Cover:
- API/database;
- API/job queue;
- worker/engine;
- engine/persistence;
- cancellation;
- recovery;
- authenticated targets.

## E2E

Use controlled local vulnerable applications. Do not automate destructive testing against random public sites.

## CI

Run:
- lint;
- type checking;
- unit tests;
- integration tests;
- security/static checks;
- build verification.

No paid services required.

## Local Deployment

Docker Compose:
```text
postgres
backend
worker
frontend
```

## Development Standards

- Python type hints.
- Ruff.
- Pytest.
- TypeScript strict mode.
- ESLint.
- Alembic migrations.
- No secrets in Git.
- New audit checks require tests.
- Security-sensitive architectural changes require ADRs.

## Definition of Done

Implementation + tests + security review + documentation consistency.
