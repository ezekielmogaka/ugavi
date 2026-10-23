# MVP2 Implementation and Verification Matrix

> **Verified:** 2026-10-22  
> **Runtime:** ERPNext 16.51.1, Frappe 16.52.0, Ugavi 0.1.0  
> **Verdict:** substantial vertical slices delivered; pilot remains conditional.

## Confirmed product decisions

| Decision | Selected outcome |
|---|---|
| Finance system of record | ERPNext |
| Procurement policy | Kenya PPADA/PPRA-aligned configurable controls |
| Budget model | Donor + project + fiscal year, with cost center as activity |
| Payment channels | Bank Transfer and M-Pesa |
| Tax | Kenya VAT and withholding |
| e-invoicing | KRA sandbox boundary; transmission disabled pending contract and credentials |
| Reporting | Generic configurable donor pack first |
| Retention | Seven years by default, with donor-specific policy support |
| Identity | Frappe authentication and TOTP; SSO extension-ready |

## Workstream traceability

| Workstream | Status | Delivered evidence | Remaining acceptance work |
|---|---|---|---|
| W1 Tender documents and security | Substantial | Versioned `Tender Document Template`, template application, issued addenda with bidder notification, independent bid-security verification and validity checks | Presenter UI and policy-approved templates |
| W2 Evaluation and award | Partial | Committee-bound COI declarations, conflicted-member blocking, weighted comparison, enforced resolved standstill before award | Individual scoring sheets, evaluation-session minutes, regret notices, policy routing |
| W3 Complaints | Substantial | Bidder-only intake, active-window enforcement, three-person conflict-free review panel, response target, outcomes, remedial action and award suspension | Statutory timeline legal review and appeal escalation |
| W4 Inspection | Substantial | Native ERPNext Quality Inspection requirement on selected PO lines; submitted inspection enforced before receipt | Seeded partial-rejection acceptance journey and branded report |
| W5 Invoice and match | Substantial | Identity-bound supplier invoice upload; native receipt-to-invoice mapper; line-level PO/receipt/invoice matching; discrepancy task | DoA approval for exceptions and posting/reversal UAT |
| W6 Payments | Partial | Native ERPNext Payment Order/Payment Entry retained; Bank Transfer and M-Pesa modes configured | Bank export format, M-Pesa API credentials/adapter, reconciliation UAT |
| W7 Budgets and grants | Partial | Native Budget reused; donor dimension; project/activity validation; idempotent PO encumbrance, release and reversal | Burn-rate/variance reports and over-budget UAT |
| W8 Donor reporting | Partial | Reproducible generic donor snapshot over procurement, stock, assets, fleet and commitments | Scheduled PDF/XLSX delivery and donor-specific templates |
| W9 Retention | Substantial | Retention policy, active legal hold, private archive requirement, approved disposal request, global delete guard | Approved donor override schedule and archive storage provider |
| W10 Access | Partial | Deployment-controlled Frappe TOTP, password/session hardening | Privileged-user enrolment, access-review report, break-glass procedure |
| W11 Analytics | Partial | Existing Frappe workspaces and dashboards retained | Verify five dashboards, ten cards and three scheduled reports against seed |
| W12 Tax/eTIMS | Partial | Correct non-group VAT Input and WHT accounts; native tax templates; no fake eTIMS acknowledgements | KRA-approved sandbox API contract, credentials and certification tests |
| W13 Import | Substantial | Private CSV/XLSX dry run, required/link/duplicate validation, handoff to native Frappe Data Import | Customer data mapping rehearsal and rollback evidence |

## ERPNext patterns reused

- Purchase Order:
  `erpnext/buying/doctype/purchase_order/purchase_order.py`
- Purchase Invoice:
  `erpnext/accounts/doctype/purchase_invoice/purchase_invoice.py`
- Purchase Receipt and receipt-to-invoice mapper:
  `erpnext/stock/doctype/purchase_receipt/purchase_receipt.py`
- Quality Inspection:
  `erpnext/stock/doctype/quality_inspection/quality_inspection.py`
- Payment Entry and Payment Order:
  `erpnext/accounts/doctype/payment_entry/` and
  `erpnext/accounts/doctype/payment_order/`
- Budget and Accounting Dimension:
  `erpnext/accounts/doctype/budget/` and
  `erpnext/accounts/doctype/accounting_dimension/`
- Data Import:
  `frappe/core/doctype/data_import/data_import.py`
- TOTP:
  `frappe/twofactor/`

Ugavi uses custom fields, app-owned DocTypes, `doc_events`, portal commands and
Frappe workspaces. It does not override ERPNext transaction controllers.

## Verified commands

```bash
make upgrade-check
make seed                # canonical LOKADO seed (alias: seed-lokado)
make demo-check
make fleet-check
make e2e
make tenant-manifest-check
```

Observed results:

- Upstream compatibility: `compatible: true`, zero issues and zero missing controllers.
- DocTypes: 67 Ugavi and 529 ERPNext.
- Backend: 57 tests passed.
- Demo acceptance: 19 users, five supplier identities, fleet and asset evidence,
  zero issues.
- Fleet acceptance: purchase-backed reconciliation and donor isolation passed
  with zero issues.
- Monthly stock reports: USAID receipts/issues 150/20 and IOM receipts/issues
  75/8; both closing balances reconciled.
- Browser: not executed in the 2026-10-22 authoritative rehearsal because the
  host-side Playwright runtime was unavailable. This is an environment gap, not
  a passing browser result.
- Public health: `{"message":"pong"}`.

## Conditional pilot blockers

1. KRA sandbox contract and credentials.
2. M-Pesa disbursement API credentials and reconciliation format.
3. Approved PPRA/legal timeline review.
4. Named backup/archive storage and RPO/RTO.
5. Privileged-user TOTP enrolment before enabling `UGAVI_ENFORCE_2FA=1`.
