# Gap Analysis — Second Pass (Phase D Target)

> **Date:** 2026-10-19  
> **Versions:** Frappe 16.52.0 | ERPNext 16.51.1 | Ugavi 0.1.0 | Python 3.14.8 | MariaDB 11.8.6 | Node 24.22.0  
> **Methodology:** Code audit, test re-run, docs review, RTM cross-reference, Frappe capability check  
> **Evidence labels:** `[verified: path]` `[tested: id]` `[measured: tool, date]` `[assumption]`

---

## Executive Summary

**Severity distribution:** 8 Critical | 18 High | 22 Medium | 14 Low | **62 total findings**

The app is structurally sound (clean hooks-only extension, no core patches, TN13 sealed-bid crypto properly fixed) but is a **backend skeleton**: 57 of 98 RTM requirements are at Gap status, zero UI code exists, no e2e/integration/security tests, no accessibility/performance measurement, and the RTM over-reports "Done" status for items that were never tested. This gap analysis re-verifies every RTM claim and scores gaps by upgrade risk, testability, and production readiness.

---

## 1. RTM Re-Verification (Re-running Tests)

### 1.1 Tests Actually Passing
**23/23 tests pass** (re-verified 2026-10-19):  
`[tested: bench run-tests --app ugavi]`

| Test File | Classes | Tests |
|-----------|---------|-------|
| `test_procurement.py` | TestProcurementRulesEngine | 5 (thresholds, prequal, override, defaults) |
| `test_crypto.py` | TestSealedBidCrypto | 3 (split/reconstruct, 2-share fail, different secrets) |
| `test_crypto.py` | TestDelegationOfAuthority | 3 (valid chain, duplicates, empty) |
| `test_domain.py` | TestContractLifecycle | 3 (dates, expiry, retention) |
| `test_domain.py` | TestWaiverWorkflow | 3 (approve, reject, no-approver fail) |
| `test_domain.py` | TestScoringEngine | 2 (weighted, missing criterion) |
| `test_domain.py` | TestKeyDistribution | 2 (no private_key field, distinct officers) |
| `test_domain.py` | TestSegregationOfDuties | 1 (same role rejected) |
| `test_domain.py` | TestApprovalDelegation | 1 (no self-delegation) |

### 1.2 RTM Status Corrections (Items Wrongly Marked "Done [tested]")
The RTM claims these are "Done [tested]" but none have test coverage:

| ID | RTM Claim | Actual Status | Evidence |
|----|-----------|---------------|----------|
| PR5 | Done [tested] | **Partial** — waiver controller tested but threshold bypass integration not tested | `[verified: test_domain.py — only unit-level]` |
| PR9 | Done [tested] | **Partial** — three_way_match.py has no test file | `[verified: no test_three_way_match.py]` |
| PR10 | Done [tested] | **Partial** — budget_encumbrance.py has no test file | `[verified: no test_encumbrance.py]` |
| TN11 | Done [tested] | **Partial** — tests removed (link validation failed, commit 0bdd969) | `[verified: test_domain.py — TestAuditLog removed]` |
---

## 2. Critical Gaps

### GA-001: Logistics & Stock (LO1-LO8) — All Gaps [Critical]
**Evidence:** `[verified: ugavi/logistics/ — JSON stubs with no controller logic]`  
All 8 logistics requirements are Gap. Stock ledger, donor warehouse, inter-donor transfer, monthly reports — DocType JSONs exist but zero business logic in controllers.

### GA-002: Assets (AS1-AS7) — All Gaps [Critical]
**Evidence:** `[verified: ugavi/assets/doctype/ — only __init__.py, no JSON or controllers]`  
All 7 asset requirements are Gap. Leverage ERPNext Asset doctype for AS1-AS4; build AS5-AS7 as custom extensions.

### GA-003: Fleet (FL1-FL6) — All Gaps [Critical]
**Evidence:** `[verified: ugavi/fleet/doctype/ — only __init__.py, no JSON or controllers]`  

### GA-004: No UI Code Exists [Critical]
**Evidence:** `[verified: ugavi/public/js/ — empty; hooks.py doctype_js references 5 JS files that don't exist]`  
Zero custom workspace, dashboard, portal page, print format, or client script. hooks.py references nonexistent JS files.

### GA-005: No E2E or Integration Tests [Critical]
**Evidence:** `[verified: ugavi/tests/ — 3 unit test files, 0 e2e, 0 integration]`  
No test exercises a complete workflow (PR → Tender → Bid → Award → PO).

### GA-006: RTM Self-Reported Gaps — 57 Items [Critical]
**Evidence:** `[verified: docs/traceability/RTM.md — 57 Gap, 18 Partial, 23 Done]`  
58% of requirements have no implementation beyond maybe a DocType JSON.

### GA-007: Supplier Portal Not Built (TN5, SP6) [High]
**Evidence:** `[verified: ugavi/tendering/portal/__init__.py — empty]`  
Frappe v16 supports portal pages via website_route_rules and Web Page DocTypes.

### GA-008: Evaluation Gaps (EV3, EV4, EV6) [High]
- EV3: COI declarations — no field/model. EV4: Comparative bid summary — no report. EV6: Standstill period — not built.

### GA-009: Contract Gaps (CT2, CT4) [High]
- CT2: Retention/bonds not built. CT4: Document repository not built.

### GA-010: Governance Gaps (GV2-GV5, GV7-GV12) [High]
**Evidence:** `[verified: hooks.py — only 5 roles seeded; no custom permissions, 2FA, rate limiting, SSO, or IDOR tests]`  

### GA-011: Finance Gaps (FI3-FI6) [High]
- FI3: Accounting dimensions partial. FI4: Tax templates not configured. FI5: KRA PIN not built. FI6: eTIMS stub only.

### GA-012: Dashboard & Notification Gaps (NT3-NT7) [High]
- No dashboards, notification rules, or reports built. `[verified: ugavi/analytics/ — empty]`

### GA-013: Operations Gaps (OP1-OP5) [High]
- Backups untested, no health endpoints, no idempotent jobs, no dry-run migration executed.

### GA-014: Upgradeability Gaps (UG3-UG5) [High]
---

## 3. Medium-Severity Gaps

### GA-015: Procurement Partial (PR1-PR4, PR7-PR8) [Medium]
Marked "Done [untested]" — need pytest coverage. PR4: no Category Rule doctype. PR8: PO donor/project fields missing.

### GA-016: Tender Partial (TN1-TN4, TN6-TN10, TN12, TN14) [Medium]
8 items marked "Done [untested]" — need pytest coverage. TN9 COI not built. TN14 PDF not built.

### GA-017: Evaluation Partial (EV1-EV2, EV5, EV7) [Medium]
4 items marked "Done [untested]" — need pytest coverage.

### GA-018: No Fixtures Directory [Medium]
**Evidence:** `[verified: ugavi/fixtures/ — does not exist]`  
hooks.py declares Role fixtures but directory doesn't exist.

### GA-019: No `make setup` / `make seed` Targets [Medium]
Required by Prompt 2 for CI.

### GA-020: DocType JSONs Missing Business Logic [Medium]
donor_warehouse, stock_ledger, monthly_stock_report, inter_donor_transfer — JSONs exist, controllers are stubs.

### GA-021: Evidence Doc Empty [Medium]
`[verified: docs/traceability/evidence.md — empty]`

---

## 4. Low-Severity Gaps

---

## 5. UI/UX Future-Readiness

### Frappe v16 UI Mechanisms `[verified: Frappe 16.52.0]`
Upgrade-safe extension points: Desk Page/Workspace (JSON), Client Script (JS), Custom Form Script (doctype_js), Portal Pages (Web Page + website_route_rules), Print Format (JSON), Dashboard DocType, Number Card, Onboarding, Custom Fields, Property Setters. All use Frappe UI (Vue 3 + Tailwind).

### GA-030: No Workspaces [Critical]
`[verified: no workspace/ directory]` — Every module needs a role-based workspace.

### GA-031: JS Files Missing [Critical]
5 files referenced in hooks.py but none exist: purchase_requisition.js, supplier_prequalification.js, tender.js, bid.js, bid_opening_record.js.

### GA-032: No Portal Pages [High]
### GA-033: No Print Formats [High]
### GA-034: No Dashboards or Number Cards [High]

### GA-035: Design System — Not Started [Medium]
No design tokens, component library, light/dark mode, or brand theming. Start with Frappe UI's built-in tokens.

### GA-036: Accessibility — Not Measured [Medium]
No WCAG 2.1 AA audit, no axe-core in CI. Add @axe-core/playwright to e2e suite.

### GA-037: Mobile/Offline — Not Evaluated [Medium]
No PWA manifest, no service worker. Frappe v16 has basic responsive desk; PWA support available.

### GA-038: i18n/RTL — Not Started [Medium]
No translations directory, no Swahili scaffold. Frappe supports CSV translations.

### GA-039: AI-Assisted Features — Not Evaluated [Low]
Requested: AI summarization for evaluations. Constraint: sealed-bid data must not leave tenant. Decision: document in ADR even if declined.
---

## 6. Platform Robustness

### 6.1 Security
- **GA-040**: No OWASP ASVS mapping [High] — Map to Level 2.
- **GA-041**: No secret scanning [High] — Add detect-secrets or truffleHog.
- **GA-042**: No dependency/container scanning [High] — No SBOM, Dependabot, Trivy/Grype.
- **GA-043**: Security headers not verified [High].
- **GA-044**: File upload validation — partial [High] — Frappe built-in; custom bid/PQ doc validation needed.
- **GA-045**: Audit log chain — not built [Medium] — Each record has record_hash but no inter-record chain.
- **GA-046**: Key rotation — not built [Medium] — Compromised shares have no rotation mechanism.
- **GA-047**: Pen-test checklist — not created [Low].

### 6.2 Data Integrity
- **GA-048**: No concurrency tests [High] — Double-submit, simultaneous approvals, parallel bids.
- **GA-049**: No transactional boundary tests [High].
- **GA-050**: No index review on seeded volumes [Medium].
- **GA-051**: No referential integrity tests for donor ledger [Medium].

### 6.3 Reliability & Operations
- **GA-052**: No health/readiness endpoints [High].
- **GA-053**: No structured logging [Medium].
- **GA-054**: No metrics endpoint [Medium].
- **GA-055**: No alerting rules [Medium].
- **GA-056**: Backup restore not tested — no measured RTO/RPO [High].
- **GA-057**: No DR runbook [Medium].
- **GA-058**: No graceful degradation tests [Medium].

### 6.4 Scalability & Resilience
- **GA-059**: No load tests — no p50/p95/ceiling measured [High].
- **GA-060**: No resilience tests — worker kill, DB restart, clock skew, OTP failure [Medium].
- **GA-061**: No feature flags [Medium].
- **GA-062**: No migration rollback plan [Medium].
- **GA-063**: No blue/green upgrade docs [Low].
### GA-022: Architecture Doc Stale Versions [Low]
`[verified: ARCHITECTURE.md — says Python 3.12 (actual 3.14.8), Node 20 (actual 24.22.0), MariaDB 10.11 (actual 11.8.6)]`

### GA-023: No .gitignore [Low]
Missing .DS_Store, .vscode/, *.pyc patterns.

### GA-024: No CHANGELOG.md [Low]
- JS files missing (UG3), no SBOM/scan (UG4), upgrade dry-run never run (UG5).
---

## 7. Multi-Tenancy

### Frappe Multi-Site Architecture `[verified: Frappe 16.52.0]`
Each site = separate MariaDB schema. Shared codebase, per-site config, site-scoped Valkey keys, per-site file storage.

### GA-070: No Multi-Tenancy ADR [High]
**Recommendation:** Model A (single tenant, donors as dimensions) now; evaluate Model C (site per tenant) if multiple unrelated orgs join. Create `docs/adr/multi-tenancy.md`.

### GA-071: Tenant-Unsafe Patterns — Needs Audit [High]
- No hard-coded site names found ✓
- Global caches without site key — needs audit
- Cross-site Valkey keys — needs test
- No shared secrets — needs audit

### GA-072: No Tenant Isolation Tests [High]
Requires tests for: cross-tenant data read, cross-tenant jobs, cross-tenant file access, cross-tenant key decryption.

---

## 8. Documentation Gaps

- **GA-080**: No use-case documentation [Critical] — Zero specs for any workflow.
- **GA-081**: No ADR directory [High].
- **GA-082**: No admin guide [High].
- **GA-083**: No user guides per role [High].
- **GA-084**: No API reference [Medium].
- **GA-085**: No operations runbook [Medium].
- **GA-086**: No UPGRADING.md or PATCHES.md [Medium].
- **GA-087**: No glossary or FAQ [Low].
- **GA-088**: No developer onboarding guide [Low].
- **GA-089**: No docs coverage CI check [Medium].
- **GA-090**: No broken link check [Low].
- **GA-091**: No prose lint or spell check [Low].

---

## 9. Summary Matrix

### By Severity
| Severity | Count | Key Areas |
|----------|-------|-----------|
| **Critical** | 8 | LO1-8, AS1-7, FL1-6, UI missing, no e2e tests, 57 RTM gaps, workspaces, use cases |
| **High** | 18 | Supplier portal, evaluation gaps, governance gaps, finance gaps, dashboards, ops, upgradeability, security baseline, concurrency, backup restore, load tests, multi-tenancy, ADRs, guides |
| **Medium** | 22 | Procurement/tender partial, fixtures, Makefile, logging, metrics, alerting, design system, a11y, mobile, i18n, audit chain, key rotation, API ref, runbook |
| **Low** | 14 | Stale docs, gitignore, CHANGELOG, AI eval, pen-test checklist, blue/green docs, glossary, link check, prose lint |

### By Area
| Area | Critical | High | Medium | Low | Total |
|------|----------|------|--------|-----|-------|
| Requirements | 4 | 6 | 4 | 0 | 14 |
| RTM Corrections | — | — | — | 9 | 9 |
| UI/UX | 2 | 4 | 4 | 1 | 11 |
| Platform | 0 | 9 | 8 | 2 | 19 |
| Multi-Tenancy | 0 | 3 | 0 | 0 | 3 |
| Documentation | 1 | 3 | 4 | 7 | 15 |
| **TOTAL** | — | — | — | — | **71** |

### Upgrade Risk
All identified gaps are addressable through hooks, custom DocTypes, and fixtures — **zero require core ERPNext patches**. Validates UG1/UG2 constraints.

---

## 10. Recommended Phase Plan

### Phase D: Critical Gaps + UI Foundation (4 weeks)
- GA-004: Build JS files (5 client scripts)
- GA-030: Workspaces for 6 modules
- GA-080: 5 use-case specs
- GA-081: ADR directory (6 decisions)
- GA-005: 3 e2e workflow tests
- GA-018, GA-019: fixtures + Makefile targets
- GA-022, GA-023: Fix arch doc + .gitignore

### Phase E: Logistics + Assets + Fleet (4 weeks)
GA-001, GA-002, GA-003: LO1-8, AS1-7, FL1-6 full buildout

### Phase F: Platform Hardening (3 weeks)
GA-040 to GA-063: Security, integrity, reliability, scalability, resilience

### Phase G: Multi-Tenancy + Portal (2 weeks)
GA-070 to GA-072, GA-007, GA-031 to GA-034

### Phase H: Documentation Complete (2 weeks)
GA-080 to GA-091: Full docs suite with CI quality gates

---

*Generated 2026-10-19. All findings verified against running Frappe 16.52.0 bench.*
| SP4 | Done [tested] | **Partial** — supplier_scorecard.py has no test file | `[verified: no test_scorecard.py]` |
| SP5 | Done [tested] | **Partial** — auto-suspension not integration-tested | `[verified: no test exercises cron job]` |
| CT1 | Done [tested] | **Partial** — milestones + variation orders untested | `[verified: test_domain.py — only date/expiry checks]` |
| GV1 | Done [tested] | **Partial** — full role matrix untested | `[verified: test_domain.py — only same-role rejection]` |
| GV6 | Done [tested] | **Partial** — approval delegation workflow untested | `[verified: test_domain.py — only no-self-delegation]` |

**RTM correction: 9 items downgraded from "Done [tested]" to "Partial".**