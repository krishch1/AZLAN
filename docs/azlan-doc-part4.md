# AZLAN — PART 4: PERFORMANCE, OBSERVABILITY & FRONTEND

## Performance

Measure before locking hard numerical targets.

Track:
- audit startup;
- crawl throughput;
- request latency;
- check duration;
- evidence processing;
- finding processing;
- memory;
- storage;
- concurrent audits.

## Resource Budgets

```text
max_audit_duration
max_requests
max_concurrency
max_discovery_depth
max_resources
max_response_size
max_evidence_size
```

Defaults require validation/benchmarking.

## Observability

Structured events:
- audit created;
- validation started/completed;
- resource discovered;
- request attempted;
- check started/completed;
- finding generated/deduplicated;
- audit cancelled/failed/completed.

Logs must be secret-free.

## Frontend

Stack:
- React;
- TypeScript;
- Vite.

Screens:
1. Dashboard
2. Create Audit
3. Audit Progress
4. Audit Results
5. Finding Details
6. Audit History
7. Settings

Finding presentation:
`What was found → Why it matters → Evidence → Affected resource → Confidence → Fix → Verification`

