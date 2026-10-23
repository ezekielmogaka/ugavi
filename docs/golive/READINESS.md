# Go-Live Readiness Scorecard — Ugavi 0.1.0

> **Date:** 2026-10-21 | **Prepared by:** Release Manager
> **Scoring:** PASS ✅ / PARTIAL ⚠️ / FAIL ❌ / SKIP (gated) / NA (not in scope)
> **Evidence reference:** G0-PRECONDITIONS.md

---

## Summary

| Gate | Score | Key Blocker |
|------|-------|-------------|
| G0: Preconditions | ❌ FAIL | MVP2 not built, no client, no prod env |
| G1: Production Env | ❌ SKIP | G0 failure |
| G2: Data Migration | ❌ SKIP | G0 failure |
| G3: Acceptance | ❌ SKIP | G0 failure |
| G4: Runbooks | ❌ SKIP | G0 failure |
| G5: Cutover | ❌ SKIP | G0 failure |
| G6: Hypercare | ❌ SKIP | G0 failure |

**Overall: ❌ NOT READY for production go-live.**

---

## G0 Detailed Scorecard

| # | Criterion | Score | Evidence |
|---|-----------|-------|----------|
| G0.1 | MVP1 validation reviewed | ✅ PASS | BASELINE.md reviewed |
| G0.2 | MVP2 validation reviewed | ✅ PASS | GO-NO-GO.md reviewed |
| G0.3 | MVP1 gate met | ⚠️ PARTIAL | CONDITIONAL-GO (demo only) |
| G0.4 | MVP2 gate met | ❌ FAIL | W1-W13 not built |
| G0.5 | MVP3 gate met | ❌ FAIL | Blocked by MVP2 |
| G0.6 | Full test suite passes | ✅ PASS | 27/27, 0.562s |
| G0.7 | Seed check passes | ❌ FAIL | 17 failures |
| G0.8 | Hosting decision confirmed | ❌ FAIL | ADR-006 PROPOSED only |
| G0.9 | Data residency confirmed | ❌ FAIL | Not decided |
| G0.10 | SSH/DB access documented | ❌ FAIL | No production env |
| G0.11 | Threshold boundary confirmed | ❌ FAIL | Not decided |
| G0.12 | Method below threshold confirmed | ❌ FAIL | Not decided |
| G0.13 | Templates confirmed (PR, PO, etc.) | ❌ FAIL | Not decided |
| G0.14 | Sealed-bid key-loss policy | ❌ FAIL | Not decided |
| G0.15 | Sealed-bid officers designated | ❌ FAIL | Not decided |
| G0.16 | Retention periods confirmed | ❌ FAIL | Not decided |
| G0.17 | Tax/e-invoicing scope confirmed | ❌ FAIL | Not decided |
| G0.18 | SSO choice confirmed | ❌ FAIL | Not decided |
| G0.19 | Crypto review commissioned | ❌ FAIL | Not commissioned |
| G0.20 | Penetration test commissioned | ❌ FAIL | Not commissioned |
| G0.21 | Privacy review commissioned | ❌ FAIL | Not commissioned |

### G0 Score: 2 PASS / 1 PARTIAL / 18 FAIL

---

## G1 Detailed Scorecard (Pro Forma — Not Executed)

These criteria would be assessed once G0 passes and a production environment is provisioned:

| # | Pro Forma Criterion | Status |
|---|---------------------|--------|
| G1.1 | Production separate from staging/demo | SKIP |
| G1.2 | No demo seed/credentials in production | SKIP |
| G1.3 | Infrastructure as code | SKIP |
| G1.4 | Pinned versions (Frappe, ERPNext, deps) | SKIP |
| G1.5 | No code/asset mutation at startup | SKIP |
| G1.6 | Secrets in secret store | SKIP |
| G1.7 | TLS configured | SKIP |
| G1.8 | Security headers | SKIP |
| G1.9 | Least-privilege accounts | SKIP |
| G1.10 | 2FA for privileged roles | SKIP |
| G1.11 | SSO configured (if chosen) | SKIP |
| G1.12 | Network exposure minimized | SKIP |
| G1.13 | Admin access audited | SKIP |
| G1.14 | Rate limits | SKIP |
| G1.15 | Dependency/container/secrets scans | SKIP |
| G1.16 | SBOM archived | SKIP |
| G1.17 | Scheduled backups (DB + files) | SKIP |
| G1.18 | Backup encryption | SKIP |
| G1.19 | Backup stored per residency | SKIP |
| G1.20 | Restore tested (measured RPO/RTO) | SKIP |
| G1.21 | Health checks | SKIP |
| G1.22 | Structured logs | SKIP |
| G1.23 | Metrics + dashboards | SKIP |
| G1.24 | Alerting (failed logins, jobs, backups) | SKIP |
| G1.25 | Email/SMS: production provider | SKIP |
| G1.26 | SPF/DKIM/DMARC | SKIP |
| G1.27 | Load test (measured p50/p95) | SKIP |

---

## Path to READY

1. Identify client → confirm decisions D01-D12 → commission external reviews
2. Build MVP2 minimum path (18-26 hrs development)
3. Commit all changes, clean build
4. Provision staging environment
5. Re-run this assessment when G0 scores ≥16 PASS

---

*Document version: 1.0. All unexecuted criteria marked SKIP. No invented scores or assumptions about readiness.*