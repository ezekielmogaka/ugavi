# MVP2 SCOPE — Procure-to-Pay + Compliance + Reporting

> **Date:** 2026-10-21 | **Author:** Cline QA / Architect
> **Source:** Client requirements document, Ugavi architecture, ERPNext 16.51.1 capabilities
> **Status:** PROPOSAL — client decisions needed before building blocked workstreams

---

## Scope Philosophy

MVP2 closes the procure-to-pay loop and adds compliance, control, and reporting. Every workstream must:
1. **Reuse standard ERPNext** DocTypes, workflows, and reports wherever they fit
2. **Extend via custom fields, hooks, service classes** — create custom DocTypes only where proven gap exists
3. **No core edits** — supported extension points only
4. **Configuration over code** — tolerances, approval rules, retention periods, tax rules as settings

---

## Client Decisions Required (BLOCKING)

Before building the blocked workstreams, the client must answer:

| # | Decision | Blocks | Options |
|---|----------|--------|---------|
| D1 | Finance system of record | W5, W6, W7, W8 | (a) ERPNext alone, (b) External + ERPNext sync, (c) Hybrid |
| D2 | Applicable tax regime | W12 | (a) Kenya VAT + withholding, (b) Other, (c) None |
| D3 | E-invoicing / eTIMS | W12 | (a) eTIMS (Kenya), (b) Other e-invoicing, (c) None |
| D4 | Applicable procurement regulation | W1, W2, W3 | (a) PPOA/PPDA (Kenya), (b) Other, (c) Internal policy only |
| D5 | Donor report formats required | W8 | List: USAID, EU, UN, World Bank, GAVI, Global Fund, other |
| D6 | Records retention periods (years) | W9 | (a) 7 years, (b) 10 years, (c) Per-donor schedules |
| D7 | Payment channels | W6 | (a) Bank transfer only, (b) Mobile money (M-Pesa), (c) Both |
| D8 | SSO provider | W10 | (a) Azure AD/OIDC, (b) Google/SAML, (c) LDAP, (d) None |
| D9 | Production domain / SSL | Cross-cutting | Domain name for SSL certs, S3 bucket for backups |
| D10 | Budget/grant structure | W7 | (a) Per-donor/project/year, (b) Per-program/activity, (c) Both |
---

## Workstreams

### W1 — Tender Documents and Bid Security
**Priority:** P0 (Critical) | **Status:** 🟢 UNBLOCKED | **Depends:** MVP1 Tender

Standard tender-document templates, versioned addenda, bid-security records, clarifications log.

- Tender Document Template DocType (attachment + versioning)
- Addendum workflow (draft → issued, notification to bidders)
- Bid Security: amount, instrument, issuing bank, validity, verification, release/forfeiture
- Clarifications Log (child table): Q&A, timestamp, visibility
- Integration: bid security verified before bid opening
- Roles: Procurement Officer, Tender Committee Chair

**ERPNext capability:** No native bid-security. Custom DocType needed.
**Acceptance:** 2 templates, 1 addendum, 1 bid security → verify/forfeit → audit trail.

---

### W2 — Evaluation and Award Hardening
**Priority:** P0 (Critical) | **Status:** 🟢 UNBLOCKED | **Depends:** MVP1 Evaluation, DoA

Committee with COI, weighted scoring, individual sheets, anonymized mode, comparative summary, DoA routing, award/regret notices, standstill enforcement.

- Evaluation Committee: members, roles, COI per member
- Scoring Sheet: per evaluator/bid/criterion (technical + financial)
- Weight calculation: configurable weights, auto-total, anonymized toggle
- Comparative Summary: side-by-side, auto-highlight best-value
- Award Recommendation: routed through DoA for approval
- Award Notice + Regret Notice: email + portal
- Standstill: system-enforced, no award during period
- Minutes: per evaluation session

**ERPNext capability:** No native evaluation/scoring. Custom DocTypes needed.
**Acceptance:** 3-member committee, 2 COIs, 3 scoring sheets, 1 summary, DoA routing, standstill enforced.

---

### W3 — Complaints, Appeals and Disputes
**Priority:** P1 (High) | **Status:** 🟡 READINESS SLICE DELIVERED | **Depends:** W2

Delivered readiness slice: bidder-only supplier portal intake during an active
standstill, private supporting documents, duplicate-open-complaint prevention,
procurement review status/outcome, standstill complaint counts, supplier
resolution notifications, and audit history. Review-panel composition,
policy-specific deadlines, and automatic remedial actions remain MVP2 work.

Supplier complaint intake (portal), deadlines, review panel, outcome, award suspension.

- Complaint DocType: supplier, tender, grounds, date, status
- Review Panel: member assignment, deliberation, outcome
- Deadline tracking: submission window, response timeline
- Outcome: upheld/rejected/partially upheld, remedial action
- Suspension: auto-suspend award during standstill if complaint received
- Full audit trail

**ERPNext capability:** No native complaints. Custom DocType.
**Acceptance:** 1 complaint → reviewed → outcome → audit log complete.

---

### W4 — Goods Inspection and Acceptance
**Priority:** P1 (High) | **Status:** 🟡 PARTIALLY BLOCKED | **Depends:** W5 (PO)

Inspection against PO terms, accept/partial/reject, link to receipt + scorecard.

- Inspection DocType: PO reference, criteria, inspector, date
- Outcome: accept / partial accept / reject with reason
- Link to Stock Entry (goods receipt)
- Supplier Scorecard: quality metric update
- Inspection Report PDF

---

### W5 — Invoices and Three-Way Match
**Priority:** P0 (Critical) | **Status:** 🔴 BLOCKED (D1) | **Depends:** W4

Supplier invoice capture, three-way match, configurable tolerances, exception queue.

- Purchase Invoice linked to PO and Purchase Receipt
- Three-way match: quantity × price × receipt tolerance
- Tolerance config: amount %, quantity %, line-level
- Exception queue + approval via DoA
- Supplier portal: upload invoice, check status
- **BLOCKED:** Will ERPNext be the accounting system of record?

**ERPNext capability:** Native Purchase Invoice, Purchase Receipt, matching engine. Verify.
**Acceptance:** 1 invoice matched within tolerance; 1 exception routed; GL entries correct.

---

### W6 — Payments
**Priority:** P0 (Critical) | **Status:** 🔴 BLOCKED (D1, D7) | **Depends:** W5

Payment request → approval → segregation → payment run → reconciliation.

- Payment Request: linked to invoice, amount, due date
- Approval: DoA routing, segregation enforced
- Payment Run: batch payments, bank export file
- Channel adapter: bank / M-Pesa / both
- Reconciliation: match payment to invoice
- **BLOCKED:** Finance system of record and payment channels

**ERPNext capability:** Native Payment Entry, Payment Request, Payment Order. Verify.
**Acceptance:** 1 payment → approved → run → export → reconciled.

---

### W7 — Budgets and Grants
**Priority:** P1 (High) | **Status:** 🔴 BLOCKED (D1, D10) | **Depends:** W5

Budget per donor/grant/project, commitment tracking, availability, burn-rate reports.

- Budget DocType: donor, project, cost center, period, amount
- Commitment: PR → PO → invoice encumbrance
- Availability check: reject or route over-budget for approval
- Burn rate: actual vs budget, % consumed
- Variance report: budget vs actual vs committed
- Donor eligibility rules: allowed cost categories per donor
- **BLOCKED:** Budget structure and finance system of record

**ERPNext capability:** Native Budget, Accounting Dimension, Cost Center. Verify.
**Acceptance:** 2 donor budgets, 1 over-budget PO routed, burn-rate report balanced.

---

### W8 — Donor Reporting Packs
**Priority:** P2 (Medium) | **Status:** 🔴 BLOCKED (D5) | **Depends:** W7

Per-donor report definitions, branded, scheduled PDF/Excel export, source-of-funds traceability.

- Report Pack Definition: donor, report type, columns, period
- Branding: logo, header, footer as configuration
- Reports: procurement, stock, budget vs actual, asset, fleet
- Scheduled: monthly/quarterly auto-generation + email
- Source-of-funds: requisition → PO → receipt → stock/asset → payment
- **BLOCKED:** Which donor formats are required?

**ERPNext capability:** Native Report Builder, Script Report, Query Report. Extend.
**Acceptance:** 1 donor pack generated, reproducible from seed.

---

### W9 — Records Retention and Legal Hold
**Priority:** P2 (Medium) | **Status:** 🔴 BLOCKED (D6) | **Depends:** None

Retention schedule, legal-hold flag, archival, deletion workflow, audit.

- Retention Schedule: per DocType, period configurable
- Legal Hold: flag prevents deletion of specific records
- Archival: export JSON/CSV/PDF before deletion
- Deletion: approval workflow, audit trail
- Never delete audited or sealed-bid records outside policy
- **BLOCKED:** Retention periods (7 or 10 years? per-donor?)

**ERPNext capability:** Frappe has no native retention/deletion. Custom DocType + scheduler.
**Acceptance:** 1 record under hold → deletion blocked; 1 expired → approved deletion.

---

### W10 — Access Control
**Priority:** P1 (High) | **Status:** 🔴 BLOCKED (D8) | **Depends:** None

2FA for sensitive roles, SSO, session policy, password policy, access reviews.

- 2FA enforcement: Tender Committee, Finance Approver, System Admin
- SSO: OIDC, SAML, or LDAP as chosen
- Session policy: timeout, max concurrent, IP restriction
- Password policy: complexity, expiry, history
- Access review: users × roles × permissions report
- Privileged-access logging
- Break-glass procedure
- **BLOCKED:** Which SSO provider?

**ERPNext capability:** Frappe 16 supports OIDC, SAML, LDAP, TOTP 2FA. Verify.
**Acceptance:** 2FA enforced, SSO login, access review report generated.

---

### W11 — Analytics and Dashboards
**Priority:** P2 (Medium) | **Status:** 🟢 UNBLOCKED | **Depends:** W5, W7

Role-based dashboards, charts, saved reports, scheduled emails.

- Dashboards: Procurement, Finance, Program, Fleet, Warehouse
- Charts: cycle times, spend by donor/category/supplier, tender savings, supplier score, stock turnover, expiry risk, budget burn, fleet cost, asset utilization
- Saved reports + scheduled emails
- Every metric traceable to query, tested on seed

**ERPNext capability:** Native Dashboard, Number Card, Chart. Extend.
**Acceptance:** 5 dashboards, 10 number cards, 3 scheduled reports, balanced.

---

### W12 — Tax and E-Invoicing
**Priority:** P3 (Low) | **Status:** 🔴 BLOCKED (D2, D3) | **Depends:** W5

VAT and withholding tax, e-invoicing adapter behind interface.

- Tax templates: VAT, withholding (varying rates)
- Auto-calculation on Purchase Invoice
- eTIMS adapter: behind interface, sandbox-only until live test
- **BLOCKED:** Tax regime and e-invoicing requirement
- **WARNING:** Never claim live e-invoicing without sandbox test

**ERPNext capability:** Native Sales/Purchase Taxes and Charges Template.
**Acceptance:** 1 invoice with VAT + withholding; eTIMS stub if confirmed.

---

### W13 — Data Import and Migration
**Priority:** P3 (Low) | **Status:** 🟢 UNBLOCKED | **Depends:** None

Import templates, dry-run, error reports, idempotency, migration runbook.

- Templates: suppliers, items, opening stock, assets, vehicles, users
- Dry-run mode: validate before commit
- Error reports: row-level + summary
- Idempotency: re-run without duplicates
- Migration runbook: step-by-step + rollback
- Support CSV and Excel

**ERPNext capability:** Native Data Import tool. Extend with validators + templates.
**Acceptance:** Dry-run 100 suppliers → error report → fix → import → verify counts.

---

## Cross-Cutting Requirements

### Security
- Threat-model addendum for payments, invoices, complaints, retention
- Permission + IDOR tests per endpoint
- Secrets via environment/vault only
- Dependency + container scans (Trivy)
- SBOM updated (CycloneDX)

### Data Integrity
- Transactional boundaries for postings
- Idempotent scheduler jobs
- Concurrency tests: double approval, double payment, simultaneous match
- Reconciliation queries must balance

### Performance & Reliability
- P50/P95 on new screens at seeded volumes
- Backup/restore re-tested
- Upgrade rehearsal on data copy

### UI/UX
- Ugavi design system extensions
- Role-based workspaces updated
- Approval inbox covers new DocTypes
- WCAG 2.2 AA re-check

### Anti-Pattern Controls
- CI green: no core edits, no private imports, no hard-coded thresholds
- No duplicate scripts or orphan DocTypes
- Migration idempotency test
- Update technical-debt.md

---

## Workstream Dependency Order

```
W0 → W1 → W2 → W3
        ↓
  W4 → W5 → W6
        ↓
  W7 → W8

W9, W10 (parallel)
W11 (after W5, W7)
W13 (any time)
W12 (only if D2/D3 confirmed)
```

## Per-Workstream Deliverables

1. Code: DocTypes, hooks, services, custom fields, workflows
2. Tests: Unit + integration + negative paths
3. Docs: Guideline + use cases
4. Seed: Demo data in seed_demo.py
5. Evidence: Atom traceability, measured results

---

*Document version: 1.0 — PROPOSAL. Decisions D1-D10 needed for blocked workstreams.*
**ERPNext capability:** Native Quality Inspection DocType. Verify for v16.53.0.
**Acceptance:** 1 inspection → partial accept → stock receipt → scorecard update.