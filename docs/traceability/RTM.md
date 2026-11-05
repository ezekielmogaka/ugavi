# Requirements Traceability Matrix (RTM) — Ugavi 0.1.0

> **Versions:** Frappe 16.53.0 | ERPNext 16.52.1 | Ugavi 0.1.0
> **Updated:** 2026-10-23 (persona access, real opening ceremony and submitted-data gates)
> **Status:** Done [tested] | Done [controller] | Configured | Gap

---

## 1. Procurement

| ID | Requirement | Approach | Status | Evidence |
|----|------------|----------|--------|----------|
| PR1 | Auto-determined method | App-owned Purchase Requisition controller + rules service | Done [controller] | `ugavi/procurement/doctype/purchase_requisition/` |
| PR2 | Configurable thresholds | rules_engine.py | Done [controller] | procurement/services/rules_engine.py |
| PR3 | Donor-specific rules | Donor Rule + rules engine | Done [controller] | procurement/services/rules_engine.py |
| PR4 | Category-specific rules | Category Rule DocType | Done [controller] | procurement/doctype/category_rule/ |
| PR5 | Waiver for bypass | Waiver DocType + controller | Done [tested] | test_domain.py::TestWaiverWorkflow |
| PR6 | DoA matrix | Delegation of Authority | Done [controller] | procurement/doctype/delegation_of_authority/ |
| PR7 | Budget check before PR | budget_encumbrance.py | Done [controller] | procurement/services/budget_encumbrance.py |
| PR8 | PO with donor dimensions | Prefixed ERPNext Purchase Order Custom Fields | Done [controller] | `ugavi/scripts/setup_config.py` |
| PR9 | Three-way match | Three Way Match DocType | Done [controller] | `ugavi/compliance/doctype/three_way_match/` |
| PR10 | Budget encumbrance | Budget Encumbrance DocType | Done [controller] | `ugavi/compliance/doctype/budget_encumbrance/` |

## 2. Tendering

| ID | Requirement | Approach | Status | Evidence |
|----|------------|----------|--------|----------|
| TN1 | Tender lifecycle | Tender DocType + controller | Done [controller] | tendering/doctype/tender/ |
| TN2 | Restricted: prequalified | requires_prequalified_suppliers | Done [controller] | tendering/doctype/tender/tender.py |
| TN3 | Publication + deadline | Tender.publish + deadline check | Done [controller] | tendering/doctype/tender/tender.py |
| TN4 | Addenda + extension | Addendum child table | Done [controller] | tendering/doctype/addendum/ |
| TN5 | Supplier portal bids | Identity-scoped portal service + Bid.submit_bid | Done [tested] | `ugavi/procurement/portal/supplier_portal.py`; `tests/e2e/demo.spec.ts` |
| TN6 | Late-bid rejection | Bid._validate_deadline | Done [controller] | procurement/doctype/bid/bid.py |
| TN7 | RSA-4096 + AES-256-GCM | sealed_bid.py (cryptography) | Done [controller] | tendering/services/sealed_bid.py |
| TN8 | SSS 3-of-3 key split | Custom SSS / Mersenne prime | Done [tested] | test_crypto.py::TestSealedBidCrypto |
| TN9 | 3 officers + COI | COI Declaration + BOR | Done [controller] | tendering/doctype/coi_declaration/ |
| TN10 | OTP: 6-digit/5-min/3-retry | sealed_bid.py OTP mgmt | Done [controller] | tendering/services/sealed_bid.py |
| TN11 | Immutable audit log | Audit Log + hash chain | Done [tested] | governance/services/hash_chain.py |
| TN12 | 1/2 users cannot decrypt | SSS needs 3 shares | Done [tested] | test_crypto.py (2-share fail) |
| TN13 | No DB plaintext path | Key split; never stored | Done [tested] | test_crypto.py::TestKeyDistribution |
| TN14 | Signed BOR PDF | BOR controller + hash chain | Done [controller] | tendering/doctype/bid_opening_record/ |

## 3. Evaluation & Award

| ID | Requirement | Status | Evidence |
|----|------------|--------|----------|
| EV1 | Evaluation committee | Done [controller] | tendering/doctype/evaluation_committee/ |
| EV2 | Weighted scoring | Done [tested] | test_domain.py::TestScoringEngine |
| EV3 | COI declarations | Done [controller] | tendering/doctype/coi_declaration/coi_declaration.py |
| EV4 | Comparative bid summary | Done [controller] | tendering/doctype/bid_evaluation_summary/ |
| EV5 | Award -> approval | Done [controller] | tendering/doctype/tender/tender.py |
| EV6 | Standstill period | Done [controller] | tendering/doctype/standstill_period/ |
| EV7 | Auto-create PO from award | Done [controller] | tendering/doctype/tender/tender.py |

## 4. Supplier Management

| ID | Requirement | Status | Evidence |
|----|------------|--------|----------|
| SP1 | Prequalification + expiry | Done [controller] | Supplier portal and `Supplier Prequalification` |
| SP2 | Document verification | Done [controller] | Private owner-checked upload and document child rows |
| SP3 | Auto-suspension on expiry | Done [controller] | Scheduled prequalification lifecycle |
| SP4 | Performance scorecard | Done [controller] | `Ugavi Supplier Evaluation` linked to Purchase Receipt |
| SP5 | Cumulative rating -> suspend | Done [controller] | Supplier evaluation controller |
| SP6 | Supplier portal | Done [tested] | Profile, prequalification, opportunities, bids, clarifications, awards, contracts, deliveries, evaluations, notifications |

## 5. Contract Management

| ID | Requirement | Status |
|----|------------|--------|
| CT1 | Milestones + variations | Done [controller] |
| CT2 | Retention and bonds | Done [controller] |
| CT3 | Expiry alerts | Done [controller] |
| CT4 | Document repository | Done [controller] |

## 6. Logistics & Stock

| ID | Requirement | Status |
|----|------------|--------|
| LO1 | Donor-segregated warehouses | Done [controller] |
| LO2 | No cross-donor consumption | Done [controller] |
| LO3 | Batch/expiry tracking | Done [controller] |
| LO4 | Reorder levels | Done [controller] |
| LO5 | Stock reconciliation | Done [controller] |
| LO6 | Inter-donor transfer | Done [controller] |
| LO7 | Monthly stock report | Done [controller] |
| LO8 | Donor-specific ledgers | Done [controller] |

## 7. Assets

| ID | Requirement | Status |
|----|------------|--------|
| AS1 | Categories + depreciation | Done [controller] |
| AS2 | QR tagging | Done [controller] |
| AS3 | Custody + movement | Done [controller] |
| AS4 | Maintenance schedules | Done [controller] |
| AS5 | Donor-funded flag | Done [controller] |
| AS6 | Disposal with approval | Done [controller] |
| AS7 | Asset verification | Done [controller] |

## 8. Fleet

| ID | Requirement | Status |
|----|------------|--------|
| FL1 | Vehicle + driver records | Done [controller] |
| FL2 | Vehicle allocation | Done [controller] |
| FL3 | Fuel/spares linked to purchase | Done [controller] |
| FL4 | Expiry alerts (insurance/license) | Done [controller] |
| FL5 | Cost-per-km analytics | Done [controller] |
| FL6 | Monthly fleet reports | Done [controller] |

## 9. Governance & Security

| ID | Requirement | Approach | Status |
|----|------------|----------|--------|
| GV1 | Segregation of duties | Role matrix + validation | Done [tested] |
| GV2 | Least-privilege roles | Role fixtures | Done [controller] |
| GV3 | User Permissions donor/warehouse | Frappe User Permissions | Configured |
| GV4 | Field-level permissions | Frappe Role Permissions | Configured |
| GV5 | Hash chain for critical docs | hash_chain.py + record_hash | Done [controller] |
| GV6 | Approval delegation | Approval Delegation DocType | Done [tested] |
| GV7 | E-signature | Frappe Signature | Configured |
| GV8 | 2FA for approvers | Frappe Two Factor | Configured |
| GV9 | Session/password policy | Frappe System Settings | Configured |
| GV10 | Rate limiting | rate_limiter.py | Done [controller] |
| GV11 | SSO scaffolding | Frappe OAuth/OIDC | Configured |
| GV12 | IDOR protection | Frappe permissions + portal | Done [controller] |

## 10. Finance & Kenya Localization

| ID | Requirement | Status |
|----|------------|--------|
| FI1 | KES + multi-currency | Done [controller] |
| FI2 | Chart of Accounts + fiscal yr | Done [controller] |
| FI3 | Accounting dimensions | Done [controller] |
| FI4 | Tax templates: VAT, WHT | Configured |
| FI5 | KRA PIN validation | Done [controller] |
| FI6 | eTIMS integration (adapter) | Done [controller] |
| FI7 | SMS provider abstraction | Done [controller] |

## 11. Notifications & Dashboards

| ID | Requirement | Status |
|----|------------|--------|
| NT1 | Email notifications (Mailpit) | Configured |
| NT2 | SMS notifications | Done [controller] |
| NT3 | Notification rules | Configured |
| NT4 | Procurement dashboard | Done [controller] |
| NT5 | Stock dashboard | Done [controller] |
| NT6 | Fleet dashboard | Done [controller] |
| NT7 | Asset dashboard | Done [controller] |

## 12. Operations

| ID | Requirement | Status |
|----|------------|--------|
| OP1 | Scheduled backups | Done [controller] |
| OP2 | Scheduler + workers | Configured |
| OP3 | Error/health endpoints | Done [controller] |
| OP4 | Idempotent background jobs | Done [controller] |
| OP5 | Dry-run migration | Done [controller] |

## 13. Upgradeability

| ID | Requirement | Status | Evidence |
|----|------------|--------|----------|
| UG1 | Zero core patches | Done [verified] | 0 patches; test_hook_safety.py |
| UG2 | Additive hooks; no core controller/method overrides | Done [verified] | `hooks.py`, compatibility scanner, upgrade-safety tests |
| UG3 | UI in Ugavi assets and app-owned templates only | Done [controller] | `ugavi/public/css/`; `ugavi/www/supplier/` |
| UG4 | SBOM + dependency scan | Done [controller] | Dockerfile + CI pipeline |
| UG5 | Upgrade dry-run | Done [controller] | CI migrate job |

---

## Summary (Pass 2 — Post Phase D-H)

| Category | Done [tested] | Done [controller] | Configured | Gap | Total |
|----------|---------------|-------------------|------------|-----|-------|
| Procurement | 1 | 9 | 0 | 0 | 10 |
| Tendering | 3 | 11 | 0 | 0 | 14 |
| Evaluation | 1 | 6 | 0 | 0 | 7 |
| Supplier MGMT | 0 | 6 | 0 | 0 | 6 |
| Contracts | 0 | 4 | 0 | 0 | 4 |
| Logistics | 0 | 8 | 0 | 0 | 8 |
| Assets | 0 | 7 | 0 | 0 | 7 |
| Fleet | 0 | 6 | 0 | 0 | 6 |
| Governance | 2 | 3 | 7 | 0 | 12 |
| Finance | 0 | 4 | 3 | 0 | 7 |
| Notifications | 0 | 4 | 3 | 0 | 7 |
| Operations | 0 | 4 | 1 | 0 | 5 |
| Upgradeability | 0 | 5 | 0 | 0 | 5 |
| **TOTAL** | **7** | **77** | **14** | **0** | **98** |

**98 requirements mapped to implementations/configuration.** The classification
table is an implementation inventory, not 98 passed acceptance tests or a
production-readiness certificate. External integrations, client templates,
production 2FA/SSO, capacity targets and recovery objectives need separate
acceptance. GV8 is configurable but demo 2FA is off; FI6 is an adapter, not a
certified eTIMS connection.

Current automated evidence: [evidence registry](evidence.md). The
[functional demo tour](../demo/LOKADO-DEMO-TOUR.md#4-requirement-to-scene-map)
maps every original client requirement to actors, scenes, positive evidence,
negative controls and verification limits. The new runtime test exercises
one/two/three-code opening with actual crypto, database writes and private PDF
creation. Browser tests cover all 16 staff identities plus supplier
desktop/mobile access. Other business transitions remain explicit live steps.
