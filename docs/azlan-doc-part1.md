# AZLAN — PART 1: FOUNDATIONS, REQUIREMENTS & SYSTEM ARCHITECTURE

## Product Vision `[LOCKED]`

AZLAN is a production-grade web application security auditing platform that helps developers secure their websites by auditing essential security aspects, identifying security problems, explaining those problems with evidence and context, providing actionable remediation guidance, and allowing developers to verify fixes through re-auditing.

**Core loop:** `Audit → Understand → Fix → Verify`

## Primary User `[LOCKED]`

Individual developers auditing websites they are authorized to test.

## Primary Workflow `[LOCKED]`

```text
Developer → Website + optional configuration → AZLAN Audit
→ Discover → Analyze → Findings → Fix → Re-Audit → Verify
```

## Goals

- Audit essential website security domains.
- Discover the application surface before testing.
- Produce evidence-backed findings.
- Make findings actionable.
- Support one developer-provided authenticated context.
- Support re-auditing and verification.
- Keep the core zero-cost and locally runnable.
- Maintain production-grade security boundaries.

## V1 Non-Goals

- Destructive exploitation.
- Malware/persistence testing.
- Full client-side JavaScript security research.
- Enterprise multi-tenancy.
- Cloud-scale distributed scanning.
- Mandatory AI/LLM.
- Guaranteed detection of every vulnerability.
- Unbounded fuzzing/brute force.

## Locked Audit Scope

| ID | Domain | V1 |
|---|---|---|
| AS-001 | Target/configuration | URL + optional auth/scan configuration |
| AS-002 | Discovery | Full application surface |
| AS-003 | Crawling | Adaptive |
| AS-004 | JavaScript | Basic endpoint discovery |
| AS-005 | REST | Comprehensive discovery + basic security checks |
| AS-006 | GraphQL | Comprehensive discovery + basic security checks |
| AS-007 | HTTPS/TLS | Comprehensive |
| AS-008 | HTTP security headers | Comprehensive |
| AS-009 | Cookies/sessions | Comprehensive |
| AS-010 | Authentication | Basic |
| AS-011 | Authorization | Basic externally observable checks |
| AS-012 | Input/injection | Basic/common |
| AS-013 | Information disclosure | Comprehensive |
| AS-014 | Security misconfiguration | Basic/common |
| AS-015 | Finding analysis | Evidence-based |
| AS-016 | Re-audit | Before/after verification |
| AS-017 | Active scope | Authorized target only |
| AS-018 | Active safety | Controlled/non-destructive |
| AS-019 | Active limits | Resource/request/concurrency limits |
| AS-020 | Evidence | Sufficient evidence required |

## Functional Requirements

### Target Management
FR-001 Create Audit `[LOCKED]`
FR-002 Configure Audit `[LOCKED]`
FR-003 Validate Target `[LOCKED]`

### Discovery
FR-004 Discover Application Surface `[LOCKED]`
FR-005 Adaptive Crawling `[LOCKED]`
FR-006 JavaScript Endpoint Discovery `[LOCKED]`

### Authentication
FR-007 Support Developer-Provided Authentication `[LOCKED]`
FR-008 Support Single Authenticated Context `[LOCKED]`

### Passive Analysis
FR-009 Perform Passive Auditing `[LOCKED]`
FR-010 Audit HTTPS/TLS `[LOCKED]`
FR-011 Audit HTTP Security Headers `[LOCKED]`
FR-012 Audit Cookies and Sessions `[LOCKED]`
FR-013 Detect Information Disclosure `[LOCKED]`
FR-014 Detect Security Misconfiguration `[LOCKED]`

### Active Analysis
FR-015 Perform Active Auditing `[LOCKED]`
FR-016 Perform Injection Testing `[LOCKED]`
FR-017 Perform Authentication Checks `[LOCKED]`
FR-018 Perform Authorization Checks `[LOCKED]`

### APIs
FR-019 Audit REST APIs `[LOCKED]`
FR-020 Audit GraphQL APIs `[LOCKED]`

### Findings
FR-021 Generate Security Findings `[LOCKED]`
FR-022 Collect Finding Evidence `[LOCKED]`
FR-023 Reduce Duplicate Findings `[RECOMMENDED]`
FR-024 Provide Finding Context `[LOCKED]`

### Remediation
FR-025 Provide Remediation Guidance `[LOCKED]`
FR-026 Support Finding Verification `[LOCKED]`
FR-027 Track Finding Resolution `[RECOMMENDED]`

### Execution
FR-028 Track Audit State `[LOCKED]`
FR-029 Handle Audit Failure `[LOCKED]`
FR-030 Support Audit Cancellation `[RECOMMENDED]`

### Results
FR-031 Display Audit Results `[LOCKED]`
FR-032 Filter and Organize Findings `[RECOMMENDED]`

### Re-audit
FR-033 Re-run Audit `[LOCKED]`
FR-034 Verify Previous Findings `[LOCKED]`
FR-035 Preserve Audit History `[RECOMMENDED]`

### Safety
FR-036 Enforce Target Scope `[LOCKED]`
FR-037 Enforce Active-Test Safety `[LOCKED]`
FR-038 Enforce Resource Limits `[LOCKED]`

## NFR Categories

- NFR-SEC Security
- NFR-REL Reliability
- NFR-PERF Performance
- NFR-SCL Scalability
- NFR-MNT Maintainability
- NFR-EXT Extensibility
- NFR-OBS Observability
- NFR-PRV Privacy & Data Handling
- NFR-USE Usability
- NFR-CMP Compatibility
- NFR-TST Testability
- NFR-DEP Deployment & Operations
- NFR-SAF Safety

The detailed category specifications are distributed across Parts 1–6.

## Architecture Constraints

- Modular monolith + dedicated worker.
- PostgreSQL is the source of truth.
- PostgreSQL-backed queue avoids another mandatory infrastructure service.
- Active scanning never becomes authorized merely because a resource was discovered.
- Credentials are secrets.
- Browser automation is isolated behind an adapter.
- Core detection/remediation works without an LLM.
