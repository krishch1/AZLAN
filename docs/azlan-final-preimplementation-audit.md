# AZLAN — FINAL PRE-IMPLEMENTATION CONSISTENCY & CONTRADICTION AUDIT

## Purpose

Final gate before feature implementation.

## Checklist

### Product
- [ ] Vision matches workflow.
- [ ] Primary user is developer.
- [ ] V1 scope is bounded.
- [ ] Zero-cost core is preserved.

### Requirements
- [ ] FRs map to implementation areas.
- [ ] NFRs are represented.
- [ ] No implementation task expands scope.

### Architecture
- [ ] API/worker/engine/frontend boundaries are explicit.
- [ ] PostgreSQL is source of truth.
- [ ] Queue semantics are defined.
- [ ] Browser automation is isolated.

### Security
- [ ] Central scope enforcement.
- [ ] SSRF/bypass tests.
- [ ] Credential redaction.
- [ ] Non-destructive active checks.
- [ ] Resource limits.
- [ ] Audit isolation.

### Data
- [ ] Schema supports lifecycle.
- [ ] Evidence links to findings.
- [ ] Secrets are protected.
- [ ] State transitions are transactional.

### Testing
- [ ] Every check has fixtures.
- [ ] Security boundaries have bypass tests.
- [ ] Lifecycle/recovery are integration tested.
- [ ] E2E uses controlled targets.

### Operations
- [ ] Docker Compose works.
- [ ] CI works without paid services.
- [ ] Health checks exist.
- [ ] Logs are secret-free.

## Contradiction Policy

1. `[LOCKED]` wins.
2. Two conflicting locked decisions require an ADR and implementation stop in that area.
3. `[RECOMMENDED]` can change with justification.
4. `[UNRESOLVED]` cannot silently become decided.
5. `[VALIDATION REQUIRED]` requires an experiment.
