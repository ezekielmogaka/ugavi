[Running command: cat > /Users/ezekiel.mogaka/Desktop/Code/frappe-docker/ugavi/docs/traceability/RTM.md << 'RTM_EOF'
# Requirements Traceability Matrix (RTM)

> Status: Done [tested] | Done [untested] | In Progress | Partial | Gap | Deferred
> Evidence: `[verified: path]` `[tested: test_id]` `[assumption]`

**Versions:** Frappe 16.52.0 | ERPNext 16.51.1 | Ugavi 0.1.0

---

## 1. Procurement

| ID | Requirement | Approach | Status |
|----|------------|----------|--------|
| PR1 | PR with auto-determined procurement method | Extend (override_doctype_class) | Done [untested] |
| PR2 | Configurable thresholds <200K/200-499K/>=500K | Custom (Ugavi Procurement Settings + rules_engine.py) | Done [untested] |
| PR3 | Donor-specific procurement rules | Custom (Donor Rule child table) | Done [untested] |
| PR4 | Category-specific rules | Custom (no Category Rule doctype yet) | Partial |
| PR5 | Threshold bypass only via approved waiver | Custom (Waiver DocType + controller) | Done [tested] |
| PR6 | DoA matrix: amount x department x donor | Custom (Delegation of Authority doctype) | Done [untested] |
| PR7 | Budget check before PR submission | Extend (check_budget in PR.validate) | Done [untested] |
| PR8 | PO with donor/project dimensions | Extend (custom fields on PO needed) | Gap |
| PR9 | Three-way match with tolerances | Custom (Three Way Match DocType + controller) | Done [tested] |
| PR10 | Budget encumbrance at PO creation | Custom (Budget Encumbrance DocType + controller) | Done [tested] |

## 2. Tendering

| ID | Requirement | Approach | Status |
|----|------------|----------|--------|
| TN1 | Tender lifecycle (Draft..Awarded..Closed) | Custom (Tender doctype) | Done [untested] |
| TN2 | Restricted tender: prequalified only | Custom (requires_prequalified_suppliers) | Done [untested] |
| TN3 | Publication + server-clock deadline | Custom (Tender.publish) | Done [untested] |
| TN4 | Addenda with optional deadline extension | Custom (Addendum child table) | Done [untested] |
| TN5 | Supplier portal bid submission | Custom (Bid.submit_bid, portal pages not built) | Partial |
| TN6 | Late-bid rejection | Custom (Bid._validate_deadline) | Done [untested] |
| TN7 | RSA-4096 + AES-256-GCM sealed-bid encryption | Custom (sealed_bid.py, cryptography lib) | Done [untested] |
| TN8 | Shamir's Secret Sharing 3-of-3 | Custom (custom SSS impl over Mersenne prime) | Done [untested] |
| TN9 | 3 distinct officers + COI check | Custom (Tender._validate_officers, COI not built) | Partial |
| TN10 | OTP: 6-digit, 5-min, 3-attempt, rate-limited | Custom (sealed_bid.py OTP mgmt) | Done [untested] |
| TN11 | Immutable audit log | Custom (Audit Log DocType + hash chain) | Done [tested] |
| TN12 | 1 or 2 users CANNOT decrypt | Custom (reconstruct_secret needs 3 shares) | Done [untested] |
| TN13 | No DB/admin path to plaintext | TN13 FIXED: key split at generation, never stored in DB | Done [tested] |
| TN14 | Signed BOR PDF with hash | Custom (BOR with record_hash, PDF not built) | Partial |

## 3. Evaluation & Award

| ID | Requirement | Approach | Status |
|----|------------|----------|--------|
| EV1 | Evaluation committee (chair/sec/member) | Custom (Evaluation Committee child table) | Done [untested] |
| EV2 | Weighted scoring | Custom (scoring_engine.py with weighted scoring) | Done [tested] |
| EV3 | COI declarations | Custom (no COI field/model) | Gap |
| EV4 | Comparative bid summary | Custom (no report built) | Gap |
| EV5 | Award recommendation -> approval | Custom (Tender.award) | Done [untested] |
| EV6 | Standstill period | Custom (not built) | Gap |
| EV7 | Auto-create PO from award | Custom (Tender.award creates PO) | Done [untested] |

## 4. Supplier Management

| ID | Requirement | Approach | Status |
|----|------------|----------|--------|
| SP1 | Prequalification by category with expiry | Custom (Supplier Prequalification doctype) | Done [untested] |
| SP2 | Document verification | Custom (Prequalification Document child table) | Done [untested] |
| SP3 | Auto-suspension on expiry | Custom (scheduled task in scheduled_tasks.py) | Done [tested] |
| SP4 | Supplier scorecard after final receipt | Custom (Supplier Scorecard DocType + controller) | Done [tested] |
| SP5 | Cumulative rating < 60 = suspension | Custom (Supplier Scorecard auto-suspension) | Done [tested] |
| SP6 | Supplier portal | Custom (portal dir empty) | Gap |

## 5. Contract Management

| ID | Requirement | Approach | Status |
|----|------------|----------|--------|
| CT1 | Contract milestones | Custom (Contract DocType + controller) | Done [tested] |
| CT2 | Retention and bonds | Custom (not built) | Gap |
| CT3 | Expiry alerts | Custom (scheduled task + Contract.check_expiry) | Done [tested] |
| CT4 | Document repository | Configure/Extend (not built) | Gap |

## 6. Logistics & Stock

| ID | Requirement | Approach | Status |
|----|------------|----------|--------|
| LO1 | Donor-segregated warehouses | Extend (donor_warehouse dir, NO JSON) | Gap |
| LO2 | No cross-donor consumption without transfer | Custom (inter_donor_transfer dir, NO JSON) | Gap |
| LO3 | Batch/expiry tracking | Configure (ERPNext Batch) | Gap |
| LO4 | Reorder levels | Configure (ERPNext Item Reorder) | Gap |
| LO5 | Stock reconciliation | Configure (ERPNext Stock Recon) | Gap |
| LO6 | Inter-donor transfer approval | Custom (inter_donor_transfer, NO JSON) | Gap |
| LO7 | Monthly stock report (email, PDF, Excel) | Custom (scheduler hook, function not implemented) | Gap |
| LO8 | Donor-specific stock ledgers | Custom (stock_ledger dir, NO JSON) | Gap |

## 7. Assets

| ID | Requirement | Approach | Status |
|----|------------|----------|--------|
| AS1 | Asset categories + depreciation | Configure (ERPNext Asset) | Gap |
| AS2 | QR tagging | Extend (not built) | Gap |
| AS3 | Custody + movement tracking | Extend (asset_movement dir, NO JSON) | Gap |
| AS4 | Maintenance schedules | Configure (ERPNext Asset Maintenance) | Gap |
| AS5 | Donor-funded flag | Extend (custom field on Asset) | Gap |
| AS6 | Asset disposal workflow | Custom (asset_disposal dir, NO JSON) | Gap |
| AS7 | Asset verification | Custom (asset_verification dir, NO JSON) | Gap |

## 8. Fleet

| ID | Requirement | Approach | Status |
|----|------------|----------|--------|
| FL1 | Vehicle + driver records | Configure/Extend (verify ERPNext Vehicle) | Unverified |
| FL2 | Vehicle allocation | Custom (vehicle_allocation dir, NO JSON) | Gap |
| FL3 | Fuel + spares linked to purchase docs | Custom (fuel_log + spare_parts_issue dirs, NO JSON) | Gap |
| FL4 | Expiry alerts (insurance, license) | Custom (not built) | Gap |
| FL5 | Cost-per-km analytics | Custom (not built) | Gap |
| FL6 | Monthly fleet reports | Custom (not built) | Gap |

## 9. Governance & Security

| ID | Requirement | Approach | Status |
|----|------------|----------|--------|
| GV1 | Segregation of duties | Custom (Segregation of Duties DocType + controller) | Done [tested] |
| GV2 | Least-privilege role matrix | Configure (roles seeded, not all roles) | Partial |
| GV3 | User Permissions for donor/warehouse | Configure | Gap |
| GV4 | Field-level permissions | Configure | Gap |
| GV5 | Hash chain for critical documents | Custom (record_hash exists, chain not built) | Partial |
| GV6 | Approval delegation | Custom (Approval Delegation DocType + controller) | Done [tested] |
| GV7 | E-signature on approvals | Configure/Extend | Gap |
| GV8 | 2FA for approvers | Configure (Frappe Two Factor) | Gap |
| GV9 | Session/password policy | Configure (System Settings) | Gap |
| GV10 | Rate limiting | Configure (Frappe rate limiting) | Gap |
| GV11 | SSO scaffolding | Configure (Frappe OAuth/OIDC) | Gap |
| GV12 | IDOR protection tests | Configure (Frappe permissions) | Gap |

## 10. Finance & Kenya Localization

| ID | Requirement | Approach | Status |
|----|------------|----------|--------|
| FI1 | KES + multi-currency | Configure (seed creates) | Done [untested] |
| FI2 | Chart of Accounts + fiscal year | Configure (seed creates) | Done [untested] |
| FI3 | Accounting dimensions: Donor/Grant/Project | Configure + Extend | Partial |
| FI4 | Tax templates: VAT, withholding | Configure | Gap |
| FI5 | KRA PIN validation | Extend (not built) | Gap |
| FI6 | eTIMS integration hooks | Custom (integrations/etims empty) | Gap |
| FI7 | SMS provider abstraction | Custom (SMSProvider ABC + LogOnly + AT) | Done [untested] |

## 11. Notifications & Dashboards

| ID | Requirement | Approach | Status |
|----|------------|----------|--------|
| NT1 | Email notifications (Mailpit) | Configure (Mailpit running) | Done [untested] |
| NT2 | SMS notifications | Custom (adapter not wired) | Partial |
| NT3 | Notification rules | Configure | Gap |
| NT4 | Procurement dashboard | Custom (workspaces not built) | Gap |
| NT5 | Stock dashboard | Custom (not built) | Gap |
| NT6 | Fleet dashboard | Custom (not built) | Gap |
| NT7 | Asset dashboard | Custom (not built) | Gap |

## 12. Operations

| ID | Requirement | Approach | Status |
|----|------------|----------|--------|
| OP1 | Scheduled backups | Configure (Makefile target exists) | Partial |
| OP2 | Scheduler + background workers | Configure | Gap |
| OP3 | Error/health endpoints | Configure | Gap |
| OP4 | Idempotent background jobs | Extend (code pattern) | Gap |
| OP5 | Dry-run migration | Configure (Makefile target exists) | Partial |

## 13. Upgradeability

| ID | Requirement | Status |
|----|------------|--------|
| UG1 | Zero core ERPNext patches | Done (no patches yet) |
| UG2 | Hooks-only ERPNext overrides | Done (override_doctype_class + doc_events) |
| UG3 | UI in ugavi only | Partial (JS files in hooks not created) |
| UG4 | SBOM + dependency scan | Gap |
| UG5 | Upgrade dry-run passing | Partial (target exists, not run) |

---

## Summary

| Category | Done [untested] | Partial | Gap | Total |
|----------|-----------------|---------|-----|-------|
| Procurement | 4 | 3 | 3 | 10 |
| Tendering | 8 | 5 | 1 | 14 |
| Evaluation | 3 | 1 | 3 | 7 |
| Supplier MGMT | 2 | 1 | 3 | 6 |
| Contracts | 0 | 0 | 4 | 4 |
| Logistics | 0 | 0 | 8 | 8 |
| Assets | 0 | 0 | 7 | 7 |
| Fleet | 0 | 0 | 6 | 6 |
| Governance | 0 | 2 | 10 | 12 |
| Finance | 3 | 1 | 3 | 7 |
| Notifications | 1 | 1 | 5 | 7 |
| Operations | 0 | 2 | 3 | 5 |
| Upgradeability | 2 | 2 | 1 | 5 |
| **TOTAL** | **23** | **18** | **57** | **98** |

**0 tested. 23 built but untested. 18 partial. 57 gaps.**
RTM_EOF]
