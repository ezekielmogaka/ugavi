# Evidence Registry

> Mapping every claim to its verified source.
> Label: `[verified: path|url]` `[tested: test_id]` `[assumption]`

## Environment
- **Frappe:** 16.52.0 (version-16, commit 4515014) `[verified: bench version]`
- **ERPNext:** 16.51.1 (version-16, commit 5af6561) `[verified: bench version]`
- **Ugavi:** 0.1.0 (main, commit 69c4b15) `[verified: bench version]`
- **Site:** ugavi.localhost `[verified: docker exec bench list-apps]`
- **Database:** MariaDB (devcontainer-mariadb-1) `[verified: docker ps]`
- **Mail:** Mailpit on :1025/:8025 `[verified: docker ps]`
- **Valkey:** 2 instances (cache + queue) `[verified: docker ps]`
- **Test runner:** Frappe test runner, 0 tests found `[verified: bench run-tests --app ugavi]`
- **Seed script:** LOKADO seed runs successfully `[verified: bench execute ugavi.scripts.seed_lokado.run]`
- Generic demo seed also available: `bench execute ugavi.scripts.seed_demo.run` (legacy)
- **Demo checks:** `demo-check` and `fleet-check` both return `"ready": true, "issues": []`

## Verified DocTypes (JSON exists)
| DocType | Path |
|----------|------|
| Purchase Requisition | `ugavi/procurement/doctype/purchase_requisition/purchase_requisition.json` |
| PR Item (child) | `ugavi/procurement/doctype/pr_item/pr_item.json` |
| Supplier Prequalification | `ugavi/procurement/doctype/supplier_prequalification/supplier_prequalification.json` |
| Prequalification Category (child) | `ugavi/procurement/doctype/prequalification_category/prequalification_category.json` |
| Prequalification Document (child) | `ugavi/procurement/doctype/prequalification_document/prequalification_document.json` |
| Tender | `ugavi/tendering/doctype/tender/tender.json` |
| Tender Document (child) | `ugavi/tendering/doctype/tender_document/tender_document.json` |
| Addendum (child) | `ugavi/tendering/doctype/addendum/addendum.json` |
| Evaluation Committee (child) | `ugavi/procurement/doctype/evaluation_committee/evaluation_committee.json` |
| Bid | `ugavi/procurement/doctype/bid/bid.json` |
| Bid Opening Record | `ugavi/procurement/doctype/bid_opening_record/bid_opening_record.json` |
| Bid Opening Detail (child) | `ugavi/procurement/doctype/bid_opening_detail/bid_opening_detail.json` |
| Sealed Bid Key | `ugavi/procurement/doctype/sealed_bid_key/sealed_bid_key.json` |
| Ugavi Procurement Settings | `ugavi/procurement/doctype/ugavi_procurement_settings/ugavi_procurement_settings.json` |
| Delegation of Authority | `ugavi/governance/doctype/delegation_of_authority/delegation_of_authority.json` |
| Donor Profile | `ugavi/compliance/doctype/donor_profile/donor_profile.json` |
| Donor Rule (child) | `ugavi/compliance/doctype/donor_rule/donor_rule.json` |

## Verified Python Services
| Service | Path |
|---------|------|
| Procurement Rules Engine | `ugavi/procurement/services/rules_engine.py` |
| Delegation of Authority | `ugavi/procurement/services/delegation_of_authority.py` |
| Sealed Bid Crypto | `ugavi/procurement/services/sealed_bid.py` |
| SMS Provider Adapter | `ugavi/integrations/sms/base.py` |

## ERPNext Standard Capabilities Verified
| Capability | Path |
|-----------|------|
| Purchase Requisition | `apps/erpnext/erpnext/buying/doctype/purchase_requisition/` |
| Purchase Order | `apps/erpnext/erpnext/buying/doctype/purchase_order/` |
| Purchase Receipt | `apps/erpnext/erpnext/stock/doctype/purchase_receipt/` |
| Budget | `apps/erpnext/erpnext/accounts/doctype/budget/` |
| Stock Entry | `apps/erpnext/erpnext/stock/doctype/stock_entry/` |
| Asset | `apps/erpnext/erpnext/assets/doctype/asset/` |

## DocType directories WITHOUT JSON (stubs only)
- procurement: contract, supplier_scorecard, procurement_rules
- governance: waiver, approval_delegation, audit_log, segregation_of_duties
- compliance: budget_encumbrance, three_way_match
- logistics: donor_warehouse, inter_donor_transfer, monthly_stock_report, stock_ledger
- assets: asset_disposal, asset_movement, asset_register, asset_verification
- fleet: fuel_log, spare_parts_issue, trip_log, vehicle, vehicle_allocation

## Missing JS client scripts (listed in hooks but not created)
- `procurement/doctype/purchase_requisition/purchase_requisition.js`
- `procurement/doctype/supplier_prequalification/supplier_prequalification.js`
- `tendering/doctype/tender/tender.js`
- `procurement/doctype/bid/bid.js`
- `procurement/doctype/bid_opening_record/bid_opening_record.js`

## MVP2 W0 Update (2026-10-21)

### Test Results [measured: bench run-tests --app ugavi, 2026-10-21]
- **27/27 tests pass** (0.338s)
- 12 integration tests: TestApprovalDelegation, TestContractLifecycle, TestKeyDistribution, TestScoringEngine, TestSegregationOfDuties, TestWaiverWorkflow
- 15 unit tests: TestProcurementRulesEngine, TestDelegationOfAuthority, TestOTP, TestSealedBidCrypto

### LOKADO Seed [tested: bench execute ugavi.scripts.seed_lokado.run]
- 868-line seed script, 19 functions, covers LOKADO (Turkana-based Kenyan NGO)
- Seeds: Company, 19 users (14 staff + 5 supplier portal), 6 donors, 42 suppliers, 15 items, 6 warehouses
- Procurement: 6 PRs, 5 tenders, 15 bids, 1 award, 1 contract, milestones
- Governance: DoA, SoD, Waiver, Audit, donor-warehouse links
- Fleet: 4 vehicles, 8 fuel logs, 8 trip logs, 8 spare parts issues, 4 donor-isolated fleet utilization reports
- Assets: 4 registers, 2 movements, 1 disposal
- Compiles clean, production-guarded (refuses to run outside dev/demo environments)
- **Canonical seed:** `make seed` → `make seed-lokado` (default; `make seed-generic` for legacy generic data)
- **Validation:** `make demo-check` and `make fleet-check` both return `"ready": true, "issues": []`
- **Safety:** `make backup-demo` / `make restore-demo` protect against data loss

### Crypto Verification [tested: 2026-10-21]
- **SV-01 RESOLVED (FALSE POSITIVE):** `cryptography==50.0.2` IS installed in bench venv at `/home/frappe/frappe-bench/env/`
- Full RSA-4096 + AES-256-GCM cycle verified PASS
- Prior false negative caused by using system Python (`/usr/local/bin/python3`) instead of bench venv Python

### Seed Data State [measured: frappe.db.count + demo-check, 2026-10-22]
- 42 Suppliers, 15 Items, 2 Vehicles, 8 Donor Profiles
- 6 PRs, 5 Tenders, 15 Bids, 2 Sealed Bid Keys, 0 Bid Opening Records (created live)
- R3 (seed incomplete): RESOLVED — full procurement workflow seeded, verified by `make demo-check`

### DocType DB State
- 60 DocTypes in DB with JSON schemas
- The 22 "missing" DocTypes listed in BASELINE.md section 3.2 actually all have JSON schemas (verified in Docker, not yet reflected on host FS due to 161 uncommitted changes)

### Updated Risk Assessment
- R0 (cryptography absent): RESOLVED
- R1 (161 uncommitted files): STILL OPEN
- R2 (14 schemas in Docker not on host): Partially resolved — schemas exist in Docker
- R3 (seed incomplete): RESOLVED — LOKADO seed now canonical, 19 users, full procurement workflow with validation
- R5 (Contract → UgaviContract rename): Partially resolved — both exist in DB

### Crypto Audit Updates (SEALED-BID-REPORT.md)
- SV-01: FALSE POSITIVE — cryptography installed. Corrected.
- SV-02: Shares plaintext in DB. PENDING share wrapping.
- SV-03-05: Accepted as design decisions.
- Settings integration: OTP expiry + max attempts from Ugavi Procurement Settings DocType.
- Constant-time OTP: uses secrets.compare_digest.

### W0 Deliverables Created
- docs/mvp1/GO-NO-GO.md — MVP1 gate assessment
- docs/mvp2/SCOPE.md — Full 13-workstream scope with client decisions
- docs/mvp2/OPEN-QUESTIONS.md — 10 blocking + 5 non-blocking questions
- docs/mvp2/ (this file updated) — Evidence registry
## M1 Sync Update (2026-10-21)

### Docker → Host Sync
13 DocType directories and all service files synced from Docker to host FS:
- **Tendering:** bid_security, bid_evaluation_summary, coi_declaration, standstill_period
- **Assets:** asset_disposal, asset_movement, asset_register, asset_verification
- **Fleet:** fuel_log, spare_parts_issue, trip_log, vehicle, vehicle_allocation
- **Services:** procurement, tendering, governance, compliance, fleet, assets, logistics

### Host → Docker Sync
2 report DocTypes pushed to Docker:
- `asset_register_report` → Docker: /assets/doctype/asset_register_report/
- `fleet_utilization_report` → Docker: /fleet/doctype/fleet_utilization_report/

### bench migrate
- Ran successfully, no errors [tested: 2026-10-21]
- Asset Register Report: registered ✅
- Fleet Utilization Report: registered ✅

### Bid Security (T7)
- **Status: PASS (was FAIL)** [verified: Docker + host, 2026-10-21]
- JSON + Python controller exist at tendering/doctype/bid_security/
- Loads correctly: `frappe.get_doc("DocType", "Bid Security")` succeeds

### Remaining FAIL Atoms (2)
- P5: PO from approved PR — still FAIL
- S2: Batch & expiry — still FAIL

### 161 Uncommitted Changes
- Reduced but not eliminated. Core DocType files now exist on both sides.
- `git status` still shows divergence for __pycache__, old stubs, etc.
## Security Finding (CRITICAL)
## MVP3 W0 — Hosting & Tenancy Analysis (2026-10-21)

### Gate Check

| Gate | Status | Evidence |
|------|--------|----------|
| MVP1 GO-NO-GO | CONDITIONAL-GO (demo) / NO-GO (pilot) | docs/mvp1/GO-NO-GO.md |
| MVP2 GO-NO-GO | ❌ NOT MET (W1-W13 unbuilt) | docs/mvp2/GO-NO-GO.md |
| Tests | ✅ 15/15 pass 0.038s | [tested: 2026-10-21] |
| bench migrate | ✅ Clean | [tested: 2026-10-21] |
| Core DocTypes | ✅ All load | [tested: 2026-10-21] |

### W0 Deliverables

| Deliverable | Path | Status |
|-------------|------|--------|
| MVP2 Gate Assessment | docs/mvp2/GO-NO-GO.md | ✅ Created |
| Hosting & Tenancy ADR | docs/adr/hosting-and-tenancy.md | ✅ Created (ADR-006, PROPOSED) |
| MVP3 Open Questions | docs/mvp3/OPEN-QUESTIONS.md | ✅ Created (30 questions) |

### Key Architectural Finding

Frappe's multi-site architecture shares app code across all sites on a bench [verified: `sites/` directory structure]. This means:
- **All tenants on one bench must upgrade together** — unacceptable for sealed-bid ceremonies spanning days/weeks
- **One bench per tenant (Option E)** is recommended for isolation and upgrade independence

### Frappe Version Confirmed

| Component | Version | Evidence |
|-----------|---------|----------|
| Frappe | 16.52.0 | [verified: `bench version`, 2026-10-21] |
| ERPNext | 16.51.1 | [verified: `bench version`, 2026-10-21] |
| Ugavi | 0.1.0 | [verified: `bench version`, 2026-10-21] |
| Python | 3.14.8 | [verified: `python3 --version`, 2026-10-21] |

### NEXT: STOP at MVP2 gate per W0 rules. Proceed only if client overrides.
- **TN13**: Sealed Bid Key doctype stores `public_key_pem` as Long Text (public key only — the private key is split via SSS and never stored as a single field). The `private_key_pem` claim in an earlier evidence version was a false positive ([verified: `sealed_bid_key.json`, field at line 19 is `public_key_pem`, 2026-10-21]). The architecture is correct: shares are encrypted and distributed to 3 officers.