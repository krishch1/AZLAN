# AZLAN — PART 2: AUDIT ENGINE, DISCOVERY & ANALYSIS

## Engine Responsibilities

Target validation, scope enforcement, discovery, evidence collection, passive checks, controlled active checks, findings, correlation, remediation metadata, and verification.

## Engine Layers

```text
Scan Orchestrator
 ├── Scope Policy
 ├── Discovery
 ├── Evidence Store
 ├── Passive Checks
 ├── Active Checks
 ├── API Analysis
 ├── Finding Correlator
 └── Verification
```

## Discovery

Adaptive discovery covers:
- seed URL;
- HTML links/forms;
- redirects;
- robots.txt;
- sitemap.xml;
- static resources;
- JavaScript endpoint strings;
- REST signals;
- GraphQL signals;
- bounded common resources.

Discovery produces normalized resources. It does not automatically authorize active testing.

## Scope Policy

```text
normalize → canonicalize → scope decision → allowed/excluded/unknown
```

Out-of-scope and unknown resources are not actively tested.

## JavaScript

V1 performs basic static endpoint discovery:
- absolute/relative URLs;
- fetch/XHR-style strings;
- WebSocket-looking endpoints;
- REST route hints;
- GraphQL endpoint hints.

No deep JavaScript security analysis in V1.

## REST / GraphQL

REST and GraphQL discovery is comprehensive, while V1 security checks remain basic and externally observable.

## Passive Check Interface

Every passive check exposes:
- stable check ID;
- category;
- applicability;
- evidence requirements;
- evaluation;
- finding output;
- remediation;
- verification strategy.

## Active Check Interface

Every active check declares:
- scope requirement;
- safety class;
- expected side effects;
- rate-limit class;
- timeout;
- evidence requirements;
- cancellation behavior.

The central safety policy cannot be bypassed.

## Evidence

Evidence may contain request/response metadata, normalized URL, status, selected headers/body excerpts, timing, check ID, timestamp, and redaction metadata.

Secrets must be removed before persistence/presentation.

## Finding

```text
finding_id
audit_id
check_id
category
title
severity
confidence
resource
description
evidence_refs
impact
remediation
verification_strategy
status
```

## Verification

```text
previous finding → same check/resource → new evidence
→ resolved / persists / changed / unable to verify
```

## Audit Catalog

The implementation must maintain a machine-readable catalog containing:
`check_id`, `category`, `mode`, `severity`, `safe`, `evidence`, `remediation`, `verification`, `enabled`.

