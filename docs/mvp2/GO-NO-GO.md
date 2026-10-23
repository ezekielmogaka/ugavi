# MVP2 GO/NO-GO — Procure-to-Pay + Compliance + Reporting

> **Historical gate snapshot with 2026-10-22 update:** use
> [IMPLEMENTATION.md](./IMPLEMENTATION.md) for current runtime-verified status.
> MVP2 now has substantial W1, W3-W5, W8, W9 and W13 slices, but pilot release
> remains conditional on the explicitly listed integration and policy blockers.

> **Date:** 2026-10-21 | **Author:** Cline Architect
> **Evidence:** BASELINE.md, bench test runs, SCOPE.md, known-gaps.md
> **Target:** Ugavi 0.1.0 on Frappe 16.52.0 + ERPNext 16.51.1 [verified: `bench version`]

---

## W0 PRECONDITION FOR MVP3

MVP3 W0 requires: "Verify MVP1 and MVP2 gates are met. If not, STOP and report."

**Verdict: ❌ MVP2 GATE NOT MET.** Workstreams W1-W13 are specified (SCOPE.md) but NONE are built. Only the `validation-2/` infrastructure work (seed, tests, crypto tests) exists — this is MVP1 scope validation, not MVP2 build.

---

## Gate Criteria

Each criterion is marked PASS ✅, PARTIAL ⚠️, FAIL ❌.

### G1: MVP1 Blockers Resolved — ⚠️ PARTIAL

| Check | Result | Evidence |
|-------|--------|----------|
| Share wrapping inserted (Slice 2) | ❌ FAIL | Code written but NOT inserted into sealed_bid.py |
| Opening ceremony implemented (Slice 3) | ❌ FAIL | Not implemented |
| Seed extended (tenders, bids, PRs) | ✅ PASS | LOKADO seed: 6 PRs, 5 tenders, 15 bids, 1 award, 1 contract |
| 7 stale stubs removed | ✅ PASS | Removed 2026-10-21 |
| Duplicate Tender dir removed | ✅ PASS | Removed 2026-10-21 |
| DocType sync complete | ✅ PASS | 47 DocType JSONs on host; all core DocTypes load |
| Container diverged files committed | ❌ FAIL | Remaining uncommitted host changes |

### G2: MVP2 Workstreams (W1-W13) — ❌ GATE NOT COMPLETE

| Workstream | Status | Evidence |
|-----------|--------|----------|
| W1 Tender Docs & Bid Security | ⚠️ SUBSTANTIAL | Versioned templates, issued addenda and verified security controls exist |
| W2 Evaluation & Award | ⚠️ PARTIAL | COI, comparative summary and standstill enforcement exist; individual sheets/minutes remain |
| W3 Complaints & Appeals | ⚠️ SUBSTANTIAL | Review panel, response target, outcomes, remedies and suspension controls exist |
| W4 Inspection & Acceptance | ⚠️ SUBSTANTIAL | Native Quality Inspection enforced for flagged PO lines |
| W5 Invoices & Three-Way Match | ⚠️ SUBSTANTIAL | Supplier upload, native invoice mapper and line-level match exist |
| W6 Payments | ⚠️ PARTIAL | Native payment records and channels exist; gateway/export/reconciliation remain |
| W7 Budget & Grant Tracking | ⚠️ PARTIAL | Native Budget plus donor/project/activity commitments exist; reports remain |
| W8 Donor Reporting | ⚠️ PARTIAL | Generic reproducible pack exists; scheduling and donor formats remain |
| W9 Records & Retention | ⚠️ SUBSTANTIAL | Seven-year policy, legal hold, archive and approved disposal exist |
| W10 Access & SSO | ⚠️ PARTIAL | Deployment-controlled Frappe TOTP exists; enrolment/access review remain |
| W11 Analytics & Dashboards | ⚠️ PARTIAL | Workspaces/dashboards exist; full acceptance count remains |
| W12 Tax & E-Invoicing | ⚠️ PARTIAL | VAT/WHT configured; eTIMS correctly blocked pending KRA contract |
| W13 Data Import & Migration | ⚠️ SUBSTANTIAL | Private CSV/XLSX validation hands off to native Data Import |

### G3: Cross-Cutting — ⚠️ PARTIAL

| Check | Result | Evidence |
|-------|--------|----------|
| Tests (all passing) | ✅ PASS | 27/27, 0.338s (12 integration + 15 unit) |
| Crypto primitives | ✅ PASS | RSA-4096, AES-256-GCM, SSS |
| `bench migrate` clean | ✅ PASS | Runs successfully |
| Core DocTypes loadable | ✅ PASS | All 6 key DocTypes verified |
| Upgrade safety (no core edits) | ✅ PASS | 0 patches in PATCHES.md |
| Threat model updated for MVP2 | ❌ FAIL | Not done |
| SBOM updated | ❌ FAIL | Not done |

---

## Verdict

### For Demo: ✅ GO (LOKADO-ready)

**The LOKADO demo shows the complete procurement lifecycle:**

- PR → Tender → Sealed-Bid Opening → Award → Contract → Logistics
- 6 donors with dual-funding trail (IOM-Japan)
- Threshold enforcement, SoD, DoA, supplier prequalification
- Full LOKADO tour: `docs/demo/LOKADO-DEMO-TOUR.md`

### For Pilot: ⚠️ CONDITIONAL NO-GO

Core vertical slices are operational. Pilot activation still requires the five
external/policy items in `IMPLEMENTATION.md`: KRA and M-Pesa contracts,
procurement timeline approval, backup/RPO decisions, and privileged TOTP
enrolment.

### For MVP3: ❌ BLOCKED

Per MVP3 W0 requirements, MVP2 gate must be met before beginning multi-tenancy work. The following is the minimum path to unblock:

---

## Minimum Path to MVP3 Start

| Priority | Item | Est. Effort |
|----------|------|-------------|
| P0 | Complete sealed-bid Slice 2 (share wrapping) | 1-2 hours |
| P0 | Complete sealed-bid Slice 3 (opening ceremony) | 3-4 hours |
| P0 | Extend seed: 2 tenders, 3 bids, 2 PRs | 1-2 hours |
| P0 | Build W1 (Tender Documents + Bid Security) | 4-6 hours |
| P1 | Build W5 (PO from approved PR) | 3-4 hours |
| P1 | Build W2 (Evaluation & Award) | 6-8 hours |
| -- | **Total minimum to unblock MVP3** | **18-26 hours** |

Per user instruction, these are listed but NOT built. MVP3 W0 analytical work (hosting ADR, OPEN-QUESTIONS.md) proceeds independently.

---

*Assessment version: 1.0. Gate: MVP2 is NOT MET. Evidence: code inspection, bench test run, known-gaps.md.*