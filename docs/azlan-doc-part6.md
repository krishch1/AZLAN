# AZLAN — PART 6: RISKS, DECISIONS, READINESS & CONSISTENCY

## Risk Register

| ID | Risk | Impact | Mitigation |
|---|---|---|---|
| R-001 | SSRF/scope bypass | Critical | Central scope + network policy + tests |
| R-002 | False positives | High | Evidence + confidence + conservative checks |
| R-003 | Active scan harm | Critical | Non-destructive checks + limits |
| R-004 | Credential leakage | Critical | Secret classification/redaction |
| R-005 | Crawl explosion | High | Adaptive limits |
| R-006 | Browser resource usage | High | Adapter + budgets |
| R-007 | Worker crash | High | Persistent state + recovery |
| R-008 | Storage growth | Medium | Evidence minimization |
| R-009 | Scope creep | High | Locked catalog + change control |
| R-010 | Dependency vulnerability | High | Reproducible dependency process |
| R-011 | Solo developer overload | High | Phase gates + modular architecture |
| R-012 | Premature performance targets | Medium | Benchmark before SLA |

## ADRs

### ADR-001 — Modular Monolith + Worker
**Decision:** API plus dedicated scan worker.  
**Status:** `[LOCKED]`

### ADR-002 — PostgreSQL-backed Job Queue
**Decision:** PostgreSQL queue for V1 instead of Redis/Kafka.  
**Reason:** zero-cost and fewer infrastructure services.  
**Status:** `[LOCKED]`

### ADR-003 — No Mandatory AI
**Decision:** Core functionality works without an LLM.  
**Status:** `[LOCKED]`

### ADR-004 — Browser Adapter
**Decision:** Playwright stays behind an adapter.  
**Status:** `[RECOMMENDED]`

### ADR-005 — Local-first Deployment
**Decision:** Docker Compose is canonical for development.  
**Status:** `[LOCKED]`

## Open Decisions

- Numeric resource budgets `[VALIDATION REQUIRED]`
- Exact active-check payloads `[VALIDATION REQUIRED]`
- Retention defaults `[UNRESOLVED]`
- Hosted deployment topology `[UNRESOLVED]`
- Optional hosted-user authentication `[UNRESOLVED]`

## Readiness Gate

Implementation starts only when:
- Parts 1–6 are consistent;
- audit catalog exists;
- data model exists;
- API contracts exist;
- security boundaries exist;
- testing strategy exists;
- sprint tasks map to requirements;
- implementation dependencies are consistent.
